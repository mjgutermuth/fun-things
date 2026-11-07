const WORKER_URL = 'https://genshin-roster.meli327.workers.dev';
const CACHE_TTL = 5 * 60 * 1000;
const ELEMENTS = ['Pyro','Hydro','Anemo','Electro','Dendro','Cryo','Geo'];
const ELEMENT_MAP = {
  Fire: 'Pyro', Water: 'Hydro', Wind: 'Anemo',
  Electric: 'Electro', Grass: 'Dendro', Ice: 'Cryo', Rock: 'Geo',
};
const DAY_NAMES = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday'];
const TARGET_LEVELS = [20, 40, 50, 60, 70, 80, 90];

// Bump this whenever DOMAINS or TEAMS_DATA are checked against the current version.
const DATA_VERSION = 'v7.2 — Nov 2026';

// Talent book domains — days: 1=Mon,4=Thu | 2=Tue,5=Fri | 3=Wed,6=Sat | 0=Sun(all)
const DOMAINS = [
  {
    name: 'Forsaken Rift', region: 'Mondstadt',
    slots: [
      { days: [1,4], book: 'Freedom',    chars: ['Amber','Barbara','Klee','Sucrose','Diona'] },
      { days: [2,5], book: 'Resistance', chars: ['Jean','Diluc','Razor','Bennett','Noelle','Mona','Eula'] },
      { days: [3,6], book: 'Ballad',     chars: ['Lisa','Kaeya','Venti','Fischl','Albedo','Rosaria','Mika','Durin'] },
    ],
  },
  {
    name: 'Taishan Mansion', region: 'Liyue',
    slots: [
      { days: [1,4], book: 'Prosperity', chars: ['Xiao','Ningguang','Qiqi','Keqing','Shenhe','Yelan','Gaming'] },
      { days: [2,5], book: 'Diligence',  chars: ['Xiangling','Chongyun','Ganyu','Hu Tao','Kazuha','Yun Jin','Yaoyao','Lan Yan'] },
      { days: [3,6], book: 'Gold',       chars: ['Beidou','Xingqiu','Zhongli','Xinyan','Yanfei','Baizhu','Xianyun','Zibai'] },
    ],
  },
  {
    name: 'Violet Court', region: 'Inazuma',
    slots: [
      { days: [1,4], book: 'Transience', chars: ['Yoimiya','Thoma','Kokomi','Heizou','Kirara','Mizuki'] },
      { days: [2,5], book: 'Elegance',   chars: ['Kamisato Ayaka','Kujou Sara','Itto','Kamisato Ayato','Kuki Shinobu'] },
      { days: [3,6], book: 'Light',      chars: ['Yae Miko','Sayu','Gorou','Raiden Shogun','Chiori'] },
    ],
  },
  {
    name: 'Steeple of Ignorance', region: 'Sumeru',
    slots: [
      { days: [1,4], book: 'Admonition', chars: ['Cyno','Tighnari','Candace','Faruzan'] },
      { days: [2,5], book: 'Ingenuity',  chars: ['Nahida','Layla','Dori','Alhaitham','Kaveh'] },
      { days: [3,6], book: 'Praxis',     chars: ['Wanderer','Collei','Dehya','Nilou','Sethos'] },
    ],
  },
  {
    name: 'Pale Forgotten Glory', region: 'Fontaine',
    slots: [
      { days: [1,4], book: 'Equity',   chars: ['Lyney','Navia','Sigewinne','Neuvillette'] },
      { days: [2,5], book: 'Justice',  chars: ['Charlotte','Freminet','Furina','Clorinde','Escoffier'] },
      { days: [3,6], book: 'Order',    chars: ['Lynette','Arlecchino','Wriothesley','Emilie','Chevreuse'] },
    ],
  },
  {
    name: 'Lightless Capital', region: 'Nod-Krai',
    slots: [
      { days: [1,4], book: 'Vagrancy',  chars: ['Jahoda','Flins','Linnea'] },
      { days: [2,5], book: 'Elysium',   chars: ['Nefer','Aino','Illuga','Nicole'] },
      { days: [3,6], book: 'Moonlight', chars: ['Lauma','Columbina'] },
    ],
  },
  {
    name: 'Blazing Ruins', region: 'Natlan',
    slots: [
      { days: [1,4], book: 'Contention', chars: ['Skirk','Mualani','Mavuika'] },
      { days: [2,5], book: 'Kindling',   chars: ['Kinich','Citlali','Xilonen','Ororon'] },
      { days: [3,6], book: 'Conflict',   chars: ['Kachina','Chasca','Ifa','Varesa'] },
    ],
  },
  {
    name: 'Relics of the Fallen Grace', region: 'Snezhnaya',
    slots: [
      { days: [1,4], book: 'Charity',   chars: ['Odette','Mitya'] },
      { days: [2,5], book: 'Fortitude', chars: ['Alyosha','Vodyanitsa'] },
      { days: [3,6], book: 'Glory',     chars: ['Vesna','Valeriy'] },
    ],
  },
];

const CHAR_DOMAIN = Object.fromEntries(
  DOMAINS.flatMap(d => d.slots.flatMap(s => s.chars.map(c => [c, { domain: d.name, book: s.book, days: s.days }])))
);


const META_CHARS = typeof TEAMS_DATA !== 'undefined'
  ? new Set(TEAMS_DATA.flatMap(t => t.roles.flatMap(r => r.chars)))
  : new Set();

let teamsPromise = null;

let allChars = [];
let activeElement = 'all';
let activeSearch = '';
let activeSort = 'default';
let activeView = 'grid';
let activeTab = 'roster';
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

// ── PRIORITY ──

function loadPriority() {
  try { return JSON.parse(localStorage.getItem('genshin_priority') || '{}'); }
  catch { return {}; }
}
function savePriority(p) { localStorage.setItem('genshin_priority', JSON.stringify(p)); }

function togglePriority(name) {
  const p = loadPriority();
  if (p[name]) delete p[name];
  else p[name] = { targetLevel: 90 };
  savePriority(p);
  renderRoster();
  if (activeTab === 'priority') renderPriorityTab();
}

