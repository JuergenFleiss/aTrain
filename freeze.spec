# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata
from importlib.resources import files

icon_path = str(files("aTrain.static").joinpath("favicon.ico"))

datas = []
datas += collect_data_files('aTrain')
datas += collect_data_files('torch')
datas += collect_data_files('nicegui')
datas += collect_data_files('lightning')
datas += collect_data_files('lightning_fabric')
datas += collect_data_files('lightning_utilities')
datas += collect_data_files('pyannote')
datas += collect_data_files('pyannote.audio.models')
datas += collect_data_files('pyannote.audio.models.segmentation')
datas += collect_data_files('pyannote.audio.models.embedding')
datas += collect_data_files('pytorch_lightning')
datas += collect_data_files('faster_whisper')
datas += collect_data_files('aTrain_core')
datas += copy_metadata('lightning')
datas += copy_metadata('lightning_utilities')
datas += copy_metadata('torch')
datas += copy_metadata('tqdm')
datas += copy_metadata('requests')
datas += copy_metadata('packaging')
datas += copy_metadata('filelock')
datas += copy_metadata('numpy')
datas += copy_metadata('tokenizers')
datas += copy_metadata('pyannote.audio')
datas += copy_metadata('huggingface-hub')
datas += copy_metadata('pyyaml')
datas += copy_metadata('pytorch_lightning')
datas += copy_metadata('aTrain_core')

hiddenimports = ['pytorch_lightning','pyyaml','huggingface-hub','pyannote','pytorch','lightning']
hiddenimports += collect_submodules('wakepy')
hiddenimports += collect_submodules('pyannote')
hiddenimports += collect_submodules('sklearn')

a = Analysis(
    ['freeze.py', 'freeze_cli.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
runtime_scripts = [script for script in a.scripts if script[0] not in ('freeze', 'freeze_cli')]
gui_scripts = runtime_scripts + [script for script in a.scripts if script[0] == 'freeze']
cli_scripts = runtime_scripts + [script for script in a.scripts if script[0] == 'freeze_cli']

exe = EXE(
    pyz,
    gui_scripts,
    [],
    exclude_binaries=True,
    name='aTrain',
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
    icon=[icon_path],
    plist='Info.plist'
)
exe_cli = EXE(
    pyz,
    cli_scripts,
    [],
    exclude_binaries=True,
    name='aTrain-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[icon_path],
    plist='Info.plist'
)
coll = COLLECT(
    exe,
    exe_cli,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='aTrain',
)
