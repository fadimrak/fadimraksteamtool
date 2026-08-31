/**
 * Online-Fix Installer & In-App Search Engine Module
 */

let ofCurrentDetailUrl  = '';
let ofCurrentGameTitle  = '';
let ofCurrentGameDir    = '';
let ofInstalledGamesList = [];
let ofSearchDebounceTimer = null;

// Manuel Sekme State'i
let ofArchivePath = '';
let ofGameDir     = '';

// ── 1. Başlangıç ve Sekmeler ──────────────────────────────────────

async function ofInit() {
  try {
    const info = await pywebview.api.check_extractor();
    const warn = document.getElementById('of-extractor-warn');
    if (warn) {
      if (!info.rar) warn.classList.remove('hidden');
      else           warn.classList.add('hidden');
    }
  } catch (e) {}

  // Yerel oyunları yükle
  ofLoadInstalledGames();
}

function ofSwitchTab(tabName, btn) {
  document.querySelectorAll('#page-onlinefix .tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('#page-onlinefix .tab-btn').forEach(b => b.classList.remove('active'));

  const targetPane = document.getElementById(`of-tab-${tabName}`);
  if (targetPane) targetPane.classList.add('active');
  if (btn) btn.classList.add('active');

  if (tabName === 'installed' && (!ofInstalledGamesList || !ofInstalledGamesList.length)) {
    ofLoadInstalledGames();
  }
}

// ── 2. Uygulama İçi Arama ────────────────────────────────────────

function ofOnSearchInput(val) {
  if (ofSearchDebounceTimer) clearTimeout(ofSearchDebounceTimer);
  const q = (val || '').trim();
  if (!q) return;

  ofSearchDebounceTimer = setTimeout(() => {
    ofSearch(q);
  }, 400);
}

function ofQuickSearch(term) {
  const input = document.getElementById('of-search-input');
  if (input) input.value = term;
  ofSwitchTab('search', document.querySelector('#page-onlinefix .tab-btn[data-i18n="onlinefix.tab_search"]'));
  ofSearch(term);
}

async function ofSearch(query) {
  const q = (query || '').trim();
  if (!q) return;

  const loader = document.getElementById('of-search-loader');
  const empty  = document.getElementById('of-search-empty');
  const grid   = document.getElementById('of-search-results');

  if (loader) loader.classList.remove('hidden');
  if (empty)  empty.classList.add('hidden');
  if (grid)   grid.innerHTML = '';

  await pywebview.api.of_search_games(q);
}

function ofRenderSearchResults(results, query) {
  const loader = document.getElementById('of-search-loader');
  const empty  = document.getElementById('of-search-empty');
  const grid   = document.getElementById('of-search-results');

  if (loader) loader.classList.add('hidden');
  if (!grid) return;

  if (!results || !results.length) {
    if (empty) empty.classList.remove('hidden');
    return;
  }
  if (empty) empty.classList.add('hidden');

  grid.innerHTML = '';

  results.forEach(item => {
    const card = document.createElement('div');
    card.className = 'game-card of-card';

    // Afiş
    const img = document.createElement('img');
    img.className = 'card-cover of-card-cover';
    img.src       = item.image || 'logo.png';
    img.alt       = esc(item.title);
    img.onerror   = function() { this.src = 'logo.png'; this.style.opacity = '.3'; };
    card.appendChild(img);

    // Rozetler (Co-op / Multiplayer)
    const badgeWrap = document.createElement('div');
    badgeWrap.className = 'of-card-badges';
    if (item.modes && item.modes.length) {
      item.modes.forEach(m => {
        const b = document.createElement('span');
        b.className = 'of-badge of-badge-mode';
        b.textContent = m;
        badgeWrap.appendChild(b);
      });
    } else {
      const b = document.createElement('span');
      b.className = 'of-badge of-badge-mode';
      b.textContent = item.category || 'Online';
      badgeWrap.appendChild(b);
    }
    card.appendChild(badgeWrap);

    // Kart Bilgisi
    const info = document.createElement('div');
    info.className = 'card-info';
    info.innerHTML = `
      <div class="card-name" title="${esc(item.title)}">${esc(item.title)}</div>
      <div class="card-sub" style="margin-top:4px;">
        <span style="font-size:10px;color:var(--muted);">${esc(item.date || item.category || '')}</span>
        <button class="btn btn-primary btn-sm" style="padding:2px 8px;font-size:11px;"
                onclick="event.stopPropagation();ofOpenDetail('${esc(item.url)}', '${esc(item.title)}', '${esc(item.image)}')">
          ${t('onlinefix.btn_inspect_install')}
        </button>
      </div>`;
    card.appendChild(info);

    card.addEventListener('click', () => {
      ofOpenDetail(item.url, item.title, item.image);
    });

    grid.appendChild(card);
  });
}

// ── 3. Detay ve Kurulum Modalı ───────────────────────────────────

async function ofOpenDetail(articleUrl, gameTitle, gameImage) {
  ofCurrentDetailUrl = articleUrl;
  ofCurrentGameTitle = gameTitle;

  const modal = document.getElementById('of-detail-modal');
  if (!modal) return;

  // Başlık, Afiş, Meta sıfırla
  document.getElementById('of-modal-title').textContent = gameTitle;
  document.getElementById('of-modal-img').src = gameImage || 'logo.png';
  document.getElementById('of-modal-cat').textContent = 'Online Fix';
  document.getElementById('of-modal-ver').textContent = 'Yükleniyor…';
  document.getElementById('of-modal-author').textContent = 'online-fix.me';
  document.getElementById('of-modal-desc').textContent = 'Oyun detayları ve indirme linkleri taranıyor…';
  
  // Klasör input ve otomatik tespit sıfırla
  document.getElementById('of-modal-folder-input').value = '';
  document.getElementById('of-modal-autofound').classList.add('hidden');

  // Fix dropdown sıfırla
  const fixSelect = document.getElementById('of-modal-fix-select');
  fixSelect.innerHTML = `<option value="">${t('onlinefix.loading_fixes')}</option>`;
  fixSelect.disabled = true;

  // İlerleme ve Başarı panellerini gizle
  document.getElementById('of-modal-progress-wrap').classList.add('hidden');
  document.getElementById('of-modal-success-box').classList.add('hidden');

  const installBtn = document.getElementById('of-modal-install-btn');
  installBtn.disabled = true;
  installBtn.textContent = t('onlinefix.btn_start_install');

  // Kurulu oyunlar dropdown'ını doldur
  _ofPopulateInstalledDropdown();

  // Modalı aç
  modal.classList.remove('hidden');

  // 1. Bilgisayarda bu oyun kurulu mu otomatik eşleştir
  try {
    const matchRes = await pywebview.api.of_auto_match_dir(gameTitle);
    if (matchRes && matchRes.ok && matchRes.path) {
      document.getElementById('of-modal-folder-input').value = matchRes.path;
      document.getElementById('of-modal-autofound').classList.remove('hidden');
      ofCurrentGameDir = matchRes.path;
    }
  } catch (e) {}

  // 2. Detayları ve İndirme Linklerini resmi siteden çek
  await pywebview.api.of_get_details(articleUrl);
}

function ofCloseModal() {
  const modal = document.getElementById('of-detail-modal');
  if (modal) modal.classList.add('hidden');
}

function ofRenderDetailData(data) {
  document.getElementById('of-modal-title').textContent = data.title || ofCurrentGameTitle;
  if (data.image) document.getElementById('of-modal-img').src = data.image;
  if (data.version) document.getElementById('of-modal-ver').textContent = data.version;
  if (data.author) document.getElementById('of-modal-author').textContent = data.author;
  if (data.description) {
    document.getElementById('of-modal-desc').textContent = data.description;
  } else {
    document.getElementById('of-modal-desc').textContent = t('onlinefix.default_desc');
  }

  // İndirme seçeneklerini doldur
  const fixSelect = document.getElementById('of-modal-fix-select');
  fixSelect.innerHTML = '';

  const fixes = data.fix_downloads || [];
  const fulls = data.full_downloads || [];

  if (fixes.length > 0) {
    fixes.forEach((f, idx) => {
      const opt = document.createElement('option');
      opt.value = f.direct_url || f.url;
      const sizeStr = f.size_mb > 0 ? ` (${f.size_mb} MB)` : '';
      opt.textContent = `★ ${f.name}${sizeStr} — [${f.source}]`;
      if (idx === 0) opt.selected = true;
      fixSelect.appendChild(opt);
    });
  } else if (fulls.length > 0) {
    fulls.forEach((f, idx) => {
      const opt = document.createElement('option');
      opt.value = f.direct_url || f.url;
      const sizeStr = f.size_mb > 0 ? ` (${f.size_mb} MB)` : '';
      opt.textContent = `● ${f.name}${sizeStr} — [${f.source}]`;
      if (idx === 0) opt.selected = true;
      fixSelect.appendChild(opt);
    });
  } else {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = t('onlinefix.no_direct_fix');
    fixSelect.appendChild(opt);
  }

  fixSelect.disabled = !(fixes.length || fulls.length);
  _ofUpdateModalInstallBtn();
}

function _ofPopulateInstalledDropdown() {
  const sel = document.getElementById('of-modal-installed-select');
  if (!sel) return;
  sel.innerHTML = `<option value="">${t('onlinefix.select_installed_game')}</option>`;

  if (ofInstalledGamesList && ofInstalledGamesList.length) {
    ofInstalledGamesList.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.install_dir;
      opt.textContent = `${g.name} (${g.install_dir})`;
      sel.appendChild(opt);
    });
  }
}

