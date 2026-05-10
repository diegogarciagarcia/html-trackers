// GET /api/keys — list all stored keys
export async function onRequestGet(context) {
  const { env } = context;
  const list = await env.TRACKER_STATE.list();
  const keys = list.keys.map(k => k.name);

  return new Response(JSON.stringify({ keys }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' },
  });
}
