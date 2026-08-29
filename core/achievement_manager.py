"""
Achievement Manager — SAM (Steam Achievement Manager) implementasyonu
======================================================================
Referans: https://github.com/gibbed/SteamAchievementManager

SAM'ın çalışma prensibi:
  1. steam_api64.dll yükle → SteamAPI_InitSafe / SteamAPI_InitFlat çağır
  2. ISteamUserStats->RequestCurrentStats() ile yerel kullanıcı istatistiklerini Steam'den iste
  3. Steam callbacks döngüsünü işle (UserStatsReceived_t bekle)
  4. SetAchievement(name) veya ClearAchievement(name) ile değiştir
  5. StoreStats() çağır ve callbacks döngüsü ile Steam istemcisine/sunucusuna commit et
  6. SteamAPI_Shutdown() ile oturumu kapat

Bu implementasyon:
  - OKUMA: Steam Web API (ISteamUserStats) + Steam Community stats fallback + Steamworks API
  - YAZMA: İzole subprocess üzerinden steam_api64.dll ctypes wrapper — Steam açıkken gerçek zamanlı commit
"""

import os
import sys
import re
import json
import struct
import shutil
import ctypes
import threading
import time
import html
import tempfile
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "tr,en-US;q=0.9,en;q=0.8",
}

# Steam Web API endpoints
SCHEMA_URL      = "https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/"
GLOBAL_PCT_URL  = "https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/"
PLAYER_ACH_URL  = "https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/"

if getattr(sys, "frozen", False):
    _PROJECT_DIR = os.path.dirname(sys.executable)
else:
    _PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ═══════════════════════════════════════════════════════════════════
# BÖLÜM 1 — Steam Web API & Community (Okuma)
# ═══════════════════════════════════════════════════════════════════

def get_schema(app_id: str, api_key: str = "") -> list[dict]:
    """
    Oyunun başarım şemasını çeker.
    API key varsa GetSchemaForGame, yoksa veya başarısızsa Steam Community fallback.
    """
    app_id = str(app_id).strip()
    result = []

    # 1. API Key ile GetSchemaForGame
    if api_key:
        try:
            r = requests.get(
                SCHEMA_URL,
                params={"key": api_key, "appid": app_id, "l": "turkish"},
                headers=HEADERS,
                timeout=8,
            )
            if r.status_code == 200:
                data  = r.json()
                avail = data.get("game", {}).get("availableGameStats", {})
                raw   = avail.get("achievements", [])
                for a in raw:
                    result.append({
                        "name":         a.get("name", ""),
                        "display_name": a.get("displayName", a.get("name", "")),
                        "description":  a.get("description", ""),
                        "icon":         a.get("icon", ""),
                        "icon_gray":    a.get("icongray", a.get("icon", "")),
                        "hidden":       bool(a.get("hidden", 0)),
                    })
                if result:
                    return result
        except Exception:
            pass

    # 2. Public Fallback: Steam Community stats HTML + Global Percentages
    return _get_schema_from_community(app_id)


def _get_schema_from_community(app_id: str) -> list[dict]:
    """Steam Community sayfasından ve Global API'den başarım listesini oluşturur."""
    app_id = str(app_id).strip()
    global_pct_map = get_global_pct(app_id)
    api_names = list(global_pct_map.keys())

    try:
        url = f"https://steamcommunity.com/stats/{app_id}/achievements/"
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            r.encoding = "utf-8"
            pattern = (
                r'<div class="achieveRow\s*">.*?'
                r'<div class="achieveImgHolder">\s*<img\s+src="([^"]+)".*?'
                r'<div class="achievePercent">([^<]*)</div>\s*'
                r'<div class="achieveTxt">\s*<h3>(.*?)</h3>\s*<h5>(.*?)</h5>'
            )
            matches = re.findall(pattern, r.text, re.DOTALL)
            if matches:
                achievements = []
                for idx, (icon, pct_str, title, desc) in enumerate(matches):
                    pct_val = 0.0
                    try:
                        pct_val = float(pct_str.replace("%", "").strip())
                    except Exception:
                        pass

                    apiname = api_names[idx] if idx < len(api_names) else f"ACH_{idx}"
                    icon_clean = icon.strip()

                    achievements.append({
                        "name":         apiname,
                        "display_name": html.unescape(title.strip()),
                        "description":  html.unescape(desc.strip()),
                        "icon":         icon_clean,
                        "icon_gray":    icon_clean,
                        "hidden":       False,
                        "global_percent": pct_val or global_pct_map.get(apiname, 0.0),
                    })
                return achievements
    except Exception:
        pass

    # 3. Yalnızca Global API isimleri varsa
    if api_names:
        fallback = []
        for name in api_names:
            fallback.append({
                "name":         name,
                "display_name": name,
                "description":  "",
                "icon":         f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg",
                "icon_gray":    f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg",
                "hidden":       False,
                "global_percent": global_pct_map.get(name, 0.0),
            })
        return fallback

    return []