function ofModalOnSelectInstalled(path) {
  if (!path) return;
  document.getElementById('of-modal-folder-input').value = path;
  ofCurrentGameDir = path;
  document.getElementById('of-modal-autofound').classList.add('hidden');
  _ofUpdateModalInstallBtn();
}

async function ofModalBrowseFolder() {
  const res = await pywebview.api.browse_game_folder();
  if (!res || !res.path) return;
  document.getElementById('of-modal-folder-input').value = res.path;
  ofCurrentGameDir = res.path;
  document.getElementById('of-modal-autofound').classList.add('hidden');
  _ofUpdateModalInstallBtn();
}

function _ofUpdateModalInstallBtn() {
  const folderVal = document.getElementById('of-modal-folder-input')?.value.trim();
  const fixVal    = document.getElementById('of-modal-fix-select')?.value.trim();
  const btn       = document.getElementById('of-modal-install-btn');

  if (btn) {
    btn.disabled = !(folderVal && fixVal);
  }
}

// ── 4. Tek Tıkla İndir & Kur Akışı ───────────────────────────────

async function ofModalStartDownloadAndInstall() {
  const folderVal = document.getElementById('of-modal-folder-input')?.value.trim();
  const fixUrl    = document.getElementById('of-modal-fix-select')?.value.trim();
  if (!folderVal || !fixUrl) {
    toast('warn', t('onlinefix.warn_missing_fields'), t('onlinefix.warn_missing_desc'));
    return;
  }

  ofCurrentGameDir = folderVal;

  const btn          = document.getElementById('of-modal-install-btn');
  const progressWrap = document.getElementById('of-modal-progress-wrap');
  const statusText   = document.getElementById('of-modal-status-text');
  const speedText    = document.getElementById('of-modal-speed');
  const pctText      = document.getElementById('of-modal-pct');
  const progressBar  = document.getElementById('of-modal-progress-bar');
  const successBox   = document.getElementById('of-modal-success-box');

  if (btn) {
    btn.disabled = true;
    btn.textContent = t('onlinefix.btn_installing');
  }
  if (successBox)   successBox.classList.add('hidden');
  if (progressWrap) progressWrap.classList.remove('hidden');

  if (progressBar) {
    progressBar.style.width = '0%';
    progressBar.style.background = 'var(--success)';
  }
  if (statusText) statusText.textContent = t('onlinefix.status_downloading');
  if (speedText)  speedText.textContent = '0 MB/s';
  if (pctText)    pctText.textContent = '0%';

  await pywebview.api.of_start_download_and_install(fixUrl, folderVal, true);
}

