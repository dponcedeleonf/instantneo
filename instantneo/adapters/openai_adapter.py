from openai import OpenAI, OpenAIError
from typing import Dict, Any, Generator
from instantneo.adapters.base_adapter import BaseAdapter

class OpenAIAdapter(BaseAdapter):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def create_chat_completion(self, **kwargs) -> Dict[str, Any]:
        cleaned_kwargs = self._clean_kwargs(kwargs)

        try:
            response = self.client.chat.completions.create(**cleaned_kwargs)
            return response
        except OpenAIError as e:
            raise RuntimeError(f"Error in OpenAI API: {str(e)}")

    def create_streaming_chat_completion(self, **kwargs) -> Generator[Dict[str, Any], None, None]:
        kwargs['stream'] = True
        cleaned_kwargs = self._clean_kwargs(kwargs)

        response = self.client.chat.completions.create(**cleaned_kwargs)
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    def supports_images(self) -> bool:
        return True

    def _clean_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        cleaned_kwargs = {k: v for k, v in kwargs.items() if v is not None}

        if 'tools' in cleaned_kwargs and not cleaned_kwargs['tools']:
            del cleaned_kwargs['tools']

        # Manejar específicamente el argumento 'stop'
        if 'stop' in cleaned_kwargs:
            if cleaned_kwargs['stop'] is None:
                del cleaned_kwargs['stop']
            elif isinstance(cleaned_kwargs['stop'], str):
                cleaned_kwargs['stop'] = [cleaned_kwargs['stop']]
            elif not isinstance(cleaned_kwargs['stop'], list):
                del cleaned_kwargs['stop']

        return cleaned_kwargs