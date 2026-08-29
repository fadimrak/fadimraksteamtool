/**
 * Core Application Engine & Event Dispatcher
 */

// ── State ──────────────────────────────────────────────────────────
let currentPage    = 'library';
let installedGames = [];
let ctxTarget      = null;

// ── Image helpers ──────────────────────────────────────────────────
const CDNS = [
  id => `https://cdn.akamai.steamstatic.com/steam/apps/${id}/header.jpg`,
  id => `https://cdn.cloudflare.steamstatic.com/steam/apps/${id}/header.jpg`,
  id => `https://cdn.akamai.steamstatic.com/steam/apps/${id}/capsule_231x87.jpg`,
];

function attachImg(img, appId) {
  img.dataset.appId = appId;
  img.style.cssText = 'opacity:0;transition:opacity .25s ease;';
  img.onload  = function() {
    if (this.naturalWidth < 16 || this.naturalHeight < 16) { imgErr(this, appId); return; }
    if (this._t) { clearTimeout(this._t); this._t = null; }
    this.style.opacity = '1';
  };
  img.onerror = function() { imgErr(this, appId); };
  img._t = setTimeout(() => imgErr(img, appId), 6000);
}

function imgErr(img, appId) {
  if (img._t) { clearTimeout(img._t); img._t = null; }
  const step = parseInt(img.dataset.step || '0', 10);
  img.dataset.step = String(step + 1);
  if (step < CDNS.length) {
    img.src = CDNS[step](appId);
    img._t = setTimeout(() => imgErr(img, appId), 6000);
  } else {
    img.src = 'logo.png';
    img.style.cssText = 'opacity:.3;padding:16px;object-fit:contain;background:var(--bg3);';
    img._placeholder = true;
  }
}

// ── Init & Boot ────────────────────────────────────────────────────
window.addEventListener('pywebviewready', async () => {
  const legal = await pywebview.api.get_legal_status();
  if (!legal.accepted) {
    document.getElementById('legal-modal').classList.remove('hidden');
  } else {
    boot();
  }
  window.addEventListener('focus', () => {
    if (currentPage === 'library') loadLibrary();
  });
});

async function acceptLegal() {
  await pywebview.api.accept_legal();
  document.getElementById('legal-modal').classList.add('hidden');
  boot();
}
async function rejectLegal() { await pywebview.api.reject_legal(); }

async function boot() {
  const splash = document.getElementById('splash');
  const fill   = document.getElementById('splash-fill');
  const sleep  = ms => new Promise(r => setTimeout(r, ms));

  fill.style.width = '20%';
  await sleep(400);
  const vd = await pywebview.api.get_version();
  document.getElementById('sidebar-ver').textContent = 'v' + vd.version;
  const settingsVerEl = document.getElementById('settings-ver');
  if (settingsVerEl) settingsVerEl.textContent = 'v' + vd.version;

  // Settings & Language
  const s = await pywebview.api.get_settings();
  if (s && s.lang) {
    setLanguage(s.lang, false);
  } else {
    setLanguage('tr', false);
  }

  fill.style.width = '55%';
  await loadLibrary();

  fill.style.width = '80%';
  checkUpdate();
  if (s && s.steam_path) {
    const spInput = document.getElementById('steam-path');
    if (spInput) spInput.value = s.steam_path;
    document.getElementById('sidebar-steam').textContent = 'steam';
    document.getElementById('sidebar-steam').style.color = 'var(--success)';
  }

  doSearch('');
  fill.style.width = '100%';
  checkDllStatus();
  settingsInit(); // Tray butonlarını boot'ta kontrol et

  await sleep(400);
  splash.classList.add('hidden');
}

// ── Navigation ─────────────────────────────────────────────────────
function navigateTo(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + page)?.classList.add('active');
  document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');
  currentPage = page;
  if (page === 'library')    loadLibrary();
  if (page === 'onlinefix')  ofInit();
  if (page === 'sam')        samInit();
  if (page === 'idle')       idleInit();
  if (page === 'account')    accountInit();
  if (page === 'settings')   settingsInit();
  if (page === 'dlc')        dlcInit();
}

