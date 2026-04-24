# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_dash_app.py'],
    pathex=[],
    binaries=[],
    datas=[('config', 'config'), ('output_files', 'output_files'), ('app_dash.py', '.'), ('run_dash_app.py', '.')],
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
    a.binaries,
    a.datas,
    [],
    name='Blood_Collection_Dashboard_Web',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='Blood_Collection_Dashboard_Web.app',
    icon=None,
    bundle_identifier=None,
)
