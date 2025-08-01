"""
Gene Py evolutionary system for PHOENIXxHYDRA.

Implements animal-inspired genetic traits, Rubik personality matrices,
and evolutionary algorithms for digital cell evolution.
"""

import random
import math
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from phoenix_demigod.utils.logging import get_logger


class GeneCategory(Enum):
    """Categories of genetic traits."""
    BIOLOGICAL = "biological"
    PHYSICAL = "physical"
    MATHEMATICAL = "mathematical"
    TECHNICAL = "technical"


class Archetype(Enum):
    """Personality archetypes for cells."""
    EXPLORER = "explorer"
    GUARDIAN = "guardian"
    ARTIST = "artist"
    SCIENTIST = "scientist"
    WARRIOR = "warrior"
    HEALER = "healer"
    BUILDER = "builder"
    COMMUNICATOR = "communicator"
    LEADER = "leader"
    FOLLOWER = "follower"


class Mood(Enum):
    """Mood states for cells."""
    ALERT = "alert"
    CALM = "calm"
    EXCITED = "excited"
    FOCUSED = "focused"
    CREATIVE = "creative"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    CURIOUS = "curious"
    CONFIDENT = "confident"
    ANXIOUS = "anxious"
    MYSTERIOUS = "mysterious"
    INSPIRED = "inspired"
    METHODICAL = "methodical"
    SPONTANEOUS = "spontaneous"
    RESILIENT = "resilient"


@dataclass
class AnimalTrait:
    """Base class for animal-inspired traits."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    def apply_trait(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply this trait to a given context."""
        return context


