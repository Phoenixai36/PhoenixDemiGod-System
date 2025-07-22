"""
Cellular Communication Protocol (CCP) package.

This package implements a specialized communication framework for the PHOENIXxHYDRA
system's cellular architecture, enabling efficient, secure, and resilient
communication between digital cells across the P2P mesh network.
"""

from .core import CCPCore, CCPConfig, MessageOptions
from .data_models import (
    Message, MessageId, MessagePriority, MessageSensitivity,
    EncryptedMessage, EncryptionLevel, ResonanceParameters, Route,
    NetworkConditions, Session
)

__all__ = [
    'CCPCore',
    'CCPConfig',
    'MessageOptions',
    'Message',
    'MessageId',
    'MessagePriority',
    'MessageSensitivity',
    'EncryptedMessage',
    'EncryptionLevel',
    'ResonanceParameters',
    'Route',
    'NetworkConditions',
    'Session',
]
