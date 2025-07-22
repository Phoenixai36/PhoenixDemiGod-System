#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Holographic Memory Module for Phoenix DemiGod

This module implements a holographic memory system that provides distributed
storage with content-based retrieval and superposition capabilities.
"""

import logging
import numpy as np
import torch
from typing import Dict, List, Optional, Tuple, Union

from src.utils.config_loader import ConfigLoader
from src.utils.vector_representation import VectorRepresentation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/holographic_memory.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HolographicMemory")

class HolographicMemory:
    """
    Holographic memory system using circular convolution for storage and retrieval.
    
    Attributes:
        dimension (int): Dimension of the memory vectors
        memory_traces (Dict[str, np.ndarray]): Dictionary mapping keys to memory traces
        vector_rep (VectorRepresentation): Utility for converting content to vectors
        capacity_used (float): Percentage of memory capacity currently used
    """
    
    def __init__(self, dimension: int = 1024, config: Dict = None):
        """
        Initialize the holographic memory system.
        
        Args:
            dimension: Dimension of memory vectors
            config: Configuration dictionary
        """
        self.config = config or ConfigLoader().load_config("memory/holographic")
        self.dimension = dimension
        self.memory_traces = {}
        self.vector_rep = VectorRepresentation()
        self.capacity_used = 0.0
        
        # Load configuration if available
        if self.config:
            self.dimension = self.config.get("dimension", dimension)
        
        logger.info(f"Holographic Memory initialized with dimension {self.dimension}")
    
    def store(self, key: str, content: Union[str, np.ndarray]) -> bool:
        """
        Store content in holographic memory.
        
        Args:
            key: Unique identifier for the content
            content: Content to store (text or vector)
            
        Returns:
            True if storage successful, False otherwise
        """
        try:
            # Convert content to vector if it's text
            if isinstance(content, str):
                content_vector = self.vector_rep.encode(content)
            else:
                content_vector = content
                
            # Ensure vector has correct dimension
            if len(content_vector) != self.dimension:
                content_vector = self._resize_vector(content_vector, self.dimension)
            
            # Generate a unique key vector
            key_vector = self._generate_key_vector(key)
            
            # Use circular convolution to bind key and content
            memory_trace = self._circular_convolution(key_vector, content_vector)
            
            # Store the memory trace
            self.memory_traces[key] = memory_trace
            
            # Update capacity used
            self.capacity_used = len(self.memory_traces) / self._theoretical_capacity()
            
            logger.info(f"Stored content with key '{key}'. Capacity used: {self.capacity_used:.2%}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store content with key '{key}': {str(e)}")
            return False
    
    def retrieve(self, key: str) -> Optional[np.ndarray]:
        """
        Retrieve content from holographic memory using its key.
        
        Args:
            key: The key used during storage
            
        Returns:
            Retrieved content vector or None if retrieval fails
        """
        try:
            if key not in self.memory_traces:
                logger.warning(f"No content found with key '{key}'")
                return None
            
            # Get the memory trace
            memory_trace = self.memory_traces[key]
            
            # Generate the key vector
            key_vector = self._generate_key_vector(key)
            
            # Use circular correlation to unbind the content
            content_vector = self._circular_correlation(memory_trace, key_vector)
            
            logger.info(f"Retrieved content with key '{key}'")
            return content_vector
            
        except Exception as e:
            logger.error(f"Failed to retrieve content with key '{key}': {str(e)}")
            return None
    
    def retrieve_similar(self, content: Union[str, np.ndarray], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Retrieve keys with content similar to the query.
        
        Args:
            content: Query content (text or vector)
            top_k: Number of top results to return
            
        Returns:
            List of (key, similarity) tuples sorted by similarity
        """
        try:
            # Convert query to vector if it's text
            if isinstance(content, str):
                query_vector = self.vector_rep.encode(content)
            else:
                query_vector = content
                
            # Ensure vector has correct dimension
            if len(query_vector) != self.dimension:
                query_vector = self._resize_vector(query_vector, self.dimension)
            
            # Calculate similarity with all memory traces
            similarities = []
            for key, memory_trace in self.memory_traces.items():
                # Retrieve content vector
                content_vector = self.retrieve(key)
                if content_vector is not None:
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_vector, content_vector)
                    similarities.append((key, similarity))
            
            # Sort by similarity (descending) and take top-k
            similarities.sort(key=lambda x: x[1], reverse=True)
            top_results = similarities[:top_k]
            
            logger.info(f"Found {len(top_results)} similar items for query")
            return top_results
            
        except Exception as e:
            logger.error(f"Failed to retrieve similar content: {str(e)}")
            return []
    
    def superpose(self, keys: List[str]) -> Optional[np.ndarray]:
        """
        Create a superposition of multiple memory traces.
        
        Args:
            keys: List of keys to superpose
            
        Returns:
            Superposed memory trace or None if superposition fails
        """
        try:
            if not keys:
                logger.warning("No keys provided for superposition")
                return None
            
            # Check if all keys exist
            missing_keys = [k for k in keys if k not in self.memory_traces]
            if missing_keys:
                logger.warning(f"Some keys not found: {missing_keys}")
                return None
            
            # Create superposition by adding memory traces
            superposition = np.zeros(self.dimension)
            for key in keys:
                superposition += self.memory_traces[key]
            
            # Normalize the superposition
            superposition = superposition / np.linalg.norm(superposition)
            
            logger.info(f"Created superposition of {len(keys)} memory traces")
            return superposition
            
        except Exception as e:
            logger.error(f"Failed to create superposition: {str(e)}")
            return None
    
    def cleanup(self) -> int:
        """
        Clean up the memory by removing noisy or degraded memory traces.
        
        Returns:
            Number of memory traces removed
        """
        try:
            # Identify noisy or degraded memory traces
            keys_to_remove = []
            for key, memory_trace in self.memory_traces.items():
                # Check if memory trace is too noisy
                if np.isnan(memory_trace).any() or np.std(memory_trace) < 0.01:
                    keys_to_remove.append(key)
            
            # Remove identified memory traces
            for key in keys_to_remove:
                del self.memory_traces[key]
            
            # Update capacity used
            if self.memory_traces:
                self.capacity_used = len(self.memory_traces) / self._theoretical_capacity()
            else:
                self.capacity_used = 0.0
            
            logger.info(f"Cleaned up {len(keys_to_remove)} memory traces. New capacity used: {self.capacity_used:.2%}")
            return len(keys_to_remove)
            
        except Exception as e:
            logger.error(f"Failed to clean up memory: {str(e)}")
            return 0
    
    def _generate_key_vector(self, key: str) -> np.ndarray:
        """
        Generate a unique vector for a key.
        
        Args:
            key: The key to generate a vector for
            
        Returns:
            Key vector
        """
        # Use hash of key to seed random number generator
        np.random.seed(hash(key) % 2**32)
        
        # Generate random vector
        key_vector = np.random.normal(0, 1, self.dimension)
        
        # Normalize to unit length
        key_vector = key_vector / np.linalg.norm(key_vector)
        
        return key_vector
    
    def _circular_convolution(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        Perform circular convolution of two vectors.
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Convolved vector
        """
        # Use FFT for efficient computation
        fft_a = np.fft.fft(a)
        fft_b = np.fft.fft(b)
        
        # Element-wise multiplication in frequency domain
        fft_result = fft_a * fft_b
        
        # Inverse FFT to get result in time domain
        result = np.fft.ifft(fft_result).real
        
        return result
    
    def _circular_correlation(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        Perform circular correlation of two vectors.
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Correlated vector
        """
        # Use FFT for efficient computation
        fft_a = np.fft.fft(a)
        fft_b = np.fft.fft(b)
        
        # Complex conjugate of the second vector
        fft_b_conj = np.conjugate(fft_b)
        
        # Element-wise multiplication in frequency domain
        fft_result = fft_a * fft_b_conj
        
        # Inverse FFT to get result in time domain
        result = np.fft.ifft(fft_result).real
        
        return result
    
    def _resize_vector(self, vector: np.ndarray, target_dim: int) -> np.ndarray:
        """
        Resize vector to target dimension.
        
        Args:
            vector: Vector to resize
            target_dim: Target dimension
            
        Returns:
            Resized vector
        """
        current_dim = len(vector)
        
        if current_dim == target_dim:
            return vector
        
        if current_dim > target_dim:
            # Downsample
            return vector[:target_dim]
        else:
            # Upsample with padding
            result = np.zeros(target_dim)
            result[:current_dim] = vector
            return result
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Cosine similarity value between -1 and 1
        """
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0
        
        return np.dot(a, b) / (norm_a * norm_b)
    
    def _theoretical_capacity(self) -> float:
        """
        Calculate theoretical capacity of the memory.
        
        Returns:
            Theoretical number of items that can be stored
        """
        # Theoretical capacity is proportional to vector dimension
        # but with a safety factor to avoid interference
        return self.dimension / 3.0
    
    def get_stats(self) -> Dict:
        """
        Get memory statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        return {
            "dimension": self.dimension,
            "items_stored": len(self.memory_traces),
            "capacity_used": self.capacity_used,
            "theoretical_capacity": self._theoretical_capacity()
        }
