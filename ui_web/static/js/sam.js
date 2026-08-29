/**
 * SAM (Steam Achievement Manager) Module
 * Visual Game Grid Selector & Achievement Editor
 */

let _samAppId      = '';
let _samGameName   = '';
let _samFilter     = 'all';
let _samSearchQ    = '';
let _samAchs       = [];
let _samAllGames   = [];
let _samInited     = false;

async function samInit() {
  if (!_samInited) {
    _samInited = true;
  }

  // Hesap bağlı değilse login duvarı göster
  if (!_accountLoggedIn) {
    _samShowLoginWall();
    return;
  }

  _samShowContentWrap();
  await samRefreshGameList();
}

function _samShowLoginWall() {
  document.getElementById('sam-login-wall')?.classList.remove('hidden');
  document.getElementById('sam-content-wrap')?.classList.add('hidden');
  document.getElementById('sam-ach-view')?.classList.add('hidden');
  document.getElementById('sam-games-view')?.classList.remove('hidden');
}

function _samShowContentWrap() {
  document.getElementById('sam-login-wall')?.classList.add('hidden');
  document.getElementById('sam-content-wrap')?.classList.remove('hidden');
}

async function samRefreshGameList() {
  const res = await pywebview.api.sam_get_game_list();
  if (res && res.ok) {
    _samFillGrid(res.games || []);
  }
}

function _samFillGrid(games) {
  _samAllGames = games || [];
  _samRenderGameGrid();
}

function _samRenderGameGrid() {
  const grid  = document.getElementById('sam-game-grid');
  const count = document.getElementById('sam-game-count');
  const q     = (document.getElementById('sam-game-search')?.value || '').toLowerCase();
  if (!grid) return;

  grid.innerHTML = '';

  let list = _samAllGames;
  if (q) list = list.filter(g => (g.name || '').toLowerCase().includes(q) || String(g.appid).includes(q));

  if (count) count.textContent = `${list.length} oyun`;

  if (!list.length) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1;">
        <div class="empty-icon"></div>
        <div style="font-size:14px;font-weight:700;margin-bottom:4px;">Başarımı olan oyun bulunamadı</div>
        <div style="font-size:11px;color:var(--muted);">Sadece başarımı olan oyunlar bu listede listelenir.</div>
      </div>`;
    return;
  }

  list.forEach(g => {
    const aid = String(g.appid);
    const card = document.createElement('div');
    card.className = 'game-card';
    card.dataset.appId = aid;
    card.dataset.name  = g.name;

    const img = document.createElement('img');
    img.className = 'card-cover';
    img.src = g.cover || `https://cdn.akamai.steamstatic.com/steam/apps/${aid}/header.jpg`;
    img.alt = esc(g.name);
    attachImg(img, aid);
    card.appendChild(img);

    const info = document.createElement('div');
    info.className = 'card-info';
    info.innerHTML = `
      <div class="card-name" title="${esc(g.name)}">${esc(g.name)}</div>
      <div class="card-sub">
        <span>App ID: ${esc(aid)}</span>
        <button class="btn btn-primary btn-sm" style="padding:2px 8px;font-size:10px;"
                onclick="event.stopPropagation();samSelectGame('${esc(aid)}','${esc(g.name)}')">Başarımlar →</button>
      </div>`;
    card.appendChild(info);

    card.addEventListener('click', () => {
      samSelectGame(aid, g.name);
    });

    grid.appendChild(card);
  });
}

function samFilterGames(val) {
  _samRenderGameGrid();
}

async function samSelectGame(appId, gameName) {
  _samAppId    = String(appId);
  _samGameName = gameName || `App ${appId}`;

  document.getElementById('sam-games-view')?.classList.add('hidden');
  const achView = document.getElementById('sam-ach-view');
  if (achView) achView.classList.remove('hidden');

  const titleEl = document.getElementById('sam-selected-game-title');
  if (titleEl) titleEl.textContent = _samGameName;

  _samShowLoading();
  await pywebview.api.sam_get_achievements(_samAppId, _accountLoggedIn);
}

function samBackToGames() {
  _samAppId = '';
  document.getElementById('sam-ach-view')?.classList.add('hidden');
  document.getElementById('sam-games-view')?.classList.remove('hidden');
}

function _samShowLoading() {
  document.getElementById('sam-stats')?.classList.add('hidden');
  document.getElementById('sam-filter-bar')?.classList.add('hidden');
  const btnUnlock = document.getElementById('sam-unlock-all-btn');
  const btnLock   = document.getElementById('sam-lock-all-btn');
  if (btnUnlock) btnUnlock.disabled = true;
  if (btnLock)   btnLock.disabled   = true;

  const content = document.getElementById('sam-content');
  if (content) {
    content.innerHTML = `
      <div class="empty-state">
        <div class="spin" style="width:32px;height:32px;margin-bottom:14px;"></div>
        <div>Başarımlar yükleniyor…</div>
      </div>`;
  }
}

