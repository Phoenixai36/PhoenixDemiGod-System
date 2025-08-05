"""
Phoenix Hydra Chatbot Agent

A gamified chatbot interface that serves as an intermediary between
the Phoenix Hydra system and users, featuring adult and nerdy animations.
"""

from .animation_controller import AnimationController
from .chatbot_agent import ChatbotAgent
from .gamification_system import GamificationSystem
from .personality_engine import PersonalityEngine

__all__ = [
    'ChatbotAgent',
    'PersonalityEngine', 
    'GamificationSystem',
    'AnimationController'
]