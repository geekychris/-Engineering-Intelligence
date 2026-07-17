"""Synthetic engineering telemetry generator.

Emits realistic-shaped events for pull requests, reviews, CI runs,
deployments, incidents, actors, teams, and Engineering Changes.
"""
from .generator import Config, Generator

__version__ = "0.1.0"
__all__ = ["Config", "Generator"]
