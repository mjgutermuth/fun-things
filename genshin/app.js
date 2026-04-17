const CACHE_TTL = 5 * 60 * 1000;
const ELEMENTS = ['Pyro','Hydro','Anemo','Electro','Dendro','Cryo','Geo'];
const ELEMENT_MAP = {
  Fire: 'Pyro', Water: 'Hydro', Wind: 'Anemo',
  Electric: 'Electro', Grass: 'Dendro', Ice: 'Cryo', Rock: 'Geo',
};
const DAY_NAMES = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday'];
const TARGET_LEVELS = [20, 40, 50, 60, 70, 80, 90];

// Talent book domains — days: 1=Mon,4=Thu | 2=Tue,5=Fri | 3=Wed,6=Sat | 0=Sun(all)
const DOMAINS = [
  {
    name: 'Forsaken Rift', region: 'Mondstadt',
    slots: [
      { days: [1,4], book: 'Freedom',    chars: ['Amber','Kaeya','Lisa','Razor','Fischl','Mika'] },
      { days: [2,5], book: 'Resistance', chars: ['Barbara','Noelle','Jean','Sucrose','Bennett','Diluc'] },
      { days: [3,6], book: 'Ballad',     chars: ['Venti','Klee','Albedo','Mona','Rosaria','Eula','Kazuha','Durin'] },
    ],
  },
  {
    name: 'Taishan Mansion', region: 'Liyue',
    slots: [
      { days: [1,4], book: 'Prosperity', chars: ['Xiangling','Chongyun','Beidou','Ningguang','Keqing','Qiqi','Xinyan','Yun Jin','Gaming'] },
      { days: [2,5], book: 'Diligence',  chars: ['Xiao','Ganyu','Hu Tao','Yanfei','Shenhe','Yelan','Baizhu'] },
      { days: [3,6], book: 'Gold',       chars: ['Xingqiu','Zhongli','Xianyun','Zibai'] },
    ],
  },
  {
    name: 'Violet Court', region: 'Inazuma',
    slots: [
      { days: [1,4], book: 'Transience', chars: ['Kamisato Ayaka','Yoimiya','Thoma','Sayu','Gorou'] },
      { days: [2,5], book: 'Elegance',   chars: ['Kokomi','Yae Miko','Kujou Sara','Kuki Shinobu','Kirara'] },
      { days: [3,6], book: 'Light',      chars: ['Raiden Shogun','Itto','Wanderer','Heizou'] },
    ],
  },
  {
    name: 'Steeple of Ignorance', region: 'Sumeru',
    slots: [
      { days: [1,4], book: 'Admonition', chars: ['Collei','Tighnari','Cyno','Dori'] },
      { days: [2,5], book: 'Ingenuity',  chars: ['Nahida','Layla','Sethos','Nilou'] },
      { days: [3,6], book: 'Praxis',     chars: ['Alhaitham','Kaveh','Faruzan','Dehya'] },
    ],
  },
  {
    name: 'Pale Forgotten Glory', region: 'Fontaine',
    slots: [
      { days: [1,4], book: 'Equity',   chars: ['Lynette','Charlotte','Freminet'] },
      { days: [2,5], book: 'Justice',  chars: ['Lyney','Furina','Clorinde','Sigewinne','Navia'] },
      { days: [3,6], book: 'Order',    chars: ['Neuvillette','Wriothesley','Chevreuse','Emilie','Escoffier'] },
    ],
  },
  {
    name: 'Lightless Capital', region: 'Nod-Krai',
    slots: [
      { days: [1,4], book: 'Moonlight', chars: ['Lauma','Columbina'] },
      { days: [2,5], book: 'Elysium',   chars: ['Nefer','Aino','Illuga'] },
      { days: [3,6], book: 'Vagrancy',  chars: ['Jahoda','Flins','Linnea'] },
    ],
  },
  {
    name: 'Blazing Ruins', region: 'Natlan',
    slots: [
      { days: [1,4], book: 'Conflict',   chars: ['Xilonen','Chasca','Ifa'] },
      { days: [2,5], book: 'Kindling',   chars: ['Mualani','Kinich','Lan Yan'] },
      { days: [3,6], book: 'Contention', chars: ['Citlali','Mavuika','Ororon','Varesa'] },
    ],
  },
];

const CHAR_DOMAIN = Object.fromEntries(
  DOMAINS.flatMap(d => d.slots.flatMap(s => s.chars.map(c => [c, { domain: d.name, book: s.book, days: s.days }])))
);

