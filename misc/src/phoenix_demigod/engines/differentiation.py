"""
Differentiation Engine for the Phoenix DemiGod system.

The Differentiation Engine creates specialized subsystems based on the
analysis from the Traversal Engine, following a template-based approach.
"""

import os
import string
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from phoenix_demigod.core.state_tree import StateNode, StateTree
from phoenix_demigod.engines.traversal import AnalysisReport, Pattern, Recommendation
from phoenix_demigod.utils.logging import get_logger


class SubsystemTemplate:
    """Template for generating subsystems."""
    
    def __init__(self, name: str, template_path: str):
        """
        Initialize a new SubsystemTemplate.
        
        Args:
            name: Template name
            template_path: Path to the template file
        """
        self.name = name
        self.template_path = template_path
        self.content = ""
        self.loaded = False
    
    async def load(self) -> bool:
        """
        Load the template content from file.
        
        Returns:
            True if the template was loaded successfully, False otherwise
        """
        try:
            with open(self.template_path, 'r') as f:
                self.content = f.read()
            self.loaded = True
            return True
        except Exception:
            return False
    
    def generate(self, parameters: Dict[str, Any]) -> str:
        """
        Generate subsystem code from template and parameters.
        
        Args:
            parameters: Parameters to substitute in the template
            
        Returns:
            Generated code
            
        Raises:
            ValueError: If the template is not loaded
        """
        if not self.loaded:
            raise ValueError(f"Template {self.name} not loaded")
            
        # Simple string template substitution
        template = string.Template(self.content)
        return template.safe_substitute(parameters)
    
    def validate(self, generated_code: str) -> bool:
        """
        Validate the generated subsystem code.
        
        Args:
            generated_code: Generated code to validate
            
        Returns:
            True if the code is valid, False otherwise
        """
        # In a real implementation, this would perform syntax checking,
        # security analysis, etc. For now, we'll do a simple check.
        if not generated_code:
            return False
            
        # Check for required elements
        required_elements = [
            "class", "def __init__", "def initialize", 
            "def process", "def get_health", "def shutdown"
        ]
        
        for element in required_elements:
            if element not in generated_code:
                return False
                
        return True


