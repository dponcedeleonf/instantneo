from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional, Union, Generator
import asyncio
import json
import threading
from instantneo.skills import SkillManager
from instantneo.utils.image_utils import process_images
from instantneo.utils.skill_utils import format_tool

@dataclass
class InstantNeoParams:
    provider: str
    api_key: str
    model: str
    role_setup: str
    skills: Optional[List[Callable[..., Any]]] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = 200
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    logit_bias: Optional[Dict[int, float]] = None
    seed: Optional[int] = None
    stream: bool = False
    images: Optional[Union[str, List[str]]] = None
    image_detail: str = "auto"
    skill_manager: Optional[SkillManager] = None # type: ignore

@dataclass
class RunParams:
    prompt: str
    execution_mode: str = "wait_response"
    async_execution: bool = False
    return_full_response: bool = False
    additional_params: Dict[str, Any] = field(default_factory=dict)
    
    # Campos heredados de InstantNeoParams
    model: str = None
    role_setup: str = None
    skills: Optional[List[str]] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    logit_bias: Optional[Dict[int, float]] = None
    seed: Optional[int] = None
    stream: bool = False
    images: Optional[Union[str, List[str]]] = None
    image_detail: str = None

    @classmethod
    def from_instantneo_params(cls, instantneo_params: InstantNeoParams, prompt: str, **kwargs):
        run_params = cls(prompt=prompt)
        for field in InstantNeoParams.__dataclass_fields__:
            if field not in ['provider', 'api_key']:
                value = getattr(instantneo_params, field)
                setattr(run_params, field, value)
        
        for key, value in kwargs.items():
            if hasattr(run_params, key):
                setattr(run_params, key, value)
            else:
                run_params.additional_params[key] = value
        
        return run_params

@dataclass
class AdapterParams:
    model: str
    messages: List[Dict[str, Any]]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    logit_bias: Optional[Dict[int, float]] = None
    seed: Optional[int] = None
    stream: bool = False
    additional_params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_run_params(cls, run_params: RunParams, messages: List[Dict[str, Any]]):
        adapter_params = cls(
            model=run_params.model,
            messages=messages,
            temperature=run_params.temperature,
            max_tokens=run_params.max_tokens,
            presence_penalty=run_params.presence_penalty,
            frequency_penalty=run_params.frequency_penalty,
            stop=run_params.stop,
            logit_bias=run_params.logit_bias,
            seed=run_params.seed,
            stream=run_params.stream,

        )
        exclude_params = {'execution_mode', 'async_execution', 'return_full_response', 'prompt', 'role_setup', 'skills', 'images', 'image_detail'}
        adapter_params.additional_params = {
            k: v for k, v in run_params.additional_params.items() 
            if k not in exclude_params
        }
        return adapter_params

    def to_dict(self) -> Dict[str, Any]:
        result = {k: v for k, v in self.__dict__.items() if v is not None and k != 'additional_params'}
        result.update(self.additional_params)
        return result

@dataclass
class ImageConfig:
    images: Union[str, List[str]]
    image_detail: str = "auto"
    convert_to_base64: bool = True

