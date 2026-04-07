# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# Collect everything from PySide6 (Qt DLLs, plugins, QML, etc.)
pyside6_datas, pyside6_binaries, pyside6_hiddenimports = collect_all("PySide6")

# Collect pymupdf (contains mupdfcpp64.dll and .pyd extensions)
pymupdf_datas, pymupdf_binaries, pymupdf_hiddenimports = collect_all("pymupdf")

# fitz is a thin wrapper over pymupdf
fitz_datas, fitz_binaries, fitz_hiddenimports = collect_all("fitz")

# Merge all hidden imports
all_hiddenimports = (
    pyside6_hiddenimports
    + pymupdf_hiddenimports
    + fitz_hiddenimports
    + collect_submodules("fitz")
    + collect_submodules("pymupdf")
    + [
        "pymupdf",
        "fitz",
        "PySide6.QtSvg",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtPrintSupport",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "PIL.ImageFont",
    ]
)

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=pyside6_binaries + pymupdf_binaries + fitz_binaries,
    datas=(
        pyside6_datas
        + pymupdf_datas
        + fitz_datas
        + [
            ("assets", "assets"),
            ("SVGs", "SVGs"),
        ]
    ),
    hiddenimports=all_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim unused heavy Qt modules to keep size manageable
        "PySide6.Qt3DAnimation",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DExtras",
        "PySide6.Qt3DInput",
        "PySide6.Qt3DLogic",
        "PySide6.Qt3DRender",
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtLocation",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtNfc",
        "PySide6.QtPositioning",
        "PySide6.QtQuick",
        "PySide6.QtQuick3D",
        "PySide6.QtQuickControls2",
        "PySide6.QtQuickWidgets",
        "PySide6.QtRemoteObjects",
        "PySide6.QtScxml",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
        "PySide6.QtSpatialAudio",
        "PySide6.QtTextToSpeech",
        "PySide6.QtVirtualKeyboard",
        "PySide6.QtWebChannel",
        "PySide6.QtWebEngine",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineQuick",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebSockets",
        "tkinter",
        "unittest",
        "email",
        "html",
        "http",
        "xmlrpc",
        "pydoc",
        "doctest",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# ── Single-file executable ──────────────────────────────────────────────────
# All binaries, datas, and the Python runtime DLL are embedded inside the
# .exe and extracted to %TEMP%\_MEIxxxxxx at launch, so the app runs on any
# machine with no external dependencies.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # ← embed ALL native DLLs (incl. python3.dll, mupdfcpp64.dll)
    a.datas,         # ← embed assets, Qt plugins, fonts, SVGs
    [],
    name="PDF-eSign",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,       # UPX can corrupt Qt/MuPDF DLLs — keep off for reliability
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