function _samShowError(msg) {
  const content = document.getElementById('sam-content');
  if (content) {
    content.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon" style="color:var(--danger)">X</div>
        <div style="color:var(--danger);font-size:13px;font-weight:700;">${esc(msg)}</div>
        <div style="margin-top:8px;font-size:11px;color:var(--muted);">Bu oyunun başarımı olmayabilir veya Steam API yanıt vermedi.</div>
      </div>`;
  }
}

function _samRender(data) {
  _samAchs = data.achievements || [];
  _samUpdateStats();

  document.getElementById('sam-stats')?.classList.remove('hidden');
  document.getElementById('sam-filter-bar')?.classList.remove('hidden');
  const btnUnlock = document.getElementById('sam-unlock-all-btn');
  const btnLock   = document.getElementById('sam-lock-all-btn');
  if (btnUnlock) btnUnlock.disabled = false;
  if (btnLock)   btnLock.disabled   = false;

  _samRenderList();
}

function _samUpdateStats() {
  const total    = _samAchs.length;
  const unlocked = _samAchs.filter(a => a.achieved || a.lua_unlocked).length;
  const luaCount = _samAchs.filter(a => a.lua_unlocked).length;
  const pct      = total > 0 ? Math.round((unlocked / total) * 100) : 0;
  const circum   = 2 * Math.PI * 21;

  const totalEl  = document.getElementById('sam-stat-total');
  const unlEl    = document.getElementById('sam-stat-unlocked');
  const luaEl    = document.getElementById('sam-stat-lua');
  const pctEl    = document.getElementById('sam-ring-pct');
  const fill     = document.getElementById('sam-ring-fill');

  if (totalEl) totalEl.textContent = total;
  if (unlEl)   unlEl.textContent   = unlocked;
  if (luaEl)   luaEl.textContent   = luaCount;
  if (pctEl)   pctEl.textContent   = pct + '%';
  if (fill) {
    fill.setAttribute('stroke-dasharray', circum.toFixed(1));
    fill.setAttribute('stroke-dashoffset', (circum - circum * pct / 100).toFixed(1));
  }
}

function _samRenderList() {
  const container = document.getElementById('sam-content');
  if (!container) return;

  const q = _samSearchQ.toLowerCase();
  let list = _samAchs;

  if (_samFilter === 'unlocked') list = list.filter(a => a.achieved || a.lua_unlocked);
  if (_samFilter === 'locked')   list = list.filter(a => !a.achieved && !a.lua_unlocked);
  if (q) {
    list = list.filter(a =>
      (a.display_name || '').toLowerCase().includes(q) || (a.description || '').toLowerCase().includes(q)
    );
  }

  if (!list.length) {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon"></div><div>Sonuç bulunamadı.</div></div>`;
    return;
  }

  container.innerHTML = `<div class="sam-ach-list" id="sam-ach-list"></div>`;
  const ul = document.getElementById('sam-ach-list');
  list.forEach(a => ul.appendChild(_samMakeRow(a)));
}

function _samMakeRow(a) {
  const isUnl = a.achieved || a.lua_unlocked;
  const div   = document.createElement('div');
  div.className = 'sam-ach-row'
    + (a.achieved     ? ' unlocked'     : '')
    + (a.lua_unlocked ? ' lua-unlocked' : '');
  div.dataset.name = a.name;

  const iconSrc  = isUnl ? (a.icon || a.icon_gray || '') : (a.icon_gray || a.icon || '');
  const iconCls  = !isUnl ? 'sam-ach-icon gray' : 'sam-ach-icon';
  const badgeCls = a.achieved ? 'sam-badge-unlocked' : (a.lua_unlocked ? 'sam-badge-lua' : 'sam-badge-locked');
  const badgeTxt = a.achieved ? 'Açık' : (a.lua_unlocked ? 'Açık (Lua)' : 'Kilitli');
  const pct      = a.global_percent > 0 ? `%${a.global_percent.toFixed(1)} oyuncu` : '';

  div.innerHTML = `
    <img class="${iconCls}" src="${esc(iconSrc)}" alt="" onerror="this.style.opacity='.2'">
    <div class="sam-ach-info">
      <div class="sam-ach-name" title="${esc(a.display_name)}">${esc(a.display_name)}</div>
      <div class="sam-ach-desc">${esc(a.description || (a.hidden ? 'Gizli başarım' : ''))}</div>
    </div>
    <div class="sam-ach-pct">${esc(pct)}</div>
    <span class="sam-ach-badge ${badgeCls}">${badgeTxt}</span>
    <div class="sam-ach-actions">
      ${!isUnl ? `<button class="sam-ach-btn unlock" onclick="samUnlockOne('${esc(a.name)}',this)">Kilidi Kaldır</button>` : ''}
      ${isUnl  ? `<button class="sam-ach-btn lock-btn" onclick="samLockOne('${esc(a.name)}',this)">Kilitle</button>` : ''}
    </div>`;
  return div;
}

