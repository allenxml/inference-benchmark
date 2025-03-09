# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['logging_main.py'],  # 使用带日志记录的主文件
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'numpy',
        'aiohttp',
        'tqdm',
        'transformers',
        'cryptography',
        'psutil',
        'matplotlib',
        'matplotlib.backends.backend_tkagg'
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
    name='LLM基准测试工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
