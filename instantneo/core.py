from openai import OpenAI
import json
import inspect
import typing
from typing import List, Any, Callable

class InstantNeo:
    def __init__(self, api_key: str, model: str, role_setup: str,
                 temperature: float = 0.45,
                 max_tokens: int = 150,
                 presence_penalty: float = 0.1,
                 frequency_penalty: float = 0.1,
                 skills: List[Callable[..., Any]] = None,
                 stop=None,):
        # Inicialización de la instancia con configuraciones y habilidades.
        self.skills = skills if skills is not None else []
        self.function_map = {f.__name__: f for f in self.skills}
        self.model = model
        self.role_setup = role_setup
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.stop = stop
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.instance = OpenAI(api_key=api_key)

    @staticmethod
    def python_type_to_string(python_type):
        # Convierte tipos de Python a su representación como tipos de datos JSON.
        if python_type in [int, float]:
            return "number"
        elif python_type is str:
            return "string"
        elif python_type in [list, tuple]:
            return "array"
        elif python_type is dict:
            return "object"
        elif python_type is bool:
            return "boolean"
        elif python_type is type(None):
            return "null"
        else:
            return "unknown"
    
    @staticmethod
    def serialize_argument(arg):
        # Convierte argumentos complejos (listas, diccionarios) a JSON para su procesamiento.
        if isinstance(arg, (list, dict)):
            return json.dumps(arg)
        return arg

    @staticmethod
    def extract_parameter_descriptions(function):
        # Extrae descripciones de los parámetros de las funciones a partir de sus docstrings.
        if function.__doc__ is None:
            raise ValueError(f"La función '{function.__name__}' no tiene un docstring.")

        doc = function.__doc__
        descriptions = {}
        in_args_section = False
        for line in doc.split('\n'):
            line = line.strip()
            if line.startswith('Args:'):
                in_args_section = True
            elif line.startswith(('Returns:', 'Raises:')):
                in_args_section = False
            elif in_args_section and line:
                parts = line.partition(':')
                if len(parts) != 3 or not parts[0].strip():
                    raise ValueError(f"Formato de docstring incorrecto en la función '{function.__name__}'.")
                param_name, _, param_description = parts
                descriptions[param_name.strip()] = param_description.strip()
        return descriptions


    def set_up_skills(self):
        # Configura las habilidades (funciones) para su uso en la instancia.
        skills = []
        if not self.skills:
            return skills
        for function in self.skills:
            params_info = inspect.signature(function).parameters
            param_descriptions = self.extract_parameter_descriptions(function)
            properties = {}
            required = []
            for name, param in params_info.items():
                param_type = self.python_type_to_string(param.annotation)
                description = param_descriptions.get(name, "")
                # Procesamiento específico para tipos de datos
                # Aquí excluimos diccionarios, pues no los admite el API de OpenAI
                if isinstance(param.annotation, typing._GenericAlias):
                    if param.annotation.__origin__ in [list, typing.List]:
                        if param.annotation.__args__:
                            element_type = self.python_type_to_string(param.annotation.__args__[0])
                        else:
                            element_type = "unknown"
                        item_schema = {"type": element_type}
                        properties[name] = {
                            "type": "array",
                            "items": item_schema,
                            "description": description,
                        }
                    # Excluyendo el manejo de diccionarios.
                    elif param.annotation.__origin__ in [dict, typing.Dict]:
                        raise TypeError("Las funciones con diccionarios como argumentos no son soportadas.")
                else:
                    properties[name] = {
                        "type": param_type,
                        "description": description,
                    }

                if param.default is param.empty:
                    required.append(name)

                skill = {
                    "name": function.__name__,
                    "description": f"Descripción de {function.__name__}",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                }
                skills.append(skill)
        return skills

    def run(self,
            prompt: str,
            model: str = None,
            role_setup: str = None,
            temperature: float = None,
            max_tokens: int = None,
            stop=None,
            presence_penalty: float = None,
            frequency_penalty: float = None,
            return_full_response: bool = False):
        
        # Configuración y ejecución de la solicitud al modelo.
        
        model = model or self.model
        role_setup = role_setup or self.role_setup
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        stop = stop or self.stop
        presence_penalty = presence_penalty or self.presence_penalty
        frequency_penalty = frequency_penalty or self.frequency_penalty

        # Configurar habilidades para la instancia
        skills = self.set_up_skills()

        # Solicitud al modelo de OpenAI. Preparar argumentos para la solicitud
        chat_args = {
            "model": model,
            "messages": [
                {"role": "system", "content": role_setup},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stop": stop,
            "presence_penalty": presence_penalty,
            "frequency_penalty": frequency_penalty
        }
        # # Solicitud al modelo de OpenAI. Incluir habilidades si están disponibles
        if skills:
            chat_args["functions"] = skills
            chat_args["function_call"] = "auto"

        try:
            # Realizar la solicitud al modelo de OpenAI
            response = self.instance.chat.completions.create(**chat_args)
            # Retornar respuesta completa si se solicita.
            # La respuesta completa es un JSON que incluye la respuesta y metadata
            if return_full_response:
                return response
            # Procesar la respuesta para ver si incluye la llamada a una función como respuesta del modelo
            function_call = response.choices[0].message.function_call
            if function_call:
                # Si el modelo responde con una llamada a una función, se extrae la información de la función
                function_name = function_call.name
                arguments_str = function_call.arguments
                arguments_dic = json.loads(arguments_str)
                #Se ejecuta directamente la función
                is_valid_function = any(skill["name"] == function_name for skill in skills)
                if is_valid_function:
                    function = self.function_map.get(function_name)
                    if function:
                        result = function(**arguments_dic)
                        return result
                    else:
                        raise ValueError(f'Función no encontrada: {function_name}')
                else:
                    raise ValueError(f'Función no permitida: {function_name}')
            # Si no se llama a una función, retorna el contenido de la respuesta
            elif response.choices[0].message.content:
                return response.choices[0].message.content

            else:
                raise ValueError('No se encontró contenido ni llamada a función en la respuesta.')

        except Exception as e:
            return str(e)
