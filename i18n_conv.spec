# i18n_conv.spec
# PyInstaller spec file — use instead of CLI flags for reproducible builds.
#
# Build:  pyinstaller i18n_conv.spec
# Or via hatch-pyinstaller (add to build-system.requires in pyproject.toml):
#   [tool.hatch.build.hooks.pyinstaller]
#   scripts = ["llm_jsoni18/cli.py"]
#   onefile = true
#   name    = "i18n-conv"

block_cipher = None

a = Analysis(
    ["llm_jsoni18/cli.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # Include plugin source so compileall can write .pyc at first run
        ("llm_jsoni18/plugins/*.py", "llm_jsoni18/plugins"),
    ],
    hiddenimports=[
        # Dynamic plugin loader won't be seen by static analysis
        "llm_jsoni18.plugins.ollama",
        "llm_jsoni18.plugins.claude_ai",
        "llm_jsoni18.plugins.openai_be",
        "llm_jsoni18.plugins.noop",
        # Optional backends (won't break if absent at build time)
        "anthropic",
        "httpx",
        "openai",
        "rich",
        "translate",       # translate-toolkit top-level
        "orjson",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "test"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="i18n-conv",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    onefile=True,
)
