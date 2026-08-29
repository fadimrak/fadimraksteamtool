/**
 * Idle Farmer Module — Kart ve Saat Kasma
 */

let _idleRunning    = new Set();
let _idleAllGames   = [];
let _idleInited     = false;
let _idleCardFilter = 'all';

async function idleInit() {
  if (!_idleInited) {
    _idleInited = true;
  }

  // Aktif kasılanları önce her durumda yükle
  try {
    const st = await pywebview.api.idle_get_status();
    if (st && st.running && st.running.length) {
      st.running.forEach(r => _idleRunning.add(String(r.app_id)));
      _idleUpdateRunningSection(st.running);
      _idleUpdateActiveCount();
      const stopAll = document.getElementById('idle-stop-all-btn');
      if (stopAll) stopAll.classList.remove('hidden');
    }
  } catch (e) {}

  _idleShowLoading();

  try {
    const res = await pywebview.api.idle_get_game_list();
    if (res && res.ok && res.games && res.games.length > 0) {
      _idleLoadGames(res.games || []);
    } else if (_accountLoggedIn) {
      _idleLoadGames([]);
    } else {
      // Hesap bağlı değil ve yerel oyun bulunamadıysa giriş duvarını göster ama sayfa kontrollerini erişilebilir tut
      _idleShowLoginWall();
    }
  } catch (e) {
    if (!_accountLoggedIn) {
      _idleShowLoginWall();
    } else {
      _idleLoadGames([]);
    }
  }
}

function _idleShowLoginWall() {
  document.getElementById('idle-login-wall')?.classList.remove('hidden');
  document.getElementById('idle-loading')?.classList.add('hidden');
  const main = document.getElementById('idle-main');
  if (main) main.classList.remove('hidden');
}

function _idleShowLoading() {
  document.getElementById('idle-login-wall')?.classList.add('hidden');
  document.getElementById('idle-loading')?.classList.remove('hidden');
  const main = document.getElementById('idle-main');
  if (main) main.classList.add('hidden');
}

function _idleLoadGames(games) {
  document.getElementById('idle-login-wall')?.classList.add('hidden');
  document.getElementById('idle-loading')?.classList.add('hidden');
  const main = document.getElementById('idle-main');
  if (main) main.classList.remove('hidden');

  _idleAllGames = games || [];

  const libCount = document.getElementById('idle-lib-count');
  if (libCount) libCount.textContent = _idleAllGames.length;

  _idleRenderGrid();

  // Toplu kart hakkı bilgisi çek (ilk 100 oyun)
  const ids = _idleAllGames.map(g => String(g.appid));
  if (ids.length > 0) {
    try {
      pywebview.api.idle_get_cards_batch(ids.slice(0, 100));
    } catch (e) {}
  }
}

