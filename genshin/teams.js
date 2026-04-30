const TEAMS_DATA = [
  // --- Tier 0 ---
  {
    "name": "Mavuika Natlan", "tier": 0, "tags": ["Pyro", "Natlan"],
    "notes": "Citlali provides Cryo shred. Xilonen gives Pyro RES shred and healing.",
    "roles": [
      { "label": "DPS",    "chars": ["Mavuika"] },
      { "label": "Cryo",   "chars": ["Citlali"] },
      { "label": "Natlan", "chars": ["Xilonen", "Chasca", "Kinich", "Mualani", "Ifa"] },
      { "label": "Flex",   "chars": ["Bennett", "Kazuha", "Furina", "Zhongli"] }
    ]
  },
  {
    "name": "Nefer Lunar Bloom", "tier": 0, "tags": ["Lunar Bloom", "Dendro"],
    "notes": "Lauma converts Bloom cores into Lunar Cores; Columbina amplifies all Lunar Reactions. Nilou triggers immediate detonation.",
    "roles": [
      { "label": "DPS",    "chars": ["Nefer"] },
      { "label": "Buffer", "chars": ["Lauma"] },
      { "label": "Hydro",  "chars": ["Columbina", "Nilou", "Kokomi", "Aino"] },
      { "label": "Flex",   "chars": ["Nilou", "Nahida", "Sucrose", "Kokomi"] }
    ]
  },
  // --- Tier 1 ---
  {
    "name": "Neuvillette Hypercarry", "tier": 1, "tags": ["Hydro"],
    "notes": "Furina dramatically boosts damage via HP fluctuation. Anemo for resistance shred.",
    "roles": [
      { "label": "DPS",    "chars": ["Neuvillette"] },
      { "label": "Archon", "chars": ["Furina"] },
      { "label": "Anemo",  "chars": ["Kazuha", "Venti", "Sucrose"] },
      { "label": "Flex",   "chars": ["Zhongli", "Charlotte", "Layla", "Nahida", "Fischl"] }
    ]
  },
  {
    "name": "Skirk Freeze", "tier": 1, "tags": ["Freeze"],
    "notes": "Current top Freeze team. Escoffier provides Cryo application and strong buffs. Furina can't be used in Lunar comps so she's a natural fit here alongside Skirk.",
    "roles": [
      { "label": "DPS",   "chars": ["Skirk"] },
      { "label": "Cryo",  "chars": ["Escoffier"] },
      { "label": "Hydro", "chars": ["Furina", "Neuvillette", "Kokomi"] },
      { "label": "Anemo", "chars": ["Kazuha", "Venti"] }
    ]
  },
  {
    "name": "Hu Tao Double Hydro", "tier": 1, "tags": ["Vaporize"],
    "notes": "Run both Xingqiu and Yelan for consistent Vaporize. Zhongli shields protect Hu Tao.",
    "roles": [
      { "label": "DPS",     "chars": ["Hu Tao"] },
      { "label": "Hydro 1", "chars": ["Yelan", "Xingqiu"] },
      { "label": "Hydro 2", "chars": ["Xingqiu", "Yelan"] },
      { "label": "Support", "chars": ["Zhongli", "Layla", "Albedo"] }
    ]
  },
  {
    "name": "Hyperbloom", "tier": 1, "tags": ["Hyperbloom"],
    "notes": "Electro-triggered Dendro seeds deal huge AoE damage. Kokomi for field Hydro.",
    "roles": [
      { "label": "Dendro",  "chars": ["Nahida", "Collei", "Kirara", "Yaoyao"] },
      { "label": "Hydro",   "chars": ["Kokomi", "Yelan", "Xingqiu", "Barbara", "Furina"] },
      { "label": "Electro", "chars": ["Raiden Shogun", "Fischl", "Kuki Shinobu", "Beidou"] },
      { "label": "Flex",    "chars": ["Kazuha", "Zhongli", "Nahida", "Baizhu"] }
    ]
  },
  // --- Tier 2 ---
  {
    "name": "Yae Miko Aggravate", "tier": 2, "tags": ["Aggravate"],
    "notes": "Nahida applies Dendro off-field; Kazuha boosts Electro DMG bonus.",
    "roles": [
      { "label": "DPS",     "chars": ["Yae Miko"] },
      { "label": "Electro", "chars": ["Fischl", "Raiden Shogun", "Beidou"] },
      { "label": "Dendro",  "chars": ["Nahida", "Collei"] },
      { "label": "Anemo",   "chars": ["Kazuha", "Sucrose"] }
    ]
  },
  {
    "name": "Clorinde Aggravate", "tier": 2, "tags": ["Aggravate"],
    "notes": "High single-target Electro DPS; Kazuha amplifies and groups.",
    "roles": [
      { "label": "DPS",     "chars": ["Clorinde"] },
      { "label": "Electro", "chars": ["Fischl", "Raiden Shogun"] },
      { "label": "Dendro",  "chars": ["Nahida", "Collei"] },
      { "label": "Anemo",   "chars": ["Kazuha", "Sucrose"] }
    ]
  },
  {
    "name": "Mualani Vaporize", "tier": 2, "tags": ["Hydro", "Vaporize"],
    "notes": "Furina dramatically boosts Mualani's shark bite damage.",
    "roles": [
      { "label": "DPS",    "chars": ["Mualani"] },
      { "label": "Archon", "chars": ["Furina"] },
      { "label": "Pyro",   "chars": ["Bennett", "Xiangling"] },
      { "label": "Anemo",  "chars": ["Kazuha", "Venti", "Sucrose"] }
    ]
  },
  {
    "name": "Kinich Dendro", "tier": 2, "tags": ["Dendro", "Natlan"],
    "notes": "Nahida enables consistent Dendro reactions. Xilonen is near-required — provides Pyro/Dendro RES shred and healing. Furina boosts off-field scaling.",
    "roles": [
      { "label": "DPS",     "chars": ["Kinich"] },
      { "label": "Dendro",  "chars": ["Nahida", "Collei"] },
      { "label": "Support", "chars": ["Xilonen"] },
      { "label": "Flex",    "chars": ["Furina", "Bennett", "Kazuha", "Zhongli"] }
    ]
  },
  {
    "name": "Xiao Hypercarry", "tier": 2, "tags": ["Anemo", "Plunge"],
    "notes": "Xianyun enables buffed plunge attacks. Faruzan shreds Anemo resistance.",
    "roles": [
      { "label": "DPS",     "chars": ["Xiao"] },
      { "label": "Buffer",  "chars": ["Faruzan"] },
      { "label": "Jump",    "chars": ["Xianyun", "Jean"] },
      { "label": "Support", "chars": ["Furina", "Bennett", "Zhongli", "Layla"] }
    ]
  },
  {
    "name": "Wanderer Hypercarry", "tier": 2, "tags": ["Anemo"],
    "notes": "Faruzan is essentially required. Furina or Bennett provide big multipliers.",
    "roles": [
      { "label": "DPS",     "chars": ["Wanderer"] },
      { "label": "Buffer",  "chars": ["Faruzan"] },
      { "label": "Support", "chars": ["Furina", "Bennett", "Zhongli", "Layla"] },
      { "label": "Flex",    "chars": ["Zhongli", "Layla", "Fischl", "Nahida"] }
    ]
  },
  {
    "name": "Ayaka Freeze", "tier": 2, "tags": ["Freeze"],
    "notes": "Freeze keeps enemies locked. Venti/Kazuha group and shred resistance. Note: Skirk Freeze is now the premier Freeze team; Ayaka is a strong budget alternative.",
    "roles": [
      { "label": "DPS",   "chars": ["Kamisato Ayaka"] },
      { "label": "Hydro", "chars": ["Kokomi", "Mona", "Barbara"] },
      { "label": "Cryo",  "chars": ["Shenhe", "Rosaria", "Diona"] },
      { "label": "Anemo", "chars": ["Kazuha", "Venti"] }
    ]
  },
  // --- Solid / Niche ---
  {
    "name": "Wriothesley Freeze", "tier": 3, "tags": ["Freeze"],
    "notes": "Furina synergizes with Wriothesley's low-HP mechanic for big multipliers. Note: Skirk Freeze is now the top Freeze team; Wriothesley is a solid second option.",
    "roles": [
      { "label": "DPS",   "chars": ["Wriothesley"] },
      { "label": "Hydro", "chars": ["Furina", "Kokomi"] },
      { "label": "Cryo",  "chars": ["Shenhe", "Rosaria", "Diona"] },
      { "label": "Anemo", "chars": ["Kazuha", "Venti"] }
    ]
  },
  {
    "name": "Ganyu Freeze", "tier": 3, "tags": ["Freeze"],
    "notes": "Long-range AoE Cryo with Venti for mass grouping. Very consistent against hordes. Note: Skirk Freeze has overtaken this as the top Freeze comp.",
    "roles": [
      { "label": "DPS",   "chars": ["Ganyu"] },
      { "label": "Hydro", "chars": ["Kokomi", "Mona", "Barbara"] },
      { "label": "Anemo", "chars": ["Venti", "Kazuha"] },
      { "label": "Cryo",  "chars": ["Shenhe", "Diona", "Rosaria"] }
    ]
  },
  {
    "name": "Nilou Bloom", "tier": 3, "tags": ["Bloom"],
    "notes": "Full Hydro+Dendro only — no other elements. Nilou boosts Bloom damage significantly.",
    "roles": [
      { "label": "Core",   "chars": ["Nilou"] },
      { "label": "Dendro", "chars": ["Nahida", "Baizhu", "Yaoyao"] },
      { "label": "Healer", "chars": ["Kokomi", "Baizhu", "Barbara"] },
      { "label": "Dendro", "chars": ["Collei", "Nahida", "Kirara"] }
    ]
  },
  {
    "name": "Lyney Mono Pyro", "tier": 3, "tags": ["Pyro"],
    "notes": "Full Pyro team — Chevreuse buffs all Pyro members and shreds Pyro/Electro RES. Avoids off-element reactions that would dilute Lyney's charged attacks.",
    "roles": [
      { "label": "DPS",    "chars": ["Lyney"] },
      { "label": "Buffer", "chars": ["Bennett"] },
      { "label": "Pyro",   "chars": ["Chevreuse"] },
      { "label": "Pyro",   "chars": ["Xiangling", "Thoma", "Yanfei"] }
    ]
  },
  {
    "name": "Navia Geo", "tier": 3, "tags": ["Geo"],
    "notes": "Fischl generates Crystalize off-field; Zhongli shreds and shields.",
    "roles": [
      { "label": "DPS",     "chars": ["Navia"] },
      { "label": "Geo",     "chars": ["Zhongli", "Albedo"] },
      { "label": "Electro", "chars": ["Fischl", "Beidou"] },
      { "label": "Flex",    "chars": ["Furina", "Kazuha", "Bennett"] }
    ]
  },
  {
    "name": "Itto Mono Geo", "tier": 3, "tags": ["Geo"],
    "notes": "Gorou is essential for Itto — triple Geo unlocks all Gorou buffs.",
    "roles": [
      { "label": "DPS",      "chars": ["Arataki Itto"] },
      { "label": "Buffer",   "chars": ["Gorou"] },
      { "label": "Geo 3rd",  "chars": ["Albedo", "Zhongli", "Ningguang"] },
      { "label": "Flex Geo", "chars": ["Zhongli", "Albedo", "Ningguang"] }
    ]
  },
  {
    "name": "Cyno Aggravate", "tier": 3, "tags": ["Aggravate"],
    "notes": "Long burst window; Nahida keeps Dendro applied throughout Cyno's field time.",
    "roles": [
      { "label": "DPS",     "chars": ["Cyno"] },
      { "label": "Dendro",  "chars": ["Nahida"] },
      { "label": "Electro", "chars": ["Fischl", "Beidou", "Raiden Shogun"] },
      { "label": "Support", "chars": ["Zhongli", "Kazuha", "Baizhu"] }
    ]
  },
  {
    "name": "Raiden National", "tier": 3, "tags": ["Overloaded"],
    "notes": "Raiden recharges everyone's bursts. Reliable all-content team.",
    "roles": [
      { "label": "Electro", "chars": ["Raiden Shogun"] },
      { "label": "Pyro",    "chars": ["Xiangling"] },
      { "label": "Hydro",   "chars": ["Xingqiu", "Yelan"] },
      { "label": "Buffer",  "chars": ["Bennett"] }
    ]
  },
  // --- Utility Core ---
  {
    "name": "Bennett Xiangling Core", "tier": 4, "tags": ["Vaporize", "Pyro"],
    "notes": "Flexible core that slots into dozens of teams. Run with any Hydro carry.",
    "roles": [
      { "label": "Buffer",   "chars": ["Bennett"] },
      { "label": "Sub DPS",  "chars": ["Xiangling"] },
      { "label": "Hydro",    "chars": ["Xingqiu", "Yelan"] },
      { "label": "Flex DPS", "chars": ["Raiden Shogun", "Eula", "Beidou", "Fischl", "Clorinde"] }
    ]
  }
];
