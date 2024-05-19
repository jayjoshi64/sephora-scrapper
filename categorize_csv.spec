# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['brand_wise_1_0.py'],
    pathex=['/Users/jjoshi/.local/share/virtualenvs/sephora-NFgSTR_O/lib/python3.10/site-packages'],
    binaries=[],
    datas=[],
    hiddenimports=['backports', 'backports.functools_lru_cache', 'backports.tarfile'],
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
    name='categorize_csv',
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
)
