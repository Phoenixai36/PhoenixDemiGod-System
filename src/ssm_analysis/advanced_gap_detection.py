"""
Phoenix Hydra Advanced Gap Detection for SSM/Local Systems
Comprehensive gap analysis for non-transformer architectures and local processing
"""

import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


class GapSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class GapCategory(Enum):
    SSM_IMPLEMENTATION = "ssm_implementation"
    LOCAL_PROCESSING = "local_processing"
    ENERGY_EFFICIENCY = "energy_efficiency"
    BIOMIMETIC_AGENTS = "biomimetic_agents"
    MODEL_AVAILABILITY = "model_availability"
    INFRASTRUCTURE = "infrastructure"
    CONFIGURATION = "configuration"


@dataclass
class Gap:
    id: str
    category: GapCategory
    severity: GapSeverity
    title: str
    description: str
    current_state: str
    expected_state: str
    impact: str
    remediation: List[str]
    estimated_effort: str
    dependencies: List[str]
    validation_criteria: List[str]
    timestamp: float


class AdvancedGapDetector:
    """Advanced gap detection system for SSM/Local processing architecture"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.gaps: List[Gap] = []
        self.analysis_results = {}

    def detect_all_gaps(self) -> List[Gap]:
        """Run comprehensive gap detection across all categories"""
        print("🔍 Starting advanced gap detection for SSM/Local systems...")

        # Run all detection methods
        detection_methods = [
            self._detect_ssm_implementation_gaps,
            self._detect_local_processing_gaps,
            self._detect_energy_efficiency_gaps,
            self._detect_biomimetic_agent_gaps,
            self._detect_model_availability_gaps,
            self._detect_infrastructure_gaps,
            self._detect_configuration_gaps,
        ]

        for method in detection_methods:
            try:
                method()
            except Exception as e:
                print(f"⚠️  Error in {method.__name__}: {e}")

        print(f"✅ Gap detection complete. Found {len(self.gaps)} gaps.")
        return self.gaps

    def _detect_ssm_implementation_gaps(self):
        """Detect gaps in SSM/Mamba implementation"""
        print("🔍 Analyzing SSM/Mamba implementation...")

        # Check for SSM model files
        ssm_files = list(self.project_root.rglob("*ssm*.py")) + list(
            self.project_root.rglob("*mamba*.py")
        )

        if not ssm_files:
            self._add_gap(
                "ssm_001",
                GapCategory.SSM_IMPLEMENTATION,
                GapSeverity.CRITICAL,
                "Missing SSM/Mamba Model Implementation",
                "No SSM or Mamba model implementation files found in the project",
                "No SSM implementation detected",
                "Complete SSM/Mamba model architecture implemented",
                "Cannot achieve energy-efficient processing without SSM models",
                [
                    "Implement core SSM model classes",
                    "Add Mamba architecture support",
                    "Create SSM-based analysis engines",
                    "Integrate with existing pipeline",
                ],
                "3-5 days",
                ["mamba-ssm library", "causal-conv1d"],
                [
                    "SSM models can process sequences",
                    "Energy consumption reduced by 60-70%",
                ],
            )

        # Check for transformer residuals
        transformer_files = list(self.project_root.rglob("*transformer*.py")) + list(
            self.project_root.rglob("*attention*.py")
        )

        if transformer_files:
            self._add_gap(
                "ssm_002",
                GapCategory.SSM_IMPLEMENTATION,
                GapSeverity.HIGH,
                "Transformer Architecture Residuals Detected",
                f"Found {len(transformer_files)} files with transformer/attention patterns",
                f"Transformer code present in {len(transformer_files)} files",
                "All transformer code replaced with SSM equivalents",
                "Transformer residuals prevent full energy efficiency gains",
                [
                    "Audit all transformer usage",
                    "Replace attention mechanisms with SSM",
                    "Migrate transformer models to Mamba",
                    "Update model loading logic",
                ],
                "2-3 days",
                ["SSM implementation complete"],
                [
                    "No transformer imports in codebase",
                    "All models use SSM architecture",
                ],
            )

        # Check for SSM dependencies
        requirements_files = list(self.project_root.glob("*requirements*.txt"))
        has_mamba_ssm = False

        for req_file in requirements_files:
            try:
                content = req_file.read_text()
                if "mamba-ssm" in content or "causal-conv1d" in content:
                    has_mamba_ssm = True
                    break
            except Exception:
                continue

        if not has_mamba_ssm:
            self._add_gap(
                "ssm_003",
                GapCategory.SSM_IMPLEMENTATION,
                GapSeverity.MEDIUM,
                "Missing SSM Dependencies",
                "Required SSM/Mamba dependencies not found in requirements",
                "SSM dependencies not specified",
                "mamba-ssm and causal-conv1d dependencies added",
                "Cannot run SSM models without proper dependencies",
                [
                    "Add mamba-ssm>=1.2.0 to requirements",
                    "Add causal-conv1d>=1.1.0 to requirements",
                    "Update installation documentation",
                    "Test dependency installation",
                ],
                "1 hour",
                [],
                ["Dependencies install successfully", "SSM models can be imported"],
            )

    def _detect_local_processing_gaps(self):
        """Detect gaps in local processing capabilities"""
        print("🔍 Analyzing local processing implementation...")

        # Check for offline detection
        offline_files = list(self.project_root.rglob("*offline*.py")) + list(
            self.project_root.rglob("*local*.py")
        )

        if not offline_files:
            self._add_gap(
                "local_001",
                GapCategory.LOCAL_PROCESSING,
                GapSeverity.CRITICAL,
                "Missing Offline Processing Detection",
                "No offline/local processing detection mechanism found",
                "No offline detection system",
                "Robust offline detection and fallback system",
                "Cannot guarantee 100% local processing without detection",
                [
                    "Implement network connectivity detection",
                    "Create offline mode switching",
                    "Add local model fallback logic",
                    "Build offline capability validation",
                ],
                "2-3 days",
                ["Local model storage", "Model management system"],
                ["System works without internet", "All processing stays local"],
            )

        # Check for cloud service calls
        cloud_patterns = ["openai", "anthropic", "cohere", "huggingface_hub.inference"]
        cloud_violations = []

        for py_file in self.project_root.rglob("*.py"):
            try:
                content = py_file.read_text()
                for pattern in cloud_patterns:
                    if pattern in content.lower():
                        cloud_violations.append((py_file, pattern))
            except Exception:
                continue

        if cloud_violations:
            self._add_gap(
                "local_002",
                GapCategory.LOCAL_PROCESSING,
                GapSeverity.HIGH,
                "Cloud Service Dependencies Detected",
                f"Found {len(cloud_violations)} potential cloud service calls",
                f"Cloud dependencies in {len(set(v[0] for v in cloud_violations))} files",
                "All processing uses local models only",
                "Cloud dependencies violate local processing requirement",
                [
                    "Audit all cloud service calls",
                    "Replace with local model equivalents",
                    "Add local processing validation",
                    "Update configuration to disable cloud services",
                ],
                "1-2 days",
                ["Local models available", "Offline detection system"],
                ["No outbound API calls", "All models run locally"],
            )

        # Check for model storage
        model_dirs = ["models", "cache", ".cache"]
        has_model_storage = any((self.project_root / d).exists() for d in model_dirs)

        if not has_model_storage:
            self._add_gap(
                "local_003",
                GapCategory.LOCAL_PROCESSING,
                GapSeverity.MEDIUM,
                "Missing Local Model Storage",
                "No dedicated model storage directory found",
                "No model storage structure",
                "Organized local model storage with caching",
                "Cannot store and manage local models effectively",
                [
                    "Create models directory structure",
                    "Implement model caching system",
                    "Add model versioning support",
                    "Create model cleanup utilities",
                ],
                "1 day",
                [],
                ["Models stored locally", "Model cache management works"],
            )

    def _detect_energy_efficiency_gaps(self):
        """Detect energy efficiency implementation gaps"""
        print("🔍 Analyzing energy efficiency implementation...")

        # Check for energy monitoring
        energy_files = (
            list(self.project_root.rglob("*energy*.py"))
            + list(self.project_root.rglob("*power*.py"))
            + list(self.project_root.rglob("*efficiency*.py"))
        )

        if not energy_files:
            self._add_gap(
                "energy_001",
                GapCategory.ENERGY_EFFICIENCY,
                GapSeverity.MEDIUM,
                "Missing Energy Monitoring",
                "No energy consumption monitoring implementation found",
                "No energy monitoring system",
                "Comprehensive energy monitoring and reporting",
                "Cannot validate 60-70% energy reduction claims",
                [
                    "Implement energy consumption tracking",
                    "Add power usage monitoring",
                    "Create efficiency comparison tools",
                    "Build energy reporting dashboard",
                ],
                "2-3 days",
                ["System monitoring tools", "Metrics collection"],
                ["Energy consumption tracked", "Efficiency gains measurable"],
            )

        # Check for GPU optimization
        gpu_files = list(self.project_root.rglob("*gpu*.py")) + list(
            self.project_root.rglob("*cuda*.py")
        )

        if not gpu_files:
            self._add_gap(
                "energy_002",
                GapCategory.ENERGY_EFFICIENCY,
                GapSeverity.LOW,
                "Missing GPU Optimization",
                "No GPU-specific optimization code found",
                "No GPU optimization",
                "GPU-optimized SSM implementations",
                "Missing potential energy efficiency gains from GPU optimization",
                [
                    "Add CUDA support for SSM models",
                    "Implement GPU memory optimization",
                    "Create GPU/CPU fallback logic",
                    "Optimize batch processing for GPUs",
                ],
                "3-4 days",
                ["CUDA toolkit", "GPU-enabled hardware"],
                ["GPU acceleration works", "Energy efficiency on GPU measured"],
            )

    def _detect_biomimetic_agent_gaps(self):
        """Detect gaps in biomimetic agent implementation"""
        print("🔍 Analyzing biomimetic agent system...")

        # Check for RUBIK implementation
        rubik_files = list(self.project_root.rglob("*rubik*.py")) + list(
            self.project_root.rglob("*biomimetic*.py")
        )

        if not rubik_files:
            self._add_gap(
                "bio_001",
                GapCategory.BIOMIMETIC_AGENTS,
                GapSeverity.HIGH,
                "Missing RUBIK Biomimetic System",
                "No RUBIK biomimetic agent implementation found",
                "No biomimetic agent system",
                "Complete RUBIK 20-base genetic system",
                "Cannot achieve adaptive intelligence without biomimetic agents",
                [
                    "Implement RUBIK genetic encoding",
                    "Create agent persona system",
                    "Add mood and emotion engines",
                    "Build cross-generational learning",
                ],
                "5-7 days",
                ["SSM models", "Local processing"],
                ["Agents evolve and adapt", "Genetic encoding works"],
            )

        # Check for Thanatos controller
        thanatos_files = list(self.project_root.rglob("*thanatos*.py")) + list(
            self.project_root.rglob("*lifecycle*.py")
        )

        if not thanatos_files:
            self._add_gap(
                "bio_002",
                GapCategory.BIOMIMETIC_AGENTS,
                GapSeverity.MEDIUM,
                "Missing Thanatos Lifecycle Controller",
                "No agent lifecycle management system found",
                "No lifecycle management",
                "Thanatos controller managing agent death/rebirth cycles",
                "Agents cannot evolve through death/rebirth cycles",
                [
                    "Implement Thanatos controller",
                    "Add agent lifecycle tracking",
                    "Create death/rebirth logic",
                    "Build evolution metrics",
                ],
                "2-3 days",
                ["RUBIK agent system"],
                ["Agent lifecycles managed", "Evolution through rebirth works"],
            )

    def _detect_model_availability_gaps(self):
        """Detect gaps in 2025 model availability"""
        print("🔍 Analyzing 2025 model ecosystem availability...")

        # Check for Ollama installation
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, "ollama")

            # Parse available models
            ollama_models = []
            for line in result.stdout.split("\n")[1:]:  # Skip header
                if line.strip():
                    model_name = line.split()[0]
                    ollama_models.append(model_name)

            # Check for 2025 flagship models
            flagship_models = [
                "qwen2.5-coder",
                "glm-4.5",
                "deepseek-coder-v2",
                "phi3",
                "gemma2",
                "llama3.2",
            ]

            missing_models = []
            for model in flagship_models:
                if not any(model in om for om in ollama_models):
                    missing_models.append(model)

            if missing_models:
                self._add_gap(
                    "model_001",
                    GapCategory.MODEL_AVAILABILITY,
                    GapSeverity.MEDIUM,
                    "Missing 2025 Flagship Models",
                    f"Missing {len(missing_models)} key 2025 models: {', '.join(missing_models)}",
                    f"{len(ollama_models)} models available, {len(missing_models)} missing",
                    "All 2025 flagship models available locally",
                    "Reduced capability without latest 2025 models",
                    [
                        "Run model download script",
                        "Download missing flagship models",
                        "Verify model functionality",
                        "Update model configuration",
                    ],
                    "2-4 hours",
                    ["Ollama installation", "Sufficient storage space"],
                    ["All flagship models available", "Models respond to queries"],
                )

        except (subprocess.CalledProcessError, FileNotFoundError):
            self._add_gap(
                "model_002",
                GapCategory.MODEL_AVAILABILITY,
                GapSeverity.CRITICAL,
                "Ollama Not Available",
                "Ollama is not installed or not accessible",
                "Ollama not available",
                "Ollama installed and running with models",
                "Cannot run local models without Ollama",
                [
                    "Install Ollama from https://ollama.ai",
                    "Start Ollama service",
                    "Download initial models",
                    "Test model access",
                ],
                "1-2 hours",
                [],
                ["Ollama responds to commands", "Models can be listed and used"],
            )

    def _detect_infrastructure_gaps(self):
        """Detect infrastructure gaps"""
        print("🔍 Analyzing infrastructure setup...")

        # Check for Podman setup
        compose_files = list(self.project_root.glob("**/compose.yaml")) + list(
            self.project_root.glob("**/docker-compose.yaml")
        )

        if not compose_files:
            self._add_gap(
                "infra_001",
                GapCategory.INFRASTRUCTURE,
                GapSeverity.MEDIUM,
                "Missing Container Orchestration",
                "No Podman/Docker compose files found",
                "No container orchestration",
                "Complete Podman compose setup for all services",
                "Cannot deploy Phoenix Hydra stack efficiently",
                [
                    "Create Podman compose files",
                    "Define service dependencies",
                    "Add volume management",
                    "Configure networking",
                ],
                "1-2 days",
                ["Podman installation"],
                ["Services start with compose", "All components accessible"],
            )

        # Check for monitoring setup
        monitoring_files = list(self.project_root.rglob("*prometheus*.yaml")) + list(
            self.project_root.rglob("*grafana*.yaml")
        )

        if not monitoring_files:
            self._add_gap(
                "infra_002",
                GapCategory.INFRASTRUCTURE,
                GapSeverity.LOW,
                "Missing Monitoring Infrastructure",
                "No monitoring configuration found",
                "No monitoring setup",
                "Prometheus and Grafana monitoring configured",
                "Cannot monitor system performance and energy efficiency",
                [
                    "Add Prometheus configuration",
                    "Create Grafana dashboards",
                    "Configure metrics collection",
                    "Set up alerting rules",
                ],
                "2-3 days",
                ["Container orchestration"],
                ["Metrics collected", "Dashboards show system status"],
            )

    def _detect_configuration_gaps(self):
        """Detect configuration gaps"""
        print("🔍 Analyzing configuration completeness...")

        # Check for Phoenix Hydra config
        config_files = list(self.project_root.rglob("*phoenix*.yaml")) + list(
            self.project_root.rglob("*phoenix*.json")
        )

        if not config_files:
            self._add_gap(
                "config_001",
                GapCategory.CONFIGURATION,
                GapSeverity.MEDIUM,
                "Missing Phoenix Hydra Configuration",
                "No Phoenix Hydra configuration files found",
                "No centralized configuration",
                "Complete Phoenix Hydra configuration system",
                "Cannot configure system behavior and model selection",
                [
                    "Create main configuration file",
                    "Add model selection config",
                    "Configure processing modes",
                    "Set energy efficiency parameters",
                ],
                "1 day",
                [],
                ["Configuration loads successfully", "All components use config"],
            )

        # Check for environment configuration
        env_files = list(self.project_root.glob(".env*"))

        if not env_files:
            self._add_gap(
                "config_002",
                GapCategory.CONFIGURATION,
                GapSeverity.LOW,
                "Missing Environment Configuration",
                "No environment configuration files found",
                "No environment config",
                "Environment variables properly configured",
                "May have configuration issues in different environments",
                [
                    "Create .env.example file",
                    "Document required environment variables",
                    "Add environment validation",
                    "Create setup scripts",
                ],
                "2-3 hours",
                [],
                ["Environment variables documented", "Setup scripts work"],
            )

    def _add_gap(
        self,
        gap_id: str,
        category: GapCategory,
        severity: GapSeverity,
        title: str,
        description: str,
        current_state: str,
        expected_state: str,
        impact: str,
        remediation: List[str],
        estimated_effort: str,
        dependencies: List[str],
        validation_criteria: List[str],
    ):
        """Add a gap to the collection"""
        gap = Gap(
            id=gap_id,
            category=category,
            severity=severity,
            title=title,
            description=description,
            current_state=current_state,
            expected_state=expected_state,
            impact=impact,
            remediation=remediation,
            estimated_effort=estimated_effort,
            dependencies=dependencies,
            validation_criteria=validation_criteria,
            timestamp=time.time(),
        )
        self.gaps.append(gap)

    def generate_gap_report(self) -> Dict[str, Any]:
        """Generate comprehensive gap analysis report"""
        # Categorize gaps
        gaps_by_category = {}
        gaps_by_severity = {}

        for gap in self.gaps:
            # By category
            if gap.category not in gaps_by_category:
                gaps_by_category[gap.category] = []
            gaps_by_category[gap.category].append(gap)

            # By severity
            if gap.severity not in gaps_by_severity:
                gaps_by_severity[gap.severity] = []
            gaps_by_severity[gap.severity].append(gap)

        # Calculate metrics
        total_gaps = len(self.gaps)
        critical_gaps = len(gaps_by_severity.get(GapSeverity.CRITICAL, []))
        high_gaps = len(gaps_by_severity.get(GapSeverity.HIGH, []))

        # Estimate total effort
        effort_mapping = {
            "1 hour": 1,
            "2-3 hours": 2.5,
            "1 day": 8,
            "2-3 days": 20,
            "3-4 days": 28,
            "5-7 days": 48,
            "1-2 weeks": 80,
        }

        total_effort_hours = 0
        for gap in self.gaps:
            effort = gap.estimated_effort.lower()
            for pattern, hours in effort_mapping.items():
                if pattern in effort:
                    total_effort_hours += hours
                    break

        report = {
            "timestamp": time.time(),
            "summary": {
                "total_gaps": total_gaps,
                "critical_gaps": critical_gaps,
                "high_priority_gaps": high_gaps,
                "estimated_effort_hours": total_effort_hours,
                "estimated_effort_days": round(total_effort_hours / 8, 1),
            },
            "gaps_by_category": {
                cat.value: [asdict(gap) for gap in gaps]
                for cat, gaps in gaps_by_category.items()
            },
            "gaps_by_severity": {
                sev.value: [asdict(gap) for gap in gaps]
                for sev, gaps in gaps_by_severity.items()
            },
            "prioritized_action_plan": self._generate_action_plan(),
            "validation_checklist": self._generate_validation_checklist(),
        }

        return report

    def _generate_action_plan(self) -> List[Dict[str, Any]]:
        """Generate prioritized action plan"""
        # Sort gaps by severity and dependencies
        severity_order = {
            GapSeverity.CRITICAL: 0,
            GapSeverity.HIGH: 1,
            GapSeverity.MEDIUM: 2,
            GapSeverity.LOW: 3,
            GapSeverity.INFO: 4,
        }

        sorted_gaps = sorted(self.gaps, key=lambda g: severity_order[g.severity])

        action_plan = []
        for i, gap in enumerate(sorted_gaps, 1):
            action_plan.append(
                {
                    "priority": i,
                    "gap_id": gap.id,
                    "title": gap.title,
                    "category": gap.category.value,
                    "severity": gap.severity.value,
                    "estimated_effort": gap.estimated_effort,
                    "dependencies": gap.dependencies,
                    "next_actions": gap.remediation[:3],  # Top 3 actions
                }
            )

        return action_plan

    def _generate_validation_checklist(self) -> List[Dict[str, Any]]:
        """Generate validation checklist for gap resolution"""
        checklist = []

        for gap in self.gaps:
            for criterion in gap.validation_criteria:
                checklist.append(
                    {
                        "gap_id": gap.id,
                        "category": gap.category.value,
                        "validation_item": criterion,
                        "completed": False,
                    }
                )

        return checklist

    def save_gap_report(self, output_path: str = "gap_analysis_report.json") -> Path:
        """Save gap analysis report to file"""
        report = self.generate_gap_report()

        output_file = Path(output_path)
        with open(output_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"📄 Gap analysis report saved to: {output_file}")
        return output_file


def main():
    """Main function for gap detection"""
    print("🚀 Phoenix Hydra Advanced Gap Detection")
    print("=" * 50)

    detector = AdvancedGapDetector()
    gaps = detector.detect_all_gaps()

    # Generate and save report
    report_path = detector.save_gap_report()

    # Display summary
    report = detector.generate_gap_report()
    summary = report["summary"]

    print(f"\n📊 Gap Analysis Summary:")
    print(f"  Total Gaps: {summary['total_gaps']}")
    print(f"  Critical: {summary['critical_gaps']}")
    print(f"  High Priority: {summary['high_priority_gaps']}")
    print(f"  Estimated Effort: {summary['estimated_effort_days']} days")

    print(f"\n🎯 Next Steps:")
    action_plan = report["prioritized_action_plan"][:5]  # Top 5
    for action in action_plan:
        print(f"  {action['priority']}. {action['title']} ({action['severity']})")

    print(f"\n✅ Gap detection complete! Report saved to {report_path}")


if __name__ == "__main__":
    main()
