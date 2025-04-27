import sys
import os
path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(path)
# print(sys.path)
from env import get_env_value
from lang_chain.client.client_error import ClientUrlFormatError, ClientAPIUnsupportedError
from lang_chain.client.llm_client_generic import LLMClientGeneric
from lang_chain.client.gpt_3.client import GPT_3Client
from lang_chain.client.client_provider import ClientProvider
from utils.singleton import Singleton
from utils.url_paser import is_valid_url


class ClientFactory(metaclass=Singleton):


    def __init__(self):
        self._client_url = get_env_value("LLM_BASE_URL")
        self._api_key = get_env_value("LLM_API_KEY")
        self._sanity_check()

    @property
    def client_provider(self):
        return self._client_provider

    @property
    def client_url(self):
        return self._client_url

    @property
    def api_key(self):
        return self._api_key

    def _sanity_check(self):
        print(f"client url: {self._client_url}")
        if not is_valid_url(self._client_url):
            raise ClientUrlFormatError("client url provided is not a url string")

        # if self._client_url not in self._client_provider_mappings:
        #     raise ClientAPIUnsupportedError("Invalid client API")

    def get_client(self) -> LLMClientGeneric:
        if self._client_provider == ClientProvider.GPT_3:
            return GPT_3Client()
        raise ClientAPIUnsupportedError("No client API adapted")


if __name__ == "__main__":
    factory1 = ClientFactory()
    #factory2 = ClientFactory()

    #print(factory1 is factory2)
    print(factory1.client_url)
    print(factory1.api_key)
