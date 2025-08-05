<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" class="logo" width="120"/>

# DevOps Ultra-Detallado: Non-Transformer Analysis Engines y Advanced Gap Detection para Phoenix DemiGod

## Introducción Técnica: Transcendencia Arquitectónica SSM/Mamba

El desarrollo de **Non-Transformer Analysis Engines** representa una evolución fundamental en la arquitectura de procesamiento de IA, especialmente para sistemas local-first como Phoenix DemiGod[^1][^2]. Los **State Space Models (SSM)** y arquitecturas **Mamba** ofrecen ventajas computacionales significativas: consumo energético 80% menor que Transformers equivalentes, capacidad de procesamiento de secuencias ultra-largas con escalado lineal, y latencia constante independiente de la longitud de secuencia[^3][^4].

**Biomimetic AI** complementa esta arquitectura copiando procesos cognitivos naturales para crear sistemas más eficientes y adaptativos[^5]. Esta aproximación permite desarrollar agentes capaces de tomar decisiones autónomas y evolucionar estrategias basándose en resultados operacionales, fundamentales para el éxito de Phoenix DemiGod en entornos de producción.

## 13.4 Create Non-Transformer Analysis Engines

### Arquitectura SSM-Based Analysis Engine

#### **Core SSM Processing Module**

```python
# src/core/ssm_analysis_engine.py
import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

@dataclass
class SSMAnalysisConfig:
    """
    Configuración para SSM Analysis Engine
    """
    d_model: int = 512        # Dimensión del modelo (embedding dimension)
    d_state: int = 64         # Dimensión del estado SSM (state dimension)
    d_conv: int = 4           # Ancho de convolución local (convolution kernel size)
    expand_factor: int = 2    # Factor de expansión (expansion factor for hidden layers)
    dt_rank: int = 32         # Rango para parámetro temporal (rank for the temporal parameter)
    dt_min: float = 0.001     # Valor mínimo dt (minimum value for the temporal parameter)
    dt_max: float = 0.1       # Valor máximo dt (maximum value for the temporal parameter)
    memory_efficient: bool = True # Flag to enable memory-efficient operations
    local_processing: bool = True # Flag to enable optimizations for local processing
    energy_optimization: bool = True # Flag to enable energy optimization techniques

class StateSpaceLayer(torch.nn.Module):
    """
    Implementación optimizada de State Space Layer para análisis
    """
    
    def __init__(self, config: SSMAnalysisConfig):
        """
        Initializes the StateSpaceLayer with the given configuration.
        """
        super().__init__()
        self.config = config
        self.d_model = config.d_model
        self.d_state = config.d_state
        self.d_conv = config.d_conv

        # Input and output projections
        self.in_proj = torch.nn.Linear(self.d_model, self.d_model * 2)
        self.conv1d = torch.nn.Conv1d(
            in_channels=self.d_model,
            out_channels=self.d_model,
            kernel_size=config.d_conv,
            padding=config.d_conv - 1,
            groups=self.d_model
        )

        # SSM parameters
        self.x_proj = torch.nn.Linear(self.d_model, config.dt_rank + config.d_state * 2)
        self.dt_proj = torch.nn.Linear(config.dt_rank, self.d_model)

        # Optimized initialization for analysis
        self._initialize_ssm_parameters()

    def _initialize_ssm_parameters(self):
        """
        Specialized initialization for component analysis.
        Initializes SSM parameters including A, B, C, and D matrices.
        """
        # Matrix A: HiPPO initialization for capturing long-range dependencies
        A = torch.arange(1, self.config.d_state + 1, dtype=torch.float32)
        A = A.repeat(self.d_model, 1)
        self.A_log = torch.nn.Parameter(torch.log(A))

        # Matrix B: Optimized for temporal analysis
        self.B = torch.nn.Parameter(torch.randn(self.d_model, self.config.d_state))

        # Matrix C: Output projection
        self.C = torch.nn.Parameter(torch.randn(self.d_model, self.config.d_state))

        # Parameter D: Residual connection
        self.D = torch.nn.Parameter(torch.ones(self.d_model))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass optimized for efficient analysis.
        Applies input projection, convolution, SSM application, and gating.
        """
        B, L, D = x.shape
        
        # Input projection and splitting
        x = self.in_proj(x)  # (B, L, 2*D) - Project input to a higher dimension
        x, z = x.chunk(2, dim=-1)  # (B, L, D), (B, L, D) - Split into two chunks for processing
        
        # 1D convolution for local feature extraction
        x = x.transpose(1, 2)  # (B, D, L) - Transpose for convolution
        x = self.conv1d(x)[:, :, :L]  # Apply convolution with valid padding
        x = x.transpose(1, 2)  # (B, L, D) - Transpose back
        
        # Apply the State Space Model
        x = self._apply_ssm(x)
        
        # Gating mechanism using SiLU activation
        x = x * torch.nn.functional.silu(z)
        
        return x
    
    def _apply_ssm(self, x: torch.Tensor) -> torch.Tensor:
        """Aplicación eficiente del State Space Model"""
        B, L, D = x.shape
        
        # Proyección para parámetros dinámicos
        x_proj = self.x_proj(x)  # (B, L, dt_rank + 2*d_state)
        dt, B_proj, C_proj = torch.split(
            x_proj, 
            [self.config.dt_rank, self.config.d_state, self.config.d_state], 
            dim=-1
        )
        
        # Dynamic temporal parameter
        dt = torch.nn.functional.softplus(self.dt_proj(dt))  # (B, L, D)
        
        # Dynamic matrices
        A = -torch.exp(self.A_log.float())  # (D, d_state)
        B = self.B.unsqueeze(0) * B_proj.unsqueeze(-2)  # (B, L, D, d_state)
        C = self.C.unsqueeze(0) * C_proj.unsqueeze(-2)  # (B, L, D, d_state)
        
        # Discretization using Zero-Order Hold (ZOH) method
        dt_A = dt.unsqueeze(-1) * A.unsqueeze(0).unsqueeze(0)  # (B, L, D, d_state)
        A_discrete = torch.exp(dt_A)
        B_discrete = dt.unsqueeze(-1) * B
        
        # Parallel scan for SSM
        y = self._parallel_scan(A_discrete, B_discrete, C, x)
        
        # Residual connection
        y = y + self.D.unsqueeze(0).unsqueeze(0) * x
        
        return y
    
    def _parallel_scan(self, A: torch.Tensor, B: torch.Tensor, 
                      C: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
        """Implementación de parallel scan optimizada para hardware local"""
        B, L, D, d_state = A.shape
        
        # Estado inicial
        h = torch.zeros(B, D, d_state, device=x.device, dtype=x.dtype)
        outputs = []
        
        # Procesamiento secuencial optimizado para memoria
        for i in range(L):
            # Actualización de estado: h = A * h + B * x
            h = A[:, i] * h + B[:, i] * x[:, i].unsqueeze(-1)
            # Salida: y = C * h
            y = torch.sum(C[:, i] * h, dim=-1)
            outputs.append(y)
        
        return torch.stack(outputs, dim=1)  # (B, L, D)

class NonTransformerAnalysisEngine:
    """Motor de análisis basado en SSM para componentes de sistema"""
    
    def __init__(self, config: SSMAnalysisConfig):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Capas de análisis especializadas
        self.component_analyzer = StateSpaceLayer(config)
        self.temporal_analyzer = StateSpaceLayer(config)
        self.memory_analyzer = StateSpaceLayer(config)
        
        # Sistema de memoria recurrente
        self.memory_bank = {}
        self.processing_history = []
        
        # Optimizaciones para hardware local
        if config.memory_efficient:
            self._apply_memory_optimizations()
        
        # Métricas de eficiencia energética
        self.energy_monitor = EnergyEfficiencyMonitor()
        
    def _apply_memory_optimizations(self):
        """Aplicar optimizaciones de memoria para hardware local"""
        # Gradient checkpointing para reducir uso de memoria
        for layer in [self.component_analyzer, self.temporal_analyzer, self.memory_analyzer]:
            if hasattr(layer, 'gradient_checkpointing'):
                layer.gradient_checkpointing = True
        
        # Cuantización dinámica para inferencia
        if self.config.local_processing:
            self._apply_dynamic_quantization()
    
    def _apply_dynamic_quantization(self):
        """Cuantización dinámica para optimización local"""
        for layer in [self.component_analyzer, self.temporal_analyzer, self.memory_analyzer]:
            layer = torch.quantization.quantize_dynamic(
                layer, {torch.nn.Linear}, dtype=torch.qint8
            )
    
    async def analyze_components(self, components: List[Dict]) -> Dict:
        """Análisis principal de componentes usando SSM"""
        analysis_results = {
            "component_analysis": {},
            "temporal_patterns": {},
            "memory_states": {},
            "performance_metrics": {},
            "energy_consumption": {}
        }
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Análisis paralelo de componentes
            component_futures = []
            for component in components:
                future = executor.submit(self._analyze_single_component, component)
                component_futures.append((component['id'], future))
            
            # Recolección de resultados
            for component_id, future in component_futures:
                result = await asyncio.wrap_future(future)
                analysis_results["component_analysis"][component_id] = result
        
        # Análisis temporal agregado
        temporal_data = self._extract_temporal_features(components)
        analysis_results["temporal_patterns"] = self._analyze_temporal_patterns(temporal_data)
        
        # Análisis de estados de memoria
        memory_states = self._extract_memory_states()
        analysis_results["memory_states"] = self._analyze_memory_efficiency(memory_states)
        
        # Métricas de rendimiento
        analysis_results["performance_metrics"] = self._calculate_performance_metrics()
        
        # Consumo energético
        analysis_results["energy_consumption"] = self.energy_monitor.get_consumption_report()
        
        return analysis_results
    
    def _analyze_single_component(self, component: Dict) -> Dict:
        """Análisis individual de componente usando SSM"""
        self.energy_monitor.start_measurement()
        
        # Preparación de datos
        component_data = self._prepare_component_data(component)
        
        # Análisis con SSM
        with torch.no_grad():
            # Análisis de componente
            component_features = self.component_analyzer(component_data)
            
            # Análisis temporal
            temporal_features = self.temporal_analyzer(component_data)
            
            # Análisis de memoria
            memory_features = self.memory_analyzer(component_data)
        
        # Procesamiento de resultados
        results = {
            "component_health": self._evaluate_component_health(component_features),
            "temporal_behavior": self._evaluate_temporal_behavior(temporal_features),
            "memory_usage": self._evaluate_memory_usage(memory_features),
            "optimization_suggestions": self._generate_optimization_suggestions(
                component_features, temporal_features, memory_features
            )
        }
        
        self.energy_monitor.end_measurement()
        return results
    
    def _prepare_component_data(self, component: Dict) -> torch.Tensor:
        """Preparación de datos de componente para SSM"""
        # Extracción de características
        features = []
        
        # Métricas de rendimiento
        if 'performance' in component:
            perf_data = component['performance']
            features.extend([
                perf_data.get('cpu_usage', 0.0),
                perf_data.get('memory_usage', 0.0),
                perf_data.get('latency', 0.0),
                perf_data.get('throughput', 0.0)
            ])
        
        # Estado del sistema
        if 'system_state' in component:
            state_data = component['system_state']
            features.extend([
                state_data.get('temperature', 0.0),
                state_data.get('power_consumption', 0.0),
                state_data.get('error_rate', 0.0)
            ])
        
        # Datos temporales
        if 'temporal_data' in component:
            temporal_data = component['temporal_data']
            features.extend(temporal_data[-self.config.d_model:])  # Últimas secuencias
        
        # Padding si necesario
        while len(features) < self.config.d_model:
            features.append(0.0)
        
        # Conversión a tensor
        tensor_data = torch.tensor(features[:self.config.d_model], dtype=torch.float32)
        return tensor_data.unsqueeze(0).unsqueeze(0)  # (1, 1, d_model)
    
    def _evaluate_component_health(self, features: torch.Tensor) -> Dict:
        """Evaluación de salud del componente"""
        feature_stats = features.squeeze().cpu().numpy()
        
        # Análisis estadístico
        health_score = np.mean(feature_stats)
        stability_score = 1.0 - np.std(feature_stats)
        
        # Detección de anomalías
        anomaly_threshold = np.percentile(feature_stats, 95)
        anomalies = (feature_stats > anomaly_threshold).sum()
        
        return {
            "health_score": float(health_score),
            "stability_score": float(stability_score),
            "anomaly_count": int(anomalies),
            "status": "healthy" if health_score > 0.7 else "degraded"
        }
    
    def _evaluate_temporal_behavior(self, features: torch.Tensor) -> Dict:
        """Evaluación de comportamiento temporal"""
        temporal_stats = features.squeeze().cpu().numpy()
        
        # Análisis de tendencias
        trend = np.polyfit(range(len(temporal_stats)), temporal_stats, 1)[0]
        
        # Periodicidad
        fft = np.fft.fft(temporal_stats)
        dominant_frequency = np.argmax(np.abs(fft[1:len(fft)//2])) + 1
        
        return {
            "trend": float(trend),
            "dominant_frequency": int(dominant_frequency),
            "periodicity_strength": float(np.max(np.abs(fft[1:len(fft)//2]))),
            "temporal_stability": float(1.0 - np.std(temporal_stats))
        }
    
    def _generate_optimization_suggestions(self, component_features, 
                                         temporal_features, memory_features) -> List[str]:
        """Generación de sugerencias de optimización"""
        suggestions = []
        
        # Análisis de componente
        comp_health = self._evaluate_component_health(component_features)
        if comp_health["health_score"] < 0.7:
            suggestions.append("Consider component maintenance or replacement")
        
        # Análisis temporal
        temp_behavior = self._evaluate_temporal_behavior(temporal_features)
        if temp_behavior["trend"] < -0.1:
            suggestions.append("Performance degradation detected, investigate root cause")
        
        # Análisis de memoria
        mem_usage = self._evaluate_memory_usage(memory_features)
        if mem_usage["efficiency_score"] < 0.6:
            suggestions.append("Memory optimization recommended")
        
        return suggestions

class EnergyEfficiencyMonitor:
    """Monitor de eficiencia energética para hardware local"""
    
    def __init__(self):
        self.measurements = []
        self.current_measurement = None
        
    def start_measurement(self):
        """Iniciar medición de consumo energético"""
        import time
        import psutil
        
        self.current_measurement = {
            "start_time": time.time(),
            "start_cpu": psutil.cpu_percent(),
            "start_memory": psutil.virtual_memory().percent
        }
        
        # GPU monitoring si está disponible
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            power = pynvml.nvmlDeviceGetPowerUsage(handle)
            self.current_measurement["start_gpu_power"] = power
        except:
            self.current_measurement["start_gpu_power"] = 0
    
    def end_measurement(self):
        """Finalizar medición y calcular consumo"""
        if not self.current_measurement:
            return
        
        import time
        import psutil
        
        end_time = time.time()
        duration = end_time - self.current_measurement["start_time"]
        
        measurement = {
            "duration": duration,
            "avg_cpu": (self.current_measurement["start_cpu"] + psutil.cpu_percent()) / 2,
            "avg_memory": (self.current_measurement["start_memory"] + 
                          psutil.virtual_memory().percent) / 2,
            "estimated_power_watts": self._estimate_power_consumption()
        }
        
        self.measurements.append(measurement)
        self.current_measurement = None
    
    def _estimate_power_consumption(self) -> float:
        """Estimación de consumo energético"""
        # Modelo simplificado basado en uso de CPU/GPU
        base_power = 50  # Watts base del sistema
        
        if self.current_measurement:
            cpu_power = self.current_measurement["start_cpu"] * 0.5  # CPU factor
            gpu_power = self.current_measurement.get("start_gpu_power", 0) / 1000  # mW to W
            
            return base_power + cpu_power + gpu_power
        
        return base_power
    
    def get_consumption_report(self) -> Dict:
        """Reporte de consumo energético"""
        if not self.measurements:
            return {"total_energy_wh": 0, "avg_power_w": 0, "efficiency_score": 1.0}
        
        total_energy = sum(m["estimated_power_watts"] * m["duration"] / 3600 
                          for m in self.measurements)  # Wh
        avg_power = np.mean([m["estimated_power_watts"] for m in self.measurements])
        
        # Score de eficiencia basado en comparación con Transformers
        transformer_baseline = 150  # Watts típicos para Transformer equivalente
        efficiency_score = min(1.0, transformer_baseline / avg_power) if avg_power > 0 else 1.0
        
        return {
            "total_energy_wh": float(total_energy),
            "avg_power_w": float(avg_power),
            "efficiency_score": float(efficiency_score),
            "measurements_count": len(self.measurements)
        }

```

