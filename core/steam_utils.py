import os
import subprocess
import sys
import time
import urllib.request
import requests

# winreg kütüphanesini sadece Windows'taysak içe aktar
if sys.platform == "win32":
    import winreg
else:
    winreg = None

# DLL dosyalarının indirileceği URL'ler
HID_DLL_URLS = [
    ("https://raw.githubusercontent.com/toprak1224/hid.dll/main/dwmapi.dll", "dwmapi.dll"),
    ("https://raw.githubusercontent.com/toprak1224/hid.dll/main/toprakcracker.dll", "toprakcracker.dll"),
]

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
    """HID DLL dosyalarını Steam klasöründen kaldırır. Kaldırılan dosya listesini döndürür."""
    steam_path = detect_steam_path()
    if not steam_path:
        return []

    if sys.platform == "win32":
        subprocess.run(['taskkill', '/F', '/IM', 'steam.exe'])
    else:
        subprocess.run(['pkill', '-f', 'steam'])

    time.sleep(2)

    removed = []
    for dll_name in ["dwmapi.dll", "toprakcracker.dll"]:
        dll_path = os.path.join(steam_path, dll_name)
        if os.path.exists(dll_path):
            os.remove(dll_path)
            removed.append(dll_name)
    return removed

def download_hid_dll(steam_path):
    """HID DLL dosyalarını steam_path'e indirir. Kaydedilen yolu döndürür."""
    for url, filename in HID_DLL_URLS:
        if not url:
            raise ValueError(f"{filename} için indirme URL'si yapılandırılmamış.")
        urllib.request.urlretrieve(url, os.path.join(steam_path, filename))
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
