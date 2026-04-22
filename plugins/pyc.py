import importlib.util
import pathlib
import sys
import compileall
compileall.compile_dir(str(PLUGIN_DIR), force=False)

PLUGIN_DIR = pathlib.Path(__file__).parent


def load(name: str):
    """
    Load plugin function (expects: translate(text) -> str)

    Priority:
      1. __pycache__/*.pyc
      2. .py source fallback
    """

    pycache = PLUGIN_DIR / "__pycache__"

    # 1️⃣ Try compiled .pyc first
    if pycache.exists():
        pyc_files = sorted(pycache.glob(f"{name}*.pyc"))
        if pyc_files:
            return _load_pyc(pyc_files[0], name).translate

    # 2️⃣ Fallback to .py
    py_file = PLUGIN_DIR / f"{name}.py"
    if py_file.exists():
        return _load_py(py_file, name).translate

    raise ImportError(f"Plugin not found: {name}")


def _load_py(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_pyc(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