#### **Recurrent Processing Module**

```python
# src/core/recurrent_processor.py
import torch
import numpy as np
from typing import Dict, List, Optional, Any
from collections import deque
import asyncio
import threading
import time

class RecurrentMemoryState:
    """Estado de memoria recurrente para análisis temporal"""
    
    def __init__(self, capacity: int = 1000, decay_factor: float = 0.95):
        self.capacity = capacity
        self.decay_factor = decay_factor
        self.memory_buffer = deque(maxlen=capacity)
        self.state_history = deque(maxlen=100)
        self.access_patterns = {}
        self.last_update = time.time()
        
    def update(self, new_state: torch.Tensor, metadata: Dict = None):
        """Actualizar estado de memoria con decaimiento temporal"""
        current_time = time.time()
        time_delta = current_time - self.last_update
        
        # Aplicar decaimiento temporal
        if self.memory_buffer:
            decay_weight = np.exp(-time_delta * (1 - self.decay_factor))
            for i, (state, meta) in enumerate(self.memory_buffer):
                if isinstance(state, torch.Tensor):
                    self.memory_buffer[i] = (state * decay_weight, meta)
        
        # Agregar nuevo estado
        self.memory_buffer.append((new_state.clone(), metadata or {}))
        self.state_history.append({
            "timestamp": current_time,
            "state_norm": float(torch.norm(new_state)),
        })
        
        # Actualizar patrones de acceso
        if metadata and 'component_id' in metadata:
            component_id = metadata['component_id']
            if component_id not in self.access_patterns:
                self.access_patterns[component_id] = {"access_count": 0, "last_accessed": current_time}
            self.access_patterns[component_id]["access_count"] += 1
            self.access_patterns[component_id]["last_accessed"] = current_time
        
        self.last_update = current_time
    
    def get_memory_snapshot(self) -> List[Dict]:
        """Obtener snapshot de la memoria"""
        snapshot = []
        for state, meta in self.memory_buffer:
            snapshot.append({
                "state_norm": float(torch.norm(state)),
                "metadata": meta
            })
        return snapshot
    
    def get_access_patterns(self) -> Dict:
        """Obtener patrones de acceso a la memoria"""
        return self.access_patterns
    
    def decay_memory(self):
        """Decaer la memoria con el tiempo"""
        current_time = time.time()
        time_delta = current_time - self.last_update
        
        if self.memory_buffer:
            decay_weight = np.exp(-time_delta * (1 - self.decay_factor))
            for i, (state, meta) in enumerate(self.memory_buffer):
                if isinstance(state, torch.Tensor):
                    self.memory_buffer[i] = (state * decay_weight, meta)
        
        self.last_update = current_time

class RecurrentProcessor:
    """Procesador recurrente para análisis temporal"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.memory_state = RecurrentMemoryState(
            capacity=config.get('memory_capacity', 1000),
            decay_factor=config.get('memory_decay_factor', 0.95)
        )
        self.lock = threading.Lock()
    
    async def process_state(self, new_state: torch.Tensor, metadata: Dict = None):
        """Procesar nuevo estado y actualizar la memoria recurrente"""
        with self.lock:
            self.memory_state.update(new_state, metadata)
    
    def get_recurrent_state(self) -> RecurrentMemoryState:
        """Obtener el estado de memoria recurrente"""
        return self.memory_state
    
    def get_memory_snapshot(self) -> List[Dict]:
        """Obtener snapshot de la memoria"""
        with self.lock:
            return self.memory_state.get_memory_snapshot()
    
    def get_access_patterns(self) -> Dict:
        """Obtener patrones de acceso a la memoria"""
        with self.lock:
            return self.memory_state.get_access_patterns()
    
    def decay_memory(self):
        """Decaer la memoria con el tiempo"""
        with self.lock:
            self.memory_state.decay_memory()

```

