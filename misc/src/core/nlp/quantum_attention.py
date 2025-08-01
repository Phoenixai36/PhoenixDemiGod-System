#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Quantum Attention Module for Phoenix DemiGod

This module implements quantum-inspired attention mechanisms for natural
language processing tasks, enabling superposition of semantic states.
"""

import logging
import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/quantum_attention.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("QuantumAttention")

class QuantumAttention(nn.Module):
    """
    Quantum-inspired attention mechanism that processes information using
    principles inspired by quantum mechanics.
    
    Attributes:
        embed_dim (int): Embedding dimension
        num_heads (int): Number of attention heads
        dropout (float): Dropout probability
        entanglement (bool): Whether to use entanglement between heads
        superposition (bool): Whether to use superposition of attention states
    """
    
    def __init__(
        self,
        embed_dim: int = 768,
        num_heads: int = 8,
        dropout: float = 0.1,
        entanglement: bool = True,
        superposition: bool = True
    ):
        """
        Initialize the quantum attention module.
        
        Args:
            embed_dim: Embedding dimension
            num_heads: Number of attention heads
            dropout: Dropout probability
            entanglement: Whether to use entanglement between heads
            superposition: Whether to use superposition of attention states
        """
        super().__init__()
        
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.entanglement = entanglement
        self.superposition = superposition
        
        # Ensure head_dim is divisible
        if self.head_dim * num_heads != embed_dim:
            raise ValueError(f"embed_dim ({embed_dim}) must be divisible by num_heads ({num_heads})")
        
        # Linear projections for queries, keys, values
        self.q_proj = nn.Linear(embed_dim, embed_dim)
        self.k_proj = nn.Linear(embed_dim, embed_dim)
        self.v_proj = nn.Linear(embed_dim, embed_dim)
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        
        # Phase encoding for quantum simulation
        self.phase_encoding = nn.Parameter(torch.randn(num_heads, self.head_dim) * 0.02)
        
        # Hadamard transformation (quantum-inspired)
        h = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        
        # Build Hadamard matrix of appropriate size
        n = int(np.log2(self.head_dim))
        if 2**n != self.head_dim:
            # If head_dim is not a power of 2, use the closest power of 2
            n = int(np.ceil(np.log2(self.head_dim)))
            h_matrix = np.zeros((2**n, 2**n))
            h_matrix[:self.head_dim, :self.head_dim] = np.kron(*([h] * n))[:self.head_dim, :self.head_dim]
        else:
            h_matrix = np.kron(*([h] * n))
        
        # Register Hadamard matrix as non-trainable parameter
        self.register_buffer('hadamard', torch.tensor(h_matrix, dtype=torch.float32))
        
        self.dropout = nn.Dropout(dropout)
        
        logger.info(f"Initialized QuantumAttention with {num_heads} heads, dimension {embed_dim}")
    
    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_mask: Optional[torch.Tensor] = None,
        key_padding_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass for quantum attention.
        
        Args:
            query: Query embeddings (batch_size, seq_len_q, embed_dim)
            key: Key embeddings (batch_size, seq_len_k, embed_dim)
            value: Value embeddings (batch_size, seq_len_v, embed_dim)
            attn_mask: Attention mask (seq_len_q, seq_len_k)
            key_padding_mask: Key padding mask (batch_size, seq_len_k)
            
        Returns:
            Tuple of (output, attention weights)
        """
        batch_size, seq_len_q, _ = query.shape
        _, seq_len_k, _ = key.shape
        
        # Linear projections
        q = self.q_proj(query)
        k = self.k_proj(key)
        v = self.v_proj(value)
        
        # Reshape for multi-head attention
        q = q.view(batch_size, seq_len_q, self.num_heads, self.head_dim).transpose(1, 2)
        k = k.view(batch_size, seq_len_k, self.num_heads, self.head_dim).transpose(1, 2)
        v = v.view(batch_size, -1, self.num_heads, self.head_dim).transpose(1, 2)
        
        # Apply quantum transformations
        if self.superposition:
            q = self._apply_superposition(q)
            k = self._apply_superposition(k)
        
        # Apply phase encoding (quantum-inspired)
        q = q * torch.exp(1j * self.phase_encoding.unsqueeze(1).unsqueeze(0))
        k = k * torch.exp(-1j * self.phase_encoding.unsqueeze(1).unsqueeze(0))
        
        # Take real part after phase encoding
        q = torch.real(q)
        k = torch.real(k)
        
        # Calculate attention scores
        # Scale dot product attention
        attn_weights = torch.matmul(q, k.transpose(2, 3)) / math.sqrt(self.head_dim)
        
        # Apply attention mask if provided
        if attn_mask is not None:
            attn_weights = attn_weights + attn_mask.unsqueeze(0).unsqueeze(0)
        
        # Apply key padding mask if provided
        if key_padding_mask is not None:
            attn_weights = attn_weights.masked_fill(
                key_padding_mask.unsqueeze(1).unsqueeze(2),
                float('-inf')
            )
        
        # Apply softmax and dropout
        attn_probs = F.softmax(attn_weights, dim=-1)
        attn_probs = self.dropout(attn_probs)
        
        # Apply entanglement between heads if enabled
        if self.entanglement:
            attn_probs = self._apply_entanglement(attn_probs)
        
        # Apply attention to values
        context = torch.matmul(attn_probs, v)
        
        # Reshape and project output
        context = context.transpose(1, 2).contiguous().view(batch_size, seq_len_q, self.embed_dim)
        output = self.out_proj(context)
        
        return output, attn_probs
    
    def _apply_superposition(self, x: torch.Tensor) -> torch.Tensor:
        """
        Apply quantum-inspired superposition using Hadamard transformation.
        
        Args:
            x: Input tensor (batch_size, num_heads, seq_len, head_dim)
            
        Returns:
            Tensor with applied superposition
        """
        batch_size, num_heads, seq_len, _ = x.shape
        
        # Reshape for hadamard multiplication
        x_reshaped = x.view(-1, self.head_dim)
        
        # Apply Hadamard transformation
        x_superposition = torch.matmul(x_reshaped, self.hadamard.to(x.device))
        
        # Reshape back
        return x_superposition.view(batch_size, num_heads, seq_len, self.head_dim)
    
    def _apply_entanglement(self, attn_probs: torch.Tensor) -> torch.Tensor:
        """
        Apply quantum-inspired entanglement between attention heads.
        
        Args:
            attn_probs: Attention probabilities (batch_size, num_heads, seq_len_q, seq_len_k)
            
        Returns:
            Entangled attention probabilities
        """
        batch_size, num_heads, seq_len_q, seq_len_k = attn_probs.shape
        
        # Create entanglement mask (randomly entangle pairs of heads)
        if not hasattr(self, 'entanglement_mask') or self.training:
            # During training, create a new entanglement mask each time
            entanglement_mask = torch.eye(num_heads, device=attn_probs.device)
            # Randomly pair heads for entanglement
            perm = torch.randperm(num_heads)
            for i in range(0, num_heads - 1, 2):
                h1, h2 = perm[i], perm[i + 1]
                # Create entanglement between these heads
                entanglement_mask[h1, h2] = 0.2
                entanglement_mask[h2, h1] = 0.2
            
            if self.training:
                self.entanglement_mask = entanglement_mask
            else:
                # During evaluation, use a fixed entanglement mask
                self.register_buffer('entanglement_mask', entanglement_mask)
        
        # Apply entanglement by mixing attention probabilities between heads
        entangled_probs = torch.einsum('bhqk,hg->bgqk', attn_probs, self.entanglement_mask)
        
        return entangled_probs


