from lang_chain.client.llm_client_generic import LLMClientGeneric


class GPT_3Client(LLMClientGeneric):
    """
    GPT_3.5 AI Client
    """
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
