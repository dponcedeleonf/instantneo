# skill_manager.py

from typing import Callable, Dict, Any, List
import inspect

class SkillManager:
    def __init__(self):
        self.skills: Dict[str, Callable] = {}
        self.skill_metadata: Dict[str, Dict[str, Any]] = {}

    def add_skill(self, skill: Callable):
        skill_name = skill.__name__
        if skill_name in self.skills:
            raise ValueError(f"Skill '{skill_name}' already exists.")
        self.skills[skill_name] = skill
        metadata = getattr(skill, '_skill_metadata', None)
        if metadata:
            # Convert metadata to dictionary if it's an object
            if hasattr(metadata, '__dict__'):
                metadata = metadata.__dict__
            self.skill_metadata[skill_name] = metadata
        else:
            # If no metadata is provided, generate basic metadata
            self.skill_metadata[skill_name] = self._generate_metadata(skill)

    def remove_skill(self, skill_name: str):
        if skill_name in self.skills:
            del self.skills[skill_name]
            del self.skill_metadata[skill_name]
        else:
            raise ValueError(f"Skill '{skill_name}' not found.")

    def get_skill(self, skill_name: str) -> Callable:
        return self.skills.get(skill_name)

    def get_skill_info(self, skill_name: str) -> Dict[str, Any]:
        return self.skill_metadata.get(skill_name, {})

    def list_skills(self) -> List[str]:
        return list(self.skills.keys())

    def _generate_metadata(self, skill: Callable) -> Dict[str, Any]:
        sig = inspect.signature(skill)
        parameters = {}
        required = []
        for name, param in sig.parameters.items():
            param_type = self._get_type_str(param.annotation)
            param_desc = "No description provided"
            param_default = None

            if param.default is not inspect.Parameter.empty:
                if isinstance(param.default, Param):
                    param_desc = param.default.description
                    param_default = param.default.default
                else:
                    param_default = param.default
            else:
                required.append(name)

            parameters[name] = {
                'type': param_type,
                'description': param_desc,
            }
            if param_default is not None:
                parameters[name]['default'] = param_default

        return_type = self._get_type_str(sig.return_annotation)
        return_info = {
            'type': return_type,
            'description': 'No description provided',
        }

        metadata = {
            'name': skill.__name__,
            'description': skill.__doc__ or "No description provided",
            'parameters': parameters,
            'return_info': return_info,
        }
        return metadata

    def _get_type_str(self, annotation):
        type_map = {
            int: "integer",
            float: "number",
            str: "string",
            bool: "boolean",
            list: "array",
            dict: "object",
            Any: "any",
        }
        if annotation is inspect.Parameter.empty:
            return 'any'
        if isinstance(annotation, str):
            return annotation
        if annotation is Any:
            return 'any'
        origin = getattr(annotation, '__origin__', None)
        if origin is not None:
            if origin is list or origin is List:
                args = getattr(annotation, '__args__', [])
                if args:
                    return {
                        "type": "array",
                        "items": {"type": self._get_type_str(args[0])}
                    }
                else:
                    return {"type": "array", "items": {"type": "any"}}
            elif origin is dict or origin is Dict:
                args = getattr(annotation, '__args__', [])
                if len(args) == 2:
                    return {
                        "type": "object",
                        "additionalProperties": {"type": self._get_type_str(args[1])}
                    }
                else:
                    return {"type": "object"}
            else:
                return 'object'
        else:
            return type_map.get(annotation, 'string')

# Assuming Param class is defined in skill_decorators.py
class Param:
    def __init__(self, description: str, default: Any = inspect.Parameter.empty, enum: List[Any] = None):
        self.description = description
        self.default = default
        self.enum = enum