const TEAM_ARCHETYPES = [
  {
    name: 'Neuvillette Hypercarry', tags: ['Hydro'],
    notes: 'Furina dramatically boosts damage via HP fluctuation. Anemo for resistance shred.',
    roles: [
      { label: 'DPS',    chars: ['Neuvillette'] },
      { label: 'Archon', chars: ['Furina'] },
      { label: 'Anemo',  chars: ['Kazuha','Venti','Sucrose'] },
      { label: 'Flex',   chars: ['Zhongli','Charlotte','Layla','Nahida','Fischl'] },
    ],
  },
  {
    name: 'Hu Tao Double Hydro', tags: ['Vaporize'],
    notes: 'Run both Xingqiu and Yelan for consistent Vaporize. Zhongli shields protect Hu Tao.',
    roles: [
      { label: 'DPS',     chars: ['Hu Tao'] },
      { label: 'Hydro 1', chars: ['Yelan','Xingqiu'] },
      { label: 'Hydro 2', chars: ['Xingqiu','Yelan'] },
      { label: 'Support', chars: ['Zhongli','Layla','Albedo'] },
    ],
  },
  {
    name: 'Raiden National', tags: ['Overloaded'],
    notes: 'Raiden recharges everyone\'s bursts. Reliable all-content team.',
    roles: [
      { label: 'Electro', chars: ['Raiden Shogun'] },
      { label: 'Pyro',    chars: ['Xiangling'] },
      { label: 'Hydro',   chars: ['Xingqiu','Yelan'] },
      { label: 'Buffer',  chars: ['Bennett'] },
    ],
  },
  {
    name: 'Ayaka Freeze', tags: ['Freeze'],
    notes: 'Freeze keeps enemies locked. Venti/Kazuha group and shred resistance.',
    roles: [
      { label: 'DPS',   chars: ['Kamisato Ayaka'] },
      { label: 'Hydro', chars: ['Kokomi','Mona','Barbara'] },
      { label: 'Cryo',  chars: ['Shenhe','Rosaria','Diona'] },
      { label: 'Anemo', chars: ['Kazuha','Venti'] },
    ],
  },
  {
    name: 'Ganyu Freeze', tags: ['Freeze'],
    notes: 'Long-range AoE Cryo with Venti for mass grouping. Very consistent against hordes.',
    roles: [
      { label: 'DPS',   chars: ['Ganyu'] },
      { label: 'Hydro', chars: ['Kokomi','Mona','Barbara'] },
      { label: 'Anemo', chars: ['Venti','Kazuha'] },
      { label: 'Cryo',  chars: ['Shenhe','Diona','Rosaria'] },
    ],
  },
  {
    name: 'Hyperbloom', tags: ['Hyperbloom'],
    notes: 'Electro-triggered Dendro seeds deal huge AoE damage. Kokomi for field Hydro.',
    roles: [
      { label: 'Dendro',  chars: ['Nahida','Collei','Kirara','Yaoyao'] },
      { label: 'Hydro',   chars: ['Kokomi','Yelan','Xingqiu','Barbara','Furina'] },
      { label: 'Electro', chars: ['Raiden Shogun','Fischl','Kuki Shinobu','Beidou'] },
      { label: 'Flex',    chars: ['Kazuha','Zhongli','Nahida','Baizhu'] },
    ],
  },
  {
    name: 'Nilou Bloom', tags: ['Bloom'],
    notes: 'Full Hydro+Dendro only — no other elements. Nilou boosts Bloom damage significantly.',
    roles: [
      { label: 'Core',   chars: ['Nilou'] },
      { label: 'Dendro', chars: ['Nahida','Baizhu','Yaoyao'] },
      { label: 'Healer', chars: ['Kokomi','Baizhu','Barbara'] },
      { label: 'Dendro', chars: ['Collei','Nahida','Kirara'] },
    ],
  },
  {
    name: 'Wanderer Hypercarry', tags: ['Anemo'],
    notes: 'Faruzan is essentially required. Furina or Bennett provide big multipliers.',
    roles: [
      { label: 'DPS',     chars: ['Wanderer'] },
      { label: 'Buffer',  chars: ['Faruzan'] },
      { label: 'Support', chars: ['Furina','Bennett','Zhongli','Layla'] },
      { label: 'Flex',    chars: ['Zhongli','Layla','Fischl','Nahida'] },
    ],
  },
  {
    name: 'Xiao Hypercarry', tags: ['Anemo', 'Plunge'],
    notes: 'Xianyun enables buffed plunge attacks. Faruzan shreds Anemo resistance.',
    roles: [
      { label: 'DPS',     chars: ['Xiao'] },
      { label: 'Buffer',  chars: ['Faruzan'] },
      { label: 'Jump',    chars: ['Xianyun','Jean'] },
      { label: 'Support', chars: ['Furina','Bennett','Zhongli','Layla'] },
    ],
  },
  {
    name: 'Itto Mono Geo', tags: ['Geo'],
    notes: 'Gorou is essential for Itto — triple Geo unlocks all Gorou buffs.',
    roles: [
      { label: 'DPS',      chars: ['Arataki Itto'] },
      { label: 'Buffer',   chars: ['Gorou'] },
      { label: 'Geo 3rd',  chars: ['Albedo','Zhongli','Ningguang'] },
      { label: 'Flex Geo', chars: ['Zhongli','Albedo','Ningguang'] },
    ],
  },
  {
    name: 'Yae Miko Aggravate', tags: ['Aggravate'],
    notes: 'Nahida applies Dendro off-field; Kazuha boosts Electro DMG bonus.',
    roles: [
      { label: 'DPS',     chars: ['Yae Miko'] },
      { label: 'Electro', chars: ['Fischl','Raiden Shogun','Beidou'] },
      { label: 'Dendro',  chars: ['Nahida','Collei'] },
      { label: 'Anemo',   chars: ['Kazuha','Sucrose'] },
    ],
  },
  {
    name: 'Clorinde Aggravate', tags: ['Aggravate'],
    notes: 'High single-target Electro DPS; Kazuha amplifies and groups.',
    roles: [
      { label: 'DPS',     chars: ['Clorinde'] },
      { label: 'Electro', chars: ['Fischl','Raiden Shogun'] },
      { label: 'Dendro',  chars: ['Nahida','Collei'] },
      { label: 'Anemo',   chars: ['Kazuha','Sucrose'] },
    ],
  },
  {
    name: 'Cyno Aggravate', tags: ['Aggravate'],
    notes: 'Long burst window; Nahida keeps Dendro applied throughout Cyno\'s field time.',
    roles: [
      { label: 'DPS',     chars: ['Cyno'] },
      { label: 'Dendro',  chars: ['Nahida'] },
      { label: 'Electro', chars: ['Fischl','Beidou','Raiden Shogun'] },
      { label: 'Support', chars: ['Zhongli','Kazuha','Baizhu'] },
    ],
  },
  {
    name: 'Lyney Vaporize', tags: ['Pyro', 'Vaporize'],
    notes: 'Furina and Bennett amplify charged attack damage. Xiangling for off-field Pyro.',
    roles: [
      { label: 'DPS',    chars: ['Lyney'] },
      { label: 'Buffer', chars: ['Bennett'] },
      { label: 'Archon', chars: ['Furina'] },
      { label: 'Pyro',   chars: ['Xiangling','Chevreuse','Kazuha'] },
    ],
  },
  {
    name: 'Navia Geo', tags: ['Geo'],
    notes: 'Fischl generates Crystalize off-field; Zhongli shreds and shields.',
    roles: [
      { label: 'DPS',     chars: ['Navia'] },
      { label: 'Geo',     chars: ['Zhongli','Albedo'] },
      { label: 'Electro', chars: ['Fischl','Beidou'] },
      { label: 'Flex',    chars: ['Furina','Kazuha','Bennett'] },
    ],
  },
  {
    name: 'Wriothesley Freeze', tags: ['Freeze'],
    notes: 'Furina synergizes with Wriothesley\'s low-HP mechanic for big multipliers.',
    roles: [
      { label: 'DPS',   chars: ['Wriothesley'] },
      { label: 'Hydro', chars: ['Furina','Kokomi'] },
      { label: 'Cryo',  chars: ['Shenhe','Rosaria','Diona'] },
      { label: 'Anemo', chars: ['Kazuha','Venti'] },
    ],
  },
  {
    name: 'Mavuika Natlan', tags: ['Pyro', 'Natlan'],
    notes: 'Citlali provides Cryo shred. Xilonen gives Pyro RES shred and healing.',
    roles: [
      { label: 'DPS',    chars: ['Mavuika'] },
      { label: 'Cryo',   chars: ['Citlali'] },
      { label: 'Natlan', chars: ['Xilonen','Chasca','Kinich','Mualani','Ifa'] },
      { label: 'Flex',   chars: ['Bennett','Kazuha','Furina','Zhongli'] },
    ],
  },
  {
    name: 'Mualani Vaporize', tags: ['Hydro', 'Vaporize'],
    notes: 'Furina dramatically boosts Mualani\'s shark bite damage.',
    roles: [
      { label: 'DPS',    chars: ['Mualani'] },
      { label: 'Archon', chars: ['Furina'] },
      { label: 'Pyro',   chars: ['Bennett','Xiangling'] },
      { label: 'Anemo',  chars: ['Kazuha','Venti','Sucrose'] },
    ],
  },
  {
    name: 'Kinich Dendro', tags: ['Dendro', 'Natlan'],
    notes: 'Nahida enables consistent Dendro reactions. Furina boosts off-field scaling.',
    roles: [
      { label: 'DPS',    chars: ['Kinich'] },
      { label: 'Dendro', chars: ['Nahida','Collei'] },
      { label: 'Support',chars: ['Furina','Zhongli'] },
      { label: 'Flex',   chars: ['Bennett','Kazuha','Xilonen'] },
    ],
  },
  {
    name: 'Nefer Lunar Bloom', tags: ['Lunar Bloom', 'Dendro'],
    notes: 'Lauma converts Bloom cores into Lunar Cores; Columbina amplifies all Lunar Reactions. Nilou triggers immediate detonation.',
    roles: [
      { label: 'DPS',    chars: ['Nefer'] },
      { label: 'Buffer', chars: ['Lauma'] },
      { label: 'Hydro',  chars: ['Columbina','Nilou','Kokomi','Aino'] },
      { label: 'Flex',   chars: ['Nilou','Nahida','Sucrose','Kokomi'] },
    ],
  },
  {
    name: 'Bennett Xiangling Core', tags: ['Vaporize', 'Pyro'],
    notes: 'Flexible core that slots into dozens of teams. Run with any Hydro carry.',
    roles: [
      { label: 'Buffer',   chars: ['Bennett'] },
      { label: 'Sub DPS',  chars: ['Xiangling'] },
      { label: 'Hydro',    chars: ['Xingqiu','Yelan'] },
      { label: 'Flex DPS', chars: ['Raiden Shogun','Eula','Beidou','Fischl','Clorinde'] },
    ],
  },
];

