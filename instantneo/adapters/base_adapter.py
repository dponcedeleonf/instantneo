#base_adapter.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Generator, AsyncGenerator

class BaseAdapter(ABC):
    @abstractmethod
    def create_chat_completion(self, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_streaming_chat_completion(self, **kwargs) -> Union[Generator[Dict[str, Any], None, None], AsyncGenerator[Dict[str, Any], None]]:
        pass

    def format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return messages

    def format_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return tools

    def supports_images(self) -> bool:
        return False