# ──────────────────────────────────────────────────────────────────────────────
# llm-jsoni18 — Makefile
# Requires: hatch, pip
# ──────────────────────────────────────────────────────────────────────────────

.PHONY: all install dev lint test clean \
        build-wheel build-cython build-pyinstaller build-cx_freeze \
        precompile-pyc

PYTHON   ?= python3
HATCH    ?= hatch
PIP      ?= pip

# ── Dev setup ─────────────────────────────────────────────────────────────────

install:
	$(PIP) install -e ".[all]"

dev:
	$(PIP) install -e ".[all,dev]"

# ── Lint / test ───────────────────────────────────────────────────────────────

lint:
	ruff check llm_jsoni18 tests
	mypy llm_jsoni18

test:
	pytest

# ── Pre-compile plugins to .pyc (cheap, no Cython) ───────────────────────────
#
# This is what plugins/__init__.py does automatically at runtime (force=False).
# Run explicitly to pre-warm __pycache__ before packaging or deployment.

precompile-pyc:
	$(PYTHON) -m compileall -q -b llm_jsoni18/plugins/

# ── Standard wheel / sdist ────────────────────────────────────────────────────

build-wheel:
	$(HATCH) build -t wheel -t sdist

# ── Cython: compile hot modules to .so ───────────────────────────────────────
#
# Requires: pip install ".[cython]"
# Adds hatch-cythonize to build-system.requires in pyproject.toml first, then:
#
#   make build-cython
#
# The resulting .so files are importable in-place; .pyc tier still works as
# fallback for modules not yet Cythonized.

build-cython:
	@echo "→ Uncomment hatch-cythonize in pyproject.toml [build-system.requires] first"
	@echo "→ Then uncomment [tool.hatch.build.hooks.cythonize] section"
	$(HATCH) build -t wheel

# ── PyInstaller one-file executable ──────────────────────────────────────────
#
# Requires: pip install ".[pyinstaller]"
# Or add hatch-pyinstaller to build-system.requires and use hatch build.
# The hook below uses pyinstaller directly (more control over hidden imports).

build-pyinstaller:
	$(PIP) install ".[pyinstaller]" --quiet
	pyinstaller \
	  --onefile \
	  --name i18n-conv \
	  --hidden-import llm_jsoni18.plugins.ollama \
	  --hidden-import llm_jsoni18.plugins.claude_ai \
	  --hidden-import llm_jsoni18.plugins.openai_be \
	  --hidden-import llm_jsoni18.plugins.noop \
	  --hidden-import orjson \
	  --collect-all llm_jsoni18 \
	  llm_jsoni18/cli.py
	@echo "→ Binary at dist/i18n-conv"

# ── cx_Freeze (no hatch plugin — invoked directly) ───────────────────────────
#
# Requires: pip install ".[cx_freeze]"
# Produces:  build/exe.<platform>/i18n-conv[.exe]
# Windows:   python cx_freeze_setup.py bdist_msi   → build/*.msi

build-cx_freeze:
	$(PIP) install ".[cx_freeze]" --quiet
	$(PYTHON) cx_freeze_setup.py build
	@echo "→ Binary in build/"

build-msi: build-cx_freeze
	$(PYTHON) cx_freeze_setup.py bdist_msi
	@echo "→ MSI installer in build/"

# ── Clean ─────────────────────────────────────────────────────────────────────

clean:
	rm -rf dist/ build/ *.egg-info .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.so"  -delete

all: lint test build-wheel
