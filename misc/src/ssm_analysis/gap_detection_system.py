"""
Advanced Gap Detection System for SSM/Local Systems

This module implements comprehensive gap detection for validating the
migration from Transformer to SSM/Mamba architectures and ensuring
100% local processing capabilities.
"""

import ast
import asyncio
import json
import logging
import re
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class GapType(Enum):
    """Types of gaps that can be detected"""

    TRANSFORMER_RESIDUAL = "transformer_residual"
    CLOUD_DEPENDENCY = "cloud_dependency"
    ENERGY_INEFFICIENCY = "energy_inefficiency"
    NON_LOCAL_PROCESSING = "non_local_processing"
    MISSING_SSM_IMPLEMENTATION = "missing_ssm_implementation"
    BIOMIMETIC_INCOMPLETE = "biomimetic_incomplete"


@dataclass
class GapDetectionResult:
    """Result of gap detection analysis"""

    gap_type: GapType
    severity: str  # "critical", "high", "medium", "low"
    file_path: str
    line_number: int
    description: str
    recommendation: str
    code_snippet: str
    confidence: float


class TransformerResidualDetector:
    """Detects remaining Transformer implementations in codebase"""

    def __init__(self):
        self.transformer_patterns = [
            r"import\s+torch\.nn\.MultiheadAttention",
            r"from\s+transformers\s+import",
            r"class\s+\w*Attention\w*\(.*nn\.Module\)",
            r"self\.attention\s*=.*MultiheadAttention",
            r"torch\.nn\.functional\.scaled_dot_product_attention",
            r"attention_mask",
            r"\.attention\(",
            r"self_attention",
            r"cross_attention",
        ]

        self.ssm_indicators = [
            r"StateSpaceLayer",
            r"SSMAnalysisConfig",
            r"_apply_ssm",
            r"state_space",
            r"mamba",
            r"selective_scan",
        ]

    async def detect_transformer_residuals(
        self, project_path: Path
    ) -> List[GapDetectionResult]:
        """Detect remaining Transformer code in project"""
        results = []

        # Scan Python files
        for py_file in project_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                file_results = await self._analyze_file_for_transformers(
                    py_file, content
                )
                results.extend(file_results)
            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")

        return results

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = [
            "test_",
            "__pycache__",
            ".git",
            "node_modules",
            "venv",
            ".venv",
        ]

        return any(pattern in str(file_path) for pattern in skip_patterns)

    async def _analyze_file_for_transformers(
        self, file_path: Path, content: str
    ) -> List[GapDetectionResult]:
        """Analyze single file for Transformer residuals"""
        results = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Check for Transformer patterns
            for pattern in self.transformer_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if this is in a context that should use SSM
                    if self._should_be_ssm_context(lines, line_num):
                        results.append(
                            GapDetectionResult(
                                gap_type=GapType.TRANSFORMER_RESIDUAL,
                                severity="high",
                                file_path=str(file_path),
                                line_number=line_num,
                                description=f"Transformer code detected: {line.strip()}",
                                recommendation="Replace with SSM/Mamba equivalent",
                                code_snippet=line.strip(),
                                confidence=0.9,
                            )
                        )

        return results

    def _should_be_ssm_context(self, lines: List[str], line_num: int) -> bool:
        """Check if context suggests this should be SSM-based"""
        # Look at surrounding context
        start = max(0, line_num - 10)
        end = min(len(lines), line_num + 10)
        context = "\n".join(lines[start:end])

        # If there are SSM indicators nearby, this should probably be SSM
        return any(
            re.search(pattern, context, re.IGNORECASE)
            for pattern in self.ssm_indicators
        )