function setPriorityTarget(name, val) {
  const p = loadPriority();
  if (p[name]) { p[name].targetLevel = +val; savePriority(p); }
}


// ── TABS ──

function setTab(tab) {
  activeTab = tab;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
  const isRoster = tab === 'roster';
  document.getElementById('roster-controls').classList.toggle('hidden', !isRoster);
  document.getElementById('roster').classList.toggle('hidden', !isRoster || !allChars.length);

  const priorityEl = document.getElementById('tab-priority');
  const teamsEl    = document.getElementById('tab-teams');
  const abyssEl    = document.getElementById('tab-abyss');

  priorityEl.classList.add('hidden');
  teamsEl.classList.add('hidden');
  abyssEl.classList.add('hidden');

  if (tab === 'priority') { priorityEl.classList.remove('hidden'); renderPriorityTab(); }
  if (tab === 'teams')    { teamsEl.classList.remove('hidden');    renderTeamsTab(); }
  if (tab === 'abyss')    { abyssEl.classList.remove('hidden');    renderAbyssTab(); }
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
  teamsPromise = Promise.resolve(typeof TEAMS_DATA !== 'undefined' ? TEAMS_DATA : []);
  const config = loadConfig();
  const ok = config && config.ltuid_v2 && config.ltoken_v2 && config.uid;
  if (ok) showRoster(config);
  else showSetup();
}

// ── SETUP VIEW ──

function showSetup() {
  document.getElementById('view-roster').classList.add('hidden');
  document.getElementById('view-setup').classList.remove('hidden');

  const config = loadConfig() || {};
  if (config.ltuid_v2)  document.getElementById('cfg-ltuid').value  = config.ltuid_v2;
  if (config.ltoken_v2) document.getElementById('cfg-ltoken').value = config.ltoken_v2;
  if (config.ltmid_v2)  document.getElementById('cfg-ltmid').value  = config.ltmid_v2;
  if (config.uid)       document.getElementById('cfg-uid').value    = config.uid;

  document.getElementById('setup-save').onclick = () => {
    const cfg = {
      ltuid_v2:  document.getElementById('cfg-ltuid').value.trim(),
      ltoken_v2: document.getElementById('cfg-ltoken').value.trim(),
      ltmid_v2:  document.getElementById('cfg-ltmid').value.trim(),
      uid:       document.getElementById('cfg-uid').value.trim(),
    };
    const missing = Object.entries(cfg).filter(([k, v]) => k !== 'ltmid_v2' && !v).map(([k]) => k);
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
  document.getElementById('view-btn').onclick = () => {
    activeView = activeView === 'grid' ? 'list' : 'grid';
    document.getElementById('view-btn').title = activeView === 'grid' ? 'Toggle view' : 'Toggle view';
    document.getElementById('view-btn').textContent = activeView === 'grid' ? '☰' : '⊞';
    renderRoster();
  };
  document.getElementById('search-input').oninput = e => {
    activeSearch = e.target.value.toLowerCase();
    renderRoster();
  };
  document.getElementById('sort-select').onchange = e => {
    activeSort = e.target.value;
    renderRoster();
  };
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.onclick = () => setTab(btn.dataset.tab);
  });

  loadRoster(config);
}

async function loadRoster(config) {
  const cached = loadCache();
  if (cached) {
    allChars = cached.characters;
    renderFilters();
    renderRoster();
    document.getElementById('loading').classList.add('hidden');
    setFooter(cached.uid, allChars, true);
    return;
  }

  document.getElementById('loading').classList.remove('hidden');
  document.getElementById('error').classList.add('hidden');
  document.getElementById('roster').classList.add('hidden');
  document.getElementById('footer').classList.add('hidden');

  try {
    const res = await fetch(WORKER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ltuid_v2: config.ltuid_v2, ltoken_v2: config.ltoken_v2, ltmid_v2: config.ltmid_v2, uid: config.uid }),
    });
    const data = await res.json();

    if (data.retcode !== undefined && data.retcode !== 0) {
      if ([1005, -100, 10001, 10101].includes(data.retcode)) {
        showSessionExpired();
      } else {
        showError(`HoYoLAB error ${data.retcode}: ${data.message || JSON.stringify(data)}`);
      }
      return;
    }
    if (data.error && !data.retcode) { showError(data.error); return; }

    const characters = (data.data?.list || []).map(normalizeChar);
    saveCache(config.uid, characters);
    allChars = characters;

    renderFilters();
    renderRoster();
    if (activeTab === 'abyss') renderAbyssTab();
    document.getElementById('loading').classList.add('hidden');
    setFooter(config.uid, allChars, false);
  } catch {
    showError('Request failed. Check that your Worker URL is correct and the Worker is deployed.');
  }
}

function showSessionExpired() {
  document.getElementById('loading').classList.add('hidden');
  const el = document.getElementById('error');
  el.innerHTML = '';
  const msg = document.createElement('div');
  msg.className = 'session-expired';
  msg.innerHTML = `
    <div class="session-title">session expired</div>
    <div class="session-body">your <code>ltoken_v2</code> needs to be refreshed — go to hoyolab.com, grab the new value from cookies, and paste it below.</div>
    <button class="session-btn">update ltoken_v2 →</button>
  `;
  msg.querySelector('.session-btn').onclick = showSetup;
  el.appendChild(msg);
  el.classList.remove('hidden');
}

function showError(msg) {
  document.getElementById('loading').classList.add('hidden');
  const el = document.getElementById('error');
  el.textContent = msg;
  el.classList.remove('hidden');
}

