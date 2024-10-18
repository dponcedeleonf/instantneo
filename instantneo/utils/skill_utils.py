# skill_utils.py
from typing import Dict, Any

def python_type_to_string(python_type):
    type_map = {
        int: "integer",
        float: "number",
        str: "string",
        bool: "boolean",
        list: "array",
        dict: "object",
        Any: "any",
    }
    return type_map.get(python_type, "string")



def format_tool(skill_info: Dict[str, Any]) -> Dict[str, Any]:
    if 'parameters' not in skill_info:
        raise ValueError(f"Skill metadata for '{skill_info.get('name', 'unknown')}' is missing 'parameters' key.")
    properties = {}
    for name, param in skill_info["parameters"].items():
        param_type = param["type"]
        param_description = param["description"]
        if isinstance(param_type, dict):
            # Tipos complejos como arrays u objetos
            properties[name] = {
                "description": param_description,
                **param_type,
            }
        else:
            properties[name] = {
                "type": param_type,
                "description": param_description,
            }
        # Manejar enums si se especifican
        if 'enum' in param:
            properties[name]['enum'] = param['enum']

    required = [name for name, param in skill_info["parameters"].items() if param.get("default") is None]

    # Construir el tool según el formato esperado por el API de OpenAI
    tool = {
        "type": "function",
        "function": {
            "name": skill_info["name"],
            "description": skill_info["description"],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required if required else [],
            },
        }
    }

    return tool