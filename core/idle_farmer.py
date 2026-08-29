"""
Idle Farmer — Steam Kart ve Saat Kasma Motoru
=============================================
Referans: https://github.com/JustArchiNET/ArchiSteamFarm & Steamworks SDK

Bu modül:
  - Her oyun için izole edilmiş bir alt işlem (subprocess worker) başlatır.
  - Her worker kendi izole çalışma klasöründe (temp dir) steam_appid.txt ve ortam değişkenlerini ayarlar.
  - steam_api64.dll üzerinden SteamAPI_InitSafe / SteamAPI_InitFlat ile Steam istemcisine bağlanır.
  - ISteamUserStats::RequestUserStats ile oyun istatistik / oynama oturumunu Steam'e tescil eder.
  - Steam client bu oyunun "Oynuyor" (in-game) olduğunu algılar → saat ve kart kasmaya başlar.
  - Birden fazla oyun çakışma olmadan aynı anda bağımsız olarak kasılabilir.
"""

import os
import sys
import json
import shutil
import subprocess
import threading
import time
import tempfile
import ctypes
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html, */*",
}

CARD_EXCHANGE_URL = "https://www.steamcardexchange.net/api/request.php"
STORE_APPDETAILS  = "https://store.steampowered.com/api/appdetails"


# ── DLL Bulucu ────────────────────────────────────────────────────────────────

def find_steam_api_dll(custom_path: str = "", project_dir: str = "") -> str | None:
    """steam_api64.dll dosyasını olası tüm konumlarda arar."""
    candidates = []

    # 1. PyInstaller MEIPASS dizini
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "steam_api64.dll"))

    # 2. Proje / EXE dizini
    if project_dir:
        candidates.append(os.path.join(project_dir, "steam_api64.dll"))
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        candidates.append(os.path.join(exe_dir, "steam_api64.dll"))
    else:
        file_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.append(os.path.join(file_dir, "steam_api64.dll"))

    # 3. Özel Steam yolu
    if custom_path:
        candidates.append(os.path.join(custom_path, "steam_api64.dll"))
        candidates.append(os.path.join(custom_path, "steamapps", "common"))

    # 4. Standart Steam kurulum dizinleri
    candidates += [
        r"C:\Program Files (x86)\Steam\steam_api64.dll",
        r"C:\Program Files\Steam\steam_api64.dll",
    ]

    for p in candidates:
        if os.path.isfile(p):
            return os.path.abspath(p)
        if os.path.isdir(p):
            try:
                for root, dirs, files in os.walk(p):
                    if "steam_api64.dll" in files:
                        return os.path.abspath(os.path.join(root, "steam_api64.dll"))
                    if root.count(os.sep) - p.count(os.sep) > 3:
                        break
            except Exception:
                pass
    return None


# ── Idle Worker Core Logic ───────────────────────────────────────────────────

def run_worker(argv: list[str]) -> None:
    """
    Subprocess içinde çalışan idle worker ana fonksiyonu.
    Argümanlar:
      [0]: app_id
      [1]: custom_path
      [2]: stop_file
      [3]: worker_dir (izole temp dizini)
      [4]: project_dir
    """
    app_id      = argv[0] if len(argv) > 0 else "0"
    custom_path = argv[1] if len(argv) > 1 else ""
    stop_file   = argv[2] if len(argv) > 2 else ""
    worker_dir  = argv[3] if len(argv) > 3 else ""
    project_dir = argv[4] if len(argv) > 4 else ""

    app_id_str = str(app_id).strip()

    # İzole çalışma dizini hazırla
    if not worker_dir or not os.path.isdir(worker_dir):
        worker_dir = tempfile.mkdtemp(prefix=f"tsc_idle_{app_id_str}_")

    appid_txt = os.path.join(worker_dir, "steam_appid.txt")
    try:
        with open(appid_txt, "w", encoding="utf-8") as f:
            f.write(app_id_str)
    except Exception:
        pass

    # Çalışma dizinini izole klasöre taşı
    try:
        os.chdir(worker_dir)
    except Exception:
        pass

    # Win32 OS Ortam Değişkenleri (Steam client & steam_api64.dll doğrudan okur)
    if sys.platform == "win32":
        try:
            k32 = ctypes.windll.kernel32
            k32.SetEnvironmentVariableW("SteamAppId", app_id_str)
            k32.SetEnvironmentVariableW("SteamGameId", app_id_str)
            k32.SetEnvironmentVariableW("SteamOverlayGameId", app_id_str)
        except Exception:
            pass

    os.environ["SteamAppId"]         = app_id_str
    os.environ["SteamGameId"]        = app_id_str
    os.environ["SteamOverlayGameId"] = app_id_str

    dll_path = find_steam_api_dll(custom_path, project_dir)
    dll = None
    init_success = False

    if dll_path and os.path.exists(dll_path):
        try:
            dll = ctypes.CDLL(dll_path)

            # 1. SteamAPI_InitSafe
            init_safe = getattr(dll, "SteamAPI_InitSafe", None)
            if init_safe:
                try:
                    init_safe.restype = ctypes.c_bool
                    if init_safe():
                        init_success = True
                except Exception:
                    pass

            # 2. SteamAPI_InitFlat
            if not init_success:
                init_flat = getattr(dll, "SteamAPI_InitFlat", None)
                if init_flat:
                    try:
                        init_flat.restype = ctypes.c_int
                        err_buf = ctypes.create_string_buffer(1024)
                        if init_flat(err_buf) == 0:
                            init_success = True
                    except Exception:
                        pass

            # 3. SteamAPI_Init
            if not init_success:
                init_fn = getattr(dll, "SteamAPI_Init", None)
                if init_fn:
                    try:
                        init_fn.restype = ctypes.c_bool
                        if init_fn():
                            init_success = True
                    except Exception:
                        pass

            # 4. Steam oturumunu tam olarak aktifleştir (RequestUserStats & SteamUser)
            if init_success:
                try:
                    # SteamUser -> SteamID al
                    user_fn = (
                        getattr(dll, "SteamAPI_SteamUser_v023", None) or
                        getattr(dll, "SteamAPI_SteamUser_v022", None) or
                        getattr(dll, "SteamAPI_SteamUser_v021", None) or
                        getattr(dll, "SteamUser", None)
                    )
                    steam_id = 0
                    if user_fn:
                        user_fn.restype = ctypes.c_void_p
                        user_ptr = user_fn()
                        sid_fn = getattr(dll, "SteamAPI_ISteamUser_GetSteamID", None)
                        if sid_fn and user_ptr:
                            sid_fn.restype  = ctypes.c_uint64
                            sid_fn.argtypes = [ctypes.c_void_p]
                            steam_id = sid_fn(user_ptr)

                    # SteamUserStats -> RequestUserStats
                    sus_fn = (
                        getattr(dll, "SteamAPI_SteamUserStats_v013", None) or
                        getattr(dll, "SteamAPI_SteamUserStats_v012", None) or
                        getattr(dll, "SteamAPI_SteamUserStats_v011", None) or
                        getattr(dll, "SteamUserStats", None)
                    )
                    if sus_fn:
                        sus_fn.restype = ctypes.c_void_p
                        sus_ptr = sus_fn()
                        if sus_ptr and steam_id:
                            req_fn = getattr(dll, "SteamAPI_ISteamUserStats_RequestUserStats", None)
                            if req_fn:
                                req_fn.restype  = ctypes.c_uint64
                                req_fn.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
                                req_fn(sus_ptr, steam_id)
                except Exception:
                    pass

        except Exception:
            dll = None
            init_success = False

    # Callbacks döngüsü ve durdurma sinyali bekleme
    rcb = getattr(dll, "SteamAPI_RunCallbacks", None) if dll else None
    try:
        while True:
            # Durdurma dosyası kontrolü
            if stop_file and os.path.exists(stop_file):
                break

            # Steam callbacks çağrısı (her 1 saniyede bir)
            if rcb and init_success:
                try:
                    rcb()
                except Exception:
                    pass

            time.sleep(1.0)
    finally:
        # Graceful shutdown
        if dll and init_success:
            try:
                shutdown_fn = getattr(dll, "SteamAPI_Shutdown", None)
                if shutdown_fn:
                    shutdown_fn()
            except Exception:
                pass

        # Temizlik
        try:
            if stop_file and os.path.exists(stop_file):
                os.remove(stop_file)
        except Exception:
            pass

        try:
            if os.path.exists(worker_dir):
                shutil.rmtree(worker_dir, ignore_errors=True)
        except Exception:
            pass


# ── Standalone Worker Script (Fallback) ───────────────────────────────────────

_WORKER_SCRIPT_STANDALONE = r"""
import sys
import os
import time
import shutil
import tempfile
import ctypes

def main():
    app_id      = sys.argv[1] if len(sys.argv) > 1 else "0"
    custom_path = sys.argv[2] if len(sys.argv) > 2 else ""
    stop_file   = sys.argv[3] if len(sys.argv) > 3 else ""
    worker_dir  = sys.argv[4] if len(sys.argv) > 4 else ""
    project_dir = sys.argv[5] if len(sys.argv) > 5 else ""

    app_id_str = str(app_id).strip()

    if not worker_dir or not os.path.isdir(worker_dir):
        worker_dir = tempfile.mkdtemp(prefix=f"tsc_idle_{app_id_str}_")

    appid_txt = os.path.join(worker_dir, "steam_appid.txt")
    try:
        with open(appid_txt, "w", encoding="utf-8") as f:
            f.write(app_id_str)
    except Exception:
        pass

    try:
        os.chdir(worker_dir)
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            k32 = ctypes.windll.kernel32
            k32.SetEnvironmentVariableW("SteamAppId", app_id_str)
            k32.SetEnvironmentVariableW("SteamGameId", app_id_str)
            k32.SetEnvironmentVariableW("SteamOverlayGameId", app_id_str)
        except Exception:
            pass

    os.environ["SteamAppId"]         = app_id_str
    os.environ["SteamGameId"]        = app_id_str
    os.environ["SteamOverlayGameId"] = app_id_str

    candidates = []
    if project_dir:
        candidates.append(os.path.join(project_dir, "steam_api64.dll"))
    if custom_path:
        candidates.append(os.path.join(custom_path, "steam_api64.dll"))
        candidates.append(os.path.join(custom_path, "steamapps", "common"))
    candidates += [
        r"C:\Program Files (x86)\Steam\steam_api64.dll",
        r"C:\Program Files\Steam\steam_api64.dll",
    ]

    dll_path = None
    for p in candidates:
        if os.path.isfile(p):
            dll_path = p
            break
        if os.path.isdir(p):
            try:
                for root, dirs, files in os.walk(p):
                    if "steam_api64.dll" in files:
                        dll_path = os.path.join(root, "steam_api64.dll")
                        break
                    if root.count(os.sep) - p.count(os.sep) > 3:
                        break
            except Exception:
                pass
        if dll_path:
            break

    dll = None
    init_success = False

    if dll_path and os.path.exists(dll_path):
        try:
            dll = ctypes.CDLL(dll_path)
            init_safe = getattr(dll, "SteamAPI_InitSafe", None)
            if init_safe:
                try:
                    init_safe.restype = ctypes.c_bool
                    if init_safe():
                        init_success = True
                except Exception:
                    pass

            if not init_success:
                init_flat = getattr(dll, "SteamAPI_InitFlat", None)
                if init_flat:
                    try:
                        init_flat.restype = ctypes.c_int
                        err_buf = ctypes.create_string_buffer(1024)
                        if init_flat(err_buf) == 0:
                            init_success = True
                    except Exception:
                        pass

            if init_success:
                try:
                    user_fn = getattr(dll, "SteamAPI_SteamUser_v023", None) or getattr(dll, "SteamUser", None)
                    steam_id = 0
                    if user_fn:
                        user_fn.restype = ctypes.c_void_p
                        user_ptr = user_fn()
                        sid_fn = getattr(dll, "SteamAPI_ISteamUser_GetSteamID", None)
                        if sid_fn and user_ptr:
                            sid_fn.restype  = ctypes.c_uint64
                            sid_fn.argtypes = [ctypes.c_void_p]
                            steam_id = sid_fn(user_ptr)

                    sus_fn = getattr(dll, "SteamAPI_SteamUserStats_v013", None) or getattr(dll, "SteamUserStats", None)
                    if sus_fn and steam_id:
                        sus_fn.restype = ctypes.c_void_p
                        sus_ptr = sus_fn()
                        req_fn = getattr(dll, "SteamAPI_ISteamUserStats_RequestUserStats", None)
                        if req_fn and sus_ptr:
                            req_fn.restype  = ctypes.c_uint64
                            req_fn.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
                            req_fn(sus_ptr, steam_id)
                except Exception:
                    pass
        except Exception:
            pass

    rcb = getattr(dll, "SteamAPI_RunCallbacks", None) if dll else None
    try:
        while True:
            if stop_file and os.path.exists(stop_file):
                break
            if rcb and init_success:
                try:
                    rcb()
                except Exception:
                    pass
            time.sleep(1.0)
    finally:
        if dll and init_success:
            try:
                shutdown_fn = getattr(dll, "SteamAPI_Shutdown", None)
                if shutdown_fn:
                    shutdown_fn()
            except Exception:
                pass
        try:
            if stop_file and os.path.exists(stop_file):
                os.remove(stop_file)
        except Exception:
            pass
        try:
            if os.path.exists(worker_dir):
                shutil.rmtree(worker_dir, ignore_errors=True)
        except Exception:
            pass

if __name__ == "__main__":
    main()
"""

def _prepare_worker_script() -> str:
    """Worker scriptini temp dizine yazar, yolunu döner."""
    tmp_dir  = tempfile.gettempdir()
    script_p = os.path.join(tmp_dir, "tsc_idle_worker.py")
    try:
        with open(script_p, "w", encoding="utf-8") as f:
            f.write(_WORKER_SCRIPT_STANDALONE)
    except Exception:
        pass
    return script_p


# ── IdleFarmer Sınıfı ────────────────────────────────────────────────────────

class IdleFarmer:
    """
    Steam Oyun/Kart Kasma Motoru.
    Her oyun için izole edilmiş ayrı subprocess başlatır, Steam'e "Oynuyor" sinyali gönderir.
    """

    def __init__(self):
        self._lock        = threading.Lock()
        self._running: dict[str, dict] = {}
        self._worker_path = _prepare_worker_script()
        if getattr(sys, "frozen", False):
            self._project_dir = os.path.dirname(sys.executable)
        else:
            self._project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _make_stop_file(self, app_id: str) -> str:
        return os.path.join(tempfile.gettempdir(), f"tsc_idle_{app_id}.stop")

    def start_idle(self, app_id: str, game_name: str = "", steam_path: str = "") -> dict:
        """Oyun için kasma işlemini başlatır."""
        app_id = str(app_id).strip()
        if not app_id or not app_id.isdigit():
            return {"ok": False, "error": f"Geçersiz App ID: {app_id}"}

        with self._lock:
            if app_id in self._running:
                proc = self._running[app_id]["proc"]
                if proc.poll() is None:
                    elapsed = int(time.time() - self._running[app_id]["start_time"])
                    return {"ok": False, "error": "Bu oyun zaten kasılıyor.", "elapsed": elapsed}
                else:
                    del self._running[app_id]

        stop_file = self._make_stop_file(app_id)
        if os.path.exists(stop_file):
            try:
                os.remove(stop_file)
            except Exception:
                pass

        # Her worker için benzersiz izole geçici klasör
        worker_temp_dir = tempfile.mkdtemp(prefix=f"tsc_idle_{app_id}_")
        appid_txt = os.path.join(worker_temp_dir, "steam_appid.txt")
        try:
            with open(appid_txt, "w", encoding="utf-8") as f:
                f.write(app_id)
        except Exception:
            pass

        # Komut satırı argümanları
        if getattr(sys, "frozen", False):
            # Derlenmiş tek EXE modu: Kendi executable'ımızı CLI argümanıyla çağırıyoruz
            cmd = [
                sys.executable,
                "--idle-worker",
                app_id,
                steam_path or "",
                stop_file,
                worker_temp_dir,
                self._project_dir,
            ]
        else:
            main_script = os.path.join(self._project_dir, "main.py")
            if os.path.isfile(main_script):
                cmd = [
                    sys.executable,
                    main_script,
                    "--idle-worker",
                    app_id,
                    steam_path or "",
                    stop_file,
                    worker_temp_dir,
                    self._project_dir,
                ]
            else:
                cmd = [
                    sys.executable,
                    self._worker_path,
                    app_id,
                    steam_path or "",
                    stop_file,
                    worker_temp_dir,
                    self._project_dir,
                ]

        env = os.environ.copy()
        env["SteamAppId"]         = app_id
        env["SteamGameId"]        = app_id
        env["SteamOverlayGameId"] = app_id

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                env=env,
                cwd=worker_temp_dir,
                creationflags=(subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0),
            )
        except Exception as e:
            try:
                shutil.rmtree(worker_temp_dir, ignore_errors=True)
            except Exception:
                pass
            return {"ok": False, "error": f"Kasma işlemi başlatılamadı: {e}"}

        with self._lock:
            self._running[app_id] = {
                "proc":            proc,
                "start_time":      time.time(),
                "name":            game_name or f"App {app_id}",
                "steam_path":      steam_path,
                "stop_file":       stop_file,
                "worker_temp_dir": worker_temp_dir,
            }

        return {"ok": True, "app_id": app_id, "name": game_name or f"App {app_id}"}

    def stop_idle(self, app_id: str) -> dict:
        """Oyunun kasma işlemini durdurur."""
        app_id = str(app_id).strip()

        with self._lock:
            entry = self._running.get(app_id)

        if not entry:
            return {"ok": False, "error": "Bu oyun kasılmıyor."}

        stop_file       = entry.get("stop_file") or self._make_stop_file(app_id)
        worker_temp_dir = entry.get("worker_temp_dir", "")
        proc            = entry["proc"]
        elapsed         = int(time.time() - entry["start_time"])

        # Önce stop_file ile düzgün kapanmasını iste (SteamAPI_Shutdown çalışsın)
        try:
            with open(stop_file, "w", encoding="utf-8") as f:
                f.write("stop")
        except Exception:
            pass

        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=1)
            except Exception:
                proc.kill()

        try:
            if os.path.exists(stop_file):
                os.remove(stop_file)
        except Exception:
            pass

        try:
            if worker_temp_dir and os.path.exists(worker_temp_dir):
                shutil.rmtree(worker_temp_dir, ignore_errors=True)
        except Exception:
            pass

        with self._lock:
            self._running.pop(app_id, None)

        return {"ok": True, "app_id": app_id, "elapsed_seconds": elapsed}

    def stop_all(self) -> dict:
        """Tüm kasılan oyunları durdurur."""
        with self._lock:
            ids = list(self._running.keys())
        stopped = []
        for aid in ids:
            r = self.stop_idle(aid)
            if r.get("ok"):
                stopped.append(aid)
        return {"ok": True, "stopped": stopped}

    def get_status(self) -> list[dict]:
        """Aktif kasılan oyun listesini döndürür."""
        now = time.time()
        result = []
        with self._lock:
            for app_id, entry in list(self._running.items()):
                proc  = entry["proc"]
                alive = proc.poll() is None
                if not alive:
                    # Temizlik
                    wdir = entry.get("worker_temp_dir", "")
                    if wdir and os.path.exists(wdir):
                        shutil.rmtree(wdir, ignore_errors=True)
                    del self._running[app_id]
                    continue
                elapsed = int(now - entry["start_time"])
                result.append({
                    "app_id":          app_id,
                    "name":            entry["name"],
                    "elapsed_seconds": elapsed,
                    "elapsed_min":     elapsed // 60,
                    "alive":           True,
                })
        return result

    def is_idling(self, app_id: str) -> bool:
        with self._lock:
            entry = self._running.get(str(app_id).strip())
            if not entry:
                return False
            return entry["proc"].poll() is None

    def get_elapsed(self, app_id: str) -> int:
        with self._lock:
            entry = self._running.get(str(app_id).strip())
            if not entry:
                return 0
        return int(time.time() - entry["start_time"])


# ── Singleton ─────────────────────────────────────────────────────────────────
_farmer_instance: IdleFarmer | None = None
_farmer_lock = threading.Lock()


def get_farmer() -> IdleFarmer:
    global _farmer_instance
    with _farmer_lock:
        if _farmer_instance is None:
            _farmer_instance = IdleFarmer()
        return _farmer_instance


# ── Kart Bilgisi ──────────────────────────────────────────────────────────────
_card_cache: dict[str, dict] = {}
_card_cache_lock = threading.Lock()

def get_card_info(app_id: int | str, steam_id: str = "", api_key: str = "") -> dict:
    """Tek oyun için kart drop ve kalan hak bilgisi."""
    app_id = str(app_id).strip()

    # 1. Bağlı hesap varsa kullanıcının gerçek kalan kart hakkını kontrol et
    if steam_id and api_key:
        try:
            from core.steam_account import get_badge_remaining_cards
            rem = get_badge_remaining_cards(steam_id, api_key, app_id)
            if rem > 0:
                return {"has_cards": True, "card_count": rem, "cards_remaining": rem, "has_drops": True}
            else:
                return {"has_cards": False, "card_count": 0, "cards_remaining": 0, "has_drops": False}
        except Exception:
            pass

    with _card_cache_lock:
        if app_id in _card_cache:
            return _card_cache[app_id]

    # 2. Steam Store categories API
    try:
        r = requests.get(
            STORE_APPDETAILS,
            params={"appids": app_id, "filters": "categories"},
            headers=HEADERS,
            timeout=5,
        )
        if r.status_code == 200:
            data = r.json().get(str(app_id), {})
            if data.get("success"):
                cats = data.get("data", {}).get("categories", [])
                has_cards = any(c.get("id") == 29 for c in cats)
                res = {"has_cards": has_cards, "card_count": 0, "cards_remaining": 0, "has_drops": has_cards}
                with _card_cache_lock:
                    _card_cache[app_id] = res
                return res
    except Exception:
        pass

    res = {"has_cards": False, "card_count": 0, "cards_remaining": 0, "has_drops": False}
    with _card_cache_lock:
        _card_cache[app_id] = res
    return res


def get_cards_batch(app_ids: list[str], steam_id: str = "", api_key: str = "") -> dict:
    """Birden fazla oyun için paralel kart bilgisi."""
    results: dict = {}

    if steam_id and api_key:
        try:
            from core.steam_account import get_all_badges_map
            badge_map = get_all_badges_map(steam_id, api_key)
            for aid in app_ids:
                aid_str = str(aid).strip()
                rem = badge_map.get(aid_str, 0)
                if rem > 0:
                    results[aid_str] = {"has_cards": True, "card_count": rem, "cards_remaining": rem, "has_drops": True}
                else:
                    results[aid_str] = {"has_cards": False, "card_count": 0, "cards_remaining": 0, "has_drops": False}
            return results
        except Exception:
            pass

    lock = threading.Lock()
    from concurrent.futures import ThreadPoolExecutor
    def _fetch(aid):
        info = get_card_info(aid)
        with lock:
            results[str(aid)] = info

    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(_fetch, app_ids)

    return results


def format_elapsed(seconds: int) -> str:
    """Saniyeyi okunabilir formata çevirir."""
    seconds = max(0, int(seconds))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h} sa {m} dk {s} sn"
    if m > 0:
        return f"{m} dk {s} sn"
    return f"{s} sn"