function _samSetRowState(name, state) {
  const ach = _samAchs.find(a => a.name === name);
  if (ach) {
    if (state === 'unlocked' || state === 'lua') {
      ach.achieved = true;
      ach.lua_unlocked = true;
    } else {
      ach.achieved = false;
      ach.lua_unlocked = false;
    }
  }

  const row = document.querySelector(`.sam-ach-row[data-name="${CSS.escape(name)}"]`);
  if (row) {
    row.classList.remove('unlocked', 'lua-unlocked');
    const badge = row.querySelector('.sam-ach-badge');
    const acts  = row.querySelector('.sam-ach-actions');
    const icon  = row.querySelector('.sam-ach-icon');

    if (state === 'unlocked' || state === 'lua') {
      row.classList.add('unlocked');
      if (badge) { badge.className = 'sam-ach-badge sam-badge-unlocked'; badge.textContent = 'Açık'; }
      if (icon)  icon.classList.remove('gray');
      if (acts)  acts.innerHTML = `<button class="sam-ach-btn lock-btn" onclick="samLockOne('${esc(name)}',this)">Kilitle</button>`;
    } else {
      if (badge) { badge.className = 'sam-ach-badge sam-badge-locked'; badge.textContent = 'Kilitli'; }
      if (icon)  icon.classList.add('gray');
      if (acts)  acts.innerHTML = `<button class="sam-ach-btn unlock" onclick="samUnlockOne('${esc(name)}',this)">Kilidi Kaldır</button>`;
    }
  }

  _samUpdateStats();
}

async function samUnlockOne(name, btn) {
  if (!_samAppId) return;
  if (btn) { btn.disabled = true; btn.textContent = '…'; }
  const res = await pywebview.api.sam_unlock(_samAppId, [name]);
  if (res && res.ok) {
    _samSetRowState(name, 'unlocked');
    toast('success', 'Başarım Açıldı', name);
  } else {
    toast('error', 'Hata', res ? res.error : 'Açılamadı.');
    if (btn) { btn.disabled = false; btn.textContent = 'Kilidi Kaldır'; }
  }
}

async function samLockOne(name, btn) {
  if (!_samAppId) return;
  if (btn) { btn.disabled = true; btn.textContent = '…'; }
  const res = await pywebview.api.sam_lock(_samAppId, [name]);
  if (res && res.ok) {
    _samSetRowState(name, 'locked');
    toast('info', 'Başarım Kilitlendi', name);
  } else {
    toast('error', 'Hata', res ? res.error : 'Kilitlenemedi.');
    if (btn) { btn.disabled = false; btn.textContent = 'Kilitle'; }
  }
}

async function samUnlockAll() {
  if (!_samAppId) return;
  const names = _samAchs.map(a => a.name).filter(Boolean);
  if (!names.length) {
    toast('warn', 'Uyarı', 'Açılacak başarım bulunamadı.');
    return;
  }

  const ok = await confirm2('Tüm Başarımları Aç', `Bu oyuna ait ${names.length} başarımın tümü açılacak. Onaylıyor musunuz?`);
  if (!ok) return;

  const btn = document.getElementById('sam-unlock-all-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'Açılıyor…'; }

  const res = await pywebview.api.sam_unlock(_samAppId, names);
  if (btn) { btn.disabled = false; btn.textContent = 'Tümünü Aç'; }

  if (res && res.ok) {
    names.forEach(n => _samSetRowState(n, 'unlocked'));
    _samRenderList();
    toast('success', 'Tümü Açıldı', `${names.length} başarım başarıyla açıldı.`);
  } else {
    toast('error', 'Hata', res ? res.error : 'Açılamadı.');
  }
}

async function samLockAll() {
  if (!_samAppId) return;
  const names = _samAchs.map(a => a.name).filter(Boolean);
  if (!names.length) return;

  const ok = await confirm2('Tüm Başarımları Kilitle', `Bu oyuna ait tüm başarımlar kilitlenecek. Onaylıyor musunuz?`);
  if (!ok) return;

  const btn = document.getElementById('sam-lock-all-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'Kilitleniyor…'; }

  const res = await pywebview.api.sam_lock(_samAppId, names);
  if (btn) { btn.disabled = false; btn.textContent = 'Tümünü Kilitle'; }

  if (res && res.ok) {
    names.forEach(n => _samSetRowState(n, 'locked'));
    _samRenderList();
    toast('info', 'Tümü Kilitlendi', `${names.length} başarım kilitlendi.`);
  } else {
    toast('error', 'Hata', res ? res.error : 'Kilitlenemedi.');
  }
}

function samFilter(q) {
  _samSearchQ = q;
  _samRenderList();
}

function samSetFilter(f, btn) {
  _samFilter = f;
  document.querySelectorAll('.sam-filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  _samRenderList();
}
