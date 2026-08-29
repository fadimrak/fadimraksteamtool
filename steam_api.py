"""
steam_api.py — Steam oyun listesi çekme ve cache yönetimi

Desteklenen oyun listesi kaynakları (öncelik sırasıyla):
  1. GitHub (jsnli/steamappidlist) — games + DLC JSON
  2. Steam Web API (ISteamApps/GetAppList/v2)
  3. SteamCMD API

Desteklenen oyun filtresi (ManifestHub3 + ManifestHub2):
  — ManifestHub3 (steamtools-games): GitHub Branches API → branch adı = appId
  — ManifestHub2 (SSMGAlt):          git refs smart-http → refs/heads/{appId}
  Yalnızca en az bir kaynakta branch'i olan oyunlar listeye alınır.
"""

import requests
import json
import os
import sys

from config import (
    STEAM_APP_LIST_CACHE_FILE,
    STEAM_APP_LIST_HEADERS,
    STEAM_APP_LIST_GITHUB_SOURCES,
    VERSION_CHECK_URL,
    MANIFEST_HUB_REFS_URL,
    MANIFEST_HUB3_REFS_URL,
    MANIFEST_HUB_SAC_REFS_URL,
)

# ── Ham veri ayıklayıcılar ─────────────────────────────────────────

def _extract_steam_web_api_apps(payload):
    if isinstance(payload, dict):
        return payload.get("applist", {}).get("apps", [])
    return []


def _extract_steamcmd_apps(payload):
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("apps"), list):
        return payload["apps"]
    data = payload.get("data")
    if isinstance(data, dict):
        if isinstance(data.get("apps"), list):
            return data["apps"]
        if isinstance(data.get("list"), list):
            return data["list"]
    return []


STEAM_APP_LIST_SOURCES = [
    {
        "name":    "steam_web_api",
        "url":     "https://api.steampowered.com/ISteamApps/GetAppList/v2/",
        "extract": _extract_steam_web_api_apps,
        "timeout": 45,
    },
    {
        "name":    "steamcmd_api",
        "url":     "https://api.steamcmd.net/v1/apps",
        "extract": _extract_steamcmd_apps,
        "timeout": 45,
    },
]

# ── Normalizasyon ──────────────────────────────────────────────────

def _normalize_app_entries(entries):
    normalized = {}
    id_keys   = ("appid", "app_id", "appID", "id", "appId", "game_id")
    name_keys = ("name", "Name", "title", "app_name", "AppName", "label")

    for item in entries or []:
        app_id = name = None

        if isinstance(item, dict):
            for k in id_keys:
                if item.get(k):
                    app_id = item[k]; break
            for k in name_keys:
                if item.get(k):
                    name = item[k]; break
        elif isinstance(item, (int, float)):
            app_id = int(item)
        elif isinstance(item, str) and item.isdigit():
            app_id = item

        if app_id is None:
            continue
        app_id = str(app_id)
        if not app_id.isdigit():
            continue
        if not name:
            name = normalized.get(app_id, f"App {app_id}")
        normalized[app_id] = name

    return [{"appid": aid, "name": n} for aid, n in sorted(normalized.items(), key=lambda p: int(p[0]))]

# ── Cache ──────────────────────────────────────────────────────────

def _load_cached_app_list():
    try:
        path = STEAM_APP_LIST_CACHE_FILE
        if not os.path.exists(path) and getattr(sys, "frozen", False):
            bundle = os.path.join(sys._MEIPASS, "steam_app_list_cache.json")
            if os.path.exists(bundle):
                path = bundle
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if isinstance(cached, list):
                valid = [e for e in cached if "appid" in e and "name" in e]
                if valid:
                    return valid
    except Exception:
        pass
    return []


