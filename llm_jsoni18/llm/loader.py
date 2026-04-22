# llm_jsoni18/llm/loader.py
from importlib.metadata import entry_points

def load_backend(name: str):
    eps = entry_points(group="llm_jsoni18.backends")

    for ep in eps:
        if ep.name == name:
            return ep.load()()

    raise ValueError(f"Backend '{name}' not found")