async function ofModalLaunchGame() {
  if (!ofCurrentGameDir) return;
  const res = await pywebview.api.of_launch_game(ofCurrentGameDir);
  if (res.ok) {
    toast('success', t('onlinefix.toast_game_launched'), res.exe);
  } else {
    toast('error', t('toast.error'), res.error);
  }
}

async function ofModalUninstall() {
  if (!ofCurrentGameDir) return;
  const ok = await confirm2(t('onlinefix.confirm_uninstall_title'), t('onlinefix.confirm_uninstall_msg'));
  if (!ok) return;

  const res = await pywebview.api.of_uninstall_fix(ofCurrentGameDir);
  if (res.ok) {
    toast('info', t('onlinefix.toast_uninstalled'), t('onlinefix.toast_uninstalled_desc', { count: res.restored_count }));
    document.getElementById('of-modal-success-box')?.classList.add('hidden');
  } else {
    toast('error', t('toast.error'), res.error);
  }
}

// ── 5. Yüklü Steam Oyunları Listesi ─────────────────────────────

async function ofLoadInstalledGames() {
  const countEl = document.getElementById('of-installed-count');
  const grid    = document.getElementById('of-installed-grid');
  if (countEl) countEl.textContent = t('onlinefix.scanning_installed');

  try {
    const res = await pywebview.api.of_get_installed_steam_games();
    if (res && res.ok) {
      ofInstalledGamesList = res.games || [];
      if (countEl) countEl.textContent = t('onlinefix.installed_count', { count: ofInstalledGamesList.length });
      _ofRenderInstalledGrid(ofInstalledGamesList);
      _ofPopulateInstalledDropdown();
    }
  } catch (e) {
    if (countEl) countEl.textContent = t('onlinefix.scan_error');
  }
}

