import os
import sys

VERSION = "1.0"

# Kendi GitHub repo'nuzun raw versiyon dosyasının URL'si
VERSION_CHECK_URL = "https://raw.githubusercontent.com/fadimrak/fadimraksteamtool/refs/heads/main/verison"

if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STEAM_APP_LIST_CACHE_FILE = os.path.join(_BASE_DIR, "steam_app_list_cache.json")
STEAM_APP_LIST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                  'AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/120.0.0.0 Safari/537.36'
}

STEAM_APP_LIST_GITHUB_SOURCES = [
    {
        "name": "github_games",
        "url": "https://raw.githubusercontent.com/jsnli/steamappidlist/refs/heads/master/data/games_appid.json",
        "name_suffix": "",
    },
    {
        "name": "github_dlc",
        "url": "https://raw.githubusercontent.com/jsnli/steamappidlist/refs/heads/master/data/dlc_appid.json",
        "name_suffix": " (DLC)",
    },
]

# ManifestHub repo'sunuzun codeload URL'si — kendi repo'nuzu buraya girin
# Örnek: "https://codeload.github.com/KULLANICI_ADI/REPO_ADI/zip/refs/heads/"
MANIFEST_HUB_BASE_URL = "https://codeload.github.com/SSMGAlt/ManifestHub2/zip/refs/heads/"

# ManifestHub2 (SSMGAlt) git refs URL'si (desteklenen oyunları filtrelemek için)
MANIFEST_HUB_REFS_URL = "https://github.com/SSMGAlt/ManifestHub2.git/info/refs?service=git-upload-pack"

# SteamAutoCracks/ManifestHub refs URL'si
MANIFEST_HUB_SAC_REFS_URL = "https://github.com/SteamAutoCracks/ManifestHub.git/info/refs?service=git-upload-pack"

# ManifestHub3 (steamtools-games) GitHub REST API branches endpoint
# Sayfalandırmalı olarak tüm desteklenen App ID'leri çeker
MANIFEST_HUB3_REFS_URL = "https://api.github.com/repos/steamtools-games/ManifestHub3/branches"

# Hakkında sayfasındaki GitHub butonu için link
PROJECT_GITHUB_URL = "https://github.com/fadimrak/fadimraksteamtool"
