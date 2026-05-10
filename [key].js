// GET /api/state/:key — read tracker state from KV
export async function onRequestGet(context) {
  const { params, env } = context;
  const key = decodeURIComponent(params.key);

  if (!key) {
    return new Response(JSON.stringify({ error: 'Missing key' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const value = await env.TRACKER_STATE.get(key);
  if (value === null) {
    return new Response(JSON.stringify({ data: null }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  let parsed;
  try {
    parsed = JSON.parse(value);
  } catch (e) {
    return new Response(JSON.stringify({ data: null, error: 'Malformed data in KV' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  return new Response(JSON.stringify({ data: parsed }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}

// PUT /api/state/:key — write tracker state to KV
export async function onRequestPut(context) {
  const { params, env, request } = context;
  const key = decodeURIComponent(params.key);

  if (!key) {
    return new Response(JSON.stringify({ error: 'Missing key' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  let body;
  try {
    body = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  await env.TRACKER_STATE.put(key, JSON.stringify(body));

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