let allChars = [];
let activeElement = 'all';
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

  priorityEl.classList.add('hidden');
  teamsEl.classList.add('hidden');

  if (tab === 'priority') { priorityEl.classList.remove('hidden'); renderPriorityTab(); }
  if (tab === 'teams')    { teamsEl.classList.remove('hidden');    renderTeamsTab(); }
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
  if (config.ltmid_v2)  document.getElementById('cfg-ltmid').value  = config.ltmid_v2;
  if (config.uid)       document.getElementById('cfg-uid').value    = config.uid;

  document.getElementById('setup-save').onclick = () => {
    const cfg = {
      workerUrl: document.getElementById('cfg-worker').value.trim().replace(/\/$/, ''),
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
    document.getElementById('loading').classList.add('hidden');
    setFooter(config.uid, allChars.length, false);
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
      <span class="row-level">${char.level != null ? `${char.level}/${char.max_level}` : '—'}</span>
      <span class="row-weapon">${w ? w.name : '—'}</span>
      <span class="row-const">C${char.constellation}</span>
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

function renderTeamsTab() {
  const charNames = new Set(allChars.map(c => c.name));
  const scored = TEAM_ARCHETYPES
    .map(t => ({ ...t, score: t.roles.filter(r => r.chars.some(c => charNames.has(c))).length }))
    .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));

  document.getElementById('tab-teams').innerHTML = scored.map(t => teamCard(t, charNames)).join('');
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
        <span class="team-tags">${team.tags.map(t => `<span class="team-tag">${t}</span>`).join('')}</span>
        <span class="team-status ${statusClass}">${statusLabel}</span>
      </div>
      ${team.notes ? `<p class="team-notes">${team.notes}</p>` : ''}
      <div class="team-roles">${rolesHtml}</div>
    </div>`;
}

// ── PRIORITY TAB ──

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
    const levelDisplay = char ? `lv ${char.level}/${char.max_level}` : '';
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

function renderPriorityTab() {
  const priority = loadPriority();
  const today = new Date().getDay();
  const container = document.getElementById('tab-priority');
  container.innerHTML = renderTodaySection(today, priority) + renderQueueSection(priority);
  container.querySelectorAll('.target-select').forEach(sel => {
    sel.onchange = () => setPriorityTarget(sel.dataset.name, sel.value);
  });
  container.querySelectorAll('.remove-priority').forEach(btn => {
    btn.onclick = () => togglePriority(btn.dataset.name);
  });
}

init();
