"""
Integration tests for configuration parsing and validation
"""

import pytest
import tempfile
import json
import yaml
import toml
from pathlib import Path
from unittest.mock import Mock, patch

from phoenix_system_review.discovery.config_parser import ConfigurationParser
from phoenix_system_review.analysis.quality_assessor import QualityAssessor
from phoenix_system_review.core.config_validator import ConfigValidator
from phoenix_system_review.models.data_models import Component, ComponentCategory


class TestConfigurationParsingValidation:
    """Test integration between configuration parsing and validation"""
    
    @pytest.fixture
    def complex_configuration_set(self):
        """Create a complex set of configuration files for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Phoenix Hydra main configuration (YAML)
            phoenix_config = {
                'phoenix': {
                    'name': 'Phoenix Hydra System',
                    'version': '8.7.0',
                    'environment': 'production',
                    'debug': False,
                    'components': {
                        'core': {
                            'enabled': True,
                            'port': 8080,
                            'workers': 4
                        },
                        'nca_toolkit': {
                            'enabled': True,
                            'port': 8081,
                            'endpoints': 30
                        },
                        'system_review': {
                            'enabled': True,
                            'auto_run': True,
                            'schedule': '0 2 * * *'
                        }
                    }
                },
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'name': 'phoenix_hydra',
                    'ssl': True,
                    'pool_size': 10
                },
                'storage': {
                    'type': 'minio',
                    'endpoint': 'localhost:9000',
                    'bucket': 'phoenix-storage',
                    'ssl': False
                }
            }
            
            phoenix_file = temp_path / "phoenix.yaml"
            with open(phoenix_file, 'w') as f:
                yaml.dump(phoenix_config, f)
            
            # Monetization configuration (JSON)
            monetization_config = {
                'affiliate_programs': {
                    'digitalocean': {
                        'enabled': True,
                        'badge_deployed': True,
                        'tracking_id': 'DO-PHOENIX-2024',
                        'commission_rate': 0.25,
                        'last_updated': '2024-01-15'
                    },
                    'customgpt': {
                        'enabled': True,
                        'badge_deployed': False,
                        'api_key': 'cg_api_key_placeholder',
                        'integration_status': 'pending'
                    },
                    'cloudflare': {
                        'enabled': False,
                        'reason': 'not_applicable',
                        'review_date': '2024-06-01'
                    }
                },
                'grant_applications': {
                    'neotec_2024': {
                        'status': 'submitted',
                        'amount_requested': 400000,
                        'currency': 'EUR',
                        'deadline': '2024-12-31',
                        'completion_percentage': 95,
                        'documents': {
                            'business_plan': True,
                            'technical_specification': True,
                            'financial_projections': True,
                            'team_cv': False
                        }
                    },
                    'eic_accelerator': {
                        'status': 'planned',
                        'amount_requested': 2500000,
                        'currency': 'EUR',
                        'deadline': '2025-03-15',
                        'completion_percentage': 0,
                        'phase': 'preparation'
                    }
                },
                'revenue_tracking': {
                    'enabled': True,
                    'update_frequency': 'daily',
                    'targets': {
                        '2024': 50000,
                        '2025': 400000
                    },
                    'current_revenue': 12500
                }
            }
            
            monetization_file = temp_path / "monetization.json"
            with open(monetization_file, 'w') as f:
                json.dump(monetization_config, f, indent=2)
            
            # Infrastructure configuration (TOML)
            infra_config = """
[containers]
runtime = "podman"
rootless = true
auto_restart = true

[containers.phoenix_core]
image = "phoenix-hydra:latest"
ports = ["8080:8080"]
environment = ["DEBUG=false", "ENV=production"]
health_check = "/health"
restart_policy = "always"

[containers.n8n]
image = "n8nio/n8n:latest"
ports = ["5678:5678"]
environment = ["N8N_BASIC_AUTH_ACTIVE=true"]
volumes = ["n8n_data:/home/node/.n8n"]

[containers.windmill]
image = "ghcr.io/windmill-labs/windmill:main"
ports = ["8000:8000"]
environment = ["DATABASE_URL=postgresql://windmill:password@db:5432/windmill"]

[monitoring]
enabled = true
prometheus_port = 9090
grafana_port = 3000
retention_days = 30

[monitoring.alerts]
cpu_threshold = 80
memory_threshold = 90
disk_threshold = 85
response_time_threshold = 1000

