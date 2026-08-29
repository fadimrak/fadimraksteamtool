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

// ── Arama Görünümü ───────────────────────────────────────────────

function dlcShowSearch() {
  document.getElementById('dlc-search-view')?.classList.remove('hidden');
  document.getElementById('dlc-detail-view')?.classList.add('hidden');
  document.getElementById('dlc-appid-input').value = _dlcAppId || '';
}

// ── Yükleme tetikleyici ───────────────────────────────────────────

async function dlcLookup() {
  const input  = document.getElementById('dlc-appid-input');
  const appId  = (input?.value || '').trim();
  if (!appId || !/^\d+$/.test(appId)) {
    toast('warn', 'Uyarı', 'Geçerli bir App ID girin.');
    return;
  }
  _dlcAppId = appId;
  await pywebview.api.dlc_fetch(appId);
}

// ── Detay Görünümü ───────────────────────────────────────────────

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

// ── İstatistik çubuğu ────────────────────────────────────────────

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

// ── Liste render ─────────────────────────────────────────────────

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
        <div>${q ? 'Sonuç bulunamadı.' : 'DLC bulunamadı.'}</div>
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
  const badgeTxt = d.unlocked ? 'Açık' : 'Kilitli';
  const btnCls   = d.unlocked ? 'btn btn-danger btn-sm' : 'btn btn-primary btn-sm';
  const btnTxt   = d.unlocked ? 'Kilitle' : 'Aç';

  row.innerHTML = `
    <div class="dlc-row-info">
      <div class="dlc-row-name" title="${esc(d.name)}">${esc(d.name)}</div>
      <div class="dlc-row-id">App ID: ${esc(d.dlc_id)}</div>
    </div>
    <span class="${badgeCls}">${badgeTxt}</span>
    <button class="${btnCls}" onclick="dlcToggleOne('${esc(d.dlc_id)}', this)">${btnTxt}</button>`;

  return row;
}

// ── Tekil toggle ─────────────────────────────────────────────────

async function dlcToggleOne(dlcId, btn) {
  const entry = _dlcList.find(d => d.dlc_id === dlcId);
  if (!entry) return;

  if (btn) { btn.disabled = true; btn.textContent = '...'; }

  if (entry.unlocked) {
    const res = await pywebview.api.dlc_lock(_dlcAppId, [dlcId]);
    if (res.ok) {
      entry.unlocked = false;
      toast('info', 'Kilitledi', entry.name);
    } else {
      toast('error', 'Hata', res.error || 'Kilitlenemedi.');
    }
  } else {
    const res = await pywebview.api.dlc_unlock(_dlcAppId, [dlcId]);
    if (res.ok) {
      entry.unlocked = true;
      toast('success', 'Açıldı', entry.name);
    } else {
      toast('error', 'Hata', res.error || 'Açılamadı.');
    }
  }

  if (btn) btn.disabled = false;
  _dlcUpdateStats();
  _dlcRenderList();
}

// ── Tümünü Aç ────────────────────────────────────────────────────

async function dlcUnlockAll() {
  if (!_dlcAppId) return;
  const locked = _dlcList.filter(d => !d.unlocked);
  if (!locked.length) {
    toast('info', 'Bilgi', 'Tüm DLC\'ler zaten açık.');
    return;
  }

  const ok = await confirm2(
    'Tüm DLC\'leri Aç',
    `${_dlcGameName} oyununa ait ${locked.length} DLC açılacak.`
  );
  if (!ok) return;

  const btn = document.getElementById('dlc-unlock-all-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'Açılıyor...'; }

  const ids = locked.map(d => d.dlc_id);
  const res = await pywebview.api.dlc_unlock(_dlcAppId, ids);

  if (btn) { btn.disabled = false; btn.textContent = 'Tümünü Aç'; }

  if (res.ok) {
    ids.forEach(id => {
      const d = _dlcList.find(d => d.dlc_id === id);
      if (d) d.unlocked = true;
    });
    toast('success', 'Tümü Açıldı', `${res.added} DLC açıldı.`);
    _dlcUpdateStats();
    _dlcRenderList();
  } else {
    toast('error', 'Hata', res.error || 'Açılamadı.');
  }
}

// ── Tümünü Kilitle ───────────────────────────────────────────────

async function dlcLockAll() {
  if (!_dlcAppId) return;
  const opened = _dlcList.filter(d => d.unlocked);
  if (!opened.length) {
    toast('info', 'Bilgi', 'Açık DLC yok.');
    return;
  }

  const ok = await confirm2(
    'Tüm DLC\'leri Kilitle',
    `${opened.length} açık DLC kilitlenecek.`
  );
  if (!ok) return;

  const btn = document.getElementById('dlc-lock-all-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'Kilitleniyor...'; }

  const ids = opened.map(d => d.dlc_id);
  const res = await pywebview.api.dlc_lock(_dlcAppId, ids);

  if (btn) { btn.disabled = false; btn.textContent = 'Tümünü Kilitle'; }

  if (res.ok) {
    ids.forEach(id => {
      const d = _dlcList.find(d => d.dlc_id === id);
      if (d) d.unlocked = false;
    });
    toast('info', 'Tümü Kilitlendi', `${res.removed} DLC kilitlendi.`);
    _dlcUpdateStats();
    _dlcRenderList();
  } else {
    toast('error', 'Hata', res.error || 'Kilitlenemedi.');
  }
}

// ── Filtre & Arama ───────────────────────────────────────────────

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

// ── Push event işleyiciler (core.js'den çağrılır) ────────────────

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
        <div>DLC listesi yükleniyor...</div>
      </div>`;
  }
}

function _dlcOnLoaded(data) {
  if (!data.dlc_list || data.dlc_list.length === 0) {
    document.getElementById('dlc-search-view')?.classList.remove('hidden');
    document.getElementById('dlc-detail-view')?.classList.add('hidden');
    toast('info', 'DLC Bulunamadı', `${data.game_name} için kayıtlı DLC yok.`);
    return;
  }
  _dlcShowDetail(data.game_name, data.dlc_list);
}

function _dlcOnError(msg) {
  document.getElementById('dlc-search-view')?.classList.remove('hidden');
  document.getElementById('dlc-detail-view')?.classList.add('hidden');
  toast('error', 'DLC Hatası', msg);
}

function _dlcOnUnlockAllDone(data) {
  // Tüm liste yeniden çekilmişse ID listesiyle güncelle
  if (data.unlocked) {
    const unlSet = new Set(data.unlocked);
    _dlcList.forEach(d => { d.unlocked = unlSet.has(d.dlc_id); });
    _dlcUpdateStats();
    _dlcRenderList();
  }
  toast('success', 'Tümü Açıldı', `${data.added || 0} DLC açıldı.`);
}
