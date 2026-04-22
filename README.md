# llm_jsoni18


Format-agnostic i18n ↔ LLM middleware with automatic transmogrification
llm-jsoni18
Format-agnostic i18n ↔ LLM middleware — automatic transmogrification between
i18n-JSON, JSONL, TMX, and PO with pluggable LLM translation backends.
i18n-JSON ──┐
            ├──► Units (JSONL) ──► LLM backend ──► Units ──► i18n-JSON
TMX ────────┘                                               TMX / JSONL / PO

Install
bashpip install llm-jsoni18                        
# core (Ollama + Claude + noop)
pip install "llm-jsoni18[toolkit]"             
# + translate-toolkit (PO/TMX via cli)
pip install "llm-jsoni18[openai]"              
# + OpenAI backend

CLI — i18n-conv
Round-trip: i18n-JSON → JSONL
bashcat en.json | i18n-conv # {"id": "app.title", "source": "Hello", "target": "", "lang_src": "en"}
# ...
Round-trip: JSONL → i18n-JSON
bashcat units.jsonl | i18n-conv --from jsonl --to i18n-json
Translate with Claude (claude.ai backend)
bashexport ANTHROPIC_API_KEY=sk-ant-...
cat en.json | i18n-conv --backend claude --src en --tgt mia > mia.json
Translate with Ollama (local)
bashcat en.json | i18n-conv --backend ollama --model llama3 --src en --tgt fr > fr.json
Only translate missing entries
bash# Merge a partially-translated file — skips units that already have a target
cat partial_mia.json | i18n-conv --backend claude --src en --tgt mia --only-missing > mia.json
TMX corpus → JSONL (fine-tune dataset)
bashi18n-conv --from tmx --to jsonl corpus.tmx > finetune.jsonl
i18n-JSON → TMX (for CAT tools)
bashcat en.json | i18n-conv --to tmx --src en --tgt fr > out.tmx
Use Anthropic Batch API (large jobs)
bashcat en.json | i18n-conv --backend claude --tgt mia --batch > mia.json
List available backends
bashi18n-conv --list-backends
# claude
# ollama
# openai
# noop

Python API
pythonfrom llm_jsoni18 import json_to_units, units_to_json, load_backend

with open("en.json") as f:
    import json; obj = json.load(f)

units = list(json_to_units(obj, lang_src="en"))

# Attach target language
for u in units:
    u["lang_tgt"] = "mia"

backend = load_backend("claude")   # reads ANTHROPIC_API_KEY
translated = list(backend.translate_batch(units))

result = units_to_json(translated)

Third-party backends (plugin system)
Register in your own package's pyproject.toml:
toml[project.entry_points."llm_jsoni18.backends"]
mymemory = "my_package.mymemory_backend:MyMemoryBackend"
Implement BaseBackend.translate_unit(unit) -> str and you're done.
