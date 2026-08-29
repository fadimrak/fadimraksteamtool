/**
 * Library Module — Installed Games Management
 */

async function loadLibrary() {
  showSkeletons(8);
  installedGames = await pywebview.api.get_installed_games();
  renderLibrary(installedGames);
}

function showSkeletons(n) {
  const g = document.getElementById('lib-grid');
  if (!g) return;
  g.innerHTML = '';
  for (let i = 0; i < n; i++) {
    const d = document.createElement('div');
    d.className = 'skeleton-card';
    g.appendChild(d);
  }
}

function renderLibrary(games) {
  const grid  = document.getElementById('lib-grid');
  const empty = document.getElementById('lib-empty');
  const count = document.getElementById('lib-count');
  if (!grid) return;

  grid.innerHTML = '';
  if (count) count.textContent = t('library.count', { count: games ? games.length : 0 });

  if (!games || !games.length) {
    if (empty) empty.classList.remove('hidden');
    return;
  }
  if (empty) empty.classList.add('hidden');

  games.forEach(g => {
    const card = document.createElement('div');
    card.className      = 'game-card';
    card.dataset.appId  = g.app_id;
    card.dataset.name   = g.name;

    const img = document.createElement('img');
    img.className = 'card-cover';
    img.src       = g.cover || `https://cdn.akamai.steamstatic.com/steam/apps/${g.app_id}/header.jpg`;
    img.alt       = esc(g.name);
    attachImg(img, g.app_id);
    card.appendChild(img);

    const info = document.createElement('div');
    info.className = 'card-info';
    info.innerHTML = `
      <div class="card-name" title="${esc(g.name)}">${esc(g.name)}</div>
      <div class="card-sub">
        <span>App ID: ${esc(g.app_id)}</span>
        <button class="btn btn-ghost btn-sm" style="padding:2px 6px;font-size:10px;"
                onclick="event.stopPropagation();confirmRemove('${esc(g.app_id)}')">${t('library.remove_btn')}</button>
      </div>`;
    card.appendChild(info);

    card.addEventListener('contextmenu', e => {
      e.preventDefault();
      showCtxMenu(e, g.app_id, g.name);
    });

    card.addEventListener('click', () => {
      // Tıklandığında Başarım veya Idle'a geçiş kısayolu
      samSelectGame(g.app_id, g.name);
      navigateTo('sam');
    });

    grid.appendChild(card);
  });
}

function filterLibrary(query) {
  const q = (query || '').toLowerCase();
  document.querySelectorAll('#lib-grid .game-card').forEach(card => {
    const name = (card.dataset.name || '').toLowerCase();
    const id   = (card.dataset.appId || '').toLowerCase();
    card.style.display = (name.includes(q) || id.includes(q)) ? '' : 'none';
  });
}

async function confirmRemove(appId) {
  const game = installedGames.find(g => String(g.app_id) === String(appId));
  const name = game ? game.name : `App ${appId}`;
  const ok = await confirm2(t('library.confirm_remove_title'), t('library.confirm_remove_msg', { name }));
  if (!ok) return;

  const res = await pywebview.api.remove_game(appId);
  if (res.ok) {
    toast('info', t('library.toast_removed'), name);
    installedGames = installedGames.filter(g => String(g.app_id) !== String(appId));
    renderLibrary(installedGames);
  } else {
    toast('error', t('toast.error'), res.error || t('settings.toast_save_err'));
  }
}
