"""
llm_jsoni18.plugins
~~~~~~~~~~~~~~~~~~~
Three-tier plugin loader:

  1. __pycache__/<name>.cpython-XY.pyc  — pre-compiled bytecode (fastest)
  2. plugins/<name>.py                  — source, compiled on first load
  3. importlib entry_points             — pip-installed third-party backends

Pre-compilation
---------------
On import, compileall.compile_dir is called with force=False, so only
stale/missing .pyc files are rebuilt — noop when everything is current.
This means the next import of any plugin immediately hits tier-1.

Opt-out
-------
Set env var  LLM_JSONI18_NO_PYC=1  or pass  prefer_pyc=False  to load()
to skip tiers 1-2 entirely.  Useful under Cython .so builds.

Legacy shim
-----------
Plugins that expose a bare  translate(text) -> str  function (the original
plugins/ollama.py style) are auto-wrapped so existing code keeps working.
"""
from __future__ import annotations

import compileall
import importlib.util
import inspect
import os
import pathlib
import sys
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..backends import BaseBackend

# ── Plugin directory (same folder as this file) ───────────────────────────────
PLUGIN_DIR = pathlib.Path(__file__).parent

# ── Pre-compile stale/missing .pyc on first import ───────────────────────────
_NO_PYC = os.environ.get("LLM_JSONI18_NO_PYC", "").strip() not in ("", "0")

if not _NO_PYC:
    compileall.compile_dir(
        str(PLUGIN_DIR),
        force=False,   # skip already-fresh .pyc files
        quiet=1,       # suppress per-file noise; errors still surface
        legacy=False,  # PEP 3147 layout: __pycache__/name.cpython-XY.pyc
    )


# ── Module loading helpers ────────────────────────────────────────────────────

def _load_from_spec(path: pathlib.Path, name: str):
    """Load a module from an absolute path (.py or .pyc)."""
    fq_name = f"llm_jsoni18.plugins.{name}"
    spec = importlib.util.spec_from_file_location(fq_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot build spec from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[fq_name] = module       # register so intra-package imports work
    spec.loader.exec_module(module)     # type: ignore[union-attr]
    return module


def _find_pyc(name: str) -> pathlib.Path | None:
    """
    Return the best .pyc for *name* from __pycache__, or None.

    CPython stores files as:  __pycache__/ollama.cpython-311.pyc
    Sorting descending gives us the highest CPython version when several exist.
    """
    pycache = PLUGIN_DIR / "__pycache__"
    if not pycache.exists():
        return None
    candidates = sorted(pycache.glob(f"{name}.cpython-*.pyc"), reverse=True)
    return candidates[0] if candidates else None


def _extract_class(module, name: str):
    """
    Return an instantiable backend from a loaded module.

    Priority:
      1. First BaseBackend subclass found in the module.
      2. Bare translate(text)->str function — wrapped in a _FnBackend shim
         for backward compatibility with the original plugins/ollama.py style.
    """
    from ..backends import BaseBackend

    for attr_name in dir(module):
        obj = getattr(module, attr_name)
        if (
            inspect.isclass(obj)
            and issubclass(obj, BaseBackend)
            and obj is not BaseBackend
        ):
            return obj

    # Legacy: bare translate() function
    translate_fn = getattr(module, "translate", None)
    if callable(translate_fn):
        return _make_fn_backend(translate_fn)

    return None


def _make_fn_backend(fn):
    """
    Wrap a bare  translate(text) -> str  function as a BaseBackend subclass.

    This preserves full backward compatibility with the original plugin API:

        # plugins/ollama.py (old style)
        def translate(text, model="llama3"):
            ...
    """
    from ..backends import BaseBackend
    from ..core import Unit

    class _FnBackend(BaseBackend):
        name = "fn_shim"

        def translate_unit(self, unit: Unit) -> str:
            return fn(unit["source"])

    _FnBackend.__name__ = f"_FnBackend({fn.__module__}.{fn.__qualname__})"
    return _FnBackend


# ── Public API ────────────────────────────────────────────────────────────────

def load(name: str, prefer_pyc: bool = True, **opts) -> "BaseBackend":
    """
    Resolve and instantiate a backend by name.

    Resolution order
    ----------------
    1. __pycache__/<name>.cpython-XY.pyc  (if prefer_pyc and not NO_PYC)
    2. plugins/<name>.py                  (source fallback)
    3. importlib entry_points             (installed packages)

    Parameters
    ----------
    name       : Backend name — "claude", "ollama", "openai", "noop", …
    prefer_pyc : Set False to skip .pyc / .py tiers (e.g. under Cython .so).
    **opts     : Forwarded to the backend constructor.
    """
    use_pyc = prefer_pyc and not _NO_PYC

    # ── Tier 1: compiled bytecode ─────────────────────────────────────────
    if use_pyc:
        pyc = _find_pyc(name)
        if pyc:
            try:
                mod = _load_from_spec(pyc, name)
                cls = _extract_class(mod, name)
                if cls:
                    return cls(**opts)
            except Exception:
                pass  # degraded gracefully to tier 2

    # ── Tier 2: .py source (compileall will have written .pyc already) ────
    py_file = PLUGIN_DIR / f"{name}.py"
    if py_file.exists():
        mod = _load_from_spec(py_file, name)
        cls = _extract_class(mod, name)
        if cls:
            return cls(**opts)

    # ── Tier 3: pip-installed entry_points ────────────────────────────────
    eps = entry_points(group="llm_jsoni18.backends")
    for ep in eps:
        if ep.name == name:
            cls = ep.load()
            return cls(**opts)

    raise ValueError(
        f"Backend '{name}' not found.\n"
        f"  Checked plugin dir : {PLUGIN_DIR}\n"
        f"  Installed backends : {list_backends()}\n"
        f"  Tip: pip install your-backend-pkg, or add a .py file to {PLUGIN_DIR}"
    )


def list_backends() -> list[str]:
    """Return names of all backends registered via entry_points."""
    return sorted(ep.name for ep in entry_points(group="llm_jsoni18.backends"))
