/**
 * Add Game Module — Search, Popular Games & File Uploader
 */

let searchTimer = null;

function switchTab(id, btn) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('tab-' + id)?.classList.add('active');
}

function onSearchInput(val) {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => doSearch(val), 250);
}

async function doSearch(q) {
  const grid   = document.getElementById('search-results');
  const count  = document.getElementById('search-count');
  const loader = document.getElementById('search-loader');
  if (!grid) return;

  if (!q || q.length < 2) {
    if (loader) loader.classList.remove('hidden');
    const pop = await pywebview.api.get_popular_games();
    if (loader) loader.classList.add('hidden');
    if (count) count.textContent = 'Popüler Oyunlar';
    renderSearchResults(pop || []);
    return;
  }

  if (loader) loader.classList.remove('hidden');
  const results = await pywebview.api.search_games(q);
  if (loader) loader.classList.add('hidden');
  if (count) count.textContent = `${results.length} sonuç`;
  renderSearchResults(results || []);
}

function renderSearchResults(list) {
  const grid = document.getElementById('search-results');
  if (!grid) return;
  grid.innerHTML = '';

  if (!list.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><div class="empty-icon"></div><div>Sonuç bulunamadı.</div></div>`;
    return;
  }

  list.forEach(g => {
    const aid = String(g.appid || g.app_id);
    const card = document.createElement('div');
    card.className = 'game-card';
    card.id = `result-${aid}`;

    const isInstalled = installedGames.some(ig => String(ig.app_id) === aid);
    const btnCls = isInstalled ? 'btn btn-ghost btn-sm' : 'btn btn-primary btn-sm';
    const btnTxt = isInstalled ? 'Yüklendi' : 'İndir';

    const img = document.createElement('img');
    img.className = 'card-cover';
    img.src = `https://cdn.akamai.steamstatic.com/steam/apps/${aid}/header.jpg`;
    img.alt = esc(g.name);
    attachImg(img, aid);
    card.appendChild(img);

    const info = document.createElement('div');
    info.className = 'card-info';
    info.innerHTML = `
      <div class="card-name" title="${esc(g.name)}">${esc(g.name)}</div>
      <div class="card-sub">
        <span>App ID: ${esc(aid)}</span>
        <button class="${btnCls} install-btn" ${isInstalled ? 'disabled' : ''}
                onclick="addGameById('${aid}')">${btnTxt}</button>
      </div>`;
    card.appendChild(info);

    grid.appendChild(card);
  });
}

async function addGameById(appId) {
  const aid = String(appId).trim();
  if (!aid) { toast('warn', 'Uyarı', 'Lütfen geçerli bir App ID girin.'); return; }
  const btn = document.querySelector(`#result-${aid} .install-btn`);
  if (btn) {
    btn.disabled = true;
    btn.textContent = 'İndiriliyor…';
  }
  const res = await pywebview.api.add_game_by_id(aid);
  if (!res.ok) {
    toast('error', 'Hata', res.error || 'Oyun eklenemedi.');
    if (btn) { btn.disabled = false; btn.textContent = 'İndir'; }
  }
}

async function browseFiles() {
  const files = await pywebview.api.browse_game_files();
  if (files && files.length) {
    const res = await pywebview.api.add_game_files(files);
    if (res.ok) {
      toast('success', 'Dosyalar Yüklendi', `${res.lua} Lua, ${res.manifests} Manifest eklendi.`);
      loadLibrary();
    } else {
      toast('error', 'Hata', res.error || 'Dosyalar eklenemedi.');
    }
  }
}

// ── Drag & Drop ────────────────────────────────────────────────────
function setupDropZone() {
  const dz = document.getElementById('drop-zone');
  if (!dz) return;

  ['dragenter', 'dragover'].forEach(name => {
    dz.addEventListener(name, e => { e.preventDefault(); dz.classList.add('dragover'); });
  });
  ['dragleave', 'drop'].forEach(name => {
    dz.addEventListener(name, e => { e.preventDefault(); dz.classList.remove('dragover'); });
  });

  dz.addEventListener('drop', async e => {
    const files = e.dataTransfer.files;
    if (!files || !files.length) return;

    const fileList = [];
    for (const f of files) {
      const b64 = await readFileAsBase64(f);
      fileList.push({ name: f.name, data: b64 });
    }

    const res = await pywebview.api.add_dropped_files(fileList);
    if (res.ok) {
      toast('success', 'Yüklendi', `${res.lua} Lua, ${res.manifests} Manifest kuruldu.`);
      loadLibrary();
    } else {
      toast('error', 'Hata', res.error || 'Yüklenemedi.');
    }
  });
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const b64 = reader.result.split(',')[1];
      resolve(b64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

document.addEventListener('DOMContentLoaded', setupDropZone);
