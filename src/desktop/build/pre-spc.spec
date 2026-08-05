# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir 配置（Spec §11：onedir 规避杀软误报）
# 使用：pyinstaller build/pre-spc.spec

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent.parent

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "app" / "resources" / "icons"), "app/resources/icons"),
        (str(ROOT / "app" / "resources" / "design-tokens.json"), "app/resources"),
        (str(ROOT.parent / "engine"), "engine"),
    ],
    hiddenimports=["PyQt6.QtSvg"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["backend", "tests"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pre-spc",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="pre-spc",
)
