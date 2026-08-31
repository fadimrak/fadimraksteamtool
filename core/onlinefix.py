"""
core/onlinefix.py  —  Online Fix Arama, İndirme ve Otomatik Kurulum Motoru

Özellikler:
  1. Resmi online-fix.me sitesinden doğrudan arama ve detay çekme
  2. Fix Repair arşivlerini Pixeldrain / Hosters üzerinden tek tıkla uygulama içine indirme
  3. Yerel Steam kütüphanelerinden kurulu oyunları otomatik tespit etme
  4. Şifreli (online-fix.me) otomatik arşiv açma (ZIP / RAR / 7Z)
  5. Orijinal dosyaları otomatik yedekleme ve tek tıkla geri alma (Uninstall Fix)
  6. Oyunu doğrudan uygulama içinden başlatma
"""

import os
import sys
import shutil
import zipfile
import subprocess
import tempfile
import time
import re
import json
import html
import urllib.parse
import requests

from core.steam_utils import detect_steam_path

# online-fix.me arşivlerinin şifresi sabittir
ONLINEFIX_PASSWORD = "online-fix.me"
ONLINEFIX_BASE = "https://online-fix.me"
ONLINEFIX_SEARCH_URL = "https://online-fix.me/index.php?do=search&subaction=search&story={query}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://online-fix.me/",
}


# ── Extractor tespiti ─────────────────────────────────────────────

if sys.platform == "win32":
    import winreg
else:
    winreg = None