function _ofRenderInstalledGrid(games) {
  const grid = document.getElementById('of-installed-grid');
  if (!grid) return;
  grid.innerHTML = '';

  if (!games || !games.length) {
    grid.innerHTML = `<div class="empty-state" style="grid-column:1/-1;">
      <div class="empty-icon"></div>
      <div style="font-size:13px;color:var(--muted);">${t('onlinefix.no_steam_games')}</div>
    </div>`;
    return;
  }

  games.forEach(g => {
    const card = document.createElement('div');
    card.className = 'game-card of-installed-card';

    const img = document.createElement('img');
    img.className = 'card-cover';
    img.src       = `https://cdn.akamai.steamstatic.com/steam/apps/${g.app_id}/header.jpg`;
    img.alt       = esc(g.name);
    attachImg(img, g.app_id);
    card.appendChild(img);

    const info = document.createElement('div');
    info.className = 'card-info';
    info.innerHTML = `
      <div class="card-name" title="${esc(g.name)}">${esc(g.name)}</div>
      <div class="card-sub" style="margin-top:4px;">
        <span style="font-size:10px;color:var(--muted);">${esc(g.install_dir.split('\\').pop())}</span>
        <button class="btn btn-primary btn-sm" style="padding:2px 8px;font-size:10px;"
                onclick="event.stopPropagation();ofQuickSearch('${esc(g.name)}')">
          ${t('onlinefix.btn_search_fix')} ↗
        </button>
      </div>`;
    card.appendChild(info);

    card.addEventListener('click', () => {
      ofQuickSearch(g.name);
    });

    grid.appendChild(card);
  });
}

// ── 6. Manuel Arşiv Seçimi (Geriye Dönük Uyumluluk) ──────────────

async function ofSelectArchive() {
  const res = await pywebview.api.browse_fix_archive();
  if (!res || !res.path) return;
  ofArchivePath = res.path;

  const info = document.getElementById('of-archive-info');
  document.getElementById('of-archive-name').textContent = res.name;
  document.getElementById('of-archive-ext').textContent  = res.ext.toUpperCase();
  if (info) info.classList.remove('hidden');
  document.getElementById('of-num1')?.classList.add('done');

  _ofUpdateManualInstallBtn();
}

async function ofSelectGameDir() {
  const res = await pywebview.api.browse_game_folder();
  if (!res || !res.path) return;
  ofGameDir = res.path;

  const info = document.getElementById('of-gamedir-info');
  document.getElementById('of-gamedir-path').textContent = res.path;
  if (info) info.classList.remove('hidden');
  document.getElementById('of-num2')?.classList.add('done');

  _ofUpdateManualInstallBtn();
}

function _ofUpdateManualInstallBtn() {
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

  await pywebview.api.install_online_fix(ofArchivePath, ofGameDir);
}
