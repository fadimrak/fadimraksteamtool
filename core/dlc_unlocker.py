"""
DLC Unlocker — Steam DLC Kilidi Kaldırma Modülü
================================================
Çalışma prensibi:
  - Steam Store API'den oyunun DLC listesi çekilir (appdetails endpoint).
  - İstenen DLC ID'leri Steam Lua scriptine (marcellus.lua) addappid(dlc_id, 1)
    satırı eklenerek Steam tarafına bildirilir.
  - DLC kaldırma: addappid satırı marcellus.lua'dan silinir.

Lua dosya konumu: <steam_path>/config/lua/marcellus.lua
"""

import os
import re
import requests

STORE_API_URL = "https://store.steampowered.com/api/appdetails"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr,en-US;q=0.9,en;q=0.8",
}


# ── DLC bilgisi çekme ─────────────────────────────────────────────

def fetch_dlc_list(app_id: str) -> dict:
    """
    Steam Store API'den oyunun DLC listesini çeker.
    Döndürür:
        {
            "ok": True,
            "game_name": "...",
            "dlc_list": [
                {"dlc_id": "123", "name": "DLC Adı", "description": "..."},
                ...
            ]
        }
    """
    app_id = str(app_id)
    try:
        r = requests.get(
            STORE_API_URL,
            params={"appids": app_id, "l": "turkish"},
            headers=HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return {"ok": False, "error": f"Steam API isteği başarısız: {e}"}

    if not data or app_id not in data or not data[app_id].get("success"):
        return {"ok": False, "error": "Oyun bilgisi alınamadı veya geçersiz App ID."}

    game_data  = data[app_id]["data"]
    game_name  = game_data.get("name", f"App {app_id}")
    raw_dlc    = game_data.get("dlc", [])

    if not raw_dlc:
        return {"ok": True, "game_name": game_name, "dlc_list": []}

    # DLC'lerin isimlerini tek seferde çek (batch API yok, tek tek çekiyoruz ama
    # makul bir sayıda DLC için timeout kısa tutulur)
    dlc_list = _fetch_dlc_names(raw_dlc)
    return {"ok": True, "game_name": game_name, "dlc_list": dlc_list}


def _fetch_dlc_names(dlc_ids: list, batch_size: int = 10) -> list:
    """
    DLC ID listesi için isim bilgisini Steam Store API'den paralel olarak çeker.
    Yüzlerce DLC'li oyunlarda tek tek istek yerine thread pool kullanır.
    """
    import concurrent.futures

    def fetch_one(dlc_id):
        return {"dlc_id": str(dlc_id), "name": _fetch_single_app_name(str(dlc_id))}

    result = []
    # Aynı anda en fazla 8 eşzamanlı istek
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_one, did): did for did in dlc_ids}
        for future in concurrent.futures.as_completed(futures):
            try:
                result.append(future.result())
            except Exception:
                did = str(futures[future])
                result.append({"dlc_id": did, "name": f"DLC {did}"})

    # Orijinal sırayı koru
    order = {str(d): i for i, d in enumerate(dlc_ids)}
    result.sort(key=lambda x: order.get(x["dlc_id"], 9999))
    return result


def _fetch_single_app_name(app_id: str) -> str:
    """Tek bir appid için isim çeker; başarısız olursa generic isim döner."""
    try:
        r = requests.get(
            STORE_API_URL,
            params={"appids": app_id, "filters": "basic", "l": "turkish"},
            headers=HEADERS,
            timeout=6,
        )
        data = r.json()
        if data and app_id in data and data[app_id].get("success"):
            return data[app_id]["data"].get("name", f"DLC {app_id}")
    except Exception:
        pass
    return f"DLC {app_id}"


# ── Lua dosyası okuma/yazma ───────────────────────────────────────

def _marcellus_path(steam_path: str) -> str:
    return os.path.join(steam_path, "config", "lua", "marcellus.lua")


def get_unlocked_dlcs(steam_path: str) -> set:
    """marcellus.lua'da addappid ile açılmış DLC ID setini döndürür."""
    path = _marcellus_path(steam_path)
    if not os.path.exists(path):
        return set()
    unlocked = set()
    pattern  = re.compile(r"addappid\((\d+)\s*,\s*1\)")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = pattern.search(line)
            if m:
                unlocked.add(m.group(1))
    return unlocked


def unlock_dlcs(steam_path: str, dlc_ids: list) -> dict:
    """
    Verilen DLC ID'lerini marcellus.lua'ya ekler.
    Zaten ekli olanları atlar.
    Döndürür: {"ok": True, "added": N, "skipped": M}
    """
    lua_dir = os.path.join(steam_path, "config", "lua")
    os.makedirs(lua_dir, exist_ok=True)

    path      = _marcellus_path(steam_path)
    existing  = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        pattern = re.compile(r"addappid\((\d+)\s*,\s*1\)")
        existing = set(pattern.findall(content))

    added   = 0
    skipped = 0
    try:
        with open(path, "a", encoding="utf-8") as f:
            for dlc_id in dlc_ids:
                sid = str(dlc_id)
                if sid in existing:
                    skipped += 1
                else:
                    f.write(f"addappid({sid}, 1)\n")
                    added += 1
    except Exception as e:
        return {"ok": False, "error": str(e)}

    return {"ok": True, "added": added, "skipped": skipped}


def lock_dlcs(steam_path: str, dlc_ids: list) -> dict:
    """
    Verilen DLC ID'lerini marcellus.lua'dan kaldırır.
    Döndürür: {"ok": True, "removed": N}
    """
    path = _marcellus_path(steam_path)
    if not os.path.exists(path):
        return {"ok": True, "removed": 0}

    target_ids = {str(d) for d in dlc_ids}
    pattern    = re.compile(r"addappid\((\d+)\s*,\s*1\)")
    removed    = 0

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            m = pattern.search(line)
            if m and m.group(1) in target_ids:
                removed += 1
            else:
                new_lines.append(line)

        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        return {"ok": False, "error": str(e)}

    return {"ok": True, "removed": removed}


def unlock_all_dlcs(steam_path: str, app_id: str) -> dict:
    """
    Oyunun tüm DLC'lerini çekip hepsini unlock eder.
    Döndürür: {"ok": True, "added": N, "skipped": M, "game_name": "..."}
    """
    result = fetch_dlc_list(app_id)
    if not result["ok"]:
        return result

    dlc_ids = [d["dlc_id"] for d in result["dlc_list"]]
    if not dlc_ids:
        return {
            "ok":        True,
            "added":     0,
            "skipped":   0,
            "game_name": result["game_name"],
            "msg":       "Bu oyunun DLC'si bulunamadı.",
        }

    unlock_result = unlock_dlcs(steam_path, dlc_ids)
    unlock_result["game_name"] = result["game_name"]
    unlock_result["total"]     = len(dlc_ids)
    return unlock_result
