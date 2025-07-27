"""
Behave AI Orchestration Plugin

A comprehensive plugin for testing AI framework coordination and business logic
orchestration using natural language BDD scenarios.

This plugin provides:
- Step definitions for common AI framework interactions
- Business logic testing patterns
- Cross-framework coordination testing
- Template scenarios for common business processes
"""

__version__ = '0.1.0'
__author__ = 'Business Logic Orchestration Team'

from .steps import *
from .fixtures import AITestFixtures
from .templates import TemplateGenerator

__all__ = [
    'AITestFixtures',
    'TemplateGenerator',
]
