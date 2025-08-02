#!/usr/bin/env python3
"""
SSM-based Analysis Engine for Phoenix Hydra
Non-Transformer analysis using State Space Models for energy efficiency
"""

import asyncio
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psutil
import torch
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
ANALYSIS_COUNTER = Counter('analysis_requests_total', 'Total analysis requests')
ANALYSIS_DURATION = Histogram('analysis_duration_seconds', 'Analysis duration')
ENERGY_CONSUMPTION = Gauge('energy_consumption_watts', 'Estimated energy consumption')
COMPONENT_HEALTH = Gauge('component_health_score', 'Component health score', ['component_id'])


@dataclass
class SSMAnalysisConfig:
    """Configuration for SSM Analysis Engine"""
    d_model: int = 256        # Model dimension (reduced for local processing)
    d_state: int = 32         # SSM state dimension
    d_conv: int = 4           # Local convolution width
    expand_factor: int = 2    # Expansion factor
    dt_rank: int = 16         # Temporal parameter rank
    dt_min: float = 0.001     # Minimum dt value
    dt_max: float = 0.1       # Maximum dt value
    memory_efficient: bool = True
    local_processing: bool = True
    energy_optimization: bool = True
    max_sequence_length: int = 512


class EnergyEfficiencyMonitor:
    """Monitor energy efficiency for local hardware"""
    
    def __init__(self):
        self.measurements = []
        self.current_measurement = None
        
    def start_measurement(self):
        """Start energy consumption measurement"""
        self.current_measurement = {
            "start_time": time.time(),
            "start_cpu": psutil.cpu_percent(),
            "start_memory": psutil.virtual_memory().percent
        }
        
    def end_measurement(self):
        """End measurement and calculate consumption"""
        if not self.current_measurement:
            return 0.0
            
        duration = time.time() - self.current_measurement["start_time"]
        avg_cpu = (self.current_measurement["start_cpu"] + psutil.cpu_percent()) / 2
        
        # Simplified power estimation (Watts)
        base_power = 30  # Base system power
        cpu_power = avg_cpu * 0.3  # CPU contribution
        estimated_power = base_power + cpu_power
        
        energy_wh = estimated_power * duration / 3600  # Watt-hours
        
        measurement = {
            "duration": duration,
            "avg_cpu": avg_cpu,
            "estimated_power_watts": estimated_power,
            "energy_wh": energy_wh
        }
        
        self.measurements.append(measurement)
        ENERGY_CONSUMPTION.set(estimated_power)
        
        return estimated_power


