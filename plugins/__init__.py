# plugins/__init__.py
def load(name):
    if name == "ollama":
        from . import ollama
        return ollama.translate
    elif name == "openai":
        from . import openai
        return openai.translate
    else:
        raise ValueError(f"Unknown backend: {name}")