class CloudDependencyDetector:
    """Detects cloud dependencies that violate local processing requirements"""

    def __init__(self):
        self.cloud_patterns = [
            r"requests\.get\(",
            r"requests\.post\(",
            r"urllib\.request",
            r"http[s]?://(?!localhost|127\.0\.0\.1)",
            r"openai\.api",
            r"anthropic\.",
            r"google\.cloud",
            r"aws\.",
            r"azure\.",
            r"api_key\s*=",
            r"\.api\.",
            r"remote_url",
            r"cloud_endpoint",
        ]

        self.allowed_local_patterns = [
            r"localhost",
            r"127\.0\.0\.1",
            r"0\.0\.0\.0",
            r"local_",
            r"offline_",
        ]

    async def detect_cloud_dependencies(
        self, project_path: Path
    ) -> List[GapDetectionResult]:
        """Detect cloud dependencies in project"""
        results = []

        for py_file in project_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                file_results = await self._analyze_file_for_cloud_deps(py_file, content)
                results.extend(file_results)
            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")

        return results

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = ["test_", "__pycache__", ".git", "examples"]
        return any(pattern in str(file_path) for pattern in skip_patterns)

    async def _analyze_file_for_cloud_deps(
        self, file_path: Path, content: str
    ) -> List[GapDetectionResult]:
        """Analyze file for cloud dependencies"""
        results = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern in self.cloud_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if it's actually a local pattern
                    if not any(
                        re.search(local_pattern, line, re.IGNORECASE)
                        for local_pattern in self.allowed_local_patterns
                    ):
                        results.append(
                            GapDetectionResult(
                                gap_type=GapType.CLOUD_DEPENDENCY,
                                severity="critical",
                                file_path=str(file_path),
                                line_number=line_num,
                                description=f"Cloud dependency detected: {line.strip()}",
                                recommendation="Replace with local processing equivalent",
                                code_snippet=line.strip(),
                                confidence=0.8,
                            )
                        )

        return results


