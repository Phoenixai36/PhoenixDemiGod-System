"""
Integration tests for Dependency Analysis

Tests the integration between dependency analyzer and other system components.
"""

import pytest
from pathlib import Path
import tempfile

from src.phoenix_system_review.analysis.dependency_analyzer import DependencyAnalyzer
from src.phoenix_system_review.analysis.component_evaluator import ComponentEvaluator
from src.phoenix_system_review.discovery.file_scanner import FileSystemScanner
from src.phoenix_system_review.models.data_models import Component, ComponentCategory, ComponentStatus


class TestDependencyAnalysisIntegration:
    """Integration test cases for dependency analysis"""
    
    @pytest.fixture
    def temp_phoenix_project(self):
        """Create temporary Phoenix Hydra project structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create Phoenix Hydra project structure
            directories = [
                "src/phoenix_demigod",
                "src/agents",
                "src/core",
                "src/containers",
                "src/hooks",
                "src/integration",
                "src/metrics",
                "src/scheduler",
                "src/services",
                "infra/podman",
                "configs",
                "scripts",
                ".vscode"
            ]
            
            for directory in directories:
                (project_root / directory).mkdir(parents=True, exist_ok=True)
            
            # Create key files
            files = {
                "src/phoenix_demigod/nca_toolkit.py": "# NCA Toolkit implementation",
                "src/core/database.py": "# Database connection manager",
                "src/services/minio_service.py": "# Minio S3 service",
                "src/metrics/prometheus_client.py": "# Prometheus metrics",
                "src/integration/grafana_dashboard.py": "# Grafana integration",
                "src/agents/affiliate_marketing.py": "# Affiliate marketing agent",
                "src/scheduler/revenue_tracker.py": "# Revenue tracking scheduler",
                "scripts/deploy-badges.js": "// Badge deployment script",
                "scripts/complete-phoenix-deployment.ps1": "# PowerShell deployment",
                ".vscode/tasks.json": '{"version": "2.0.0", "tasks": []}',
                "infra/podman/compose.yaml": "version: '3.8'\nservices:\n  phoenix-core:\n    image: phoenix-hydra",
                "configs/phoenix-monetization.json": '{"affiliatePrograms": {"digitalOcean": {}}}',
                "pyproject.toml": "[tool.poetry]\nname = 'phoenix-hydra'"
            }
            
            for file_path, content in files.items():
                full_path = project_root / file_path
                full_path.write_text(content)
            
            yield str(project_root)
    
    @pytest.fixture
    def dependency_analyzer(self):
        """Create dependency analyzer instance"""
        return DependencyAnalyzer()
    
    @pytest.fixture
    def component_evaluator(self, temp_phoenix_project):
        """Create component evaluator instance"""
        return ComponentEvaluator(temp_phoenix_project)
    
    @pytest.fixture
    def file_scanner(self, temp_phoenix_project):
        """Create file scanner instance"""
        return FileSystemScanner(temp_phoenix_project)
    
    def test_dependency_analysis_with_discovered_components(self, dependency_analyzer, file_scanner):
        """Test dependency analysis using components discovered by file scanner"""
        # Discover components using file scanner
        inventory = file_scanner.scan_project_structure()
        
        # Convert discovered components to Component objects
        components = []
        for component in inventory.components:
            components.append(Component(
                name=component.name,
                category=component.category,
                path=component.path,
                status=ComponentStatus.OPERATIONAL if component.status == "active" else ComponentStatus.UNKNOWN,
                description=component.description
            ))
        
        # Analyze dependencies
        result = dependency_analyzer.analyze_dependencies(components)
        
        # Verify analysis results
        assert result is not None
        assert len(result.dependency_graph.components) > 0
        assert isinstance(result.overall_dependency_health, float)
        assert 0.0 <= result.overall_dependency_health <= 1.0
    
    def test_integration_with_component_evaluator(self, dependency_analyzer, component_evaluator):
        """Test integration between dependency analyzer and component evaluator"""
        # Create sample components
        components = [
            Component(
                name="NCA Toolkit",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/api/nca_toolkit.py",
                status=ComponentStatus.OPERATIONAL,
                dependencies=["PostgreSQL Database", "Minio Storage"]
            ),
            Component(
                name="PostgreSQL Database",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/db/postgres.py",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="Minio Storage",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/storage/minio.py",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="Affiliate Marketing",
                category=ComponentCategory.MONETIZATION,
                path="/monetization/affiliate.py",
                status=ComponentStatus.OPERATIONAL,
                dependencies=["PostgreSQL Database"]
            )
        ]
        
        # Evaluate components
        evaluations = component_evaluator.evaluate_components(components)
        
        # Analyze dependencies
        dependency_result = dependency_analyzer.analyze_dependencies(components)
        
        # Verify integration
        assert len(evaluations) == len(components)
        assert len(dependency_result.dependency_graph.components) == len(components)
        
        # Check that component names match between evaluations and dependency analysis
        evaluation_names = {eval.component.name for eval in evaluations}
        dependency_names = set(dependency_result.dependency_graph.components.keys())
        assert evaluation_names == dependency_names
    
    def test_phoenix_hydra_dependency_patterns(self, dependency_analyzer):
        """Test Phoenix Hydra specific dependency patterns"""
        # Create Phoenix Hydra components with realistic dependencies
        components = [
            Component(
                name="NCA Toolkit API",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/phoenix_demigod/nca_toolkit.py",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="PostgreSQL Database",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/core/database.py",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="Minio S3 Storage",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/services/minio_service.py",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="Prometheus Metrics",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/metrics/prometheus_client.py",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="Grafana Dashboard",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/src/integration/grafana_dashboard.py",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="Affiliate Marketing System",
                category=ComponentCategory.MONETIZATION,
                path="/src/agents/affiliate_marketing.py",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="Revenue Tracking",
                category=ComponentCategory.MONETIZATION,
                path="/src/scheduler/revenue_tracker.py",
                status=ComponentStatus.OPERATIONAL
            )
        ]
        
        # Analyze dependencies
        result = dependency_analyzer.analyze_dependencies(components)
        
        # Verify Phoenix Hydra specific patterns
        dependencies = result.dependency_graph.dependencies
        
        # Check that NCA Toolkit depends on database and storage
        nca_deps = [dep for dep in dependencies if dep.source == "NCA Toolkit API"]
        nca_targets = [dep.target for dep in nca_deps]
        
        # Should have inferred dependencies based on Phoenix Hydra patterns
        assert len(nca_deps) > 0
        
        # Check that Grafana depends on Prometheus
        grafana_deps = [dep for dep in dependencies if dep.source == "Grafana Dashboard"]
        if grafana_deps:
            grafana_targets = [dep.target for dep in grafana_deps]
            assert any("prometheus" in target.lower() for target in grafana_targets)
    
    def test_circular_dependency_detection_integration(self, dependency_analyzer):
        """Test circular dependency detection in realistic scenarios"""
        # Create components with potential circular dependencies
        components = [
            Component(
                name="Service A",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/services/service_a.py",
                status=ComponentStatus.OPERATIONAL,
                dependencies=["Service B"]
            ),
            Component(
                name="Service B",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/services/service_b.py",
                status=ComponentStatus.OPERATIONAL,
                dependencies=["Service C"]
            ),
            Component(
                name="Service C",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/services/service_c.py",
                status=ComponentStatus.OPERATIONAL,
                dependencies=["Service A"]  # Creates circular dependency
            )
        ]
        
        # Analyze dependencies
        result = dependency_analyzer.analyze_dependencies(components)
        
        # Should detect circular dependency
        assert len(result.circular_dependencies) > 0
        
        # Verify the circular dependency includes all three services
        if result.circular_dependencies:
            cycle = result.circular_dependencies[0]
            cycle_components = set(cycle)
            assert len(cycle_components) >= 3
    
    def test_layer_violation_detection(self, dependency_analyzer):
        """Test detection of architectural layer violations"""
        # Create components that violate Phoenix Hydra layering
        components = [
            Component(
                name="Database Service",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/infrastructure/database.py",
                status=ComponentStatus.OPERATIONAL,
                dependencies=["Affiliate Marketing"]  # Violation: infra depending on monetization
            ),
            Component(
                name="Affiliate Marketing",
                category=ComponentCategory.MONETIZATION,
                path="/monetization/affiliate.py",
                status=ComponentStatus.OPERATIONAL
            )
        ]
        
        # Analyze dependencies
        result = dependency_analyzer.analyze_dependencies(components)
        
        # Should detect layer violation
        assert len(result.dependency_violations) > 0
        
        # Verify violation message mentions layer violation
        violation_text = " ".join(result.dependency_violations).lower()
        assert "layer violation" in violation_text
    
    def test_dependency_health_calculation_integration(self, dependency_analyzer):
        """Test dependency health calculation with various scenarios"""
        # Scenario 1: Healthy dependencies
        healthy_components = [
            Component(
                name="API Gateway",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/api/gateway.py",
                status=ComponentStatus.OPERATIONAL,
                dependencies=["Database"]
            ),
            Component(
                name="Database",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/db/database.py",
                status=ComponentStatus.OPERATIONAL
            )
        ]
        
        healthy_result = dependency_analyzer.analyze_dependencies(healthy_components)
        
        # Scenario 2: Unhealthy dependencies
        unhealthy_components = [
            Component(
                name="API Gateway",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/api/gateway.py",
                status=ComponentStatus.OPERATIONAL,
                dependencies=["Missing Service", "Failed Service"]
            ),
            Component(
                name="Failed Service",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/services/failed.py",
                status=ComponentStatus.FAILED
            )
        ]
        
        unhealthy_result = dependency_analyzer.analyze_dependencies(unhealthy_components)
        
        # Healthy scenario should have better dependency health
        assert healthy_result.overall_dependency_health > unhealthy_result.overall_dependency_health
    
    def test_dependency_report_generation_integration(self, dependency_analyzer):
        """Test comprehensive dependency report generation"""
        # Create realistic Phoenix Hydra component set
        components = [
            Component(
                name="NCA Toolkit",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/nca/toolkit.py",
                status=ComponentStatus.OPERATIONAL,
                dependencies=["Database", "Storage"]
            ),
            Component(
                name="Database",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/db/postgres.py",
                status=ComponentStatus.OPERATIONAL
            ),
            Component(
                name="Storage",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/storage/minio.py",
                status=ComponentStatus.DEGRADED  # Degraded dependency
            ),
            Component(
                name="Affiliate System",
                category=ComponentCategory.MONETIZATION,
                path="/monetization/affiliate.py",
                status=ComponentStatus.OPERATIONAL,
                dependencies=["Database", "Missing Analytics"]  # Missing dependency
            )
        ]
        
        # Analyze and generate report
        result = dependency_analyzer.analyze_dependencies(components)
        report = dependency_analyzer.generate_dependency_report(result)
        
        # Verify comprehensive report structure
        assert isinstance(report, dict)
        
        required_fields = [
            "overall_health",
            "total_components",
            "total_dependencies",
            "missing_dependencies_count",
            "component_scores",
            "recommendations"
        ]
        
        for field in required_fields:
            assert field in report
        
        # Verify report contains meaningful data
        assert report["total_components"] == len(components)
        assert report["missing_dependencies_count"] > 0  # Should detect missing dependency
        assert len(report["recommendations"]) > 0  # Should have recommendations
        assert isinstance(report["component_scores"], dict)
        assert len(report["component_scores"]) == len(components)
    
    def test_performance_with_large_component_set(self, dependency_analyzer):
        """Test dependency analysis performance with larger component sets"""
        # Create a larger set of components
        components = []
        
        # Create 50 components with various dependency patterns
        for i in range(50):
            component = Component(
                name=f"Component_{i}",
                category=ComponentCategory.INFRASTRUCTURE if i < 25 else ComponentCategory.MONETIZATION,
                path=f"/components/component_{i}.py",
                status=ComponentStatus.OPERATIONAL,
                dependencies=[f"Component_{j}" for j in range(max(0, i-3), i) if j != i]  # Depend on previous 3
            )
            components.append(component)
        
        # Analyze dependencies (should complete in reasonable time)
        import time
        start_time = time.time()
        
        result = dependency_analyzer.analyze_dependencies(components)
        
        end_time = time.time()
        analysis_time = end_time - start_time
        
        # Verify analysis completed and results are reasonable
        assert result is not None
        assert len(result.dependency_graph.components) == 50
        assert analysis_time < 5.0  # Should complete within 5 seconds
        assert isinstance(result.overall_dependency_health, float)


if __name__ == "__main__":
    pytest.main([__file__])