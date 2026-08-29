"""
System Tray Yöneticisi
=======================
Idle Farm açıkken uygulama system tray'e eklenir ve arka planda çalışmaya devam eder.
Pencere kapatıldığında tray'e küçülür, "Çıkış" seçilirse tamamen kapanır.

Bağımlılık: pystray + Pillow
  pip install pystray pillow

pystray olmadan: tray devre dışı kalır, normal kapanma davranışı sürer.
"""

import os
import sys
import threading
import base64

# ── Tray ikonu (gömülü base64 PNG — 32x32 siyah Steam simgesi) ───────────────
# Ayrı bir .ico dosyasına gerek yok, logo.png'yi kullanacağız.

_tray_available = False
try:
    import pystray
    from PIL import Image
    _tray_available = True
except ImportError:
    pass


def _load_icon_image(static_dir: str = "") -> "Image.Image | None":
    """
    Tray ikonu için PIL Image yükler.
    Önce logo.png'yi dener, bulamazsa basit bir kare oluşturur.
    """
    if not _tray_available:
        return None

    candidates = []
    if static_dir:
        candidates.append(os.path.join(static_dir, "logo.png"))
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(sys._MEIPASS, "static", "logo.png"))
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.append(os.path.join(base, "ui_web", "static", "logo.png"))

    for path in candidates:
        if os.path.exists(path):
            try:
                img = Image.open(path).convert("RGBA").resize((32, 32))
                return img
            except Exception:
                pass

    # Fallback: basit mavi kare
    try:
        img = Image.new("RGBA", (32, 32), color=(28, 60, 140, 255))
        return img
    except Exception:
        return None