class SimpleSSMLayer(torch.nn.Module):
    """Simplified SSM layer for local processing"""
    
    def __init__(self, config: SSMAnalysisConfig):
        super().__init__()
        self.config = config
        self.d_model = config.d_model
        self.d_state = config.d_state
        
        # Simplified projections
        self.input_proj = torch.nn.Linear(self.d_model, self.d_model * 2)
        self.output_proj = torch.nn.Linear(self.d_model, self.d_model)
        
        # SSM parameters (simplified)
        self.A = torch.nn.Parameter(torch.randn(self.d_model, self.d_state) * 0.1)
        self.B = torch.nn.Parameter(torch.randn(self.d_model, self.d_state) * 0.1)
        self.C = torch.nn.Parameter(torch.randn(self.d_model, self.d_state) * 0.1)
        self.D = torch.nn.Parameter(torch.ones(self.d_model) * 0.1)
        
        # Activation
        self.activation = torch.nn.SiLU()
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass with simplified SSM computation"""
        B, L, D = x.shape
        
        # Input projection
        x_proj = self.input_proj(x)  # (B, L, 2*D)
        x_ssm, x_gate = x_proj.chunk(2, dim=-1)  # (B, L, D), (B, L, D)
        
        # Simplified SSM computation
        # In a full implementation, this would be the parallel scan
        # For now, we use a simplified recurrent computation
        h = torch.zeros(B, self.d_state, device=x.device, dtype=x.dtype)
        outputs = []
        
        for i in range(L):
            # Simplified state update: h = A @ h + B @ x
            h = torch.tanh(torch.einsum('bd,ds->bs', h, self.A.T) + 
                          torch.einsum('bd,ds->bs', x_ssm[:, i], self.B))
            
            # Output: y = C @ h + D @ x
            y = torch.einsum('bs,ds->bd', h, self.C.T) + self.D * x_ssm[:, i]
            outputs.append(y)
        
        ssm_output = torch.stack(outputs, dim=1)  # (B, L, D)
        
        # Apply gating
        output = ssm_output * self.activation(x_gate)
        
        return self.output_proj(output)


class NonTransformerAnalysisEngine:
    """SSM-based analysis engine for system components"""
    
    def __init__(self, config: SSMAnalysisConfig):
        self.config = config
        self.device = torch.device("cpu")  # Force CPU for local processing
        
        # Analysis layers
        self.component_analyzer = SimpleSSMLayer(config)
        self.temporal_analyzer = SimpleSSMLayer(config)
        
        # Energy monitoring
        self.energy_monitor = EnergyEfficiencyMonitor()
        
        # Memory for recurrent processing
        self.component_memory = {}
        self.analysis_history = []
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        logger.info(f"Initialized SSM Analysis Engine with config: {config}")
        
    async def analyze_components(self, components: List[Dict]) -> Dict:
        """Main analysis function for system components"""
        ANALYSIS_COUNTER.inc()
        
        with ANALYSIS_DURATION.time():
            self.energy_monitor.start_measurement()
            
            try:
                analysis_results = {
                    "timestamp": time.time(),
                    "component_analysis": {},
                    "temporal_patterns": {},
                    "performance_metrics": {},
                    "energy_consumption": {},
                    "health_summary": {}
                }
                
                # Analyze each component
                for component in components:
                    component_id = component.get('id', 'unknown')
                    result = await self._analyze_single_component(component)
                    analysis_results["component_analysis"][component_id] = result
                    
                    # Update Prometheus metrics
                    health_score = result.get("component_health", {}).get("health_score", 0.0)
                    COMPONENT_HEALTH.labels(component_id=component_id).set(health_score)
                
                # Aggregate temporal patterns
                analysis_results["temporal_patterns"] = self._analyze_temporal_patterns()
                
                # Performance metrics
                analysis_results["performance_metrics"] = self._calculate_performance_metrics()
                
                # Energy consumption report
                power_consumption = self.energy_monitor.end_measurement()
                analysis_results["energy_consumption"] = {
                    "current_power_watts": power_consumption,
                    "efficiency_score": min(1.0, 100.0 / power_consumption) if power_consumption > 0 else 1.0
                }
                
                # Health summary
                analysis_results["health_summary"] = self._generate_health_summary(
                    analysis_results["component_analysis"]
                )
                
                # Store in history
                self.analysis_history.append(analysis_results)
                if len(self.analysis_history) > 100:  # Keep last 100 analyses
                    self.analysis_history.pop(0)
                
                logger.info(f"Completed analysis of {len(components)} components")
                return analysis_results
                
            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                self.energy_monitor.end_measurement()
                raise
    
    async def _analyze_single_component(self, component: Dict) -> Dict:
        """Analyze individual component using SSM"""
        component_id = component.get('id', 'unknown')
        
        try:
            # Prepare component data
            component_tensor = self._prepare_component_data(component)
            
            # Run SSM analysis
            with torch.no_grad():
                component_features = self.component_analyzer(component_tensor)
                temporal_features = self.temporal_analyzer(component_tensor)
            
            # Process results
            results = {
                "component_health": self._evaluate_component_health(component_features),
                "temporal_behavior": self._evaluate_temporal_behavior(temporal_features),
                "optimization_suggestions": self._generate_optimization_suggestions(component),
                "analysis_timestamp": time.time()
            }
            
            # Update component memory
            self.component_memory[component_id] = {
                "last_analysis": results,
                "features": component_features.cpu().numpy(),
                "timestamp": time.time()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to analyze component {component_id}: {e}")
            return {
                "component_health": {"health_score": 0.0, "status": "error"},
                "temporal_behavior": {"trend": 0.0, "stability": 0.0},
                "optimization_suggestions": [f"Analysis failed: {str(e)}"],
                "analysis_timestamp": time.time()
            }
    
    def _prepare_component_data(self, component: Dict) -> torch.Tensor:
        """Prepare component data for SSM analysis"""
        features = []
        
        # Performance metrics
        if 'performance' in component:
            perf = component['performance']
            features.extend([
                perf.get('cpu_usage', 0.0),
                perf.get('memory_usage', 0.0),
                perf.get('latency', 0.0),
                perf.get('throughput', 0.0)
            ])
        
        # System state
        if 'system_state' in component:
            state = component['system_state']
            features.extend([
                state.get('temperature', 0.0),
                state.get('power_consumption', 0.0),
                state.get('error_rate', 0.0)
            ])
        
        # Health metrics
        if 'health' in component:
            health = component['health']
            features.extend([
                health.get('uptime', 0.0),
                health.get('response_time', 0.0),
                health.get('success_rate', 1.0)
            ])
        
        # Pad or truncate to model dimension
        while len(features) < self.config.d_model:
            features.append(0.0)
        features = features[:self.config.d_model]
        
        # Convert to tensor: (batch=1, sequence=1, features)
        tensor_data = torch.tensor(features, dtype=torch.float32)
        return tensor_data.unsqueeze(0).unsqueeze(0)  # (1, 1, d_model)
    
    def _evaluate_component_health(self, features: torch.Tensor) -> Dict:
        """Evaluate component health from SSM features"""
        feature_stats = features.squeeze().cpu().numpy()
        
        # Calculate health metrics
        health_score = float(np.clip(np.mean(feature_stats), 0.0, 1.0))
        stability_score = float(np.clip(1.0 - np.std(feature_stats), 0.0, 1.0))
        
        # Determine status
        if health_score > 0.8:
            status = "healthy"
        elif health_score > 0.5:
            status = "degraded"
        else:
            status = "critical"
        
        return {
            "health_score": health_score,
            "stability_score": stability_score,
            "status": status,
            "anomaly_count": int(np.sum(np.abs(feature_stats) > 2.0))  # Simple anomaly detection
        }
    
    def _evaluate_temporal_behavior(self, features: torch.Tensor) -> Dict:
        """Evaluate temporal behavior patterns"""
        temporal_stats = features.squeeze().cpu().numpy()
        
        # Simple trend analysis
        if len(temporal_stats) > 1:
            trend = float(np.polyfit(range(len(temporal_stats)), temporal_stats, 1)[0])
        else:
            trend = 0.0
        
        stability = float(np.clip(1.0 - np.std(temporal_stats), 0.0, 1.0))
        
        return {
            "trend": trend,
            "stability": stability,
            "temporal_score": float(np.mean(temporal_stats))
        }
    
    def _generate_optimization_suggestions(self, component: Dict) -> List[str]:
        """Generate optimization suggestions based on analysis"""
        suggestions = []
        
        # Check performance metrics
        if 'performance' in component:
            perf = component['performance']
            if perf.get('cpu_usage', 0) > 80:
                suggestions.append("High CPU usage detected - consider scaling or optimization")
            if perf.get('memory_usage', 0) > 85:
                suggestions.append("High memory usage - check for memory leaks")
            if perf.get('latency', 0) > 1000:  # ms
                suggestions.append("High latency detected - investigate bottlenecks")
        
        # Check system state
        if 'system_state' in component:
            state = component['system_state']
            if state.get('error_rate', 0) > 0.05:  # 5%
                suggestions.append("High error rate - check logs and error handling")
            if state.get('temperature', 0) > 70:  # Celsius
                suggestions.append("High temperature - check cooling and workload")
        
        if not suggestions:
            suggestions.append("Component operating within normal parameters")
        
        return suggestions
    
    def _analyze_temporal_patterns(self) -> Dict:
        """Analyze temporal patterns across all components"""
        if len(self.analysis_history) < 2:
            return {"patterns": [], "overall_trend": 0.0}
        
        # Extract health scores over time
        health_scores = []
        for analysis in self.analysis_history[-10:]:  # Last 10 analyses
            scores = [
                comp.get("component_health", {}).get("health_score", 0.0)
                for comp in analysis.get("component_analysis", {}).values()
            ]
            if scores:
                health_scores.append(np.mean(scores))
        
        if len(health_scores) > 1:
            trend = float(np.polyfit(range(len(health_scores)), health_scores, 1)[0])
        else:
            trend = 0.0
        
        return {
            "patterns": ["temporal_analysis_available"],
            "overall_trend": trend,
            "stability": float(1.0 - np.std(health_scores)) if health_scores else 1.0
        }
    
    def _calculate_performance_metrics(self) -> Dict:
        """Calculate overall performance metrics"""
        current_time = time.time()
        
        # System metrics
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        
        return {
            "system_cpu_percent": cpu_percent,
            "system_memory_percent": memory.percent,
            "analysis_engine_uptime": current_time - getattr(self, '_start_time', current_time),
            "total_analyses_performed": len(self.analysis_history),
            "components_in_memory": len(self.component_memory)
        }
    
    def _generate_health_summary(self, component_analysis: Dict) -> Dict:
        """Generate overall health summary"""
        if not component_analysis:
            return {"overall_status": "unknown", "healthy_components": 0, "total_components": 0}
        
        health_scores = [
            comp.get("component_health", {}).get("health_score", 0.0)
            for comp in component_analysis.values()
        ]
        
        healthy_count = sum(1 for score in health_scores if score > 0.7)
        total_count = len(health_scores)
        avg_health = np.mean(health_scores) if health_scores else 0.0
        
        if avg_health > 0.8:
            overall_status = "healthy"
        elif avg_health > 0.5:
            overall_status = "degraded"
        else:
            overall_status = "critical"
        
        return {
            "overall_status": overall_status,
            "average_health_score": float(avg_health),
            "healthy_components": healthy_count,
            "total_components": total_count,
            "health_percentage": float(healthy_count / total_count * 100) if total_count > 0 else 0.0
        }


async def main():
    """Main function for standalone execution"""
    # Start Prometheus metrics server
    start_http_server(8090)
    logger.info("Started Prometheus metrics server on port 8090")
    
    # Initialize analysis engine
    config = SSMAnalysisConfig()
    engine = NonTransformerAnalysisEngine(config)
    engine._start_time = time.time()
    
    logger.info("SSM Analysis Engine started successfully")
    
    # Example analysis loop
    while True:
        try:
            # Mock component data for testing
            test_components = [
                {
                    "id": "phoenix-core",
                    "performance": {
                        "cpu_usage": np.random.uniform(20, 80),
                        "memory_usage": np.random.uniform(30, 70),
                        "latency": np.random.uniform(100, 500),
                        "throughput": np.random.uniform(50, 200)
                    },
                    "system_state": {
                        "temperature": np.random.uniform(40, 65),
                        "power_consumption": np.random.uniform(50, 150),
                        "error_rate": np.random.uniform(0, 0.02)
                    },
                    "health": {
                        "uptime": np.random.uniform(0.95, 1.0),
                        "response_time": np.random.uniform(50, 200),
                        "success_rate": np.random.uniform(0.98, 1.0)
                    }
                }
            ]
            
            # Perform analysis
            results = await engine.analyze_components(test_components)
            
            # Log summary
            health_summary = results.get("health_summary", {})
            logger.info(f"Analysis complete - Overall status: {health_summary.get('overall_status', 'unknown')}, "
                       f"Health: {health_summary.get('health_percentage', 0):.1f}%")
            
            # Wait before next analysis
            await asyncio.sleep(30)  # Analyze every 30 seconds
            
        except KeyboardInterrupt:
            logger.info("Shutting down analysis engine...")
            break
        except Exception as e:
            logger.error(f"Analysis loop error: {e}")
            await asyncio.sleep(10)  # Wait before retrying


if __name__ == "__main__":
    asyncio.run(main())