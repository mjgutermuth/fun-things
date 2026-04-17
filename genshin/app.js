const CACHE_TTL = 5 * 60 * 1000;
const ELEMENTS = ['Pyro','Hydro','Anemo','Electro','Dendro','Cryo','Geo'];
const ELEMENT_MAP = {
  Fire: 'Pyro', Water: 'Hydro', Wind: 'Anemo',
  Electric: 'Electro', Grass: 'Dendro', Ice: 'Cryo', Rock: 'Geo',
};

let allChars = [];
let activeElement = 'all';
let activeSort = 'default';
const expanded = new Set();

// ── CONFIG ──

function loadConfig() {
  try { return JSON.parse(localStorage.getItem('genshin_config') || 'null'); }
  catch { return null; }
}
function saveConfig(cfg) {
  localStorage.setItem('genshin_config', JSON.stringify(cfg));
}

// ── CACHE ──

function loadCache() {
  try {
    const c = JSON.parse(localStorage.getItem('genshin_cache') || 'null');
    if (!c || Date.now() - c.ts > CACHE_TTL) return null;
    return c;
  } catch { return null; }
}
function saveCache(uid, characters) {
  localStorage.setItem('genshin_cache', JSON.stringify({ ts: Date.now(), uid, characters }));
}

// ── NORMALIZE ──

function normalizeChar(raw) {
  return {
    name: raw.name,
    element: ELEMENT_MAP[raw.element] || raw.element || null,
    rarity: raw.rarity || 0,
    level: raw.level || null,
    max_level: raw.max_level || null,
    constellation: raw.actived_constellation_num ?? 0,
    friendship: raw.fetter ?? 0,
    icon: raw.icon,
    weapon: raw.weapon ? {
      name: raw.weapon.name,
      level: raw.weapon.level,
      max_level: raw.weapon.max_level || null,
      refinement: raw.weapon.affix_level ?? 1,
      rarity: raw.weapon.rarity,
    } : null,
    artifacts: (raw.reliquaries || []).map(a => ({
      name: a.name,
      set: a.set?.name || '',
      pos_name: a.pos_name,
      rarity: a.rarity,
      level: a.level,
      main_stat: a.main_property
        ? { name: a.main_property.name, value: a.main_property.value }
        : null,
      sub_stats: (a.append_prop_list || []).map(s => ({ name: s.name, value: s.value })),
    })),
  };
}

// ── INIT ──

function init() {
  const config = loadConfig();
  const ok = config && config.workerUrl && config.ltuid_v2 && config.ltoken_v2 && config.uid;
  if (ok) showRoster(config);
  else showSetup();
}

// ── SETUP VIEW ──

function showSetup() {
  document.getElementById('view-roster').classList.add('hidden');
  document.getElementById('view-setup').classList.remove('hidden');

  const config = loadConfig() || {};
  if (config.workerUrl) document.getElementById('cfg-worker').value = config.workerUrl;
  if (config.ltuid_v2)  document.getElementById('cfg-ltuid').value  = config.ltuid_v2;
  if (config.ltoken_v2) document.getElementById('cfg-ltoken').value = config.ltoken_v2;
  if (config.uid)       document.getElementById('cfg-uid').value    = config.uid;

  document.getElementById('setup-save').onclick = () => {
    const cfg = {
      workerUrl: document.getElementById('cfg-worker').value.trim().replace(/\/$/, ''),
      ltuid_v2:  document.getElementById('cfg-ltuid').value.trim(),
      ltoken_v2: document.getElementById('cfg-ltoken').value.trim(),
      uid:       document.getElementById('cfg-uid').value.trim(),
    };
    const missing = Object.entries(cfg).filter(([, v]) => !v).map(([k]) => k);
    if (missing.length) { alert(`Fill in: ${missing.join(', ')}`); return; }
    saveConfig(cfg);
    localStorage.removeItem('genshin_cache');
    showRoster(cfg);
  };
}

// ── ROSTER VIEW ──

function showRoster(config) {
  document.getElementById('view-setup').classList.add('hidden');
  document.getElementById('view-roster').classList.remove('hidden');

  document.getElementById('settings-btn').onclick = showSetup;
  document.getElementById('refresh-btn').onclick = () => {
    localStorage.removeItem('genshin_cache');
    loadRoster(config);
  };
  document.getElementById('sort-select').onchange = e => {
    activeSort = e.target.value;
    renderRoster();
  };

  loadRoster(config);
}

async function loadRoster(config) {
  const cached = loadCache();
  if (cached) {
    allChars = cached.characters;
    renderFilters();
    renderRoster();
    document.getElementById('loading').classList.add('hidden');
    setFooter(cached.uid, allChars.length, true);
    return;
  }

  document.getElementById('loading').classList.remove('hidden');
  document.getElementById('error').classList.add('hidden');
  document.getElementById('roster').classList.add('hidden');
  document.getElementById('footer').classList.add('hidden');

  try {
    const res = await fetch(config.workerUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ltuid_v2: config.ltuid_v2, ltoken_v2: config.ltoken_v2, uid: config.uid }),
    });
    const data = await res.json();

    if (data.error) { showError(JSON.stringify(data)); return; }
    if (data.retcode !== undefined && data.retcode !== 0) {
      showError(`HoYoLAB error: ${JSON.stringify(data)}`);
      return;
    }

    const characters = (data.data?.list || []).map(normalizeChar);
    saveCache(config.uid, characters);
    allChars = characters;

    renderFilters();
    renderRoster();
    document.getElementById('loading').classList.add('hidden');
    setFooter(config.uid, allChars.length, false);
  } catch {
    showError('Request failed. Check that your Worker URL is correct and the Worker is deployed.');
  }
}

