
from abc import abstractmethod, ABCMeta, ABC
from typing import List, Dict, Tuple, Optional,Union

from openai import OpenAI, Stream
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from env import get_env_value
from utils.singleton import Singleton


class LLMClientBase(object):
    def __init__(self):
        self.__client = OpenAI(
            api_key=get_env_value("LLM_API_KEY"),
            base_url=get_env_value("LLM_BASE_URL"),
        )
        self.__model_name = get_env_value("MODEL_NAME")

    @property
    def client(self) -> OpenAI:
        return self.__client

    @property
    def model_name(self) -> str:
        return self.__model_name

    @abstractmethod
    def chat_with_ai(self, prompt: str) -> Optional[str]:
        raise NotImplementedError()

    @staticmethod
    def construct_messages(prompt: str,history: Optional[List[List]]) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    def chat_with_ai_stream(self, prompt: str,
                            history: Optional[List[List[str]]] = None
                            ) -> Union[ChatCompletion, Stream[ChatCompletionChunk]]:
        raise NotImplementedError()

    @abstractmethod
    def chat_using_messages(self, messages: List[Dict]
                            ) -> Optional[str]:
        raise NotImplementedError()

    @abstractmethod
    def chat_on_tools(self, prompt: str, tools: List[Dict],
                      history: Optional[List[List[str]]] = None
                      ) -> Optional[Tuple[str, Dict]]:
        raise NotImplementedError()
