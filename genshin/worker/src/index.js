// Pure-JS MD5 — no node:crypto dependency needed
function md5(str) {
  function add(x, y) {
    const l = (x & 0xffff) + (y & 0xffff);
    return ((x >>> 16) + (y >>> 16) + (l >>> 16)) << 16 | l & 0xffff;
  }
  function L(q, n) { return q << n | q >>> 32 - n; }
  function cmn(q, a, b, x, s, t) { return add(L(add(add(a, q), add(x, t)), s), b); }
  function ff(a, b, c, d, x, s, t) { return cmn(b & c | ~b & d, a, b, x, s, t); }
  function gg(a, b, c, d, x, s, t) { return cmn(b & d | c & ~d, a, b, x, s, t); }
  function hh(a, b, c, d, x, s, t) { return cmn(b ^ c ^ d, a, b, x, s, t); }
  function ii(a, b, c, d, x, s, t) { return cmn(c ^ (b | ~d), a, b, x, s, t); }

  const bytes = [...new TextEncoder().encode(str)];
  const bl = bytes.length * 8;
  bytes.push(128);
  while (bytes.length % 64 !== 56) bytes.push(0);
  bytes.push(bl & 255, bl >> 8 & 255, bl >> 16 & 255, bl >> 24 & 255, 0, 0, 0, 0);

  let a = 1732584193, b = -271733879, c = -1732584194, d = 271733878;

  for (let i = 0; i < bytes.length; i += 64) {
    const m = Array.from({ length: 16 }, (_, j) =>
      bytes[i + j*4] | bytes[i + j*4+1] << 8 | bytes[i + j*4+2] << 16 | bytes[i + j*4+3] << 24
    );
    const [aa, bb, cc, dd] = [a, b, c, d];

    a=ff(a,b,c,d,m[0],7,-680876936);d=ff(d,a,b,c,m[1],12,-389564586);c=ff(c,d,a,b,m[2],17,606105819);b=ff(b,c,d,a,m[3],22,-1044525330);
    a=ff(a,b,c,d,m[4],7,-176418897);d=ff(d,a,b,c,m[5],12,1200080426);c=ff(c,d,a,b,m[6],17,-1473231341);b=ff(b,c,d,a,m[7],22,-45705983);
    a=ff(a,b,c,d,m[8],7,1770035416);d=ff(d,a,b,c,m[9],12,-1958414417);c=ff(c,d,a,b,m[10],17,-42063);b=ff(b,c,d,a,m[11],22,-1990404162);
    a=ff(a,b,c,d,m[12],7,1804603682);d=ff(d,a,b,c,m[13],12,-40341101);c=ff(c,d,a,b,m[14],17,-1502002290);b=ff(b,c,d,a,m[15],22,1236535329);

    a=gg(a,b,c,d,m[1],5,-165796510);d=gg(d,a,b,c,m[6],9,-1069501632);c=gg(c,d,a,b,m[11],14,643717713);b=gg(b,c,d,a,m[0],20,-373897302);
    a=gg(a,b,c,d,m[5],5,-701558691);d=gg(d,a,b,c,m[10],9,38016083);c=gg(c,d,a,b,m[15],14,-660478335);b=gg(b,c,d,a,m[4],20,-405537848);
    a=gg(a,b,c,d,m[9],5,568446438);d=gg(d,a,b,c,m[14],9,-1019803690);c=gg(c,d,a,b,m[3],14,-187363961);b=gg(b,c,d,a,m[8],20,1163531501);
    a=gg(a,b,c,d,m[13],5,-1444681467);d=gg(d,a,b,c,m[2],9,-51403784);c=gg(c,d,a,b,m[7],14,1735328473);b=gg(b,c,d,a,m[12],20,-1926607734);

    a=hh(a,b,c,d,m[5],4,-378558);d=hh(d,a,b,c,m[8],11,-2022574463);c=hh(c,d,a,b,m[11],16,1839030562);b=hh(b,c,d,a,m[14],23,-35309556);
    a=hh(a,b,c,d,m[1],4,-1530992060);d=hh(d,a,b,c,m[4],11,1272893353);c=hh(c,d,a,b,m[7],16,-155497632);b=hh(b,c,d,a,m[10],23,-1094730640);
    a=hh(a,b,c,d,m[13],4,681279174);d=hh(d,a,b,c,m[0],11,-358537222);c=hh(c,d,a,b,m[3],16,-722521979);b=hh(b,c,d,a,m[6],23,76029189);
    a=hh(a,b,c,d,m[9],4,-640364487);d=hh(d,a,b,c,m[12],11,-421815835);c=hh(c,d,a,b,m[15],16,530742520);b=hh(b,c,d,a,m[2],23,-995338651);

    a=ii(a,b,c,d,m[0],6,-198630844);d=ii(d,a,b,c,m[7],10,1126891415);c=ii(c,d,a,b,m[14],15,-1416354905);b=ii(b,c,d,a,m[5],21,-57434055);
    a=ii(a,b,c,d,m[12],6,1700485571);d=ii(d,a,b,c,m[3],10,-1894986606);c=ii(c,d,a,b,m[10],15,-1051523);b=ii(b,c,d,a,m[1],21,-2054922799);
    a=ii(a,b,c,d,m[8],6,1873313359);d=ii(d,a,b,c,m[15],10,-30611744);c=ii(c,d,a,b,m[6],15,-1560198380);b=ii(b,c,d,a,m[13],21,1309151649);
    a=ii(a,b,c,d,m[4],6,-145523070);d=ii(d,a,b,c,m[11],10,-1120210379);c=ii(c,d,a,b,m[2],15,718787259);b=ii(b,c,d,a,m[9],21,-343485551);

    a=add(a,aa); b=add(b,bb); c=add(c,cc); d=add(d,dd);
  }

  return [a,b,c,d].map(n =>
    Array.from({ length: 4 }, (_, i) => (n >> i * 8 & 0xff).toString(16).padStart(2, '0')).join('')
  ).join('');
}

