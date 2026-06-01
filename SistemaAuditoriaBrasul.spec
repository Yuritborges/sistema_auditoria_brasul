# -*- mode: python ; coding: utf-8 -*-

import os

# Em .spec, __file__ pode não estar definido dependendo da forma de invocação.
ROOT = os.path.abspath(".")
_ICON_CANDIDATES = [
    os.path.join(ROOT, "assets", "iconebrasul2.ico"),
    os.path.join(ROOT, "assets", "logos", "iconebrasul2.ico"),
    os.path.join(ROOT, "assets", "logos", "logo_brasul.ico"),
]
_ICON_EXE = next((os.path.normpath(p) for p in _ICON_CANDIDATES if os.path.isfile(p)), "")
if not _ICON_EXE:
    raise FileNotFoundError(
        "Nenhum .ico para o build. Coloque assets/iconebrasul2.ico (blocos 3D Brasul)."
    )


a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[(os.path.join(ROOT, 'assets'), 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SISTEMA AUDITORIA BRASUL',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=_ICON_EXE,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SISTEMA AUDITORIA BRASUL',
)
