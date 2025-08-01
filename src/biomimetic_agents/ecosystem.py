"""
RUBIK Biomimetic Ecosystem

This module provides the complete RUBIK ecosystem that integrates all components
of the biomimetic agent system with the 2025 advanced AI model stack.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ..local_processing import LocalAIPipeline, ProcessingMode, ProcessingRequest
from .agent_system import AgentStatus, BiomimeticAgent
from .cross_generational_learning import CrossGenerationalLearningSystem, KnowledgeBase
from .rubik_genome import Archetype, GenomePool, RUBIKGenome
from .thanatos_controller import LifecycleEvent, ThanatosController

logger = logging.getLogger(__name__)


@dataclass
class EcosystemConfig:
    """Configuration for the RUBIK ecosystem."""

    max_population: int = 50
    min_population: int = 10
    evolution_interval: float = 300.0  # 5 minutes
    learning_enabled: bool = True
    auto_scaling: bool = True
    model_preferences: Dict[str, str] = None

    def __post_init__(self):
        if self.model_preferences is None:
            # Default 2025 advanced model stack
            self.model_preferences = {
                "reasoning_primary": "minimax-m1-80k",
                "reasoning_fallback": "kimi-k2-instruct",
                "coding_primary": "qwen3-coder-480b-a35b",
                "coding_fallback": "qwen2.5-coder-32b",
                "multimodal_primary": "flux-kontext-max",
                "multimodal_fallback": "flux-dev",
                "local_backbone": "mamba-codestral-7b",
                "local_fallback": "llama-3.3-8b",
            }


class RUBIKEcosystem:
    """
    Complete RUBIK Biomimetic Agent Ecosystem.

    This class orchestrates the entire biomimetic agent system, integrating
    genetic evolution, agent lifecycle management, cross-generational learning,
    and advanced AI model routing for transcendent capabilities.
    """

    def __init__(
        self,
        config: Optional[EcosystemConfig] = None,
        ai_pipeline: Optional[LocalAIPipeline] = None,
    ):
        self.config = config or EcosystemConfig()
        self.ai_pipeline = ai_pipeline

        # Core components
        self.knowledge_base = KnowledgeBase()
        self.learning_system = CrossGenerationalLearningSystem(self.knowledge_base)
        self.thanatos_controller = ThanatosController(
            ai_pipeline=ai_pipeline,
            max_population=self.config.max_population,
            min_population=self.config.min_population,
        )

        # Task management
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_tasks: List[Dict[str, Any]] = []

        # Performance tracking
        self.ecosystem_metrics = {
            "total_tasks_processed": 0,
            "successful_tasks": 0,
            "average_processing_time": 0.0,
            "total_energy_consumed": 0.0,
            "agent_generations": 0,
            "knowledge_fragments": 0,
            "ecosystem_uptime": 0.0,
        }

        # Event system
        self.event_callbacks: Dict[str, List[Callable]] = {
            "task_completed": [],
            "agent_born": [],
            "agent_died": [],
            "evolution_cycle": [],
            "knowledge_inherited": [],
        }

        # Control flags
        self.running = False
        self.start_time = None

        # Register for Thanatos events
        self._register_thanatos_callbacks()

        logger.info("Initialized RUBIK Biomimetic Ecosystem")

    def _register_thanatos_callbacks(self):
        """Register callbacks for Thanatos controller events."""

        async def on_agent_birth(event_type, data):
            await self._on_agent_birth(data)

        async def on_agent_death(event_type, data):
            await self._on_agent_death(data)

        self.thanatos_controller.register_event_callback(
            LifecycleEvent.BIRTH, on_agent_birth
        )
        self.thanatos_controller.register_event_callback(
            LifecycleEvent.DEATH, on_agent_death
        )

    async def start(self):
        """Start the RUBIK ecosystem."""
        if self.running:
            logger.warning("RUBIK Ecosystem already running")
            return

        self.running = True
        self.start_time = time.time()

        logger.info("Starting RUBIK Biomimetic Ecosystem")

        # Start core components
        await self.thanatos_controller.start()

        # Start task processing
        asyncio.create_task(self._task_processing_loop())

        # Start metrics update loop
        asyncio.create_task(self._metrics_update_loop())

        logger.info(
            f"RUBIK Ecosystem started with {len(self.thanatos_controller.active_agents)} agents"
        )

    async def stop(self):
        """Stop the RUBIK ecosystem."""
        logger.info("Stopping RUBIK Ecosystem")

        self.running = False

        # Stop core components
        await self.thanatos_controller.stop()

        # Wait for active tasks to complete
        while self.active_tasks:
            await asyncio.sleep(0.1)

        logger.info("RUBIK Ecosystem stopped")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task using the biomimetic agent ecosystem.

        Args:
            task: Task specification

        Returns:
            Task result with ecosystem metadata
        """
        task_id = task.get("id", f"task_{int(time.time())}")
        task["id"] = task_id

        # Add to queue
        await self.task_queue.put(task)

        # Wait for completion
        start_time = time.time()
        timeout = task.get("timeout", 60.0)

        while task_id not in [t["task_id"] for t in self.completed_tasks]:
            if time.time() - start_time > timeout:
                return {"success": False, "error": "Task timeout", "task_id": task_id}

            await asyncio.sleep(0.1)

        # Find and return completed task result
        for completed_task in self.completed_tasks:
            if completed_task["task_id"] == task_id:
                return completed_task["result"]

        return {"success": False, "error": "Task result not found", "task_id": task_id}

    async def _task_processing_loop(self):
        """Main task processing loop."""
        logger.info("Starting task processing loop")

        while self.running:
            try:
                # Get next task
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)

                # Process task
                result = await self._process_single_task(task)

                # Store result
                self.completed_tasks.append(
                    {
                        "task_id": task["id"],
                        "task": task,
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

                # Limit completed tasks history
                if len(self.completed_tasks) > 1000:
                    self.completed_tasks = self.completed_tasks[-1000:]

                # Mark task as done
                self.task_queue.task_done()

            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error in task processing loop: {e}")
                await asyncio.sleep(1.0)

    async def _process_single_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single task using the best available agent."""
        task_id = task["id"]
        start_time = time.time()

        try:
            # Select best agent for task
            selected_agent = await self._select_agent_for_task(task)

            if not selected_agent:
                return {
                    "success": False,
                    "error": "No suitable agent available",
                    "task_id": task_id,
                    "processing_time": time.time() - start_time,
                }

            # Add to active tasks
            self.active_tasks[task_id] = {
                "task": task,
                "agent_id": selected_agent.agent_id,
                "start_time": start_time,
            }

            # Process with selected agent
            agent_result = await selected_agent.process_task(task)

            # Record learning experience if enabled
            if self.config.learning_enabled:
                await self.learning_system.record_learning_experience(
                    selected_agent, task, agent_result
                )

            # Update ecosystem metrics
            self._update_task_metrics(agent_result)

            # Trigger callbacks
            await self._trigger_event_callbacks(
                "task_completed",
                {
                    "task": task,
                    "result": agent_result,
                    "agent_id": selected_agent.agent_id,
                },
            )

            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            # Add ecosystem metadata
            ecosystem_result = agent_result.copy()
            ecosystem_result.update(
                {
                    "ecosystem_metadata": {
                        "agent_id": selected_agent.agent_id,
                        "agent_archetype": selected_agent.archetype.value,
                        "agent_generation": selected_agent.genome.generation,
                        "agent_fitness": selected_agent.calculate_fitness(),
                        "ecosystem_population": len(
                            self.thanatos_controller.active_agents
                        ),
                        "knowledge_fragments_used": self._count_knowledge_usage(
                            agent_result
                        ),
                    }
                }
            )

            return ecosystem_result

        except Exception as e:
            logger.error(f"Task processing failed: {e}")

            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

            return {
                "success": False,
                "error": str(e),
                "task_id": task_id,
                "processing_time": time.time() - start_time,
            }

    async def _select_agent_for_task(
        self, task: Dict[str, Any]
    ) -> Optional[BiomimeticAgent]:
        """Select the best agent for a given task."""
        task_type = task.get("task_type", "general")
        available_agents = [
            agent
            for agent in self.thanatos_controller.active_agents.values()
            if agent.status == AgentStatus.ACTIVE
        ]

        if not available_agents:
            return None

        # Score agents based on task suitability
        agent_scores = []

        for agent in available_agents:
            score = await self._calculate_agent_task_score(agent, task)
            agent_scores.append((agent, score))

        # Sort by score and select best
        agent_scores.sort(key=lambda x: x[1], reverse=True)

        # Add some randomness to prevent always using the same agent
        top_agents = agent_scores[: min(3, len(agent_scores))]
        weights = [score for _, score in top_agents]

        if sum(weights) > 0:
            # Weighted random selection from top agents
            import random

            selected_agent = random.choices(
                [agent for agent, _ in top_agents], weights=weights
            )[0]
            return selected_agent

        return agent_scores[0][0] if agent_scores else None

    async def _calculate_agent_task_score(
        self, agent: BiomimeticAgent, task: Dict[str, Any]
    ) -> float:
        """Calculate how suitable an agent is for a task."""
        base_score = 0.0

        # Archetype suitability
        task_type = task.get("task_type", "general")
        archetype_scores = {
            "analysis": {
                Archetype.EXPLORER: 0.8,
                Archetype.GUARDIAN: 0.6,
                Archetype.CREATOR: 0.7,
                Archetype.DESTROYER: 0.5,
            },
            "coding": {
                Archetype.CREATOR: 0.9,
                Archetype.EXPLORER: 0.7,
                Archetype.GUARDIAN: 0.5,
                Archetype.DESTROYER: 0.6,
            },
            "security": {
                Archetype.GUARDIAN: 0.9,
                Archetype.DESTROYER: 0.7,
                Archetype.EXPLORER: 0.6,
                Archetype.CREATOR: 0.4,
            },
            "optimization": {
                Archetype.DESTROYER: 0.9,
                Archetype.CREATOR: 0.7,
                Archetype.GUARDIAN: 0.6,
                Archetype.EXPLORER: 0.5,
            },
            "discovery": {
                Archetype.EXPLORER: 0.9,
                Archetype.CREATOR: 0.6,
                Archetype.GUARDIAN: 0.4,
                Archetype.DESTROYER: 0.5,
            },
        }

        if task_type in archetype_scores:
            base_score += archetype_scores[task_type].get(agent.archetype, 0.5)
        else:
            base_score += 0.5  # Neutral score for unknown task types

        # Fitness score
        base_score += agent.calculate_fitness() * 0.3

        # Experience with similar tasks
        similar_tasks = [
            task_record
            for task_record in agent.completed_tasks
            if task_record["task"].get("task_type") == task_type
        ]

        if similar_tasks:
            success_rate = sum(
                1
                for task_record in similar_tasks
                if task_record["result"].get("success", False)
            ) / len(similar_tasks)
            base_score += success_rate * 0.2

        # Current workload (prefer less busy agents)
        workload_penalty = len(agent.active_tasks) * 0.1
        base_score -= workload_penalty

        # Mood suitability
        mood_bonuses = {
            "focused": 0.1 if task.get("complexity", 0.5) > 0.7 else 0.0,
            "excited": 0.1 if task_type in ["discovery", "creative"] else 0.0,
            "calm": 0.1 if task_type in ["analysis", "security"] else 0.0,
            "confident": 0.05,  # General bonus
        }

        base_score += mood_bonuses.get(agent.current_mood.value, 0.0)

        return max(0.0, min(1.0, base_score))

    def _count_knowledge_usage(self, result: Dict[str, Any]) -> int:
        """Count how many knowledge fragments were used in processing."""
        # This would be implemented based on how knowledge usage is tracked
        # For now, return a placeholder
        return 0

    def _update_task_metrics(self, result: Dict[str, Any]):
        """Update ecosystem-level task metrics."""
        self.ecosystem_metrics["total_tasks_processed"] += 1

        if result.get("success", False):
            self.ecosystem_metrics["successful_tasks"] += 1

        processing_time = result.get("processing_time", 0.0)
        total_tasks = self.ecosystem_metrics["total_tasks_processed"]
        current_avg = self.ecosystem_metrics["average_processing_time"]

        self.ecosystem_metrics["average_processing_time"] = (
            current_avg * (total_tasks - 1) + processing_time
        ) / total_tasks

        energy_consumed = result.get("energy_consumed", 0.0)
        self.ecosystem_metrics["total_energy_consumed"] += energy_consumed

    async def _metrics_update_loop(self):
        """Update ecosystem metrics periodically."""
        while self.running:
            try:
                # Update uptime
                if self.start_time:
                    self.ecosystem_metrics["ecosystem_uptime"] = (
                        time.time() - self.start_time
                    )

                # Update population metrics
                population_summary = self.thanatos_controller.get_population_summary()
                self.ecosystem_metrics["agent_generations"] = population_summary[
                    "genome_pool_stats"
                ]["generation"]

                # Update knowledge metrics
                learning_stats = self.learning_system.get_inheritance_statistics()
                self.ecosystem_metrics["knowledge_fragments"] = learning_stats[
                    "total_knowledge_fragments"
                ]

                await asyncio.sleep(30.0)  # Update every 30 seconds

            except Exception as e:
                logger.error(f"Error in metrics update loop: {e}")
                await asyncio.sleep(10.0)

    async def _on_agent_birth(self, data: Dict[str, Any]):
        """Handle agent birth events."""
        agent = data.get("agent")
        if agent and self.config.learning_enabled:
            # Inherit knowledge from previous generations
            await self.learning_system.inherit_knowledge(agent, "selective_inheritance")

        # Trigger callbacks
        await self._trigger_event_callbacks("agent_born", data)

    async def _on_agent_death(self, data: Dict[str, Any]):
        """Handle agent death events."""
        # Trigger callbacks
        await self._trigger_event_callbacks("agent_died", data)

    async def _trigger_event_callbacks(self, event_type: str, data: Dict[str, Any]):
        """Trigger registered event callbacks."""
        for callback in self.event_callbacks.get(event_type, []):
            try:
                await callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in event callback for {event_type}: {e}")

    def register_event_callback(self, event_type: str, callback: Callable):
        """Register a callback for ecosystem events."""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []

        self.event_callbacks[event_type].append(callback)
        logger.info(f"Registered callback for {event_type} events")

    def get_ecosystem_status(self) -> Dict[str, Any]:
        """Get comprehensive ecosystem status."""
        population_summary = self.thanatos_controller.get_population_summary()
        learning_stats = self.learning_system.get_inheritance_statistics()

        return {
            "running": self.running,
            "uptime_seconds": self.ecosystem_metrics["ecosystem_uptime"],
            "population": population_summary,
            "learning": learning_stats,
            "task_metrics": self.ecosystem_metrics.copy(),
            "active_tasks": len(self.active_tasks),
            "queue_size": self.task_queue.qsize(),
            "config": {
                "max_population": self.config.max_population,
                "min_population": self.config.min_population,
                "learning_enabled": self.config.learning_enabled,
                "auto_scaling": self.config.auto_scaling,
            },
        }

    def get_agent_details(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific agent."""
        agent = self.thanatos_controller.get_agent(agent_id)
        if agent:
            return agent.get_status_summary()
        return None

    def get_agents_by_archetype(self, archetype: Archetype) -> List[Dict[str, Any]]:
        """Get all agents of a specific archetype."""
        agents = self.thanatos_controller.get_agents_by_archetype(archetype)
        return [agent.get_status_summary() for agent in agents]

    async def force_evolution_cycle(self) -> Dict[str, Any]:
        """Force an evolution cycle."""
        return self.thanatos_controller.genome_pool.evolve_generation()

    async def create_agent_with_genome(self, genome: RUBIKGenome) -> str:
        """Create a new agent with a specific genome."""
        agent = BiomimeticAgent(genome, ai_pipeline=self.ai_pipeline)
        await self.thanatos_controller._birth_agent(agent)
        return agent.agent_id

    def save_ecosystem_state(self, directory: Path):
        """Save complete ecosystem state."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        # Save Thanatos state
        thanatos_path = directory / "thanatos_state.json"
        self.thanatos_controller.save_state(str(thanatos_path))

        # Save knowledge base
        knowledge_path = directory / "knowledge_base.json"
        self.learning_system.save_knowledge_base(str(knowledge_path))

        # Save ecosystem config and metrics
        ecosystem_path = directory / "ecosystem_state.json"
        ecosystem_data = {
            "config": {
                "max_population": self.config.max_population,
                "min_population": self.config.min_population,
                "evolution_interval": self.config.evolution_interval,
                "learning_enabled": self.config.learning_enabled,
                "auto_scaling": self.config.auto_scaling,
                "model_preferences": self.config.model_preferences,
            },
            "metrics": self.ecosystem_metrics,
            "completed_tasks_count": len(self.completed_tasks),
        }

        with open(ecosystem_path, "w") as f:
            json.dump(ecosystem_data, f, indent=2)

        logger.info(f"Saved ecosystem state to {directory}")

    def load_ecosystem_state(self, directory: Path):
        """Load complete ecosystem state."""
        directory = Path(directory)

        # Load Thanatos state
        thanatos_path = directory / "thanatos_state.json"
        if thanatos_path.exists():
            self.thanatos_controller.load_state(str(thanatos_path))

        # Load knowledge base
        knowledge_path = directory / "knowledge_base.json"
        if knowledge_path.exists():
            self.learning_system.load_knowledge_base(str(knowledge_path))

        # Load ecosystem config and metrics
        ecosystem_path = directory / "ecosystem_state.json"
        if ecosystem_path.exists():
            with open(ecosystem_path, "r") as f:
                ecosystem_data = json.load(f)

            # Restore config
            config_data = ecosystem_data.get("config", {})
            self.config.max_population = config_data.get("max_population", 50)
            self.config.min_population = config_data.get("min_population", 10)
            self.config.evolution_interval = config_data.get(
                "evolution_interval", 300.0
            )
            self.config.learning_enabled = config_data.get("learning_enabled", True)
            self.config.auto_scaling = config_data.get("auto_scaling", True)
            self.config.model_preferences = config_data.get("model_preferences", {})

            # Restore metrics
            self.ecosystem_metrics.update(ecosystem_data.get("metrics", {}))

        logger.info(f"Loaded ecosystem state from {directory}")


async def create_rubik_ecosystem(
    config: Optional[EcosystemConfig] = None,
    ai_pipeline: Optional[LocalAIPipeline] = None,
) -> RUBIKEcosystem:
    """
    Create and start a complete RUBIK biomimetic ecosystem.

    Args:
        config: Ecosystem configuration
        ai_pipeline: Local AI processing pipeline

    Returns:
        Started RUBIK ecosystem
    """
    ecosystem = RUBIKEcosystem(config, ai_pipeline)
    await ecosystem.start()
    return ecosystem
