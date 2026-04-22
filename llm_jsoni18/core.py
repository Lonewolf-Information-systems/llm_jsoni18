"""
llm_jsoni18.cli
~~~~~~~~~~~~~~~
i18n-conv — the main command-line entry point.

Examples
--------
# i18n-JSON → JSONL (no backend)
$ cat en.json | i18n-conv

# i18n-JSON → translate in-place → i18n-JSON
$ cat en.json | i18n-conv --backend claude --src en --tgt mia > mia.json

# JSONL → i18n-JSON
$ cat units.jsonl | i18n-conv --from jsonl --to i18n-json

# TMX → JSONL (for fine-tune dataset)
$ i18n-conv --from tmx --to jsonl corpus.tmx > dataset.jsonl

# i18n-JSON → TMX
$ cat en.json | i18n-conv --to tmx --src en --tgt fr > out.tmx

# List available backends
$ i18n-conv --list-backends
"""
from __future__ import annotations
import sys
import json
import click

from .core import (
    json_to_units, units_to_json,
    units_to_jsonl, jsonl_to_units,
)
from .plugins import load as load_backend, list_backends


# ── Format sniffers ──────────────────────────────────────────────────────────

def _sniff(data: str) -> str:
    stripped = data.lstrip()
    if stripped.startswith("<?xml") or stripped.startswith("<tmx"):
        return "tmx"
    if stripped.startswith("{"):
        return "i18n-json"
    return "jsonl"


# ── Format readers ───────────────────────────────────────────────────────────

def _read(fmt: str, data: str, src: str, tgt: str):
    if fmt == "i18n-json":
        return json_to_units(json.loads(data), lang_src=src)
    if fmt == "jsonl":
        return jsonl_to_units(data.splitlines())
    if fmt == "tmx":
        import io
        from .formats.tmx_fmt import tmx_to_units
        return tmx_to_units(io.StringIO(data), lang_src=src, lang_tgt=tgt)
    if fmt == "po":
        try:
            from .formats.po_fmt import po_to_units
        except ImportError:
            raise click.ClickException("PO support requires: pip install translate-toolkit")
        import io
        return po_to_units(io.StringIO(data), lang_src=src, lang_tgt=tgt)
    raise click.ClickException(f"Unknown input format: {fmt}")


# ── Format writers ───────────────────────────────────────────────────────────

def _write(fmt: str, units, src: str, tgt: str) -> str:
    units = list(units)
    if fmt == "i18n-json":
        return json.dumps(units_to_json(units), indent=2, ensure_ascii=False)
    if fmt == "jsonl":
        return "\n".join(units_to_jsonl(units))
    if fmt == "tmx":
        from .formats.tmx_fmt import units_to_tmx
        return units_to_tmx(units, src_lang=src, tgt_lang=tgt or "xx")
    raise click.ClickException(f"Unknown output format: {fmt}")


# ── CLI ───────────────────────────────────────────────────────────────────────

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("file", required=False, type=click.File("r"), default="-")
@click.option("--from", "from_fmt",   default="",    metavar="FMT",
              help="Input format: i18n-json, jsonl, tmx, po  (auto-detected if omitted)")
@click.option("--to",   "to_fmt",     default="",    metavar="FMT",
              help="Output format: i18n-json, jsonl, tmx  (default: jsonl, or i18n-json when input is jsonl)")
@click.option("--backend", "-b",      default="",    metavar="NAME",
              help="LLM backend to use for translation (ollama, claude, openai, noop, …)")
@click.option("--src",                default="en",  metavar="LANG",  show_default=True,
              help="Source BCP-47 language code")
@click.option("--tgt",                default="",    metavar="LANG",
              help="Target BCP-47 language code (required for translation)")
@click.option("--model",              default="",    metavar="MODEL",
              help="Model override for the selected backend")
@click.option("--batch/--no-batch",   default=False,
              help="Use backend batch API if supported (e.g. Anthropic Message Batches)")
@click.option("--only-missing",       is_flag=True,
              help="Only translate units where target is empty")
@click.option("--list-backends",      is_flag=True,  is_eager=True, expose_value=False,
              callback=lambda ctx, _, v: (click.echo("\n".join(list_backends())), ctx.exit()) if v else None,
              help="List registered translation backends and exit")
def main(file, from_fmt, to_fmt, backend, src, tgt, model, batch, only_missing):
    """
    Format-agnostic i18n ↔ LLM middleware.

    Reads i18n-JSON / JSONL / TMX / PO from FILE (or stdin),
    optionally translates via --backend, and writes the requested output format.
    """
    data = file.read()

    # Auto-detect input format
    in_fmt  = from_fmt or _sniff(data)

    # Default output format
    if not to_fmt:
        to_fmt = "i18n-json" if in_fmt == "jsonl" else "jsonl"

    # Parse → units
    units = list(_read(in_fmt, data, src, tgt))

    # Translate
    if backend:
        opts = {"use_batch": batch}
        if model:
            opts["model"] = model
        be = load_backend(backend, **opts)
        if only_missing:
            translated, passthru = [], []
            for u in units:
                (translated if u.needs_translation else passthru).append(u)
            units = list(be.translate_batch(translated)) + passthru
        else:
            units = list(be.translate_batch(units))

    # Serialise → output format
    click.echo(_write(to_fmt, units, src, tgt))


if __name__ == "__main__":
    main()