@dataclass
class EcholocationTrait(AnimalTrait):
    """Bat echolocation trait for navigation and obstacle detection."""
    
    def __init__(self):
        super().__init__(
            name="Echolocation",
            description="Ultrasonic navigation and obstacle detection like bats",
            parameters={
                "frequency_range": (20, 120),  # kHz
                "precision": 0.95,
                "range_meters": 100
            }
        )
    
    def apply_trait(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply echolocation capabilities to context."""
        context["navigation_boost"] = 1.5
        context["obstacle_detection"] = True
        context["frequency_range"] = self.parameters["frequency_range"]
        return context


@dataclass
class BioluminescenceTrait(AnimalTrait):
    """Deep sea creature bioluminescence for communication."""
    
    def __init__(self):
        super().__init__(
            name="Bioluminescence",
            description="Convert oxygen to light for deep communication like abyssal creatures",
            parameters={
                "oxygen_to_light_efficiency": 0.87,
                "communication_range": 1000,
                "energy_cost": 0.3
            }
        )
    
    def apply_trait(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply bioluminescence capabilities to context."""
        context["deep_communication"] = True
        context["energy_conversion"] = self.parameters["oxygen_to_light_efficiency"]
        context["light_generation"] = True
        return context


@dataclass
class GoldenRatioTrait(AnimalTrait):
    """Mathematical golden ratio for harmonic growth."""
    
    def __init__(self):
        super().__init__(
            name="Golden Ratio",
            description="Harmonic growth and aesthetic optimization using φ = 1.618...",
            parameters={
                "phi": 1.618033988749,
                "growth_efficiency": 1.3,
                "aesthetic_score": 0.9
            }
        )
    
    def apply_trait(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply golden ratio optimization to context."""
        context["harmonic_growth"] = True
        context["growth_multiplier"] = self.parameters["growth_efficiency"]
        context["aesthetic_optimization"] = True
        return context


@dataclass
class TeslaCoilTrait(AnimalTrait):
    """Tesla coil resonance for energy transmission."""
    
    def __init__(self):
        super().__init__(
            name="Tesla Coil Resonance",
            description="Resonance frequency transmission and energy absorption",
            parameters={
                "resonance_frequency": 150000,  # Hz
                "energy_efficiency": 0.92,
                "transmission_range": 500
            }
        )
    
    def apply_trait(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Tesla coil resonance to context."""
        context["energy_transmission"] = True
        context["resonance_frequency"] = self.parameters["resonance_frequency"]
        context["wireless_power"] = True
        return context


@dataclass
class GenePy:
    """
    A genetic trait inspired by animal characteristics.
    
    Each GenePy represents a specific survival trait that has allowed
    animals to persist and thrive in their environments.
    """
    
    gene_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    category: GeneCategory = GeneCategory.BIOLOGICAL
    trait: AnimalTrait = field(default_factory=lambda: AnimalTrait("", ""))
    archetype: Archetype = Archetype.EXPLORER
    mood: Mood = Mood.ALERT
    buffs: List[str] = field(default_factory=list)
    debuffs: List[str] = field(default_factory=list)
    unique_properties: Dict[str, Any] = field(default_factory=dict)
    fitness_contribution: float = 0.0
    mutation_rate: float = 0.01
    expression_level: float = 1.0  # 0.0 to 1.0
    
    def mutate(self) -> 'GenePy':
        """Create a mutated version of this gene."""
        mutated = GenePy(
            name=self.name,
            category=self.category,
            trait=self.trait,
            archetype=self.archetype,
            mood=self.mood,
            buffs=self.buffs.copy(),
            debuffs=self.debuffs.copy(),
            unique_properties=self.unique_properties.copy(),
            fitness_contribution=self.fitness_contribution,
            mutation_rate=self.mutation_rate,
            expression_level=self.expression_level
        )
        
        # Apply mutations
        if random.random() < self.mutation_rate:
            # Mutate expression level
            mutated.expression_level = max(0.0, min(1.0, 
                self.expression_level + random.gauss(0, 0.1)
            ))
            
        if random.random() < self.mutation_rate * 0.5:
            # Mutate fitness contribution
            mutated.fitness_contribution += random.gauss(0, 0.05)
            
        if random.random() < self.mutation_rate * 0.3:
            # Mutate mood (rare)
            mutated.mood = random.choice(list(Mood))
            
        return mutated
    
    def crossover(self, other: 'GenePy') -> Tuple['GenePy', 'GenePy']:
        """Create two offspring through genetic crossover."""
        # Simple crossover - combine traits
        child1 = GenePy(
            name=f"{self.name}x{other.name}",
            category=self.category,
            trait=self.trait,
            archetype=self.archetype,
            mood=random.choice([self.mood, other.mood]),
            buffs=self.buffs + [b for b in other.buffs if b not in self.buffs],
            debuffs=self.debuffs,
            unique_properties={**self.unique_properties, **other.unique_properties},
            fitness_contribution=(self.fitness_contribution + other.fitness_contribution) / 2,
            mutation_rate=(self.mutation_rate + other.mutation_rate) / 2,
            expression_level=(self.expression_level + other.expression_level) / 2
        )
        
        child2 = GenePy(
            name=f"{other.name}x{self.name}",
            category=other.category,
            trait=other.trait,
            archetype=other.archetype,
            mood=random.choice([self.mood, other.mood]),
            buffs=other.buffs + [b for b in self.buffs if b not in other.buffs],
            debuffs=other.debuffs,
            unique_properties={**other.unique_properties, **self.unique_properties},
            fitness_contribution=(self.fitness_contribution + other.fitness_contribution) / 2,
            mutation_rate=(self.mutation_rate + other.mutation_rate) / 2,
            expression_level=(self.expression_level + other.expression_level) / 2
        )
        
        return child1, child2


class RubikPersonalityMatrix:
    """
    20-dimensional personality matrix for cells.
    
    Creates unique personalities using base-20 system with astrological
    influences and mood calculations.
    """
    
    PERSONALITY_DIMENSIONS = [
        'creativity', 'logic', 'empathy', 'aggression', 'curiosity',
        'patience', 'adaptability', 'leadership', 'cooperation', 'intuition',
        'analytical', 'artistic', 'social', 'independent', 'cautious',
        'bold', 'methodical', 'spontaneous', 'focused', 'versatile'
    ]
    
    def __init__(self, base: int = 20):
        self.base = base
        self.logger = get_logger("phoenixxhydra.personality")
        
        # Generate personality values (1 to base)
        self.personality_values = {
            dim: random.randint(1, base) for dim in self.PERSONALITY_DIMENSIONS
        }
        
        # Calculate derived properties
        self.mood_state = self._calculate_mood()
        self.archetype_alignment = self._determine_archetype()
        self.astrological_profile = self._generate_astrological_profile()
        self.compatibility_matrix = self._calculate_compatibility_matrix()
        
    def _calculate_mood(self) -> Mood:
        """Calculate mood based on personality dimensions."""
        # Use weighted combination of personality traits
        creativity_logic_ratio = self.personality_values['creativity'] / max(1, self.personality_values['logic'])
        social_independent_ratio = self.personality_values['social'] / max(1, self.personality_values['independent'])
        
        if creativity_logic_ratio > 1.5:
            return Mood.CREATIVE
        elif self.personality_values['aggression'] > 15:
            return Mood.AGGRESSIVE
        elif self.personality_values['curiosity'] > 16:
            return Mood.CURIOUS
        elif social_independent_ratio > 1.3:
            return Mood.EXCITED
        elif self.personality_values['patience'] > 17:
            return Mood.CALM
        else:
            return random.choice(list(Mood))
    
    def _determine_archetype(self) -> Archetype:
        """Determine archetype based on personality profile."""
        # Calculate archetype scores
        archetype_scores = {
            Archetype.EXPLORER: self.personality_values['curiosity'] + self.personality_values['bold'],
            Archetype.GUARDIAN: self.personality_values['patience'] + self.personality_values['cautious'],
            Archetype.ARTIST: self.personality_values['creativity'] + self.personality_values['artistic'],
            Archetype.SCIENTIST: self.personality_values['logic'] + self.personality_values['analytical'],
            Archetype.WARRIOR: self.personality_values['aggression'] + self.personality_values['bold'],
            Archetype.HEALER: self.personality_values['empathy'] + self.personality_values['cooperation'],
            Archetype.BUILDER: self.personality_values['methodical'] + self.personality_values['focused'],
            Archetype.COMMUNICATOR: self.personality_values['social'] + self.personality_values['empathy'],
            Archetype.LEADER: self.personality_values['leadership'] + self.personality_values['bold'],
            Archetype.FOLLOWER: self.personality_values['cooperation'] + self.personality_values['patience']
        }
        
        return max(archetype_scores, key=archetype_scores.get)
    
    def _generate_astrological_profile(self) -> Dict[str, Any]:
        """Generate astrological influences for uniqueness."""
        elements = ['fire', 'earth', 'air', 'water']
        qualities = ['cardinal', 'fixed', 'mutable']
        planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn']
        
        return {
            'dominant_element': random.choice(elements),
            'quality': random.choice(qualities),
            'ruling_planet': random.choice(planets),
            'lunar_phase': random.randint(0, 29),  # Days in lunar cycle
            'birth_timestamp': datetime.now().timestamp(),
            'cosmic_seed': random.randint(1, 999999)
        }
    
    def _calculate_compatibility_matrix(self) -> Dict[str, float]:
        """Calculate compatibility with different personality types."""
        compatibility = {}
        
        for archetype in Archetype:
            # Base compatibility on personality similarity/complementarity
            score = 0.5  # Base neutral compatibility
            
            if archetype == self.archetype_alignment:
                score += 0.3  # Same archetype bonus
            
            # Add some randomness for uniqueness
            score += random.gauss(0, 0.1)
            
            compatibility[archetype.value] = max(0.0, min(1.0, score))
        
        return compatibility
    
    def calculate_relationship_score(self, other: 'RubikPersonalityMatrix') -> float:
        """Calculate relationship compatibility with another personality."""
        # Compare personality dimensions
        dimension_similarity = 0.0
        for dim in self.PERSONALITY_DIMENSIONS:
            diff = abs(self.personality_values[dim] - other.personality_values[dim])
            similarity = 1.0 - (diff / self.base)
            dimension_similarity += similarity
        
        dimension_similarity /= len(self.PERSONALITY_DIMENSIONS)
        
        # Factor in archetype compatibility
        archetype_compatibility = self.compatibility_matrix.get(
            other.archetype_alignment.value, 0.5
        )
        
        # Combine factors
        relationship_score = (dimension_similarity * 0.6 + archetype_compatibility * 0.4)
        
        # Add astrological influence
        cosmic_influence = self._calculate_cosmic_compatibility(other)
        relationship_score = (relationship_score * 0.8 + cosmic_influence * 0.2)
        
        return max(0.0, min(1.0, relationship_score))
    
    def _calculate_cosmic_compatibility(self, other: 'RubikPersonalityMatrix') -> float:
        """Calculate astrological compatibility."""
        my_profile = self.astrological_profile
        other_profile = other.astrological_profile
        
        # Element compatibility
        element_compatibility = {
            ('fire', 'air'): 0.8, ('air', 'fire'): 0.8,
            ('earth', 'water'): 0.8, ('water', 'earth'): 0.8,
            ('fire', 'fire'): 0.7, ('air', 'air'): 0.7,
            ('earth', 'earth'): 0.7, ('water', 'water'): 0.7,
            ('fire', 'water'): 0.3, ('water', 'fire'): 0.3,
            ('earth', 'air'): 0.4, ('air', 'earth'): 0.4,
            ('fire', 'earth'): 0.5, ('earth', 'fire'): 0.5,
            ('air', 'water'): 0.5, ('water', 'air'): 0.5
        }
        
        elements = (my_profile['dominant_element'], other_profile['dominant_element'])
        base_compatibility = element_compatibility.get(elements, 0.5)
        
        # Lunar phase influence
        lunar_diff = abs(my_profile['lunar_phase'] - other_profile['lunar_phase'])
        lunar_influence = 1.0 - (lunar_diff / 29.0)
        
        return (base_compatibility * 0.7 + lunar_influence * 0.3)


class GenePool:
    """
    Manages the collection of available genes and genetic operations.
    
    Provides methods for gene selection, combination, and evolution.
    """
    
    def __init__(self):
        self.logger = get_logger("phoenixxhydra.genepool")
        self.genes: Dict[str, GenePy] = {}
        self._initialize_gene_library()
        
    def _initialize_gene_library(self):
        """Initialize the library with animal-inspired genes."""
        # Biological genes
        self._add_gene("Echolocation_Bat", GeneCategory.BIOLOGICAL, EcholocationTrait(),
                      Archetype.EXPLORER, Mood.ALERT, 
                      ["navigation_boost", "obstacle_detection"], ["light_sensitivity"])
        
        self._add_gene("Bioluminescence_Abyss", GeneCategory.BIOLOGICAL, BioluminescenceTrait(),
                      Archetype.COMMUNICATOR, Mood.MYSTERIOUS,
                      ["deep_communication", "energy_conversion"], ["surface_vulnerability"])
        
        self._add_gene("Magnetoreception_Turtle", GeneCategory.BIOLOGICAL, 
                      AnimalTrait("Magnetoreception", "Geospatial navigation using magnetic fields"),
                      Archetype.EXPLORER, Mood.METHODICAL,
                      ["magnetic_navigation", "precision_movement"], ["electromagnetic_interference"])
        
        # Mathematical genes
        self._add_gene("Golden_Ratio_Math", GeneCategory.MATHEMATICAL, GoldenRatioTrait(),
                      Archetype.ARTIST, Mood.INSPIRED,
                      ["harmonic_growth", "aesthetic_optimization"], ["perfectionism_paralysis"])
        
        # Technical genes
        self._add_gene("Tesla_Coil_Resonance", GeneCategory.TECHNICAL, TeslaCoilTrait(),
                      Archetype.SCIENTIST, Mood.FOCUSED,
                      ["energy_transmission", "wireless_power"], ["frequency_interference"])
        
        # Physical genes
        self._add_gene("Quantum_Tunneling", GeneCategory.PHYSICAL,
                      AnimalTrait("Quantum Tunneling", "Probability-based barrier penetration"),
                      Archetype.EXPLORER, Mood.CURIOUS,
                      ["barrier_penetration", "probability_manipulation"], ["quantum_decoherence"])
        
        self.logger.info(f"Initialized gene library with {len(self.genes)} genes")
    
    def _add_gene(self, name: str, category: GeneCategory, trait: AnimalTrait,
                  archetype: Archetype, mood: Mood, buffs: List[str], debuffs: List[str]):
        """Add a gene to the library."""
        gene = GenePy(
            name=name,
            category=category,
            trait=trait,
            archetype=archetype,
            mood=mood,
            buffs=buffs,
            debuffs=debuffs,
            fitness_contribution=random.uniform(0.1, 0.9),
            mutation_rate=random.uniform(0.005, 0.02)
        )
        self.genes[gene.gene_id] = gene
    
    def get_random_genes(self, count: int) -> List[GenePy]:
        """Get a random selection of genes."""
        available_genes = list(self.genes.values())
        return random.sample(available_genes, min(count, len(available_genes)))
    
    def generate_combination(self, count: int = 20, base: int = 20) -> List[GenePy]:
        """Generate a unique combination of genes for a cell."""
        # Select genes with some bias towards fitness
        genes = list(self.genes.values())
        weights = [gene.fitness_contribution + 0.1 for gene in genes]  # Avoid zero weights
        
        selected_genes = random.choices(genes, weights=weights, k=count)
        
        # Apply some mutations for uniqueness
        mutated_genes = []
        for gene in selected_genes:
            if random.random() < 0.1:  # 10% chance of mutation
                mutated_genes.append(gene.mutate())
            else:
                mutated_genes.append(gene)
        
        return mutated_genes
    
    def evolve_genes(self, parent_genes: List[List[GenePy]], 
                    fitness_scores: List[float]) -> List[GenePy]:
        """Evolve new genes based on parent fitness."""
        # Select parents based on fitness
        total_fitness = sum(fitness_scores)
        if total_fitness == 0:
            return self.get_random_genes(20)
        
        probabilities = [f / total_fitness for f in fitness_scores]
        
        # Select two parents
        parent1_idx = random.choices(range(len(parent_genes)), weights=probabilities)[0]
        parent2_idx = random.choices(range(len(parent_genes)), weights=probabilities)[0]
        
        parent1_genes = parent_genes[parent1_idx]
        parent2_genes = parent_genes[parent2_idx]
        
        # Combine genes from both parents
        combined_genes = []
        min_length = min(len(parent1_genes), len(parent2_genes))
        
        for i in range(min_length):
            if random.random() < 0.5:
                combined_genes.append(parent1_genes[i])
            else:
                combined_genes.append(parent2_genes[i])
        
        # Fill remaining slots with mutations or new genes
        while len(combined_genes) < 20:
            if random.random() < 0.7 and combined_genes:
                # Mutate existing gene
                base_gene = random.choice(combined_genes)
                combined_genes.append(base_gene.mutate())
            else:
                # Add random gene
                combined_genes.extend(self.get_random_genes(1))
        
        return combined_genes[:20]
    
    def add_custom_gene(self, gene: GenePy):
        """Add a custom gene to the pool."""
        self.genes[gene.gene_id] = gene
        self.logger.info(f"Added custom gene: {gene.name}")
    
    def get_gene_stats(self) -> Dict[str, Any]:
        """Get statistics about the gene pool."""
        category_counts = {}
        archetype_counts = {}
        
        for gene in self.genes.values():
            category_counts[gene.category.value] = category_counts.get(gene.category.value, 0) + 1
            archetype_counts[gene.archetype.value] = archetype_counts.get(gene.archetype.value, 0) + 1
        
        return {
            "total_genes": len(self.genes),
            "category_distribution": category_counts,
            "archetype_distribution": archetype_counts,
            "average_fitness": sum(g.fitness_contribution for g in self.genes.values()) / len(self.genes),
            "average_mutation_rate": sum(g.mutation_rate for g in self.genes.values()) / len(self.genes)
        }