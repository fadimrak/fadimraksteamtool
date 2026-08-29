/**
 * Settings & System Controls Module
 */

async function settingsInit() {
  try {
    const trayRes = await pywebview.api.tray_is_available();
    const available = trayRes.available;

    const trayWrap = document.getElementById('tray-btn-wrap');
    if (trayWrap) trayWrap.style.display = available ? '' : 'none';

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
    toast('success', t('settings.toast_detected'), res.path);
    checkDllStatus();
  } else {
    toast('warn', t('toast.warn'), t('settings.toast_not_detected'));
  }
}

async function savePath() {
  const path = document.getElementById('steam-path').value.trim();
  const res  = await pywebview.api.save_settings(path);
  if (res && res.ok) {
    toast('success', t('settings.toast_saved'), path);
    checkDllStatus();
  } else {
    toast('error', t('toast.error'), t('settings.toast_save_err'));
  }
}

async function restartSteam() {
  toast('info', t('toast.restarting'), t('settings.toast_restarting'));
  const res = await pywebview.api.restart_steam();
  if (res && res.ok) {
    toast('success', t('toast.success'), t('settings.toast_restarted'));
  } else {
    toast('error', t('toast.error'), res.error || t('settings.toast_save_err'));
  }
}

async function downloadDll() {
  toast('info', t('toast.downloading'), t('settings.toast_downloading_dll'));
  const res = await pywebview.api.download_hid_dll();
  if (res && res.ok) {
    toast('success', t('toast.completed'), t('settings.toast_dll_installed'));
    checkDllStatus();
  } else {
    toast('error', t('toast.error'), res.error || t('settings.toast_save_err'));
  }
}

async function removeDll() {
  const ok = await confirm2(t('settings.confirm_remove_dll_title'), t('settings.confirm_remove_dll_msg'));
  if (!ok) return;
  const res = await pywebview.api.remove_hid_dll();
  if (res && res.ok) {
    toast('info', t('toast.removed'), t('settings.toast_dll_removed', { count: res.removed }));
    checkDllStatus();
  } else {
    toast('error', t('toast.error'), res.error || t('settings.toast_save_err'));
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
        text.textContent = t('nav.dll_active');
      } else {
        dot.className = 'dll-status-dot';
        text.textContent = res && res.msg === 'Steam Yok' ? t('nav.steam_missing') : t('nav.dll_missing');
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
