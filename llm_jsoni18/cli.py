# cli.py
import sys, json
from .core import json_to_jsonl, jsonl_to_json
from .plugins import load as load_plugin

def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--translate", help="backend (ollama/openai)")
    args = p.parse_args()

    data = sys.stdin.read()

    if data.strip().startswith("{"):
        obj = json.loads(data)
        entries = obj.items()

        if args.translate:
            translate = load_plugin(args.translate)

            out = {}
            for k, v in entries:
                out[k] = translate(v or k)
            print(json.dumps(out, indent=2))
        else:
            for line in json_to_jsonl(obj):
                print(line)

    else:
        lines = data.splitlines()
        print(json.dumps(jsonl_to_json(lines), indent=2))
