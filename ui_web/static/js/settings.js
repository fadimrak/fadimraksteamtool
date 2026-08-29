/**
 * Settings & System Controls Module
 */

async function settingsInit() {
  // Tray butonunu yalnızca pystray mevcutsa göster (ayarlar sayfası + sidebar)
  try {
    const trayRes = await pywebview.api.tray_is_available();
    const available = trayRes.available;

    // Ayarlar sayfasındaki buton
    const trayWrap = document.getElementById('tray-btn-wrap');
    if (trayWrap) trayWrap.style.display = available ? '' : 'none';

    // Sidebar butonu
    const traySidebar = document.getElementById('tray-sidebar-btn');
    if (traySidebar) traySidebar.style.display = available ? '' : 'none';
  } catch (e) {}
}

async function browseSteam() {
  const res = await pywebview.api.browse_steam_folder();
  if (res && res.path) {
    document.getElementById('steam-path').value = res.path;
  }
}

async function autoDetect() {
  const res = await pywebview.api.detect_steam_path();
  if (res && res.path) {
    document.getElementById('steam-path').value = res.path;
    toast('success', 'Bulundu', res.path);
    checkDllStatus();
  } else {
    toast('warn', 'Bulunamadı', 'Steam otomatik tespit edilemedi.');
  }
}

async function savePath() {
  const path = document.getElementById('steam-path').value.trim();
  const res  = await pywebview.api.save_settings(path);
  if (res && res.ok) {
    toast('success', 'Kaydedildi', path);
    checkDllStatus();
  } else {
    toast('error', 'Hata', 'Kaydedilemedi.');
  }
}

async function restartSteam() {
  toast('info', 'Yeniden Başlatılıyor…', 'Steam kapatılıp tekrar açılıyor.');
  const res = await pywebview.api.restart_steam();
  if (res && res.ok) {
    toast('success', 'Başarılı', 'Steam yeniden başlatıldı.');
  } else {
    toast('error', 'Hata', res.error || 'Steam başlatılamadı.');
  }
}

async function downloadDll() {
  toast('info', 'İndiriliyor…', 'DLL dosyaları yükleniyor.');
  const res = await pywebview.api.download_hid_dll();
  if (res && res.ok) {
    toast('success', 'Tamamlandı', 'DLL dosyaları kuruldu.');
    checkDllStatus();
  } else {
    toast('error', 'Hata', res.error || 'DLL indirilemedi.');
  }
}

async function removeDll() {
  const ok = await confirm2('DLL Kaldır', 'Crack DLL dosyaları Steam dizininden kaldırılacak.');
  if (!ok) return;
  const res = await pywebview.api.remove_hid_dll();
  if (res && res.ok) {
    toast('info', 'Kaldırıldı', `${res.removed} DLL dosyası silindi.`);
    checkDllStatus();
  } else {
    toast('error', 'Hata', res.error || 'DLL kaldırılamadı.');
  }
}

async function checkDllStatus() {
  try {
    const res = await pywebview.api.check_dlls();
    const dot  = document.getElementById('dll-dot');
    const text = document.getElementById('dll-text');
    if (dot && text) {
      if (res && res.installed) {
        dot.className = 'dll-status-dot active';
        text.textContent = res.msg || 'DLL Aktif';
      } else {
        dot.className = 'dll-status-dot';
        text.textContent = res.msg || 'DLL Eksik';
      }
    }
  } catch (e) {}
}

async function checkUpdate() {
  try {
    const res = await pywebview.api.check_for_updates();
    if (res && res.has_update) {
      const b = document.getElementById('update-banner');
      if (b) b.classList.remove('hidden');
    }
  } catch (e) {}
}

async function openGithub() {
  const url = await pywebview.api.get_project_github_url();
  if (url) pywebview.api.open_in_browser(url);
}