[security]
ssl_enabled = true
cert_path = "/etc/ssl/certs/phoenix.crt"
key_path = "/etc/ssl/private/phoenix.key"
firewall_enabled = true
allowed_ips = ["127.0.0.1", "10.0.0.0/8"]
"""
            
            infra_file = temp_path / "infrastructure.toml"
            with open(infra_file, 'w') as f:
                f.write(infra_config)
            
            # Invalid configuration for error testing
            invalid_config = """
invalid: yaml: content: [
  - missing: closing: bracket
  - another: invalid: entry
"""
            
            invalid_file = temp_path / "invalid.yaml"
            with open(invalid_file, 'w') as f:
                f.write(invalid_config)
            
            yield {
                'temp_path': temp_path,
                'phoenix_file': str(phoenix_file),
                'monetization_file': str(monetization_file),
                'infra_file': str(infra_file),
                'invalid_file': str(invalid_file),
                'all_files': [str(phoenix_file), str(monetization_file), str(infra_file), str(invalid_file)]
            }
    
    def test_multi_format_configuration_parsing(self, complex_configuration_set):
        """Test parsing multiple configuration formats"""
        
        parser = ConfigurationParser()
        
        # Parse all configuration files
        config_files = complex_configuration_set['all_files'][:-1]  # Exclude invalid file
        parsed_configs = parser.parse_configurations(config_files)
        
        assert len(parsed_configs) == 3
        
        # Verify YAML parsing
        phoenix_config = parsed_configs[complex_configuration_set['phoenix_file']]
        assert phoenix_config is not None
        assert 'phoenix' in phoenix_config
        assert phoenix_config['phoenix']['name'] == 'Phoenix Hydra System'
        assert phoenix_config['phoenix']['version'] == '8.7.0'
        assert 'components' in phoenix_config['phoenix']
        
        # Verify JSON parsing
        monetization_config = parsed_configs[complex_configuration_set['monetization_file']]
        assert monetization_config is not None
        assert 'affiliate_programs' in monetization_config
        assert 'grant_applications' in monetization_config
        assert monetization_config['revenue_tracking']['enabled'] is True
        
        # Verify TOML parsing
        infra_config = parsed_configs[complex_configuration_set['infra_file']]
        assert infra_config is not None
        assert 'containers' in infra_config
        assert 'monitoring' in infra_config
        assert 'security' in infra_config
        assert infra_config['containers']['runtime'] == 'podman'
    
    def test_configuration_validation_integration(self, complex_configuration_set):
        """Test integration between parsing and validation"""
        
        parser = ConfigurationParser()
        quality_assessor = QualityAssessor()
        
        # Parse configurations
        config_files = complex_configuration_set['all_files']
        parsed_configs = parser.parse_configurations(config_files)
        
        # Validate configurations
        validation_issues = quality_assessor.validate_configuration_files(config_files)
        
        assert isinstance(validation_issues, list)
        
        # Should identify issues with invalid file
        invalid_file_issues = [issue for issue in validation_issues if 'invalid.yaml' in issue]
        assert len(invalid_file_issues) > 0
        
        # Valid configurations should have fewer or no issues
        valid_files = config_files[:-1]  # Exclude invalid file
        valid_file_issues = quality_assessor.validate_configuration_files(valid_files)
        
        # Valid files should have fewer issues than total issues
        assert len(valid_file_issues) <= len(validation_issues)
    
    def test_configuration_driven_component_creation(self, complex_configuration_set):
        """Test creating components based on parsed configurations"""
        
        parser = ConfigurationParser()
        
        # Parse configurations
        config_files = complex_configuration_set['all_files'][:-1]  # Exclude invalid
        parsed_configs = parser.parse_configurations(config_files)
        
        # Create components based on configurations
        components = []
        
        # Create components from Phoenix configuration
        phoenix_config = parsed_configs[complex_configuration_set['phoenix_file']]
        if phoenix_config and 'phoenix' in phoenix_config:
            phoenix_components = phoenix_config['phoenix'].get('components', {})
            
            for component_name, component_config in phoenix_components.items():
                if component_config.get('enabled', False):
                    component = Component(
                        name=f"phoenix-{component_name}",
                        category=ComponentCategory.INFRASTRUCTURE,
                        path=f"/src/{component_name}",
                        configuration=component_config,
                        status=ComponentStatus.OPERATIONAL if component_config.get('enabled') else ComponentStatus.UNKNOWN
                    )
                    components.append(component)
        
        # Create monetization components
        monetization_config = parsed_configs[complex_configuration_set['monetization_file']]
        if monetization_config:
            # Affiliate program components
            if 'affiliate_programs' in monetization_config:
                for program_name, program_config in monetization_config['affiliate_programs'].items():
                    if program_config.get('enabled', False):
                        component = Component(
                            name=f"affiliate-{program_name}",
                            category=ComponentCategory.MONETIZATION,
                            path=f"/monetization/affiliates/{program_name}",
                            configuration=program_config,
                            status=ComponentStatus.OPERATIONAL
                        )
                        components.append(component)
            
            # Grant application components
            if 'grant_applications' in monetization_config:
                for grant_name, grant_config in monetization_config['grant_applications'].items():
                    component = Component(
                        name=f"grant-{grant_name}",
                        category=ComponentCategory.MONETIZATION,
                        path=f"/monetization/grants/{grant_name}",
                        configuration=grant_config,
                        status=ComponentStatus.IN_PROGRESS if grant_config.get('status') == 'submitted' else ComponentStatus.PLANNED
                    )
                    components.append(component)
        
        # Create infrastructure components
        infra_config = parsed_configs[complex_configuration_set['infra_file']]
        if infra_config and 'containers' in infra_config:
            container_configs = {k: v for k, v in infra_config['containers'].items() if isinstance(v, dict)}
            
            for container_name, container_config in container_configs.items():
                component = Component(
                    name=f"container-{container_name}",
                    category=ComponentCategory.INFRASTRUCTURE,
                    path=f"/infra/containers/{container_name}",
                    configuration=container_config,
                    status=ComponentStatus.OPERATIONAL
                )
                components.append(component)
        
        # Verify components were created
        assert len(components) > 0
        
        # Verify component categories
        infrastructure_components = [c for c in components if c.category == ComponentCategory.INFRASTRUCTURE]
        monetization_components = [c for c in components if c.category == ComponentCategory.MONETIZATION]
        
        assert len(infrastructure_components) > 0
        assert len(monetization_components) > 0
        
        # Verify specific components
        component_names = [c.name for c in components]
        assert any('phoenix-core' in name for name in component_names)
        assert any('affiliate-digitalocean' in name for name in component_names)
        assert any('grant-neotec' in name for name in component_names)
    
    def test_configuration_dependency_extraction(self, complex_configuration_set):
        """Test extracting dependencies from configurations"""
        
        parser = ConfigurationParser()
        
        # Parse configurations
        config_files = complex_configuration_set['all_files'][:-1]
        parsed_configs = parser.parse_configurations(config_files)
        
        # Extract dependencies from configurations
        dependencies = {}
        
        # Extract from Phoenix configuration
        phoenix_config = parsed_configs[complex_configuration_set['phoenix_file']]
        if phoenix_config:
            # Phoenix core depends on database and storage
            dependencies['phoenix-core'] = ['database', 'storage']
            
            # NCA Toolkit depends on Phoenix core
            if phoenix_config.get('phoenix', {}).get('components', {}).get('nca_toolkit', {}).get('enabled'):
                dependencies['nca-toolkit'] = ['phoenix-core']
        
        # Extract from infrastructure configuration
        infra_config = parsed_configs[complex_configuration_set['infra_file']]
        if infra_config and 'containers' in infra_config:
            # Windmill depends on database
            if 'windmill' in infra_config['containers']:
                windmill_config = infra_config['containers']['windmill']
                if 'DATABASE_URL' in str(windmill_config.get('environment', [])):
                    dependencies['windmill'] = ['database']
            
            # Monitoring depends on all services
            if infra_config.get('monitoring', {}).get('enabled'):
                dependencies['monitoring'] = ['phoenix-core', 'n8n', 'windmill']
        
        # Extract from monetization configuration
        monetization_config = parsed_configs[complex_configuration_set['monetization_file']]
        if monetization_config:
            # Revenue tracking depends on affiliate programs
            if monetization_config.get('revenue_tracking', {}).get('enabled'):
                active_affiliates = [
                    name for name, config in monetization_config.get('affiliate_programs', {}).items()
                    if config.get('enabled', False)
                ]
                if active_affiliates:
                    dependencies['revenue-tracking'] = [f'affiliate-{name}' for name in active_affiliates]
        
        # Verify dependencies were extracted
        assert len(dependencies) > 0
        assert 'phoenix-core' in dependencies
        assert 'database' in dependencies['phoenix-core']
        assert 'storage' in dependencies['phoenix-core']
    
    def test_configuration_validation_rules(self, complex_configuration_set):
        """Test specific validation rules for Phoenix Hydra configurations"""
        
        parser = ConfigurationParser()
        validator = ConfigValidator()
        
        # Parse configurations
        config_files = complex_configuration_set['all_files'][:-1]
        parsed_configs = parser.parse_configurations(config_files)
        
        # Validate Phoenix configuration
        phoenix_config = parsed_configs[complex_configuration_set['phoenix_file']]
        if phoenix_config:
            # Validate required fields
            assert 'phoenix' in phoenix_config
            assert 'name' in phoenix_config['phoenix']
            assert 'version' in phoenix_config['phoenix']
            
            # Validate component configuration
            components = phoenix_config['phoenix'].get('components', {})
            for component_name, component_config in components.items():
                assert isinstance(component_config, dict)
                assert 'enabled' in component_config
                
                if component_config.get('enabled') and 'port' in component_config:
                    port = component_config['port']
                    assert isinstance(port, int)
                    assert 1 <= port <= 65535
        
        # Validate monetization configuration
        monetization_config = parsed_configs[complex_configuration_set['monetization_file']]
        if monetization_config:
            # Validate affiliate programs
            affiliate_programs = monetization_config.get('affiliate_programs', {})
            for program_name, program_config in affiliate_programs.items():
                assert isinstance(program_config, dict)
                assert 'enabled' in program_config
                
                if program_config.get('enabled'):
                    # Should have tracking information
                    assert 'badge_deployed' in program_config or 'tracking_id' in program_config
            
            # Validate grant applications
            grant_applications = monetization_config.get('grant_applications', {})
            for grant_name, grant_config in grant_applications.items():
                assert isinstance(grant_config, dict)
                assert 'status' in grant_config
                assert 'amount_requested' in grant_config
                assert 'currency' in grant_config
                
                # Validate completion percentage
                if 'completion_percentage' in grant_config:
                    completion = grant_config['completion_percentage']
                    assert isinstance(completion, (int, float))
                    assert 0 <= completion <= 100
        
        # Validate infrastructure configuration
        infra_config = parsed_configs[complex_configuration_set['infra_file']]
        if infra_config:
            # Validate container configuration
            containers = infra_config.get('containers', {})
            assert 'runtime' in containers
            assert containers['runtime'] in ['podman', 'docker']
            
            # Validate monitoring configuration
            monitoring = infra_config.get('monitoring', {})
            if monitoring.get('enabled'):
                assert 'prometheus_port' in monitoring
                assert 'grafana_port' in monitoring
                
                # Validate alert thresholds
                alerts = monitoring.get('alerts', {})
                for threshold_name, threshold_value in alerts.items():
                    if 'threshold' in threshold_name:
                        assert isinstance(threshold_value, (int, float))
                        assert 0 <= threshold_value <= 100
    
    def test_configuration_error_handling(self, complex_configuration_set):
        """Test error handling in configuration parsing and validation"""
        
        parser = ConfigurationParser()
        
        # Test parsing invalid configuration
        invalid_file = complex_configuration_set['invalid_file']
        invalid_config = parser.parse_configuration_file(invalid_file)
        
        # Should return None for invalid files
        assert invalid_config is None
        
        # Test parsing non-existent file
        nonexistent_config = parser.parse_configuration_file('/nonexistent/config.yaml')
        assert nonexistent_config is None
        
        # Test parsing with mixed valid/invalid files
        all_files = complex_configuration_set['all_files']
        parsed_configs = parser.parse_configurations(all_files)
        
        # Should parse valid files and skip invalid ones
        valid_configs = {k: v for k, v in parsed_configs.items() if v is not None}
        invalid_configs = {k: v for k, v in parsed_configs.items() if v is None}
        
        assert len(valid_configs) >= 3  # At least 3 valid configs
        assert len(invalid_configs) >= 1  # At least 1 invalid config
        
        # Verify that valid configurations are properly structured
        for file_path, config in valid_configs.items():
            assert isinstance(config, dict)
            assert len(config) > 0


if __name__ == '__main__':
    pytest.main([__file__])