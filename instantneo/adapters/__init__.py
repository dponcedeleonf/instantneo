"""Módulo de adaptadores para diferentes proveedores de IA.

Este módulo contiene los adaptadores que permiten a InstantNeo
interactuar con diferentes proveedores de modelos de lenguaje.
"""

from .base_adapter import BaseAdapter

__all__ = ['BaseAdapter']

# Intentar importar OpenAIAdapter si está disponible
try:
    from .openai_adapter import OpenAIAdapter
    __all__.append('OpenAIAdapter')
except ImportError:
    OpenAIAdapter = None  # Evita errores si se intenta acceder

# Intentar importar AnthropicAdapter si está disponible
try:
    from .anthropic_adapter import AnthropicAdapter
    __all__.append('AnthropicAdapter')
except ImportError:
    AnthropicAdapter = None

# Intentar importar GroqAdapter si está disponible
try:
    from .groq_adapter import GroqAdapter
    __all__.append('GroqAdapter')
except ImportError:
    GroqAdapter = None
