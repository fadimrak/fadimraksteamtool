import os
import subprocess
import sys
import time
import shutil
import requests

# winreg kütüphanesini sadece Windows'taysak içe aktar
if sys.platform == "win32":
    import winreg
else:
    winreg = None

# DLL dosyalarının indirme bağlantıları (fadimrak resmi repo)
DLL_DOWNLOAD_URLS = [
    ("https://github.com/fadimrak/dlls/raw/refs/heads/main/dwmapi.dll", "dwmapi.dll"),
    ("https://github.com/fadimrak/dlls/raw/refs/heads/main/fadimrak.dll", "fadimrak.dll"),
]
DLL_FILES = ["dwmapi.dll", "fadimrak.dll"]
LEGACY_DLL_FILES = ["xinput1_4.dll"]

def _get_dll_build_dir():
    """Derlenmiş DLL'lerin bulunduğu yerel build dizinini döndürür."""
    if getattr(sys, '_MEIPASS', None):
        return sys._MEIPASS
    here = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(here)
    return os.path.join(project_root, "steamapishowcase", "build")

def detect_steam_path():
    """Steam kurulum yolunu döndürür, bulunamazsa None."""
    if sys.platform == "win32":
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Valve\\Steam") as key:
                path = winreg.QueryValueEx(key, "InstallPath")[0]
                if os.path.exists(path):
                    return path
        except Exception:
            pass

        common_paths = [
            os.path.expanduser("~") + "\\Program Files (x86)\\Steam",
            os.path.expanduser("~") + "\\Program Files\\Steam",
            "C:\\Program Files (x86)\\Steam",
            "C:\\Program Files\\Steam",
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
    else:
        # Linux / CachyOS üzerindeki Steam yolları
        linux_paths = [
            os.path.expanduser("~/.local/share/Steam"),
            os.path.expanduser("~/.steam/steam"),
            os.path.expanduser("~/.var/app/com.valvesoftware.Steam/data/Steam")  # Flatpak Steam
        ]
        for path in linux_paths:
            if os.path.exists(path):
                return path

    return None

def get_lua_dir(steam_path):
    """Steam lua klasör yolunu döndürür."""
    return os.path.join(steam_path, 'config', 'lua') if steam_path else ""

def restart_steam(steam_path):
    """Steam'i kapatıp yeniden başlatır."""
    if sys.platform == "win32":
        steam_exe = os.path.join(steam_path, 'steam.exe')
        if not os.path.isfile(steam_exe):
            raise FileNotFoundError(steam_exe)
        subprocess.run(['taskkill', '/F', '/IM', 'steam.exe'])
        subprocess.Popen([steam_exe])
    else:
        # Linux üzerinde Steam kapatma ve başlatma
        subprocess.run(['pkill', '-f', 'steam'])
        time.sleep(1)
        subprocess.Popen(['steam'])

def remove_hid_dll():
    """DLL dosyalarını Steam klasöründen kaldırır. Kaldırılan dosya listesini döndürür."""
    steam_path = detect_steam_path()
    if not steam_path:
        return []

    if sys.platform == "win32":
        subprocess.run(['taskkill', '/F', '/IM', 'steam.exe'])
    else:
        subprocess.run(['pkill', '-f', 'steam'])

    time.sleep(2)

    removed = []
    for dll_name in DLL_FILES + LEGACY_DLL_FILES:
        dll_path = os.path.join(steam_path, dll_name)
        if os.path.exists(dll_path):
            try:
                os.remove(dll_path)
                removed.append(dll_name)
            except Exception:
                pass
    return removed

def download_hid_dll(steam_path):
    """DLL dosyalarını fadimrak resmi GitHub reposundan steam_path'e indirir (yerel fallback ile)."""
    # Steam çalışıyorsa DLL kilitli olabilir, kapatmayı dene
    if sys.platform == "win32":
        subprocess.run(['taskkill', '/F', '/IM', 'steam.exe'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

    # Eski DLL'leri temizle (varsa)
    for legacy in LEGACY_DLL_FILES:
        legacy_path = os.path.join(steam_path, legacy)
        if os.path.exists(legacy_path):
            try:
                os.remove(legacy_path)
            except Exception:
                pass

    for url, filename in DLL_DOWNLOAD_URLS:
        dst = os.path.join(steam_path, filename)
        downloaded = False
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 1000:
                with open(dst, "wb") as f:
                    f.write(resp.content)
                downloaded = True
        except Exception:
            downloaded = False

        # İnternet/bağlantı hatası durumunda yerel build'den kopyala (fallback)
        if not downloaded:
            build_dir = _get_dll_build_dir()
            src = os.path.join(build_dir, filename)
            if os.path.exists(src):
                shutil.copy2(src, dst)
            else:
                raise RuntimeError(f"{filename} indirilemedi ve yerel yedek bulunamadı.")

    return steam_path

def get_dlc_ids(app_id):
    """Steam API'den oyunun DLC ID listesini çeker."""
    try:
        response = requests.get(
            f'https://store.steampowered.com/api/appdetails?appids={app_id}',
            timeout=5
        )
        dlc_ids = response.json().get(str(app_id), {}).get('data', {}).get('dlc', [])
        return dlc_ids if isinstance(dlc_ids, list) else []
    except Exception:
        return []