// ── Python Push Events ─────────────────────────────────────────────
window.onPythonEvent = function({ event, data }) {
  switch (event) {
    case 'install_progress': {
      const btn = document.querySelector(`#result-${data.app_id} .install-btn`);
      if (btn) btn.textContent = data.step === 'downloading' ? t('add.btn_downloading') : t('add.btn_installing');
      break;
    }
    case 'install_done': {
      toast('success', t('add.toast_installed'), data.game_name);
      const btn = document.querySelector(`#result-${data.app_id} .install-btn`);
      if (btn) { btn.className = 'btn btn-ghost btn-sm'; btn.textContent = t('add.btn_installed'); btn.disabled = true; }
      installedGames.push({ app_id: data.app_id, name: data.game_name, cover: data.cover });
      if (currentPage === 'library') renderLibrary(installedGames);
      break;
    }
    case 'install_error': {
      const errMsg = (data.error && data.error.includes('Mevcut değil')) ? t('add.toast_err_unavailable') : (data.error || '');
      toast('error', t('add.toast_install_err'), errMsg);
      const btn = document.querySelector(`#result-${data.app_id} .install-btn`);
      if (btn) { btn.className = 'btn btn-primary btn-sm'; btn.textContent = t('add.btn_download'); btn.disabled = false; }
      break;
    }
    case 'game_name_updated': {
      const card = document.querySelector(`.game-card[data-app-id="${data.app_id}"]`);
      if (card) {
        card.dataset.name = data.name;
        const el = card.querySelector('.card-name');
        if (el) { el.textContent = data.name; el.title = data.name; }
      }
      break;
    }

    // Fix events
    case 'fix_progress': {
      const bar   = document.getElementById('of-progress-bar');
      const label = document.getElementById('of-progress-label');
      const pct   = data.pct || 0;
      if (bar)   bar.style.width   = pct + '%';
      if (label) label.textContent = pct < 100 ? t('onlinefix.label_installing_pct', { pct }) : t('onlinefix.label_completing');
      break;
    }
    case 'fix_done': {
      const bar   = document.getElementById('of-progress-bar');
      const label = document.getElementById('of-progress-label');
      const btn   = document.getElementById('of-install-btn');
      if (bar)   { bar.style.width = '100%'; bar.style.background = 'var(--success)'; }
      if (label) label.textContent = t('onlinefix.label_done');
      if (btn)   { btn.textContent = t('onlinefix.btn_done'); btn.disabled = true; }
      toast('success', t('onlinefix.toast_done'), `${data.archive} → ${data.game_dir}`);
      document.getElementById('of-num1')?.classList.add('done');
      document.getElementById('of-num2')?.classList.add('done');
      break;
    }
    case 'fix_error': {
      const label = document.getElementById('of-progress-label');
      const btn   = document.getElementById('of-install-btn');
      if (label) { label.textContent = `${t('toast.error')}: ${data.error}`; label.style.color = 'var(--danger)'; }
      if (btn)   { btn.textContent = t('onlinefix.btn_install'); btn.disabled = false; }
      toast('error', t('onlinefix.toast_err'), data.error);
      break;
    }

    // SAM events
    case 'sam_loading': {
      _samShowLoading();
      break;
    }
    case 'sam_loaded': {
      _samRender(data);
      break;
    }
    case 'sam_error': {
      _samShowError(data.error);
      toast('error', t('sam.toast_err'), data.error);
      break;
    }
    case 'sam_unlock_done': {
      (data.names || []).forEach(n => _samSetRowState(n, 'lua'));
      if (data.warning) {
        toast('warn', t('sam.toast_unlocked_lua'), data.warning);
      } else {
        toast('success', t('sam.toast_unlocked'), '');
      }
      break;
    }
    case 'sam_lock_done': {
      (data.names || []).forEach(n => _samSetRowState(n, 'locked'));
      if (data.warning) {
        toast('warn', t('sam.toast_locked_lua'), data.warning);
      } else {
        toast('info', t('sam.toast_locked'), '');
      }
      break;
    }
    case 'sam_unlock_all_done': {
      if (data.ok) {
        document.querySelectorAll('.sam-ach-row').forEach(r => {
          if (!r.classList.contains('unlocked')) _samSetRowState(r.dataset.name, 'lua');
        });
        toast('success', t('sam.toast_all_unlocked'), t('sam.toast_all_unlocked_msg', { count: '' }));
      } else {
        toast('error', t('toast.error'), data.error);
      }
      break;
    }
    case 'sam_lock_all_done': {
      document.querySelectorAll('.sam-ach-row.lua-unlocked').forEach(r => _samSetRowState(r.dataset.name, 'locked'));
      toast('info', t('sam.toast_all_locked'), t('sam.toast_all_locked_msg', { count: '' }));
      break;
    }

    // Idle events
    case 'idle_started': {
      _idleMarkRunning(data.app_id, true);
      _idleUpdateRunningSection();
      toast('success', t('idle.toast_started'), data.name);
      break;
    }
    case 'idle_tick': {
      const timeEl = document.getElementById(`idle-time-${data.app_id}`);
      if (timeEl) timeEl.textContent = data.elapsed_str;
      const runEl = document.getElementById(`idle-run-time-${data.app_id}`);
      if (runEl) runEl.textContent = data.elapsed_str;
      break;
    }
    case 'idle_stopped': {
      _idleMarkRunning(data.app_id, false);
      _idleUpdateRunningSection();
      toast('info', t('idle.toast_stopped'), data.elapsed_str || '');
      break;
    }
    case 'idle_all_stopped': {
      (data.stopped || []).forEach(id => _idleMarkRunning(id, false));
      _idleUpdateRunningSection();
      const count = (data.stopped || []).length;
      toast('info', t('idle.toast_all_stopped'), t('idle.toast_all_stopped_msg', { count }));
      break;
    }
    case 'idle_card_info': {
      const el = document.getElementById(`idle-cards-${data.app_id}`);
      if (el) {
        el.textContent = data.has_cards
          ? (data.card_count > 0 ? t('idle.drops_remaining', { count: data.card_count }) : t('idle.has_cards'))
          : t('idle.no_cards');
        if (data.has_cards) el.classList.add('has');
      }
      break;
    }
    case 'idle_cards_batch': {
      Object.entries(data.results || {}).forEach(([aid, info]) => {
        const el = document.getElementById(`idle-cards-${aid}`);
        if (el) {
          el.textContent = info.has_cards
            ? (info.card_count > 0 ? t('idle.drops_remaining', { count: info.card_count }) : t('idle.has_cards'))
            : t('idle.no_cards');
          if (info.has_cards) el.classList.add('has');
        }
      });
      break;
    }

    // Account events
    case 'account_logged_in':
    case 'account_restored': {
      _accountSetLoggedIn(data.steam_id, data.name, data.avatar);
      break;
    }
    case 'account_logged_out': {
      _accountSetLoggedOut();
      break;
    }
    case 'owned_games_loaded': {
      _accountUpdateGameCount(data.total, data.games);
      _samFillGrid(data.games);
      _idleLoadGames(data.games);
      break;
    }
    case 'owned_games_error': {
      toast('error', t('toast.error'), data.error);
      break;
    }
    case 'idle_games_loaded': {
      document.getElementById('idle-loading')?.classList.add('hidden');
      _idleLoadGames(data.games);
      break;
    }
    case 'idle_games_error': {
      document.getElementById('idle-loading')?.classList.add('hidden');
      toast('error', t('toast.error'), data.error);
      break;
    }

    // DLC Unlocker events
    case 'dlc_loading': {
      _dlcOnLoading();
      break;
    }
    case 'dlc_loaded': {
      _dlcOnLoaded(data);
      break;
    }
    case 'dlc_error': {
      _dlcOnError(data.error);
      break;
    }
    case 'dlc_unlock_all_done': {
      _dlcOnUnlockAllDone(data);
      break;
    }
  }
};