#### **Advanced Gap Detection Module**

```python
# src/core/gap_detector.py
import torch
import numpy as np
from typing import Dict, List, Optional
from collections import deque
import asyncio
import threading
import time
from scipy.fft import fft

class TemporalAnomalyDetector:
    """Detector de anomalías temporales basado en FFT"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.data_buffer = deque(maxlen=config.get('buffer_size', 100))
        self.fft_results = deque(maxlen=config.get('fft_buffer_size', 30))
        self.lock = threading.Lock()
    
    def update_data(self, new_value: float):
        """Actualizar el buffer de datos"""
        with self.lock:
            self.data_buffer.append(new_value)
            if len(self.data_buffer) == self.data_buffer.maxlen:
                self._calculate_fft()
    
    def _calculate_fft(self):
        """Calcular la FFT de los datos en el buffer"""
        with self.lock:
            data = np.array(self.data_buffer)
            fft_result = fft(data)
            self.fft_results.append(np.abs(fft_result[:len(fft_result)//2]))  # Solo la mitad del espectro
    
    def detect_anomalies(self) -> List[Dict]:
        """Detectar anomalías en los resultados de la FFT"""
        with self.lock:
            if len(self.fft_results) < self.config.get('min_fft_samples', 10):
                return []
            
            anomalies = []
            
            # Calcular la media y la desviación estándar de los resultados de la FFT
            fft_matrix = np.array(list(self.fft_results))
            mean_fft = np.mean(fft_matrix, axis=0)
            std_fft = np.std(fft_matrix, axis=0)
            
            # Identificar anomalías como valores que se desvían significativamente de la media
            threshold = self.config.get('anomaly_threshold', 2.0)  # Multiplicador de la desviación estándar
            last_fft = fft_matrix[-1]
            
            for i, value in enumerate(last_fft):
                if std_fft[i] > 0 and abs(value - mean_fft[i]) > threshold * std_fft[i]:
                    anomalies.append({
                        "frequency": i,
                        "value": float(value),
                        "mean": float(mean_fft[i]),
                        "std": float(std_fft[i])
                    })
            
            return anomalies
    
    def get_fft_results(self) -> List[np.ndarray]:
        """Obtener los resultados de la FFT"""
        return list(self.fft_results)

class AdvancedGapDetector:
    """Detector avanzado de gaps basado en análisis temporal"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.temporal_anomaly_detector = TemporalAnomalyDetector(config.get('temporal_anomaly_config', {}))
        self.state_buffer = deque(maxlen=config.get('state_buffer_size', 50))
        self.gap_history = deque(maxlen=config.get('gap_history_size', 20))
        self.lock = threading.Lock()
    
    async def process_state(self, new_state: torch.Tensor, metadata: Dict = None):
        """Procesar nuevo estado y detectar gaps"""
        with self.lock:
            self.state_buffer.append((new_state.clone(), metadata or {}))
            self.temporal_anomaly_detector.update_data(float(torch.norm(new_state)))
            
            # Detectar anomalías temporales
            anomalies = self.temporal_anomaly_detector.detect_anomalies()
            
            # Evaluar gaps basados en anomalías y cambios de estado
            gaps = self._evaluate_gaps(anomalies)
            self.gap_history.extend(gaps)
    
    def _evaluate_gaps(self, anomalies: List[Dict]) -> List[Dict]:
        """Evaluar gaps basados en anomalías y cambios de estado"""
        gaps = []
        
        if anomalies:
            # Identificar gaps basados en anomalías temporales
            for anomaly in anomalies:
                gaps.append({
                    "type": "temporal_anomaly",
                    "frequency": anomaly["frequency"],
                    "value": anomaly["value"],
                    "mean": anomaly["mean"],
                    "std": anomaly["std"],
                    "timestamp": time.time()
                })
        
        # Identificar gaps basados en cambios significativos de estado
        if len(self.state_buffer) > 1:
            last_state, last_metadata = self.state_buffer[-2]
            current_state, current_metadata = self.state_buffer[-1]
            
            state_diff = torch.norm(current_state - last_state).item()
            
            if state_diff > self.config.get('state_change_threshold', 1.0):
                gaps.append({
                    "type": "state_change",
                    "state_diff": state_diff,
                    "timestamp": time.time()
                })
        
        return gaps
    
    def get_gap_history(self) -> List[Dict]:
        """Obtener el historial de gaps"""
        return list(self.gap_history)
    
    def get_state_buffer(self) -> List[Dict]:
        """Obtener el buffer de estados"""
        return list(self.state_buffer)
    
    def get_fft_results(self) -> List[np.ndarray]:
        """Obtener los resultados de la FFT del detector de anomalías temporales"""
        return self.temporal_anomaly_detector.get_fft_results()

```

