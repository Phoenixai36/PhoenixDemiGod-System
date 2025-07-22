"""
Configuration management for PHOENIXxHYDRA system
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import json
import yaml
from pathlib import Path


@dataclass
class SystemConfig:
    """Main system configuration"""
    
    # Core system settings
    system_name: str = "PHOENIXxHYDRA"
    version: str = "0.1.0"
    debug_mode: bool = False
    log_level: str = "INFO"
    
    # Phoenix Core settings
    max_event_queue_size: int = 10000
    event_processing_timeout: float = 30.0
    system_health_check_interval: int = 60
    
    # HYDRA Head settings
    max_cells_per_head: int = 100
    cell_spawn_timeout: float = 10.0
    cell_health_check_interval: int = 30
    head_coordination_timeout: float = 60.0
    
    # P2P Network settings
    p2p_port: int = 8080
    p2p_discovery_interval: int = 30
    p2p_message_ttl: int = 300
    p2p_max_peers: int = 50
    p2p_encryption_enabled: bool = True
    
    # Genetic Evolution settings
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    selection_pressure: float = 0.3
    fitness_evaluation_interval: int = 300
    max_generations: int = 1000
    
    # Personality Matrix settings
    personality_base: int = 20
    mood_calculation_factors: List[str] = field(default_factory=lambda: [
        "recent_interactions", "performance_metrics", "genetic_traits"
    ])
    relationship_decay_rate: float = 0.01
    trust_threshold: float = 0.7
    
    # Agent settings
    nick_resonance_frequency_range: tuple = (150.0, 300.0)
    kai_chaos_test_interval: int = 3600
    thanatos_selection_interval: int = 1800
    niso_resource_allocation_interval: int = 600
    mape_response_timeout: float = 10.0
    
    # Security settings
    encryption_key_rotation_interval: int = 86400  # 24 hours
    max_failed_auth_attempts: int = 3
    security_scan_interval: int = 1800
    
    # Performance settings
    metrics_collection_interval: int = 60
    performance_optimization_interval: int = 3600
    auto_scaling_threshold: float = 0.8
    resource_allocation_strategy: str = "genetic_fitness"
    
    # Integration settings
    external_apis: Dict[str, str] = field(default_factory=dict)
    webhook_endpoints: List[str] = field(default_factory=list)
    monitoring_endpoints: Dict[str, str] = field(default_factory=dict)


@dataclass
class CellConfig:
    """Configuration for individual cells"""
    
    max_task_queue_size: int = 100
    task_processing_timeout: float = 30.0
    health_check_interval: int = 60
    communication_timeout: float = 10.0
    max_relationships: int = 50
    fitness_update_interval: int = 300
    gene_expression_rate: float = 1.0
    personality_stability: float = 0.8


@dataclass
class HydraHeadConfig:
    """Configuration for HYDRA heads"""
    
    # NeuroSymbolic Head
    neural_model_path: str = ""
    symbolic_reasoning_depth: int = 5
    qa_engine_timeout: float = 30.0
    
    # GeneticEvolution Head
    population_size: int = 1000
    elite_selection_ratio: float = 0.1
    diversity_maintenance_threshold: float = 0.3
    
    # MCPOrchestration Head
    container_runtime: str = "podman"  # podman or docker
    max_concurrent_deployments: int = 10
    deployment_timeout: float = 300.0
    
    # Personalization Head
    user_profile_cache_size: int = 1000
    personalization_model_update_interval: int = 3600
    feedback_processing_batch_size: int = 100
    
    # KnowledgeDetection Head
    knowledge_extraction_depth: int = 3
    pattern_recognition_threshold: float = 0.7
    audit_trail_retention_days: int = 30
    
    # MultimodalAnalysis Head
    supported_formats: List[str] = field(default_factory=lambda: [
        "text", "image", "audio", "video", "json", "csv"
    ])
    processing_pipeline_timeout: float = 120.0
    max_file_size_mb: int = 100
    
    # HybridStrategy Head
    strategy_evaluation_interval: int = 86400  # 24 hours
    roadmap_update_triggers: List[str] = field(default_factory=lambda: [
        "performance_milestone", "funding_event", "market_change"
    ])
    decision_confidence_threshold: float = 0.8


class ConfigurationManager:
    """Manages system configuration loading and validation"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/system_config.yaml"
        self.system_config = SystemConfig()
        self.cell_config = CellConfig()
        self.hydra_head_config = HydraHeadConfig()
    
    def load_configuration(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file"""
        path = Path(config_path or self.config_path)
        
        if not path.exists():
            # Create default configuration file
            self.save_default_configuration(str(path))
            return self.get_default_configuration()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() == '.json':
                    config_data = json.load(f)
                elif path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {path.suffix}")
            
            # Convert lists back to tuples where needed
            config_data = self._convert_lists_to_tuples(config_data)
            
            # Update configuration objects
            self._update_configs_from_dict(config_data)
            return config_data
            
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration from {path}: {e}")
    
    def save_configuration(self, config: Dict[str, Any], config_path: Optional[str] = None) -> bool:
        """Save configuration to file"""
        path = Path(config_path or self.config_path)
        
        try:
            # Ensure directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                if path.suffix.lower() == '.json':
                    json.dump(config, f, indent=2, default=str)
                elif path.suffix.lower() in ['.yaml', '.yml']:
                    # Convert tuples to lists for YAML compatibility
                    yaml_config = self._convert_tuples_to_lists(config)
                    yaml.dump(yaml_config, f, default_flow_style=False, indent=2)
                else:
                    raise ValueError(f"Unsupported config file format: {path.suffix}")
            
            return True
            
        except Exception as e:
            raise RuntimeError(f"Failed to save configuration to {path}: {e}")
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate system config
        if 'system' in config:
            system_config = config['system']
            
            if system_config.get('max_cells_per_head', 0) <= 0:
                errors.append("max_cells_per_head must be greater than 0")
            
            if system_config.get('max_cells_per_head', 0) > 1000:
                errors.append("max_cells_per_head should not exceed 1000 for performance reasons")
            
            if not (0.0 <= system_config.get('mutation_rate', 0.1) <= 1.0):
                errors.append("mutation_rate must be between 0.0 and 1.0")
            
            if not (0.0 <= system_config.get('crossover_rate', 0.8) <= 1.0):
                errors.append("crossover_rate must be between 0.0 and 1.0")
            
            if system_config.get('personality_base', 20) not in [10, 20, 30]:
                errors.append("personality_base should be 10, 20, or 30")
        
        # Validate P2P network config
        if 'p2p' in config:
            p2p_config = config['p2p']
            
            port = p2p_config.get('port', 8080)
            if not (1024 <= port <= 65535):
                errors.append("P2P port must be between 1024 and 65535")
            
            max_peers = p2p_config.get('max_peers', 50)
            if max_peers <= 0 or max_peers > 1000:
                errors.append("max_peers must be between 1 and 1000")
        
        # Validate agent configs
        if 'agents' in config:
            agents_config = config['agents']
            
            # Validate Nick agent
            if 'nick' in agents_config:
                freq_range = agents_config['nick'].get('resonance_frequency_range', (150.0, 300.0))
                if not isinstance(freq_range, (list, tuple)) or len(freq_range) != 2:
                    errors.append("Nick resonance_frequency_range must be a tuple/list of 2 values")
                elif freq_range[0] >= freq_range[1]:
                    errors.append("Nick resonance frequency range min must be less than max")
        
        return errors
    
    def get_default_configuration(self) -> Dict[str, Any]:
        """Get default system configuration"""
        return {
            "system": {
                "name": self.system_config.system_name,
                "version": self.system_config.version,
                "debug_mode": self.system_config.debug_mode,
                "log_level": self.system_config.log_level,
                "max_cells_per_head": self.system_config.max_cells_per_head,
                "mutation_rate": self.system_config.mutation_rate,
                "crossover_rate": self.system_config.crossover_rate,
                "personality_base": self.system_config.personality_base
            },
            "p2p": {
                "port": self.system_config.p2p_port,
                "discovery_interval": self.system_config.p2p_discovery_interval,
                "message_ttl": self.system_config.p2p_message_ttl,
                "max_peers": self.system_config.p2p_max_peers,
                "encryption_enabled": self.system_config.p2p_encryption_enabled
            },
            "agents": {
                "nick": {
                    "resonance_frequency_range": self.system_config.nick_resonance_frequency_range
                },
                "kai": {
                    "chaos_test_interval": self.system_config.kai_chaos_test_interval
                },
                "thanatos": {
                    "selection_interval": self.system_config.thanatos_selection_interval
                },
                "niso": {
                    "resource_allocation_interval": self.system_config.niso_resource_allocation_interval
                },
                "mape": {
                    "response_timeout": self.system_config.mape_response_timeout
                }
            },
            "hydra_heads": {
                "neurosymbolic": {
                    "symbolic_reasoning_depth": self.hydra_head_config.symbolic_reasoning_depth,
                    "qa_engine_timeout": self.hydra_head_config.qa_engine_timeout
                },
                "genetic_evolution": {
                    "population_size": self.hydra_head_config.population_size,
                    "elite_selection_ratio": self.hydra_head_config.elite_selection_ratio
                },
                "mcp_orchestration": {
                    "container_runtime": self.hydra_head_config.container_runtime,
                    "max_concurrent_deployments": self.hydra_head_config.max_concurrent_deployments
                },
                "personalization": {
                    "user_profile_cache_size": self.hydra_head_config.user_profile_cache_size,
                    "feedback_processing_batch_size": self.hydra_head_config.feedback_processing_batch_size
                },
                "knowledge_detection": {
                    "knowledge_extraction_depth": self.hydra_head_config.knowledge_extraction_depth,
                    "pattern_recognition_threshold": self.hydra_head_config.pattern_recognition_threshold
                },
                "multimodal_analysis": {
                    "supported_formats": self.hydra_head_config.supported_formats,
                    "max_file_size_mb": self.hydra_head_config.max_file_size_mb
                },
                "hybrid_strategy": {
                    "strategy_evaluation_interval": self.hydra_head_config.strategy_evaluation_interval,
                    "decision_confidence_threshold": self.hydra_head_config.decision_confidence_threshold
                }
            },
            "cells": {
                "max_task_queue_size": self.cell_config.max_task_queue_size,
                "task_processing_timeout": self.cell_config.task_processing_timeout,
                "health_check_interval": self.cell_config.health_check_interval,
                "max_relationships": self.cell_config.max_relationships
            }
        }
    
    def save_default_configuration(self, config_path: str) -> bool:
        """Save default configuration to file"""
        default_config = self.get_default_configuration()
        return self.save_configuration(default_config, config_path)
    
    def _update_configs_from_dict(self, config_data: Dict[str, Any]):
        """Update configuration objects from dictionary"""
        # Update system config
        if 'system' in config_data:
            system_data = config_data['system']
            for key, value in system_data.items():
                if hasattr(self.system_config, key):
                    setattr(self.system_config, key, value)
        
        # Update cell config
        if 'cells' in config_data:
            cell_data = config_data['cells']
            for key, value in cell_data.items():
                if hasattr(self.cell_config, key):
                    setattr(self.cell_config, key, value)
        
        # Update hydra head config
        if 'hydra_heads' in config_data:
            head_data = config_data['hydra_heads']
            for head_name, head_config in head_data.items():
                for key, value in head_config.items():
                    if hasattr(self.hydra_head_config, key):
                        setattr(self.hydra_head_config, key, value)
    
    def _convert_tuples_to_lists(self, data: Any) -> Any:
        """Convert tuples to lists recursively for YAML compatibility"""
        if isinstance(data, dict):
            return {key: self._convert_tuples_to_lists(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._convert_tuples_to_lists(item) for item in data]
        elif isinstance(data, tuple):
            return [self._convert_tuples_to_lists(item) for item in data]
        else:
            return data
    
    def _convert_lists_to_tuples(self, data: Any) -> Any:
        """Convert specific lists back to tuples where needed"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key == 'resonance_frequency_range' and isinstance(value, list) and len(value) == 2:
                    result[key] = tuple(value)
                else:
                    result[key] = self._convert_lists_to_tuples(value)
            return result
        elif isinstance(data, list):
            return [self._convert_lists_to_tuples(item) for item in data]
        else:
            return data