class DifferentiationResult:
    """Result of the differentiation process."""
    
    def __init__(self):
        """Initialize a new DifferentiationResult."""
        self.generated_subsystems: List[Dict[str, Any]] = []
        self.modified_subsystems: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.timestamp = datetime.now()
    
    def add_generated_subsystem(self, subsystem_info: Dict[str, Any]) -> None:
        """
        Add a generated subsystem to the result.
        
        Args:
            subsystem_info: Information about the generated subsystem
        """
        self.generated_subsystems.append(subsystem_info)
    
    def add_modified_subsystem(self, subsystem_info: Dict[str, Any]) -> None:
        """
        Add a modified subsystem to the result.
        
        Args:
            subsystem_info: Information about the modified subsystem
        """
        self.modified_subsystems.append(subsystem_info)
    
    def add_error(self, error_info: Dict[str, Any]) -> None:
        """
        Add an error to the result.
        
        Args:
            error_info: Information about the error
        """
        self.errors.append(error_info)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary representation.
        
        Returns:
            Dictionary representation of the result
        """
        return {
            "generated_subsystems": self.generated_subsystems,
            "modified_subsystems": self.modified_subsystems,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat()
        }


class DifferentiationEngine:
    """
    Engine for creating and specializing subsystems.
    
    The DifferentiationEngine processes analysis reports from the TraversalEngine
    and generates or modifies subsystems based on detected patterns and needs.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize a new DifferentiationEngine.
        
        Args:
            config: Configuration parameters (default: empty dict)
        """
        self.logger = get_logger("phoenix_demigod.engines.differentiation")
        self.config = config or {}
        
        # Extract configuration parameters with defaults
        self.template_directory = self.config.get("template_directory", "templates/")
        self.validation_timeout = self.config.get("validation_timeout", 10.0)
        self.max_generation_attempts = self.config.get("max_generation_attempts", 3)
        self.enable_adaptive_specialization = self.config.get("enable_adaptive_specialization", True)
        self.specialization_threshold = self.config.get("specialization_threshold", 0.6)
        
        # Initialize templates
        self.templates: Dict[str, SubsystemTemplate] = {}
        
        self.logger.info(f"DifferentiationEngine initialized with config: {self.config}")
    
    async def initialize_templates(self) -> None:
        """Load all templates from the template directory."""
        self.logger.info(f"Loading templates from {self.template_directory}")
        
        try:
            # Check if directory exists
            if not os.path.isdir(self.template_directory):
                self.logger.error(f"Template directory not found: {self.template_directory}")
                return
                
            # Load all .template files
            for filename in os.listdir(self.template_directory):
                if filename.endswith(".template"):
                    template_name = filename.split(".")[0]
                    template_path = os.path.join(self.template_directory, filename)
                    
                    template = SubsystemTemplate(template_name, template_path)
                    if await template.load():
                        self.templates[template_name] = template
                        self.logger.debug(f"Loaded template: {template_name}")
                    else:
                        self.logger.warning(f"Failed to load template: {template_name}")
                        
            self.logger.info(f"Loaded {len(self.templates)} templates")
            
        except Exception as e:
            self.logger.error(f"Error initializing templates: {e}", exc_info=True)
    
    async def process_analysis(
        self,
        analysis_report: AnalysisReport,
        state_tree: StateTree
    ) -> DifferentiationResult:
        """
        Process analysis results and generate/modify subsystems.
        
        Args:
            analysis_report: Analysis report from the TraversalEngine
            state_tree: Current state tree
            
        Returns:
            Differentiation result
        """
        self.logger.info("Processing analysis report")
        
        # Initialize result
        result = DifferentiationResult()
        
        # Ensure templates are loaded
        if not self.templates:
            await self.initialize_templates()
            
        # Process recommendations for subsystem generation
        for recommendation in analysis_report.recommendations:
            if recommendation.priority >= self.specialization_threshold:
                await self._process_recommendation(recommendation, state_tree, result)
        
        # Process patterns for subsystem specialization
        if self.enable_adaptive_specialization:
            for pattern in analysis_report.patterns:
                if pattern.confidence >= self.specialization_threshold:
                    await self._process_pattern(pattern, state_tree, result)
        
        self.logger.info(
            f"Differentiation completed: "
            f"{len(result.generated_subsystems)} generated, "
            f"{len(result.modified_subsystems)} modified, "
            f"{len(result.errors)} errors"
        )
        
        return result
    
    async def _process_recommendation(
        self,
        recommendation: Recommendation,
        state_tree: StateTree,
        result: DifferentiationResult
    ) -> None:
        """
        Process a recommendation for subsystem generation.
        
        Args:
            recommendation: Recommendation to process
            state_tree: Current state tree
            result: Differentiation result to update
        """
        try:
            self.logger.debug(f"Processing recommendation: {recommendation.type} at {recommendation.path}")
            
            # Determine if we need to generate a new subsystem
            if recommendation.type == "STRUCTURE_OPTIMIZATION":
                await self._generate_optimization_subsystem(recommendation, state_tree, result)
                
            elif recommendation.type == "CACHING":
                await self._generate_caching_subsystem(recommendation, state_tree, result)
                
            elif recommendation.type == "DATA_OPTIMIZATION":
                await self._generate_data_optimization_subsystem(recommendation, state_tree, result)
                
            elif recommendation.type == "METADATA_ENHANCEMENT":
                await self._generate_metadata_subsystem(recommendation, state_tree, result)
                
            elif recommendation.type == "STRUCTURE_COMPLETION":
                await self._generate_structure_subsystem(recommendation, state_tree, result)
                
            elif recommendation.type == "PERFORMANCE_OPTIMIZATION":
                await self._generate_performance_subsystem(recommendation, state_tree, result)
                
        except Exception as e:
            self.logger.error(f"Error processing recommendation: {e}", exc_info=True)
            result.add_error({
                "type": "RECOMMENDATION_PROCESSING_ERROR",
                "recommendation_type": recommendation.type,
                "path": recommendation.path,
                "error": str(e)
            })
    
    async def _process_pattern(
        self,
        pattern: Pattern,
        state_tree: StateTree,
        result: DifferentiationResult
    ) -> None:
        """
        Process a pattern for subsystem specialization.
        
        Args:
            pattern: Pattern to process
            state_tree: Current state tree
            result: Differentiation result to update
        """
        try:
            self.logger.debug(f"Processing pattern: {pattern.type} at {pattern.path}")
            
            # Check if there's an existing subsystem to specialize
            subsystems_node = state_tree.get_node("/runtime_state/active_subsystems")
            if not subsystems_node:
                return
                
            # Find subsystems that might benefit from specialization
            for child in subsystems_node.children:
                if child.type == "subsystem":
                    # Check if this subsystem is related to the pattern
                    if self._is_subsystem_related_to_pattern(child, pattern):
                        await self._specialize_subsystem(child, pattern, state_tree, result)
                        
        except Exception as e:
            self.logger.error(f"Error processing pattern: {e}", exc_info=True)
            result.add_error({
                "type": "PATTERN_PROCESSING_ERROR",
                "pattern_type": pattern.type,
                "path": pattern.path,
                "error": str(e)
            })
    
    def _is_subsystem_related_to_pattern(self, subsystem_node: StateNode, pattern: Pattern) -> bool:
        """
        Check if a subsystem is related to a pattern.
        
        Args:
            subsystem_node: Subsystem node
            pattern: Pattern to check
            
        Returns:
            True if the subsystem is related to the pattern, False otherwise
        """
        # In a real implementation, this would use more sophisticated matching
        # For now, we'll use a simple heuristic
        
        # Check if the subsystem handles the same path
        if "handled_paths" in subsystem_node.data:
            for path in subsystem_node.data["handled_paths"]:
                if pattern.path.startswith(path) or path.startswith(pattern.path):
                    return True
        
        # Check if the subsystem handles the same type
        if "handled_types" in subsystem_node.data and "type" in pattern.data:
            if pattern.data["type"] in subsystem_node.data["handled_types"]:
                return True
        
        return False
    
    async def _generate_optimization_subsystem(
        self,
        recommendation: Recommendation,
        state_tree: StateTree,
        result: DifferentiationResult
    ) -> None:
        """
        Generate an optimization subsystem.
        
        Args:
            recommendation: Recommendation to process
            state_tree: Current state tree
            result: Differentiation result to update
        """
        # Check if we have the template
        if "subsystem_base" not in self.templates:
            self.logger.warning("Missing subsystem_base template")
            return
            
        # Generate parameters
        parameters = {
            "SUBSYSTEM_NAME": "OptimizationSubsystem",
            "SUBSYSTEM_VERSION": "1.0.0",
            "SUBSYSTEM_DESCRIPTION": f"Optimization subsystem for {recommendation.path}",
            "INITIALIZATION_CODE": f"# Initialize optimization for {recommendation.path}\n        self.target_path = \"{recommendation.path}\"\n        self.optimization_type = \"structure\"",
            "PROCESSING_CODE": "# Process data with structure optimization\n        result = input_data  # Placeholder for actual optimization\n        return result",
            "HEALTH_CHECK_CODE": "# Check optimization health\n        return Health(HealthStatus.HEALTHY, \"Optimization subsystem healthy\")",
            "SHUTDOWN_CODE": "# Clean up optimization resources\n        pass"
        }
        
        # Generate code
        template = self.templates["subsystem_base"]
        generated_code = template.generate(parameters)
        
        # Validate code
        if template.validate(generated_code):
            # In a real implementation, we would save this to a file and load it
            # For now, we'll just add it to the result
            result.add_generated_subsystem({
                "name": "OptimizationSubsystem",
                "type": "optimization",
                "target_path": recommendation.path,
                "recommendation_type": recommendation.type,
                "code_size": len(generated_code)
            })
            
            # Update state tree
            await self._add_subsystem_to_state_tree(
                state_tree,
                "OptimizationSubsystem",
                "optimization",
                recommendation.path,
                {
                    "handled_paths": [recommendation.path],
                    "optimization_type": "structure"
                }
            )
        else:
            result.add_error({
                "type": "VALIDATION_ERROR",
                "subsystem_name": "OptimizationSubsystem",
                "recommendation_type": recommendation.type,
                "path": recommendation.path
            })
    
    async def _generate_caching_subsystem(
        self,
        recommendation: Recommendation,
        state_tree: StateTree,
        result: DifferentiationResult
    ) -> None:
        """
        Generate a caching subsystem.
        
        Args:
            recommendation: Recommendation to process
            state_tree: Current state tree
            result: Differentiation result to update
        """
        # Check if we have the template
        if "subsystem_base" not in self.templates:
            self.logger.warning("Missing subsystem_base template")
            return
            
        # Generate parameters
        parameters = {
            "SUBSYSTEM_NAME": "CachingSubsystem",
            "SUBSYSTEM_VERSION": "1.0.0",
            "SUBSYSTEM_DESCRIPTION": f"Caching subsystem for {recommendation.path}",
            "INITIALIZATION_CODE": f"# Initialize caching for {recommendation.path}\n        self.target_path = \"{recommendation.path}\"\n        self.cache = {{}}\n        self.ttl = 300  # 5 minutes",
            "PROCESSING_CODE": "# Process data with caching\n        cache_key = str(input_data)\n        if cache_key in self.cache:\n            return self.cache[cache_key]\n        result = input_data  # Placeholder for actual processing\n        self.cache[cache_key] = result\n        return result",
            "HEALTH_CHECK_CODE": "# Check cache health\n        cache_size = len(self.cache)\n        if cache_size > 1000:\n            return Health(HealthStatus.DEGRADED, f\"Cache size ({cache_size}) is large\")\n        return Health(HealthStatus.HEALTHY, \"Cache healthy\")",
            "SHUTDOWN_CODE": "# Clean up cache\n        self.cache.clear()"
        }
        
        # Generate code
        template = self.templates["subsystem_base"]
        generated_code = template.generate(parameters)
        
        # Validate code
        if template.validate(generated_code):
            result.add_generated_subsystem({
                "name": "CachingSubsystem",
                "type": "caching",
                "target_path": recommendation.path,
                "recommendation_type": recommendation.type,
                "code_size": len(generated_code)
            })
            
            # Update state tree
            await self._add_subsystem_to_state_tree(
                state_tree,
                "CachingSubsystem",
                "caching",
                recommendation.path,
                {
                    "handled_paths": [recommendation.path],
                    "ttl": 300
                }
            )
        else:
            result.add_error({
                "type": "VALIDATION_ERROR",
                "subsystem_name": "CachingSubsystem",
                "recommendation_type": recommendation.type,
                "path": recommendation.path
            })
    
    async def _generate_data_optimization_subsystem(
        self,
        recommendation: Recommendation,
        state_tree: StateTree,
        result: DifferentiationResult
    ) -> None:
        """
        Generate a data optimization subsystem.
        
        Args:
            recommendation: Recommendation to process
            state_tree: Current state tree
            result: Differentiation result to update
        """
        # Similar implementation to other subsystem generators
        # Simplified for brevity
        result.add_generated_subsystem({
            "name": "DataOptimizationSubsystem",
            "type": "data_optimization",
            "target_path": recommendation.path,
            "recommendation_type": recommendation.type,
            "code_size": 1000  # Placeholder
        })
        
        # Update state tree
        await self._add_subsystem_to_state_tree(
            state_tree,
            "DataOptimizationSubsystem",
            "data_optimization",
            recommendation.path,
            {
                "handled_paths": [recommendation.path],
                "optimization_type": "data"
            }
        )
    
    async def _generate_metadata_subsystem(
        self,
        recommendation: Recommendation,
        state_tree: StateTree,
        result: DifferentiationResult
    ) -> None:
        """
        Generate a metadata enhancement subsystem.
        
        Args:
            recommendation: Recommendation to process
            state_tree: Current state tree
            result: Differentiation result to update
        """
        # Similar implementation to other subsystem generators
        # Simplified for brevity
        result.add_generated_subsystem({
            "name": "MetadataSubsystem",
            "type": "metadata",
            "target_path": recommendation.path,
            "recommendation_type": recommendation.type,
            "code_size": 800  # Placeholder
        })
        
        # Update state tree
        await self._add_subsystem_to_state_tree(
            state_tree,
            "MetadataSubsystem",
            "metadata",
            recommendation.path,
            {
                "handled_paths": [recommendation.path],
                "metadata_types": ["description", "created_at", "updated_at"]
            }
        )
    
    async def _generate_structure_subsystem(
        self,
        recommendation: Recommendation,
        state_tree: StateTree,
        result: DifferentiationResult
    ) -> None:
        """
        Generate a structure completion subsystem.
        
        Args:
            recommendation: Recommendation to process
            state_tree: Current state tree
            result: Differentiation result to update
        """
        # Similar implementation to other subsystem generators
        # Simplified for brevity
        result.add_generated_subsystem({
            "name": "StructureSubsystem",
            "type": "structure",
            "target_path": recommendation.path,
            "recommendation_type": recommendation.type,
            "code_size": 1200  # Placeholder
        })
        
        # Update state tree
        await self._add_subsystem_to_state_tree(
            state_tree,
            "StructureSubsystem",
            "structure",
            recommendation.path,
            {
                "handled_paths": [recommendation.path],
                "structure_type": "completion"
            }
        )
    
    async def _generate_performance_subsystem(
        self,
        recommendation: Recommendation,
        state_tree: StateTree,
        result: DifferentiationResult
    ) -> None:
        """
        Generate a performance optimization subsystem.
        
        Args:
            recommendation: Recommendation to process
            state_tree: Current state tree
            result: Differentiation result to update
        """
        # Similar implementation to other subsystem generators
        # Simplified for brevity
        result.add_generated_subsystem({
            "name": "PerformanceSubsystem",
            "type": "performance",
            "target_path": recommendation.path,
            "recommendation_type": recommendation.type,
            "code_size": 1500  # Placeholder
        })
        
        # Update state tree
        await self._add_subsystem_to_state_tree(
            state_tree,
            "PerformanceSubsystem",
            "performance",
            recommendation.path,
            {
                "handled_paths": [recommendation.path],
                "optimization_type": "performance"
            }
        )
    
    async def _specialize_subsystem(
        self,
        subsystem_node: StateNode,
        pattern: Pattern,
        state_tree: StateTree,
        result: DifferentiationResult
    ) -> None:
        """
        Specialize an existing subsystem based on a pattern.
        
        Args:
            subsystem_node: Subsystem node to specialize
            pattern: Pattern to use for specialization
            state_tree: Current state tree
            result: Differentiation result to update
        """
        self.logger.debug(f"Specializing subsystem {subsystem_node.id} for pattern {pattern.type}")
        
        # In a real implementation, this would modify the subsystem code
        # For now, we'll just update the subsystem metadata
        
        # Update subsystem data
        if "specializations" not in subsystem_node.data:
            subsystem_node.data["specializations"] = []
            
        subsystem_node.data["specializations"].append({
            "pattern_type": pattern.type,
            "pattern_path": pattern.path,
            "confidence": pattern.confidence,
            "applied_at": datetime.now().isoformat()
        })
        
        # Update version
        if "version" in subsystem_node.data:
            version_parts = subsystem_node.data["version"].split(".")
            version_parts[-1] = str(int(version_parts[-1]) + 1)
            subsystem_node.data["version"] = ".".join(version_parts)
        
        # Add to result
        result.add_modified_subsystem({
            "id": subsystem_node.id,
            "type": subsystem_node.type,
            "pattern_type": pattern.type,
            "pattern_path": pattern.path
        })
    
    async def _add_subsystem_to_state_tree(
        self,
        state_tree: StateTree,
        name: str,
        subsystem_type: str,
        target_path: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Add a subsystem to the state tree.
        
        Args:
            state_tree: State tree to update
            name: Subsystem name
            subsystem_type: Subsystem type
            target_path: Target path for the subsystem
            data: Additional subsystem data
        """
        # Get the active subsystems node
        subsystems_node = state_tree.get_node("/runtime_state/active_subsystems")
        if not subsystems_node:
            self.logger.warning("Active subsystems node not found in state tree")
            return
            
        # Create subsystem node
        subsystem_node = StateNode(
            id=f"{name.lower()}_{int(time.time())}",
            type="subsystem",
            data={
                "name": name,
                "subsystem_type": subsystem_type,
                "target_path": target_path,
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "status": "initialized",
                **data
            },
            metadata={
                "description": f"{name} for {target_path}",
                "creator": "DifferentiationEngine"
            }
        )
        
        # Add to state tree
        state_tree.add_node(subsystem_node, parent_id=subsystems_node.id)
        
        self.logger.debug(f"Added subsystem {name} to state tree")
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the DifferentiationEngine."""
        self.logger.info("Shutting down DifferentiationEngine")
        
        # Clear templates
        self.templates.clear()
        
        self.logger.info("DifferentiationEngine shutdown complete")