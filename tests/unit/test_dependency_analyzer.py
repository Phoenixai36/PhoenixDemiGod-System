"""
Unit tests for Dependency Analyzer

Tests the dependency analysis functionality including dependency mapping,
conflict detection, and relationship validation.
"""

import pytest
from unittest.mock import Mock, patch

from src.phoenix_system_review.analysis.dependency_analyzer import (
    DependencyAnalyzer,
    DependencyAnalysisResult,
    Dependency,
    DependencyGraph,
    DependencyType,
    DependencyStatus
)
from src.phoenix_system_review.models.data_models import Component, ComponentCategory, ComponentStatus


class TestDependencyAnalyzer:
    """Test cases for DependencyAnalyzer class"""
    
    @pytest.fixture
    def dependency_analyzer(self):
        """Create DependencyAnalyzer instance for testing"""
        return DependencyAnalyzer()
    
    @pytest.fixture
    def sample_components(self):
        """Create sample components for testing"""
        return [
            Component(
                name="NCA Toolkit",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/api/nca_toolkit.py",
                status=ComponentStatus.OPERATIONAL,
                description="Multimedia processing API"
            ),
            Component(
                name="PostgreSQL Database",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/db/postgres.py",
                status=ComponentStatus.OPERATIONAL,
                description="Primary database"
            ),
            Component(
                name="Minio Storage",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/storage/minio.py",
                status=ComponentStatus.OPERATIONAL,
                description="S3-compatible storage"
            ),
            Component(
                name="Affiliate Marketing",
                category=ComponentCategory.MONETIZATION,
                path="/monetization/affiliate.py",
                status=ComponentStatus.OPERATIONAL,
                description="Affiliate program management"
            ),
            Component(
                name="VS Code Integration",
                category=ComponentCategory.AUTOMATION,
                path="/.vscode/tasks.json",
                status=ComponentStatus.OPERATIONAL,
                description="IDE integration"
            )
        ]
    
    @pytest.fixture
    def components_with_explicit_deps(self):
        """Create components with explicit dependencies"""
        return [
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
            )
        ]
    
    def test_analyzer_initialization(self, dependency_analyzer):
        """Test dependency analyzer initialization"""
        assert dependency_analyzer is not None
        assert dependency_analyzer.known_dependencies is not None
        assert len(dependency_analyzer.known_dependencies) > 0
        
        # Check that known dependencies include Phoenix Hydra patterns
        assert "nca_toolkit" in dependency_analyzer.known_dependencies
        assert "grafana" in dependency_analyzer.known_dependencies
        assert "affiliate_marketing" in dependency_analyzer.known_dependencies
    
    def test_analyze_dependencies_empty_list(self, dependency_analyzer):
        """Test dependency analysis with empty component list"""
        result = dependency_analyzer.analyze_dependencies([])
        
        assert isinstance(result, DependencyAnalysisResult)
        assert len(result.dependency_graph.components) == 0
        assert len(result.dependency_graph.dependencies) == 0
        assert len(result.circular_dependencies) == 0
        assert len(result.missing_dependencies) == 0
        assert result.overall_dependency_health == 0.0
    
    def test_analyze_dependencies_basic(self, dependency_analyzer, sample_components):
        """Test basic dependency analysis"""
        result = dependency_analyzer.analyze_dependencies(sample_components)
        
        assert isinstance(result, DependencyAnalysisResult)
        assert len(result.dependency_graph.components) == len(sample_components)
        assert isinstance(result.overall_dependency_health, float)
        assert 0.0 <= result.overall_dependency_health <= 1.0
        assert isinstance(result.component_dependency_scores, dict)
    
    def test_build_dependency_graph(self, dependency_analyzer, sample_components):
        """Test dependency graph building"""
        graph = dependency_analyzer._build_dependency_graph(sample_components)
        
        assert isinstance(graph, DependencyGraph)
        assert len(graph.components) == len(sample_components)
        
        # Check that components are properly indexed
        for component in sample_components:
            assert component.name in graph.components
            assert graph.components[component.name] == component
    
    def test_extract_explicit_dependencies(self, dependency_analyzer, components_with_explicit_deps):
        """Test extraction of explicit dependencies"""
        all_components = {comp.name: comp for comp in components_with_explicit_deps}
        nca_component = components_with_explicit_deps[0]  # NCA Toolkit with dependencies
        
        dependencies = dependency_analyzer._extract_component_dependencies(nca_component, all_components)
        
        assert len(dependencies) >= 2  # At least the explicit dependencies
        
        # Check explicit dependencies are found
        explicit_targets = [dep.target for dep in dependencies if dep.dependency_type == DependencyType.REQUIRED]
        assert "PostgreSQL Database" in explicit_targets
        assert "Minio Storage" in explicit_targets
    
    def test_get_component_type(self, dependency_analyzer):
        """Test component type determination"""
        # Test infrastructure components
        nca_component = Component(
            name="NCA Toolkit API",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/api/nca.py"
        )
        assert dependency_analyzer._get_component_type(nca_component) == "nca_toolkit"
        
        db_component = Component(
            name="PostgreSQL Database",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/db/postgres.py"
        )
        assert dependency_analyzer._get_component_type(db_component) == "database"
        
        # Test monetization components
        affiliate_component = Component(
            name="Affiliate Marketing System",
            category=ComponentCategory.MONETIZATION,
            path="/monetization/affiliate.py"
        )
        assert dependency_analyzer._get_component_type(affiliate_component) == "affiliate_marketing"
        
        # Test automation components
        vscode_component = Component(
            name="VS Code Integration",
            category=ComponentCategory.AUTOMATION,
            path="/.vscode/tasks.json"
        )
        assert dependency_analyzer._get_component_type(vscode_component) == "vscode_integration"
        
        # Test unknown component
        unknown_component = Component(
            name="Unknown Service",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/unknown/service.py"
        )
        assert dependency_analyzer._get_component_type(unknown_component) == "unknown"
    
    def test_find_matching_components(self, dependency_analyzer, sample_components):
        """Test finding components matching dependency patterns"""
        all_components = {comp.name: comp for comp in sample_components}
        
        # Test pattern matching
        database_matches = dependency_analyzer._find_matching_components("database", all_components)
        assert len(database_matches) >= 1
        assert any("database" in comp.name.lower() for comp in database_matches)
        
        minio_matches = dependency_analyzer._find_matching_components("minio", all_components)
        assert len(minio_matches) >= 1
        assert any("minio" in comp.name.lower() for comp in minio_matches)
    
    def test_component_matches_pattern(self, dependency_analyzer):
        """Test component pattern matching"""
        database_component = Component(
            name="PostgreSQL Database",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/db/postgres.py"
        )
        
        # Test name-based matching
        assert dependency_analyzer._component_matches_pattern(database_component, "database")
        assert dependency_analyzer._component_matches_pattern(database_component, "postgres")
        
        # Test category-based matching
        assert dependency_analyzer._component_matches_pattern(database_component, "infrastructure")
        
        # Test path-based matching
        assert dependency_analyzer._component_matches_pattern(database_component, "db")
        
        # Test non-matching
        assert not dependency_analyzer._component_matches_pattern(database_component, "redis")
    
    def test_determine_dependency_status(self, dependency_analyzer):
        """Test dependency status determination"""
        source_component = Component(
            name="Source",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/source.py",
            status=ComponentStatus.OPERATIONAL
        )
        
        # Test operational target
        operational_target = Component(
            name="Target",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/target.py",
            status=ComponentStatus.OPERATIONAL
        )
        status = dependency_analyzer._determine_dependency_status(source_component, operational_target)
        assert status == DependencyStatus.SATISFIED
        
        # Test degraded target
        degraded_target = Component(
            name="Target",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/target.py",
            status=ComponentStatus.DEGRADED
        )
        status = dependency_analyzer._determine_dependency_status(source_component, degraded_target)
        assert status == DependencyStatus.DEGRADED
        
        # Test failed target
        failed_target = Component(
            name="Target",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/target.py",
            status=ComponentStatus.FAILED
        )
        status = dependency_analyzer._determine_dependency_status(source_component, failed_target)
        assert status == DependencyStatus.MISSING
    
    def test_detect_circular_dependencies(self, dependency_analyzer):
        """Test circular dependency detection"""
        # Create components with circular dependencies
        components = [
            Component(name="A", category=ComponentCategory.INFRASTRUCTURE, path="/a.py", dependencies=["B"]),
            Component(name="B", category=ComponentCategory.INFRASTRUCTURE, path="/b.py", dependencies=["C"]),
            Component(name="C", category=ComponentCategory.INFRASTRUCTURE, path="/c.py", dependencies=["A"])
        ]
        
        graph = dependency_analyzer._build_dependency_graph(components)
        circular_deps = dependency_analyzer._detect_circular_dependencies(graph)
        
        # Should detect the A -> B -> C -> A cycle
        assert len(circular_deps) > 0
        
        # Check that the cycle contains all three components
        if circular_deps:
            cycle = circular_deps[0]
            assert len(set(cycle)) >= 3  # At least 3 unique components in cycle
    
    def test_find_missing_dependencies(self, dependency_analyzer):
        """Test missing dependency detection"""
        # Create components where one has a dependency on a non-existent component
        components = [
            Component(
                name="Component A",
                category=ComponentCategory.INFRASTRUCTURE,
                path="/a.py",
                dependencies=["Non-existent Component"]
            )
        ]
        
        result = dependency_analyzer.analyze_dependencies(components)
        
        # Should detect missing dependencies
        assert len(result.missing_dependencies) > 0
    
    def test_is_layer_violation(self, dependency_analyzer):
        """Test layer violation detection"""
        # Infrastructure component (should not depend on higher layers)
        infra_component = Component(
            name="Database",
            category=ComponentCategory.INFRASTRUCTURE,
            path="/db.py"
        )
        
        # Monetization component
        monetization_component = Component(
            name="Affiliate System",
            category=ComponentCategory.MONETIZATION,
            path="/affiliate.py"
        )
        
        # Test violation: infrastructure depending on monetization
        assert dependency_analyzer._is_layer_violation(infra_component, monetization_component)
        
        # Test allowed: monetization depending on infrastructure
        assert not dependency_analyzer._is_layer_violation(monetization_component, infra_component)
    
    def test_calculate_dependency_scores(self, dependency_analyzer, sample_components):
        """Test dependency score calculation"""
        graph = dependency_analyzer._build_dependency_graph(sample_components)
        missing_deps = []
        conflicting_deps = []
        
        scores = dependency_analyzer._calculate_dependency_scores(graph, missing_deps, conflicting_deps)
        
        assert isinstance(scores, dict)
        assert len(scores) == len(sample_components)
        
        # All scores should be between 0.0 and 1.0
        for component_name, score in scores.items():
            assert 0.0 <= score <= 1.0
            assert isinstance(score, float)
    
    def test_calculate_overall_dependency_health(self, dependency_analyzer):
        """Test overall dependency health calculation"""
        component_scores = {"A": 0.8, "B": 0.9, "C": 0.7}
        circular_deps = []
        missing_deps = []
        conflicting_deps = []
        
        health = dependency_analyzer._calculate_overall_dependency_health(
            component_scores, circular_deps, missing_deps, conflicting_deps
        )
        
        assert isinstance(health, float)
        assert 0.0 <= health <= 1.0
        
        # With good scores and no issues, health should be high
        assert health > 0.7
    
    def test_calculate_overall_dependency_health_with_issues(self, dependency_analyzer):
        """Test overall dependency health calculation with issues"""
        component_scores = {"A": 0.8, "B": 0.9, "C": 0.7}
        circular_deps = [["A", "B", "A"]]  # One circular dependency
        missing_deps = [Mock()]  # One missing dependency
        conflicting_deps = [(Mock(), Mock())]  # One conflict
        
        health = dependency_analyzer._calculate_overall_dependency_health(
            component_scores, circular_deps, missing_deps, conflicting_deps
        )
        
        assert isinstance(health, float)
        assert 0.0 <= health <= 1.0
        
        # With issues, health should be lower
        health_without_issues = dependency_analyzer._calculate_overall_dependency_health(
            component_scores, [], [], []
        )
        assert health < health_without_issues
    
    def test_get_dependency_recommendations(self, dependency_analyzer):
        """Test dependency recommendation generation"""
        # Create analysis result with various issues
        analysis_result = DependencyAnalysisResult(
            dependency_graph=DependencyGraph(),
            circular_dependencies=[["A", "B", "A"]],
            missing_dependencies=[
                Dependency(
                    source="Component A",
                    target="Missing Component",
                    dependency_type=DependencyType.REQUIRED,
                    status=DependencyStatus.MISSING,
                    description="Test missing dependency"
                )
            ],
            conflicting_dependencies=[(Mock(), Mock())],
            component_dependency_scores={"A": 0.5, "B": 0.9}  # A has low score
        )
        
        recommendations = dependency_analyzer.get_dependency_recommendations(analysis_result)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Should have recommendations for each type of issue
        recommendation_text = " ".join(recommendations).lower()
        assert "circular" in recommendation_text
        assert "missing" in recommendation_text
        assert "conflict" in recommendation_text
    
    def test_generate_dependency_report(self, dependency_analyzer, sample_components):
        """Test dependency report generation"""
        result = dependency_analyzer.analyze_dependencies(sample_components)
        report = dependency_analyzer.generate_dependency_report(result)
        
        assert isinstance(report, dict)
        
        # Check required report fields
        required_fields = [
            "overall_health",
            "total_components",
            "total_dependencies",
            "circular_dependencies_count",
            "missing_dependencies_count",
            "conflicting_dependencies_count",
            "component_scores",
            "recommendations"
        ]
        
        for field in required_fields:
            assert field in report
        
        # Check data types
        assert isinstance(report["overall_health"], float)
        assert isinstance(report["total_components"], int)
        assert isinstance(report["component_scores"], dict)
        assert isinstance(report["recommendations"], list)
    
    def test_known_dependencies_structure(self, dependency_analyzer):
        """Test that known dependencies are properly structured"""
        known_deps = dependency_analyzer.known_dependencies
        
        assert isinstance(known_deps, dict)
        
        # Check structure of known dependencies
        for component_type, dependencies in known_deps.items():
            assert isinstance(component_type, str)
            assert isinstance(dependencies, list)
            
            for dep in dependencies:
                assert isinstance(dep, dict)
                assert "target_pattern" in dep
                assert "type" in dep
                assert "description" in dep
                
                # Validate dependency type
                assert dep["type"] in ["required", "optional"]
    
    def test_phoenix_hydra_specific_dependencies(self, dependency_analyzer):
        """Test Phoenix Hydra specific dependency patterns"""
        known_deps = dependency_analyzer.known_dependencies
        
        # Test NCA Toolkit dependencies
        nca_deps = known_deps.get("nca_toolkit", [])
        assert len(nca_deps) > 0
        
        # NCA Toolkit should depend on database and minio
        target_patterns = [dep["target_pattern"] for dep in nca_deps]
        assert "database" in target_patterns
        assert "minio" in target_patterns
        
        # Test Grafana dependencies
        grafana_deps = known_deps.get("grafana", [])
        assert len(grafana_deps) > 0
        
        # Grafana should depend on Prometheus
        grafana_targets = [dep["target_pattern"] for dep in grafana_deps]
        assert "prometheus" in grafana_targets
    
    def test_error_handling(self, dependency_analyzer):
        """Test error handling in dependency analysis"""
        # Test with invalid component data
        invalid_components = [None, "invalid", 123]
        
        # Should not crash and return valid result
        result = dependency_analyzer.analyze_dependencies(invalid_components)
        
        assert isinstance(result, DependencyAnalysisResult)
        assert result.overall_dependency_health == 0.0


if __name__ == "__main__":
    pytest.main([__file__])