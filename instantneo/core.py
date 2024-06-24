from openai import OpenAI
import json
from datetime import datetime
import inspect
import typing
from typing import List, Tuple, Dict, Any, Callable
import time
import os

class InstantNeo:
    def __init__(self, api_key: str, model: str, role_setup: str,
                 temperature: float = 0.45,
                 max_tokens: int = 150,
                 presence_penalty: float = 0.1,
                 frequency_penalty: float = 0.1,
                 skills: List[Callable[..., Any]] = None,
                 stop=None,
                 provider=None,
                 stream = False,
                 log: bool = False):
        self.api_key = api_key
        self.model = model
        self.role_setup = role_setup
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.skills = skills if skills is not None else []
        self.function_map = {f.__name__: f for f in self.skills}
        self.stop = stop
        self.provider = provider
        self.stream = stream
        self.log = log  # Nuevo parámetro de log

        if not provider:
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

    def save_log(self, response, prompt, response_time):

        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "prompt": prompt,
            "response": response.to_dict(),
            "metadata": {
                "temperature": getattr(self, 'temperature', None),
                "max_tokens": getattr(self, 'max_tokens', None),
                "role_setup": getattr(self, 'role_setup', None),
            },
            "response_time": response_time
        }

        log_dir = "LOG"
        log_file_path = os.path.join(log_dir, "responses_log.json")

        # Asegurarse de que el directorio exista
        os.makedirs(log_dir, exist_ok=True)

        try:
            # Leer el contenido existente del archivo
            if os.path.exists(log_file_path):
                with open(log_file_path, "r") as log_file:
                    try:
                        logs = json.load(log_file)
                    except json.JSONDecodeError:
                        logs = []
            else:
                logs = []

            # Agregar la nueva entrada
            logs.append(log_entry)

            # Escribir todo de nuevo en el archivo
            with open(log_file_path, "w") as log_file:
                json.dump(logs, log_file, indent=4)
        except IOError as e:
            print(f"Error al escribir en el archivo de log: {e}")
        except json.JSONDecodeError as e:
            print(f"Error al convertir el log a JSON: {e}")

    def save_error_log(self, error, context):
        error_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": {
                "type": type(error).__name__,
                "message": str(error),
            },
            "context": context
        }
        with open("error_log.json", "a") as log_file:
            log_file.write(json.dumps(error_entry, indent=4) + "\n")


    def run(self, prompt: str, model: str = None, role_setup: str = None, 
            temperature: float = None, max_tokens: int = None, stop=None, 
            presence_penalty: float = None, frequency_penalty: float = None, 
            return_full_response: bool = False, stream=False, img: str=None):
        start_time = time.time()
        if self.provider:
            return self.provider.run(
                prompt=prompt,
                api_key=self.api_key,
                model=model or self.model,
                role_setup=role_setup or self.role_setup,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                stop=stop,
                presence_penalty=presence_penalty or self.presence_penalty,
                frequency_penalty=frequency_penalty or self.frequency_penalty,
                return_full_response=return_full_response,
                stream=stream or self.stream,
                img=img
            )
        else:
            model = model or self.model
            role_setup = role_setup or self.role_setup
            temperature = temperature or self.temperature
            max_tokens = max_tokens or self.max_tokens
            stop = stop or self.stop
            presence_penalty = presence_penalty or self.presence_penalty
            frequency_penalty = frequency_penalty or self.frequency_penalty

            # Configurar habilidades para la instancia
            skills = self.set_up_skills()

            # Preparar argumentos para la solicitud a OpenAI
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

            if skills:
                chat_args["functions"] = skills
                chat_args["function_call"] = "auto"

            try:
                response = self.instance.chat.completions.create(**chat_args)
                response_time = time.time() - start_time
                if return_full_response:
                    result = response
                else:
                    function_call = response.choices[0].message.function_call
                    if function_call:
                        function_name = function_call.name
                        arguments_str = function_call.arguments
                        arguments_dic = json.loads(arguments_str)
                        is_valid_function = any(skill["name"] == function_name for skill in skills)
                        if is_valid_function:
                            function = self.function_map.get(function_name)
                            if function:
                                result = function(**arguments_dic)
                            else:
                                raise ValueError(f'Function not found: {function_name}')
                        else:
                            raise ValueError(f'Function not allowed: {function_name}')
                    elif response.choices[0].message.content:
                        result = response.choices[0].message.content
                    else:
                        raise ValueError('No content or function call found in the response.')

                # Guardar la respuesta en un archivo de texto si `log` está habilitado
                if self.log:
                    self.save_log(response,prompt,response_time)

                return result
            except Exception as e:
                context = {
                    "function": "run",
                    "parameters": {
                        "prompt": prompt,
                        "model": model or self.model,
                    }
                }
                self.save_error_log(e, context)
                return str(e)