def _save_app_list_cache(apps):
    try:
        with open(STEAM_APP_LIST_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(apps, f, ensure_ascii=False)
    except Exception:
        pass

# ── Versiyon kontrolü ──────────────────────────────────────────────

def fetch_latest_version(session=None):
    if not VERSION_CHECK_URL:
        return None
    session = session or requests.Session()
    r = session.get(VERSION_CHECK_URL, headers=STEAM_APP_LIST_HEADERS, timeout=15)
    r.raise_for_status()
    return r.text.strip()

# ── GitHub kaynaklarından oyun listesi ────────────────────────────

def _fetch_github_app_lists(session):
    combined = []
    errors   = []

    for src in STEAM_APP_LIST_GITHUB_SOURCES:
        try:
            r = session.get(src["url"], headers=STEAM_APP_LIST_HEADERS, timeout=60)
            r.raise_for_status()
            normalized = _normalize_app_entries(r.json())
            suffix = src.get("name_suffix", "")
            if suffix:
                for e in normalized:
                    e["name"] = f"{e.get('name', '')}{suffix}".strip()
            combined.extend(normalized)
        except Exception as exc:
            errors.append(f"{src['name']}: {exc}")

    if combined:
        unique = {}
        for e in combined:
            aid = e.get("appid")
            if aid:
                unique[aid] = e
        return list(unique.values())

    if errors:
        raise RuntimeError("; ".join(errors))
    return []

# ── Desteklenen oyun filtresi ──────────────────────────────────────

def _get_mh3_supported_ids(session):
    """
    ManifestHub3 (steamtools-games) için desteklenen App ID'leri döndürür.
    GitHub REST API /branches endpoint'ini kullanır.
    """
    if not MANIFEST_HUB3_REFS_URL:
        return set()
    try:
        # GitHub API sayfalandırmalı; 100'lük parçalarla tüm branch'leri çekiyoruz
        ids = set()
        page = 1
        while True:
            r = session.get(
                MANIFEST_HUB3_REFS_URL,
                params={"per_page": 100, "page": page},
                headers={**STEAM_APP_LIST_HEADERS, "Accept": "application/vnd.github+json"},
                timeout=20,
            )
            if r.status_code != 200:
                break
            data = r.json()
            if not isinstance(data, list) or not data:
                break
            for branch in data:
                name = branch.get("name", "")
                if name.isdigit():
                    ids.add(name)
            if len(data) < 100:
                break
            page += 1
        return ids
    except Exception:
        return set()


def _get_mh2_supported_ids(session):
    """
    ManifestHub2 (SSMGAlt) için git smart-http refs'den desteklenen ID'leri döndürür.
    """
    if not MANIFEST_HUB_REFS_URL:
        return set()
    try:
        r = session.get(MANIFEST_HUB_REFS_URL, timeout=15)
        r.raise_for_status()
        ids = set()
        for line in r.text.split("\n"):
            if "refs/heads/" in line:
                branch = line.split("refs/heads/")[-1].strip()
                if branch != "main" and branch.isdigit():
                    ids.add(branch)
        return ids
    except Exception:
        return set()


def _get_sac_supported_ids(session):
    """SteamAutoCracks/ManifestHub için desteklenen ID'leri döndürür."""
    if not MANIFEST_HUB_SAC_REFS_URL:
        return set()
    try:
        r = session.get(MANIFEST_HUB_SAC_REFS_URL, timeout=15)
        r.raise_for_status()
        ids = set()
        for line in r.text.split("\n"):
            if "refs/heads/" in line:
                branch = line.split("refs/heads/")[-1].strip()
                if branch != "main" and branch.isdigit():
                    ids.add(branch)
        return ids
    except Exception:
        return set()


def _filter_supported_games(apps, session):
    """
    MH3 + MH2 + SAC kaynaklarının birleşik desteklenen ID seti ile filtreler.
    """
    mh3_ids = _get_mh3_supported_ids(session)
    mh2_ids = _get_mh2_supported_ids(session)
    sac_ids = _get_sac_supported_ids(session)
    all_ids = mh3_ids | mh2_ids | sac_ids

    if not all_ids:
        return apps

    return [app for app in apps if str(app.get("appid")) in all_ids]

# ── Ana fonksiyon ──────────────────────────────────────────────────

def fetch_steam_app_list(session=None):
    cached = _load_cached_app_list()
    if cached and len(cached) > 50000:
        return cached

    session = session or requests.Session()
    errors  = []

    try:
        github_apps = _fetch_github_app_lists(session)
        if github_apps:
            filtered = _filter_supported_games(github_apps, session)
            _save_app_list_cache(filtered)
            return filtered
    except Exception as exc:
        errors.append(f"github_sources: {exc}")

    for src in STEAM_APP_LIST_SOURCES:
        try:
            r = session.get(src["url"], headers=STEAM_APP_LIST_HEADERS, timeout=src.get("timeout", 30))
            r.raise_for_status()
            apps = _normalize_app_entries(src["extract"](r.json()))
            if apps:
                filtered = _filter_supported_games(apps, session)
                _save_app_list_cache(filtered)
                return filtered
        except Exception as exc:
            errors.append(f"{src['name']}: {exc}")

    raise RuntimeError("Steam oyun listesi alınamadı. Kaynaklar: " + "; ".join(errors))
