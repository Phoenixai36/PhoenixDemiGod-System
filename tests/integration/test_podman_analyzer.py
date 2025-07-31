"""
Integration tests for Podman analyzer functionality.

Tests the Podman analyzer against real Phoenix Hydra infrastructure files
and validates the analysis results.
"""

import pytest
import tempfile
import yaml
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.phoenix_system_review.analysis.podman_analyzer import (
    PodmanAnalyzer, ContainerStatus, ContainerInfo, ComposeAnalysis, SystemdServiceInfo
)
from src.phoenix_system_review.models.data_models import Priority


class TestPodmanAnalyzer:
    """Test suite for PodmanAnalyzer"""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory with Phoenix Hydra structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create directory structure
            podman_dir = project_root / "infra" / "podman"
            systemd_dir = podman_dir / "systemd"
            podman_dir.mkdir(parents=True)
            systemd_dir.mkdir(parents=True)
            
            # Create sample compose file
            compose_content = {
                'name': 'phoenix-hydra',
                'services': {
                    'phoenix-core': {
                        'image': 'nginx:alpine',
                        'ports': ['8080:80'],
                        'environment': {
                            'MONETIZATION_MODE': 'enterprise'
                        },
                        'restart': 'unless-stopped',
                        'healthcheck': {
                            'test': ['CMD', 'curl', '-f', 'http://localhost/health'],
                            'interval': '30s',
                            'timeout': '10s',
                            'retries': 3
                        }
                    },
                    'nca-toolkit': {
                        'image': 'nginx:alpine',
                        'ports': ['8081:80'],
                        'restart': 'unless-stopped'
                    },
                    'revenue-db': {
                        'image': 'postgres:15',
                        'environment': {
                            'POSTGRES_DB': 'phoenix_revenue',
                            'POSTGRES_USER': 'phoenix'
                        },
                        'volumes': ['revenue_data:/var/lib/postgresql/data']
                    }
                },
                'volumes': {
                    'revenue_data': {}
                }
            }
            
            with open(podman_dir / "compose.yaml", 'w') as f:
                yaml.dump(compose_content, f)
            
            # Create sample systemd service file
            systemd_content = """[Unit]
Description=Phoenix Core Container
After=network-online.target

[Container]
Image=phoenixhydra/core:v8.7
Name=phoenix-core
Pod=phoenix-hydra
PublishPort=8080:8080
Restart=on-failure

[Install]
WantedBy=default.target
"""
            with open(systemd_dir / "phoenix-core.container", 'w') as f:
                f.write(systemd_content)
            
            yield project_root
    
    def test_analyzer_initialization(self, temp_project_dir):
        """Test PodmanAnalyzer initialization"""
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        
        assert analyzer.project_root == temp_project_dir
        assert analyzer.podman_dir == temp_project_dir / "infra" / "podman"
        assert analyzer.systemd_dir == temp_project_dir / "infra" / "podman" / "systemd"
        assert len(analyzer.expected_services) > 0
        assert "phoenix-core" in analyzer.expected_services
    
    def test_analyze_compose_files(self, temp_project_dir):
        """Test compose file analysis"""
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        analyses = analyzer.analyze_compose_files()
        
        # Should find at least one compose file
        assert len(analyses) >= 1
        
        # Find the main compose file analysis (not invalid ones)
        analysis = next((a for a in analyses if "compose.yaml" in a.file_path and "invalid" not in a.file_path), analyses[0])
        
        assert isinstance(analysis, ComposeAnalysis)
        assert "compose.yaml" in analysis.file_path
        assert len(analysis.services) == 3
        assert "phoenix-core" in analysis.services
        assert "nca-toolkit" in analysis.services
        assert "revenue-db" in analysis.services
        
        # Check service details
        phoenix_core = analysis.services["phoenix-core"]
        assert phoenix_core.name == "phoenix-core"
        assert phoenix_core.image == "nginx:alpine"
        assert "8080:80" in phoenix_core.ports
        assert phoenix_core.restart_policy == "unless-stopped"
        assert phoenix_core.health_check is not None
    
    def test_compose_validation_missing_services(self, temp_project_dir):
        """Test compose file validation with missing required services"""
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        analyses = analyzer.analyze_compose_files()
        
        # Find the main compose file analysis
        analysis = next((a for a in analyses if "compose.yaml" in a.file_path and "invalid" not in a.file_path), analyses[0])
        
        # Should have issues for missing required services
        missing_services = ["n8n-phoenix", "windmill-phoenix"]
        critical_issues = [issue for issue in analysis.issues if issue.severity == Priority.CRITICAL]
        
        assert len(critical_issues) >= len(missing_services)
        
        for service in missing_services:
            assert any(service in issue.description for issue in critical_issues)
    
    def test_compose_validation_missing_health_checks(self, temp_project_dir):
        """Test validation of missing health checks"""
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        analyses = analyzer.analyze_compose_files()
        
        # Find the main compose file analysis
        analysis = next((a for a in analyses if "compose.yaml" in a.file_path and "invalid" not in a.file_path), analyses[0])
        
        # nca-toolkit should have a medium priority issue for missing health check
        health_check_issues = [
            issue for issue in analysis.issues 
            if "health check" in issue.description.lower() and issue.severity == Priority.MEDIUM
        ]
        
        assert len(health_check_issues) > 0
        assert any("nca-toolkit" in issue.description for issue in health_check_issues)
    
    @patch('subprocess.run')
    def test_check_container_health_success(self, mock_run, temp_project_dir):
        """Test successful container health check"""
        # Mock successful podman ps output
        mock_containers = [
            {
                'Names': ['phoenix-core'],
                'State': 'running'
            },
            {
                'Names': ['nca-toolkit'],
                'State': 'stopped'
            },
            {
                'Names': ['revenue-db'],
                'State': 'failed'
            }
        ]
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_containers)
        )
        
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        container_status = analyzer.check_container_health()
        
        assert container_status['phoenix-core'] == ContainerStatus.RUNNING
        assert container_status['nca-toolkit'] == ContainerStatus.STOPPED
        assert container_status['revenue-db'] == ContainerStatus.FAILED
        
        mock_run.assert_called_once_with(
            ["podman", "ps", "-a", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30
        )
    
    @patch('subprocess.run')
    def test_check_container_health_failure(self, mock_run, temp_project_dir):
        """Test container health check when podman fails"""
        mock_run.side_effect = FileNotFoundError("podman not found")
        
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        container_status = analyzer.check_container_health()
        
        assert container_status == {}
    
    def test_analyze_systemd_services(self, temp_project_dir):
        """Test systemd service analysis"""
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        services = analyzer.analyze_systemd_services()
        
        assert len(services) == 1
        service = services[0]
        
        assert isinstance(service, SystemdServiceInfo)
        assert service.name == "phoenix-core"
        assert "phoenix-core.container" in service.file_path
        assert "Unit" in service.configuration
        assert "Container" in service.configuration
        assert "Install" in service.configuration
        
        # Check specific configuration values
        container_config = service.configuration["Container"]
        assert container_config["Image"] == "phoenixhydra/core:v8.7"
        assert container_config["Name"] == "phoenix-core"
        assert container_config["PublishPort"] == "8080:8080"
    
    @patch('subprocess.run')
    def test_validate_podman_installation_success(self, mock_run, temp_project_dir):
        """Test successful Podman installation validation"""
        # Mock successful podman and podman-compose commands
        mock_run.return_value = MagicMock(returncode=0, stdout="podman version 4.0.0")
        
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        is_valid, issues = analyzer.validate_podman_installation()
        
        assert is_valid
        assert len(issues) == 0
        
        # Should call both podman --version and podman-compose --version
        assert mock_run.call_count == 2
    
    @patch('subprocess.run')
    def test_validate_podman_installation_missing(self, mock_run, temp_project_dir):
        """Test Podman installation validation when podman is missing"""
        mock_run.side_effect = FileNotFoundError("podman not found")
        
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        is_valid, issues = analyzer.validate_podman_installation()
        
        assert not is_valid
        assert len(issues) > 0
        
        critical_issues = [issue for issue in issues if issue.severity == Priority.CRITICAL]
        assert len(critical_issues) > 0
        assert any("not found" in issue.description for issue in critical_issues)
    
    def test_generate_evaluation_result(self, temp_project_dir):
        """Test comprehensive evaluation result generation"""
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        
        with patch.object(analyzer, 'check_container_health') as mock_health, \
             patch.object(analyzer, 'validate_podman_installation') as mock_validate:
            
            # Mock container health check
            mock_health.return_value = {
                'phoenix-core': ContainerStatus.RUNNING,
                'nca-toolkit': ContainerStatus.STOPPED
            }
            
            # Mock Podman validation
            mock_validate.return_value = (True, [])
            
            result = analyzer.generate_evaluation_result()
            
            assert result.component.name == "podman_infrastructure"
            assert result.component.category == "infrastructure"
            assert result.completion_percentage > 0.0
            assert result.quality_score >= 0.0
            
            # Should have some criteria met
            assert len(result.criteria_met) > 0
            assert "compose_files_present" in result.criteria_met
            assert "containers_discoverable" in result.criteria_met
            assert "systemd_services_present" in result.criteria_met
            assert "podman_installation_valid" in result.criteria_met
            
            # Should have some criteria missing (due to missing services)
            assert len(result.criteria_missing) > 0
    
    def test_health_score_calculation(self, temp_project_dir):
        """Test health score calculation logic"""
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        
        # Test with no issues
        services = {"phoenix-core": ContainerInfo("phoenix-core", "nginx", ContainerStatus.RUNNING, [], [], {})}
        issues = []
        score = analyzer._calculate_compose_health_score(services, issues)
        assert score > 0.0
        
        # Test with critical issues
        critical_issue = MagicMock()
        critical_issue.severity = Priority.CRITICAL
        issues = [critical_issue]
        score_with_issues = analyzer._calculate_compose_health_score(services, issues)
        assert score_with_issues < score
    
    def test_missing_compose_files(self):
        """Test behavior when no compose files exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create empty project structure
            project_root = Path(temp_dir)
            podman_dir = project_root / "infra" / "podman"
            podman_dir.mkdir(parents=True)
            
            analyzer = PodmanAnalyzer(str(project_root))
            analyses = analyzer.analyze_compose_files()
            
            assert len(analyses) == 0
    
    def test_invalid_compose_file(self, temp_project_dir):
        """Test handling of invalid compose files"""
        # Create invalid YAML file
        podman_dir = temp_project_dir / "infra" / "podman"
        with open(podman_dir / "invalid-compose.yaml", 'w') as f:
            f.write("invalid: yaml: content: [")
        
        analyzer = PodmanAnalyzer(str(temp_project_dir))
        analyses = analyzer.analyze_compose_files()
        
        # Should have analysis for both valid and invalid files
        assert len(analyses) >= 2
        
        # Find the invalid file analysis
        invalid_analysis = next(
            (a for a in analyses if "invalid-compose.yaml" in a.file_path), 
            None
        )
        
        assert invalid_analysis is not None
        assert len(invalid_analysis.issues) > 0
        assert invalid_analysis.health_score == 0.0
        assert any("Failed to parse" in issue.description for issue in invalid_analysis.issues)


@pytest.mark.integration
class TestPodmanAnalyzerIntegration:
    """Integration tests that require actual Phoenix Hydra project structure"""
    
    def test_real_project_analysis(self):
        """Test analysis against real Phoenix Hydra project (if available)"""
        project_root = Path.cwd()
        
        # Skip if not in Phoenix Hydra project
        if not (project_root / "infra" / "podman").exists():
            pytest.skip("Not in Phoenix Hydra project directory")
        
        analyzer = PodmanAnalyzer(str(project_root))
        
        # Test compose file analysis
        analyses = analyzer.analyze_compose_files()
        assert len(analyses) > 0
        
        # Test systemd service analysis
        services = analyzer.analyze_systemd_services()
        # May be empty if systemd files don't exist
        
        # Test evaluation result generation
        result = analyzer.generate_evaluation_result()
        assert result.component.name == "podman_infrastructure"
        assert 0.0 <= result.completion_percentage <= 1.0
        assert 0.0 <= result.quality_score <= 1.0
    
    @patch('subprocess.run')
    def test_real_container_health_check(self, mock_run):
        """Test container health check with mocked podman command"""
        project_root = Path.cwd()
        
        if not (project_root / "infra" / "podman").exists():
            pytest.skip("Not in Phoenix Hydra project directory")
        
        # Mock podman ps output
        mock_containers = [
            {'Names': ['phoenix-hydra_phoenix-core_1'], 'State': 'running'},
            {'Names': ['phoenix-hydra_nca-toolkit_1'], 'State': 'running'},
            {'Names': ['phoenix-hydra_revenue-db_1'], 'State': 'running'}
        ]
        
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(mock_containers)
        )
        
        analyzer = PodmanAnalyzer(str(project_root))
        container_status = analyzer.check_container_health()
        
        assert len(container_status) == 3
        assert all(status == ContainerStatus.RUNNING for status in container_status.values())