class InstantNeo:
    WAIT_RESPONSE = "wait_response"
    EXECUTION_ONLY = "execution_only"
    GET_ARGS = "get_args"

    def __init__(self, **kwargs):
        self.config = InstantNeoParams(**kwargs)
        
        #? Buscar una forma de hacerlo global y no pasarlo como parametro
        self.skill_manager = self.config.skill_manager or SkillManager()
                    
        self.adapter = self._create_adapter()
        self.tool_calls = []  # For accumulating tool calls in streaming

    def add_skill(self, skill: Callable):
        self.skill_manager.register_skill(skill)

    def remove_skill(self, skill_name: str):
        self.skill_manager.remove_skill(skill_name)

    def list_skills(self) -> List[str]:
        return self.skill_manager.get_skill_names()

    def _create_adapter(self):
        if self.config.provider == "openai":
            from instantneo.adapters.openai_adapter import OpenAIAdapter
            return OpenAIAdapter(self.config.api_key)
        elif self.config.provider == "anthropic":
            from instantneo.adapters.anthropic_adapter import AnthropicAdapter
            return AnthropicAdapter(self.config.api_key)
        elif self.config.provider == "groq":
            from instantneo.adapters.groq_adapter import GroqAdapter
            return GroqAdapter(self.config.api_key)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def run(self, prompt: str, **kwargs):
        print("Skills available at the start of run:", self.config.skills)
        print("Skills passed to run:", kwargs.get('skills'))
        # Si se pasa skills=None, no incluir ninguna skill en la llamada
        if 'skills' not in kwargs or kwargs['skills'] is None:
            skills_to_use = self.config.skills
        else:
            skills_to_use = kwargs['skills']
        
        print(f"Skills to be used in this run: {skills_to_use}")


        run_params = RunParams.from_instantneo_params(self.config, prompt, **kwargs)
        run_params.skills = skills_to_use
        
        if run_params.execution_mode not in [self.WAIT_RESPONSE, self.EXECUTION_ONLY, self.GET_ARGS]:
            raise ValueError(f"Invalid execution_mode: {run_params.execution_mode}")

        self.async_execution = run_params.async_execution

        active_skills = self._get_active_skills(skills_to_use)
        print(f"Active skills for this run: {list(active_skills.keys())}")

        image_config = self._get_image_config(run_params)

        messages = self._prepare_messages(run_params.prompt, image_config)

        adapter_params = AdapterParams.from_run_params(run_params, messages)

        if active_skills:
            formatted_tools = []
            for name, skill in active_skills.items():
                skill_info = self.skill_manager.get_skill_metadata_by_name(name)
                if skill_info and 'parameters' in skill_info:
                    formatted_tools.append(format_tool(skill_info))
                else:
                    print(f"Warning: Skill '{name}' is missing metadata or 'parameters'. Skipping.")
            
            if formatted_tools:
                adapter_params.additional_params['tools'] = formatted_tools
                if 'tool_choice' in run_params.additional_params:
                    adapter_params.additional_params['tool_choice'] = run_params.additional_params['tool_choice']

        print("Adapter params:", json.dumps(adapter_params.to_dict(), indent=2))

        if run_params.stream:
            return self._handle_streaming_response(adapter_params, run_params.execution_mode, run_params.return_full_response)
        else:
            return self._handle_normal_response(adapter_params, run_params.execution_mode, run_params.return_full_response)

    def _get_active_skills(self, skills: List[str]) -> Dict[str, Callable]:
        active_skills = {}
        if skills:
            for skill_name in skills:
                skill = self.skill_manager.get_skill_by_name(skill_name)
                if skill:
                    active_skills[skill_name] = skill
                else:
                    print(f"Warning: Skill '{skill_name}' not found in SkillManager.")
        return active_skills
    
    def _get_image_config(self, run_params: RunParams) -> Optional[ImageConfig]:
        if run_params.images:
            return ImageConfig(images=run_params.images, image_detail=run_params.image_detail)
        elif self.config.images:
            return ImageConfig(images=self.config.images, image_detail=self.config.image_detail)
        return None

    def _process_images(self, image_config: ImageConfig) -> List[Dict[str, Any]]:
        if not self.adapter.supports_images():
            raise ValueError(f"El proveedor actual no soporta el procesamiento de imágenes")
        return process_images(image_config.images, image_config.image_detail)
    
    def _prepare_messages(self, prompt: str, image_config: Optional[ImageConfig]=None) -> List[Dict[str, Any]]:
        messages = []
        if self.config.role_setup:
            messages.append({"role": "system", "content": self.config.role_setup})
        if image_config and image_config.images:
            content = [{"type": "text", "text": prompt}]
            content.extend(process_images(image_config.images, image_config.image_detail))
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": prompt})
        return messages

    def _process_response(self, response, execution_mode):
        if not hasattr(response, 'choices') or len(response.choices) == 0:
            print("No 'choices' were found in the response")
            return None

        choice = response.choices[0]
        if not hasattr(choice, 'message'):
            print("No 'message' attribute found in the choice")
            return None

        message = choice.message
        content = message.content if message.content else ''
        tool_calls = message.tool_calls if hasattr(message, 'tool_calls') else None

        if tool_calls:
            print(f'{"*" * 40}\n* {"I am using my skills. Wait for it...":^36} *\n{"*" * 40}\n')
            results = self._handle_tool_calls(tool_calls, execution_mode)
            return results
        else:
            return content

    def _handle_tool_calls(self, tool_calls, execution_mode):
        results = []
        threads = [] 
        for tool_call in tool_calls:
            if tool_call.type == 'function':
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                print(f"Llamando a la función: {function_name} con argumentos: {function_args}")
                
                if function_name in self.skill_manager.get_skill_names():
                    skill = self.skill_manager.get_skill_by_name(function_name)
                    
                    if execution_mode == self.EXECUTION_ONLY:
                        thread = threading.Thread(target=skill, kwargs=function_args)
                        threads.append(thread)
                        thread.start()
                        print(f"Función {function_name} ejecutada en un hilo separado")
                    elif execution_mode == self.GET_ARGS:
                        results.append({"name": function_name, "arguments": function_args})
                    else:  # WAIT_RESPONSE
                        result = skill(**function_args)
                        print(f"Resultado de {function_name}: {result}")
                        results.append(result)
                else:
                    print(f"Función {function_name} no encontrada en las skills disponibles")
        
        if execution_mode == self.EXECUTION_ONLY:
            for thread in threads:
                thread.join()
            return "Todas las funciones se han ejecutado en segundo plano."
        elif execution_mode == self.GET_ARGS:
            return results
        else:  # WAIT_RESPONSE
            return results[0] if len(results) == 1 else results

    def _execute_skill(self, skill_name: str, arguments: Dict[str, Any]):
        skill = self.skill_manager.get_skill_by_name(skill_name)
        if skill is None:
            raise ValueError(f"Skill not found: {skill_name}")
        if self.async_execution:
            loop = asyncio.get_event_loop()
            result = loop.run_in_executor(None, skill, **arguments)
            print(f"Resultado de {skill_name}: {result}")
            return result
        else:
            return skill(**arguments)
    
    def _handle_streaming_response(self, adapter_params: AdapterParams, execution_mode: str, return_full_response: bool):
        stream = self.adapter.create_streaming_chat_completion(**adapter_params.to_dict())
        full_response = ""
        tool_calls = []

        for chunk in stream:
            try:
                if isinstance(chunk, int):
                    chunk = str(chunk)
                
                if isinstance(chunk, str):
                    chunk_data = json.loads(chunk)
                else:
                    chunk_data = chunk

                if isinstance(chunk_data, dict) and 'choices' in chunk_data and chunk_data['choices']:
                    delta = chunk_data['choices'][0].get('delta', {})
                    content = delta.get('content')
                    
                    if content:
                        full_response += content
                        if execution_mode == self.WAIT_RESPONSE:
                            yield content
                    
                    if 'tool_calls' in delta:
                        tool_calls.extend(delta['tool_calls'])
                    
                    if delta.get('finish_reason') == 'stop':
                        break
                else:
                    full_response += str(chunk_data)
                    if execution_mode == self.WAIT_RESPONSE:
                        yield str(chunk_data)

            except json.JSONDecodeError:
                full_response += str(chunk)
                if execution_mode == self.WAIT_RESPONSE:
                    yield str(chunk)
            except Exception as e:
                print(f"Error inesperado: {e}")

        if execution_mode == self.EXECUTION_ONLY:
            for tool_call in tool_calls:
                self._execute_skill(tool_call.function.name, json.loads(tool_call.function.arguments))
            yield "Todas las funciones se han ejecutado en segundo plano."
        elif execution_mode == self.GET_ARGS:
            yield tool_calls

        if return_full_response:
            yield {
                "content": full_response,
                "tool_calls": tool_calls
            }

    def _handle_normal_response(self, adapter_params: AdapterParams, execution_mode: str, return_full_response: bool):
        response = self.adapter.create_chat_completion(**adapter_params.to_dict())
        if return_full_response:
            return response
        else:
            return self._process_response(response, execution_mode)