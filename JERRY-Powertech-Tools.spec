# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for JERRY Powertech Tools
# To build: pyinstaller JERRY-Powertech-Tools.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('powertech_tools', 'powertech_tools'),
    ],
    hiddenimports=[
        'nptdms',
        'nptdms.tdms',
        'pandas',
        'numpy',
        'matplotlib',
        'PIL',
        'tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='JERRY-Powertech-Tools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed app (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='powertech_tools/assets/icon.ico' if os.path.exists('powertech_tools/assets/icon.ico') else None,
)