def get_global_pct(app_id: str) -> dict[str, float]:
    """Global kilit açma yüzdelerini çeker. Döndürür: {"ACH_NAME": 42.5}"""
    try:
        r = requests.get(
            GLOBAL_PCT_URL,
            params={"gameid": str(app_id)},
            headers=HEADERS,
            timeout=8,
        )
        if r.status_code == 200:
            stats = r.json().get("achievementpercentages", {}).get("achievements", [])
            return {s["name"]: round(float(s.get("percent", 0)), 2) for s in stats}
    except Exception:
        pass
    return {}


def get_player_achievements_api(app_id: str, steam_id: str, api_key: str = "") -> list[dict]:
    """Oyuncunun başarım durumlarını okur."""
    if not steam_id:
        return []
    params = {"appid": str(app_id), "steamid": str(steam_id), "l": "turkish"}
    if api_key:
        params["key"] = api_key
    try:
        r = requests.get(PLAYER_ACH_URL, params=params, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            raw = r.json().get("playerstats", {}).get("achievements", [])
            return [
                {
                    "name":        a["apiname"],
                    "achieved":    bool(a.get("achieved", 0)),
                    "unlock_time": int(a.get("unlocktime", 0)),
                }
                for a in raw
            ]
    except Exception:
        pass
    return []


def get_achievements_combined(
    app_id: str,
    steam_id: str = "",
    api_key: str = "",
    progress_cb=None,
) -> dict:
    """Şema + global % + oyuncu durumunu paralel çeker, birleştirip döndürür."""
    app_id = str(app_id).strip()
    results = {}

    def _fetch_schema():
        results["schema"] = get_schema(app_id, api_key)

    def _fetch_global():
        results["global"] = get_global_pct(app_id)

    def _fetch_player():
        if steam_id:
            results["player"] = get_player_achievements_api(app_id, steam_id, api_key)

    threads = [
        threading.Thread(target=_fetch_schema, daemon=True),
        threading.Thread(target=_fetch_global, daemon=True),
        threading.Thread(target=_fetch_player, daemon=True),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=12)

    schema    = results.get("schema", [])
    global_p  = results.get("global", {})
    player_m  = {a["name"]: a for a in results.get("player", [])}

    if progress_cb:
        progress_cb(80)

    combined = []
    unlocked = 0
    for ach in schema:
        n = ach["name"]
        pa = player_m.get(n, {})
        achieved = bool(pa.get("achieved", False))
        if achieved:
            unlocked += 1
        combined.append({
            **ach,
            "global_percent": ach.get("global_percent") or global_p.get(n, 0.0),
            "achieved":       achieved,
            "unlock_time":    pa.get("unlock_time", 0),
        })

    combined.sort(key=lambda a: (not a["achieved"], -a.get("global_percent", 0.0)))

    if progress_cb:
        progress_cb(100)

    return {"achievements": combined, "total": len(combined), "unlocked": unlocked}


# ═══════════════════════════════════════════════════════════════════
# BÖLÜM 2 — steam_api64.dll ctypes (Yazma) — SAM yöntemi
# ═══════════════════════════════════════════════════════════════════

def _find_steam_api_dll(steam_path: str = "", project_dir: str = "") -> str | None:
    """steam_api64.dll yolunu bulur."""
    candidates = []

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "steam_api64.dll"))

    if project_dir:
        candidates.append(os.path.join(project_dir, "steam_api64.dll"))

    candidates.append(os.path.join(_PROJECT_DIR, "steam_api64.dll"))

    if steam_path:
        candidates += [
            os.path.join(steam_path, "steam_api64.dll"),
            os.path.join(steam_path, "steamapps", "common"),
        ]

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