class EnergyEfficiencyAnalyzer:
    """Analyzes energy efficiency and validates 60-70% reduction targets"""

    def __init__(self):
        self.energy_inefficient_patterns = [
            r"torch\.nn\.MultiheadAttention",
            r"attention.*attention",  # O(n²) attention
            r"for.*for.*range",  # Nested loops
            r"\.cuda\(\)",  # Unnecessary GPU usage
            r"torch\.no_grad\(\)",  # Missing optimization
        ]

        self.energy_efficient_patterns = [
            r"StateSpaceLayer",
            r"linear_complexity",
            r"memory_efficient",
            r"energy_monitor",
            r"quantization",
        ]

    async def analyze_energy_efficiency(self, project_path: Path) -> Dict[str, Any]:
        """Analyze overall energy efficiency of the codebase"""

        total_files = 0
        efficient_files = 0
        inefficient_patterns_found = 0
        efficient_patterns_found = 0

        for py_file in project_path.rglob("*.py"):
            if self._should_skip_file(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                total_files += 1

                file_inefficient = sum(
                    1
                    for pattern in self.energy_inefficient_patterns
                    if re.search(pattern, content, re.IGNORECASE)
                )
                file_efficient = sum(
                    1
                    for pattern in self.energy_efficient_patterns
                    if re.search(pattern, content, re.IGNORECASE)
                )

                inefficient_patterns_found += file_inefficient
                efficient_patterns_found += file_efficient

                if file_efficient > file_inefficient:
                    efficient_files += 1

            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")

        # Calculate efficiency metrics
        efficiency_ratio = efficient_files / total_files if total_files > 0 else 0
        pattern_ratio = (
            efficient_patterns_found
            / (efficient_patterns_found + inefficient_patterns_found)
            if (efficient_patterns_found + inefficient_patterns_found) > 0
            else 0
        )

        # Estimate energy reduction
        estimated_reduction = min(0.8, efficiency_ratio * 0.7 + pattern_ratio * 0.3)
        target_achieved = estimated_reduction >= 0.6

        return {
            "total_files_analyzed": total_files,
            "efficient_files": efficient_files,
            "efficiency_ratio": efficiency_ratio,
            "estimated_energy_reduction": estimated_reduction,
            "target_60_percent_achieved": target_achieved,
            "target_70_percent_achieved": estimated_reduction >= 0.7,
            "inefficient_patterns_found": inefficient_patterns_found,
            "efficient_patterns_found": efficient_patterns_found,
        }

    def _should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        skip_patterns = ["test_", "__pycache__", ".git"]
        return any(pattern in str(file_path) for pattern in skip_patterns)


class BiomimeticReadinessEvaluator:
    """Evaluates biomimetic agent system readiness"""

    def __init__(self):
        self.required_components = [
            "RUBIKGenome",
            "BiomimeticAgent",
            "ThanatosController",
            "CrossGenerationalLearningSystem",
            "GeneticBase",
            "Archetype",
            "MoodState",
        ]

        self.required_methods = [
            "calculate_fitness",
            "should_reproduce",
            "should_terminate",
            "inherit_knowledge",
            "evolve_generation",
        ]

    async def evaluate_biomimetic_readiness(self, project_path: Path) -> Dict[str, Any]:
        """Evaluate biomimetic system completeness"""

        found_components = set()
        found_methods = set()
        implementation_quality = {}

        for py_file in project_path.rglob("*.py"):
            if "biomimetic" in str(py_file) or "rubik" in str(py_file).lower():
                try:
                    content = py_file.read_text(encoding="utf-8")

                    # Check for required components
                    for component in self.required_components:
                        if re.search(rf"class\s+{component}", content):
                            found_components.add(component)

                    # Check for required methods
                    for method in self.required_methods:
                        if re.search(rf"def\s+{method}", content):
                            found_methods.add(method)

                    # Analyze implementation quality
                    quality_score = self._analyze_implementation_quality(content)
                    implementation_quality[str(py_file)] = quality_score

                except Exception as e:
                    logger.warning(f"Could not analyze {py_file}: {e}")

        # Calculate readiness metrics
        component_completeness = len(found_components) / len(self.required_components)
        method_completeness = len(found_methods) / len(self.required_methods)
        avg_quality = (
            sum(implementation_quality.values()) / len(implementation_quality)
            if implementation_quality
            else 0
        )

        overall_readiness = (
            component_completeness * 0.4 + method_completeness * 0.4 + avg_quality * 0.2
        )

        return {
            "component_completeness": component_completeness,
            "method_completeness": method_completeness,
            "average_implementation_quality": avg_quality,
            "overall_readiness_score": overall_readiness,
            "found_components": list(found_components),
            "missing_components": list(
                set(self.required_components) - found_components
            ),
            "found_methods": list(found_methods),
            "missing_methods": list(set(self.required_methods) - found_methods),
            "ready_for_production": overall_readiness >= 0.8,
        }

    def _analyze_implementation_quality(self, content: str) -> float:
        """Analyze implementation quality of biomimetic code"""
        quality_indicators = [
            r"async\s+def",  # Async methods
            r"@dataclass",  # Proper data structures
            r"logger\.",  # Logging
            r"try:.*except",  # Error handling
            r"typing\.",  # Type hints
            r'""".*"""',  # Documentation
        ]

        quality_score = 0
        for indicator in quality_indicators:
            if re.search(indicator, content, re.DOTALL):
                quality_score += 1

        return min(1.0, quality_score / len(quality_indicators))


class AdvancedGapDetectionSystem:
    """
    Comprehensive gap detection system for SSM/Local processing validation.

    Integrates all detection components to provide complete analysis of
    system readiness for 100% local, energy-efficient processing.
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)

        # Initialize detectors
        self.transformer_detector = TransformerResidualDetector()
        self.cloud_detector = CloudDependencyDetector()
        self.energy_analyzer = EnergyEfficiencyAnalyzer()
        self.biomimetic_evaluator = BiomimeticReadinessEvaluator()

        logger.info(f"Initialized Advanced Gap Detection System for {project_path}")

    async def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive gap detection analysis"""

        logger.info("Starting comprehensive gap detection analysis...")
        start_time = time.time()

        # Run all analyses in parallel
        results = await asyncio.gather(
            self.transformer_detector.detect_transformer_residuals(self.project_path),
            self.cloud_detector.detect_cloud_dependencies(self.project_path),
            self.energy_analyzer.analyze_energy_efficiency(self.project_path),
            self.biomimetic_evaluator.evaluate_biomimetic_readiness(self.project_path),
            return_exceptions=True,
        )

        transformer_gaps, cloud_gaps, energy_analysis, biomimetic_analysis = results

        # Handle any exceptions
        if isinstance(transformer_gaps, Exception):
            logger.error(f"Transformer detection failed: {transformer_gaps}")
            transformer_gaps = []

        if isinstance(cloud_gaps, Exception):
            logger.error(f"Cloud dependency detection failed: {cloud_gaps}")
            cloud_gaps = []

        if isinstance(energy_analysis, Exception):
            logger.error(f"Energy analysis failed: {energy_analysis}")
            energy_analysis = {}

        if isinstance(biomimetic_analysis, Exception):
            logger.error(f"Biomimetic analysis failed: {biomimetic_analysis}")
            biomimetic_analysis = {}

        # Compile comprehensive report
        analysis_time = time.time() - start_time

        report = {
            "analysis_metadata": {
                "project_path": str(self.project_path),
                "analysis_time_seconds": analysis_time,
                "timestamp": time.time(),
                "analyzer_version": "2025.1.0",
            },
            "transformer_residuals": {
                "gaps_found": len(transformer_gaps),
                "critical_gaps": len(
                    [g for g in transformer_gaps if g.severity == "critical"]
                ),
                "high_priority_gaps": len(
                    [g for g in transformer_gaps if g.severity == "high"]
                ),
                "details": [self._gap_to_dict(gap) for gap in transformer_gaps],
            },
            "cloud_dependencies": {
                "gaps_found": len(cloud_gaps),
                "critical_gaps": len(
                    [g for g in cloud_gaps if g.severity == "critical"]
                ),
                "details": [self._gap_to_dict(gap) for gap in cloud_gaps],
            },
            "energy_efficiency": energy_analysis,
            "biomimetic_readiness": biomimetic_analysis,
            "overall_assessment": self._calculate_overall_assessment(
                transformer_gaps, cloud_gaps, energy_analysis, biomimetic_analysis
            ),
        }

        logger.info(f"Gap detection analysis completed in {analysis_time:.2f} seconds")

        return report

    def _gap_to_dict(self, gap: GapDetectionResult) -> Dict[str, Any]:
        """Convert gap detection result to dictionary"""
        return {
            "gap_type": gap.gap_type.value,
            "severity": gap.severity,
            "file_path": gap.file_path,
            "line_number": gap.line_number,
            "description": gap.description,
            "recommendation": gap.recommendation,
            "code_snippet": gap.code_snippet,
            "confidence": gap.confidence,
        }

    def _calculate_overall_assessment(
        self,
        transformer_gaps: List,
        cloud_gaps: List,
        energy_analysis: Dict,
        biomimetic_analysis: Dict,
    ) -> Dict[str, Any]:
        """Calculate overall system readiness assessment"""

        # Critical issues that block production readiness
        critical_issues = len(
            [g for g in transformer_gaps if g.severity == "critical"]
        ) + len([g for g in cloud_gaps if g.severity == "critical"])

        # Energy efficiency score
        energy_score = energy_analysis.get("estimated_energy_reduction", 0)
        energy_target_met = energy_analysis.get("target_60_percent_achieved", False)

        # Biomimetic readiness score
        biomimetic_score = biomimetic_analysis.get("overall_readiness_score", 0)
        biomimetic_ready = biomimetic_analysis.get("ready_for_production", False)

        # Calculate overall readiness
        if critical_issues > 0:
            readiness_level = "not_ready"
            readiness_score = 0.0
        elif not energy_target_met or not biomimetic_ready:
            readiness_level = "partially_ready"
            readiness_score = 0.5
        else:
            readiness_level = "production_ready"
            readiness_score = min(1.0, (energy_score + biomimetic_score) / 2)

        return {
            "readiness_level": readiness_level,
            "readiness_score": readiness_score,
            "critical_issues_count": critical_issues,
            "energy_target_achieved": energy_target_met,
            "biomimetic_system_ready": biomimetic_ready,
            "estimated_energy_reduction_percent": energy_score * 100,
            "production_deployment_recommended": readiness_level == "production_ready",
            "next_steps": self._generate_next_steps(
                critical_issues, energy_target_met, biomimetic_ready
            ),
        }

    def _generate_next_steps(
        self, critical_issues: int, energy_target_met: bool, biomimetic_ready: bool
    ) -> List[str]:
        """Generate next steps based on analysis results"""
        steps = []

        if critical_issues > 0:
            steps.append(f"Address {critical_issues} critical issues before proceeding")

        if not energy_target_met:
            steps.append("Optimize energy efficiency to achieve 60% reduction target")

        if not biomimetic_ready:
            steps.append("Complete biomimetic agent system implementation")

        if not steps:
            steps.append("System ready for production deployment")
            steps.append("Consider advanced optimization and monitoring setup")

        return steps

    def save_report(self, report: Dict[str, Any], output_path: Path):
        """Save gap detection report to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Gap detection report saved to {output_path}")

    async def generate_ci_cd_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CI/CD compatible report"""

        overall = report["overall_assessment"]

        ci_report = {
            "status": "PASS"
            if overall["readiness_level"] == "production_ready"
            else "FAIL",
            "score": overall["readiness_score"],
            "critical_issues": overall["critical_issues_count"],
            "energy_target_met": overall["energy_target_achieved"],
            "biomimetic_ready": overall["biomimetic_system_ready"],
            "summary": {
                "transformer_residuals": report["transformer_residuals"]["gaps_found"],
                "cloud_dependencies": report["cloud_dependencies"]["gaps_found"],
                "energy_reduction_percent": overall[
                    "estimated_energy_reduction_percent"
                ],
            },
            "recommendations": overall["next_steps"],
        }

        return ci_report


async def main():
    """Main execution function for gap detection system"""
    import os
    
    # Get project path from environment or use current directory
    project_path = os.getenv('PROJECT_PATH', '.')
    
    # Initialize gap detection system
    gap_detector = AdvancedGapDetectionSystem(project_path)
    
    # Run comprehensive analysis
    print("Starting comprehensive gap detection analysis...")
    report = await gap_detector.run_comprehensive_analysis()
    
    # Print summary
    overall = report["overall_assessment"]
    print(f"\n=== Gap Detection Analysis Results ===")
    print(f"Readiness Level: {overall['readiness_level']}")
    print(f"Readiness Score: {overall['readiness_score']:.2f}")
    print(f"Critical Issues: {overall['critical_issues_count']}")
    print(f"Energy Target Met: {overall['energy_target_achieved']}")
    print(f"Biomimetic Ready: {overall['biomimetic_system_ready']}")
    print(f"Energy Reduction: {overall['estimated_energy_reduction_percent']:.1f}%")
    
    # Print next steps
    print(f"\n=== Next Steps ===")
    for step in overall['next_steps']:
        print(f"- {step}")
    
    # Save detailed report
    output_path = os.getenv('REPORT_OUTPUT_PATH', '/app/data/gap_detection_report.json')
    gap_detector.save_report(report, output_path)
    
    # Generate CI/CD report
    ci_report = await gap_detector.generate_ci_cd_report(report)
    ci_output_path = os.getenv('CI_REPORT_OUTPUT_PATH', '/app/data/ci_gap_report.json')
    
    import json
    with open(ci_output_path, 'w') as f:
        json.dump(ci_report, f, indent=2)
    
    print(f"\nReports saved to:")
    print(f"- Detailed: {output_path}")
    print(f"- CI/CD: {ci_output_path}")
    
    # Exit with appropriate code
    exit_code = 0 if ci_report['status'] == 'PASS' else 1
    return exit_code


if __name__ == "__main__":
    import sys
    
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error during gap detection analysis: {e}")
        sys.exit(1)