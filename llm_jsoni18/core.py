# core.py
import json

def json_to_jsonl(data):
    for k, v in data.items():
        yield json.dumps({
            "id": k,
            "source": k,
            "target": v
        })

def jsonl_to_json(lines):
    out = {}
    for line in lines:
        obj = json.loads(line)
        out[obj["id"]] = obj.get("target") or obj["source"]
    return out
