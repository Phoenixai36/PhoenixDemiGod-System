#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Exponential Learning Module for Phoenix DemiGod

This module implements exponential learning algorithms that accelerate training
by adaptively adjusting the learning rate, sample selection, and model complexity
based on learning curves and performance metrics.
"""

import logging
import math
import numpy as np
import time
from typing import Dict, List, Optional, Tuple, Union, Callable

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, Subset, WeightedRandomSampler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/exponential_learning.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ExponentialLearning")

class ComplexityScheduler:
    """
    Dynamically adjusts model complexity based on training progress.
    
    Attributes:
        initial_complexity (float): Initial complexity factor
        max_complexity (float): Maximum complexity factor
        growth_rate (float): Rate at which complexity increases
        patience (int): Number of evaluations with no improvement before adjusting
        min_delta (float): Minimum change in metric to be considered improvement
        model_adapter (Callable): Function to adapt model complexity
    """
    
    def __init__(
        self,
        initial_complexity: float = 0.3,
        max_complexity: float = 1.0,
        growth_rate: float = 0.1,
        patience: int = 5,
        min_delta: float = 0.001,
        model_adapter: Callable = None
    ):
        """
        Initialize the complexity scheduler.
        
        Args:
            initial_complexity: Initial complexity factor
            max_complexity: Maximum complexity factor
            growth_rate: Rate at which complexity increases
            patience: Number of evaluations with no improvement before adjusting
            min_delta: Minimum change in metric to be considered improvement
            model_adapter: Function to adapt model complexity
        """
        self.complexity = initial_complexity
        self.max_complexity = max_complexity
        self.growth_rate = growth_rate
        self.patience = patience
        self.min_delta = min_delta
        self.model_adapter = model_adapter
        
        self.current_patience = patience
        self.best_metric = float('-inf')
        
        logger.info(f"Initialized ComplexityScheduler with initial_complexity={initial_complexity}, "
                  f"max_complexity={max_complexity}, growth_rate={growth_rate}")
    
    def step(self, metric: float, model: nn.Module) -> nn.Module:
        """
        Update complexity based on performance metric.
        
        Args:
            metric: Performance metric value
            model: Model to adapt
            
        Returns:
            Adapted model
        """
        # Check if there's improvement
        delta = metric - self.best_metric
        
        if delta > self.min_delta:
            # Improvement detected
            self.best_metric = metric
            self.current_patience = self.patience
            logger.info(f"Performance improved to {metric:.6f}")
            
            # If we're already at max complexity, no need to adapt
            if self.complexity >= self.max_complexity:
                return model
        else:
            # No improvement
            self.current_patience -= 1
            logger.info(f"No improvement detected. Patience: {self.current_patience}")
            
            if self.current_patience <= 0 and self.complexity < self.max_complexity:
                # Increase complexity
                old_complexity = self.complexity
                self.complexity = min(self.max_complexity, 
                                     self.complexity + self.growth_rate)
                
                logger.info(f"Increasing complexity from {old_complexity:.2f} to {self.complexity:.2f}")
                
                # Reset patience
                self.current_patience = self.patience
                
                # Adapt model if adapter is provided
                if self.model_adapter is not None:
                    model = self.model_adapter(model, self.complexity)
        
        return model
    
    def get_current_complexity(self) -> float:
        """
        Get the current complexity factor.
        
        Returns:
            Current complexity factor
        """
        return self.complexity


class CurriculumLearning:
    """
    Implements curriculum learning by presenting examples in order of difficulty.
    
    Attributes:
        difficulty_scorer (Callable): Function to score examples by difficulty
        initial_easy_ratio (float): Initial ratio of easy examples to use
        final_easy_ratio (float): Final ratio of easy examples to use
        total_steps (int): Total number of steps to transition from initial to final ratio
        current_step (int): Current step in the curriculum
    """
    
    def __init__(
        self,
        difficulty_scorer: Callable = None,
        initial_easy_ratio: float = 0.8,
        final_easy_ratio: float = 0.2,
        total_steps: int = 100
    ):
        """
        Initialize the curriculum learning scheduler.
        
        Args:
            difficulty_scorer: Function to score examples by difficulty
            initial_easy_ratio: Initial ratio of easy examples to use
            final_easy_ratio: Final ratio of easy examples to use
            total_steps: Total number of steps to transition from initial to final ratio
        """
        self.difficulty_scorer = difficulty_scorer
        self.initial_easy_ratio = initial_easy_ratio
        self.final_easy_ratio = final_easy_ratio
        self.total_steps = total_steps
        self.current_step = 0
        self.difficulty_scores = None
        
        logger.info(f"Initialized CurriculumLearning with initial_easy_ratio={initial_easy_ratio}, "
                  f"final_easy_ratio={final_easy_ratio}, total_steps={total_steps}")
    
    def score_dataset(self, dataset: Dataset, model: nn.Module = None) -> np.ndarray:
        """
        Score examples in the dataset by difficulty.
        
        Args:
            dataset: Dataset to score
            model: Model used to evaluate difficulty (optional)
            
        Returns:
            Array of difficulty scores
        """
        if self.difficulty_scorer is None:
            logger.warning("No difficulty scorer provided. Using random scores.")
            return np.random.random(len(dataset))
        
        if self.difficulty_scores is not None:
            logger.info("Using cached difficulty scores")
            return self.difficulty_scores
        
        logger.info("Scoring dataset examples by difficulty")
        self.difficulty_scores = self.difficulty_scorer(dataset, model)
        return self.difficulty_scores
    
    def get_curriculum_sampler(
        self,
        dataset: Dataset,
        model: nn.Module = None,
        rescore: bool = False
    ) -> WeightedRandomSampler:
        """
        Get a weighted sampler based on current curriculum stage.
        
        Args:
            dataset: Dataset to sample from
            model: Model used to evaluate difficulty (optional)
            rescore: Whether to rescore the dataset
            
        Returns:
            Weighted random sampler for curriculum learning
        """
        # Score or rescore dataset if needed
        if self.difficulty_scores is None or rescore:
            self.difficulty_scores = self.score_dataset(dataset, model)
        
        # Calculate current easy ratio
        if self.current_step >= self.total_steps:
            easy_ratio = self.final_easy_ratio
        else:
            # Linear interpolation between initial and final ratios
            progress = self.current_step / self.total_steps
            easy_ratio = self.initial_easy_ratio - progress * (self.initial_easy_ratio - self.final_easy_ratio)
        
        # Sort indices by difficulty scores
        sorted_indices = np.argsort(self.difficulty_scores)
        num_examples = len(sorted_indices)
        
        # Determine number of easy and hard examples
        num_easy = int(num_examples * easy_ratio)
        num_hard = num_examples - num_easy
        
        # Assign weights
        weights = np.zeros(num_examples)
        
        # Higher weight for easy examples
        if num_easy > 0:
            weights[sorted_indices[:num_easy]] = 1.0 / num_easy
        
        # Lower weight for hard examples
        if num_hard > 0:
            weights[sorted_indices[num_easy:]] = 0.1 / num_hard
        
        # Create sampler
        sampler = WeightedRandomSampler(weights, num_samples=num_examples, replacement=True)
        
        return sampler
    
    def step(self):
        """Advance the curriculum by one step."""
        if self.current_step < self.total_steps:
            self.current_step += 1