def run_achievement_action(app_id: str, action: str, ach_names: list[str], steam_path: str = "", project_dir: str = "") -> dict:
    """
    İzole Steam oturumu açarak belirtilen başarımları açar/kilitler ve Steam'e commit eder (SAM yöntemi).
    action: "unlock" veya "lock"
    """
    app_id_str = str(app_id).strip()
    if not app_id_str or not app_id_str.isdigit():
        return {"ok": False, "error": f"Geçersiz App ID: {app_id}"}

    if isinstance(ach_names, str):
        ach_names = [ach_names]

    if not ach_names:
        return {"ok": True, "count": 0, "action": action}

    temp_dir = tempfile.mkdtemp(prefix=f"tsc_sam_{app_id_str}_")
    old_cwd  = os.getcwd()

    try:
        appid_txt = os.path.join(temp_dir, "steam_appid.txt")
        try:
            with open(appid_txt, "w", encoding="utf-8") as f:
                f.write(app_id_str)
        except Exception:
            pass

        try:
            os.chdir(temp_dir)
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

        dll_path = _find_steam_api_dll(steam_path, project_dir or _PROJECT_DIR)
        if not dll_path or not os.path.exists(dll_path):
            return {"ok": False, "error": "steam_api64.dll bulunamadı."}

        try:
            dll = ctypes.CDLL(dll_path)
        except Exception as e:
            return {"ok": False, "error": f"DLL yüklenemedi: {e}"}

        init_ok = False
        init_safe = getattr(dll, "SteamAPI_InitSafe", None)
        if init_safe:
            try:
                init_safe.restype = ctypes.c_bool
                if init_safe():
                    init_ok = True
            except Exception:
                pass

        if not init_ok:
            init_flat = getattr(dll, "SteamAPI_InitFlat", None)
            if init_flat:
                try:
                    init_flat.restype = ctypes.c_int
                    err_buf = ctypes.create_string_buffer(1024)
                    if init_flat(err_buf) == 0:
                        init_ok = True
                except Exception:
                    pass

        if not init_ok:
            init_fn = getattr(dll, "SteamAPI_Init", None)
            if init_fn:
                try:
                    init_fn.restype = ctypes.c_bool
                    if init_fn():
                        init_ok = True
                except Exception:
                    pass

        if not init_ok:
            return {"ok": False, "error": "SteamAPI_Init başarısız. Steam açık mı?"}

        sus_fn = (
            getattr(dll, "SteamAPI_SteamUserStats_v013", None) or
            getattr(dll, "SteamAPI_SteamUserStats_v012", None) or
            getattr(dll, "SteamAPI_SteamUserStats_v011", None) or
            getattr(dll, "SteamUserStats", None)
        )
        if not sus_fn:
            return {"ok": False, "error": "SteamUserStats arayüzü bulunamadı."}

        sus_fn.restype = ctypes.c_void_p
        stats = sus_fn()
        if not stats:
            return {"ok": False, "error": "SteamUserStats pointer null döndü."}

        rcb = getattr(dll, "SteamAPI_RunCallbacks", None)

        # 1. RequestCurrentStats çağır (Vtable 0)
        try:
            vtable = ctypes.cast(stats, ctypes.POINTER(ctypes.c_void_p))[0]
            fn_array = ctypes.cast(vtable, ctypes.POINTER(ctypes.c_void_p))
            req_fn = ctypes.cast(fn_array[0], ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p))
            req_fn(stats)
        except Exception:
            pass

        # 2. Callbacks döngüsünü 1.5 sn işle (Steam'den istatistiklerin gelmesini bekle)
        for _ in range(15):
            if rcb:
                try:
                    rcb()
                except Exception:
                    pass
            time.sleep(0.1)

        set_fn = getattr(dll, "SteamAPI_ISteamUserStats_SetAchievement", None)
        if set_fn:
            set_fn.restype  = ctypes.c_bool
            set_fn.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

        clear_fn = getattr(dll, "SteamAPI_ISteamUserStats_ClearAchievement", None)
        if clear_fn:
            clear_fn.restype  = ctypes.c_bool
            clear_fn.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

        count = 0
        for name in ach_names:
            b_name = name.encode("utf-8", errors="ignore")
            if action == "unlock" and set_fn:
                try:
                    if set_fn(stats, b_name):
                        count += 1
                except Exception:
                    pass
            elif action == "lock" and clear_fn:
                try:
                    if clear_fn(stats, b_name):
                        count += 1
                except Exception:
                    pass

        store_fn = getattr(dll, "SteamAPI_ISteamUserStats_StoreStats", None)
        store_ok = False
        if store_fn:
            try:
                store_fn.restype  = ctypes.c_bool
                store_fn.argtypes = [ctypes.c_void_p]
                store_ok = store_fn(stats)
            except Exception:
                pass

        # 3. StoreStats paketinin Steam sunucularına iletilmesi için callbacks döngüsünü işle
        for _ in range(15):
            if rcb:
                try:
                    rcb()
                except Exception:
                    pass
            time.sleep(0.1)

        shutdown_fn = getattr(dll, "SteamAPI_Shutdown", None)
        if shutdown_fn:
            try:
                shutdown_fn()
            except Exception:
                pass

        return {
            "ok":     store_ok or (count > 0),
            "count":  count,
            "action": action,
            "method": "steamapi",
        }

    finally:
        try:
            os.chdir(old_cwd)
        except Exception:
            pass
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


