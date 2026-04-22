"""
llm_jsoni18.core
~~~~~~~~~~~~~~~~
Round-trip engine: i18n-JSON ↔ JSONL (the internal canonical form).
All formats and backends speak JSONL units internally.
"""
from __future__ import annotations
import json
from typing import Iterable, Iterator


# ── Canonical unit ──────────────────────────────────────────────────────────

class Unit(dict):
    """
    A single translation unit — a thin dict subclass so it serialises cleanly.

    Mandatory keys:
        id      – stable message key
        source  – source-language string (or key if no source available)
    Optional keys:
        target  – translated string (empty → needs translation)
        note    – translator note / context
        file    – originating file path (for TMX/PO traceability)
        lang_src, lang_tgt – BCP-47 tags, e.g. "en", "mia" (Miami-Illinois)
    """
    @property
    def needs_translation(self) -> bool:
        return not self.get("target", "").strip()


# ── i18n-JSON ↔ JSONL ───────────────────────────────────────────────────────

def json_to_units(obj: dict, *, lang_src: str = "en") -> Iterator[Unit]:
    """Flatten a nested i18n-JSON object into Units (depth-first, dot-joined keys)."""
    def _walk(node, prefix=""):
        if isinstance(node, dict):
            for k, v in node.items():
                yield from _walk(v, f"{prefix}.{k}" if prefix else k)
        else:
            yield Unit(id=prefix, source=str(node), target="", lang_src=lang_src)
    yield from _walk(obj)


def units_to_json(units: Iterable[Unit]) -> dict:
    """Re-assemble units into a nested i18n-JSON dict (dot-keys → nested)."""
    out: dict = {}
    for u in units:
        keys = u["id"].split(".")
        node = out
        for k in keys[:-1]:
            node = node.setdefault(k, {})
        node[keys[-1]] = u.get("target") or u["source"]
    return out


# ── JSONL serialisation ──────────────────────────────────────────────────────

def units_to_jsonl(units: Iterable[Unit]) -> Iterator[str]:
    for u in units:
        yield json.dumps(u, ensure_ascii=False)


def jsonl_to_units(lines: Iterable[str]) -> Iterator[Unit]:
    for line in lines:
        line = line.strip()
        if line:
            yield Unit(json.loads(line))


# ── Convenience round-trip helpers ───────────────────────────────────────────

def roundtrip_json_to_jsonl(obj: dict, **kw) -> list[str]:
    return list(units_to_jsonl(json_to_units(obj, **kw)))


def roundtrip_jsonl_to_json(lines: Iterable[str]) -> dict:
    return units_to_json(jsonl_to_units(lines))
