import os
import sys
import json
import threading
import time
import requests

from config import VERSION, VERSION_CHECK_URL, PROJECT_GITHUB_URL
from core import installer, game_manager, steam_utils
from core import achievement_manager, idle_farmer, steam_account, tray_manager, dlc_unlocker
from steam_api import fetch_steam_app_list

if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SETTINGS_FILE = os.path.join(_BASE_DIR, "tsc_settings.json")


class API:
    def __init__(self):
        self._window  = None
        self._tray    = None
        from steam_api import _load_cached_app_list
        self._game_list = _load_cached_app_list() or []
        self._settings  = self._load_settings()
        self._session   = steam_account.get_session()
        threading.Thread(target=self._prefetch_game_list, daemon=True).start()
        threading.Thread(target=self._restore_session, daemon=True).start()

    def set_window(self, window):
        self._window = window
        static_dir = os.path.join(_BASE_DIR, "ui_web", "static")
        if getattr(sys, "frozen", False):
            static_dir = os.path.join(sys._MEIPASS, "static")
        tray = tray_manager.get_tray(static_dir)
        tray.set_window(window)
        tray.set_idle_farmer(idle_farmer)
        tray.set_quit_callback(self._on_quit)
        tray.set_stop_idle_callback(self.idle_stop_all)
        tray.set_language(self._settings.get("lang", "tr"))
        self._tray = tray
        tray.start()

        # Pencere X butonuyla kapatılınca idle'ları durdur ve çık
        window.events.closed += self._on_window_closed

    def _on_window_closed(self):
        """Pencere X ile kapatılınca tüm idle'ları durdur."""
        self._full_shutdown()

    def _on_quit(self):
        """Tray'den Çıkış seçilince çağrılır."""
        self._full_shutdown()

    def _full_shutdown(self):
        """Tüm kaynakları temizleyip uygulamayı kapat."""
        # Önce tüm idle subprocess'lerini durdur
        try:
            idle_farmer.get_farmer().stop_all()
        except Exception:
            pass

        # Tray ikonunu kaldır
        try:
            if self._tray:
                self._tray.stop()
        except Exception:
            pass

        # Zorla process'i kapat (subprocess'ler hâlâ yaşıyorsa)
        try:
            import psutil
            current = psutil.Process()
            for child in current.children(recursive=True):
                try:
                    child.kill()
                except Exception:
                    pass
        except ImportError:
            pass
        except Exception:
            pass

        # Python process'ini tamamen sonlandır
        os._exit(0)

    def _push(self, event, data=None):
        if self._window:
            payload = json.dumps({"event": event, "data": data or {}})
            self._window.evaluate_js(f"window.onPythonEvent({payload})")

    def _load_settings(self):
        defaults = {
            "steam_path":   steam_utils.detect_steam_path() or "",
            "lang":         "tr",
            "has_accepted_legal": False,
            "steam_api_key": "",
            "steam_id":     "",
        }
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                defaults.update(saved)
            except Exception:
                pass
        return defaults

    def _save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=2, ensure_ascii=False)

    def _prefetch_game_list(self):
        try:
            self._game_list = fetch_steam_app_list()
        except Exception:
            self._game_list = []

    def _steam_path(self):
        return self._settings.get("steam_path", "")

    def _restore_session(self):
        key = self._settings.get("steam_api_key", "")
        sid = self._settings.get("steam_id", "")
        if key and sid:
            result = self._session.configure(key, sid)
            if result.get("ok"):
                self._push("account_restored", {
                    "steam_id": result["steam_id"],
                    "name":     result["name"],
                    "avatar":   result.get("avatar", ""),
                })

    def get_legal_status(self):
        return {"accepted": True}

    def accept_legal(self):
        self._settings["has_accepted_legal"] = True
        self._save_settings()
        return {"ok": True}

    def reject_legal(self):
        if self._window:
            self._window.destroy()
        return {"ok": True}

    def get_version(self):
        return {"version": VERSION}

    def check_for_updates(self):
        if not VERSION_CHECK_URL:
            return {"current": VERSION, "latest": VERSION, "has_update": False}
        try:
            r = requests.get(VERSION_CHECK_URL, timeout=5)
            latest = r.text.strip()
            return {"current": VERSION, "latest": latest, "has_update": latest != VERSION}
        except Exception:
            return {"current": VERSION, "latest": VERSION, "has_update": False}

    def open_in_browser(self, url):
        import webbrowser
        webbrowser.open(url)
        return {"ok": True}

    def get_project_github_url(self):
        return PROJECT_GITHUB_URL or ""

    def get_settings(self):
        return {
            "steam_path":    self._settings.get("steam_path", ""),
            "lang":          self._settings.get("lang", "tr"),
            "steam_api_key": self._settings.get("steam_api_key", ""),
            "steam_id":      self._settings.get("steam_id", ""),
        }

    def save_settings(self, steam_path):
        self._settings["steam_path"] = steam_path
        self._save_settings()
        return {"ok": True}

    def save_all_settings(self, data: dict):
        for k in ("steam_path", "lang", "steam_api_key", "steam_id"):
            if k in data:
                self._settings[k] = data[k]
        if "lang" in data and self._tray:
            self._tray.set_language(data["lang"])
        self._save_settings()
        return {"ok": True}

    def set_language(self, lang: str):
        lang = "en" if str(lang).lower() == "en" else "tr"
        self._settings["lang"] = lang
        self._save_settings()
        if self._tray:
            self._tray.set_language(lang)
        return {"ok": True, "lang": lang}

    def detect_steam_path(self):
        path = steam_utils.detect_steam_path()
        if path:
            self._settings["steam_path"] = path
            self._save_settings()
        return {"path": path or ""}

    def browse_steam_folder(self):
        import webview
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return {"path": result[0]}
        return {"path": ""}

    def account_login(self, api_key: str, steam_id_or_url: str):
        result = self._session.configure(api_key.strip(), steam_id_or_url.strip())
        if result.get("ok"):
            self._settings["steam_api_key"] = api_key.strip()
            self._settings["steam_id"]      = result["steam_id"]
            self._save_settings()
            self._push("account_logged_in", {
                "steam_id": result["steam_id"],
                "name":     result["name"],
                "avatar":   result.get("avatar", ""),
            })
        return result

    def account_logout(self):
        self._session.clear()
        self._settings["steam_api_key"] = ""
        self._settings["steam_id"]      = ""
        self._save_settings()
        self._push("account_logged_out", {})
        return {"ok": True}

    def account_get_status(self):
        if self._session.is_configured:
            p = self._session.profile
            return {
                "logged_in": True,
                "steam_id":  self._session.steam_id,
                "name":      p.get("name", ""),
                "avatar":    p.get("avatar", ""),
            }
        return {"logged_in": False}

    def account_get_owned_games(self, force_refresh: bool = False):
        if not self._session.is_configured:
            return {"ok": False, "error": "Steam hesabı bağlı değil. Önce Hesap sekmesinden giriş yap."}
        threading.Thread(
            target=self._fetch_owned_games_thread,
            args=(bool(force_refresh),),
            daemon=True,
        ).start()
        return {"ok": True}

    def _fetch_owned_games_thread(self, force_refresh: bool):
        try:
            self._push("owned_games_loading", {})
            games = steam_account.get_owned_games(
                self._session.steam_id,
                self._session.api_key,
                force_refresh,
            )
            self._push("owned_games_loaded", {
                "games": games,
                "total": len(games),
            })
        except PermissionError as e:
            self._push("owned_games_error", {"error": str(e)})
        except Exception as e:
            self._push("owned_games_error", {"error": f"Kütüphane yüklenemedi: {e}"})

    def get_installed_games(self):
        steam_path    = self._steam_path()
        app_ids       = game_manager.get_installed_app_ids(steam_path)
        installed_data = game_manager.load_installed_games()
        games = []

        for app_id in app_ids:
            entry = installed_data.get(app_id, {})
            if isinstance(entry, str):
                name = entry
            elif isinstance(entry, dict):
                name = entry.get("name", f"Game {app_id}")
            else:
                name = f"Game {app_id}"

            missing = False
            if name in (f"Game {app_id}", str(app_id)) or not name.strip():
                found = next(
                    (g["name"] for g in self._game_list if str(g.get("appid")) == str(app_id)),
                    None,
                )
                if found:
                    name = found
                else:
                    missing = True
                    name = f"Game {app_id}"

            games.append({
                "app_id": app_id,
                "name":   name,
                "cover":  f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg",
            })
            if missing:
                threading.Thread(
                    target=self._fetch_missing_name_thread,
                    args=(app_id,), daemon=True,
                ).start()

        return games

    def _fetch_missing_name_thread(self, app_id):
        try:
            r = requests.get(
                f"https://store.steampowered.com/api/appdetails?appids={app_id}",
                timeout=5,
            )
            data = r.json()
            if str(app_id) in data and data[str(app_id)].get("success"):
                name = data[str(app_id)]["data"]["name"]
                game_manager.add_installed_game(app_id, name)
                self._push("game_name_updated", {"app_id": app_id, "name": name})
        except Exception:
            pass

    def remove_game(self, app_id):
        steam_path = self._steam_path()
        try:
            lua_removed, manifest_removed = game_manager.remove_game_files(app_id, steam_path)
            lua_dir  = steam_utils.get_lua_dir(steam_path)
            dlc_ids  = steam_utils.get_dlc_ids(app_id)
            installer.remove_dlc_entries(lua_dir, dlc_ids)
            game_manager.remove_installed_game_entry(app_id)
            return {"ok": True, "lua": lua_removed, "manifests": manifest_removed}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def search_games(self, query):
        if not query or len(query) < 2:
            return []
        q = query.lower()
        local = [g for g in self._game_list if q in g["name"].lower()][:30]
        st_results = []
        try:
            r = requests.get(
                installer.ST_SEARCH_URL,
                params={"query": query},
                timeout=6,
                headers=installer.HEADERS,
            )
            if r.status_code == 200:
                data = r.json()
                apps = data if isinstance(data, list) else data.get("data", data.get("apps", []))
                seen_ids = {str(g.get("appid")) for g in local}
                for app in apps[:30]:
                    aid = str(app.get("appid") or app.get("app_id") or app.get("id") or "")
                    if not aid.isdigit() or aid in seen_ids:
                        continue
                    st_results.append({
                        "appid": aid,
                        "name":  app.get("name") or app.get("title") or f"App {aid}",
                    })
                    seen_ids.add(aid)
        except Exception:
            pass
        return (st_results + local)[:30]

    def get_total_games(self):
        return len(self._game_list)

    def get_popular_games(self):
        HARDWARE_IDS = {"1675200", "4165910"}
        try:
            r = requests.get(
                "https://store.steampowered.com/api/featuredcategories/?cc=US&l=english",
                timeout=8,
            )
            r.raise_for_status()
            data    = r.json()
            sellers = data.get("top_sellers", {}).get("items", [])
            results  = []
            seen_ids = set()
            for item in sellers:
                app_id = str(item.get("id", ""))
                name   = item.get("name", "")
                price  = item.get("final_price", 0) or 0
                itype  = item.get("type", 0)
                if not app_id or not app_id.isdigit():
                    continue
                if app_id in seen_ids or app_id in HARDWARE_IDS:
                    continue
                if price == 0 or itype != 0:
                    continue
                low = name.lower()
                if any(kw in low for kw in ("pack", "bundle", "collection", "dlc",
                                             "soundtrack", "artbook", "edition bonus")):
                    continue
                seen_ids.add(app_id)
                results.append({"appid": app_id, "name": name})
                if len(results) >= 20:
                    break
            if results:
                return results
        except Exception:
            pass
        return [g for g in self._game_list[:20]]

    def add_game_by_id(self, app_id):
        steam_path = self._steam_path()
        if not steam_path:
            return {"ok": False, "error": "Steam yolu ayarlanmamış."}
        threading.Thread(
            target=self._add_game_thread,
            args=(str(app_id), steam_path),
            daemon=True,
        ).start()
        return {"ok": True}

    def _add_game_thread(self, app_id, steam_path):
        try:
            self._push("install_progress", {"app_id": app_id, "step": "downloading"})
            result = installer.install_game(app_id, steam_path)
            game_manager.add_installed_game(
                app_id,
                result["game_name"],
                result["lua_files"],
                result["manifest_files"],
            )
            self._push("install_done", {
                "app_id":    app_id,
                "game_name": result["game_name"],
                "cover":     f"https://cdn.akamai.steamstatic.com/steam/apps/{app_id}/header.jpg",
            })
        except Exception:
            self._push("install_error", {
                "app_id": app_id,
                "error":  "Mevcut değil — Dosya Yükle sekmesinden ekleyin.",
            })

    def browse_game_files(self):
        import webview
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=(
                "Desteklenen Dosyalar (*.manifest;*.lua;*.zip)",
                "Zip Arşivleri (*.zip)",
                "Manifest ve Lua (*.manifest;*.lua)",
            ),
        )
        return list(result) if result else []

    def add_game_files(self, file_paths):
        steam_path = self._steam_path()
        if not steam_path:
            return {"ok": False, "error": "Steam yolu ayarlanmamış."}
        try:
            lua_total = manifest_total = 0
            zips  = [f for f in file_paths if f.lower().endswith(".zip")]
            indiv = [f for f in file_paths if f.lower().endswith((".lua", ".manifest"))]
            if indiv:
                lc, mc = installer.install_files(indiv, steam_path)
                lua_total += lc; manifest_total += mc
            for zp in zips:
                lc, mc = installer.extract_zip_files(zp, steam_path)
                lua_total += lc; manifest_total += mc
            return {"ok": True, "lua": lua_total, "manifests": manifest_total}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def add_dropped_files(self, files):
        import base64
        import tempfile
        steam_path = self._steam_path()
        if not steam_path:
            return {"ok": False, "error": "Steam yolu ayarlanmamış."}
        try:
            lua_total = manifest_total = 0
            for fi in files:
                name  = fi.get("name", "")
                b64   = fi.get("data", "")
                if not name or not b64:
                    continue
                data  = base64.b64decode(b64)
                lower = name.lower()
                if lower.endswith(".zip"):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                        tmp.write(data)
                        tp = tmp.name
                    try:
                        lc, mc = installer.extract_zip_files(tp, steam_path)
                        lua_total += lc; manifest_total += mc
                    finally:
                        if os.path.exists(tp):
                            os.remove(tp)
                elif lower.endswith(".lua"):
                    ld = os.path.join(steam_path, "config", "lua")
                    os.makedirs(ld, exist_ok=True)
                    with open(os.path.join(ld, os.path.basename(name)), "wb") as f:
                        f.write(data)
                    lua_total += 1
                elif lower.endswith(".manifest"):
                    dd = os.path.join(steam_path, "config", "depotcache")
                    os.makedirs(dd, exist_ok=True)
                    with open(os.path.join(dd, os.path.basename(name)), "wb") as f:
                        f.write(data)
                    manifest_total += 1
            return {"ok": True, "lua": lua_total, "manifests": manifest_total}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def restart_steam(self):
        steam_path = self._steam_path()
        if not steam_path or not os.path.exists(steam_path):
            return {"ok": False, "error": "Steam dizini bulunamadı."}
        try:
            steam_utils.restart_steam(steam_path)
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def download_hid_dll(self):
        steam_path = (
            self._steam_path()
            or steam_utils.detect_steam_path()
            or os.path.expanduser("~\\Desktop")
        )
        try:
            steam_utils.download_hid_dll(steam_path)
            return {"ok": True, "path": steam_path}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def remove_hid_dll(self):
        try:
            removed = steam_utils.remove_hid_dll()
            return {"ok": True, "removed": removed}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def check_dlls(self):
        steam_path = self._settings.get("steam_path")
        if not steam_path or not os.path.exists(steam_path):
            return {"installed": False, "msg": "Steam Yok"}
        d1 = os.path.join(steam_path, "dwmapi.dll")
        d2 = os.path.join(steam_path, "fadimrak.dll")
        if os.path.exists(d1) and os.path.exists(d2):
            return {"installed": True, "msg": "DLL Aktif"}
        return {"installed": False, "msg": "DLL Eksik"}

    def check_extractor(self):
        from core.onlinefix import check_extractor_available
        return check_extractor_available()

    def browse_fix_archive(self):
        import webview
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("Fix Arşivleri (*.rar;*.zip;*.7z)", "Tüm Dosyalar (*.*)"),
        )
        if result:
            path = result[0]
            return {
                "path": path,
                "name": os.path.basename(path),
                "ext":  os.path.splitext(path)[1].lower(),
            }
        return {"path": "", "name": "", "ext": ""}

    def browse_game_folder(self):
        import webview
        result = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if result:
            return {"path": result[0]}
        return {"path": ""}

    def of_search_games(self, query):
        threading.Thread(
            target=self._of_search_thread,
            args=(query,),
            daemon=True,
        ).start()
        return {"ok": True}

    def _of_search_thread(self, query):
        from core.onlinefix import search_onlinefix
        try:
            self._push("of_search_loading", {"query": query})
            result = search_onlinefix(query)
            if result.get("ok"):
                self._push("of_search_loaded", {
                    "query": query,
                    "results": result.get("results", []),
                    "count": result.get("count", 0),
                })
            else:
                self._push("of_search_error", {
                    "query": query,
                    "error": result.get("error", "Arama başarısız oldu."),
                })
        except Exception as e:
            self._push("of_search_error", {"query": query, "error": str(e)})

    def of_get_details(self, article_url):
        threading.Thread(
            target=self._of_details_thread,
            args=(article_url,),
            daemon=True,
        ).start()
        return {"ok": True}

    def _of_details_thread(self, article_url):
        from core.onlinefix import get_onlinefix_details
        try:
            self._push("of_details_loading", {"url": article_url})
            result = get_onlinefix_details(article_url)
            if result.get("ok"):
                self._push("of_details_loaded", result)
            else:
                self._push("of_details_error", {
                    "url": article_url,
                    "error": result.get("error", "Detaylar alınamadı."),
                })
        except Exception as e:
            self._push("of_details_error", {"url": article_url, "error": str(e)})

    def of_get_installed_steam_games(self):
        from core.onlinefix import get_installed_steam_games
        try:
            sp = self._steam_path()
            games = get_installed_steam_games(sp)
            return {"ok": True, "games": games}
        except Exception as e:
            return {"ok": False, "error": str(e), "games": []}

    def of_auto_match_dir(self, game_name, app_id=None):
        from core.onlinefix import auto_match_game_dir
        try:
            sp = self._steam_path()
            matched = auto_match_game_dir(game_name, app_id, sp)
            return {"ok": True, "path": matched or ""}
        except Exception as e:
            return {"ok": False, "error": str(e), "path": ""}

    def of_start_download_and_install(self, download_url, game_dir, backup=True):
        if not download_url or not game_dir:
            return {"ok": False, "error": "İndirme linki veya oyun klasörü belirtilmedi."}
        threading.Thread(
            target=self._of_download_install_thread,
            args=(download_url, game_dir, backup),
            daemon=True,
        ).start()
        return {"ok": True}

    def _of_download_install_thread(self, download_url, game_dir, backup):
        from core.onlinefix import download_fix_archive, install_fix
        try:
            # 1. Aşama: İndirme
            self._push("of_task_status", {
                "step": "downloading",
                "msg": "Fix arşivi resmi sunucudan indiriliyor...",
            })

            def on_dl_progress(d):
                self._push("of_download_progress", d)

            dl_res = download_fix_archive(download_url, progress_cb=on_dl_progress)
            if not dl_res.get("ok"):
                self._push("of_task_error", {"error": f"İndirme başarısız: {dl_res.get('error')}"})
                return

            archive_path = dl_res["file_path"]

            # 2. Aşama: Kurulum / Arşiv Çıkarma
            self._push("of_task_status", {
                "step": "installing",
                "msg": "Arşiv şifresiyle oyun klasörüne çıkartılıyor...",
            })

            def on_inst_progress(pct):
                self._push("of_install_progress", {"pct": pct})

            inst_res = install_fix(archive_path, game_dir, backup=backup, progress_cb=on_inst_progress)

            # Geçici dosyayı temizle
            if os.path.exists(archive_path):
                try:
                    os.remove(archive_path)
                except Exception:
                    pass

            if inst_res.get("ok"):
                self._push("of_task_done", {
                    "game_dir": game_dir,
                    "archive": dl_res.get("filename", ""),
                    "method": inst_res.get("method", ""),
                    "backup_count": inst_res.get("backup_count", 0),
                })
            else:
                self._push("of_task_error", {"error": f"Kurulum başarısız: {inst_res.get('error')}"})

        except Exception as e:
            self._push("of_task_error", {"error": str(e)})

    def of_uninstall_fix(self, game_dir):
        from core.onlinefix import uninstall_fix
        try:
            return uninstall_fix(game_dir)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def of_launch_game(self, game_dir):
        from core.onlinefix import launch_game_executable
        try:
            return launch_game_executable(game_dir)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def of_install_spacewar(self):
        try:
            import webbrowser
            webbrowser.open("steam://install/480")
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def install_online_fix(self, archive_path, game_dir):
        if not archive_path or not game_dir:
            return {"ok": False, "error": "Arşiv veya oyun klasörü belirtilmedi."}
        threading.Thread(
            target=self._install_fix_thread,
            args=(archive_path, game_dir),
            daemon=True,
        ).start()
        return {"ok": True}

    def _install_fix_thread(self, archive_path, game_dir):
        from core.onlinefix import install_fix
        def on_progress(pct):
            self._push("fix_progress", {"pct": pct})
        try:
            self._push("fix_progress", {"pct": 0})
            result = install_fix(archive_path, game_dir, backup=True, progress_cb=on_progress)
            if result["ok"]:
                self._push("fix_done", {
                    "method":   result.get("method", ""),
                    "game_dir": game_dir,
                    "archive":  os.path.basename(archive_path),
                })
            else:
                self._push("fix_error", {"error": result["error"]})
        except Exception as e:
            self._push("fix_error", {"error": str(e)})

    def sam_get_achievements(self, app_id: str, use_account: bool = True):
        app_id = str(app_id)
        steam_id = self._session.steam_id if (use_account and self._session.is_configured) else ""
        api_key  = self._session.api_key  if (use_account and self._session.is_configured) else ""
        threading.Thread(
            target=self._sam_fetch_thread,
            args=(app_id, steam_id, api_key),
            daemon=True,
        ).start()
        return {"ok": True}

    def _sam_fetch_thread(self, app_id, steam_id, api_key):
        try:
            self._push("sam_loading", {"app_id": app_id})

            def _progress(pct):
                self._push("sam_progress", {"app_id": app_id, "pct": pct})

            result = achievement_manager.get_achievements_combined(
                app_id, steam_id, api_key, progress_cb=_progress
            )

            steam_path  = self._steam_path()
            api_results = {}
            if steam_path:
                try:
                    api_list = achievement_manager.read_achievements_via_api(app_id, steam_path)
                    api_results = {a["name"]: a["achieved"] for a in api_list}
                except Exception:
                    pass

            lua_unlocked = set(achievement_manager.get_lua_unlocked(app_id, steam_path))

            for ach in result["achievements"]:
                n = ach["name"]
                if n in api_results:
                    ach["achieved"]     = api_results[n]
                    ach["source"]       = "steamapi"
                ach["lua_unlocked"] = (n in lua_unlocked)

            self._push("sam_loaded", {
                "app_id":       app_id,
                "achievements": result["achievements"],
                "total":        result["total"],
                "unlocked":     result["unlocked"],
            })
        except Exception as e:
            self._push("sam_error", {"app_id": app_id, "error": str(e)})

    def sam_unlock(self, app_id: str, ach_names: list):
        steam_path = self._steam_path()
        if not steam_path:
            return {"ok": False, "error": "Steam yolu ayarlanmamış."}
        if isinstance(ach_names, str):
            ach_names = [ach_names]
        result = achievement_manager.unlock_achievements(str(app_id), ach_names, steam_path)
        if result["ok"]:
            self._push("sam_unlock_done", {
                "app_id":  str(app_id),
                "names":   ach_names,
                "method":  result.get("method", ""),
                "warning": result.get("warning", ""),
            })
        return result

    def sam_lock(self, app_id: str, ach_names: list):
        steam_path = self._steam_path()
        if not steam_path:
            return {"ok": False, "error": "Steam yolu ayarlanmamış."}
        if isinstance(ach_names, str):
            ach_names = [ach_names]
        result = achievement_manager.lock_achievements(str(app_id), ach_names, steam_path)
        if result["ok"]:
            self._push("sam_lock_done", {
                "app_id":  str(app_id),
                "names":   ach_names,
                "method":  result.get("method", ""),
                "warning": result.get("warning", ""),
            })
        return result

    def sam_unlock_all(self, app_id: str):
        steam_path = self._steam_path()
        if not steam_path:
            return {"ok": False, "error": "Steam yolu ayarlanmamış."}
        threading.Thread(
            target=self._sam_unlock_all_thread,
            args=(str(app_id), steam_path),
            daemon=True,
        ).start()
        return {"ok": True}

    def _sam_unlock_all_thread(self, app_id, steam_path):
        try:
            self._push("sam_loading", {"app_id": app_id})
            result = achievement_manager.unlock_all_achievements(app_id, steam_path)
            self._push("sam_unlock_all_done", {
                "app_id": app_id,
                "ok":     result["ok"],
                "method": result.get("method", ""),
                "error":  result.get("error", ""),
            })
        except Exception as e:
            self._push("sam_error", {"app_id": app_id, "error": str(e)})

    def sam_lock_all(self, app_id: str):
        steam_path = self._steam_path()
        if not steam_path:
            return {"ok": False, "error": "Steam yolu ayarlanmamış."}
        result = achievement_manager.lock_all_achievements(str(app_id), steam_path)
        if result["ok"]:
            self._push("sam_lock_all_done", {
                "app_id": str(app_id),
                "method": result.get("method", ""),
            })
        return result

    def sam_get_game_list(self):
        games = []
        if self._session.is_configured:
            try:
                raw_games = self._session.get_games()
                games = [
                    {
                        "appid": g["appid"],
                        "name":  g["name"],
                        "cover": g.get("cover") or f"https://cdn.akamai.steamstatic.com/steam/apps/{g['appid']}/header.jpg"
                    }
                    for g in raw_games
                ]
            except Exception:
                pass
        
        if not games:
            steam_path = self._steam_path()
            app_ids    = game_manager.get_installed_app_ids(steam_path)
            installed  = game_manager.load_installed_games()
            for aid in app_ids:
                entry = installed.get(aid, {})
                name  = entry.get("name", f"Game {aid}") if isinstance(entry, dict) else str(entry)
                games.append({
                    "appid": int(aid) if str(aid).isdigit() else aid,
                    "name":  name,
                    "cover": f"https://cdn.akamai.steamstatic.com/steam/apps/{aid}/header.jpg"
                })

        filtered_games = achievement_manager.filter_games_with_achievements(games)
        return {
            "ok":     True,
            "source": "steam" if self._session.is_configured else "local",
            "games":  filtered_games,
            "total":  len(filtered_games),
        }

    def idle_get_game_list(self):
        if self._session.is_configured:
            try:
                games = list(self._session.get_games())
                badge_map = steam_account.get_all_badges_map(self._session.steam_id, self._session.api_key)
                for g in games:
                    aid = str(g["appid"])
                    rem = badge_map.get(aid, 0)
                    g["cards_remaining"] = rem
                    g["has_drops"] = rem > 0
                return {"ok": True, "games": games, "total": len(games), "source": "steam"}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        steam_path = self._steam_path()
        app_ids    = game_manager.get_installed_app_ids(steam_path)
        installed  = game_manager.load_installed_games()
        games = []
        for aid in app_ids:
            entry = installed.get(aid, {})
            name  = entry.get("name", f"Game {aid}") if isinstance(entry, dict) else str(entry)
            games.append({
                "appid": int(aid) if str(aid).isdigit() else aid,
                "name":  name,
                "cover": f"https://cdn.akamai.steamstatic.com/steam/apps/{aid}/header.jpg",
                "playtime_forever": 0,
                "cards_remaining": 0,
                "has_drops": False,
            })
        if games:
            return {"ok": True, "games": games, "total": len(games), "source": "local"}

        return {
            "ok":         False,
            "error":      "Steam hesabı bağlı değil.",
            "need_login": True,
        }

    def idle_refresh_game_list(self):
        if not self._session.is_configured:
            return {"ok": False, "error": "Hesap bağlı değil."}
        threading.Thread(
            target=self._idle_refresh_thread,
            daemon=True,
        ).start()
        return {"ok": True}

    def _idle_refresh_thread(self):
        try:
            self._push("idle_games_loading", {})
            games = self._session.get_games(force_refresh=True)
            self._push("idle_games_loaded", {
                "games": games,
                "total": len(games),
            })
        except Exception as e:
            self._push("idle_games_error", {"error": str(e)})

    def idle_start(self, app_id: str, game_name: str = ""):
        steam_path = self._steam_path()
        farmer     = idle_farmer.get_farmer()
        result     = farmer.start_idle(str(app_id), game_name, steam_path)
        if result["ok"]:
            self._push("idle_started", {
                "app_id": str(app_id),
                "name":   game_name or f"App {app_id}",
            })
            threading.Thread(
                target=self._idle_ticker_thread,
                args=(str(app_id),),
                daemon=True,
            ).start()
            if self._tray:
                self._tray.update_menu()
                self._tray.notify(
                    "Kart Kasma Başladı",
                    f"{game_name or f'App {app_id}'} kasılmaya başlandı.",
                )
        return result

    def _idle_ticker_thread(self, app_id):
        farmer = idle_farmer.get_farmer()
        tray_tick = 0
        while farmer.is_idling(app_id):
            elapsed = farmer.get_elapsed(app_id)
            self._push("idle_tick", {
                "app_id":          str(app_id),
                "elapsed_seconds": elapsed,
                "elapsed_str":     idle_farmer.format_elapsed(elapsed),
            })
            tray_tick += 1
            if self._tray and tray_tick >= 10:
                tray_tick = 0
                self._tray.update_menu()
            time.sleep(1.0)

    def idle_stop(self, app_id: str):
        farmer = idle_farmer.get_farmer()
        result = farmer.stop_idle(str(app_id))
        if result["ok"]:
            self._push("idle_stopped", {
                "app_id":      str(app_id),
                "elapsed_str": idle_farmer.format_elapsed(result["elapsed_seconds"]),
            })
            if self._tray:
                self._tray.update_menu()
        return result

    def idle_stop_all(self):
        farmer = idle_farmer.get_farmer()
        result = farmer.stop_all()
        self._push("idle_all_stopped", {"stopped": result.get("stopped", [])})
        if self._tray:
            self._tray.update_menu()
        return result

    def idle_get_status(self):
        farmer = idle_farmer.get_farmer()
        status = farmer.get_status()
        for entry in status:
            entry["elapsed_str"] = idle_farmer.format_elapsed(entry["elapsed_seconds"])
        return {"ok": True, "running": status}

    def idle_minimize_to_tray(self):
        if self._tray and self._tray.available:
            self._tray.minimize_to_tray()
            return {"ok": True}
        return {"ok": False, "error": "System tray kullanılamıyor (pystray kurulu değil)."}

    def idle_get_card_info(self, app_id: str):
        sid = self._session.steam_id if self._session.is_configured else ""
        key = self._session.api_key  if self._session.is_configured else ""
        threading.Thread(
            target=lambda: self._push("idle_card_info", {
                "app_id": str(app_id),
                **idle_farmer.get_card_info(app_id, sid, key),
            }),
            daemon=True,
        ).start()
        return {"ok": True}

    def idle_get_cards_batch(self, app_ids: list):
        if isinstance(app_ids, str):
            app_ids = [app_ids]
        sid = self._session.steam_id if self._session.is_configured else ""
        key = self._session.api_key  if self._session.is_configured else ""
        threading.Thread(
            target=lambda: self._push("idle_cards_batch", {
                "results": idle_farmer.get_cards_batch([str(a) for a in app_ids], sid, key)
            }),
            daemon=True,
        ).start()
        return {"ok": True}

    def tray_is_available(self):
        return {"available": self._tray.available if self._tray else False}

    def tray_minimize(self):
        return self.idle_minimize_to_tray()

    # ── DLC Unlocker ──────────────────────────────────────────────

    def dlc_fetch(self, app_id: str):
        """Steam Store'dan oyunun DLC listesini çeker."""
        app_id = str(app_id).strip()
        if not app_id.isdigit():
            return {"ok": False, "error": "Geçersiz App ID."}
        threading.Thread(
            target=self._dlc_fetch_thread,
            args=(app_id,),
            daemon=True,
        ).start()
        return {"ok": True}

    def _dlc_fetch_thread(self, app_id: str):
        self._push("dlc_loading", {"app_id": app_id})
        try:
            result = dlc_unlocker.fetch_dlc_list(app_id)
            if not result["ok"]:
                self._push("dlc_error", {"error": result["error"]})
                return

            steam_path = self._steam_path()
            unlocked   = dlc_unlocker.get_unlocked_dlcs(steam_path) if steam_path else set()

            for d in result["dlc_list"]:
                d["unlocked"] = d["dlc_id"] in unlocked

            self._push("dlc_loaded", {
                "app_id":    app_id,
                "game_name": result["game_name"],
                "dlc_list":  result["dlc_list"],
                "total":     len(result["dlc_list"]),
            })
        except Exception as e:
            self._push("dlc_error", {"error": str(e)})

    def dlc_unlock(self, app_id: str, dlc_ids: list):
        """Seçilen DLC'leri marcellus.lua'ya ekler."""
        steam_path = self._steam_path()
        if not steam_path:
            return {"ok": False, "error": "Steam yolu ayarlanmamış."}
        if isinstance(dlc_ids, str):
            dlc_ids = [dlc_ids]
        result = dlc_unlocker.unlock_dlcs(steam_path, dlc_ids)
        return result

    def dlc_lock(self, app_id: str, dlc_ids: list):
        """Seçilen DLC'leri marcellus.lua'dan kaldırır."""
        steam_path = self._steam_path()
        if not steam_path:
            return {"ok": False, "error": "Steam yolu ayarlanmamış."}
        if isinstance(dlc_ids, str):
            dlc_ids = [dlc_ids]
        result = dlc_unlocker.lock_dlcs(steam_path, dlc_ids)
        return result

    def dlc_unlock_all(self, app_id: str):
        """Oyunun tüm DLC'lerini otomatik unlock eder."""
        steam_path = self._steam_path()
        if not steam_path:
            return {"ok": False, "error": "Steam yolu ayarlanmamış."}
        threading.Thread(
            target=self._dlc_unlock_all_thread,
            args=(str(app_id), steam_path),
            daemon=True,
        ).start()
        return {"ok": True}

    def _dlc_unlock_all_thread(self, app_id: str, steam_path: str):
        self._push("dlc_loading", {"app_id": app_id})
        try:
            result = dlc_unlocker.unlock_all_dlcs(steam_path, app_id)
            if result["ok"]:
                # Güncel unlock listesini push et
                unlocked = dlc_unlocker.get_unlocked_dlcs(steam_path)
                self._push("dlc_unlock_all_done", {
                    "app_id":    app_id,
                    "game_name": result.get("game_name", ""),
                    "added":     result.get("added", 0),
                    "skipped":   result.get("skipped", 0),
                    "total":     result.get("total", 0),
                    "unlocked":  list(unlocked),
                })
            else:
                self._push("dlc_error", {"error": result.get("error", "Bilinmeyen hata.")})
        except Exception as e:
            self._push("dlc_error", {"error": str(e)})

    def dlc_get_unlocked(self, app_id: str):
        """Şu an açık olan DLC ID listesini döndürür."""
        steam_path = self._steam_path()
        if not steam_path:
            return {"ok": False, "error": "Steam yolu ayarlanmamış."}
        unlocked = dlc_unlocker.get_unlocked_dlcs(steam_path)
        return {"ok": True, "unlocked": list(unlocked)}