function _idleRenderGrid() {
  const grid = document.getElementById('idle-game-grid');
  if (!grid) return;
  grid.innerHTML = '';

  const q = (document.getElementById('idle-search')?.value || '').toLowerCase();

  let list = _idleAllGames;
  if (q) list = list.filter(g => (g.name || '').toLowerCase().includes(q) || String(g.appid).includes(q));

  if (!list.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><div class="empty-icon"></div><div>Oyun bulunamadı.</div></div>`;
    return;
  }

  list.forEach(g => grid.appendChild(_idleMakeCard(g)));
  idleApplyFilter();
}

function _idleMakeCard(game) {
  const appId = String(game.appid);
  const div   = document.createElement('div');
  div.className     = 'idle-game-card' + (_idleRunning.has(appId) ? ' is-idling' : '');
  div.id            = `idle-card-${appId}`;
  div.dataset.name  = game.name;
  div.dataset.appid = appId;

  const img = document.createElement('img');
  img.className = 'card-cover';
  img.src = game.cover || `https://cdn.akamai.steamstatic.com/steam/apps/${appId}/header.jpg`;
  img.alt = esc(game.name);
  attachImg(img, appId);
  div.appendChild(img);

  const isRunning = _idleRunning.has(appId);
  const btnCls    = isRunning ? 'idle-btn running' : 'idle-btn';
  const btnTxt    = isRunning ? 'Durdur' : 'Kas';

  const remDrops  = parseInt(game.cards_remaining || '0', 10);
  const hasDrops  = Boolean(game.has_drops || remDrops > 0);

  let dropsHtml = '— Kart hakkı yok';
  let dropsClass = 'idle-card-cards';
  if (hasDrops && remDrops > 0) {
    dropsHtml  = `${remDrops} kart hakkı`;
    dropsClass = 'idle-card-cards has';
  } else if (game.has_cards) {
    dropsHtml  = 'Kart hakkı bitti';
  }

  const pt = game.playtime_forever || 0;
  const ptStr = pt > 0
    ? (pt >= 60 ? `${Math.floor(pt/60)}s ${pt%60}dk` : `${pt}dk`)
    : 'Oynanmadı';

  div.insertAdjacentHTML('beforeend', `
    <div class="idle-card-body">
      <div class="idle-card-name" title="${esc(game.name)}">${esc(game.name)}</div>
      <div class="idle-card-meta">
        <span class="${dropsClass}" id="idle-cards-${appId}">${dropsHtml}</span>
        <button class="${btnCls}" id="idle-btn-${appId}"
                onclick="idleToggle('${appId}','${esc(game.name)}',this)">${btnTxt}</button>
      </div>
      <div style="font-size:10px;color:var(--muted);margin-top:4px;">Toplam Süre: ${ptStr}</div>
      <div style="font-size:10px;color:var(--success);margin-top:2px;min-height:14px;"
           id="idle-time-${appId}">${isRunning ? 'Kasılıyor' : ''}</div>
    </div>`);

  return div;
}

async function idleToggle(appId, name, btn) {
  const aid = String(appId).trim();
  if (_idleRunning.has(aid)) {
    if (btn) { btn.disabled = true; btn.textContent = 'Durduruluyor…'; }
    await pywebview.api.idle_stop(aid);
  } else {
    if (btn) { btn.disabled = true; btn.textContent = 'Başlatılıyor…'; }
    const res = await pywebview.api.idle_start(aid, name);
    if (!res.ok) {
      toast('error', 'Hata', res.error || 'Kasma başlatılamadı.');
      if (btn) { btn.disabled = false; btn.textContent = 'Kas'; }
    }
  }
}


function _idleMarkRunning(appId, running) {
  const aid = String(appId);
  if (running) _idleRunning.add(aid);
  else         _idleRunning.delete(aid);
  _idleUpdateActiveCount();

  const card = document.getElementById(`idle-card-${aid}`);
  const btn  = document.getElementById(`idle-btn-${aid}`);
  const time = document.getElementById(`idle-time-${aid}`);

  if (card) card.classList.toggle('is-idling', running);
  if (btn)  {
    btn.disabled = false;
    btn.textContent = running ? 'Durdur' : 'Kas';
    btn.className   = running ? 'idle-btn running' : 'idle-btn';
  }
  if (time && !running) time.textContent = '';

  const stopAll = document.getElementById('idle-stop-all-btn');
  if (stopAll) {
    if (_idleRunning.size > 0) stopAll.classList.remove('hidden');
    else                       stopAll.classList.add('hidden');
  }
}

function _idleUpdateRunningSection(runningList) {
  const section = document.getElementById('idle-running-section');
  const list    = document.getElementById('idle-running-list');
  if (!section || !list) return;

  if (!_idleRunning.size) {
    section.classList.add('hidden');
    list.innerHTML = '';
    return;
  }
  section.classList.remove('hidden');

  list.querySelectorAll('[data-app-id]').forEach(el => {
    if (!_idleRunning.has(el.dataset.appId)) el.remove();
  });

  const games = runningList || [..._idleRunning].map(id => ({ app_id: id, name: `App ${id}`, elapsed_str: '' }));
  games.forEach(r => {
    const aid = String(r.app_id);
    if (document.getElementById(`idle-run-row-${aid}`)) return;
    const row = document.createElement('div');
    row.className     = 'idle-running-row';
    row.id            = `idle-run-row-${aid}`;
    row.dataset.appId = aid;
    row.innerHTML = `
      <div class="idle-pulse"></div>
      <img class="idle-running-cover"
           src="https://cdn.akamai.steamstatic.com/steam/apps/${aid}/header.jpg"
           onerror="this.style.opacity='.2'" alt="">
      <div class="idle-running-info">
        <div class="idle-running-name">${esc(r.name || `App ${aid}`)}</div>
        <div class="idle-running-time" id="idle-run-time-${aid}">${esc(r.elapsed_str || '0 sn')}</div>
      </div>
      <button class="btn btn-danger btn-sm"
              onclick="idleToggle('${aid}','',document.getElementById('idle-btn-${aid}'))">
        Durdur
      </button>`;
    list.appendChild(row);
  });
}

function _idleUpdateActiveCount() {
  const el = document.getElementById('idle-active-count');
  if (el) el.textContent = _idleRunning.size;
}

async function idleStopAll() {
  const ok = await confirm2('Tümünü Durdur', `${_idleRunning.size} oyunun kasması durdurulacak.`);
  if (!ok) return;
  await pywebview.api.idle_stop_all();
}

async function idleRefreshLibrary() {
  _idleShowLoading();
  await pywebview.api.idle_refresh_game_list();
}

function idleFilter(q) {
  const l = (q || '').toLowerCase();
  document.querySelectorAll('#idle-game-grid .idle-game-card').forEach(c => {
    const name  = (c.dataset.name || '').toLowerCase();
    const appid = (c.dataset.appid || '').toLowerCase();
    const matchSearch = name.includes(l) || appid.includes(l);
    if (!matchSearch) {
      c.style.display = 'none';
      return;
    }
    if (_idleCardFilter === 'cards') {
      const cardsEl = document.getElementById(`idle-cards-${c.dataset.appid}`);
      const hasCards = cardsEl?.classList.contains('has');
      c.style.display = hasCards ? '' : 'none';
    } else {
      c.style.display = '';
    }
  });
}

function idleApplyFilter() {
  _idleCardFilter = document.getElementById('idle-filter-cards')?.value || 'all';
  const q = (document.getElementById('idle-search')?.value || '').toLowerCase();
  idleFilter(q);
}

async function minimizeToTray() {
  const res = await pywebview.api.idle_minimize_to_tray();
  if (!res.ok) toast('warn', 'Tray Yok', 'pystray kurulu değil.');
}
