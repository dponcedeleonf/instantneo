# skill_decorators.py

from typing import Any, List, Optional, Dict, Union
import inspect
from functools import wraps

class Param:
    def __init__(self, description: str, default: Any = inspect.Parameter.empty, enum: List[Any] = None):
        self.description = description
        self.default = default
        self.enum = enum

def skill(
    description: str,
    category: Optional[str] = None,
    tags: List[str] = None,
    version: str = "1.0.0",
    author: Optional[str] = None,
):
    def decorator(func):
        sig = inspect.signature(func)
        parameters = {}
        required = []
        for name, param in sig.parameters.items():
            param_type = get_type_str(param.annotation)
            param_desc = "No description provided"
            param_default = None
            param_enum = None

            if isinstance(param.default, Param):
                param_desc = param.default.description
                param_default = param.default.default
                param_enum = param.default.enum
            elif param.default is not inspect.Parameter.empty:
                param_default = param.default
            else:
                required.append(name)

            param_schema = {
                'type': param_type,
                'description': param_desc,
            }
            if param_default is not inspect.Parameter.empty and param_default is not None:
                param_schema['default'] = param_default
            if param_enum is not None:
                param_schema['enum'] = param_enum

            parameters[name] = param_schema

        return_type = get_type_str(sig.return_annotation)
        return_info = {
            'type': return_type,
            'description': 'No description provided',
        }

        metadata = {
            'name': func.__name__,
            'description': description,
            'parameters': parameters,
            'return_info': return_info,
            'category': category,
            'tags': tags,
            'version': version,
            'author': author,
        }

        func._skill_metadata = metadata

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper
    return decorator

def get_type_str(annotation):
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
    if annotation in type_map:
        return type_map[annotation]
    elif hasattr(annotation, '__origin__'):
        origin = annotation.__origin__
        args = getattr(annotation, '__args__', [])
        if origin is Union:
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return get_type_str(non_none_args[0])
            else:
                return {"oneOf": [get_type_str(arg) for arg in non_none_args]}
        elif origin is list or origin is List:
            return {
                "type": "array",
                "items": {"type": get_type_str(args[0]) if args else "any"}
            }
        elif origin is dict or origin is Dict:
            return {
                "type": "object",
                "additionalProperties": {"type": get_type_str(args[1]) if len(args) > 1 else "any"}
            }
        else:
            return 'object'
    elif isinstance(annotation, type):
        # Handle subclasses of built-in types
        for base_type, json_type in type_map.items():
            if issubclass(annotation, base_type):
                return json_type
    return 'string'  # Default to 'string' if type is unrecognized
