"""
Steam Hesap Yöneticisi
======================
ASF'ın yaptığı gibi Steam Web API üzerinden kullanıcının gerçek kütüphanesini çeker.

Referans: https://github.com/JustArchiNET/ArchiSteamFarm
API Dok: https://partner.steamgames.com/doc/webapi/IPlayerService

Giriş mantığı:
  - Kullanıcı Steam Web API Key girer (store.steampowered.com/dev/apikey)
  - Kullanıcı Steam64 ID girer VEYA profil URL'sinden otomatik çözümlenir
  - API Key + Steam64 ID ile IPlayerService/GetOwnedGames çağrısı yapılır
  - Oyun listesi cache'lenir (steam_owned_cache.json)

Neden API Key?
  - GetOwnedGames endpoint'i private profilleri okumak için key zorunlu tutar.
  - ASF de bot config'de SteamOwnerID + API key kombinasyonu kullanır.
  - Key olmadan yalnızca public profiller okunabilir (include_appinfo kısıtlı).
"""

import os
import re
import json
import time
import threading
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept":     "application/json",
}

# ── Endpoint'ler ──────────────────────────────────────────────────────────────
OWNED_GAMES_URL     = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
PLAYER_SUMMARY_URL  = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
RESOLVE_VANITY_URL  = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/"
BADGE_DATA_URL      = "https://api.steampowered.com/IPlayerService/GetBadges/v1/"
CARD_EXCHANGE_URL   = "https://www.steamcardexchange.net/api/request.php"
STORE_APPDETAILS    = "https://store.steampowered.com/api/appdetails"

