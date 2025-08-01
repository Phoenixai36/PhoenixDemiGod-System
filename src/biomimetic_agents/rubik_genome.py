"""
RUBIK Biomimetic Agent System - Genetic Architecture

This module implements the revolutionary 20-base logarithmic matrix genome system
for self-evolving AI agents, integrating with the 2025 advanced model ecosystem.
"""

import hashlib
import json
import logging
import math
import random
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class GeneticBase(Enum):
    """20-base genetic encoding system for agent characteristics."""

    # Cognitive Bases (0-4)
    REASONING = 0  # Logical analysis and problem-solving
    CREATIVITY = 1  # Novel solution generation
    MEMORY = 2  # Information retention and recall
    LEARNING = 3  # Adaptation and skill acquisition
    INTUITION = 4  # Pattern recognition and insight

    # Behavioral Bases (5-9)
    AGGRESSION = 5  # Assertiveness and competitive drive
    CAUTION = 6  # Risk assessment and safety
    CURIOSITY = 7  # Exploration and discovery
    PERSISTENCE = 8  # Task completion and resilience
    COOPERATION = 9  # Collaboration and teamwork

    # Emotional Bases (10-14)
    EMPATHY = 10  # Understanding others' states
    CONFIDENCE = 11  # Self-assurance and certainty
    ANXIETY = 12  # Stress response and vigilance
    OPTIMISM = 13  # Positive outlook and hope
    FOCUS = 14  # Attention and concentration

    # Operational Bases (15-19)
    EFFICIENCY = 15  # Resource optimization
    ADAPTABILITY = 16  # Environmental flexibility
    PRECISION = 17  # Accuracy and attention to detail
    SPEED = 18  # Processing and response velocity
    ROBUSTNESS = 19  # Error tolerance and stability


class Archetype(Enum):
    """Four primary agent archetypes with specialized roles."""

    EXPLORER = "explorer"  # Discovery and data gathering
    GUARDIAN = "guardian"  # Security and system integrity
    CREATOR = "creator"  # Building and solution generation
    DESTROYER = "destroyer"  # Elimination and optimization


class MoodState(Enum):
    """Emotional states affecting agent behavior."""

    CALM = "calm"
    EXCITED = "excited"
    FOCUSED = "focused"
    ANXIOUS = "anxious"
    CONFIDENT = "confident"
    CURIOUS = "curious"
    AGGRESSIVE = "aggressive"
    CONTEMPLATIVE = "contemplative"


@dataclass
class GeneExpression:
    """Individual gene expression with logarithmic scaling."""

    base: GeneticBase
    raw_value: float  # 0.0 to 1.0
    expression_level: float  # Logarithmically scaled
    mutation_rate: float
    dominance: float  # Interaction strength with other genes

    def __post_init__(self):
        """Calculate logarithmic expression level."""
        # Logarithmic scaling: small changes have exponential effects
        self.expression_level = math.log10(1 + 9 * self.raw_value)

    def mutate(self, mutation_strength: float = 0.1) -> "GeneExpression":
        """Create a mutated version of this gene."""
        mutation_delta = random.gauss(0, mutation_strength * self.mutation_rate)
        new_raw_value = np.clip(self.raw_value + mutation_delta, 0.0, 1.0)

        return GeneExpression(
            base=self.base,
            raw_value=new_raw_value,
            expression_level=0.0,  # Will be calculated in __post_init__
            mutation_rate=self.mutation_rate * random.uniform(0.95, 1.05),
            dominance=self.dominance * random.uniform(0.98, 1.02),
        )