def _get_registry_app_path(exe_name: str) -> str | None:
    """Windows Registry App Paths altından kurulu exe'nin yolunu sorgular."""
    if not winreg:
        return None
    reg_keys = [
        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"),
        (winreg.HKEY_CURRENT_USER, rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"),
        (winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\{exe_name}"),
    ]
    for root_k, sub_k in reg_keys:
        try:
            with winreg.OpenKey(root_k, sub_k) as k:
                val = winreg.QueryValue(k, "")
                if val and os.path.isfile(val):
                    return val
        except Exception:
            pass
    return None


def _find_exe(*names: str) -> str | None:
    """Registry, PATH ve yaygın kurulum dizinlerinde ilk bulunan exe'yi döndürür."""
    # 1. Windows Registry App Paths
    for name in names:
        reg_p = _get_registry_app_path(name)
        if reg_p:
            return reg_p

    # 2. PATH
    for name in names:
        found = shutil.which(name)
        if found:
            return found

    # 3. Bilinen Kurulum Dizinleri
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pfx86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    localapp = os.environ.get("LOCALAPPDATA", "")

    search_dirs = [
        r"C:\Program Files\WinRAR",
        r"C:\Program Files (x86)\WinRAR",
        os.path.join(pf, "WinRAR") if pf else "",
        os.path.join(pfx86, "WinRAR") if pfx86 else "",
        os.path.join(localapp, "Programs", "WinRAR") if localapp else "",
        r"C:\Program Files\7-Zip",
        r"C:\Program Files (x86)\7-Zip",
        os.path.join(pf, "7-Zip") if pf else "",
        os.path.join(pfx86, "7-Zip") if pfx86 else "",
        os.path.join(localapp, "Programs", "7-Zip") if localapp else "",
    ]

    for name in names:
        for d in search_dirs:
            if not d:
                continue
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
    return None


def _winrar_path() -> str | None:
    return _find_exe("UnRAR.exe", "WinRAR.exe", "Rar.exe", "unrar")


def _sevenz_path() -> str | None:
    return _find_exe("7z.exe", "7za.exe", "7z")


def check_extractor_available() -> dict:
    """Sistemde RAR/7Z açabilecek bir araç var mı kontrol eder."""
    return {
        "zip": True,
        "rar": _winrar_path() is not None or _sevenz_path() is not None,
        "7z":  _sevenz_path() is not None,
        "winrar_path": _winrar_path(),
        "sevenz_path": _sevenz_path(),
    }


# ── 1. Resmi Online-Fix.me Arama Motoru ───────────────────────────

def search_onlinefix(query: str, timeout: int = 10) -> dict:
    """
    Doğrudan resmi online-fix.me sitesinde arama yapar.
    Oyun başlıkları, afişleri, kategori, tarih ve makale linklerini döndürür.
    """
    q_clean = query.strip()
    if not q_clean:
        return {"ok": True, "results": [], "query": ""}

    encoded = urllib.parse.quote(q_clean)
    url = ONLINEFIX_SEARCH_URL.format(query=encoded)

    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        html = r.text

        results = []
        # DLE arama sonucu blokları: class="news news-search" veya class="article"
        # Her bir oyun kartı içindeki link, afiş, başlık ve bilgileri ayıklıyoruz
        article_blocks = re.findall(
            r'<div class="news news-search">(.*?)</div>\s*</div>\s*</div>',
            html,
            re.DOTALL
        )
        if not article_blocks:
            article_blocks = re.findall(r'<div class="article clr">(.*?)</div>\s*</div>', html, re.DOTALL)

        for block in article_blocks:
            link_m = re.search(r'href="(https://online-fix\.me/games/[^"]+\.html)"', block)
            if not link_m:
                continue
            art_url = link_m.group(1)

            # Afiş
            img_m = re.search(r'(?:data-src|src)="(https://online-fix\.me/uploads/[^"]+)"', block)
            img_url = img_m.group(1) if img_m else ""

            # Başlık
            title_m = re.search(r'alt="([^"]+)"', block)
            raw_title = title_m.group(1) if title_m else ""
            if not raw_title:
                t_sub = re.search(r'<a[^>]+href="' + re.escape(art_url) + r'"[^>]*>([^<]+)</a>', block)
                raw_title = t_sub.group(1).strip() if t_sub else os.path.basename(art_url).replace(".html", "")

            # Rusça "по сети" / "online" temizliği yaparak temiz İngilizce isim elde edelim
            clean_title = re.sub(r'\s*по\s+сети\s*', '', raw_title, flags=re.IGNORECASE).strip()

            # Tarih
            date_m = re.search(r'<time[^>]*datetime="([^"]+)"[^>]*>([^<]+)</time>', block)
            date_str = date_m.group(2).strip() if date_m else ""

            # Kategori
            cat_m = re.search(r'/games/([^/]+)/', art_url)
            category = cat_m.group(1).capitalize() if cat_m else "Game"

            # Modlar (Kooperatif / Çok Oyunculu vb.)
            modes = []
            if "Кооператив" in block or "Co-op" in block:
                modes.append("Co-op")
            if "Мультиплеер" in block or "Multiplayer" in block:
                modes.append("Multiplayer")

            results.append({
                "title": clean_title or raw_title,
                "raw_title": raw_title,
                "url": art_url,
                "image": img_url,
                "date": date_str,
                "category": category,
                "modes": modes,
            })

        # Eğer blok regexi kaçırdıysa genel link taraması yap
        if not results:
            links = re.findall(r'<a[^>]+href="(https://online-fix\.me/games/[^"]+\.html)"[^>]*>(.*?)</a>', html, re.DOTALL)
            seen = set()
            for l_url, l_txt in links:
                clean_txt = re.sub(r'<[^>]+>', '', l_txt).strip()
                if l_url not in seen and clean_txt and not clean_txt.isdigit() and "#comment" not in l_url and "page," not in l_url:
                    seen.add(l_url)
                    c_title = re.sub(r'\s*по\s+сети\s*', '', clean_txt, flags=re.IGNORECASE).strip()
                    results.append({
                        "title": c_title or clean_txt,
                        "raw_title": clean_txt,
                        "url": l_url,
                        "image": "",
                        "date": "",
                        "category": "Game",
                        "modes": ["Online"],
                    })

        return {"ok": True, "results": results, "query": q_clean, "count": len(results)}
    except Exception as e:
        return {"ok": False, "error": str(e), "results": [], "query": q_clean}


# ── 2. Oyun ve Fix Detayları Çözümleme ────────────────────────────

def get_onlinefix_details(article_url: str, timeout: int = 10) -> dict:
    """
    Oyunun resmi online-fix.me makale sayfasını parse eder.
    Sürüm, yazar, talimatlar ve indirilebilir Fix Repair linklerini getirir.
    """
    if not article_url.startswith(ONLINEFIX_BASE):
        return {"ok": False, "error": "Geçersiz Online-Fix adresi. Yalnızca resmi online-fix.me desteklenir."}

    try:
        r = requests.get(article_url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        html_text = r.text

        # Başlık ve Afiş
        title_m = re.search(r'<h1[^>]*>([^<]+)</h1>', html_text)
        raw_title = title_m.group(1).strip() if title_m else ""
        clean_title = re.sub(r'\s*по\s+сети\s*', '', raw_title, flags=re.IGNORECASE).strip()

        img_m = re.search(r'<div class="image"[^>]*>.*?<img[^>]+src="([^"]+)"', html_text, re.DOTALL)
        img_url = img_m.group(1) if img_m else ""

        # Yazar / Fix Yapan (Örn: 0xdeadc0de)
        author_m = re.search(r'/user/([^/]+)/', html_text)
        author = author_m.group(1) if author_m else "Online-Fix"

        # Fix Sürümü veya Güncelleme Tarihi
        ver_m = re.search(r'Игра обновлена до версии\s*<b>?([^<,\n]+)</b>?', html_text, re.IGNORECASE)
        version = ver_m.group(1).strip() if ver_m else "En Güncel Sürüm"

        # Açıklama / Nasıl Oynanır
        desc_clean = ""
        desc_m = re.search(r'<div class="article-content"[^>]*>(.*?)<div class="download', html_text, re.DOTALL)
        if not desc_m:
            desc_m = re.search(r'<div class="article-content"[^>]*>(.*?)</div>', html_text, re.DOTALL)
        if desc_m:
            desc_raw = desc_m.group(1)
            # HTML taglerini temizle
            desc_clean = re.sub(r'<[^>]+>', ' ', desc_raw)
            desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()[:400]

        # İndirme Linkleri Tespiti (Resmi Online-Fix Uploads ve Hosters Platformu)
        fix_downloads = []
        full_downloads = []
        seen_urls = set()

        # 1. Doğrudan Online-Fix Kendi Sunucusunu (uploads.online-fix.me:2053) tara
        uploads_links = re.findall(r'href=["\'](https://uploads\.online-fix\.me:2053/uploads/[^"\']+)["\']', html_text)
        for up_url in uploads_links:
            try:
                s_up = requests.Session()
                s_up.headers.update(HEADERS)
                # Dizin sayfasını ziyaret et (Cloudflare auth çerezini al)
                r_up = s_up.get(up_url, timeout=4)
                if r_up.status_code == 200:
                    # Fix Repair alt klasörü var mı?
                    if "Fix%20Repair/" in r_up.text or "Fix Repair/" in r_up.text:
                        repair_url = urllib.parse.urljoin(up_url, "Fix%20Repair/")
                        r_rep = s_up.get(repair_url, timeout=4)
                        if r_rep.status_code == 200:
                            f_links = re.findall(r'<a href="([^"]+\.rar)"', r_rep.text)
                            for fl in f_links:
                                direct_file_url = urllib.parse.urljoin(repair_url, fl)
                                if direct_file_url not in seen_urls:
                                    seen_urls.add(direct_file_url)
                                    fix_downloads.append({
                                        "name": urllib.parse.unquote(fl),
                                        "url": direct_file_url,
                                        "direct_url": direct_file_url,
                                        "size_bytes": 0,
                                        "size_mb": 0,
                                        "source": "Online-Fix Kendi Sunucusu (Resmi Fix Repair)",
                                        "is_fix": True,
                                        "priority": 0,
                                    })
            except Exception:
                pass

        # 2. Hosters platformunu tara (https://hosters.online-fix.me:2053/GameName)
        hosters_m = re.search(r'href=["\'](https://hosters\.online-fix\.me:2053/[^"\']+)["\']', html_text)
        hosters_url = hosters_m.group(1) if hosters_m else None

        if hosters_url:
            try:
                rh = requests.get(hosters_url, headers=HEADERS, timeout=8)
                if rh.status_code == 200:
                    # Tüm hoster sekmelerini (Pixeldrain, FileDitch, VikingFile, Gofile vb.) data-links JSON'ından ayrıştır
                    options = re.findall(
                        r'<div[^>]*class=["\']option[^"\']*["\'][^>]*data-links=(["\'])(.*?)\1[^>]*>(.*?)</div>',
                        rh.text,
                        re.DOTALL
                    )

                    for quote, data_links_raw, hoster_name in options:
                        hoster_name = hoster_name.strip()
                        unescaped = html.unescape(data_links_raw)
                        try:
                            links_data = json.loads(unescaped)
                        except Exception:
                            continue

                        for item in links_data:
                            try:
                                dlink = item.get("direct_link", "")
                                fname = item.get("file_name", "") or "Fix_Repair.rar"
                                if not dlink or dlink in seen_urls:
                                    continue
                                seen_urls.add(dlink)

                                is_repair = "repair" in fname.lower() or "fix" in fname.lower()

                                if "pixeldrain.com/u/" in dlink:
                                    file_id = dlink.split("/u/")[-1].strip("/")
                                    direct_api = f"https://pixeldrain.com/api/file/{file_id}"
                                    entry = {
                                        "name": fname,
                                        "url": direct_api,
                                        "direct_url": direct_api,
                                        "size_bytes": 0,
                                        "size_mb": 0,
                                        "source": f"Pixeldrain (Resmi Hoster: {hoster_name})",
                                        "is_fix": is_repair,
                                        "priority": 1, # Pixeldrain ikinci öncelik
                                    }
                                    if is_repair:
                                        fix_downloads.append(entry)
                                    else:
                                        full_downloads.append(entry)
                                else:
                                    entry = {
                                        "name": fname,
                                        "url": dlink,
                                        "direct_url": dlink,
                                        "size_bytes": 0,
                                        "size_mb": 0,
                                        "source": f"{hoster_name} (Resmi Hoster)",
                                        "is_fix": is_repair,
                                        "priority": 2,
                                    }
                                    if is_repair:
                                        fix_downloads.append(entry)
                                    else:
                                        full_downloads.append(entry)
                            except Exception:
                                continue
            except Exception:
                pass

        # Öncelik sıralaması: Kendi Sunucusu ve Pixeldrain en başta
        fix_downloads.sort(key=lambda x: x.get("priority", 99))
        full_downloads.sort(key=lambda x: x.get("priority", 99))

        return {
            "ok": True,
            "title": clean_title or raw_title,
            "raw_title": raw_title,
            "image": img_url,
            "version": version,
            "author": author,
            "description": desc_clean,
            "url": article_url,
            "fix_downloads": fix_downloads,
            "full_downloads": full_downloads,
            "has_direct_fix": len(fix_downloads) > 0,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── 3. Uygulama İçi İndirme Motoru ───────────────────────────────

def download_fix_archive(download_url: str, dest_dir: str = None, progress_cb = None) -> dict:
    """
    Fix arşivini uygulama içine akış olarak indirir.
    uploads.online-fix.me sunucusu için Cloudflare auth çerezini ve Referer başlığını otomatik çözer.
    """
    if not dest_dir:
        dest_dir = tempfile.gettempdir()
    os.makedirs(dest_dir, exist_ok=True)

    # İndirilecek dosya adını belirle
    fname = "OnlineFix_Archive.rar"
    try:
        parsed = urllib.parse.urlparse(download_url)
        bname = os.path.basename(parsed.path)
        if bname and "." in bname:
            fname = urllib.parse.unquote(bname)
    except Exception:
        pass

    target_path = os.path.join(dest_dir, f"of_{int(time.time())}_{fname}")

    try:
        s = requests.Session()
        s.headers.update(HEADERS)

        # uploads.online-fix.me sunucusu için önce üst dizini ziyaret edip auth çerezini al
        if "uploads.online-fix.me" in download_url:
            parent_dir = download_url.rsplit("/", 1)[0] + "/"
            try:
                s.get(parent_dir, timeout=6)
            except Exception:
                pass
            s.headers.update({"Referer": parent_dir})

        r = s.get(download_url, stream=True, timeout=30)
        r.raise_for_status()

        # Content-Disposition başlığında gerçek dosya adı varsa al
        cd = r.headers.get("Content-Disposition", "")
        cd_m = re.search(r'filename=["\']?([^"\';]+)', cd)
        if cd_m:
            real_name = urllib.parse.unquote(cd_m.group(1).strip())
            target_path = os.path.join(dest_dir, f"of_{int(time.time())}_{real_name}")

        total_size = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        start_time = time.time()
        last_update = start_time

        with open(target_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)

                now = time.time()
                if progress_cb and (now - last_update >= 0.15 or (total_size and downloaded >= total_size)):
                    elapsed = max(0.001, now - start_time)
                    speed_kb = (downloaded / 1024) / elapsed
                    pct = int((downloaded / total_size) * 100) if total_size > 0 else 50
                    progress_cb({
                        "pct": min(100, pct),
                        "downloaded_bytes": downloaded,
                        "total_bytes": total_size,
                        "downloaded_mb": round(downloaded / (1024 * 1024), 2),
                        "total_mb": round(total_size / (1024 * 1024), 2) if total_size else 0,
                        "speed_kb": round(speed_kb, 1),
                        "speed_mb": round(speed_kb / 1024, 2),
                    })
                    last_update = now

        # İndirilen dosyanın gerçek bir arşiv olup olmadığını doğrula (Sihirli Bayt Kontrolü)
        if not os.path.exists(target_path) or os.path.getsize(target_path) < 100:
            raise RuntimeError("İndirilen dosya boyutu çok küçük veya dosya oluşturulamadı.")

        with open(target_path, "rb") as vf:
            header_bytes = vf.read(64)

        is_rar = header_bytes.startswith(b"Rar!\x1a\x07\x00") or header_bytes.startswith(b"Rar!\x1a\x07\x01")
        is_zip = header_bytes.startswith(b"PK\x03\x04") or header_bytes.startswith(b"PK\x05\x06")
        is_7z  = header_bytes.startswith(b"7z\xbc\xaf\x27\x1c")

        if not (is_rar or is_zip or is_7z):
            # Dosya arşiv değilse (örn. sunucunun döndürdüğü HTML 502 / Cloudflare hata sayfası)
            try:
                os.remove(target_path)
            except Exception:
                pass
            raise RuntimeError(
                "İndirme sunucusu geçici olarak çevrimdışı veya hata sayfası döndürdü (502 / HTML). "
                "Dosya geçerli bir arşiv değil. Lütfen başka bir oyun veya listeden alternatif bir kaynak seçin."
            )

        if progress_cb:
            progress_cb({
                "pct": 100,
                "downloaded_bytes": downloaded,
                "total_bytes": downloaded,
                "downloaded_mb": round(downloaded / (1024 * 1024), 2),
                "total_mb": round(downloaded / (1024 * 1024), 2),
                "speed_kb": 0,
                "speed_mb": 0,
            })

        return {
            "ok": True,
            "file_path": target_path,
            "filename": os.path.basename(target_path),
            "size": downloaded,
        }
    except Exception as e:
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
            except Exception:
                pass
        return {"ok": False, "error": str(e)}


# ── 4. Yedekleme ve Kurulum Motoru ───────────────────────────────

def _backup_existing_files(archive_path: str, game_dir: str) -> list:
    """Arşiv içeriğinde bulunan ve oyun klasöründe zaten var olan dosyaları yedekler."""
    backup_dir = os.path.join(game_dir, ".onlinefix_backup", str(int(time.time())))
    backed_up = []

    # Dosya listesini tespit etmeye çalış
    target_names = [
        "OnlineFix64.dll", "OnlineFix.ini", "SteamOverlay64.dll",
        "steam_api64.dll", "steam_api.dll", "OnlineFix_UI.dll"
    ]
    ext = os.path.splitext(archive_path)[1].lower()
    if ext == ".zip":
        try:
            with zipfile.ZipFile(archive_path, "r") as zf:
                for name in zf.namelist():
                    b = os.path.basename(name)
                    if b and b not in target_names:
                        target_names.append(b)
        except Exception:
            pass

    for fname in target_names:
        for root, _, files in os.walk(game_dir):
            if ".onlinefix_backup" in root:
                continue
            if fname in files:
                src_path = os.path.join(root, fname)
                rel_path = os.path.relpath(src_path, game_dir)
                dst_path = os.path.join(backup_dir, rel_path)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
                backed_up.append(rel_path)

    return backed_up


def _extract_zip(archive: str, dest: str, progress_cb=None) -> dict:
    """stdlib zipfile ile ZIP'i çıkarır. Şifreli ZIP desteklenir."""
    with zipfile.ZipFile(archive, "r") as zf:
        members = zf.infolist()
        total   = len(members)
        for i, member in enumerate(members):
            try:
                zf.extract(member, dest, pwd=ONLINEFIX_PASSWORD.encode())
            except RuntimeError:
                zf.extract(member, dest)
            if progress_cb:
                progress_cb(int((i + 1) / total * 100))
    return {"ok": True, "method": "zipfile"}


def _extract_rar_winrar(archive: str, dest: str, exe: str, progress_cb=None) -> dict:
    """UnRAR.exe / WinRAR.exe ile şifreli çıkarır."""
    cmd = [
        exe, "x",
        f"-p{ONLINEFIX_PASSWORD}",
        "-y",
        "-ibck",
        archive,
        dest + os.sep,
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if result.returncode not in (0, 1):
        err_msg = (result.stderr or result.stdout or b"").decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"RAR extract başarısız (code {result.returncode}): {err_msg}"
        )
    if progress_cb:
        progress_cb(100)
    return {"ok": True, "method": os.path.basename(exe)}


def _extract_7z(archive: str, dest: str, exe: str, progress_cb=None) -> dict:
    """7-Zip ile şifreli çıkarır."""
    cmd = [
        exe, "x",
        f"-p{ONLINEFIX_PASSWORD}",
        "-y",
        f"-o{dest}",
        archive,
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if result.returncode not in (0, 1):
        err_msg = (result.stderr or result.stdout or b"").decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"7-Zip extract başarısız (code {result.returncode}): {err_msg}"
        )
    if progress_cb:
        progress_cb(100)
    return {"ok": True, "method": "7-Zip"}


def install_fix(archive_path: str, game_dir: str, backup: bool = True, progress_cb=None) -> dict:
    """
    Online Fix arşivini oyun klasörüne kurar. İsteğe bağlı olarak mevcut dosyaları yedekler.
    """
    if not os.path.isfile(archive_path):
        return {"ok": False, "error": f"Dosya bulunamadı: {archive_path}"}
    if not os.path.isdir(game_dir):
        return {"ok": False, "error": f"Oyun klasörü bulunamadı: {game_dir}"}

    # 1. Orijinal dosyaları yedekle
    backed_up = []
    if backup:
        try:
            backed_up = _backup_existing_files(archive_path, game_dir)
        except Exception:
            pass

    ext = os.path.splitext(archive_path)[1].lower()

    # 2. Arşivi Çıkar
    extract_result = None
    try:
        if ext == ".zip":
            try:
                extract_result = _extract_zip(archive_path, game_dir, progress_cb)
            except Exception:
                exe_7z = _sevenz_path()
                if exe_7z:
                    extract_result = _extract_7z(archive_path, game_dir, exe_7z, progress_cb)
                else:
                    raise

        elif ext == ".rar":
            # Tüm olası WinRAR ve 7-Zip exe'lerini sırayla dene
            rar_candidates = [
                _get_registry_app_path("WinRAR.exe"),
                _get_registry_app_path("UnRAR.exe"),
                r"C:\Program Files\WinRAR\UnRAR.exe",
                r"C:\Program Files\WinRAR\WinRAR.exe",
                r"C:\Program Files\WinRAR\Rar.exe",
                r"C:\Program Files (x86)\WinRAR\UnRAR.exe",
                r"C:\Program Files (x86)\WinRAR\WinRAR.exe",
                _winrar_path(),
            ]
            # Yinelenenleri ve None olanları temizle
            rar_candidates = [x for i, x in enumerate(rar_candidates) if x and os.path.isfile(x) and x not in rar_candidates[:i]]

            last_rar_err = None
            for exe in rar_candidates:
                try:
                    extract_result = _extract_rar_winrar(archive_path, game_dir, exe, progress_cb)
                    if extract_result:
                        break
                except Exception as e:
                    last_rar_err = str(e)

            if not extract_result:
                exe_7z = _sevenz_path()
                if exe_7z:
                    try:
                        extract_result = _extract_7z(archive_path, game_dir, exe_7z, progress_cb)
                    except Exception as e:
                        if not last_rar_err:
                            last_rar_err = str(e)

            if not extract_result:
                if last_rar_err:
                    return {"ok": False, "error": f"RAR arşivi açılamadı: {last_rar_err}"}
                return {
                    "ok": False,
                    "error": "RAR arşivini açmak için sisteminizde WinRAR veya 7-Zip kurulu olmalıdır.",
                }

        elif ext == ".7z":
            exe_7z = _sevenz_path()
            if exe_7z:
                extract_result = _extract_7z(archive_path, game_dir, exe_7z, progress_cb)
            else:
                return {"ok": False, "error": "7Z arşivini açmak için 7-Zip gerekli."}
        else:
            return {"ok": False, "error": f"Desteklenmeyen format: {ext}"}

    except Exception as e:
        return {"ok": False, "error": f"Arşiv çıkarma hatası: {e}"}

    # 3. Kurulum meta verisini kaydet
    try:
        meta_file = os.path.join(game_dir, ".onlinefix_meta.json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump({
                "installed_at": time.time(),
                "archive": os.path.basename(archive_path),
                "backed_up_files": backed_up,
            }, f, indent=2)
    except Exception:
        pass

    return {
        "ok": True,
        "method": extract_result.get("method", "extractor"),
        "game_dir": game_dir,
        "backup_count": len(backed_up),
    }


def uninstall_fix(game_dir: str) -> dict:
    """
    Kurulmuş Online Fix dosyalarını temizler ve varsa yedeği geri yükler.
    """
    if not os.path.isdir(game_dir):
        return {"ok": False, "error": f"Oyun klasörü bulunamadı: {game_dir}"}

    removed_files = []
    # Bilinen onlinefix dosyalarını temizle
    known_fix_files = [
        "OnlineFix64.dll", "OnlineFix.ini", "SteamOverlay64.dll",
        "OnlineFix_UI.dll", "steam_api64_o.dll", "steam_api_o.dll",
        "OnlineFix.url", "online-fix.me.url"
    ]
    for root, _, files in os.walk(game_dir):
        if ".onlinefix_backup" in root:
            continue
        for fname in files:
            if fname in known_fix_files:
                fp = os.path.join(root, fname)
                try:
                    os.remove(fp)
                    removed_files.append(fname)
                except Exception:
                    pass

    # Varsa en son yedeği geri yükle
    backup_base = os.path.join(game_dir, ".onlinefix_backup")
    restored_count = 0
    if os.path.isdir(backup_base):
        snapshots = sorted(os.listdir(backup_base), reverse=True)
        if snapshots:
            latest_snap = os.path.join(backup_base, snapshots[0])
            for root, _, files in os.walk(latest_snap):
                for f in files:
                    src_f = os.path.join(root, f)
                    rel_f = os.path.relpath(src_f, latest_snap)
                    dst_f = os.path.join(game_dir, rel_f)
                    try:
                        os.makedirs(os.path.dirname(dst_f), exist_ok=True)
                        shutil.copy2(src_f, dst_f)
                        restored_count += 1
                    except Exception:
                        pass

    # Meta dosyasını sil
    meta_f = os.path.join(game_dir, ".onlinefix_meta.json")
    if os.path.exists(meta_f):
        try:
            os.remove(meta_f)
        except Exception:
            pass

    return {
        "ok": True,
        "removed_count": len(removed_files),
        "restored_count": restored_count,
    }


# ── 5. Steam Yüklü Oyunları Otomatik Bulma ────────────────────────

def get_installed_steam_games(steam_path: str = None) -> list:
    """
    Kullanıcının bilgisayarındaki Steam kütüphanelerini tarayarak yüklü oyunları listeler.
    Döndürür: [{"app_id": str, "name": str, "install_dir": str, "exists": bool}]
    """
    sp = steam_path or detect_steam_path()
    if not sp or not os.path.isdir(sp):
        return []

    libraries = [sp]
    vdf_path = os.path.join(sp, "steamapps", "libraryfolders.vdf")
    if not os.path.exists(vdf_path):
        vdf_path = os.path.join(sp, "config", "libraryfolders.vdf")

    if os.path.exists(vdf_path):
        try:
            with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            paths = re.findall(r'"path"\s+"([^"]+)"', content)
            for p in paths:
                p_clean = p.replace("\\\\", "\\")
                if os.path.exists(p_clean) and p_clean not in libraries:
                    libraries.append(p_clean)
        except Exception:
            pass

    games = []
    seen_ids = set()

    for lib in libraries:
        steamapps_dir = os.path.join(lib, "steamapps")
        if not os.path.exists(steamapps_dir):
            continue
        for fname in os.listdir(steamapps_dir):
            if fname.startswith("appmanifest_") and fname.endswith(".acf"):
                acf_path = os.path.join(steamapps_dir, fname)
                try:
                    with open(acf_path, "r", encoding="utf-8", errors="ignore") as f:
                        acf_content = f.read()
                    appid_m = re.search(r'"appid"\s+"(\d+)"', acf_content)
                    name_m = re.search(r'"name"\s+"([^"]+)"', acf_content)
                    dir_m = re.search(r'"installdir"\s+"([^"]+)"', acf_content)
                    if appid_m and name_m and dir_m:
                        appid = appid_m.group(1)
                        if appid in seen_ids or appid == "228980":  # Steamworks Redist skip
                            continue
                        seen_ids.add(appid)
                        name = name_m.group(1)
                        installdir = dir_m.group(1)
                        full_path = os.path.join(steamapps_dir, "common", installdir)
                        games.append({
                            "app_id": appid,
                            "name": name,
                            "install_dir": full_path,
                            "exists": os.path.isdir(full_path),
                        })
                except Exception:
                    pass

    # İsme göre sırala
    games.sort(key=lambda x: x["name"].lower())
    return games


def auto_match_game_dir(game_name: str, app_id: str = None, steam_path: str = None) -> str | None:
    """
    Oyun adına veya App ID'sine göre yerel Steam klasörünü otomatik bulur.
    """
    games = get_installed_steam_games(steam_path)
    if app_id:
        for g in games:
            if g["app_id"] == str(app_id) and g["exists"]:
                return g["install_dir"]

    # İsim eşleştirmesi
    gn_clean = re.sub(r'[^a-zA-Z0-9]', '', game_name).lower()
    for g in games:
        if not g["exists"]:
            continue
        g_clean = re.sub(r'[^a-zA-Z0-9]', '', g["name"]).lower()
        if gn_clean in g_clean or g_clean in gn_clean:
            return g["install_dir"]

    return None


# ── 6. Oyunu Çalıştırma ──────────────────────────────────────────

def launch_game_executable(game_dir: str) -> dict:
    """
    Oyun klasöründeki ana exe'yi tespit edip çalıştırır.
    """
    if not os.path.isdir(game_dir):
        return {"ok": False, "error": "Oyun dizini bulunamadı."}

    # Ana dizindeki .exe dosyalarını listele
    ignored_exes = [
        "unitycrashhandler", "unitycrashhandler64", "unins000", "uninstall",
        "dxsetup", "vcredist", "crashreport", "crashsender", "epicgameslauncher"
    ]
    candidate_exes = []

    for fname in os.listdir(game_dir):
        if fname.lower().endswith(".exe"):
            lower_name = fname.lower()
            if not any(ign in lower_name for ign in ignored_exes):
                candidate_exes.append(os.path.join(game_dir, fname))

    # Eğer ana dizinde bulunamadıysa 1 alt seviyeye bak (örneğin Binaries/Win64)
    if not candidate_exes:
        for root, dirs, files in os.walk(game_dir):
            if "win64" in root.lower() or "binaries" in root.lower():
                for fname in files:
                    if fname.lower().endswith(".exe") and not any(ign in fname.lower() for ign in ignored_exes):
                        candidate_exes.append(os.path.join(root, fname))

    if not candidate_exes:
        return {"ok": False, "error": "Klasörde başlatılabilir .exe dosyası bulunamadı."}

    # En büyük veya en uygun olanı seç
    best_exe = candidate_exes[0]
    try:
        candidate_exes.sort(key=lambda x: os.path.getsize(x), reverse=True)
        best_exe = candidate_exes[0]
    except Exception:
        pass

    try:
        subprocess.Popen([best_exe], cwd=os.path.dirname(best_exe))
        return {"ok": True, "exe": os.path.basename(best_exe), "path": best_exe}
    except Exception as e:
        return {"ok": False, "error": f"Oyun başlatılamadı: {e}"}
