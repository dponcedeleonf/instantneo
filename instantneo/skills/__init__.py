"""Módulo de skills para InstantNeo.

Este módulo contiene las herramientas para definir y gestionar skills
que pueden ser utilizadas por InstantNeo.
"""

from .skill_manager import SkillManager
from .skill_decorators import skill
from .skill_manager_operations import SkillManagerOperations

__all__ = ['SkillManager', 'skill', 'SkillManagerOperations']