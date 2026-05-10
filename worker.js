/**
 * Cloudflare Worker — HTML Trackers State API
 *
 * Endpoints:
 *   GET  /api/state/:key  → read tracker state from KV
 *   PUT  /api/state/:key  → write tracker state to KV
 *   GET  /api/keys        → list all stored keys
 *
 * Auth: Bearer token via AUTH_TOKEN secret
 * KV Namespace binding: TRACKER_STATE
 *
 * Setup:
 *   1. Create KV namespace:  wrangler kv namespace create TRACKER_STATE
 *   2. Add secret:           wrangler secret put AUTH_TOKEN
 *   3. Bind KV in wrangler.toml (see below)
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // CORS headers for cross-origin requests from your HTML files
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // Auth check
    const authHeader = request.headers.get('Authorization') || '';
    const token = authHeader.replace('Bearer ', '');
    if (token !== env.AUTH_TOKEN) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 401,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Route: GET /api/state/:key
    if (request.method === 'GET' && path.startsWith('/api/state/')) {
      const key = decodeURIComponent(path.replace('/api/state/', ''));
      if (!key) {
        return new Response(JSON.stringify({ error: 'Missing key' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      const value = await env.TRACKER_STATE.get(key);
      if (value === null) {
        return new Response(JSON.stringify({ data: null }), {
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      return new Response(JSON.stringify({ data: JSON.parse(value) }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Route: PUT /api/state/:key
    if (request.method === 'PUT' && path.startsWith('/api/state/')) {
      const key = decodeURIComponent(path.replace('/api/state/', ''));
      if (!key) {
        return new Response(JSON.stringify({ error: 'Missing key' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      const body = await request.json();
      await env.TRACKER_STATE.put(key, JSON.stringify(body));

      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Route: GET /api/keys
    if (request.method === 'GET' && path === '/api/keys') {
      const list = await env.TRACKER_STATE.list();
      const keys = list.keys.map(k => k.name);
      return new Response(JSON.stringify({ keys }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // Fallback: serve static assets or 404
    return new Response(JSON.stringify({ error: 'Not found' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  },
};
