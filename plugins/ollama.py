# plugins/ollama.py
import requests

def translate(text, model="llama3"):
    r = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": f"Translate:\n{text}",
        "stream": False
    })
    return r.json()["response"]
