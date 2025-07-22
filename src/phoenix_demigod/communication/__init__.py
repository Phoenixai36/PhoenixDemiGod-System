"""
Communication layer for the Phoenix DemiGod system.

This module handles distributed communication, synchronization,
and coordination between multiple system instances.
"""

from .layer import CommunicationLayer
from .messaging import MessageQueue, MessageBroker
from .synchronization import DistributedLock, ConflictResolver

__all__ = [
    "CommunicationLayer",
    "MessageQueue",
    "MessageBroker", 
    "DistributedLock",
    "ConflictResolver"
]