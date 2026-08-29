/**
 * DLC Unlocker Module
 */

let _dlcAppId    = '';
let _dlcGameName = '';
let _dlcList     = [];   // { dlc_id, name, unlocked }
let _dlcFilter   = 'all'; // 'all' | 'unlocked' | 'locked'
let _dlcSearchQ  = '';

// ── Init ──────────────────────────────────────────────────────────

function dlcInit() {
  _dlcReset();
  dlcShowSearch();
}

function _dlcReset() {
  _dlcAppId    = '';
  _dlcGameName = '';
  _dlcList     = [];
  _dlcFilter   = 'all';
  _dlcSearchQ  = '';
}

// ── Search View ───────────────────────────────────────────────────

function dlcShowSearch() {
  document.getElementById('dlc-search-view')?.classList.remove('hidden');
  document.getElementById('dlc-detail-view')?.classList.add('hidden');
  document.getElementById('dlc-appid-input').value = _dlcAppId || '';
}

// ── Lookup trigger ────────────────────────────────────────────────

async function dlcLookup() {
  const input  = document.getElementById('dlc-appid-input');
  const appId  = (input?.value || '').trim();
  if (!appId || !/^\d+$/.test(appId)) {
    toast('warn', t('toast.warn'), t('add.warn_invalid_appid'));
    return;
  }
  _dlcAppId = appId;
  await pywebview.api.dlc_fetch(appId);
}

// ── Detail View ───────────────────────────────────────────────────

function _dlcShowDetail(gameName, dlcList) {
  _dlcGameName = gameName;
  _dlcList     = dlcList;

  document.getElementById('dlc-search-view')?.classList.add('hidden');
  const detail = document.getElementById('dlc-detail-view');
  if (detail) detail.classList.remove('hidden');

  const titleEl = document.getElementById('dlc-game-title');
  if (titleEl) titleEl.textContent = gameName;

  _dlcUpdateStats();
  _dlcRenderList();
}

function dlcBackToSearch() {
  dlcShowSearch();
}

// ── Stats bar ────────────────────────────────────────────────────

function _dlcUpdateStats() {
  const total    = _dlcList.length;
  const unlocked = _dlcList.filter(d => d.unlocked).length;

  const totalEl    = document.getElementById('dlc-stat-total');
  const unlockedEl = document.getElementById('dlc-stat-unlocked');
  const lockedEl   = document.getElementById('dlc-stat-locked');

  if (totalEl)    totalEl.textContent    = total;
  if (unlockedEl) unlockedEl.textContent = unlocked;
  if (lockedEl)   lockedEl.textContent   = total - unlocked;
}

// ── List render ─────────────────────────────────────────────────