function showError(msg) {
  document.getElementById('loading').classList.add('hidden');
  const el = document.getElementById('error');
  el.textContent = msg;
  el.classList.remove('hidden');
}

function setFooter(uid, count, fromCache) {
  const el = document.getElementById('footer');
  el.textContent = `${count} characters · UID ${uid}${fromCache ? ' · cached' : ''}`;
  el.classList.remove('hidden');
}

// ── FILTERS ──

function renderFilters() {
  const present = new Set(allChars.map(c => c.element));
  const container = document.getElementById('element-filters');
  container.querySelectorAll('[data-element]:not([data-element="all"])').forEach(b => b.remove());

  ELEMENTS.filter(e => present.has(e)).forEach(elem => {
    const btn = document.createElement('button');
    btn.className = 'filter-btn';
    btn.dataset.element = elem;
    btn.textContent = elem.toLowerCase();
    btn.onclick = () => setElement(elem);
    container.appendChild(btn);
  });

  container.querySelector('[data-element="all"]').onclick = () => setElement('all');
  setElement('all');
}

function setElement(elem) {
  activeElement = elem;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.toggle('active', b.dataset.element === elem));
  renderRoster();
}

// ── RENDER ──

function sortedChars() {
  const chars = activeElement === 'all' ? allChars : allChars.filter(c => c.element === activeElement);
  return [...chars].sort((a, b) => {
    switch (activeSort) {
      case 'level':         return b.level - a.level || b.rarity - a.rarity;
      case 'constellation': return b.constellation - a.constellation || b.rarity - a.rarity;
      case 'friendship':    return b.friendship - a.friendship || b.rarity - a.rarity;
      case 'name':          return a.name.localeCompare(b.name);
      default:              return b.rarity - a.rarity || b.level - a.level;
    }
  });
}

function renderRoster() {
  const container = document.getElementById('roster');
  container.innerHTML = sortedChars().map(charCard).join('');
  container.classList.remove('hidden');
  container.querySelectorAll('.char-card').forEach(card => {
    card.onclick = () => toggleExpand(card.dataset.name);
  });
}

function stars(n) { return '★'.repeat(n); }

function artifactSets(artifacts) {
  const counts = {};
  for (const a of artifacts) if (a.set) counts[a.set] = (counts[a.set] || 0) + 1;
  return Object.entries(counts).sort((a, b) => b[1] - a[1])
    .map(([name, n]) => `<span class="set-chip">${name} ${n}pc</span>`).join('');
}

function artifactRows(artifacts) {
  if (!artifacts.length) return '<p style="font-size:0.72rem;color:var(--text-muted)">No artifact data.</p>';
  const ORDER = ['Flower of Life','Plume of Death','Sands of Eon','Goblet of Eonothem','Circlet of Logos'];
  return [...artifacts]
    .sort((a, b) => ORDER.indexOf(a.pos_name) - ORDER.indexOf(b.pos_name))
    .map(a => `
      <div class="artifact-row">
        <span class="artifact-level">+${a.level}</span>
        <div class="artifact-slot">${a.pos_name}</div>
        <div class="artifact-name">${a.name}</div>
        ${a.main_stat ? `<div class="artifact-main">${a.main_stat.name} · ${a.main_stat.value}</div>` : ''}
        <div class="artifact-subs">
          ${(a.sub_stats || []).map(s => `<span class="artifact-sub">${s.name} ${s.value}</span>`).join('')}
        </div>
      </div>`).join('');
}

function charCard(char) {
  const isOpen = expanded.has(char.name);
  const rc = char.rarity === 5 ? 'r5' : 'r4';
  const w = char.weapon;
  return `
    <div class="char-card" data-element="${char.element}" data-name="${char.name}">
      <div class="char-main">
        <img class="char-icon ${rc}" src="${char.icon}" alt="${char.name}" loading="lazy"
             onerror="this.style.display='none'">
        <div class="char-info">
          <div class="char-name">${char.name}</div>
          <div class="char-meta">
            ${char.element ? `<span class="element-pill ${char.element}">${char.element}</span>` : ''}
            ${char.rarity ? `<span class="stars ${rc}">${stars(char.rarity)}</span>` : ''}
          </div>
          <div class="char-stats">
            ${char.level != null ? `<div class="stat-chip"><span class="val">${char.level}/${char.max_level}</span><span class="lbl">level</span></div>` : ''}
            <div class="stat-chip"><span class="val">C${char.constellation}</span><span class="lbl">const</span></div>
            ${char.friendship ? `<div class="stat-chip"><span class="val">${char.friendship}</span><span class="lbl">friend</span></div>` : ''}
          </div>
        </div>
      </div>
      ${w ? `
      <div class="char-weapon">
        <span class="weapon-stars ${w.rarity >= 5 ? 'r5' : 'r4'}">${stars(w.rarity)}</span>
        <span class="weapon-name">${w.name}</span>
        <span class="weapon-meta">R${w.refinement} · ${w.max_level ? `${w.level}/${w.max_level}` : w.level}</span>
      </div>` : ''}
      ${char.artifacts?.length || char.level != null ? `<div class="expand-hint">${isOpen ? '▲ hide artifacts' : '▼ show artifacts'}</div>` : ''}
      ${isOpen ? `
      <div class="artifact-panel">
        <div class="artifact-panel-title">artifacts</div>
        <div class="artifact-sets">${artifactSets(char.artifacts)}</div>
        <div class="artifact-list">${artifactRows(char.artifacts)}</div>
      </div>` : ''}
    </div>`;
}

function toggleExpand(name) {
  if (expanded.has(name)) expanded.delete(name);
  else expanded.add(name);
  renderRoster();
}

init();