class TrayManager:
    """
    System tray yöneticisi.
    - Idle Farm çalışırken "x" butonuna basınca tray'e küçülür.
    - Tray menu: Göster | Kasılan Oyunlar | Çıkış
    """

    def __init__(self, static_dir: str = ""):
        self._icon         = None
        self._window       = None   # pywebview window
        self._static_dir   = static_dir
        self._idle_farmer  = None   # idle_farmer modülü referansı
        self._lock         = threading.Lock()
        self._minimized    = False
        self._running      = False
        self._on_quit_cb   = None   # gerçek çıkış callback'i
        self._stop_idle_cb = None   # idle_stop_all bridge callback'i

    def set_window(self, window):
        self._window = window

    def set_idle_farmer(self, farmer_module):
        self._idle_farmer = farmer_module

    def set_quit_callback(self, cb):
        self._on_quit_cb = cb

    def set_stop_idle_callback(self, cb):
        """bridge.idle_stop_all'ı bağlamak için — UI'a event push eder."""
        self._stop_idle_cb = cb

    @property
    def available(self) -> bool:
        return _tray_available

    # ── Menü oluştur ──────────────────────────────────────────────

    def _build_menu(self):
        """Dinamik tray menüsü — aktif kasılan oyunlar, kontroller ve çıkış."""
        items = []

        # Başlık (tıklanınca pencereyi gösterir)
        items.append(pystray.MenuItem(
            "Fadimrak Steam Tool",
            self._show_window,
            default=True,
            enabled=True,
        ))
        items.append(pystray.Menu.SEPARATOR)

        # Kasılan oyunlar bölümü
        if self._idle_farmer:
            try:
                farmer  = self._idle_farmer.get_farmer()
                running = farmer.get_status()
                if running:
                    items.append(pystray.MenuItem("── Aktif Kasma ──", None, enabled=False))
                    for entry in running[:8]:
                        elapsed = self._idle_farmer.format_elapsed(entry["elapsed_seconds"])
                        name    = entry["name"][:28]
                        label   = f"  {name}  ({elapsed})"
                        items.append(pystray.MenuItem(label, None, enabled=False))
                    items.append(pystray.Menu.SEPARATOR)
                    # Tümünü durdur butonu (yalnızca aktif kasma varsa)
                    items.append(pystray.MenuItem(
                        "Kart & Saat Kasımı Durdur",
                        self._stop_all_idle,
                    ))
                    items.append(pystray.Menu.SEPARATOR)
            except Exception:
                pass

        # Pencere kontrolleri
        items.append(pystray.MenuItem("Pencereyi Göster", self._show_window))
        items.append(pystray.MenuItem("Pencereyi Gizle",  self._hide_window))
        items.append(pystray.Menu.SEPARATOR)

        # Uygulama çıkışı
        items.append(pystray.MenuItem("Çıkış", self._quit))

        return pystray.Menu(*items)

    # ── Eylemler ─────────────────────────────────────────────────

    def _show_window(self, icon=None, item=None):
        if self._window:
            try:
                self._window.show()
                self._window.restore()
            except Exception:
                pass
        self._minimized = False

    def _hide_window(self, icon=None, item=None):
        if self._window:
            try:
                self._window.hide()
            except Exception:
                pass
        self._minimized = True

    def _stop_all_idle(self, icon=None, item=None):
        """Tüm aktif kart/saat kasmayı durdurur, UI'a event push eder ve menüyü yeniler."""
        if self._stop_idle_cb:
            # bridge.idle_stop_all() çağrılır → farmer.stop_all() + _push("idle_all_stopped")
            try:
                self._stop_idle_cb()
            except Exception:
                pass
        elif self._idle_farmer:
            # Callback bağlı değilse doğrudan durdur (fallback)
            try:
                self._idle_farmer.get_farmer().stop_all()
            except Exception:
                pass
        self.update_menu()

    def _quit(self, icon=None, item=None):
        """Gerçek çıkış — önce idle'ları durdur, sonra kapat."""
        # Kasılan oyunları durdur
        if self._idle_farmer:
            try:
                self._idle_farmer.get_farmer().stop_all()
            except Exception:
                pass

        # Tray'i durdur
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

        # Özel çıkış callback'i (bridge._full_shutdown → os._exit(0))
        if self._on_quit_cb:
            try:
                self._on_quit_cb()
            except Exception:
                pass

        # Callback yoksa ya da çalışmazsa zorla kapat
        import os as _os
        _os._exit(0)

    # ── Başlat / Durdur ───────────────────────────────────────────

    def start(self):
        """Tray'i arka plan thread'inde başlatır."""
        if not _tray_available:
            return
        if self._running:
            return

        image = _load_icon_image(self._static_dir)
        if not image:
            return

        self._icon = pystray.Icon(
            name    = "FadimrakSteamTool",
            icon    = image,
            title   = "Fadimrak Steam Tool",
            menu    = self._build_menu(),
        )
        self._running = True

        def _run():
            try:
                self._icon.run()
            except Exception:
                pass
            self._running = False

        threading.Thread(target=_run, daemon=True, name="TrayThread").start()

    def stop(self):
        """Tray'i durdurur."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
        self._running = False

    def update_menu(self):
        """Menüyü yeniler (idle durumu değişince çağrılır)."""
        if self._icon and self._running:
            try:
                self._icon.menu = self._build_menu()
                self._icon.update_menu()
            except Exception:
                pass

    def notify(self, title: str, message: str):
        """Bildirim baloncuğu gösterir."""
        if self._icon and self._running:
            try:
                self._icon.notify(message, title)
            except Exception:
                pass

    def minimize_to_tray(self):
        """Pencereyi tray'e küçültür."""
        self._hide_window()
        self.notify("Fadimrak Steam Tool", "Arka planda çalışmaya devam ediyor.")

    def is_running(self) -> bool:
        return self._running


# ── Singleton ─────────────────────────────────────────────────────────────────
_tray_instance: TrayManager | None = None
_tray_lock = threading.Lock()


def get_tray(static_dir: str = "") -> TrayManager:
    global _tray_instance
    with _tray_lock:
        if _tray_instance is None:
            _tray_instance = TrayManager(static_dir)
        return _tray_instance
