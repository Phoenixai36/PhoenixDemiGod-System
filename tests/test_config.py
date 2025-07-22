"""
Unit tests for configuration management
"""

import pytest
import tempfile
import json
import yaml
from pathlib import Path

from src.phoenixxhydra.core.config import (
    SystemConfig, CellConfig, HydraHeadConfig, ConfigurationManager
)


class TestSystemConfig:
    """Test SystemConfig data class"""
    
    def test_default_system_config(self):
        """Test default system configuration values"""
        config = SystemConfig()
        
        assert config.system_name == "PHOENIXxHYDRA"
        assert config.version == "0.1.0"
        assert config.debug_mode is False
        assert config.max_cells_per_head == 100
        assert config.mutation_rate == 0.1
        assert config.crossover_rate == 0.8
        assert config.personality_base == 20
        assert config.p2p_port == 8080
        assert config.p2p_encryption_enabled is True
    
    def test_custom_system_config(self):
        """Test custom system configuration values"""
        config = SystemConfig(
            system_name="TestSystem",
            max_cells_per_head=200,
            mutation_rate=0.2,
            debug_mode=True
        )
        
        assert config.system_name == "TestSystem"
        assert config.max_cells_per_head == 200
        assert config.mutation_rate == 0.2
        assert config.debug_mode is True


class TestCellConfig:
    """Test CellConfig data class"""
    
    def test_default_cell_config(self):
        """Test default cell configuration values"""
        config = CellConfig()
        
        assert config.max_task_queue_size == 100
        assert config.task_processing_timeout == 30.0
        assert config.health_check_interval == 60
        assert config.max_relationships == 50
        assert config.fitness_update_interval == 300
        assert config.personality_stability == 0.8


class TestHydraHeadConfig:
    """Test HydraHeadConfig data class"""
    
    def test_default_hydra_head_config(self):
        """Test default HYDRA head configuration values"""
        config = HydraHeadConfig()
        
        assert config.symbolic_reasoning_depth == 5
        assert config.population_size == 1000
        assert config.container_runtime == "podman"
        assert config.max_concurrent_deployments == 10
        assert config.user_profile_cache_size == 1000
        assert config.knowledge_extraction_depth == 3
        assert "text" in config.supported_formats
        assert "image" in config.supported_formats
        assert config.strategy_evaluation_interval == 86400


class TestConfigurationManager:
    """Test ConfigurationManager class"""
    
    def test_get_default_configuration(self):
        """Test getting default configuration"""
        manager = ConfigurationManager()
        config = manager.get_default_configuration()
        
        assert "system" in config
        assert "p2p" in config
        assert "agents" in config
        assert "hydra_heads" in config
        assert "cells" in config
        
        # Check system config
        assert config["system"]["name"] == "PHOENIXxHYDRA"
        assert config["system"]["max_cells_per_head"] == 100
        
        # Check P2P config
        assert config["p2p"]["port"] == 8080
        assert config["p2p"]["encryption_enabled"] is True
        
        # Check agents config
        assert "nick" in config["agents"]
        assert "kai" in config["agents"]
        assert "thanatos" in config["agents"]
        
        # Check HYDRA heads config
        assert len(config["hydra_heads"]) == 7
        assert "neurosymbolic" in config["hydra_heads"]
        assert "genetic_evolution" in config["hydra_heads"]
    
    def test_validate_configuration_valid(self):
        """Test configuration validation with valid config"""
        manager = ConfigurationManager()
        config = manager.get_default_configuration()
        
        errors = manager.validate_configuration(config)
        assert len(errors) == 0
    
    def test_validate_configuration_invalid(self):
        """Test configuration validation with invalid config"""
        manager = ConfigurationManager()
        
        invalid_config = {
            "system": {
                "max_cells_per_head": -1,  # Invalid: negative
                "mutation_rate": 1.5,      # Invalid: > 1.0
                "personality_base": 15     # Invalid: not in [10, 20, 30]
            },
            "p2p": {
                "port": 100,              # Invalid: < 1024
                "max_peers": -5           # Invalid: negative
            },
            "agents": {
                "nick": {
                    "resonance_frequency_range": [300.0, 150.0]  # Invalid: min > max
                }
            }
        }
        
        errors = manager.validate_configuration(invalid_config)
        assert len(errors) > 0
        
        # Check specific error messages
        error_messages = " ".join(errors)
        assert "max_cells_per_head must be greater than 0" in error_messages
        assert "mutation_rate must be between 0.0 and 1.0" in error_messages
        assert "personality_base should be 10, 20, or 30" in error_messages
        assert "P2P port must be between 1024 and 65535" in error_messages
    
    def test_save_and_load_json_configuration(self):
        """Test saving and loading JSON configuration"""
        manager = ConfigurationManager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            # Save default configuration
            default_config = manager.get_default_configuration()
            success = manager.save_configuration(default_config, config_path)
            assert success is True
            
            # Verify file exists and is valid JSON
            assert Path(config_path).exists()
            with open(config_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data["system"]["name"] == "PHOENIXxHYDRA"
            
            # Load configuration
            loaded_config = manager.load_configuration(config_path)
            assert loaded_config["system"]["name"] == "PHOENIXxHYDRA"
            assert loaded_config["p2p"]["port"] == 8080
            
        finally:
            # Cleanup
            Path(config_path).unlink(missing_ok=True)
    
    def test_save_and_load_yaml_configuration(self):
        """Test saving and loading YAML configuration"""
        manager = ConfigurationManager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = f.name
        
        try:
            # Save default configuration
            default_config = manager.get_default_configuration()
            success = manager.save_configuration(default_config, config_path)
            assert success is True
            
            # Verify file exists and is valid YAML
            assert Path(config_path).exists()
            with open(config_path, 'r') as f:
                loaded_data = yaml.safe_load(f)
            
            assert loaded_data["system"]["name"] == "PHOENIXxHYDRA"
            
            # Load configuration
            loaded_config = manager.load_configuration(config_path)
            assert loaded_config["system"]["name"] == "PHOENIXxHYDRA"
            assert loaded_config["agents"]["kai"]["chaos_test_interval"] == 3600
            
        finally:
            # Cleanup
            Path(config_path).unlink(missing_ok=True)
    
    def test_load_nonexistent_configuration(self):
        """Test loading configuration from nonexistent file creates default"""
        manager = ConfigurationManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "nonexistent_config.yaml"
            
            # Load from nonexistent file should create default
            loaded_config = manager.load_configuration(str(config_path))
            
            # Verify default config was returned
            assert loaded_config["system"]["name"] == "PHOENIXxHYDRA"
            
            # Verify file was created
            assert config_path.exists()
    
    def test_unsupported_file_format(self):
        """Test error handling for unsupported file formats"""
        manager = ConfigurationManager()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            config_path = f.name
        
        try:
            default_config = manager.get_default_configuration()
            
            # Should raise error for unsupported format
            with pytest.raises(RuntimeError, match="Unsupported config file format"):
                manager.save_configuration(default_config, config_path)
                
        finally:
            Path(config_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__])