function _dlcRenderList() {
  const container = document.getElementById('dlc-list-container');
  if (!container) return;

  const q = _dlcSearchQ.toLowerCase();
  let list = _dlcList;

  if (_dlcFilter === 'unlocked') list = list.filter(d => d.unlocked);
  if (_dlcFilter === 'locked')   list = list.filter(d => !d.unlocked);
  if (q) list = list.filter(d => d.name.toLowerCase().includes(q) || d.dlc_id.includes(q));

  if (!list.length) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon"></div>
        <div>${q ? t('dlc.no_results') : t('dlc.no_results')}</div>
      </div>`;
    return;
  }

  container.innerHTML = `<div class="dlc-list" id="dlc-list-inner"></div>`;
  const ul = document.getElementById('dlc-list-inner');
  list.forEach(d => ul.appendChild(_dlcMakeRow(d)));
}

function _dlcMakeRow(d) {
  const row = document.createElement('div');
  row.className   = 'dlc-row' + (d.unlocked ? ' unlocked' : '');
  row.dataset.id  = d.dlc_id;

  const badgeCls = d.unlocked ? 'dlc-badge active' : 'dlc-badge locked';
  const badgeTxt = d.unlocked ? t('dlc.badge_unlocked') : t('dlc.badge_locked');
  const btnCls   = d.unlocked ? 'btn btn-danger btn-sm' : 'btn btn-primary btn-sm';
  const btnTxt   = d.unlocked ? t('dlc.btn_lock') : t('dlc.btn_unlock');

  row.innerHTML = `
    <div class="dlc-row-info">
      <div class="dlc-row-name" title="${esc(d.name)}">${esc(d.name)}</div>
      <div class="dlc-row-id">App ID: ${esc(d.dlc_id)}</div>
    </div>
    <span class="${badgeCls}">${badgeTxt}</span>
    <button class="${btnCls}" onclick="dlcToggleOne('${esc(d.dlc_id)}', this)">${btnTxt}</button>`;

  return row;
}

// ── Single toggle ─────────────────────────────────────────────────

async function dlcToggleOne(dlcId, btn) {
  const entry = _dlcList.find(d => d.dlc_id === dlcId);
  if (!entry) return;

  if (btn) { btn.disabled = true; btn.textContent = '...'; }

  if (entry.unlocked) {
    const res = await pywebview.api.dlc_lock(_dlcAppId, [dlcId]);
    if (res.ok) {
      entry.unlocked = false;
      toast('info', t('dlc.toast_locked'), entry.name);
    } else {
      toast('error', t('toast.error'), res.error || t('settings.toast_save_err'));
    }
  } else {
    const res = await pywebview.api.dlc_unlock(_dlcAppId, [dlcId]);
    if (res.ok) {
      entry.unlocked = true;
      toast('success', t('dlc.toast_unlocked'), entry.name);
    } else {
      toast('error', t('toast.error'), res.error || t('settings.toast_save_err'));
    }
  }

  if (btn) btn.disabled = false;
  _dlcUpdateStats();
  _dlcRenderList();
}

// ── Unlock All ────────────────────────────────────────────────────

async function dlcUnlockAll() {
  if (!_dlcAppId) return;
  const locked = _dlcList.filter(d => !d.unlocked);
  if (!locked.length) {
    toast('info', t('toast.info'), t('dlc.toast_already_unlocked'));
    return;
  }

  const ok = await confirm2(
    t('dlc.confirm_unlock_all_title'),
    t('dlc.confirm_unlock_all_msg', { game: _dlcGameName, count: locked.length })
  );
  if (!ok) return;

  const btn = document.getElementById('dlc-unlock-all-btn');
  if (btn) { btn.disabled = true; btn.textContent = t('dlc.unlocking_btn'); }

  const ids = locked.map(d => d.dlc_id);
  const res = await pywebview.api.dlc_unlock(_dlcAppId, ids);

  if (btn) { btn.disabled = false; btn.textContent = t('dlc.btn_unlock_all'); }

  if (res.ok) {
    ids.forEach(id => {
      const d = _dlcList.find(d => d.dlc_id === id);
      if (d) d.unlocked = true;
    });
    toast('success', t('dlc.toast_all_unlocked'), t('dlc.toast_all_unlocked_msg', { count: res.added }));
    _dlcUpdateStats();
    _dlcRenderList();
  } else {
    toast('error', t('toast.error'), res.error || t('settings.toast_save_err'));
  }
}

// ── Lock All ──────────────────────────────────────────────────────

async function dlcLockAll() {
  if (!_dlcAppId) return;
  const opened = _dlcList.filter(d => d.unlocked);
  if (!opened.length) {
    toast('info', t('toast.info'), t('dlc.toast_none_unlocked'));
    return;
  }

  const ok = await confirm2(
    t('dlc.confirm_lock_all_title'),
    t('dlc.confirm_lock_all_msg', { count: opened.length })
  );
  if (!ok) return;

  const btn = document.getElementById('dlc-lock-all-btn');
  if (btn) { btn.disabled = true; btn.textContent = t('dlc.locking_btn'); }

  const ids = opened.map(d => d.dlc_id);
  const res = await pywebview.api.dlc_lock(_dlcAppId, ids);

  if (btn) { btn.disabled = false; btn.textContent = t('dlc.btn_lock_all'); }

  if (res.ok) {
    ids.forEach(id => {
      const d = _dlcList.find(d => d.dlc_id === id);
      if (d) d.unlocked = false;
    });
    toast('info', t('dlc.toast_all_locked'), t('dlc.toast_all_locked_msg', { count: res.removed }));
    _dlcUpdateStats();
    _dlcRenderList();
  } else {
    toast('error', t('toast.error'), res.error || t('settings.toast_save_err'));
  }
}

// ── Filter & Search ───────────────────────────────────────────────

function dlcSetFilter(f, btn) {
  _dlcFilter = f;
  document.querySelectorAll('.dlc-filter-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  _dlcRenderList();
}

function dlcSearch(q) {
  _dlcSearchQ = q || '';
  _dlcRenderList();
}

// ── Push Event Handlers ───────────────────────────────────────────

function _dlcOnLoading() {
  const detail = document.getElementById('dlc-detail-view');
  const search = document.getElementById('dlc-search-view');
  if (search) search.classList.add('hidden');
  if (detail) {
    detail.classList.remove('hidden');
    const container = document.getElementById('dlc-list-container');
    if (container) container.innerHTML = `
      <div class="empty-state">
        <div class="spin" style="width:28px;height:28px;margin-bottom:12px;"></div>
        <div>${t('dlc.loading_text')}</div>
      </div>`;
  }
}

function _dlcOnLoaded(data) {
  if (!data.dlc_list || data.dlc_list.length === 0) {
    document.getElementById('dlc-search-view')?.classList.remove('hidden');
    document.getElementById('dlc-detail-view')?.classList.add('hidden');
    toast('info', t('toast.info'), t('dlc.toast_none_found', { game: data.game_name }));
    return;
  }
  _dlcShowDetail(data.game_name, data.dlc_list);
}

function _dlcOnError(msg) {
  document.getElementById('dlc-search-view')?.classList.remove('hidden');
  document.getElementById('dlc-detail-view')?.classList.add('hidden');
  toast('error', t('dlc.toast_err'), msg);
}

function _dlcOnUnlockAllDone(data) {
  if (data.unlocked) {
    const unlSet = new Set(data.unlocked);
    _dlcList.forEach(d => { d.unlocked = unlSet.has(d.dlc_id); });
    _dlcUpdateStats();
    _dlcRenderList();
  }
  toast('success', t('dlc.toast_all_unlocked'), t('dlc.toast_all_unlocked_msg', { count: data.added || 0 }));
}