#### **Energy Efficiency Monitoring Module**

```python
# src/core/energy_monitor.py
import time
import psutil
import numpy as np
from typing import Dict

class EnergyEfficiencyMonitor:
    """Monitor de eficiencia energética para hardware local"""
    
    def __init__(self):
        self.measurements = []
        self.current_measurement = None
        
    def start_measurement(self):
        """Iniciar medición de consumo energético"""
        self.current_measurement = {
            "start_time": time.time(),
            "start_cpu": psutil.cpu_percent(),
            "start_memory": psutil.virtual_memory().percent
        }
        
        # GPU monitoring si está disponible
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            power = pynvml.nvmlDeviceGetPowerUsage(handle)
            self.current_measurement["start_gpu_power"] = power
        except:
            self.current_measurement["start_gpu_power"] = 0
    
    def end_measurement(self):
        """Finalizar medición y calcular consumo"""
        if not self.current_measurement:
            return
        
        end_time = time.time()
        duration = end_time - self.current_measurement["start_time"]
        
        measurement = {
            "duration": duration,
            "avg_cpu": (self.current_measurement["start_cpu"] + psutil.cpu_percent()) / 2,
            "avg_memory": (self.current_measurement["start_memory"] + 
                          psutil.virtual_memory().percent) / 2,
            "estimated_power_watts": self._estimate_power_consumption()
        }
        
        self.measurements.append(measurement)
        self.current_measurement = None
    
    def _estimate_power_consumption(self) -> float:
        """Estimación de consumo energético"""
        # Modelo simplificado basado en uso de CPU/GPU
        base_power = 50  # Watts base del sistema
        
        if self.current_measurement:
            cpu_power = self.current_measurement["start_cpu"] * 0.5  # CPU factor
            gpu_power = self.current_measurement.get("start
