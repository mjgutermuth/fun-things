// Spiral Abyss Floor 12 — one entry per cycle. Abyss resets on the 16th (4am server time).
// Add the next cycle when its blessing + disorders are announced; leave fields null until then.
// `tags` match TEAMS_DATA tags/elements and drive the planner's team suggestions.
const ABYSS_CYCLES = [
  {
    id: '2026-10-16', start: '2026-10-16', reset: '2026-11-16', version: '7.1',
    blessing: {
      name: 'Stardread Moon',
      effect: 'Triggering Superconduct, Stellar-Conduct, Cryo Swirl, Stellar-Swirl, Frozen, or Shatter, or dealing Stellar-Conduct or Stellar-Swirl DMG, unleashes a True DMG shockwave. Once every 2s.',
    },
    halves: [
      {
        disorder: 'Stellar Glimmer DMG +75%',
        tags: ['Stellar-Conduct', 'Stellar-Swirl', 'Cryo'],
        tip: 'Stellar reactions get the disorder bonus. Keep Cryo application steady.',
      },
      {
        disorder: 'All party members gain 75% Cryo DMG Bonus',
        tags: ['Freeze', 'Cryo'],
        tip: 'Cryo carries. Bring Hydro to break the Baptist\'s Pyro shield.',
      },
    ],
    chambers: [
      { level: 95,  first: [['Battle-Hardened Chimeric Volkodlak Archer']], second: [['Iniquitous Baptist'], ['Shadowy Husk: Standard Bearer', 'Shadowy Husk: Defender']] },
      { level: 98,  first: [['Radiant Moonfly']],                           second: [['Battle-Hardened Elite Treasure Hoarder']] },
      { level: 100, first: [['Chimeric Winged Lion']],                      second: [['Secret Source Automaton: Overseer Device']] },
    ],
  },
  {
    id: '2026-11-16', start: '2026-11-16', reset: '2026-12-16', version: '7.2',
    blessing: null, // not announced yet
    halves: [
      { disorder: null, tags: [], tip: null },
      { disorder: null, tags: [], tip: null },
    ],
    chambers: [
      { level: 95,  first: [['Battle-Hardened Prism Slime']], second: [['Wavebinder']] },
      { level: 98,  first: [['Frostnight Herra']],            second: [['Guardian Blade of Drifting Snow']] },
      { level: 100, first: [['Radiant Moongecko']],           second: [['Perpetual Mechanical Array']] },
    ],
  },
];
