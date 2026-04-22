# plugins/openai.py
from openai import OpenAI

client = OpenAI()

def translate(text, model="gpt-4o-mini"):
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": text}]
    )
    return r.choices[0].message.content
