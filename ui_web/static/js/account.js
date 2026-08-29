/**
 * Steam Account Management Module
 */

let _accountLoggedIn = false;

async function accountInit() {
  const status = await pywebview.api.account_get_status();
  if (status && status.logged_in) {
    _accountSetLoggedIn(status.steam_id, status.name, status.avatar);
  } else {
    _accountSetLoggedOut();
  }
}

function _accountSetLoggedIn(steamId, name, avatar) {
  _accountLoggedIn = true;

  _samInited    = false;
  _idleInited   = false;

  const hero      = document.getElementById('account-hero');
  const form      = document.getElementById('account-login-form');
  const gamesInfo = document.getElementById('account-games-info');
  const logoutBtn = document.getElementById('account-logout-btn');

  if (hero)      hero.classList.remove('hidden');
  if (form)      form.classList.add('hidden');
  if (gamesInfo) gamesInfo.classList.remove('hidden');
  if (logoutBtn) logoutBtn.classList.remove('hidden');

  const img = document.getElementById('account-avatar');
  if (img && avatar) { img.src = avatar; img.style.opacity = '1'; }
  const nameEl = document.getElementById('account-name');
  if (nameEl) nameEl.textContent = name;
  const idEl = document.getElementById('account-id-label');
  if (idEl) idEl.textContent = `Steam ID: ${steamId}`;

  // Fetch owned games
  pywebview.api.account_get_owned_games(false);

  // If on SAM or Idle page, refresh immediately
  if (currentPage === 'sam')  samInit();
  if (currentPage === 'idle') idleInit();
}

function _accountSetLoggedOut() {
  _accountLoggedIn = false;

  _samInited  = false;
  _idleInited = false;

  const hero      = document.getElementById('account-hero');
  const form      = document.getElementById('account-login-form');
  const gamesInfo = document.getElementById('account-games-info');
  const logoutBtn = document.getElementById('account-logout-btn');

  if (hero)      hero.classList.add('hidden');
  if (form)      form.classList.remove('hidden');
  if (gamesInfo) gamesInfo.classList.add('hidden');
  if (logoutBtn) logoutBtn.classList.add('hidden');

  if (currentPage === 'sam')  _samShowLoginWall();
  if (currentPage === 'idle') _idleShowLoginWall();
}

function _accountUpdateGameCount(total, games) {
  const el = document.getElementById('account-games-count');
  if (el) el.textContent = total;
  const gamesInfo = document.getElementById('account-games-info');
  if (gamesInfo) gamesInfo.classList.remove('hidden');
}

async function accountLogin() {
  const key = document.getElementById('account-api-key')?.value.trim();
  const sid = document.getElementById('account-steam-id')?.value.trim();
  const btn = document.getElementById('account-login-btn');
  const sta = document.getElementById('account-login-status');

  if (!key || !sid) {
    if (sta) {
      sta.textContent = t('account.err_missing_fields');
      sta.style.color = 'var(--danger)';
    }
    return;
  }

  if (btn) { btn.disabled = true; btn.textContent = t('account.btn_connecting'); }
  if (sta) sta.textContent = '';

  const res = await pywebview.api.account_login(key, sid);
  if (btn) { btn.disabled = false; btn.textContent = t('account.btn_connect'); }

  if (res.ok) {
    if (sta) sta.textContent = '';
    toast('success', t('account.toast_connected'), res.name);
  } else {
    if (sta) {
      sta.textContent = res.error || t('settings.toast_save_err');
      sta.style.color = 'var(--danger)';
    }
  }
}

async function accountLogout() {
  const ok = await confirm2(t('account.confirm_logout_title'), t('account.confirm_logout_msg'));
  if (!ok) return;
  await pywebview.api.account_logout();
  toast('info', t('account.toast_logged_out'), '');
}

async function accountRefreshLibrary() {
  toast('info', t('toast.restarting'), t('account.toast_refreshing'));
  const res = await pywebview.api.account_get_owned_games(true);
  if (!res.ok) toast('error', t('toast.error'), res.error);
}
