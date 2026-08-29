"""
installer.py — Manifest indirme ve kurma modülü

İndirme kaynak önceliği (her biri başarısız olursa bir sonraki denenir):
  1. ManifestHub3      — steamtools-games/ManifestHub3   (raw .lua + key.vdf)
  2. steamtools.games  — POST /api/generate → ZIP
  3. SteamAutoCracks   — SteamAutoCracks/ManifestHub     (codeload branch ZIP)
  4. ManifestHub2      — SSMGAlt/ManifestHub2            (codeload branch ZIP)
"""

import os
import shutil
import zipfile
import tempfile
import requests

from config import MANIFEST_HUB_BASE_URL

# ── Sabitler ───────────────────────────────────────────────────────
MH3_RAW_BASE     = "https://raw.githubusercontent.com/steamtools-games/ManifestHub3"
MH3_API_BRANCH   = "https://api.github.com/repos/steamtools-games/ManifestHub3/branches/{app_id}"

ST_GENERATE_URL  = "https://steamtools.games/api/generate"
ST_SEARCH_URL    = "https://steamtools.games/api/search"

# SteamAutoCracks/ManifestHub  — branch = appId, ZIP via codeload
SAC_CODELOAD_BASE = "https://codeload.github.com/SteamAutoCracks/ManifestHub/zip/refs/heads/"
SAC_REFS_URL      = "https://github.com/SteamAutoCracks/ManifestHub.git/info/refs?service=git-upload-pack"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, */*",
}


# ── Yardımcılar ────────────────────────────────────────────────────

def _session():
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def generate_url(app_id):
    """ManifestHub2 (SSMGAlt) için codeload ZIP URL'si."""
    if not MANIFEST_HUB_BASE_URL:
        raise ValueError("MANIFEST_HUB_BASE_URL yapılandırılmamış (config.py).")
    return MANIFEST_HUB_BASE_URL + app_id


def _fetch_game_info(game_id, session=None):
    """Steam Store API'den oyun adı ve DLC listesini çeker."""
    game_name = f"Game {game_id}"
    dlc_ids   = []
    try:
        s = session or requests.Session()
        r = s.get(
            f"https://store.steampowered.com/api/appdetails?appids={game_id}",
            timeout=6,
        )
        data = r.json()
        if data and game_id in data and data[game_id].get("success"):
            gd        = data[game_id]["data"]
            game_name = gd.get("name", game_name)
            dlc_ids   = gd.get("dlc", [])
            if not isinstance(dlc_ids, list):
                dlc_ids = []
    except Exception:
        pass
    return game_name, dlc_ids


def _write_dlc_entries(lua_dir, dlc_ids):
    """marcellus.lua'ya addappid() satırları ekler. Eklenen sayısını döndürür."""
    marcellus = os.path.join(lua_dir, "marcellus.lua")
    existing  = []
    if os.path.exists(marcellus):
        with open(marcellus, "r", encoding="utf-8") as f:
            existing = f.readlines()
    added = 0
    with open(marcellus, "a", encoding="utf-8") as f:
        for dlc in dlc_ids:
            line = f"addappid({dlc}, 1)\n"
            if line not in existing:
                f.write(line)
                added += 1
    return added


# ── Kaynak 1: ManifestHub3 ────────────────────────────────────────

def _mh3_has_app(app_id, session):
    try:
        r = session.get(MH3_API_BRANCH.format(app_id=app_id), timeout=8)
        return r.status_code == 200
    except Exception:
        return False


def _mh3_download(app_id, lua_dir, depotcache_dir, session):
    os.makedirs(lua_dir,        exist_ok=True)
    os.makedirs(depotcache_dir, exist_ok=True)

    lua_url = f"{MH3_RAW_BASE}/{app_id}/{app_id}.lua"
    key_url = f"{MH3_RAW_BASE}/{app_id}/key.vdf"

    r = session.get(lua_url, timeout=15)
    r.raise_for_status()
    lua_name = f"{app_id}.lua"
    with open(os.path.join(lua_dir, lua_name), "wb") as f:
        f.write(r.content)
    lua_files      = [lua_name]
    manifest_files = []

    try:
        rk = session.get(key_url, timeout=10)
        if rk.status_code == 200:
            key_name = f"{app_id}_key.vdf"
            with open(os.path.join(depotcache_dir, key_name), "wb") as f:
                f.write(rk.content)
            manifest_files.append(key_name)
    except Exception:
        pass

    return lua_files, manifest_files


# ── Kaynak 2: steamtools.games ────────────────────────────────────

def _st_generate(app_id, session):
    r = session.post(
        ST_GENERATE_URL,
        json={"appId": str(app_id), "branch": "public"},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(f"steamtools.games: {data.get('message', 'bilinmeyen hata')}")
    return data["data"]


def _st_download_zip(app_id, session):
    info    = _st_generate(app_id, session)
    zip_url = info.get("downloadUrl") or info.get("luaUrl")
    if not zip_url:
        raise RuntimeError("steamtools.games: indirme URL'si yok")
    r = session.get(zip_url, timeout=30)
    r.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{app_id}_st.zip")
    tmp.write(r.content)
    tmp.close()
    return tmp.name


# ── Kaynak 3: SteamAutoCracks/ManifestHub ────────────────────────

def _sac_has_app(app_id, session):
    """SteamAutoCracks/ManifestHub'da bu app_id'ye ait branch var mı?"""
    try:
        r = session.get(SAC_REFS_URL, timeout=10)
        if r.status_code == 200:
            return f"refs/heads/{app_id}".encode() in r.content
    except Exception:
        pass
    return False


def _sac_download_zip(app_id, session):
    url = SAC_CODELOAD_BASE + app_id
    r   = session.get(url, timeout=30)
    r.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{app_id}_sac.zip")
    tmp.write(r.content)
    tmp.close()
    return tmp.name


# ── Kaynak 4: ManifestHub2 (SSMGAlt) ─────────────────────────────

def download_zip(app_id, timeout=30):
    """ManifestHub2'den (SSMGAlt) oyun ZIP'ini indirir."""
    url     = generate_url(app_id)
    session = _session()
    r       = session.get(url, timeout=timeout)
    r.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{app_id}.zip")
    tmp.write(r.content)
    tmp.close()
    return tmp.name


# ── Ana kurulum akışı ─────────────────────────────────────────────

def install_game(app_id, steam_path):
    """
    Oyunu sırayla 4 kaynaktan kurmaya çalışır:
      ManifestHub3 → steamtools.games → SteamAutoCracks → ManifestHub2

    Döndürür:
        {game_id, game_name, lua_count, manifest_count, dlc_count,
         lua_files, manifest_files, source}
    """
    lua_dir        = os.path.join(steam_path, "config", "lua")
    depotcache_dir = os.path.join(steam_path, "config", "depotcache")
    os.makedirs(lua_dir,        exist_ok=True)
    os.makedirs(depotcache_dir, exist_ok=True)

    session             = _session()
    game_name, dlc_ids  = _fetch_game_info(app_id, session)
    errors              = []

    # 1. ManifestHub3
    try:
        if _mh3_has_app(app_id, session):
            lua_files, manifest_files = _mh3_download(app_id, lua_dir, depotcache_dir, session)
            dlc_count = _write_dlc_entries(lua_dir, dlc_ids)
            return {
                "game_id": app_id, "game_name": game_name,
                "lua_count": len(lua_files), "manifest_count": len(manifest_files),
                "dlc_count": dlc_count,
                "lua_files": lua_files, "manifest_files": manifest_files,
                "source": "mh3",
            }
    except Exception as e:
        errors.append(f"MH3: {e}")

    # 2. steamtools.games
    tmp_zip = None
    try:
        tmp_zip = _st_download_zip(app_id, session)
        result  = _install_from_zip_path(tmp_zip, lua_dir, depotcache_dir, app_id, game_name, dlc_ids)
        result["source"] = "st"
        return result
    except Exception as e:
        errors.append(f"SteamTools: {e}")
    finally:
        _cleanup(tmp_zip)

    # 3. SteamAutoCracks/ManifestHub
    tmp_zip = None
    try:
        if _sac_has_app(app_id, session):
            tmp_zip = _sac_download_zip(app_id, session)
            result  = _install_from_zip_path(tmp_zip, lua_dir, depotcache_dir, app_id, game_name, dlc_ids)
            result["source"] = "sac"
            return result
    except Exception as e:
        errors.append(f"SAC: {e}")
    finally:
        _cleanup(tmp_zip)

    # 4. ManifestHub2 (SSMGAlt)
    tmp_zip = None
    try:
        tmp_zip = download_zip(app_id)
        result  = _install_from_zip_path(tmp_zip, lua_dir, depotcache_dir, app_id, game_name, dlc_ids)
        result["source"] = "mh2"
        return result
    except Exception as e:
        errors.append(f"MH2: {e}")
    finally:
        _cleanup(tmp_zip)

    raise RuntimeError("Oyun hiçbir kaynaktan indirilemedi. " + " | ".join(errors))


def _cleanup(path):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def _install_from_zip_path(zip_path, lua_dir, depotcache_dir, app_id, game_name, dlc_ids):
    lua_files      = []
    manifest_files = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            lower = name.lower()
            dest  = os.path.basename(name)
            if not dest:
                continue
            if lower.endswith(".lua"):
                with zf.open(name) as src, open(os.path.join(lua_dir, dest), "wb") as dst:
                    shutil.copyfileobj(src, dst)
                lua_files.append(dest)
            elif lower.endswith(".manifest"):
                with zf.open(name) as src, open(os.path.join(depotcache_dir, dest), "wb") as dst:
                    shutil.copyfileobj(src, dst)
                manifest_files.append(dest)

    dlc_count = _write_dlc_entries(lua_dir, dlc_ids)
    return {
        "game_id":        app_id,
        "game_name":      game_name,
        "lua_count":      len(lua_files),
        "manifest_count": len(manifest_files),
        "dlc_count":      dlc_count,
        "lua_files":      lua_files,
        "manifest_files": manifest_files,
    }


# ── Geriye dönük uyumluluk ────────────────────────────────────────

def install_from_zip(zip_path, steam_path, game_id=None):
    lua_dir        = os.path.join(steam_path, "config", "lua")
    depotcache_dir = os.path.join(steam_path, "config", "depotcache")
    os.makedirs(lua_dir,        exist_ok=True)
    os.makedirs(depotcache_dir, exist_ok=True)

    if game_id is None:
        base    = os.path.basename(zip_path)
        game_id = os.path.splitext(base)[0].split("_")[-1]
    if not str(game_id).isdigit():
        raise ValueError(game_id)

    game_name, dlc_ids = _fetch_game_info(str(game_id))
    result             = _install_from_zip_path(zip_path, lua_dir, depotcache_dir, str(game_id), game_name, dlc_ids)
    result["source"]   = "mh2"
    return result


def install_from_zip_ref(zip_ref, steam_path):
    lua_dir        = os.path.join(steam_path, "config", "lua")
    depotcache_dir = os.path.join(steam_path, "config", "depotcache")
    os.makedirs(lua_dir,        exist_ok=True)
    os.makedirs(depotcache_dir, exist_ok=True)
    lua_count = 0
    for name in zip_ref.namelist():
        if name.lower().endswith(".lua"):
            dest = os.path.basename(name)
            with zip_ref.open(name) as src, open(os.path.join(lua_dir, dest), "wb") as dst:
                shutil.copyfileobj(src, dst)
            lua_count += 1
    return lua_count, 0


def extract_zip_files(zip_path, steam_path):
    lua_dir        = os.path.join(steam_path, "config", "lua")
    depotcache_dir = os.path.join(steam_path, "config", "depotcache")
    os.makedirs(lua_dir,        exist_ok=True)
    os.makedirs(depotcache_dir, exist_ok=True)
    lua_count = manifest_count = 0
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name.endswith("/") or name.endswith("\\"):
                continue
            lower = name.lower()
            dest  = os.path.basename(name)
            if not dest:
                continue
            if lower.endswith(".lua"):
                with zf.open(name) as src, open(os.path.join(lua_dir, dest), "wb") as dst:
                    shutil.copyfileobj(src, dst)
                lua_count += 1
            elif lower.endswith(".manifest"):
                with zf.open(name) as src, open(os.path.join(depotcache_dir, dest), "wb") as dst:
                    shutil.copyfileobj(src, dst)
                manifest_count += 1
    return lua_count, manifest_count


def install_files(valid_files, steam_path):
    lua_dir        = os.path.join(steam_path, "config", "lua")
    depotcache_dir = os.path.join(steam_path, "config", "depotcache")
    os.makedirs(lua_dir,        exist_ok=True)
    os.makedirs(depotcache_dir, exist_ok=True)
    lua_count = manifest_count = 0
    for fp in valid_files:
        fname = os.path.basename(fp)
        if fname.lower().endswith(".lua"):
            shutil.copy2(fp, os.path.join(lua_dir,        fname)); lua_count      += 1
        elif fname.lower().endswith(".manifest"):
            shutil.copy2(fp, os.path.join(depotcache_dir, fname)); manifest_count += 1
    return lua_count, manifest_count


def remove_dlc_entries(lua_dir, dlc_ids):
    marcellus = os.path.join(lua_dir, "marcellus.lua")
    if not os.path.exists(marcellus):
        return
    with open(marcellus, "r", encoding="utf-8") as f:
        lines = f.readlines()
    new_lines = [
        line for line in lines
        if not any(f"addappid({did}," in line for did in dlc_ids)
    ]
    with open(marcellus, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
