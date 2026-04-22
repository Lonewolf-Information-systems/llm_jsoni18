"""
llm_jsoni18 backend — Claude (Anthropic)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Uses the `anthropic` SDK.  Set ANTHROPIC_API_KEY in the environment.

Supports:
  • Single-unit translate_unit()
  • True batch via the Anthropic Message Batches API (translate_batch)
  • Optional system-prompt injection for domain context (e.g. Myaamia linguistic terms)
"""
from __future__ import annotations
import os
import time
from typing import Iterable

from ..backends import BaseBackend
from ..core import Unit

try:
    import anthropic
except ImportError as exc:
    raise ImportError("Install the anthropic package: pip install anthropic") from exc


_DEFAULT_MODEL  = "claude-sonnet-4-20250514"
_DEFAULT_SYSTEM = (
    "You are a professional i18n translator embedded in an automated pipeline. "
    "When given a UI string, return ONLY the translation — no preamble, no markdown, "
    "no explanation.  Preserve placeholders like {var}, %s, {{count}}, etc. verbatim."
)


class ClaudeBackend(BaseBackend):
    name = "claude"

    def __init__(
        self,
        model: str       = _DEFAULT_MODEL,
        api_key: str     = "",
        system: str      = _DEFAULT_SYSTEM,
        max_tokens: int  = 512,
        use_batch: bool  = False,   # opt-in to Batch API
        **opts,
    ):
        super().__init__(**opts)
        self.model      = model
        self.system     = system
        self.max_tokens = max_tokens
        self.use_batch  = use_batch
        self.client     = anthropic.Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    # ── Single unit ──────────────────────────────────────────────────────────

    def translate_unit(self, unit: Unit) -> str:
        msg = self.client.messages.create(
            model      = self.model,
            max_tokens = self.max_tokens,
            system     = self.system,
            messages   = [{"role": "user", "content": self._build_prompt(unit)}],
        )
        return msg.content[0].text.strip()

    # ── Batch API (opt-in) ────────────────────────────────────────────────────

    def translate_batch(self, units: Iterable[Unit]) -> Iterable[Unit]:
        units = list(units)
        if not self.use_batch:
            yield from super().translate_batch(units)
            return

        requests_payload = [
            anthropic.types.message_create_params.Request(
                custom_id = u["id"],
                params    = anthropic.types.MessageCreateParamsNonStreaming(
                    model      = self.model,
                    max_tokens = self.max_tokens,
                    system     = self.system,
                    messages   = [{"role": "user", "content": self._build_prompt(u)}],
                ),
            )
            for u in units
        ]

        batch = self.client.messages.batches.create(requests=requests_payload)
        batch_id = batch.id
        print(f"[claude] Batch submitted: {batch_id}", flush=True)

        # Poll until complete
        while True:
            status = self.client.messages.batches.retrieve(batch_id)
            if status.processing_status == "ended":
                break
            time.sleep(5)

        # Collect results keyed by custom_id
        results: dict[str, str] = {}
        for result in self.client.messages.batches.results(batch_id):
            if result.result.type == "succeeded":
                results[result.custom_id] = result.result.message.content[0].text.strip()
            else:
                # Fallback: return source on error
                results[result.custom_id] = ""

        for u in units:
            out = dict(u)
            out["target"] = results.get(u["id"], u["source"])
            yield Unit(out)
