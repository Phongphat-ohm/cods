# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification for JADS (Judicial Automated Document System)
100% Offline & Air-Gapped Judicial Assistant
"""

import os
import sys

block_cipher = None

project_dir = os.path.abspath(SPECPATH)

datas = [
    (os.path.join(project_dir, 'fonts'), 'fonts'),
    (os.path.join(project_dir, 'templates'), 'templates'),
    (os.path.join(project_dir, 'logo.png'), '.'),
    (os.path.join(project_dir, 'logo.ico'), '.'),
]

hiddenimports = [
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtSvg',
    'openpyxl',
    'xlrd',
    'docx',
    'lxml',
    'lxml.etree',
    'sqlite3',
    'uuid',
    'shutil',
    'json',
]

a = Analysis(
    ['main.py'],
    pathex=[project_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'pydoc',
        'pdb',
        'matplotlib',
        'scipy',
        'numpy',
        'pandas',
        'torch',
        'tensorflow',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JADS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_dir, 'logo.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JADS',
)