class QuantumEnhancedTransformerEncoder(nn.Module):
    """
    Transformer encoder with quantum-enhanced attention mechanism.
    
    Attributes:
        embed_dim (int): Embedding dimension
        num_heads (int): Number of attention heads
        feedforward_dim (int): Dimension of feedforward network
        dropout (float): Dropout probability
        num_layers (int): Number of encoder layers
        quantum_layers (List[int]): Indices of layers using quantum attention
    """
    
    def __init__(
        self,
        embed_dim: int = 768,
        num_heads: int = 8,
        feedforward_dim: int = 2048,
        dropout: float = 0.1,
        num_layers: int = 6,
        quantum_layers: List[int] = None
    ):
        """
        Initialize the quantum-enhanced transformer encoder.
        
        Args:
            embed_dim: Embedding dimension
            num_heads: Number of attention heads
            feedforward_dim: Dimension of feedforward network
            dropout: Dropout probability
            num_layers: Number of encoder layers
            quantum_layers: Indices of layers using quantum attention (default: all layers)
        """
        super().__init__()
        
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        
        # Default to all layers using quantum attention if not specified
        if quantum_layers is None:
            quantum_layers = list(range(num_layers))
        self.quantum_layers = quantum_layers
        
        # Build encoder layers
        self.layers = nn.ModuleList()
        for i in range(num_layers):
            if i in quantum_layers:
                attn = QuantumAttention(embed_dim, num_heads, dropout)
            else:
                attn = nn.MultiheadAttention(embed_dim, num_heads, dropout)
            
            # Create encoder layer
            layer = EncoderLayer(
                attn=attn,
                embed_dim=embed_dim,
                feedforward_dim=feedforward_dim,
                dropout=dropout,
                is_quantum=i in quantum_layers
            )
            self.layers.append(layer)
        
        # Layer normalization
        self.layer_norm = nn.LayerNorm(embed_dim)
        
        logger.info(f"Initialized QuantumEnhancedTransformerEncoder with {num_layers} layers")
        logger.info(f"Quantum attention in layers: {quantum_layers}")
    
    def forward(
        self,
        src: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        src_key_padding_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass for quantum-enhanced transformer encoder.
        
        Args:
            src: Source embeddings (batch_size, seq_len, embed_dim)
            mask: Attention mask (seq_len, seq_len)
            src_key_padding_mask: Source key padding mask (batch_size, seq_len)
            
        Returns:
            Encoded representation
        """
        output = src
        
        # Process through each encoder layer
        for i, layer in enumerate(self.layers):
            output = layer(
                output,
                mask=mask,
                src_key_padding_mask=src_key_padding_mask
            )
        
        # Apply final layer normalization
        output = self.layer_norm(output)
        
        return output


class EncoderLayer(nn.Module):
    """
    Transformer encoder layer with support for both regular and quantum attention.
    
    Attributes:
        attn (nn.Module): Attention module (regular or quantum)
        embed_dim (int): Embedding dimension
        feedforward_dim (int): Dimension of feedforward network
        dropout (float): Dropout probability
        is_quantum (bool): Whether this layer uses quantum attention
    """
    
    def __init__(
        self,
        attn: nn.Module,
        embed_dim: int = 768,
        feedforward_dim: int = 2048,
        dropout: float = 0.1,
        is_quantum: bool = True
    ):
        """
        Initialize the encoder layer.
        
        Args:
            attn: Attention module (regular or quantum)
            embed_dim: Embedding dimension
            feedforward_dim: Dimension of feedforward network
            dropout: Dropout probability
            is_quantum: Whether this layer uses quantum attention
        """
        super().__init__()
        
        self.attn = attn
        self.is_quantum = is_quantum
        
        # Feed-forward network
        self.linear1 = nn.Linear(embed_dim, feedforward_dim)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(feedforward_dim, embed_dim)
        
        # Layer normalization
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        
        # Dropout
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
    
    def forward(
        self,
        src: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
        src_key_padding_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass for encoder layer.
        
        Args:
            src: Source embeddings (batch_size, seq_len, embed_dim)
            mask: Attention mask (seq_len, seq_len)
            src_key_padding_mask: Source key padding mask (batch_size, seq_len)
            
        Returns:
            Encoded representation
        """
        # Apply attention
        if self.is_quantum:
            # Quantum attention expects (batch_size, seq_len, embed_dim)
            attn_output, _ = self.attn(
                query=src,
                key=src,
                value=src,
                attn_mask=mask,
                key_padding_mask=src_key_padding_mask
            )
        else:
            # Regular MultiheadAttention expects (seq_len, batch_size, embed_dim)
            src_transposed = src.transpose(0, 1)
            attn_output, _ = self.attn(
                query=src_transposed,
                key=src_transposed,
                value=src_transposed,
                attn_mask=mask,
                key_padding_mask=src_key_padding_mask
            )
            # Convert back to (batch_size, seq_len, embed_dim)
            attn_output = attn_output.transpose(0, 1)
        
        # Add & Norm (first residual connection)
        src = src + self.dropout1(attn_output)
        src = self.norm1(src)
        
        # Feed Forward
        ff_output = self.linear2(self.dropout(F.relu(self.linear1(src))))
        
        # Add & Norm (second residual connection)
        src = src + self.dropout2(ff_output)
        src = self.norm2(src)
        
        return src


if __name__ == "__main__":
    # Example usage
    batch_size = 4
    seq_len = 16
    embed_dim = 256
    num_heads = 8
    
    # Create random input
    x = torch.rand(batch_size, seq_len, embed_dim)
    
    # Initialize quantum attention module
    quantum_attn = QuantumAttention(embed_dim, num_heads)
    
    # Forward pass
    output, attn_weights = quantum_attn(x, x, x)
    
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Attention weights shape: {attn_weights.shape}")
    
    # Create a quantum-enhanced transformer encoder
    encoder = QuantumEnhancedTransformerEncoder(
        embed_dim=embed_dim,
        num_heads=num_heads,
        num_layers=3,
        quantum_layers=[0, 2]
    )
    
    # Forward pass through encoder
    encoded = encoder(x)
    
    print(f"Encoded output shape: {encoded.shape}")
