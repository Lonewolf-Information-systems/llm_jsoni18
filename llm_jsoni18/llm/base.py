# llm_jsoni18/llm/base.py
class LLMBackend:
    name = "base"

    def translate(self, text: str, **kwargs) -> str:
        raise NotImplementedError
