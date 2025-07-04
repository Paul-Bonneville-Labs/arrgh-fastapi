"""
Arrgh! Aggregated Research Repository - Newsletter Processing System

This package contains the core components for processing newsletter content
and building a knowledge graph from extracted entities and facts.
"""

__version__ = "0.1.0"
__author__ = "Paul Bonneville Labs"
__description__ = "Intelligent newsletter processing and knowledge graph construction"

from .config import get_settings, get_config

__all__ = ["get_settings", "get_config"]