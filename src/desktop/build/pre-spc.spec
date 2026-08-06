# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir 配置（Spec §11：onedir 规避杀软误报）
# 使用：pyinstaller build/pre-spc.spec

import sys
import os
from pathlib import Path

# SPECPATH 在 PyInstaller 6.x 中可能是相对路径，必须转绝对后再取父目录
# PyInstaller 的 SPECPATH 是 spec 文件所在目录（如 <root>/desktop/build）
SPEC_DIR = Path(os.path.abspath(SPECPATH))
ROOT = SPEC_DIR.parent  # <root>/desktop
print("DBG ROOT=", ROOT)

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
