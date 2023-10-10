# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

datas = []
datas += [('static', 'static')]
datas += [('templates', 'templates')]
datas += [('models','models')]
datas += [('ffmpeg.exe','.')]
datas += [('faq.yaml', '.')]
datas += [('venv/Lib/site-packages/transformers','transformers')]
datas += [('venv/Lib/site-packages/speechbrain','speechbrain')]
datas += collect_data_files('torch')
datas += collect_data_files('transformers')
datas += collect_data_files('lightning')
datas += collect_data_files('lightning_cloud')
datas += collect_data_files('lightning_fabric')
datas += collect_data_files('lightning_utilities')
datas += collect_data_files('pyannote')
datas += collect_data_files('pyannote.audio.models')
datas += collect_data_files('pyannote.audio.models.segmentation')
datas += collect_data_files('pyannote.audio.models.embedding')
datas += collect_data_files('pytorch_lightning')
datas += collect_data_files('faster_whisper')
datas += collect_data_files('whisperx')
datas += copy_metadata('transformers')
datas += copy_metadata('lightning')
datas += copy_metadata('lightning_cloud')
datas += copy_metadata('lightning_utilities')
datas += copy_metadata('torch')
datas += copy_metadata('tqdm')
datas += copy_metadata('regex')
datas += copy_metadata('requests')
datas += copy_metadata('packaging')
datas += copy_metadata('filelock')
datas += copy_metadata('numpy')
datas += copy_metadata('tokenizers')
datas += copy_metadata('pyannote.audio')
datas += copy_metadata('whisperx')
datas += copy_metadata('huggingface-hub')
datas += copy_metadata('safetensors')
datas += copy_metadata('pyyaml')
datas += copy_metadata('pytorch_lightning')

hiddenimports = ['pytorch_lightning','pyyaml','safetensors','huggingface-hub','speechbrain','whisperx','pyannote','pytorch','transformers','lightning',]
hiddenimports += collect_submodules('wakepy')
hiddenimports += collect_submodules('speechbrain')
hiddenimports += collect_submodules('pyannote')
hiddenimports += collect_submodules('sklearn')

a = Analysis(
    ['app.py'],
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

exe = EXE(
    pyz,
    a.scripts,
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
    icon=['static\\favicon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='aTrain',
)