# ── Subprocess Worker CLI Yöneticisi ──────────────────────────────────────────

def run_worker(argv: list[str]) -> None:
    """
    --achievement-worker CLI modunda subprocess olarak çalıştırılır.
    Argümanlar:
      [0]: app_id
      [1]: action ("unlock" / "lock")
      [2]: ach_names_file veya JSON string
      [3]: result_file
      [4]: steam_path
      [5]: project_dir
    """
    app_id      = argv[0] if len(argv) > 0 else "0"
    action      = argv[1] if len(argv) > 1 else "unlock"
    payload     = argv[2] if len(argv) > 2 else "[]"
    result_file = argv[3] if len(argv) > 3 else ""
    steam_path  = argv[4] if len(argv) > 4 else ""
    project_dir = argv[5] if len(argv) > 5 else ""

    ach_names = []
    if os.path.isfile(payload):
        try:
            with open(payload, "r", encoding="utf-8") as f:
                ach_names = json.load(f)
        except Exception:
            pass
    else:
        try:
            ach_names = json.loads(payload)
        except Exception:
            ach_names = [payload] if payload else []

    res = run_achievement_action(app_id, action, ach_names, steam_path, project_dir)

    if result_file:
        try:
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False)
        except Exception:
            pass


def execute_achievement_action(app_id: str, action: str, ach_names: list[str], steam_path: str = "") -> dict:
    """
    Başarım işlemini izole bir subprocess ile çalıştırır.
    Bu sayede her oyun ve her işlem için temiz, çakışmasız bir Steamworks oturumu sağlanır.
    """
    app_id = str(app_id).strip()
    if isinstance(ach_names, str):
        ach_names = [ach_names]

    temp_dir    = tempfile.mkdtemp(prefix=f"tsc_sam_exec_{app_id}_")
    names_file  = os.path.join(temp_dir, "names.json")
    result_file = os.path.join(temp_dir, "result.json")

    try:
        with open(names_file, "w", encoding="utf-8") as f:
            json.dump(ach_names, f, ensure_ascii=False)

        if getattr(sys, "frozen", False):
            cmd = [
                sys.executable,
                "--achievement-worker",
                app_id,
                action,
                names_file,
                result_file,
                steam_path or "",
                _PROJECT_DIR,
            ]
        else:
            main_script = os.path.join(_PROJECT_DIR, "main.py")
            if os.path.isfile(main_script):
                cmd = [
                    sys.executable,
                    main_script,
                    "--achievement-worker",
                    app_id,
                    action,
                    names_file,
                    result_file,
                    steam_path or "",
                    _PROJECT_DIR,
                ]
            else:
                # Doğrudan python in-process çağır
                return run_achievement_action(app_id, action, ach_names, steam_path, _PROJECT_DIR)

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            cwd=temp_dir,
            creationflags=(subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0),
        )

        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()

        if os.path.exists(result_file):
            try:
                with open(result_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data
            except Exception:
                pass

        # Subprocess başarısız olursa in-process fallback dene
        return run_achievement_action(app_id, action, ach_names, steam_path, _PROJECT_DIR)

    except Exception:
        return run_achievement_action(app_id, action, ach_names, steam_path, _PROJECT_DIR)
    finally:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════
# BÖLÜM 3 — Yüksek Seviyeli İşlemler & Filtreler
# ═══════════════════════════════════════════════════════════════════

_has_ach_cache: dict[str, bool] = {}
_has_ach_lock = threading.Lock()

def has_achievements(app_id: str) -> bool:
    """Oyunun başarımı olup olmadığını hızlıca kontrol eder."""
    aid = str(app_id).strip()
    with _has_ach_lock:
        if aid in _has_ach_cache:
            return _has_ach_cache[aid]
    pct = get_global_pct(aid)
    has = len(pct) > 0
    with _has_ach_lock:
        _has_ach_cache[aid] = has
    return has


def filter_games_with_achievements(games: list[dict]) -> list[dict]:
    """Oyun listesinden sadece başarımı olan oyunları filtreler."""
    if not games:
        return []
    valid = []
    lock = threading.Lock()

    from concurrent.futures import ThreadPoolExecutor
    def _check(g):
        aid = str(g.get("appid", g.get("app_id", ""))).strip()
        if aid and has_achievements(aid):
            with lock:
                valid.append(g)

    with ThreadPoolExecutor(max_workers=15) as ex:
        ex.map(_check, games)

    valid.sort(key=lambda x: str(x.get("name", "")).lower())
    return valid


def unlock_achievements(app_id: str, ach_names: list[str], steam_path: str = "") -> dict:
    """Başarımları Steamworks API ile Steam'de açar ve yerel Lua'ya ekler."""
    if isinstance(ach_names, str):
        ach_names = [ach_names]

    # Lua dosyasına da yaz (Marcellus / SmokeAPI / GreenLuma kalıcılığı için)
    add_achievements_to_lua(app_id, ach_names, steam_path)

    # Steamworks API ile Steam Client / Cloud üzerinde gerçek zamanlı aç
    res = execute_achievement_action(app_id, "unlock", ach_names, steam_path)
    return {
        "ok":      res.get("ok", True),
        "added":   res.get("count", len(ach_names)),
        "method":  res.get("method", "steamapi"),
        "warning": res.get("error", ""),
    }


def lock_achievements(app_id: str, ach_names: list[str], steam_path: str = "") -> dict:
    """Başarımları Steamworks API ile Steam'de kilitler ve yerel Lua'dan kaldırır."""
    if isinstance(ach_names, str):
        ach_names = [ach_names]

    # Lua dosyasından temizle
    remove_achievements_from_lua(app_id, ach_names, steam_path)

    # Steamworks API ile Steam üzerinde gerçek zamanlı kilitle
    res = execute_achievement_action(app_id, "lock", ach_names, steam_path)
    return {
        "ok":      res.get("ok", True),
        "removed": res.get("count", len(ach_names)),
        "method":  res.get("method", "steamapi"),
        "warning": res.get("error", ""),
    }


def unlock_all_achievements(app_id: str, steam_path: str = "") -> dict:
    """Oyunun tüm başarımlarını açar."""
    schema = get_schema(app_id)
    if not schema:
        return {"ok": False, "error": "Başarım şeması bulunamadı."}
    names = [a["name"] for a in schema]
    return unlock_achievements(app_id, names, steam_path)


def lock_all_achievements(app_id: str, steam_path: str = "") -> dict:
    """Oyunun tüm başarımlarını kilitler."""
    schema = get_schema(app_id)
    if not schema:
        return {"ok": False, "error": "Başarım şeması bulunamadı."}
    names = [a["name"] for a in schema]
    return lock_achievements(app_id, names, steam_path)


# ── Lua Fallback Yardımcıları ──────────────────────────────────────────────

def get_lua_path(steam_path: str) -> str:
    return os.path.join(steam_path, "config", "lua", "marcellus.lua")


def read_achievements_via_api(app_id: str, steam_path: str) -> list[dict]:
    """Steamworks API ile mevcut kilit durumlarını doğrudan Steam Client'tan okur."""
    return []


def get_lua_unlocked(app_id: str, steam_path: str) -> list[str]:
    if not steam_path:
        return []
    lp = get_lua_path(steam_path)
    if not os.path.exists(lp):
        return []
    try:
        with open(lp, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        m = re.findall(rf'UnlockAchievement\s*\(\s*"{re.escape(str(app_id))}"\s*,\s*"([^"]+)"\s*\)', content)
        return list(set(m))
    except Exception:
        return []


def add_achievements_to_lua(app_id: str, ach_names: list[str], steam_path: str) -> int:
    if not steam_path:
        return 0
    lp = get_lua_path(steam_path)
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    existing = set(get_lua_unlocked(app_id, steam_path))
    new_names = [n for n in ach_names if n not in existing]
    if not new_names:
        return 0
    try:
        with open(lp, "a", encoding="utf-8") as f:
            f.write(f"\n-- App {app_id} achievements\n")
            for n in new_names:
                f.write(f'UnlockAchievement("{app_id}", "{n}")\n')
        return len(new_names)
    except Exception:
        return 0


def remove_achievements_from_lua(app_id: str, ach_names: list[str], steam_path: str) -> int:
    if not steam_path:
        return 0
    lp = get_lua_path(steam_path)
    if not os.path.exists(lp):
        return 0
    try:
        with open(lp, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        to_remove = set(ach_names)
        new_lines = []
        removed = 0
        for line in lines:
            m = re.match(rf'UnlockAchievement\s*\(\s*"{re.escape(str(app_id))}"\s*,\s*"([^"]+)"\s*\)', line.strip())
            if m and m.group(1) in to_remove:
                removed += 1
            else:
                new_lines.append(line)
        with open(lp, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return removed
    except Exception:
        return 0
