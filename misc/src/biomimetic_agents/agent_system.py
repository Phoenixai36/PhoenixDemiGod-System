"""
RUBIK Biomimetic Agent System - Core Agent Implementation

This module implements the self-evolving biomimetic agents that integrate
with the 2025 advanced AI model ecosystem for transcendent capabilities.
"""

import asyncio
import json
import logging
import random
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..local_processing import LocalAIPipeline, ProcessingMode, ProcessingRequest
from .rubik_genome import Archetype, GeneticBase, MoodState, RUBIKGenome

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent lifecycle status."""

    NASCENT = "nascent"  # Just created, not yet active
    ACTIVE = "active"  # Fully operational
    LEARNING = "learning"  # In adaptation phase
    REPRODUCING = "reproducing"  # Creating offspring
    DECLINING = "declining"  # Performance degrading
    TERMINATED = "terminated"  # Marked for termination


@dataclass
class AgentMemory:
    """Agent memory system for learning and adaptation."""

    short_term: Dict[str, Any]  # Recent experiences
    long_term: Dict[str, Any]  # Persistent knowledge
    episodic: List[Dict[str, Any]]  # Specific experiences
    semantic: Dict[str, Any]  # General knowledge
    procedural: Dict[str, Any]  # Learned skills

    def __post_init__(self):
        """Initialize memory structures."""
        if not self.short_term:
            self.short_term = {}
        if not self.long_term:
            self.long_term = {}
        if not self.episodic:
            self.episodic = []
        if not self.semantic:
            self.semantic = {}
        if not self.procedural:
            self.procedural = {}


@dataclass
class AgentPerformanceMetrics:
    """Performance tracking for agent evaluation."""

    task_success_rate: float = 0.0
    energy_efficiency: float = 0.0
    adaptation_speed: float = 0.0
    error_rate: float = 0.0
    collaboration_score: float = 0.0
    discovery_rate: float = 0.0
    security_score: float = 0.0
    innovation_score: float = 0.0
    optimization_score: float = 0.0
    total_tasks_completed: int = 0
    total_energy_consumed: float = 0.0
    learning_rate: float = 0.0

    def update_from_task(self, task_result: Dict[str, Any]):
        """Update metrics from a completed task."""
        success = task_result.get("success", False)
        energy_used = task_result.get("energy_consumed", 0.0)
        processing_time = task_result.get("processing_time", 0.0)

        # Update running averages
        self.total_tasks_completed += 1
        self.total_energy_consumed += energy_used

        # Task success rate
        current_success_rate = self.task_success_rate
        self.task_success_rate = (
            current_success_rate * (self.total_tasks_completed - 1)
            + (1.0 if success else 0.0)
        ) / self.total_tasks_completed

        # Energy efficiency (tasks per joule)
        if self.total_energy_consumed > 0:
            self.energy_efficiency = (
                self.total_tasks_completed / self.total_energy_consumed
            )

        # Error rate
        if not success:
            error_occurred = 1.0
        else:
            error_occurred = 0.0

        current_error_rate = self.error_rate
        self.error_rate = (
            current_error_rate * (self.total_tasks_completed - 1) + error_occurred
        ) / self.total_tasks_completed


class BiomimeticAgent:
    """
    Self-evolving biomimetic agent with genetic programming and mood system.

    This agent integrates with the 2025 advanced AI model ecosystem,
    using its genetic makeup to select optimal models and processing strategies.
    """

    def __init__(
        self,
        genome: RUBIKGenome,
        agent_id: Optional[str] = None,
        ai_pipeline: Optional[LocalAIPipeline] = None,
    ):
        self.genome = genome
        self.agent_id = agent_id or f"agent_{genome.genome_id[:8]}"
        self.ai_pipeline = ai_pipeline

        # Agent state
        self.status = AgentStatus.NASCENT
        self.current_mood = MoodState.CALM
        self.archetype = genome.determine_archetype()
        self.birth_time = datetime.now()
        self.last_activity = datetime.now()

        # Performance and learning
        self.performance_metrics = AgentPerformanceMetrics()
        self.memory = AgentMemory({}, {}, [], {}, {})
        self.active_tasks: Dict[str, Any] = {}
        self.completed_tasks: List[Dict[str, Any]] = []

        # Model preferences from genome
        self.model_preferences = genome.get_model_preferences()

        # Environmental awareness
        self.environmental_factors = {
            "novelty": 0.0,
            "task_complexity": 0.0,
            "threat_level": 0.0,
            "success_rate": 0.0,
            "information_availability": 0.0,
            "competition": 0.0,
            "resource_scarcity": 0.0,
            "complexity": 0.0,
        }

        # Lifecycle management
        self.age_in_cycles = 0
        self.reproduction_threshold = 0.8  # Fitness threshold for reproduction
        self.termination_threshold = 0.2  # Fitness threshold for termination

        logger.info(
            f"Created {self.archetype.value} agent {self.agent_id} "
            f"with genome {genome.genome_id[:8]}"
        )

    async def activate(self):
        """Activate the agent and begin its lifecycle."""
        if self.status != AgentStatus.NASCENT:
            logger.warning(f"Agent {self.agent_id} already activated")
            return

        self.status = AgentStatus.ACTIVE
        self.last_activity = datetime.now()

        # Initialize based on archetype
        await self._initialize_archetype_behavior()

        logger.info(f"Activated {self.archetype.value} agent {self.agent_id}")

    async def _initialize_archetype_behavior(self):
        """Initialize behavior patterns based on archetype."""
        if self.archetype == Archetype.EXPLORER:
            self.environmental_factors["novelty"] = 0.8
            self.environmental_factors["information_availability"] = 0.7
            await self._initialize_explorer_behavior()

        elif self.archetype == Archetype.GUARDIAN:
            self.environmental_factors["threat_level"] = 0.6
            self.environmental_factors["complexity"] = 0.5
            await self._initialize_guardian_behavior()

        elif self.archetype == Archetype.CREATOR:
            self.environmental_factors["novelty"] = 0.7
            self.environmental_factors["complexity"] = 0.8
            await self._initialize_creator_behavior()

        elif self.archetype == Archetype.DESTROYER:
            self.environmental_factors["competition"] = 0.7
            self.environmental_factors["resource_scarcity"] = 0.6
            await self._initialize_destroyer_behavior()

    async def _initialize_explorer_behavior(self):
        """Initialize Explorer archetype specific behavior."""
        self.memory.semantic["exploration_strategies"] = [
            "systematic_scanning",
            "random_sampling",
            "pattern_following",
            "anomaly_detection",
        ]

        self.memory.procedural["discovery_protocols"] = {
            "data_source_identification": 0.8,
            "pattern_recognition": 0.7,
            "novelty_detection": 0.9,
            "information_synthesis": 0.6,
        }

    async def _initialize_guardian_behavior(self):
        """Initialize Guardian archetype specific behavior."""
        self.memory.semantic["security_protocols"] = [
            "threat_assessment",
            "vulnerability_scanning",
            "access_control",
            "incident_response",
        ]

        self.memory.procedural["protection_strategies"] = {
            "monitoring_systems": 0.9,
            "anomaly_detection": 0.8,
            "response_coordination": 0.7,
            "recovery_procedures": 0.8,
        }

    async def _initialize_creator_behavior(self):
        """Initialize Creator archetype specific behavior."""
        self.memory.semantic["creation_methods"] = [
            "iterative_design",
            "combinatorial_synthesis",
            "emergent_construction",
            "adaptive_refinement",
        ]

        self.memory.procedural["innovation_skills"] = {
            "concept_generation": 0.8,
            "prototype_development": 0.7,
            "solution_optimization": 0.8,
            "creative_synthesis": 0.9,
        }

    async def _initialize_destroyer_behavior(self):
        """Initialize Destroyer archetype specific behavior."""
        self.memory.semantic["optimization_targets"] = [
            "redundancy_elimination",
            "efficiency_maximization",
            "resource_consolidation",
            "performance_enhancement",
        ]

        self.memory.procedural["elimination_strategies"] = {
            "bottleneck_identification": 0.8,
            "waste_elimination": 0.9,
            "process_streamlining": 0.7,
            "resource_optimization": 0.8,
        }

    def update_mood(self):
        """Update agent mood based on current environmental factors and genetics."""
        self.current_mood = self.genome.calculate_mood_state(self.environmental_factors)
        logger.debug(f"Agent {self.agent_id} mood updated to {self.current_mood.value}")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task using the agent's genetic preferences and current mood.

        Args:
            task: Task specification with input data and requirements

        Returns:
            Task result with performance metrics
        """
        if self.status not in [AgentStatus.ACTIVE, AgentStatus.LEARNING]:
            return {
                "success": False,
                "error": f"Agent {self.agent_id} not in active state: {self.status.value}",
            }

        task_id = task.get("id", f"task_{int(time.time())}")
        self.active_tasks[task_id] = task

        start_time = time.time()

        try:
            # Update mood based on task complexity
            self.environmental_factors["task_complexity"] = task.get("complexity", 0.5)
            self.update_mood()

            # Select optimal model based on genetics and mood
            selected_model = await self._select_model_for_task(task)

            # Determine processing mode based on genetic traits
            processing_mode = self._determine_processing_mode()

            # Create processing request
            processing_request = ProcessingRequest(
                id=task_id,
                input_data=task.get("input_data", ""),
                task_type=task.get("task_type", "general"),
                model_preference=selected_model,
                mode=processing_mode,
                max_processing_time=task.get("max_time", 30.0),
            )

            # Process with AI pipeline if available
            if self.ai_pipeline:
                request_id = await self.ai_pipeline.submit_request(processing_request)
                result = await self.ai_pipeline.get_result(request_id, timeout=60.0)

                if result and result.success:
                    task_result = {
                        "success": True,
                        "result": result.result,
                        "model_used": result.model_used,
                        "processing_time": result.processing_time,
                        "energy_consumed": result.energy_consumed or 0.0,
                        "fallback_used": result.fallback_used,
                        "agent_mood": self.current_mood.value,
                        "agent_archetype": self.archetype.value,
                    }
                else:
                    task_result = {
                        "success": False,
                        "error": result.error_message
                        if result
                        else "Processing failed",
                        "processing_time": time.time() - start_time,
                        "agent_mood": self.current_mood.value,
                        "agent_archetype": self.archetype.value,
                    }
            else:
                # Simulate processing without pipeline
                await asyncio.sleep(0.1)
                task_result = {
                    "success": True,
                    "result": f"Simulated result for {task.get('task_type', 'general')} task",
                    "model_used": selected_model,
                    "processing_time": time.time() - start_time,
                    "energy_consumed": random.uniform(0.1, 1.0),
                    "fallback_used": False,
                    "agent_mood": self.current_mood.value,
                    "agent_archetype": self.archetype.value,
                }

            # Update performance metrics
            self.performance_metrics.update_from_task(task_result)

            # Store in memory
            self._store_task_memory(task, task_result)

            # Update environmental factors based on success
            if task_result["success"]:
                self.environmental_factors["success_rate"] = min(
                    1.0, self.environmental_factors["success_rate"] + 0.1
                )
            else:
                self.environmental_factors["success_rate"] = max(
                    0.0, self.environmental_factors["success_rate"] - 0.1
                )

            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            # Add to completed tasks
            self.completed_tasks.append(
                {
                    "task": task,
                    "result": task_result,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Update last activity
            self.last_activity = datetime.now()

            return task_result

        except Exception as e:
            logger.error(f"Task processing failed for agent {self.agent_id}: {e}")

            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            error_result = {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time,
                "agent_mood": self.current_mood.value,
                "agent_archetype": self.archetype.value,
            }

            self.performance_metrics.update_from_task(error_result)
            return error_result

    async def _select_model_for_task(self, task: Dict[str, Any]) -> str:
        """Select optimal AI model based on genetics, mood, and task requirements."""
        task_type = task.get("task_type", "general")

        # Base selection on genetic preferences
        if task_type in ["reasoning", "analysis", "complex_problem_solving"]:
            base_model = self.model_preferences.get(
                "primary_reasoning", "kimi-k2-instruct"
            )
        elif task_type in ["coding", "programming", "software_development"]:
            base_model = self.model_preferences.get(
                "primary_coding", "qwen2.5-coder-32b"
            )
        elif task_type in ["image_generation", "multimodal", "creative"]:
            base_model = self.model_preferences.get("multimodal", "flux-dev")
        else:
            base_model = self.model_preferences.get("local_backbone", "llama-3.3-8b")

        # Modify selection based on current mood
        if self.current_mood == MoodState.EXCITED:
            # Prefer more powerful models when excited
            if "lite" in base_model or "small" in base_model:
                base_model = base_model.replace("lite", "default").replace(
                    "small", "large"
                )
        elif self.current_mood == MoodState.ANXIOUS:
            # Prefer more reliable, smaller models when anxious
            if "large" in base_model:
                base_model = base_model.replace("large", "small")
        elif self.current_mood == MoodState.FOCUSED:
            # Prefer precision models when focused
            if task_type == "coding":
                base_model = "qwen3-coder-480b-a35b"  # Highest precision coding model

        return base_model

    def _determine_processing_mode(self) -> ProcessingMode:
        """Determine processing mode based on genetic traits and mood."""
        efficiency_level = self.genome.get_effective_expression(GeneticBase.EFFICIENCY)
        speed_level = self.genome.get_effective_expression(GeneticBase.SPEED)
        precision_level = self.genome.get_effective_expression(GeneticBase.PRECISION)

        # High efficiency preference
        if efficiency_level > 1.5:
            return ProcessingMode.ENERGY_EFFICIENT

        # High speed preference with low precision tolerance
        elif speed_level > 1.3 and precision_level < 1.0:
            return ProcessingMode.MINIMAL_RESOURCES

        # High precision preference
        elif precision_level > 1.4:
            return ProcessingMode.FULL_CAPABILITY

        # Mood-based adjustments
        elif self.current_mood == MoodState.ANXIOUS:
            return ProcessingMode.OFFLINE_ONLY
        elif self.current_mood == MoodState.EXCITED:
            return ProcessingMode.FULL_CAPABILITY

        # Default balanced mode
        return ProcessingMode.ENERGY_EFFICIENT

    def _store_task_memory(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Store task experience in agent memory."""
        # Short-term memory (recent experiences)
        task_key = f"task_{len(self.completed_tasks)}"
        self.memory.short_term[task_key] = {
            "task_type": task.get("task_type"),
            "success": result["success"],
            "processing_time": result["processing_time"],
            "model_used": result.get("model_used"),
            "timestamp": datetime.now().isoformat(),
        }

        # Episodic memory (specific experiences)
        episode = {
            "task": task,
            "result": result,
            "mood_during_task": self.current_mood.value,
            "environmental_factors": self.environmental_factors.copy(),
            "timestamp": datetime.now().isoformat(),
        }
        self.memory.episodic.append(episode)

        # Limit episodic memory size
        if len(self.memory.episodic) > 1000:
            self.memory.episodic = self.memory.episodic[-1000:]

        # Update semantic memory (general knowledge)
        task_type = task.get("task_type", "general")
        if task_type not in self.memory.semantic:
            self.memory.semantic[task_type] = {
                "total_attempts": 0,
                "successful_attempts": 0,
                "average_processing_time": 0.0,
                "preferred_models": {},
                "common_patterns": [],
            }

        semantic_entry = self.memory.semantic[task_type]
        semantic_entry["total_attempts"] += 1

        if result["success"]:
            semantic_entry["successful_attempts"] += 1

        # Update average processing time
        current_avg = semantic_entry["average_processing_time"]
        total_attempts = semantic_entry["total_attempts"]
        semantic_entry["average_processing_time"] = (
            current_avg * (total_attempts - 1) + result["processing_time"]
        ) / total_attempts

        # Track model preferences
        model_used = result.get("model_used", "unknown")
        if model_used not in semantic_entry["preferred_models"]:
            semantic_entry["preferred_models"][model_used] = {"uses": 0, "successes": 0}

        semantic_entry["preferred_models"][model_used]["uses"] += 1
        if result["success"]:
            semantic_entry["preferred_models"][model_used]["successes"] += 1

    def calculate_fitness(self) -> float:
        """Calculate current fitness score based on performance metrics."""
        metrics = self.performance_metrics

        # Base fitness from performance metrics
        base_fitness = (
            metrics.task_success_rate * 0.3
            + metrics.energy_efficiency * 0.2
            + metrics.adaptation_speed * 0.2
            + (1.0 - metrics.error_rate) * 0.15
            + metrics.collaboration_score * 0.15
        )

        # Archetype-specific bonuses
        if self.archetype == Archetype.EXPLORER:
            base_fitness += metrics.discovery_rate * 0.1
        elif self.archetype == Archetype.GUARDIAN:
            base_fitness += metrics.security_score * 0.1
        elif self.archetype == Archetype.CREATOR:
            base_fitness += metrics.innovation_score * 0.1
        elif self.archetype == Archetype.DESTROYER:
            base_fitness += metrics.optimization_score * 0.1

        # Age penalty (agents decline over time)
        age_penalty = min(0.2, self.age_in_cycles * 0.01)
        base_fitness -= age_penalty

        # Activity bonus (recently active agents get bonus)
        time_since_activity = (datetime.now() - self.last_activity).total_seconds()
        if time_since_activity < 3600:  # Active within last hour
            base_fitness += 0.05

        return max(0.0, min(1.0, base_fitness))

    def should_reproduce(self) -> bool:
        """Determine if agent should reproduce based on fitness and age."""
        fitness = self.calculate_fitness()

        # Must meet fitness threshold
        if fitness < self.reproduction_threshold:
            return False

        # Must be mature enough (at least 10 cycles old)
        if self.age_in_cycles < 10:
            return False

        # Must not be too old (reproduction declines with age)
        if self.age_in_cycles > 100:
            reproduction_probability = max(0.1, 1.0 - (self.age_in_cycles - 100) * 0.01)
            return random.random() < reproduction_probability

        return True

    def should_terminate(self) -> bool:
        """Determine if agent should be terminated (Thanatos controller)."""
        fitness = self.calculate_fitness()

        # Terminate if fitness too low
        if fitness < self.termination_threshold:
            return True

        # Terminate if too old and declining
        if self.age_in_cycles > 200:
            termination_probability = (self.age_in_cycles - 200) * 0.005
            return random.random() < termination_probability

        # Terminate if inactive for too long
        time_since_activity = (datetime.now() - self.last_activity).total_seconds()
        if time_since_activity > 86400:  # 24 hours
            return True

        return False

    def age_cycle(self):
        """Advance agent age by one cycle."""
        self.age_in_cycles += 1

        # Update status based on age and performance
        fitness = self.calculate_fitness()

        if self.should_terminate():
            self.status = AgentStatus.DECLINING
        elif self.should_reproduce() and self.status == AgentStatus.ACTIVE:
            self.status = AgentStatus.REPRODUCING
        elif fitness < 0.5:
            self.status = AgentStatus.LEARNING
        else:
            self.status = AgentStatus.ACTIVE

    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive agent status summary."""
        return {
            "agent_id": self.agent_id,
            "genome_id": self.genome.genome_id,
            "archetype": self.archetype.value,
            "status": self.status.value,
            "current_mood": self.current_mood.value,
            "age_in_cycles": self.age_in_cycles,
            "fitness_score": self.calculate_fitness(),
            "birth_time": self.birth_time.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "performance_metrics": asdict(self.performance_metrics),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "model_preferences": self.model_preferences,
            "environmental_factors": self.environmental_factors,
            "memory_stats": {
                "short_term_entries": len(self.memory.short_term),
                "episodic_memories": len(self.memory.episodic),
                "semantic_categories": len(self.memory.semantic),
                "procedural_skills": len(self.memory.procedural),
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "genome": self.genome.to_dict(),
            "status": self.status.value,
            "current_mood": self.current_mood.value,
            "archetype": self.archetype.value,
            "birth_time": self.birth_time.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "age_in_cycles": self.age_in_cycles,
            "performance_metrics": asdict(self.performance_metrics),
            "environmental_factors": self.environmental_factors,
            "model_preferences": self.model_preferences,
            "memory": {
                "short_term": self.memory.short_term,
                "long_term": self.memory.long_term,
                "episodic": self.memory.episodic[-100:],  # Limit size
                "semantic": self.memory.semantic,
                "procedural": self.memory.procedural,
            },
            "completed_tasks_count": len(self.completed_tasks),
        }

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], ai_pipeline: Optional[LocalAIPipeline] = None
    ) -> "BiomimeticAgent":
        """Create agent from dictionary."""
        genome = RUBIKGenome.from_dict(data["genome"])
        agent = cls(genome, data["agent_id"], ai_pipeline)

        agent.status = AgentStatus(data["status"])
        agent.current_mood = MoodState(data["current_mood"])
        agent.archetype = Archetype(data["archetype"])
        agent.birth_time = datetime.fromisoformat(data["birth_time"])
        agent.last_activity = datetime.fromisoformat(data["last_activity"])
        agent.age_in_cycles = data["age_in_cycles"]
        agent.environmental_factors = data["environmental_factors"]
        agent.model_preferences = data["model_preferences"]

        # Restore performance metrics
        metrics_data = data["performance_metrics"]
        agent.performance_metrics = AgentPerformanceMetrics(**metrics_data)

        # Restore memory
        memory_data = data["memory"]
        agent.memory = AgentMemory(
            short_term=memory_data["short_term"],
            long_term=memory_data["long_term"],
            episodic=memory_data["episodic"],
            semantic=memory_data["semantic"],
            procedural=memory_data["procedural"],
        )

        return agent
