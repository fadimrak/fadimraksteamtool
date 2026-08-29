"""
core/onlinefix.py  —  Online Fix kurulum motoru

Akış:
  1. Kullanıcı online-fix.me'den indirdiği .rar / .zip / .7z dosyasını seçer
  2. Uygulama oyun klasörünü seçmesini ister
  3. Bu modül arşivi oyun klasörüne çıkartır (şifre: online-fix.me)
  4. İşlem sonucu döner

Desteklenen extractor önceliği:
  ZIP  — stdlib zipfile (her zaman çalışır)
  RAR  — WinRAR (UnRAR.exe)  >  7-Zip  >  winrar.exe CLI
  7Z   — 7-Zip (7z.exe)
"""

import os
import sys
import shutil
import zipfile
import subprocess
import tempfile

# online-fix.me arşivlerinin şifresi sabittir
ONLINEFIX_PASSWORD = "online-fix.me"

# ── Extractor tespiti ─────────────────────────────────────────────

def _find_exe(*names: str) -> str | None:
    """PATH ve yaygın kurulum dizinlerinde ilk bulunan exe'yi döndürür."""
    search_dirs = [
        "",                                          # PATH
        r"C:\Program Files\WinRAR",
        r"C:\Program Files (x86)\WinRAR",
        r"C:\Program Files\7-Zip",
        r"C:\Program Files (x86)\7-Zip",
    ]
    for name in names:
        # shutil.which PATH'de arar
        found = shutil.which(name)
        if found:
            return found
        for d in search_dirs:
            if not d:
                continue
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
    return None


def _winrar_path() -> str | None:
    return _find_exe("UnRAR.exe", "WinRAR.exe", "unrar")


def _sevenz_path() -> str | None:
    return _find_exe("7z.exe", "7za.exe", "7z")


# ── ZIP ───────────────────────────────────────────────────────────

def _extract_zip(archive: str, dest: str, progress_cb=None) -> dict:
    """stdlib zipfile ile ZIP'i çıkarır. Şifreli ZIP desteklenir."""
    with zipfile.ZipFile(archive, "r") as zf:
        members = zf.infolist()
        total   = len(members)
        for i, member in enumerate(members):
            try:
                zf.extract(member, dest, pwd=ONLINEFIX_PASSWORD.encode())
            except RuntimeError:
                # Şifresiz dene
                zf.extract(member, dest)
            if progress_cb:
                progress_cb(int((i + 1) / total * 100))
    return {"ok": True, "method": "zipfile"}


# ── RAR via UnRAR/WinRAR ──────────────────────────────────────────

def _extract_rar_winrar(archive: str, dest: str, exe: str, progress_cb=None) -> dict:
    """
    UnRAR.exe / WinRAR.exe / unrar CLI ile çıkarır.
    UnRAR: UnRAR.exe x -p<pass> -y <archive> <dest>
    WinRAR: WinRAR.exe x -p<pass> -y <archive> <dest>
    """
    cmd = [
        exe, "x",
        f"-p{ONLINEFIX_PASSWORD}",
        "-y",           # tüm sorulara evet
        "-ibck",        # arka planda çalış (WinRAR GUI'siz)
        archive,
        dest + os.sep,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode not in (0, 1):  # 1 = warning, kabul edilebilir
        raise RuntimeError(
            f"RAR extract başarısız (code {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    if progress_cb:
        progress_cb(100)
    return {"ok": True, "method": os.path.basename(exe)}


# ── 7-Zip (RAR + 7Z + ZIP) ───────────────────────────────────────

def _extract_7z(archive: str, dest: str, exe: str, progress_cb=None) -> dict:
    """7z.exe x ile çıkarır; şifreyi otomatik dener."""
    cmd = [
        exe, "x",
        f"-p{ONLINEFIX_PASSWORD}",
        "-y",
        f"-o{dest}",
        archive,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode not in (0, 1):
        raise RuntimeError(
            f"7-Zip extract başarısız (code {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    if progress_cb:
        progress_cb(100)
    return {"ok": True, "method": "7-Zip"}


# ── Ana fonksiyon ─────────────────────────────────────────────────

def install_fix(archive_path: str, game_dir: str, progress_cb=None) -> dict:
    """
    Online Fix arşivini oyun klasörüne kurar.

    Args:
        archive_path : İndirilen .rar / .zip / .7z dosyasının tam yolu
        game_dir     : Oyunun kurulu olduğu klasör (exe'nin olduğu yer)
        progress_cb  : İsteğe bağlı ilerleme callback (0-100 int)

    Returns:
        {"ok": True/False, "method": str, "error": str (sadece hata durumunda)}
    """
    if not os.path.isfile(archive_path):
        return {"ok": False, "error": f"Dosya bulunamadı: {archive_path}"}
    if not os.path.isdir(game_dir):
        return {"ok": False, "error": f"Oyun klasörü bulunamadı: {game_dir}"}

    ext = os.path.splitext(archive_path)[1].lower()

    # ── ZIP: stdlib, her zaman çalışır ───────────────────────────
    if ext == ".zip":
        try:
            return _extract_zip(archive_path, game_dir, progress_cb)
        except Exception as e:
            # Şifreli ZIP veya bozuk → 7-Zip ile dene
            exe_7z = _sevenz_path()
            if exe_7z:
                try:
                    return _extract_7z(archive_path, game_dir, exe_7z, progress_cb)
                except Exception as e2:
                    return {"ok": False, "error": str(e2)}
            return {"ok": False, "error": str(e)}

    # ── RAR: UnRAR > WinRAR > 7-Zip ──────────────────────────────
    if ext == ".rar":
        # 1. UnRAR / WinRAR
        exe_rar = _winrar_path()
        if exe_rar:
            try:
                return _extract_rar_winrar(archive_path, game_dir, exe_rar, progress_cb)
            except Exception as e:
                pass  # Sonraki yönteme geç

        # 2. 7-Zip (RAR desteği var)
        exe_7z = _sevenz_path()
        if exe_7z:
            try:
                return _extract_7z(archive_path, game_dir, exe_7z, progress_cb)
            except Exception as e:
                return {"ok": False, "error": str(e)}

        return {
            "ok": False,
            "error": (
                "RAR arşivini açmak için WinRAR veya 7-Zip gerekli.\n"
                "Lütfen birini kurun: winrar.com veya 7-zip.org"
            ),
        }

    # ── 7Z ────────────────────────────────────────────────────────
    if ext == ".7z":
        exe_7z = _sevenz_path()
        if exe_7z:
            try:
                return _extract_7z(archive_path, game_dir, exe_7z, progress_cb)
            except Exception as e:
                return {"ok": False, "error": str(e)}
        return {
            "ok": False,
            "error": "7Z arşivini açmak için 7-Zip gerekli: 7-zip.org",
        }

    return {"ok": False, "error": f"Desteklenmeyen format: {ext}"}


def check_extractor_available() -> dict:
    """
    Sistemde RAR açabilecek bir araç var mı kontrol eder.
    Returns: {"rar": bool, "7z": bool, "zip": True}
    """
    return {
        "zip": True,
        "rar": _winrar_path() is not None or _sevenz_path() is not None,
        "7z":  _sevenz_path() is not None,
        "winrar_path": _winrar_path(),
        "sevenz_path": _sevenz_path(),
    }
