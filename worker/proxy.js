// Cloudflare Worker: CORS relay for Terrain Press (replaces serve.py's /proxy when the page is live).
// Deploy: Cloudflare dashboard > Workers > Create > paste this file. Usage: https://<worker>/?u=<encoded url>
const ALLOW = [ // only relay these hosts
  'https://esa-worldcover.s3.eu-central-1.amazonaws.com/',
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/',
  'https://tiles.maps.eox.at/wmts/',
  'https://tile.openstreetmap.org/',
  'https://a.tile.opentopomap.org/',
];
const ORIGINS = ['https://creativep2.github.io', 'http://localhost:8787', 'http://127.0.0.1:8787']; // who may call it
const UA = 'TerrainPress/2 (Project Pluto design tool)'; // OSM tile policy requires an identifying User-Agent

export default {
  async fetch(req) {
    const origin = req.headers.get('Origin') || '';
    const cors = {
      'Access-Control-Allow-Origin': ORIGINS.includes(origin) ? origin : ORIGINS[0],
      'Access-Control-Allow-Headers': 'Range',
      'Access-Control-Expose-Headers': 'Content-Range, Content-Length, Accept-Ranges',
      'Vary': 'Origin',
    };
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (!ORIGINS.includes(origin)) return new Response('origin not allowed', { status: 403, headers: cors });
    const u = new URL(req.url).searchParams.get('u') || '';
    if (!ALLOW.some(p => u.startsWith(p))) return new Response('host not allowed', { status: 403, headers: cors });
    const range = req.headers.get('Range');
    const r = await fetch(u, {
      headers: { 'User-Agent': UA, ...(range ? { Range: range } : {}) },
      ...(range ? {} : { cf: { cacheEverything: true, cacheTtl: 86400 } }), // cache whole tiles, not byte ranges
    });
    const h = new Headers(cors);
    for (const k of ['Content-Type', 'Content-Length', 'Content-Range', 'Accept-Ranges']) if (r.headers.get(k)) h.set(k, r.headers.get(k));
    return new Response(r.body, { status: r.status, headers: h });
  },
};