const SALT = 'okr4obncj8bw5a65hbnn5weg759646a7';
const BASE_URL = 'https://sg-public-api.hoyolab.com/event/game_record/genshin/api';
const SERVER_MAP = { '6': 'os_usa', '7': 'os_euro', '9': 'os_cht' };

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

function getServer(uid) {
  return SERVER_MAP[String(uid)[0]] ?? 'os_asia';
}

function generateDS(body = '', query = '') {
  const t = Math.floor(Date.now() / 1000);
  const alpha = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const r = Array.from({ length: 6 }, () => alpha[Math.floor(Math.random() * alpha.length)]).join('');
  const h = md5(`salt=${SALT}&t=${t}&r=${r}&b=${body}&q=${query}`);
  return `${t},${r},${h}`;
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS },
  });
}

export default {
  async fetch(req) {
    if (req.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS });
    }
    if (req.method === 'GET') {
      // Verify salt against known captured DS: 1776398132,bTDJiR,8707ca827e9870813948c6abf00cc374
      // from GET getGameRecordCard?uid=166756854
      const t = '1776398132', r = 'bTDJiR', q = 'uid=166756854', expected = '8707ca827e9870813948c6abf00cc374';
      const salts = {
        current:  'okr4obncj8bw5a65hbnn5weg759646a7',
        original: '6s25p5ox5y14umn1p61aqyyvbvvl3lrt',
        alt1:     'xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs',
        alt2:     'fd1qUaL8GAlFBJI2W0Rk5VdE4kOyAIQ7',
      };
      const results = {};
      for (const [name, salt] of Object.entries(salts)) {
        const h = md5(`salt=${salt}&t=${t}&r=${r}&b=&q=${q}`);
        results[name] = { hash: h, match: h === expected };
      }
      return json({ expected, results });
    }
    if (req.method !== 'POST') {
      return new Response('Use POST', { status: 405, headers: CORS });
    }

    let body;
    try { body = await req.json(); }
    catch { return json({ error: 'Invalid JSON body' }, 400); }

    const { ltuid_v2, ltoken_v2, ltmid_v2, uid } = body;
    if (!ltuid_v2 || !ltoken_v2 || !uid) {
      return json({ error: 'Missing ltuid_v2, ltoken_v2, or uid' }, 400);
    }

    try {
      const server = getServer(uid);
      const { device_fp = '38d7f70ff4d62', device_id = 'ed60545b-254d-40c7-b020-72f5830628af' } = body;
      const commonHeaders = {
        Cookie: `ltuid_v2=${ltuid_v2}; ltoken_v2=${ltoken_v2}${ltmid_v2 ? `; ltmid_v2=${ltmid_v2}` : ''}`,
        'x-rpc-app_version': '1.5.0',
        'x-rpc-client_type': '5',
        'x-rpc-device_fp': device_fp,
        'x-rpc-device_id': device_id,
        'x-rpc-env': 'default',
        'x-rpc-lang': 'en-us',
        'x-rpc-language': 'en-us',
        'x-rpc-platform': '4',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
        Referer: 'https://act.hoyolab.com/',
        Origin: 'https://act.hoyolab.com',
      };

      // Step 1: get character IDs from /character/list
      const listBody = JSON.stringify({ role_id: uid, server });
      const listRes = await fetch(`${BASE_URL}/character/list`, {
        method: 'POST',
        headers: { ...commonHeaders, 'Content-Type': 'application/json' },
        body: listBody,
      });
      const listText = await listRes.text();
      let listData;
      try { listData = JSON.parse(listText); }
      catch { return json({ error: `character/list ${listRes.status}: ${listText.slice(0, 200)}` }, 502); }
      if (listData.retcode !== 0) return json({ error: 'character/list failed', retcode: listData.retcode, message: listData.message });

      return json(listData);
    } catch (e) {
      return json({ error: `Worker error: ${e.message}` }, 500);
    }
  },
};
