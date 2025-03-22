import json  # Import json module
from anthropic import Anthropic
from typing import Dict, Any, Generator
from instantneo.adapters.base_adapter import BaseAdapter

from types import SimpleNamespace  # Import SimpleNamespace

class ToolCall:
    def __init__(self, name, arguments):
        self.type = 'function'  # Necesario para InstantNeo
        # JSON-encode the arguments dictionary
        arguments_json = json.dumps(arguments)
        # Use SimpleNamespace to create an object with attributes
        self.function = SimpleNamespace(name=name, arguments=arguments_json)

    def __repr__(self):
        return f"ToolCall(type={self.type}, function={self.function})"

class Response:
    def __init__(self, choices, usage=None):
        self.choices = choices
        self.usage = usage  # Nuevo atributo para almacenar información de uso

    def __repr__(self):
        return f"Response(choices={self.choices}, usage={self.usage})"

class Choice:
    def __init__(self, message, finish_reason=None):
        self.message = message
        self.finish_reason = finish_reason

    def __repr__(self):
        return f"Choice(message={self.message}, finish_reason={self.finish_reason})"

class Message:
    def __init__(self, content='', function_call=None, tool_calls=None):
        self.content = content
        self.function_call = function_call
        self.tool_calls = tool_calls or []

    def __repr__(self):
        return f"Message(content={self.content}, function_call={self.function_call}, tool_calls={self.tool_calls})"

class AnthropicAdapter(BaseAdapter):
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def create_chat_completion(self, **kwargs) -> Response:
        cleaned_kwargs = self._clean_kwargs(kwargs)
        # print("Parámetros limpiados:", cleaned_kwargs)

        try:
            response = self.client.messages.create(**cleaned_kwargs )
            # Convertir la respuesta al formato que InstantNeo espera
            assistant_choice = self._convert_response_to_instantneo_format(response)
            
            # Intentar obtener la información de uso
            usage = getattr(response, 'usage', None)
            if usage is None:
                # Si no existe 'usage', revisar si está en 'metadata' o en otro lugar
                usage = getattr(response, 'metadata', {}).get('usage', None)

            # Crear y retornar el objeto Response con la información de uso
            return Response(choices=[assistant_choice], usage=usage)
        except Exception as e:
            raise RuntimeError(f"Error en la API de Anthropic: {str(e)}")

    def create_streaming_chat_completion(self, **kwargs) -> Generator[str, None, None]:
        cleaned_kwargs = self._clean_kwargs(kwargs)

        try:
            with self.client.messages.stream(**cleaned_kwargs) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise RuntimeError(f"Error in Anthropic API: {str(e)}")

    def supports_images(self) -> bool:
        return True  # Anthropic supports images starting from Claude 3 models

    def _convert_response_to_instantneo_format(self, response) -> Choice:
        # print("response: ",response)
        message_content = ''
        function_call = None
        tool_calls = []

        for block in response.content:
            if block.type == 'text':
                message_content += block.text
            elif block.type == 'tool_use':
                # Create a ToolCall instance with the expected structure
                function_call = ToolCall(name=block.name, arguments=block.input)
                tool_calls.append(function_call)

        # Create a Message instance
        message = Message(
            content=message_content if message_content else None,
            function_call=function_call,
            tool_calls=tool_calls
        )

        # Create and return a Choice instance
        return Choice(
            message=message,
            finish_reason=response.stop_reason
        )

    def _clean_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        cleaned_kwargs = {k: v for k, v in kwargs.items() if v is not None}
        
        # Remover 'stream' de los kwargs si está presente
        cleaned_kwargs.pop('stream', None)

        # Manejar el parámetro 'system'
        system = cleaned_kwargs.pop('system', None)
        if system:
            if isinstance(system, list):
                system = ''.join(system)
            elif not isinstance(system, str):
                raise ValueError("El parámetro 'system' debe ser una cadena o una lista de caracteres")
            cleaned_kwargs['system'] = system

        # Manejar el parámetro 'messages'
        if 'messages' in cleaned_kwargs:
            new_messages = []
            for message in cleaned_kwargs['messages']:
                if message['role'] == 'system':
                    # Mover el contenido del mensaje 'system' al parámetro 'system' de nivel superior
                    if 'system' not in cleaned_kwargs:
                        cleaned_kwargs['system'] = message['content']
                    else:
                        cleaned_kwargs['system'] += "\n" + message['content']
                else:
                    content = message['content']
                    if isinstance(content, list):
                        # Si el contenido es una lista, convertirlo a una cadena
                        content = ' '.join(str(item) for item in content)
                    elif isinstance(content, dict):
                        # Si el contenido es un diccionario, dejarlo como está
                        pass
                    else:
                        # Si es una cadena u otro tipo, convertirlo a cadena
                        content = str(content)
                    
                    new_messages.append({**message, 'content': content})
            
            cleaned_kwargs['messages'] = new_messages

        # Manejar el parámetro 'tools'
        if 'tools' in cleaned_kwargs:
            tools = cleaned_kwargs['tools']
            cleaned_tools = []
            for tool in tools:
                if 'function' in tool:
                    function = tool['function']
                    name = function.get('name')
                    description = function.get('description')
                    input_schema = function.get('parameters')
                else:
                    name = tool.get('name')
                    description = tool.get('description')
                    input_schema = tool.get('parameters')

                if name and input_schema:
                    cleaned_tool = {
                        'name': name,
                        'description': description or '',
                        'input_schema': input_schema
                    }
                    cleaned_tools.append(cleaned_tool)
                else:
                    raise ValueError("Cada herramienta debe tener 'name' y 'parameters'/'input_schema'.")

            cleaned_kwargs['tools'] = cleaned_tools

        # Manejar el parámetro 'stop'
        if 'stop' in cleaned_kwargs:
            stop = cleaned_kwargs.pop('stop')
            if stop is not None:
                if isinstance(stop, str):
                    cleaned_kwargs['stop_sequences'] = [stop]
                elif isinstance(stop, list):
                    cleaned_kwargs['stop_sequences'] = stop

        return cleaned_kwargs