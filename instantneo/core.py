from openai import OpenAI
import os
import json
import inspect
from typing import List, Any, Callable

class InstantNeo:
    def __init__(self, api_key:str, model: str, role_setup: str,
             temperature: float = 0.45,
             max_tokens: int = 150,
             presence_penalty: float = 0.1,
             frequency_penalty: float = 0.1,
             skills: List[Callable[..., Any]] = None,
             stop=None,): 
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
        if python_type is int:
            return "integer"
        elif python_type is str:
            return "string"
        elif python_type is list:
            return "array"
        elif python_type is dict:
            return "object"
        else:
            return str(python_type)

    @staticmethod
    def extract_parameter_descriptions(function):
        doc = function.__doc__
        descriptions = {}
        in_args_section = False
        for line in doc.split('\n'):
            line = line.strip()
            if line.startswith('Args:'):
                in_args_section = True
            elif line.startswith(('Returns:', 'Raises:')):
                in_args_section = False
            elif in_args_section:
                parts = line.split(':')
                if len(parts) > 1:
                    param_name = parts[0].strip()
                    param_description = parts[1].strip()
                    descriptions[param_name] = param_description
        return descriptions

    def set_up_skills(self):
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
                properties[name] = {
                    "type": param_type,
                    "description": description,
                }
                if param.default is param.empty:
                    required.append(name)

            skill = {
                "name": function.__name__,
                "description": f"Description for {function.__name__}",
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
        stop = None,
        presence_penalty: float = None,
        frequency_penalty: float = None,
        return_full_response: bool = False):

        model = model or self.model
        role_setup = role_setup or self.role_setup
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        stop = stop or self.stop
        presence_penalty = presence_penalty or self.presence_penalty
        frequency_penalty = frequency_penalty or self.frequency_penalty

        skills = self.set_up_skills()

        # Preparando los argumentos para openai.ChatCompletion.create
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

        # Si hay habilidades, las agregamos al diccionario
        if skills:
            chat_args["functions"] = skills
            chat_args["function_call"] = "auto"

        try:
            response = self.instance.chat.completions.create(**chat_args)

            # Si return_full_response es True, retornar la respuesta completa
            if return_full_response:
                return response

            # Checar si la respuesta contiene una llamada a función
            function_call = response.choices[0].message.function_call
            if function_call:
                function_name = function_call.name
                arguments_str = function_call.arguments
                arguments_dic = json.loads(arguments_str)

                # Verificar si la función está permitida
                is_valid_function = any(skill["name"] == function_name for skill in skills)
                if is_valid_function:
                    function = self.function_map.get(function_name)
                    if function:
                        # Ejecutar la función con los argumentos desempaquetados
                        result = function(**arguments_dic)
                        return result
                    else:
                        raise ValueError(f'Función no encontrada: {function_name}')
                else:
                    raise ValueError(f'Función no permitida: {function_name}')

            # Si no hay una llamada a función, verificar si hay texto de respuesta
            elif response.choices[0].message.content:
                content = response.choices[0].message.content
                return content

            else:
                raise ValueError('No se encontró contenido ni llamada a función en la respuesta.')

        except Exception as e:
            return str(e)