class RUBIKGenome:
    """
    20-base logarithmic matrix genome for biomimetic agents.

    This class implements the core genetic architecture that defines
    agent behavior, capabilities, and evolutionary potential.
    """

    def __init__(self, genes: Optional[List[GeneExpression]] = None):
        self.genes: Dict[GeneticBase, GeneExpression] = {}
        self.interaction_matrix = np.zeros((20, 20))  # Gene interaction matrix
        self.genome_id = self._generate_genome_id()
        self.generation = 0
        self.fitness_score = 0.0
        self.parent_genomes: List[str] = []

        if genes:
            for gene in genes:
                self.genes[gene.base] = gene
        else:
            self._initialize_random_genome()

        self._calculate_interaction_matrix()

    def _generate_genome_id(self) -> str:
        """Generate unique genome identifier."""
        timestamp = str(datetime.now().timestamp())
        random_data = str(random.random())
        return hashlib.sha256((timestamp + random_data).encode()).hexdigest()[:16]

    def _initialize_random_genome(self):
        """Initialize genome with random gene expressions."""
        for base in GeneticBase:
            self.genes[base] = GeneExpression(
                base=base,
                raw_value=random.random(),
                expression_level=0.0,  # Calculated in __post_init__
                mutation_rate=random.uniform(0.01, 0.05),
                dominance=random.uniform(0.5, 1.5),
            )

    def _calculate_interaction_matrix(self):
        """Calculate gene interaction matrix using logarithmic relationships."""
        for i, base_i in enumerate(GeneticBase):
            for j, base_j in enumerate(GeneticBase):
                if i == j:
                    self.interaction_matrix[i][j] = 1.0  # Self-interaction
                else:
                    # Calculate interaction strength based on gene categories
                    interaction = self._calculate_gene_interaction(base_i, base_j)
                    self.interaction_matrix[i][j] = interaction

    def _calculate_gene_interaction(
        self, base_i: GeneticBase, base_j: GeneticBase
    ) -> float:
        """Calculate interaction strength between two genetic bases."""
        # Define interaction rules based on biological and psychological principles
        synergistic_pairs = {
            (GeneticBase.REASONING, GeneticBase.FOCUS): 1.5,
            (GeneticBase.CREATIVITY, GeneticBase.CURIOSITY): 1.4,
            (GeneticBase.MEMORY, GeneticBase.LEARNING): 1.3,
            (GeneticBase.PERSISTENCE, GeneticBase.CONFIDENCE): 1.2,
            (GeneticBase.EMPATHY, GeneticBase.COOPERATION): 1.4,
            (GeneticBase.CAUTION, GeneticBase.ANXIETY): 1.1,
            (GeneticBase.EFFICIENCY, GeneticBase.PRECISION): 1.3,
            (GeneticBase.ADAPTABILITY, GeneticBase.LEARNING): 1.2,
        }

        antagonistic_pairs = {
            (GeneticBase.AGGRESSION, GeneticBase.CAUTION): 0.7,
            (GeneticBase.SPEED, GeneticBase.PRECISION): 0.8,
            (GeneticBase.CONFIDENCE, GeneticBase.ANXIETY): 0.6,
            (GeneticBase.FOCUS, GeneticBase.CURIOSITY): 0.9,
        }

        # Check for defined interactions
        pair = (base_i, base_j)
        reverse_pair = (base_j, base_i)

        if pair in synergistic_pairs:
            return synergistic_pairs[pair]
        elif reverse_pair in synergistic_pairs:
            return synergistic_pairs[reverse_pair]
        elif pair in antagonistic_pairs:
            return antagonistic_pairs[pair]
        elif reverse_pair in antagonistic_pairs:
            return antagonistic_pairs[reverse_pair]
        else:
            # Default neutral interaction with slight randomness
            return random.uniform(0.95, 1.05)

    def get_effective_expression(self, base: GeneticBase) -> float:
        """
        Calculate effective gene expression considering interactions.

        This is where the logarithmic matrix magic happens - small genetic
        changes can have exponential effects on behavior.
        """
        if base not in self.genes:
            return 0.0

        base_expression = self.genes[base].expression_level
        base_index = base.value

        # Calculate interaction effects
        interaction_effect = 0.0
        for other_base, other_gene in self.genes.items():
            if other_base != base:
                other_index = other_base.value
                interaction_strength = self.interaction_matrix[base_index][other_index]
                interaction_effect += (
                    other_gene.expression_level
                    * interaction_strength
                    * other_gene.dominance
                    * 0.1
                )

        # Apply logarithmic scaling to interaction effects
        total_expression = base_expression + math.log10(1 + abs(interaction_effect))

        # Normalize to 0-2 range (allowing for super-expression)
        return np.clip(total_expression, 0.0, 2.0)

    def determine_archetype(self) -> Archetype:
        """Determine primary archetype based on gene expressions."""
        archetype_scores = {
            Archetype.EXPLORER: (
                self.get_effective_expression(GeneticBase.CURIOSITY) * 1.5
                + self.get_effective_expression(GeneticBase.ADAPTABILITY) * 1.2
                + self.get_effective_expression(GeneticBase.LEARNING) * 1.1
            ),
            Archetype.GUARDIAN: (
                self.get_effective_expression(GeneticBase.CAUTION) * 1.5
                + self.get_effective_expression(GeneticBase.ROBUSTNESS) * 1.3
                + self.get_effective_expression(GeneticBase.PERSISTENCE) * 1.1
            ),
            Archetype.CREATOR: (
                self.get_effective_expression(GeneticBase.CREATIVITY) * 1.5
                + self.get_effective_expression(GeneticBase.REASONING) * 1.2
                + self.get_effective_expression(GeneticBase.PRECISION) * 1.1
            ),
            Archetype.DESTROYER: (
                self.get_effective_expression(GeneticBase.AGGRESSION) * 1.4
                + self.get_effective_expression(GeneticBase.EFFICIENCY) * 1.3
                + self.get_effective_expression(GeneticBase.FOCUS) * 1.2
            ),
        }

        return max(archetype_scores.items(), key=lambda x: x[1])[0]

    def calculate_mood_state(
        self, environmental_factors: Dict[str, float]
    ) -> MoodState:
        """Calculate current mood state based on genes and environment."""
        # Base mood tendencies from genes
        mood_influences = {
            MoodState.CALM: (
                self.get_effective_expression(GeneticBase.CONFIDENCE)
                + self.get_effective_expression(GeneticBase.ROBUSTNESS)
                - self.get_effective_expression(GeneticBase.ANXIETY)
            ),
            MoodState.EXCITED: (
                self.get_effective_expression(GeneticBase.OPTIMISM)
                + self.get_effective_expression(GeneticBase.CURIOSITY)
                + environmental_factors.get("novelty", 0.0)
            ),
            MoodState.FOCUSED: (
                self.get_effective_expression(GeneticBase.FOCUS)
                + self.get_effective_expression(GeneticBase.PERSISTENCE)
                + environmental_factors.get("task_complexity", 0.0)
            ),
            MoodState.ANXIOUS: (
                self.get_effective_expression(GeneticBase.ANXIETY)
                + self.get_effective_expression(GeneticBase.CAUTION)
                + environmental_factors.get("threat_level", 0.0)
            ),
            MoodState.CONFIDENT: (
                self.get_effective_expression(GeneticBase.CONFIDENCE)
                + self.get_effective_expression(GeneticBase.AGGRESSION)
                + environmental_factors.get("success_rate", 0.0)
            ),
            MoodState.CURIOUS: (
                self.get_effective_expression(GeneticBase.CURIOSITY)
                + self.get_effective_expression(GeneticBase.LEARNING)
                + environmental_factors.get("information_availability", 0.0)
            ),
            MoodState.AGGRESSIVE: (
                self.get_effective_expression(GeneticBase.AGGRESSION)
                + environmental_factors.get("competition", 0.0)
                + environmental_factors.get("resource_scarcity", 0.0)
            ),
            MoodState.CONTEMPLATIVE: (
                self.get_effective_expression(GeneticBase.REASONING)
                + self.get_effective_expression(GeneticBase.MEMORY)
                + environmental_factors.get("complexity", 0.0)
            ),
        }

        return max(mood_influences.items(), key=lambda x: x[1])[0]

    def crossover(self, other_genome: "RUBIKGenome") -> "RUBIKGenome":
        """
        Create offspring genome through genetic crossover.

        Implements sophisticated crossover that preserves beneficial
        gene combinations while introducing variation.
        """
        offspring_genes = []

        for base in GeneticBase:
            parent1_gene = self.genes[base]
            parent2_gene = other_genome.genes[base]

            # Weighted selection based on fitness
            if self.fitness_score > other_genome.fitness_score:
                selection_probability = 0.6  # Favor fitter parent
            elif other_genome.fitness_score > self.fitness_score:
                selection_probability = 0.4
            else:
                selection_probability = 0.5  # Equal fitness

            if random.random() < selection_probability:
                selected_gene = parent1_gene
            else:
                selected_gene = parent2_gene

            # Create new gene with potential crossover
            if random.random() < 0.3:  # 30% chance of crossover
                # Blend genes
                blended_value = (parent1_gene.raw_value + parent2_gene.raw_value) / 2
                blended_mutation_rate = (
                    parent1_gene.mutation_rate + parent2_gene.mutation_rate
                ) / 2
                blended_dominance = (
                    parent1_gene.dominance + parent2_gene.dominance
                ) / 2

                offspring_gene = GeneExpression(
                    base=base,
                    raw_value=blended_value,
                    expression_level=0.0,
                    mutation_rate=blended_mutation_rate,
                    dominance=blended_dominance,
                )
            else:
                # Direct inheritance
                offspring_gene = GeneExpression(
                    base=selected_gene.base,
                    raw_value=selected_gene.raw_value,
                    expression_level=0.0,
                    mutation_rate=selected_gene.mutation_rate,
                    dominance=selected_gene.dominance,
                )

            offspring_genes.append(offspring_gene)

        # Create offspring genome
        offspring = RUBIKGenome(offspring_genes)
        offspring.generation = max(self.generation, other_genome.generation) + 1
        offspring.parent_genomes = [self.genome_id, other_genome.genome_id]

        return offspring

    def mutate(self, mutation_strength: float = 0.1) -> "RUBIKGenome":
        """Create a mutated version of this genome."""
        mutated_genes = []

        for base, gene in self.genes.items():
            if random.random() < gene.mutation_rate:
                mutated_genes.append(gene.mutate(mutation_strength))
            else:
                mutated_genes.append(gene)

        mutated_genome = RUBIKGenome(mutated_genes)
        mutated_genome.generation = self.generation
        mutated_genome.parent_genomes = [self.genome_id]

        return mutated_genome

    def get_model_preferences(self) -> Dict[str, float]:
        """
        Determine AI model preferences based on genetic makeup.

        This integrates with the 2025 advanced model ecosystem,
        selecting optimal models based on agent characteristics.
        """
        preferences = {}

        # Reasoning-heavy tasks
        reasoning_affinity = (
            self.get_effective_expression(GeneticBase.REASONING) * 0.4
            + self.get_effective_expression(GeneticBase.FOCUS) * 0.3
            + self.get_effective_expression(GeneticBase.PRECISION) * 0.3
        )

        if reasoning_affinity > 1.5:
            preferences["primary_reasoning"] = "minimax-m1-80k"  # Ultra-long context
        elif reasoning_affinity > 1.0:
            preferences["primary_reasoning"] = "glm-4.5"  # Unified reasoning
        else:
            preferences["primary_reasoning"] = "kimi-k2-instruct"  # Efficient agentic

        # Coding tasks
        coding_affinity = (
            self.get_effective_expression(GeneticBase.CREATIVITY) * 0.3
            + self.get_effective_expression(GeneticBase.PRECISION) * 0.4
            + self.get_effective_expression(GeneticBase.PERSISTENCE) * 0.3
        )

        if coding_affinity > 1.5:
            preferences["primary_coding"] = "qwen3-coder-480b-a35b"  # Massive context
        else:
            preferences["primary_coding"] = "qwen2.5-coder-32b"  # Efficient local

        # Multimodal preferences
        creativity_level = self.get_effective_expression(GeneticBase.CREATIVITY)
        if creativity_level > 1.3:
            preferences["multimodal"] = "flux-kontext-max"  # Advanced contextual
        else:
            preferences["multimodal"] = "flux-dev"  # Standard generation

        # Energy efficiency preferences
        efficiency_focus = self.get_effective_expression(GeneticBase.EFFICIENCY)
        if efficiency_focus > 1.2:
            preferences["local_backbone"] = "mamba-codestral-7b"  # SSM efficiency
        else:
            preferences["local_backbone"] = "llama-3.3-8b"  # Balanced performance

        return preferences

    def to_dict(self) -> Dict[str, Any]:
        """Convert genome to dictionary for serialization."""
        return {
            "genome_id": self.genome_id,
            "generation": self.generation,
            "fitness_score": self.fitness_score,
            "parent_genomes": self.parent_genomes,
            "genes": {
                base.name: {
                    "raw_value": gene.raw_value,
                    "expression_level": gene.expression_level,
                    "mutation_rate": gene.mutation_rate,
                    "dominance": gene.dominance,
                }
                for base, gene in self.genes.items()
            },
            "interaction_matrix": self.interaction_matrix.tolist(),
            "archetype": self.determine_archetype().value,
            "model_preferences": self.get_model_preferences(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RUBIKGenome":
        """Create genome from dictionary."""
        genes = []
        for base_name, gene_data in data["genes"].items():
            base = GeneticBase[base_name]
            gene = GeneExpression(
                base=base,
                raw_value=gene_data["raw_value"],
                expression_level=gene_data["expression_level"],
                mutation_rate=gene_data["mutation_rate"],
                dominance=gene_data["dominance"],
            )
            genes.append(gene)

        genome = cls(genes)
        genome.genome_id = data["genome_id"]
        genome.generation = data["generation"]
        genome.fitness_score = data["fitness_score"]
        genome.parent_genomes = data["parent_genomes"]
        genome.interaction_matrix = np.array(data["interaction_matrix"])

        return genome

    def __str__(self) -> str:
        """String representation of genome."""
        archetype = self.determine_archetype()
        top_genes = sorted(
            [(base, self.get_effective_expression(base)) for base in GeneticBase],
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        return (
            f"RUBIKGenome({self.genome_id[:8]}): "
            f"Gen{self.generation} {archetype.value.title()} "
            f"Fitness={self.fitness_score:.3f} "
            f"Top: {', '.join([f'{base.name}={expr:.2f}' for base, expr in top_genes])}"
        )


class GenomePool:
    """
    Manages a population of RUBIK genomes for evolutionary processes.

    This class handles the population-level genetics including selection,
    breeding, and evolutionary pressure management.
    """

    def __init__(self, initial_population_size: int = 100):
        self.genomes: Dict[str, RUBIKGenome] = {}
        self.population_size = initial_population_size
        self.generation_count = 0
        self.fitness_history: List[Dict[str, float]] = []

        # Initialize random population
        self._initialize_population()

    def _initialize_population(self):
        """Initialize population with diverse random genomes."""
        logger.info(f"Initializing genome pool with {self.population_size} genomes")

        for i in range(self.population_size):
            genome = RUBIKGenome()
            self.genomes[genome.genome_id] = genome

        logger.info(f"Created {len(self.genomes)} initial genomes")

    def evaluate_fitness(
        self, genome_id: str, performance_metrics: Dict[str, float]
    ) -> float:
        """
        Evaluate and update genome fitness based on performance metrics.

        Args:
            genome_id: Genome identifier
            performance_metrics: Performance data from agent execution

        Returns:
            Updated fitness score
        """
        if genome_id not in self.genomes:
            logger.warning(f"Genome {genome_id} not found in pool")
            return 0.0

        genome = self.genomes[genome_id]

        # Calculate fitness based on multiple factors
        task_success_rate = performance_metrics.get("task_success_rate", 0.0)
        energy_efficiency = performance_metrics.get("energy_efficiency", 0.0)
        adaptation_speed = performance_metrics.get("adaptation_speed", 0.0)
        error_rate = performance_metrics.get("error_rate", 1.0)
        collaboration_score = performance_metrics.get("collaboration_score", 0.0)

        # Weighted fitness calculation
        fitness = (
            task_success_rate * 0.3
            + energy_efficiency * 0.2
            + adaptation_speed * 0.2
            + (1.0 - error_rate) * 0.15
            + collaboration_score * 0.15
        )

        # Apply archetype-specific bonuses
        archetype = genome.determine_archetype()
        if archetype == Archetype.EXPLORER:
            fitness += performance_metrics.get("discovery_rate", 0.0) * 0.1
        elif archetype == Archetype.GUARDIAN:
            fitness += performance_metrics.get("security_score", 0.0) * 0.1
        elif archetype == Archetype.CREATOR:
            fitness += performance_metrics.get("innovation_score", 0.0) * 0.1
        elif archetype == Archetype.DESTROYER:
            fitness += performance_metrics.get("optimization_score", 0.0) * 0.1

        # Update genome fitness
        genome.fitness_score = fitness

        logger.debug(f"Updated fitness for {genome_id[:8]}: {fitness:.3f}")
        return fitness

    def select_parents(
        self, selection_pressure: float = 0.7
    ) -> Tuple[RUBIKGenome, RUBIKGenome]:
        """
        Select two parent genomes for breeding using tournament selection.

        Args:
            selection_pressure: Higher values favor fitter individuals

        Returns:
            Tuple of two parent genomes
        """
        genomes_list = list(self.genomes.values())

        # Tournament selection
        tournament_size = max(3, int(len(genomes_list) * 0.1))

        def tournament_select():
            tournament = random.sample(genomes_list, tournament_size)
            tournament.sort(key=lambda g: g.fitness_score, reverse=True)

            # Probabilistic selection favoring fitter individuals
            for i, genome in enumerate(tournament):
                selection_prob = (1 - selection_pressure) ** i
                if random.random() < selection_prob:
                    return genome

            return tournament[-1]  # Fallback to least fit

        parent1 = tournament_select()
        parent2 = tournament_select()

        # Ensure different parents
        while parent2.genome_id == parent1.genome_id and len(genomes_list) > 1:
            parent2 = tournament_select()

        return parent1, parent2

    def breed_offspring(
        self, parent1: RUBIKGenome, parent2: RUBIKGenome, mutation_rate: float = 0.1
    ) -> RUBIKGenome:
        """Create offspring through crossover and mutation."""
        offspring = parent1.crossover(parent2)

        # Apply mutation
        if random.random() < mutation_rate:
            offspring = offspring.mutate()

        return offspring

    def evolve_generation(
        self, survival_rate: float = 0.3, mutation_rate: float = 0.1
    ) -> Dict[str, Any]:
        """
        Evolve the population to the next generation.

        Args:
            survival_rate: Fraction of population that survives
            mutation_rate: Probability of mutation in offspring

        Returns:
            Evolution statistics
        """
        logger.info(f"Evolving generation {self.generation_count}")

        # Sort genomes by fitness
        sorted_genomes = sorted(
            self.genomes.values(), key=lambda g: g.fitness_score, reverse=True
        )

        # Calculate statistics
        fitness_scores = [g.fitness_score for g in sorted_genomes]
        stats = {
            "generation": self.generation_count,
            "population_size": len(sorted_genomes),
            "max_fitness": max(fitness_scores) if fitness_scores else 0.0,
            "avg_fitness": sum(fitness_scores) / len(fitness_scores)
            if fitness_scores
            else 0.0,
            "min_fitness": min(fitness_scores) if fitness_scores else 0.0,
            "archetype_distribution": self._calculate_archetype_distribution(),
        }

        # Select survivors
        num_survivors = int(len(sorted_genomes) * survival_rate)
        survivors = sorted_genomes[:num_survivors]

        # Create new population
        new_genomes = {}

        # Add survivors
        for genome in survivors:
            new_genomes[genome.genome_id] = genome

        # Breed offspring to fill population
        while len(new_genomes) < self.population_size:
            parent1, parent2 = self.select_parents()
            offspring = self.breed_offspring(parent1, parent2, mutation_rate)
            new_genomes[offspring.genome_id] = offspring

        # Update population
        self.genomes = new_genomes
        self.generation_count += 1
        self.fitness_history.append(stats)

        logger.info(
            f"Generation {self.generation_count} evolved: "
            f"Max fitness: {stats['max_fitness']:.3f}, "
            f"Avg fitness: {stats['avg_fitness']:.3f}"
        )

        return stats

    def _calculate_archetype_distribution(self) -> Dict[str, int]:
        """Calculate distribution of archetypes in population."""
        distribution = {archetype.value: 0 for archetype in Archetype}

        for genome in self.genomes.values():
            archetype = genome.determine_archetype()
            distribution[archetype.value] += 1

        return distribution

    def get_best_genomes(self, count: int = 10) -> List[RUBIKGenome]:
        """Get the top performing genomes."""
        sorted_genomes = sorted(
            self.genomes.values(), key=lambda g: g.fitness_score, reverse=True
        )
        return sorted_genomes[:count]

    def get_diverse_genomes(self, count: int = 4) -> List[RUBIKGenome]:
        """Get a diverse set of genomes representing different archetypes."""
        archetype_genomes = {}

        for genome in self.genomes.values():
            archetype = genome.determine_archetype()
            if (
                archetype not in archetype_genomes
                or genome.fitness_score > archetype_genomes[archetype].fitness_score
            ):
                archetype_genomes[archetype] = genome

        # Return up to count genomes, prioritizing diversity
        diverse_genomes = list(archetype_genomes.values())

        if len(diverse_genomes) < count:
            # Fill remaining slots with high-fitness genomes
            remaining = count - len(diverse_genomes)
            best_genomes = self.get_best_genomes(remaining * 2)

            for genome in best_genomes:
                if genome not in diverse_genomes and len(diverse_genomes) < count:
                    diverse_genomes.append(genome)

        return diverse_genomes[:count]

    def save_population(self, filepath: str):
        """Save population to file."""
        data = {
            "generation_count": self.generation_count,
            "population_size": self.population_size,
            "fitness_history": self.fitness_history,
            "genomes": {
                genome_id: genome.to_dict()
                for genome_id, genome in self.genomes.items()
            },
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved population to {filepath}")

    def load_population(self, filepath: str):
        """Load population from file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        self.generation_count = data["generation_count"]
        self.population_size = data["population_size"]
        self.fitness_history = data["fitness_history"]

        self.genomes = {}
        for genome_id, genome_data in data["genomes"].items():
            genome = RUBIKGenome.from_dict(genome_data)
            self.genomes[genome_id] = genome

        logger.info(
            f"Loaded population from {filepath}: "
            f"{len(self.genomes)} genomes, generation {self.generation_count}"
        )
