# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[
        # steam_api64.dll — EXE ile aynı dizine koy
        ('steam_api64.dll', '.'),
    ],
    datas=[
        # UI dosyaları — _MEIPASS/static altına
        ('ui_web/static', 'static'),
        # Oyun arama cache (uygulama güncelleyebilir, başlangıç için gerekli)
        ('steam_app_list_cache.json', '.'),
        # Versiyon dosyası
        ('verison', '.'),
        # Temiz başlangıç ayarları (kullanıcı verisi yok)
        ('tsc_settings.json', '.'),
        # Temiz kurulu oyun listesi
        ('installed_games.json', '.'),
    ],
    hiddenimports=[
        # pywebview Windows backend'leri
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'clr',
        # requests bağımlılıkları
        'requests',
        'requests.adapters',
        'requests.auth',
        'requests.packages',
        'urllib3',
        'urllib3.util.retry',
        'urllib3.util.ssl_',
        'charset_normalizer',
        'idna',
        'certifi',
        # pystray Windows backend
        'pystray._win32',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        # concurrent.futures (dlc_unlocker paralel çekme)
        'concurrent.futures',
        'concurrent.futures.thread',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Gereksiz büyük kütüphaneler
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'test',
        'unittest',
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
    a.binaries,
    a.datas,
    [],
    name='FadimrakSteamTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        # UPX bu DLL'leri bozabilir
        'vcruntime140.dll',
        'python3*.dll',
        'steam_api64.dll',
    ],
    runtime_tmpdir=None,
    console=False,              # Pencere modu, konsol yok
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico',
    version_file=None,
)
