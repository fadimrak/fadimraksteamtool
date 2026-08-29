/**
 * Online-Fix Installer Module
 */

let ofArchivePath = '';
let ofGameDir     = '';

async function ofInit() {
  try {
    const info = await pywebview.api.check_extractor();
    const warn = document.getElementById('of-extractor-warn');
    if (warn) {
      if (!info.rar) warn.classList.remove('hidden');
      else           warn.classList.add('hidden');
    }
  } catch (e) {}
}

async function ofSelectArchive() {
  const res = await pywebview.api.browse_fix_archive();
  if (!res || !res.path) return;
  ofArchivePath = res.path;

  const info = document.getElementById('of-archive-info');
  document.getElementById('of-archive-name').textContent = res.name;
  document.getElementById('of-archive-ext').textContent  = res.ext.toUpperCase();
  if (info) info.classList.remove('hidden');
  document.getElementById('of-num1')?.classList.add('done');

  _ofUpdateInstallBtn();
}

async function ofSelectGameDir() {
  const res = await pywebview.api.browse_game_folder();
  if (!res || !res.path) return;
  ofGameDir = res.path;

  const info = document.getElementById('of-gamedir-info');
  document.getElementById('of-gamedir-path').textContent = res.path;
  if (info) info.classList.remove('hidden');
  document.getElementById('of-num2')?.classList.add('done');

  _ofUpdateInstallBtn();
}

function _ofUpdateInstallBtn() {
  const btn = document.getElementById('of-install-btn');
  if (btn) btn.disabled = !(ofArchivePath && ofGameDir);
}

async function ofInstall() {
  if (!ofArchivePath || !ofGameDir) return;

  const btn     = document.getElementById('of-install-btn');
  const section = document.getElementById('of-progress-section');
  const bar     = document.getElementById('of-progress-bar');
  const label   = document.getElementById('of-progress-label');

  if (btn) {
    btn.disabled    = true;
    btn.textContent = t('onlinefix.btn_installing');
  }
  if (bar) {
    bar.style.width = '0%';
    bar.style.background = 'var(--success)';
  }
  if (label) {
    label.textContent = t('onlinefix.label_starting');
    label.style.color = 'var(--muted)';
  }
  if (section) section.classList.remove('hidden');

  const res = await pywebview.api.install_online_fix(ofArchivePath, ofGameDir);
  if (!res.ok) {
    if (label) {
      label.textContent = `${t('toast.error')}: ${res.error}`;
      label.style.color = 'var(--danger)';
    }
    if (btn) {
      btn.textContent = t('onlinefix.btn_install');
      btn.disabled    = false;
    }
    toast('error', t('onlinefix.toast_err'), res.error);
  }
}
