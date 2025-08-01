#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Neuroevolution Manager for Phoenix DemiGod

This module implements neuroevolution algorithms to optimize neural network
architectures using genetic algorithms with quantum-inspired enhancements.
"""

import logging
import os
import random
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Callable

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from src.utils.config_loader import ConfigLoader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/neuroevolution.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("NeuroevolutionManager")

class Individual:
    """
    Represents an individual neural network in the population.
    
    Attributes:
        architecture (Dict): Neural network architecture specification
        model (nn.Module): PyTorch model instance
        fitness (float): Fitness score of the individual
        id (str): Unique identifier
        created_at (datetime): Creation timestamp
        generation (int): Generation number
        parent_ids (List[str]): IDs of parent individuals
    """
    
    def __init__(self, architecture: Dict, model: nn.Module = None):
        """
        Initialize a new individual.
        
        Args:
            architecture: Neural network architecture specification
            model: PyTorch model instance (if None, will be created from architecture)
        """
        self.architecture = architecture
        self.model = model if model is not None else self._build_model()
        self.fitness = 0.0
        self.id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now()
        self.generation = 0
        self.parent_ids = []
    
    def _build_model(self) -> nn.Module:
        """
        Build a PyTorch model from the architecture specification.
        
        Returns:
            PyTorch model instance
        """
        # This is a placeholder. In a real implementation, this would create
        # a model according to the architecture specification
        layers = []
        input_dim = self.architecture["input_dim"]
        
        for layer_spec in self.architecture["layers"]:
            if layer_spec["type"] == "linear":
                layers.append(nn.Linear(input_dim, layer_spec["units"]))
                if layer_spec.get("activation") == "relu":
                    layers.append(nn.ReLU())
                elif layer_spec.get("activation") == "tanh":
                    layers.append(nn.Tanh())
                input_dim = layer_spec["units"]
            elif layer_spec["type"] == "dropout":
                layers.append(nn.Dropout(layer_spec["rate"]))
        
        # Output layer
        output_dim = self.architecture["output_dim"]
        layers.append(nn.Linear(input_dim, output_dim))
        
        return nn.Sequential(*layers)
    
    def get_param_count(self) -> int:
        """
        Get the number of trainable parameters in the model.
        
        Returns:
            Number of trainable parameters
        """
        return sum(p.numel() for p in self.model.parameters() if p.requires_grad)
    
    def __str__(self) -> str:
        """String representation of the individual."""
        return f"Individual(id={self.id}, fitness={self.fitness:.4f}, params={self.get_param_count()})"

class NeuroevolutionManager:
    """
    Manager for neuroevolution process using genetic algorithms.
    
    Attributes:
        population_size (int): Size of the population
        mutation_rate (float): Probability of mutation
        crossover_rate (float): Probability of crossover
        elitism_count (int): Number of top individuals to preserve unchanged
        tournament_size (int): Size of tournament for selection
        population (List[Individual]): Current population
        generation (int): Current generation number
        best_individual (Individual): Best individual found so far
        history (List[Dict]): History of evolution metrics
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the neuroevolution manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or ConfigLoader().load_config("training/neuroevolution")
        
        # Evolution parameters
        self.population_size = self.config.get("population_size", 30)
        self.mutation_rate = self.config.get("mutation_rate", 0.2)
        self.crossover_rate = self.config.get("crossover_rate", 0.7)
        self.elitism_count = self.config.get("elitism_count", 2)
        self.tournament_size = self.config.get("tournament_size", 3)
        self.use_quantum = self.config.get("use_quantum", False)
        
        # State
        self.population = []
        self.generation = 0
        self.best_individual = None
        self.history = []
        
        # Architecture specifications
        self.input_dim = self.config.get("input_dim", 768)
        self.output_dim = self.config.get("output_dim", 10)
        self.min_layers = self.config.get("min_layers", 1)
        self.max_layers = self.config.get("max_layers", 5)
        self.min_units = self.config.get("min_units", 32)
        self.max_units = self.config.get("max_units", 512)
        
        logger.info(f"NeuroevolutionManager initialized with population size {self.population_size}")
    
    def initialize_population(self) -> None:
        """Initialize the population with random individuals."""
        logger.info("Initializing population")
        self.population = []
        
        for _ in range(self.population_size):
            # Create random architecture
            architecture = self._generate_random_architecture()
            
            # Create individual
            individual = Individual(architecture)
            individual.generation = self.generation
            
            self.population.append(individual)
        
        logger.info(f"Initialized population with {len(self.population)} individuals")
    
    def evolve(self, fitness_function: Callable[[Individual], float], generations: int = 10) -> Individual:
        """
        Evolve the population for a specified number of generations.
        
        Args:
            fitness_function: Function to evaluate individual fitness
            generations: Number of generations to evolve
            
        Returns:
            Best individual found
        """
        logger.info(f"Starting evolution for {generations} generations")
        
        # Initialize population if not already done
        if not self.population:
            self.initialize_population()
        
        for gen in range(generations):
            self.generation = gen + 1
            logger.info(f"Generation {self.generation}/{generations}")
            
            # Evaluate fitness
            self._evaluate_fitness(fitness_function)
            
            # Record history
            self._record_history()
            
            # Check if we've reached the last generation
            if gen == generations - 1:
                break
            
            # Create next generation
            self._create_next_generation()
        
        logger.info(f"Evolution completed. Best fitness: {self.best_individual.fitness:.4f}")
        return self.best_individual
    
    def _evaluate_fitness(self, fitness_function: Callable[[Individual], float]) -> None:
        """
        Evaluate fitness for all individuals in the population.
        
        Args:
            fitness_function: Function to evaluate individual fitness
        """
        for individual in self.population:
            individual.fitness = fitness_function(individual)
        
        # Sort population by fitness (descending)
        self.population.sort(key=lambda ind: ind.fitness, reverse=True)
        
        # Update best individual
        if self.best_individual is None or self.population[0].fitness > self.best_individual.fitness:
            self.best_individual = self.population[0]
            logger.info(f"New best individual: {self.best_individual}")
    
    def _create_next_generation(self) -> None:
        """Create the next generation through selection, crossover, and mutation."""
        new_population = []
        
        # Elitism: keep best individuals unchanged
        for i in range(min(self.elitism_count, len(self.population))):
            new_population.append(self.population[i])
        
        # Fill the rest of the population using selection, crossover, and mutation
        while len(new_population) < self.population_size:
            # Selection
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()
            
            # Crossover
            if random.random() < self.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = Individual(parent1.architecture), Individual(parent2.architecture)
                
            # Set parent information
            child1.parent_ids = [parent1.id, parent2.id]
            child2.parent_ids = [parent1.id, parent2.id]
            child1.generation = self.generation
            child2.generation = self.generation
            
            # Mutation
            if random.random() < self.mutation_rate:
                self._mutate(child1)
            if random.random() < self.mutation_rate:
                self._mutate(child2)
            
            # Add children to new population
            new_population.append(child1)
            if len(new_population) < self.population_size:
                new_population.append(child2)
        
        # Update population
        self.population = new_population
    
    def _tournament_selection(self) -> Individual:
        """
        Select an individual using tournament selection.
        
        Returns:
            Selected individual
        """
        # Select random individuals for the tournament
        participants = random.sample(self.population, min(self.tournament_size, len(self.population)))
        
        # Select the best individual from the tournament
        return max(participants, key=lambda ind: ind.fitness)
    
    def _crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """
        Perform crossover between two parents.
        
        Args:
            parent1: First parent
            parent2: Second parent
            
        Returns:
            Two child individuals
        """
        # Create copies of parent architectures
        arch1 = parent1.architecture.copy()
        arch2 = parent2.architecture.copy()
        
        # Perform crossover on the layer specifications
        layers1 = arch1["layers"]
        layers2 = arch2["layers"]
        
        # Select crossover point
        min_len = min(len(layers1), len(layers2))
        if min_len > 1:
            if self.use_quantum:
                # Quantum-inspired crossover: superposition of architectures
                crossover_point = random.randint(1, min_len - 1)
                
                # Create superpositions
                child1_layers = layers1[:crossover_point] + layers2[crossover_point:]
                child2_layers = layers2[:crossover_point] + layers1[crossover_point:]
                
                # Apply quantum collapse (randomly select some layers)
                for i in range(len(child1_layers)):
                    if random.random() < 0.5:
                        if i < len(layers1):
                            child1_layers[i] = layers1[i]
                        else:
                            child1_layers[i] = {"type": "linear", "units": random.randint(self.min_units, self.max_units)}
                
                for i in range(len(child2_layers)):
                    if random.random() < 0.5:
                        if i < len(layers2):
                            child2_layers[i] = layers2[i]
                        else:
                            child2_layers[i] = {"type": "linear", "units": random.randint(self.min_units, self.max_units)}
            else:
                # Classical crossover: swap layers at crossover point
                crossover_point = random.randint(1, min_len - 1)
                child1_layers = layers1[:crossover_point] + layers2[crossover_point:]
                child2_layers = layers2[:crossover_point] + layers1[crossover_point:]
        else:
            child1_layers = layers1
            child2_layers = layers2
        
        # Create child architectures
        child1_arch = arch1.copy()
        child1_arch["layers"] = child1_layers
        
        child2_arch = arch2.copy()
        child2_arch["layers"] = child2_layers
        
        # Create child individuals
        child1 = Individual(child1_arch)
        child2 = Individual(child2_arch)
        
        return child1, child2
    
    def _mutate(self, individual: Individual) -> None:
        """
        Mutate an individual.
        
        Args:
            individual: Individual to mutate
        """
        arch = individual.architecture
        layers = arch["layers"]
        
        if self.use_quantum:
            # Quantum-inspired mutation: probabilistic changes
            mutation_type = random.choice(["add", "remove", "modify", "superposition"])
        else:
            # Classical mutation: deterministic changes
            mutation_type = random.choice(["add", "remove", "modify"])
        
        if mutation_type == "add" and len(layers) < self.max_layers:
            # Add a new layer
            position = random.randint(0, len(layers))
            new_layer = self._generate_random_layer(
                input_dim=layers[position-1]["units"] if position > 0 else self.input_dim
            )
            layers.insert(position, new_layer)
            
        elif mutation_type == "remove" and len(layers) > self.min_layers:
            # Remove a layer
            position = random.randint(0, len(layers) - 1)
            layers.pop(position)
            
        elif mutation_type == "modify" and layers:
            # Modify a layer
            position = random.randint(0, len(layers) - 1)
            if layers[position]["type"] == "linear":
                # Modify number of units
                if random.random() < 0.7:
                    layers[position]["units"] = random.randint(self.min_units, self.max_units)
                
                # Modify activation
                if random.random() < 0.3:
                    layers[position]["activation"] = random.choice([None, "relu", "tanh"])
            
            elif layers[position]["type"] == "dropout":
                # Modify dropout rate
                layers[position]["rate"] = random.uniform(0.1, 0.5)
        
        elif mutation_type == "superposition" and self.use_quantum and layers:
            # Quantum-inspired superposition: create a superposition of layer configurations
            position = random.randint(0, len(layers) - 1)
            if layers[position]["type"] == "linear":
                # Create superposition of units
                superposition_units = [
                    random.randint(self.min_units, self.max_units)
                    for _ in range(3)
                ]
                # Collapse to one value
                layers[position]["units"] = random.choice(superposition_units)
                
                # Create superposition of activations
                superposition_activations = [None, "relu", "tanh"]
                # Collapse to one value
                layers[position]["activation"] = random.choice(superposition_activations)
        
        # Ensure model architecture is valid
        self._validate_architecture(arch)
        
        # Update the model
        individual.model = individual._build_model()
    
    def _generate_random_architecture(self) -> Dict:
        """
        Generate a random neural network architecture.
        
        Returns:
            Architecture specification dictionary
        """
        num_layers = random.randint(self.min_layers, self.max_layers)
        
        architecture = {
            "input_dim": self.input_dim,
            "output_dim": self.output_dim,
            "layers": []
        }
        
        input_dim = self.input_dim
        for _ in range(num_layers):
            layer = self._generate_random_layer(input_dim)
            architecture["layers"].append(layer)
            
            if layer["type"] == "linear":
                input_dim = layer["units"]
        
        return architecture
    
    def _generate_random_layer(self, input_dim: int) -> Dict:
        """
        Generate a random layer specification.
        
        Args:
            input_dim: Input dimension for the layer
            
        Returns:
            Layer specification dictionary
        """
        layer_type = random.choice(["linear", "dropout"])
        
        if layer_type == "linear":
            units = random.randint(self.min_units, self.max_units)
            activation = random.choice([None, "relu", "tanh"])
            
            layer = {
                "type": "linear",
                "units": units
            }
            
            if activation:
                layer["activation"] = activation
                
            return layer
        
        elif layer_type == "dropout":
            rate = random.uniform(0.1, 0.5)
            
            return {
                "type": "dropout",
                "rate": rate
            }
    
    def _validate_architecture(self, arch: Dict) -> None:
        """
        Ensure architecture is valid, fixing any issues.
        
        Args:
            arch: Architecture specification to validate
        """
        layers = arch["layers"]
        
        # Ensure we have at least the minimum number of layers
        while len(layers) < self.min_layers:
            input_dim = self.input_dim if not layers else layers[-1].get("units", self.input_dim)
            layers.append(self._generate_random_layer(input_dim))
        
        # Ensure we don't have dropout at the end
        if layers and layers[-1]["type"] == "dropout":
            # Replace with a linear layer
            input_dim = layers[-2].get("units", self.input_dim) if len(layers) > 1 else self.input_dim
            layers[-1] = {
                "type": "linear",
                "units": random.randint(self.min_units, self.max_units),
                "activation": random.choice([None, "relu", "tanh"])
            }
    
    def _record_history(self) -> None:
        """Record metrics for the current generation."""
        avg_fitness = sum(ind.fitness for ind in self.population) / len(self.population)
        best_fitness = self.population[0].fitness
        worst_fitness = self.population[-1].fitness
        
        entry = {
            "generation": self.generation,
            "best_fitness": best_fitness,
            "avg_fitness": avg_fitness,
            "worst_fitness": worst_fitness,
            "population_size": len(self.population),
            "timestamp": datetime.now().isoformat()
        }
        
        self.history.append(entry)
    
    def save_best_model(self, path: str) -> bool:
        """
        Save the best model to a file.
        
        Args:
            path: Path to save the model
            
        Returns:
            True if successful, False otherwise
        """
        if self.best_individual is None:
            logger.warning("No best individual to save")
            return False
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Save model weights
            torch.save(self.best_individual.model.state_dict(), path)
            
            # Save architecture
            with open(f"{path}.arch.json", "w") as f:
                import json
                json.dump(self.best_individual.architecture, f)
            
            logger.info(f"Saved best model to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")
            return False
    
    def load_model(self, path: str) -> Optional[Individual]:
        """
        Load a model from a file.
        
        Args:
            path: Path to the model
            
        Returns:
            Loaded individual or None if loading fails
        """
        try:
            # Load architecture
            import json
            with open(f"{path}.arch.json", "r") as f:
                architecture = json.load(f)
            
            # Create individual
            individual = Individual(architecture)
            
            # Load model weights
            individual.model.load_state_dict(torch.load(path))
            
            logger.info(f"Loaded model from {path}")
            return individual
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return None
    
    def get_summary(self) -> Dict:
        """
        Get a summary of the evolution process.
        
        Returns:
            Summary dictionary
        """
        if not self.history:
            return {"status": "No evolution history available"}
        
        first_gen = self.history[0]
        last_gen = self.history[-1]
        
        improvement = (last_gen["best_fitness"] - first_gen["best_fitness"]) / first_gen["best_fitness"] * 100 if first_gen["best_fitness"] != 0 else 0
        
        return {
            "generations": self.generation,
            "initial_best_fitness": first_gen["best_fitness"],
            "final_best_fitness": last_gen["best_fitness"],
            "improvement_percent": improvement,
            "best_individual": str(self.best_individual) if self.best_individual else None
        }