// ── Toasts ─────────────────────────────────────────────────────────
function toast(type, title, msg) {
  const icons = { success:'✓', error:'✕', info:'·', warn:'!' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <div class="toast-icon">${icons[type]||'·'}</div>
    <div>
      <div class="toast-title">${esc(title)}</div>
      ${msg ? `<div class="toast-msg">${esc(msg)}</div>` : ''}
    </div>`;
  document.getElementById('toast-container')?.appendChild(el);
  setTimeout(() => { el.classList.add('removing'); setTimeout(() => el.remove(), 220); }, 3800);
}

// ── Context Menu ───────────────────────────────────────────────────
function showCtxMenu(e, appId, name) {
  ctxTarget = { appId, name };
  const m = document.getElementById('ctx-menu');
  if (!m) return;
  m.classList.remove('hidden');
  m.style.left = Math.min(e.clientX, window.innerWidth - 170) + 'px';
  m.style.top  = Math.min(e.clientY, window.innerHeight - 120) + 'px';
}
function hideCtxMenu() { document.getElementById('ctx-menu')?.classList.add('hidden'); }
document.addEventListener('click', hideCtxMenu);
document.addEventListener('keydown', e => { if (e.key === 'Escape') hideCtxMenu(); });

function ctxSteamDB() { if (ctxTarget) pywebview.api.open_in_browser(`https://steamdb.info/app/${ctxTarget.appId}/`); }
function ctxCopyId()  { if (ctxTarget) navigator.clipboard?.writeText(ctxTarget.appId).then(() => toast('info', t('ctx.toast_copied'), `App ID: ${ctxTarget.appId}`)); }
function ctxRemove()  { if (ctxTarget) confirmRemove(ctxTarget.appId); }

// ── Confirm Modal ──────────────────────────────────────────────────
function confirm2(title, msg) {
  return new Promise(resolve => {
    const modal = document.getElementById('confirm-modal');
    document.getElementById('confirm-title').textContent = title;
    document.getElementById('confirm-msg').textContent   = msg;
    modal.classList.remove('hidden');
    const yes = document.getElementById('confirm-yes');
    const no  = document.getElementById('confirm-no');
    function cleanup() { modal.classList.add('hidden'); yes.onclick = null; no.onclick = null; }
    yes.onclick = () => { cleanup(); resolve(true); };
    no.onclick  = () => { cleanup(); resolve(false); };
  });
}

function esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
