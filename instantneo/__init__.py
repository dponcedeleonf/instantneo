"""Paquete InstantNeo

Este paquete provee la interfaz principal para acceder a las funcionalidades de InstantNeo.

Estructura de importación:
- instantneo.InstantNeo: Clase principal que encapsula la lógica de InstantNeo.
- instantneo.Skills: Contiene utilidades relacionadas con las skills.
    - instantneo.Skills.skill: Decorador para definir skills.
    - instantneo.Skills.SkillManager: Administrador de skills.
    - instantneo.Skills.SkillManagerOperations: Operaciones adicionales para gestionar skills y sus managers.
- instantneo.Adapters: Contiene los adaptadores para los diferentes proveedores.
    - instantneo.Adapters.Groq: Adaptador para Groq.
    - instantneo.Adapters.Openai: Adaptador para OpenAI.
    - instantneo.Adapters.Anthropic: Adaptador para Anthropic.
"""

# Importación de la clase principal
from .core import InstantNeo

# Importaciones para Skills
from .skills.skill_decorators import skill
from .skills.skill_manager import SkillManager
from .skills.skill_manager_operations import SkillManagerOperations

# Importaciones para Adapters - Usando importación condicional
# Inicializar variables para evitar errores de referencia
GroqAdapter = None
OpenAIAdapter = None
AnthropicAdapter = None

# Intentar importar OpenAIAdapter si está disponible
try:
    from .adapters.openai_adapter import OpenAIAdapter
    print("OpenAIAdapter importado correctamente")
except ImportError:
    print("No se pudo importar OpenAIAdapter - el paquete openai no está instalado")

# Intentar importar AnthropicAdapter si está disponible
try:
    from .adapters.anthropic_adapter import AnthropicAdapter
    print("AnthropicAdapter importado correctamente")
except ImportError:
    print("No se pudo importar AnthropicAdapter - el paquete anthropic no está instalado")

# Intentar importar GroqAdapter si está disponible
try:
    from .adapters.groq_adapter import GroqAdapter
    print("GroqAdapter importado correctamente")
except ImportError:
    print("No se pudo importar GroqAdapter - el paquete groq no está instalado")

# Namespace para Skills
class Skills:
    """Skills toolkit"""
    skill = skill
    SkillManager = SkillManager
    SkillManagerOperations = SkillManagerOperations

# Namespace para Adapters
class Adapters:
    """Adapters for different providers"""
    Groq = GroqAdapter
    Openai = OpenAIAdapter
    Anthropic = AnthropicAdapter

# Definir qué se exporta
__all__ = ["InstantNeo", "Skills", "Adapters"]
