/**
 * Cloudflare Pages Worker — HTML Trackers
 *
 * Deployed as a Cloudflare Pages project with _worker.js advanced mode.
 * Static files are served automatically via env.ASSETS for non-API routes.
 * This worker intercepts /api/ routes for state sync.
 *
 * Endpoints:
 *   GET  /api/state/:key  → read tracker state from KV
 *   PUT  /api/state/:key  → write tracker state to KV
 *   GET  /api/keys        → list all stored keys
 *
 * Auth: Bearer token via AUTH_TOKEN secret (only for /api/ routes)
 * KV Namespace binding: TRACKER_STATE
 */

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname;

    // Non-API routes — let Cloudflare Pages serve static assets
    if (!path.startsWith('/api/')) {
      return env.ASSETS.fetch(request);
    }

    // CORS headers for cross-origin requests
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, PUT, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    };

    // Handle preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // Auth check (only for /api/ routes)
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

      let parsed;
      try {
        parsed = JSON.parse(value);
      } catch (e) {
        return new Response(JSON.stringify({ data: null, error: 'Malformed data in KV' }), {
          status: 200,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

      return new Response(JSON.stringify({ data: parsed }), {
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

      let body;
      try {
        body = await request.json();
      } catch {
        return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        });
      }

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

    // Fallback for unknown /api/ routes
    return new Response(JSON.stringify({ error: 'Not found' }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  },
};