# ── Cache dosyası ──────────────────────────────────────────────────────────────
if getattr(__import__("sys"), "frozen", False):
    _BASE_DIR = os.path.dirname(__import__("sys").executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OWNED_CACHE_FILE = os.path.join(_BASE_DIR, "steam_owned_cache.json")
CACHE_TTL        = 1800  # 30 dakika


# ── Yardımcı Fonksiyonlar ─────────────────────────────────────────────────────

def resolve_steam_id(steam_id_or_url: str, api_key: str = "") -> str | None:
    """
    Steam64 ID, profil URL'si veya vanity URL'sini 64-bit Steam ID'ye çevirir.

    Örnekler:
      "76561198123456789"        → aynen döner
      "https://steamcommunity.com/id/username" → vanity çözer
      "https://steamcommunity.com/profiles/76561198123456789" → doğrudan ID
      "username"                 → vanity çözer

    Döndürür: "76561198123456789" veya None
    """
    s = steam_id_or_url.strip()
    if not s:
        return None

    # Doğrudan 64-bit Steam ID (17 haneli rakam)
    if re.fullmatch(r"\d{17}", s):
        return s

    # /profiles/76561...
    m = re.search(r"/profiles/(\d{17})", s)
    if m:
        return m.group(1)

    # /id/vanityname
    m = re.search(r"/id/([^/]+)/?$", s)
    vanity = m.group(1) if m else s

    # ResolveVanityURL
    try:
        params = {"vanityurl": vanity}
        if api_key:
            params["key"] = api_key
        r = requests.get(RESOLVE_VANITY_URL, params=params, headers=HEADERS, timeout=8)
        data = r.json()
        resp = data.get("response", {})
        if resp.get("success") == 1:
            return str(resp["steamid"])
    except Exception:
        pass

    return None


def get_player_summary(steam_id: str, api_key: str) -> dict:
    """
    Oyuncu profil özetini getirir: isim, avatar, profil linki.
    Döndürür: {"name": str, "avatar": str, "profile_url": str, "steam_id": str}
    """
    try:
        r = requests.get(
            PLAYER_SUMMARY_URL,
            params={"key": api_key, "steamids": steam_id},
            headers=HEADERS,
            timeout=8,
        )
        data   = r.json()
        player = data.get("response", {}).get("players", [{}])[0]
        return {
            "name":        player.get("personaname", f"User {steam_id}"),
            "avatar":      player.get("avatarfull", player.get("avatarmedium", "")),
            "profile_url": player.get("profileurl", ""),
            "steam_id":    steam_id,
        }
    except Exception:
        return {"name": f"User {steam_id}", "avatar": "", "profile_url": "", "steam_id": steam_id}


# ── Kütüphane Çekme ───────────────────────────────────────────────────────────

def _load_owned_cache() -> dict | None:
    """Cache dosyasını yükler, TTL dolmuşsa None döner."""
    if not os.path.exists(OWNED_CACHE_FILE):
        return None
    try:
        with open(OWNED_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - data.get("_cached_at", 0) > CACHE_TTL:
            return None
        return data
    except Exception:
        return None


def _save_owned_cache(steam_id: str, games: list[dict]):
    """Kütüphane listesini cache'e kaydeder."""
    try:
        with open(OWNED_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"steam_id": steam_id, "games": games, "_cached_at": time.time()},
                f,
                indent=2,
                ensure_ascii=False,
            )
    except Exception:
        pass


def get_owned_games(steam_id: str, api_key: str, force_refresh: bool = False) -> list[dict]:
    """
    IPlayerService/GetOwnedGames ile kullanıcının gerçek Steam kütüphanesini çeker.
    ASF'ın yaptığı gibi include_appinfo=true ile isim ve icon da gelir.

    Döndürür: [{"appid": int, "name": str, "playtime_forever": int, "cover": str}, ...]
    """
    # Cache kontrolü
    if not force_refresh:
        cached = _load_owned_cache()
        if cached and cached.get("steam_id") == steam_id and cached.get("games"):
            return cached["games"]

    params = {
        "key":                       api_key,
        "steamid":                   steam_id,
        "include_appinfo":           True,
        "include_played_free_games": True,
        "format":                    "json",
    }

    try:
        r = requests.get(OWNED_GAMES_URL, params=params, headers=HEADERS, timeout=15)
        r.raise_for_status()
        data  = r.json()
        raw   = data.get("response", {}).get("games", [])

        games = []
        for g in raw:
            app_id = g.get("appid")
            if not app_id:
                continue
            name = g.get("name") or f"App {app_id}"
            games.append({
                "appid":            app_id,
                "name":             name,
                "playtime_forever": g.get("playtime_forever", 0),   # dakika cinsinden
                "playtime_2weeks":  g.get("playtime_2weeks", 0),
                "cover":            f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg",
            })

        # Oyun adına göre sırala
        games.sort(key=lambda x: x["name"].lower())

        _save_owned_cache(steam_id, games)
        return games

    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 403:
            raise PermissionError(
                "Steam API erişimi reddedildi. API key geçersiz veya profil gizli olabilir."
            )
        raise RuntimeError(f"Steam API hatası: {e}")
    except requests.RequestException as e:
        raise RuntimeError(f"Ağ hatası: {e}")


def get_owned_games_with_card_info(
    steam_id: str,
    api_key: str,
    progress_cb=None,
    force_refresh: bool = False,
) -> list[dict]:
    """
    Kütüphaneyi çekip kart bilgisi (has_cards, card_count) ekler.
    Ağır işlem — progress_cb(pct) ile ilerleme bildirir.
    """
    games = get_owned_games(steam_id, api_key, force_refresh)
    total = len(games)

    if progress_cb:
        progress_cb(20)

    # Kart bilgilerini paralel çek
    results_lock = threading.Lock()
    card_map: dict[int, dict] = {}

    def _fetch_card(game):
        app_id = game["appid"]
        info   = _get_card_info_fast(app_id)
        with results_lock:
            card_map[app_id] = info

    # Paralel çekme — en fazla 20 thread aynı anda
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(_fetch_card, games)

    if progress_cb:
        progress_cb(80)

    # Sonuçları birleştir
    result = []
    for g in games:
        info = card_map.get(g["appid"], {"has_cards": False, "card_count": 0})
        result.append({**g, **info})

    if progress_cb:
        progress_cb(100)

    return result


def _get_card_info_fast(app_id: int) -> dict:
    """
    Tek oyun için hızlı kart bilgisi çekme.
    steamcardexchange.net veya Steam Store categories API.
    """
    # 1. steamcardexchange.net
    try:
        r = requests.get(
            CARD_EXCHANGE_URL,
            params={"appid": app_id},
            headers=HEADERS,
            timeout=5,
        )
        data = r.json()
        if data.get("status") == "success":
            card_count = int(data.get("data", {}).get("card_count", 0))
            return {"has_cards": True, "card_count": card_count}
    except Exception:
        pass

    # 2. Steam Store categories
    try:
        r = requests.get(
            STORE_APPDETAILS,
            params={"appids": app_id, "filters": "categories"},
            headers=HEADERS,
            timeout=5,
        )
        data = r.json().get(str(app_id), {})
        if data.get("success"):
            cats      = data["data"].get("categories", [])
            has_cards = any(c.get("id") == 29 for c in cats)
            return {"has_cards": has_cards, "card_count": 0}
    except Exception:
        pass

    return {"has_cards": False, "card_count": 0}


# ── Badge / Remaining Cards (Kart Düşürme Hakkı) ──────────────────────────────

_badge_cache: dict[str, dict] = {}
_badge_cache_time: float = 0
_badge_lock = threading.Lock()

def get_all_badges_map(steam_id: str, api_key: str, force_refresh: bool = False) -> dict[str, int]:
    """
    Kullanıcının tüm rozetlerini çekerek kalan kart düşürme haklarını döner.
    Döndürür: {"440": 3, "730": 0, ...}
    """
    global _badge_cache, _badge_cache_time
    with _badge_lock:
        if not force_refresh and _badge_cache and (time.time() - _badge_cache_time < 300):
            return dict(_badge_cache)

    if not steam_id or not api_key:
        return {}

    try:
        r = requests.get(
            BADGE_DATA_URL,
            params={"key": api_key, "steamid": steam_id},
            headers=HEADERS,
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json().get("response", {})
            badges = data.get("badges", [])
            badge_map = {}
            for b in badges:
                aid = str(b.get("appid", ""))
                if aid:
                    badge_map[aid] = int(b.get("cards_remaining", 0) or 0)
            with _badge_lock:
                _badge_cache = badge_map
                _badge_cache_time = time.time()
            return badge_map
    except Exception:
        pass
    return {}

def get_badge_remaining_cards(steam_id: str, api_key: str, app_id: int | str) -> int:
    """Tek bir oyun için kalan kart düşürme sayısını döner."""
    badge_map = get_all_badges_map(steam_id, api_key)
    return badge_map.get(str(app_id), 0)


# ── Session Storage ───────────────────────────────────────────────────────────

class SteamSession:
    """
    Uygulama oturumu boyunca Steam hesap bilgilerini saklar.
    Bridge.API tarafından instance olarak tutulur.
    """

    def __init__(self):
        self._lock     = threading.Lock()
        self._api_key  = ""
        self._steam_id = ""
        self._profile  = {}
        self._games    = []        # cache

    def configure(self, api_key: str, steam_id_or_url: str) -> dict:
        """
        API key ve Steam ID/URL ile oturumu yapılandırır.
        Döndürür: {"ok": bool, "steam_id": str, "name": str, "error": str}
        """
        api_key = api_key.strip()
        if not api_key:
            return {"ok": False, "error": "Steam Web API key boş olamaz."}

        sid = resolve_steam_id(steam_id_or_url, api_key)
        if not sid:
            return {"ok": False, "error": "Steam ID çözümlenemedi. Geçerli bir Steam ID veya profil URL'si girin."}

        profile = get_player_summary(sid, api_key)

        with self._lock:
            self._api_key  = api_key
            self._steam_id = sid
            self._profile  = profile
            self._games    = []     # cache'i temizle

        return {
            "ok":       True,
            "steam_id": sid,
            "name":     profile["name"],
            "avatar":   profile["avatar"],
        }

    @property
    def is_configured(self) -> bool:
        with self._lock:
            return bool(self._api_key and self._steam_id)

    @property
    def api_key(self) -> str:
        with self._lock:
            return self._api_key

    @property
    def steam_id(self) -> str:
        with self._lock:
            return self._steam_id

    @property
    def profile(self) -> dict:
        with self._lock:
            return dict(self._profile)

    def clear(self):
        with self._lock:
            self._api_key  = ""
            self._steam_id = ""
            self._profile  = {}
            self._games    = []
        # Cache dosyasını da sil
        if os.path.exists(OWNED_CACHE_FILE):
            try:
                os.remove(OWNED_CACHE_FILE)
            except Exception:
                pass

    def get_games(self, force_refresh: bool = False) -> list[dict]:
        with self._lock:
            key = self._api_key
            sid = self._steam_id
            cached = list(self._games)

        if cached and not force_refresh:
            return cached

        if not key or not sid:
            return []

        games = get_owned_games(sid, key, force_refresh)

        with self._lock:
            self._games = games
        return games


# ── Global singleton ──────────────────────────────────────────────────────────
_session: SteamSession | None = None
_session_lock = threading.Lock()


def get_session() -> SteamSession:
    global _session
    with _session_lock:
        if _session is None:
            _session = SteamSession()
        return _session
