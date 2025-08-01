"""
Thanatos Controller - Agent Lifecycle Management

This module implements the Thanatos controller that manages the life and death
cycles of biomimetic agents, enabling evolutionary pressure and system optimization.
"""

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from ..local_processing import LocalAIPipeline
from .agent_system import AgentStatus, BiomimeticAgent
from .rubik_genome import Archetype, GenomePool, RUBIKGenome

logger = logging.getLogger(__name__)


class LifecycleEvent(Enum):
    """Types of lifecycle events."""

    BIRTH = "birth"
    ACTIVATION = "activation"
    REPRODUCTION = "reproduction"
    DECLINE = "decline"
    DEATH = "death"
    RESURRECTION = "resurrection"


@dataclass
class LifecycleRecord:
    """Record of an agent lifecycle event."""

    agent_id: str
    event_type: LifecycleEvent
    timestamp: datetime
    details: Dict[str, Any]
    fitness_score: float
    age_in_cycles: int


class ThanatosController:
    """
    Manages the lifecycle of biomimetic agents including birth, death, and rebirth.

    Named after Thanatos, the Greek personification of death, this controller
    implements evolutionary pressure by terminating underperforming agents
    and creating new ones through genetic recombination.
    """

    def __init__(
        self,
        ai_pipeline: Optional[LocalAIPipeline] = None,
        max_population: int = 50,
        min_population: int = 10,
    ):
        self.ai_pipeline = ai_pipeline
        self.max_population = max_population
        self.min_population = min_population

        # Agent management
        self.active_agents: Dict[str, BiomimeticAgent] = {}
        self.genome_pool = GenomePool(initial_population_size=max_population)
        self.lifecycle_history: List[LifecycleRecord] = []

        # Evolution parameters
        self.evolution_cycle_interval = 300.0  # 5 minutes
        self.fitness_evaluation_window = 100  # Number of tasks to consider
        self.reproduction_cooldown = 60.0  # Seconds between reproductions
        self.last_reproduction_time = 0.0

        # Performance tracking
        self.population_stats = {
            "total_births": 0,
            "total_deaths": 0,
            "total_reproductions": 0,
            "average_lifespan": 0.0,
            "average_fitness": 0.0,
            "generation_count": 0,
        }

        # Event callbacks
        self.event_callbacks: Dict[LifecycleEvent, List[Callable]] = {
            event: [] for event in LifecycleEvent
        }

        # Control flags
        self.running = False
        self.evolution_enabled = True

        logger.info(
            f"Initialized Thanatos Controller: "
            f"max_pop={max_population}, min_pop={min_population}"
        )

    async def start(self):
        """Start the Thanatos controller and begin agent lifecycle management."""
        if self.running:
            logger.warning("Thanatos Controller already running")
            return

        self.running = True
        logger.info("Starting Thanatos Controller")

        # Initialize population with diverse agents
        await self._initialize_population()

        # Start lifecycle management loop
        asyncio.create_task(self._lifecycle_management_loop())

        logger.info(
            f"Thanatos Controller started with {len(self.active_agents)} agents"
        )

    async def stop(self):
        """Stop the Thanatos controller and terminate all agents."""
        logger.info("Stopping Thanatos Controller")
        self.running = False

        # Gracefully terminate all agents
        for agent in list(self.active_agents.values()):
            await self._terminate_agent(agent, "system_shutdown")

        logger.info("Thanatos Controller stopped")

    async def _initialize_population(self):
        """Initialize the agent population with diverse genomes."""
        logger.info("Initializing agent population")

        # Get diverse genomes from the pool
        diverse_genomes = self.genome_pool.get_diverse_genomes(self.min_population)

        # Create agents from genomes
        for genome in diverse_genomes:
            agent = BiomimeticAgent(genome, ai_pipeline=self.ai_pipeline)
            await self._birth_agent(agent)

        # Fill remaining slots with random genomes
        while len(self.active_agents) < self.max_population // 2:
            # Get a random high-fitness genome
            best_genomes = self.genome_pool.get_best_genomes(10)
            if best_genomes:
                selected_genome = random.choice(best_genomes)
                # Create a mutated version for diversity
                mutated_genome = selected_genome.mutate()
                agent = BiomimeticAgent(mutated_genome, ai_pipeline=self.ai_pipeline)
                await self._birth_agent(agent)
            else:
                break

        logger.info(f"Initialized population with {len(self.active_agents)} agents")

    async def _lifecycle_management_loop(self):
        """Main lifecycle management loop."""
        logger.info("Starting lifecycle management loop")

        while self.running:
            try:
                # Age all agents
                await self._age_population()

                # Evaluate fitness and update genome pool
                await self._evaluate_population_fitness()

                # Handle reproductions
                await self._handle_reproductions()

                # Handle terminations
                await self._handle_terminations()

                # Maintain population size
                await self._maintain_population()

                # Evolution cycle
                if self.evolution_enabled:
                    await self._evolution_cycle()

                # Update statistics
                self._update_population_stats()

                # Wait for next cycle
                await asyncio.sleep(self.evolution_cycle_interval)

            except Exception as e:
                logger.error(f"Error in lifecycle management loop: {e}")
                await asyncio.sleep(10.0)  # Short delay before retry

    async def _age_population(self):
        """Age all agents by one cycle."""
        for agent in self.active_agents.values():
            agent.age_cycle()

    async def _evaluate_population_fitness(self):
        """Evaluate fitness for all agents and update genome pool."""
        for agent in self.active_agents.values():
            fitness = agent.calculate_fitness()

            # Update genome fitness in pool
            performance_metrics = {
                "task_success_rate": agent.performance_metrics.task_success_rate,
                "energy_efficiency": agent.performance_metrics.energy_efficiency,
                "adaptation_speed": agent.performance_metrics.adaptation_speed,
                "error_rate": agent.performance_metrics.error_rate,
                "collaboration_score": agent.performance_metrics.collaboration_score,
                "discovery_rate": agent.performance_metrics.discovery_rate,
                "security_score": agent.performance_metrics.security_score,
                "innovation_score": agent.performance_metrics.innovation_score,
                "optimization_score": agent.performance_metrics.optimization_score,
            }

            self.genome_pool.evaluate_fitness(
                agent.genome.genome_id, performance_metrics
            )

    async def _handle_reproductions(self):
        """Handle agent reproductions based on fitness and readiness."""
        current_time = time.time()

        # Check reproduction cooldown
        if current_time - self.last_reproduction_time < self.reproduction_cooldown:
            return

        # Find agents ready for reproduction
        reproduction_candidates = [
            agent
            for agent in self.active_agents.values()
            if agent.should_reproduce() and agent.status == AgentStatus.REPRODUCING
        ]

        if len(reproduction_candidates) < 2:
            return

        # Don't exceed population limit
        if len(self.active_agents) >= self.max_population:
            return

        # Select parents
        parents = random.sample(reproduction_candidates, 2)
        parent1, parent2 = parents

        # Create offspring through genetic crossover
        offspring_genome = parent1.genome.crossover(parent2.genome)

        # Apply mutation
        if random.random() < 0.2:  # 20% mutation chance
            offspring_genome = offspring_genome.mutate()

        # Create new agent
        offspring_agent = BiomimeticAgent(
            offspring_genome, ai_pipeline=self.ai_pipeline
        )

        # Birth the offspring
        await self._birth_agent(offspring_agent)

        # Record reproduction event
        await self._record_lifecycle_event(
            parent1.agent_id,
            LifecycleEvent.REPRODUCTION,
            {
                "parent1_id": parent1.agent_id,
                "parent2_id": parent2.agent_id,
                "offspring_id": offspring_agent.agent_id,
                "parent1_fitness": parent1.calculate_fitness(),
                "parent2_fitness": parent2.calculate_fitness(),
            },
            parent1.calculate_fitness(),
            parent1.age_in_cycles,
        )

        # Update reproduction time
        self.last_reproduction_time = current_time
        self.population_stats["total_reproductions"] += 1

        # Reset parent status
        parent1.status = AgentStatus.ACTIVE
        parent2.status = AgentStatus.ACTIVE

        logger.info(
            f"Reproduction: {parent1.agent_id} + {parent2.agent_id} -> {offspring_agent.agent_id}"
        )

    async def _handle_terminations(self):
        """Handle agent terminations based on fitness and age."""
        termination_candidates = [
            agent for agent in self.active_agents.values() if agent.should_terminate()
        ]

        for agent in termination_candidates:
            # Don't terminate if it would go below minimum population
            if len(self.active_agents) <= self.min_population:
                break

            await self._terminate_agent(agent, "natural_death")

    async def _maintain_population(self):
        """Maintain population within desired bounds."""
        current_population = len(self.active_agents)

        # Add agents if below minimum
        if current_population < self.min_population:
            needed = self.min_population - current_population

            for _ in range(needed):
                # Create new agent from best genomes
                best_genomes = self.genome_pool.get_best_genomes(5)
                if best_genomes:
                    selected_genome = random.choice(best_genomes)
                    mutated_genome = selected_genome.mutate()
                    agent = BiomimeticAgent(
                        mutated_genome, ai_pipeline=self.ai_pipeline
                    )
                    await self._birth_agent(agent)

        # Remove excess agents if above maximum
        elif current_population > self.max_population:
            excess = current_population - self.max_population

            # Sort agents by fitness (lowest first)
            sorted_agents = sorted(
                self.active_agents.values(), key=lambda a: a.calculate_fitness()
            )

            # Terminate lowest fitness agents
            for agent in sorted_agents[:excess]:
                await self._terminate_agent(agent, "population_control")

    async def _evolution_cycle(self):
        """Perform evolutionary cycle on the genome pool."""
        if len(self.genome_pool.genomes) < 10:
            return

        # Evolve the genome pool
        evolution_stats = self.genome_pool.evolve_generation(
            survival_rate=0.4, mutation_rate=0.15
        )

        self.population_stats["generation_count"] = evolution_stats["generation"]

        logger.info(
            f"Evolution cycle {evolution_stats['generation']}: "
            f"Max fitness: {evolution_stats['max_fitness']:.3f}, "
            f"Avg fitness: {evolution_stats['avg_fitness']:.3f}"
        )

        # Trigger evolution event callbacks
        await self._trigger_event_callbacks(LifecycleEvent.BIRTH, evolution_stats)

    async def _birth_agent(self, agent: BiomimeticAgent):
        """Birth a new agent and add it to the active population."""
        # Add to active agents
        self.active_agents[agent.agent_id] = agent

        # Activate the agent
        await agent.activate()

        # Record birth event
        await self._record_lifecycle_event(
            agent.agent_id,
            LifecycleEvent.BIRTH,
            {
                "archetype": agent.archetype.value,
                "genome_id": agent.genome.genome_id,
                "generation": agent.genome.generation,
            },
            0.0,  # No fitness at birth
            0,  # Age 0 at birth
        )

        self.population_stats["total_births"] += 1

        # Trigger birth callbacks
        await self._trigger_event_callbacks(
            LifecycleEvent.BIRTH, {"agent": agent, "agent_id": agent.agent_id}
        )

        logger.info(f"Agent born: {agent.agent_id} ({agent.archetype.value})")

    async def _terminate_agent(self, agent: BiomimeticAgent, reason: str):
        """Terminate an agent and remove it from the active population."""
        agent_id = agent.agent_id
        fitness = agent.calculate_fitness()
        age = agent.age_in_cycles

        # Update agent status
        agent.status = AgentStatus.TERMINATED

        # Record death event
        await self._record_lifecycle_event(
            agent_id,
            LifecycleEvent.DEATH,
            {
                "reason": reason,
                "archetype": agent.archetype.value,
                "final_fitness": fitness,
                "tasks_completed": agent.performance_metrics.total_tasks_completed,
                "lifespan_cycles": age,
            },
            fitness,
            age,
        )

        # Remove from active agents
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]

        self.population_stats["total_deaths"] += 1

        # Update average lifespan
        total_deaths = self.population_stats["total_deaths"]
        current_avg = self.population_stats["average_lifespan"]
        self.population_stats["average_lifespan"] = (
            current_avg * (total_deaths - 1) + age
        ) / total_deaths

        # Trigger death callbacks
        await self._trigger_event_callbacks(
            LifecycleEvent.DEATH,
            {"agent_id": agent_id, "reason": reason, "fitness": fitness, "age": age},
        )

        logger.info(
            f"Agent terminated: {agent_id} (reason: {reason}, "
            f"fitness: {fitness:.3f}, age: {age})"
        )

    async def _record_lifecycle_event(
        self,
        agent_id: str,
        event_type: LifecycleEvent,
        details: Dict[str, Any],
        fitness: float,
        age: int,
    ):
        """Record a lifecycle event in the history."""
        record = LifecycleRecord(
            agent_id=agent_id,
            event_type=event_type,
            timestamp=datetime.now(),
            details=details,
            fitness_score=fitness,
            age_in_cycles=age,
        )

        self.lifecycle_history.append(record)

        # Limit history size
        if len(self.lifecycle_history) > 10000:
            self.lifecycle_history = self.lifecycle_history[-10000:]

    def _update_population_stats(self):
        """Update population statistics."""
        if not self.active_agents:
            return

        # Calculate average fitness
        fitness_scores = [
            agent.calculate_fitness() for agent in self.active_agents.values()
        ]
        self.population_stats["average_fitness"] = sum(fitness_scores) / len(
            fitness_scores
        )

    async def _trigger_event_callbacks(
        self, event_type: LifecycleEvent, data: Dict[str, Any]
    ):
        """Trigger registered callbacks for lifecycle events."""
        for callback in self.event_callbacks[event_type]:
            try:
                await callback(event_type, data)
            except Exception as e:
                logger.error(f"Error in event callback for {event_type.value}: {e}")

    def register_event_callback(self, event_type: LifecycleEvent, callback: Callable):
        """Register a callback for lifecycle events."""
        self.event_callbacks[event_type].append(callback)
        logger.info(f"Registered callback for {event_type.value} events")

    def get_agent(self, agent_id: str) -> Optional[BiomimeticAgent]:
        """Get an agent by ID."""
        return self.active_agents.get(agent_id)

    def get_agents_by_archetype(self, archetype: Archetype) -> List[BiomimeticAgent]:
        """Get all agents of a specific archetype."""
        return [
            agent
            for agent in self.active_agents.values()
            if agent.archetype == archetype
        ]

    def get_population_summary(self) -> Dict[str, Any]:
        """Get comprehensive population summary."""
        if not self.active_agents:
            return {
                "total_agents": 0,
                "archetype_distribution": {},
                "status_distribution": {},
                "fitness_distribution": {},
                "age_distribution": {},
                "population_stats": self.population_stats,
            }

        agents = list(self.active_agents.values())

        # Archetype distribution
        archetype_dist = {}
        for archetype in Archetype:
            archetype_dist[archetype.value] = len(
                [a for a in agents if a.archetype == archetype]
            )

        # Status distribution
        status_dist = {}
        for status in AgentStatus:
            status_dist[status.value] = len([a for a in agents if a.status == status])

        # Fitness distribution
        fitness_scores = [a.calculate_fitness() for a in agents]
        fitness_dist = {
            "min": min(fitness_scores),
            "max": max(fitness_scores),
            "avg": sum(fitness_scores) / len(fitness_scores),
            "std": (
                sum(
                    (f - sum(fitness_scores) / len(fitness_scores)) ** 2
                    for f in fitness_scores
                )
                / len(fitness_scores)
            )
            ** 0.5,
        }

        # Age distribution
        ages = [a.age_in_cycles for a in agents]
        age_dist = {"min": min(ages), "max": max(ages), "avg": sum(ages) / len(ages)}

        return {
            "total_agents": len(agents),
            "archetype_distribution": archetype_dist,
            "status_distribution": status_dist,
            "fitness_distribution": fitness_dist,
            "age_distribution": age_dist,
            "population_stats": self.population_stats,
            "genome_pool_stats": {
                "total_genomes": len(self.genome_pool.genomes),
                "generation": self.genome_pool.generation_count,
            },
        }

    def get_lifecycle_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent lifecycle history."""
        recent_history = self.lifecycle_history[-limit:]

        return [
            {
                "agent_id": record.agent_id,
                "event_type": record.event_type.value,
                "timestamp": record.timestamp.isoformat(),
                "details": record.details,
                "fitness_score": record.fitness_score,
                "age_in_cycles": record.age_in_cycles,
            }
            for record in recent_history
        ]

    async def force_reproduction(
        self, parent1_id: str, parent2_id: str
    ) -> Optional[str]:
        """Force reproduction between two specific agents."""
        parent1 = self.active_agents.get(parent1_id)
        parent2 = self.active_agents.get(parent2_id)

        if not parent1 or not parent2:
            logger.error(f"Cannot force reproduction: agents not found")
            return None

        if len(self.active_agents) >= self.max_population:
            logger.error(f"Cannot force reproduction: population at maximum")
            return None

        # Create offspring
        offspring_genome = parent1.genome.crossover(parent2.genome)
        offspring_agent = BiomimeticAgent(
            offspring_genome, ai_pipeline=self.ai_pipeline
        )

        # Birth the offspring
        await self._birth_agent(offspring_agent)

        logger.info(
            f"Forced reproduction: {parent1_id} + {parent2_id} -> {offspring_agent.agent_id}"
        )
        return offspring_agent.agent_id

    async def force_termination(self, agent_id: str) -> bool:
        """Force termination of a specific agent."""
        agent = self.active_agents.get(agent_id)
        if not agent:
            logger.error(f"Cannot force termination: agent {agent_id} not found")
            return False

        if len(self.active_agents) <= self.min_population:
            logger.error(f"Cannot force termination: population at minimum")
            return False

        await self._terminate_agent(agent, "forced_termination")
        return True

    def save_state(self, filepath: str):
        """Save Thanatos controller state to file."""
        state_data = {
            "population_stats": self.population_stats,
            "max_population": self.max_population,
            "min_population": self.min_population,
            "evolution_enabled": self.evolution_enabled,
            "active_agents": {
                agent_id: agent.to_dict()
                for agent_id, agent in self.active_agents.items()
            },
            "lifecycle_history": self.get_lifecycle_history(1000),
        }

        with open(filepath, "w") as f:
            json.dump(state_data, f, indent=2)

        # Save genome pool separately
        genome_pool_path = filepath.replace(".json", "_genomes.json")
        self.genome_pool.save_population(genome_pool_path)

        logger.info(f"Saved Thanatos state to {filepath}")

    def load_state(self, filepath: str):
        """Load Thanatos controller state from file."""
        with open(filepath, "r") as f:
            state_data = json.load(f)

        self.population_stats = state_data["population_stats"]
        self.max_population = state_data["max_population"]
        self.min_population = state_data["min_population"]
        self.evolution_enabled = state_data["evolution_enabled"]

        # Restore agents
        self.active_agents = {}
        for agent_id, agent_data in state_data["active_agents"].items():
            agent = BiomimeticAgent.from_dict(agent_data, self.ai_pipeline)
            self.active_agents[agent_id] = agent

        # Load genome pool
        genome_pool_path = filepath.replace(".json", "_genomes.json")
        self.genome_pool.load_population(genome_pool_path)

        logger.info(
            f"Loaded Thanatos state from {filepath}: "
            f"{len(self.active_agents)} agents"
        )