function setFooter(uid, chars, fromCache) {
  const fiveStars = chars.filter(c => c.rarity === 5).length;
  const el = document.getElementById('footer');
  el.textContent = `${chars.length} characters · ${fiveStars} five-stars · UID ${uid}${fromCache ? ' · cached' : ''}`;
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
  let chars = activeElement === 'all' ? allChars : allChars.filter(c => c.element === activeElement);
  if (activeSort === 'meta') chars = chars.filter(c => META_CHARS.has(c.name));
  if (activeSearch) chars = chars.filter(c => c.name.toLowerCase().includes(activeSearch));
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
  const priority = loadPriority();
  const container = document.getElementById('roster');
  if (activeTab !== 'roster') return;
  if (activeView === 'list') {
    container.className = 'roster roster-list';
    container.innerHTML = sortedChars().map(c => charRow(c, priority)).join('');
  } else {
    container.className = 'roster';
    container.innerHTML = sortedChars().map(c => charCard(c, priority)).join('');
    container.querySelectorAll('.char-card').forEach(card => {
      card.onclick = () => toggleExpand(card.dataset.name);
    });
  }
  container.classList.remove('hidden');
  container.querySelectorAll('.priority-star').forEach(btn => {
    btn.onclick = e => { e.stopPropagation(); togglePriority(btn.dataset.name); };
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

function charRow(char, priority = {}) {
  const isPriority = !!priority[char.name];
  const rc = char.rarity === 5 ? 'r5' : 'r4';
  const w = char.weapon;
  return `
    <div class="char-row" data-element="${char.element}" data-name="${char.name}">
      <img class="row-icon ${rc}" src="${char.icon}" alt="${char.name}" loading="lazy" onerror="this.style.display='none'">
      <span class="row-name">${char.name}</span>
      ${char.element ? `<span class="element-pill ${char.element}">${char.element}</span>` : ''}
      <span class="row-level">${char.level != null ? `${char.level}${char.max_level != null ? `/${char.max_level}` : ''}` : '—'}</span>
      <span class="row-weapon">${w ? w.name : '—'}</span>
      <span class="row-const">C${char.constellation}</span>
      <span class="row-book">${CHAR_DOMAIN[char.name] ? CHAR_DOMAIN[char.name].book.toLowerCase() : '—'}</span>
      ${META_CHARS.has(char.name) ? `<span class="row-meta" title="used in a meta team">meta</span>` : '<span></span>'}
      <button class="priority-star${isPriority ? ' active' : ''}" data-name="${char.name}" title="${isPriority ? 'remove from queue' : 'add to queue'}">★</button>
    </div>`;
}

function charCard(char, priority = {}) {
  const isOpen = expanded.has(char.name);
  const isPriority = !!priority[char.name];
  const rc = char.rarity === 5 ? 'r5' : 'r4';
  const w = char.weapon;
  return `
    <div class="char-card" data-element="${char.element}" data-name="${char.name}">
      <button class="priority-star${isPriority ? ' active' : ''}" data-name="${char.name}" title="${isPriority ? 'remove from queue' : 'add to queue'}">★</button>
      <div class="char-main">
        <img class="char-icon ${rc}" src="${char.icon}" alt="${char.name}" loading="lazy"
             onerror="this.style.display='none'">
        <div class="char-info">
          <div class="char-name">${char.name}</div>
          <div class="char-meta">
            ${char.element ? `<span class="element-pill ${char.element}">${char.element}</span>` : ''}
            ${char.rarity ? `<span class="stars ${rc}">${stars(char.rarity)}</span>` : ''}
            ${META_CHARS.has(char.name) ? `<span class="meta-badge">meta</span>` : ''}
          </div>
          <div class="char-stats">
            ${char.level != null ? `<div class="stat-chip"><span class="val">${char.level}${char.max_level != null ? `/${char.max_level}` : ''}</span><span class="lbl">level</span></div>` : ''}
            <div class="stat-chip"><span class="val">C${char.constellation}</span><span class="lbl">const</span></div>
            ${char.friendship ? `<div class="stat-chip"><span class="val">${char.friendship}</span><span class="lbl">friend</span></div>` : ''}
          </div>
          ${CHAR_DOMAIN[char.name] ? `<div class="char-book">book of ${CHAR_DOMAIN[char.name].book.toLowerCase()}</div>` : ''}
        </div>
      </div>
      ${w ? `
      <div class="char-weapon">
        <span class="weapon-stars ${w.rarity >= 5 ? 'r5' : 'r4'}">${stars(w.rarity)}</span>
        <span class="weapon-name">${w.name}</span>
        <span class="weapon-meta">R${w.refinement} · ${w.max_level ? `${w.level}/${w.max_level}` : w.level}</span>
      </div>` : ''}
      ${char.artifacts?.length ? `<div class="expand-hint">${isOpen ? '▲ hide artifacts' : '▼ show artifacts'}</div>` : ''}
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

// ── TEAMS TAB ──

async function renderTeamsTab() {
  const archetypes = await teamsPromise;
  const charNames = new Set(allChars.map(c => c.name));
  const scored = archetypes
    .map(t => ({ ...t, score: t.roles.filter(r => r.chars.some(c => charNames.has(c))).length }))
    .sort((a, b) => b.score - a.score || (a.tier ?? 99) - (b.tier ?? 99) || a.name.localeCompare(b.name));

  const updatedNote = `<p class="setup-note teams-updated">meta last checked: ${DATA_VERSION}</p>`;
  document.getElementById('tab-teams').innerHTML = updatedNote + scored.map(t => teamCard(t, charNames)).join('');
}

function teamCard(team, charNames) {
  const total = team.roles.length;
  const filled = team.roles.filter(r => r.chars.some(c => charNames.has(c))).length;
  const statusLabel = filled === total ? 'ready' : filled === total - 1 ? '1 missing' : `${total - filled} missing`;
  const statusClass = filled === total ? 'status-ready' : filled >= total - 1 ? 'status-almost' : filled >= 2 ? 'status-partial' : 'status-low';

  const rolesHtml = team.roles.map(role => {
    const have    = role.chars.filter(c => charNames.has(c));
    const missing = role.chars.filter(c => !charNames.has(c));
    const isFilled = have.length > 0;
    const charHtml = isFilled
      ? have.map(name => {
          const c = allChars.find(x => x.name === name);
          return c
            ? `<div class="role-char have"><img src="${c.icon}" alt="${name}" class="role-icon ${c.rarity === 5 ? 'r5' : 'r4'}" onerror="this.style.display='none'"><span>${name}</span></div>`
            : `<div class="role-char have"><span>${name}</span></div>`;
        }).join('')
      : missing.slice(0, 3).map(n => `<div class="role-char missing"><span>${n}</span></div>`).join('');

    return `
      <div class="team-role${isFilled ? '' : ' unfilled'}">
        <div class="role-label">${role.label}</div>
        <div class="role-chars">${charHtml}</div>
      </div>`;
  }).join('');

  return `
    <div class="team-card">
      <div class="team-header">
        <span class="team-name">${team.name}</span>
        ${team.tier != null ? `<span class="team-tier">T${team.tier}</span>` : ''}
        <span class="team-tags">${team.tags.map(t => `<span class="team-tag">${t}</span>`).join('')}</span>
        <span class="team-status ${statusClass}">${statusLabel}</span>
      </div>
      ${team.notes ? `<p class="team-notes">${team.notes}</p>` : ''}
      <div class="team-roles">${rolesHtml}</div>
    </div>`;
}

// ── ABYSS TAB ──

const HALF_NAMES = ['first half', 'second half'];
const WIKI_API = 'https://genshin-impact.fandom.com/api.php';
let abyssCycleId = null;
let abyssActiveHalf = 0;
let abyssPoolElement = 'all';
let abyssPoolSearch = '';
let abyssPullMsg = '';

// An element DMG bonus also favors teams tagged only by the reaction that element carries.
const ELEMENT_REACTIONS = {
  Cryo:    ['Freeze', 'Melt'],
  Pyro:    ['Vaporize', 'Melt', 'Overloaded'],
  Hydro:   ['Vaporize', 'Freeze', 'Bloom'],
  Electro: ['Aggravate', 'Hyperbloom', 'Lunar-Charged'],
  Dendro:  ['Bloom', 'Hyperbloom', 'Lunar Bloom'],
};

// Disorder text → TEAMS_DATA tags, so suggestions follow whatever the wiki says.
const DISORDER_TAGS = [
  [/stellar glimmer/i,          ['Stellar-Conduct', 'Stellar-Swirl']],
  [/stellar-conduct|superconduct/i, ['Stellar-Conduct']],
  [/stellar[- ]swirl/i,         ['Stellar-Swirl']],
  [/lunar[- ]charged/i,         ['Lunar-Charged']],
  [/lunar[- ]bloom/i,           ['Lunar Bloom']],
  [/frozen|freeze|shatter/i,    ['Freeze']],
  [/hyperbloom/i,               ['Hyperbloom']],
  [/\bbloom\b/i,                ['Bloom']],
  [/vaporize/i,                 ['Vaporize']],
  [/\bmelt\b/i,                 ['Melt']],
  [/aggravate/i,                ['Aggravate']],
  [/overloaded/i,               ['Overloaded']],
  [/plunging/i,                 ['Plunge']],
  ...ELEMENTS.map(e => [new RegExp(`\\b${e}\\b`, 'i'), [e, ...(ELEMENT_REACTIONS[e] || [])]]),
];

function disorderTags(text) {
  if (!text) return [];
  return [...new Set(DISORDER_TAGS.filter(([re]) => re.test(text)).flatMap(([, tags]) => tags))];
}

// ── abyss data: static abyss.js, overlaid with whatever was last pulled from the wiki ──

function loadPulledAbyss() {
  try { return JSON.parse(localStorage.getItem('genshin_abyss_pulled') || 'null'); }
  catch { return null; }
}

function mergeCycle(base, pulled) {
  return {
    ...base, ...pulled,
    blessing: pulled.blessing || base.blessing,
    halves: pulled.halves.map((h, i) => ({
      disorder: h.disorder || base.halves[i]?.disorder || null,
      tags: h.tags.length ? h.tags : (base.halves[i]?.tags || []),
      tip: base.halves[i]?.tip || null, // tips are hand-written, the wiki has none
    })),
    chambers: pulled.chambers.length ? pulled.chambers : base.chambers,
  };
}

function abyssCycles() {
  const byId = new Map((typeof ABYSS_CYCLES !== 'undefined' ? ABYSS_CYCLES : []).map(c => [c.id, c]));
  for (const p of loadPulledAbyss()?.cycles || []) {
    byId.set(p.id, byId.has(p.id) ? mergeCycle(byId.get(p.id), p) : p);
  }
  return [...byId.values()].sort((a, b) => a.start.localeCompare(b.start));
}

// ── wiki pull ──

async function wikiApi(params) {
  const url = new URL(WIKI_API);
  Object.entries({ format: 'json', formatversion: '2', origin: '*', ...params })
    .forEach(([k, v]) => url.searchParams.set(k, v));
  const data = await (await fetch(url)).json();
  if (data.error) throw new Error(data.error.info || data.error.code);
  return data;
}

function cleanWiki(s) {
  return s
    .replace(/\[\[(?:[^|\]]*\|)?([^\]]*)\]\]/g, '$1')
    .replace(/\{\{Color\|[^|}]*\|([^}]*)\}\}/g, '$1')
    .replace(/\{\{[^}]*\}\}/g, '')
    .replace(/'''?/g, '')
    .replace(/<[^>]+>/g, '')
    .trim();
}

function templateParams(block) {
  const params = {};
  for (const line of block.split('\n')) {
    const m = line.match(/^\s*\|\s*(\w+)\s*=\s*(.*)$/);
    if (m) params[m[1]] = m[2].trim();
  }
  return params;
}

// "A*2; B// C*?" → [['A ×2', 'B'], ['C']]
function parseWaves(s) {
  return (s || '').split('//').map(wave => wave.split(';').map(e => {
    const [name, count] = e.split('*').map(x => x.trim());
    return cleanWiki(name) + (/^\d+$/.test(count || '') ? ` ×${count}` : '');
  }).filter(Boolean)).filter(w => w.length);
}

function isoDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function nextCycleStart(start) {
  const d = new Date(`${start}T12:00`);
  d.setMonth(d.getMonth() + 1, 16);
  return isoDate(d);
}

async function fetchWikiCycle(start) {
  const title = `Spiral Abyss/Floors/${start}`;
  const { parse } = await wikiApi({ action: 'parse', page: title, prop: 'wikitext' });
  // The wiki comments out anything not yet confirmed — treat that as not announced.
  const wt = parse.wikitext.replace(/<!--[\s\S]*?-->/g, '');

  const spire = templateParams(wt.match(/\{\{Abyssal Moon Spire([\s\S]*?)\}\}/)?.[1] || '');
  const floor12 = wt.split(/^===\s*Floor 12\s*===\s*$/m)[1]?.split(/^==[^=]/m)[0] || '';
  const enemies = templateParams(floor12.match(/\{\{Domain Enemies([\s\S]*?)\n\}\}/)?.[1] || '');
  const chambers = [1, 2, 3]
    .filter(n => enemies[`enemies${n}_1`])
    .map(n => ({
      level: +enemies[`level${n}`] || null,
      first: parseWaves(enemies[`enemies${n}_1`]),
      second: parseWaves(enemies[`enemies${n}_2`]),
    }));
  if (!chambers.length) throw new Error(`no Floor 12 lineup on ${title}`);

  const halfDisorder = label => {
    const m = floor12.match(new RegExp(`${label}(?:\\}\\})?\\s*:\\s*(.+)`, 'i'));
    return m ? cleanWiki(m[1]) : null;
  };
  const halves = ['First Half', 'Second Half'].map(label => {
    const disorder = halfDisorder(label);
    return { disorder, tags: disorderTags(disorder), tip: null };
  });

  let blessing = null;
  if (wt.includes('{{Blessing of the Abyssal Moon Schedule}}')) {
    const { expandtemplates } = await wikiApi({
      action: 'expandtemplates', prop: 'wikitext', title,
      text: '{{Blessing of the Abyssal Moon Schedule}}',
    });
    const html = expandtemplates.wikitext;
    const name = html.match(/!\s*colspan=2\s*\|\s*(.+)/)?.[1];
    const effect = [...html.matchAll(/<li>([\s\S]*?)<\/li>/g)].map(m => cleanWiki(m[1])).join(' ');
    if (name && effect) blessing = { name: cleanWiki(name), effect };
  }

  return {
    id: start, start,
    reset: spire.next || nextCycleStart(start),
    version: spire.startVersion || '?',
    blessing, halves, chambers,
  };
}

async function pullAbyssFromWiki() {
  // Cycles start on the 16th: pull the one running now and the next one.
  const cur = new Date();
  if (cur.getDate() < 16) cur.setMonth(cur.getMonth() - 1, 16); else cur.setDate(16);
  const start = isoDate(cur);

  const results = await Promise.allSettled([start, nextCycleStart(start)].map(fetchWikiCycle));
  const cycles = results.filter(r => r.status === 'fulfilled').map(r => r.value);
  if (!cycles.length) throw new Error(results[0].reason?.message || 'wiki pull failed');

  const prev = loadPulledAbyss()?.cycles || [];
  const merged = [...prev.filter(p => !cycles.some(c => c.id === p.id)), ...cycles];
  localStorage.setItem('genshin_abyss_pulled', JSON.stringify({ ts: Date.now(), cycles: merged }));
  return cycles;
}

function loadAbyssPlans() {
  try { return JSON.parse(localStorage.getItem('genshin_abyss') || '{}'); }
  catch { return {}; }
}
function saveAbyssPlans(p) { localStorage.setItem('genshin_abyss', JSON.stringify(p)); }

function abyssPlan(cycleId) {
  const plan = loadAbyssPlans()[cycleId];
  return plan?.halves ? plan.halves : [[null,null,null,null],[null,null,null,null]];
}
function setAbyssPlan(cycleId, halves) {
  const plans = loadAbyssPlans();
  plans[cycleId] = { halves };
  saveAbyssPlans(plans);
}

// Cycles flip at 4am server time; local 4am is close enough for a countdown.
function abyssDate(s) { return new Date(`${s}T04:00:00`); }
function shortDate(d) { return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }).toLowerCase(); }

function cycleStatus(c, now = new Date()) {
  if (now < abyssDate(c.start)) return 'upcoming';
  if (now >= abyssDate(c.reset)) return 'ended';
  return 'live';
}

function defaultAbyssCycle(all = abyssCycles()) {
  return all.find(c => cycleStatus(c) === 'live')
      || all.find(c => cycleStatus(c) === 'upcoming')
      || all[all.length - 1];
}

function placeInHalf(halves, name, half, slot) {
  // A character can only be in one slot across both halves — pull them out first.
  halves.forEach(h => h.forEach((n, i) => { if (n === name) h[i] = null; }));
  halves[half][slot] = name;
}

function abyssSuggestions(half, halves) {
  const owned = new Set(allChars.map(c => c.name));
  const usedElsewhere = new Set(halves[1 - half].filter(Boolean));
  const available = n => owned.has(n) && !usedElsewhere.has(n);
  const tags = new Set(abyssCycle().halves[half]?.tags || []);
  return TEAMS_DATA
    .filter(t => !tags.size || t.tags.some(tag => tags.has(tag)))
    .map(t => ({
      ...t,
      score: t.roles.filter(r => r.chars.some(available)).length,
      // A team's first tag is its archetype, so a match there counts double.
      fit: t.tags.reduce((n, tag, i) => n + (tags.has(tag) ? (i === 0 ? 2 : 1) : 0), 0),
    }))
    .filter(t => t.score > 0)
    .sort((a, b) => b.score - a.score || b.fit - a.fit || (a.tier ?? 99) - (b.tier ?? 99))
    .slice(0, 3)
    .map(t => {
      const picked = [];
      for (const r of t.roles) picked.push(r.chars.find(c => available(c) && !picked.includes(c)) || null);
      return { team: t, picked };
    });
}

function abyssCycle(all = abyssCycles()) {
  return all.find(c => c.id === abyssCycleId) || defaultAbyssCycle(all);
}

function renderAbyssTab() {
  const container = document.getElementById('tab-abyss');
  const all = abyssCycles();
  const pullBtn = `<button id="abyss-pull" class="abyss-clear-btn abyss-pull-btn">↻ pull from wiki</button>`;
  if (!all.length) {
    container.innerHTML = `<div class="abyss-top">${pullBtn}</div><p class="empty-hint">no abyss data — pull from the wiki or add a cycle to abyss.js</p>`;
    wireAbyssPull();
    return;
  }

  const cycle = abyssCycle(all);
  abyssCycleId = cycle.id;
  const now = new Date();
  const halves = abyssPlan(cycle.id);
  const last = all[all.length - 1];
  const pulledAt = loadPulledAbyss()?.ts;

  const visible = all.filter(c => cycleStatus(c, now) !== 'ended');
  const cycles = visible.length ? visible : [last];
  const resetEnd = new Date(abyssDate(cycle.reset) - 86400000);
  const daysLeft = Math.ceil((abyssDate(cycle.reset) - now) / 86400000);
  const status = cycleStatus(cycle, now);

  const staleNote = !all.some(c => cycleStatus(c, now) === 'live')
    ? `<div class="abyss-warn">abyss data is out of date — the last known cycle reset on ${shortDate(abyssDate(last.reset))}. hit "pull from wiki" to grab the current one.</div>`
    : '';
  const pullNote = abyssPullMsg || (pulledAt ? `pulled from the genshin wiki ${shortDate(new Date(pulledAt))}` : 'using abyss.js');

  const cycleChips = cycles.map(c => `
    <button class="filter-btn abyss-cycle-btn${c.id === cycle.id ? ' active' : ''}" data-cycle="${c.id}">
      v${c.version} · ${shortDate(abyssDate(c.start))}${cycleStatus(c, now) === 'upcoming' ? ' · next' : ''}
    </button>`).join('');

  const timing = status === 'live'
    ? `resets in ${daysLeft} day${daysLeft === 1 ? '' : 's'} · ${shortDate(abyssDate(cycle.start))} – ${shortDate(resetEnd)}`
    : status === 'upcoming'
      ? `starts ${shortDate(abyssDate(cycle.start))} · runs until ${shortDate(resetEnd)}`
      : `ended ${shortDate(resetEnd)}`;

  const blessing = cycle.blessing
    ? `<div class="abyss-blessing"><span class="abyss-blessing-name">${cycle.blessing.name}</span> ${cycle.blessing.effect}</div>`
    : `<div class="abyss-blessing tbd">blessing not announced yet</div>`;

  container.innerHTML = `
    ${staleNote}
    <div class="abyss-top">
      <div class="element-filters">${cycleChips}</div>
      <span class="setup-note">${timing}</span>
    </div>
    <div class="abyss-top">
      <span class="setup-note">${pullNote}</span>
      ${pullBtn}
    </div>
    ${blessing}
    <div class="abyss-halves">${[0, 1].map(h => abyssHalfHtml(cycle, h, halves)).join('')}</div>
    ${abyssPoolHtml(halves)}
  `;
  wireAbyssTab(cycle, halves);
}

function abyssHalfHtml(cycle, h, halves) {
  const info = cycle.halves[h];
  const enemies = cycle.chambers.map((ch, i) => `
    <div class="abyss-chamber">
      <span class="abyss-chamber-num">12-${i + 1}${ch.level ? ` · lv ${ch.level}` : ''}</span>
      <span class="abyss-enemies">${ch[h === 0 ? 'first' : 'second'].map(w => w.join(', ')).join(' → ')}</span>
    </div>`).join('');

  const slots = halves[h].map((name, i) => {
    const c = name && allChars.find(x => x.name === name);
    if (!name) return `<div class="abyss-slot empty" data-half="${h}" data-slot="${i}">+</div>`;
    return `
      <div class="abyss-slot" data-half="${h}" data-slot="${i}" data-element="${c?.element || ''}" draggable="true" data-name="${name}">
        ${c ? `<img src="${c.icon}" alt="${name}" class="abyss-slot-icon ${c.rarity === 5 ? 'r5' : 'r4'}" onerror="this.style.display='none'">` : ''}
        <span class="abyss-slot-name">${name}</span>
        <button class="abyss-slot-remove" data-half="${h}" data-slot="${i}" title="remove">×</button>
      </div>`;
  }).join('');

  const elements = halves[h].map(n => allChars.find(c => c.name === n)?.element).filter(Boolean);
  const elementPills = [...new Set(elements)].map(e => `<span class="element-pill ${e}">${e}</span>`).join('');

  const suggestions = abyssSuggestions(h, halves).map((s, i) => `
    <div class="abyss-suggestion">
      <span class="abyss-sugg-name">${s.team.name}</span>
      <span class="abyss-sugg-chars">${s.picked.map(n => n || '—').join(' · ')}</span>
      <button class="abyss-use-btn" data-half="${h}" data-sugg="${i}">use</button>
    </div>`).join('');

  return `
    <section class="abyss-half${abyssActiveHalf === h ? ' active' : ''}" data-half="${h}">
      <div class="abyss-half-head">
        <span class="abyss-half-name">${HALF_NAMES[h]}</span>
        ${elementPills}
        <button class="abyss-clear-btn" data-half="${h}">clear</button>
      </div>
      <div class="abyss-disorder${info.disorder ? '' : ' tbd'}">${info.disorder || 'disorder not announced yet'}</div>
      ${info.tip ? `<p class="team-notes">${info.tip}</p>` : ''}
      <div class="abyss-chambers">${enemies}</div>
      <div class="abyss-slots">${slots}</div>
      ${suggestions ? `<div class="abyss-suggestions"><div class="role-label">suggested from your roster</div>${suggestions}</div>` : ''}
    </section>`;
}

function abyssPoolHtml(halves) {
  if (!allChars.length) return '<p class="empty-hint">roster still loading…</p>';
  const usedIn = {};
  halves.forEach((h, i) => h.forEach(n => { if (n) usedIn[n] = i; }));

  const present = new Set(allChars.map(c => c.element));
  const filters = ['all', ...ELEMENTS.filter(e => present.has(e))].map(e => `
    <button class="filter-btn abyss-pool-filter${abyssPoolElement === e ? ' active' : ''}" data-element="${e}">${e.toLowerCase()}</button>`).join('');

  const chars = allChars
    .filter(c => abyssPoolElement === 'all' || c.element === abyssPoolElement)
    .filter(c => !abyssPoolSearch || c.name.toLowerCase().includes(abyssPoolSearch))
    .sort((a, b) => b.rarity - a.rarity || b.level - a.level || a.name.localeCompare(b.name));

  const pills = chars.map(c => `
    <div class="abyss-pool-char${usedIn[c.name] != null ? ' used' : ''}" draggable="true" data-name="${c.name}" data-element="${c.element}">
      <img src="${c.icon}" alt="${c.name}" class="mini-icon ${c.rarity === 5 ? 'r5' : 'r4'}" onerror="this.style.display='none'">
      <span class="mini-name">${c.name}</span>
      ${usedIn[c.name] != null ? `<span class="abyss-used-badge">${usedIn[c.name] === 0 ? '1st' : '2nd'}</span>` : ''}
    </div>`).join('');

  return `
    <section class="priority-section abyss-pool-section">
      <div class="priority-section-head">your roster · drag into a slot, or click to add to the ${HALF_NAMES[abyssActiveHalf]}</div>
      <div class="abyss-pool-controls">
        <div class="element-filters">${filters}</div>
        <div class="search-group"><input id="abyss-search" type="text" placeholder="search..." spellcheck="false" value="${abyssPoolSearch.replace(/"/g, '&quot;')}"></div>
      </div>
      <div class="abyss-pool">${pills || '<p class="empty-hint">no matches</p>'}</div>
    </section>`;
}

function wireAbyssPull() {
  const btn = document.getElementById('abyss-pull');
  if (!btn) return;
  btn.onclick = async () => {
    btn.disabled = true;
    btn.textContent = 'pulling…';
    try {
      const got = await pullAbyssFromWiki();
      abyssPullMsg = `pulled ${got.map(c => `v${c.version}`).join(' + ')} from the genshin wiki just now`;
    } catch (e) {
      abyssPullMsg = `wiki pull failed: ${e.message}`;
    }
    renderAbyssTab();
  };
}

function wireAbyssTab(cycle, halves) {
  const container = document.getElementById('tab-abyss');
  const commit = () => { setAbyssPlan(cycle.id, halves); renderAbyssTab(); };
  wireAbyssPull();

  container.querySelectorAll('.abyss-cycle-btn').forEach(btn => {
    btn.onclick = () => { abyssCycleId = btn.dataset.cycle; renderAbyssTab(); };
  });
  container.querySelectorAll('.abyss-half').forEach(sec => {
    sec.onclick = e => {
      if (e.target.closest('button, .abyss-slot:not(.empty)')) return;
      abyssActiveHalf = +sec.dataset.half;
      renderAbyssTab();
    };
  });
  container.querySelectorAll('.abyss-slot-remove').forEach(btn => {
    btn.onclick = () => { halves[+btn.dataset.half][+btn.dataset.slot] = null; commit(); };
  });
  container.querySelectorAll('.abyss-clear-btn').forEach(btn => {
    btn.onclick = () => { halves[+btn.dataset.half] = [null, null, null, null]; commit(); };
  });
  container.querySelectorAll('.abyss-use-btn').forEach(btn => {
    btn.onclick = () => {
      const h = +btn.dataset.half;
      const { picked } = abyssSuggestions(h, halves)[+btn.dataset.sugg];
      halves[h] = [null, null, null, null];
      picked.forEach((n, i) => { if (n) placeInHalf(halves, n, h, i); });
      commit();
    };
  });
  container.querySelectorAll('.abyss-pool-filter').forEach(btn => {
    btn.onclick = () => { abyssPoolElement = btn.dataset.element; renderAbyssTab(); };
  });
  const search = container.querySelector('#abyss-search');
  if (search) search.oninput = e => {
    abyssPoolSearch = e.target.value.toLowerCase();
    renderAbyssTab();
    const el = document.getElementById('abyss-search');
    el.focus();
    el.setSelectionRange(el.value.length, el.value.length);
  };

  // Click-to-add: fills the first empty slot of the active half.
  container.querySelectorAll('.abyss-pool-char').forEach(el => {
    el.onclick = () => {
      const slot = halves[abyssActiveHalf].indexOf(null);
      if (slot === -1) return;
      placeInHalf(halves, el.dataset.name, abyssActiveHalf, slot);
      commit();
    };
  });

  // Drag and drop: pool → slot, slot → slot (swaps), slot → pool (removes).
  container.querySelectorAll('[draggable="true"]').forEach(el => {
    el.ondragstart = e => {
      const from = el.classList.contains('abyss-slot') ? { half: +el.dataset.half, slot: +el.dataset.slot } : null;
      e.dataTransfer.setData('text/plain', JSON.stringify({ name: el.dataset.name, from }));
      e.dataTransfer.effectAllowed = 'move';
    };
  });
  const readDrag = e => { try { return JSON.parse(e.dataTransfer.getData('text/plain')); } catch { return null; } };

  container.querySelectorAll('.abyss-slot').forEach(slotEl => {
    slotEl.ondragover = e => { e.preventDefault(); slotEl.classList.add('drag-over'); };
    slotEl.ondragleave = () => slotEl.classList.remove('drag-over');
    slotEl.ondrop = e => {
      e.preventDefault();
      const drag = readDrag(e);
      if (!drag) return;
      const h = +slotEl.dataset.half, s = +slotEl.dataset.slot;
      if (drag.from) {
        const displaced = halves[h][s];
        halves[h][s] = drag.name;
        halves[drag.from.half][drag.from.slot] = displaced;
      } else {
        placeInHalf(halves, drag.name, h, s);
      }
      commit();
    };
  });
  const pool = container.querySelector('.abyss-pool');
  if (pool) {
    pool.ondragover = e => e.preventDefault();
    pool.ondrop = e => {
      e.preventDefault();
      const drag = readDrag(e);
      if (drag?.from) { halves[drag.from.half][drag.from.slot] = null; commit(); }
    };
  }
}

// ── PRIORITY TAB ──

function nextFarmDay(name) {
  const today = new Date().getDay();
  const domain = CHAR_DOMAIN[name];
  if (!domain) return null;
  if (today === 0 || domain.days.includes(today)) return 'today';
  for (let offset = 1; offset <= 6; offset++) {
    const d = (today + offset) % 7;
    if (d === 0 || domain.days.includes(d)) return d === 0 ? 'sunday' : DAY_NAMES[d];
  }
  return null;
}

function charMiniPill(name, char) {
  const rc = char ? (char.rarity === 5 ? 'r5' : 'r4') : '';
  const icon = char
    ? `<img src="${char.icon}" alt="${name}" class="mini-icon ${rc}" onerror="this.style.display='none'">`
    : '';
  return `<div class="char-mini">${icon}<span class="mini-name">${name}</span></div>`;
}

function renderTodaySection(day, priority) {
  const isSunday = day === 0;
  const dayName = DAY_NAMES[day];
  const priorityNames = new Set(Object.keys(priority));

  if (priorityNames.size === 0) {
    return `
      <section class="priority-section">
        <div class="priority-section-head">today · ${dayName}${isSunday ? ' · all domains open' : ''}</div>
        <p class="empty-hint">add characters to your queue below to see what to farm</p>
      </section>`;
  }

  const openWithPriority = DOMAINS.flatMap(d =>
    d.slots
      .filter(s => isSunday || s.days.includes(day))
      .map(s => ({ domain: d.name, book: s.book, chars: s.chars.filter(c => priorityNames.has(c)) }))
      .filter(s => s.chars.length > 0)
  );

  if (openWithPriority.length === 0) {
    return `
      <section class="priority-section">
        <div class="priority-section-head">today · ${dayName}</div>
        <p class="empty-hint">nothing to farm today — save your resin for tomorrow</p>
      </section>`;
  }

  const rows = openWithPriority.map(slot => `
    <div class="domain-row">
      <div class="domain-label">
        <div class="domain-name">${slot.domain}</div>
        <div class="domain-book">book of ${slot.book.toLowerCase()}</div>
      </div>
      <div class="domain-chars">
        ${slot.chars.map(n => charMiniPill(n, allChars.find(c => c.name === n))).join('')}
      </div>
    </div>`).join('');

  return `
    <section class="priority-section">
      <div class="priority-section-head">today · ${dayName}${isSunday ? ' · all domains open' : ''}</div>
      <div class="domain-list">${rows}</div>
    </section>`;
}

function renderQueueSection(priority) {
  const names = Object.keys(priority);

  if (names.length === 0) {
    return `
      <section class="priority-section">
        <div class="priority-section-head">priority queue</div>
        <p class="empty-hint">go to the roster tab and click ★ on characters you're leveling</p>
      </section>`;
  }

  const cards = names.map(name => {
    const char = allChars.find(c => c.name === name);
    const prio = priority[name];
    const rc = char ? (char.rarity === 5 ? 'r5' : 'r4') : '';
    const icon = char
      ? `<img src="${char.icon}" alt="${name}" class="prio-icon ${rc}" onerror="this.style.display='none'">`
      : `<div class="prio-icon-placeholder"></div>`;
    const levelDisplay = char ? `lv ${char.level}${char.max_level != null ? `/${char.max_level}` : ''}` : '';
    const domain = CHAR_DOMAIN[name];
    const domainInfo = domain ? `${domain.domain} · ${domain.book}` : '—';
    const targetOpts = TARGET_LEVELS
      .map(l => `<option value="${l}"${l === prio.targetLevel ? ' selected' : ''}>${l}</option>`)
      .join('');
    return `
      <div class="prio-card">
        ${icon}
        <div class="prio-info">
          <div class="prio-name">${name}</div>
          ${levelDisplay ? `<div class="prio-level">${levelDisplay}</div>` : ''}
          <div class="prio-domain">${domainInfo}</div>
          ${nextFarmDay(name) ? `<div class="prio-next${nextFarmDay(name) === 'today' ? ' is-today' : ''}">farm ${nextFarmDay(name)}</div>` : ''}
        </div>
        <div class="prio-controls">
          <label class="target-label">target
            <select class="target-select" data-name="${name}">${targetOpts}</select>
          </label>
          <button class="remove-priority" data-name="${name}" title="remove from queue">×</button>
        </div>
      </div>`;
  }).join('');

  return `
    <section class="priority-section">
      <div class="priority-section-head">priority queue</div>
      <div class="prio-queue">${cards}</div>
    </section>`;
}

function renderWeekSection(priority) {
  const priorityNames = new Set(Object.keys(priority));
  if (priorityNames.size === 0) return '';

  const DAY_PAIRS = [
    { key: 1, label: 'mon · thu' },
    { key: 2, label: 'tue · fri' },
    { key: 3, label: 'wed · sat' },
  ];

  const rows = DAY_PAIRS.map(pair => {
    const slots = DOMAINS.flatMap(d =>
      d.slots
        .filter(s => s.days.includes(pair.key))
        .map(s => ({ book: s.book, chars: s.chars.filter(c => priorityNames.has(c)) }))
        .filter(s => s.chars.length > 0)
    );
    return { label: pair.label, slots };
  }).filter(row => row.slots.length > 0);

  if (rows.length === 0) return '';

  const html = rows.map(pair => `
    <div class="week-pair">
      <div class="week-day-label">${pair.label}</div>
      <div class="week-slots">
        ${pair.slots.map(slot => `
          <div class="week-slot">
            <div class="week-book">book of ${slot.book.toLowerCase()}</div>
            <div class="week-chars">${slot.chars.map(n => charMiniPill(n, allChars.find(c => c.name === n))).join('')}</div>
          </div>`).join('')}
      </div>
    </div>`).join('');

  return `
    <section class="priority-section">
      <div class="priority-section-head">week ahead</div>
      <div class="week-grid">${html}</div>
    </section>`;
}

function renderPriorityTab() {
  const priority = loadPriority();
  const today = new Date().getDay();
  const container = document.getElementById('tab-priority');
  const updatedNote = `<p class="setup-note teams-updated">domain schedule last checked: ${DATA_VERSION}</p>`;
  container.innerHTML = updatedNote + renderTodaySection(today, priority) + renderWeekSection(priority) + renderQueueSection(priority);
  container.querySelectorAll('.target-select').forEach(sel => {
    sel.onchange = () => setPriorityTarget(sel.dataset.name, sel.value);
  });
  container.querySelectorAll('.remove-priority').forEach(btn => {
    btn.onclick = () => togglePriority(btn.dataset.name);
  });
}

init();
