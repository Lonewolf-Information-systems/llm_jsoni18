import sys
import json
from .core import json_to_jsonl, jsonl_to_json

def main():
    data = sys.stdin.read()

    if data.strip().startswith("{"):
        # JSON → JSONL
        obj = json.loads(data)
        for line in json_to_jsonl(obj):
            print(line)
    else:
        # JSONL → JSON
        lines = data.splitlines()
        print(json.dumps(jsonl_to_json(lines), indent=2))
