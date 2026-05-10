# HTML Trackers

Personal study and fitness trackers — standalone HTML files with localStorage persistence and Cloudflare KV sync.

## Structure

```
├── index.html                 Landing page with links to all trackers
├── tracker-sync.js            Client-side sync module (localStorage + Cloudflare KV)
├── worker.js                  Cloudflare Worker API for state persistence
├── wrangler.toml              Worker configuration
├── study/
│   ├── aws_dea_fast_track_tracker.html    AWS Data Engineer Associate (DEA-C01)
│   ├── aws_ml_associate_tracker.html      AWS ML Engineer Associate (MLA-C01)
│   ├── aws_sa_associate_tracker.html      AWS Solutions Architect Associate (SAA-C03)
│   └── dataexpert_bootcamp_tracker.html   DataExpert.io Community Bootcamp
└── gym/
    ├── gym_program.html                   Training program + cheat sheet + session log
    └── weekly_tracker.html                Weekly session logger
```

## How It Works

- Each HTML file is self-contained (inline CSS + JS, no build step)
- State saves to localStorage immediately on every change
- `tracker-sync.js` transparently syncs state to Cloudflare KV for cross-device access
- If the server is unreachable, localStorage continues working offline

## Deployment

### Static files (Cloudflare Pages)

Push to GitHub — Cloudflare Pages auto-deploys from the connected repo.

### API Worker (Cloudflare Workers)

```bash
# Create KV namespace
npx wrangler kv namespace create TRACKER_STATE
# Paste the ID into wrangler.toml

# Set auth token
npx wrangler secret put AUTH_TOKEN

# Deploy
npx wrangler deploy
```

### Browser setup (one-time per device)

Open any tracker page, click the sync status pill (bottom-right), and enter your auth token.

## Local Development

```bash
# Start the API worker locally
npx wrangler dev worker.js --local

# Serve static files
python3 -m http.server 3000

# Open http://localhost:3000
```

For local dev, change the `SYNC_API` URL in `tracker-sync.js` to `http://localhost:8787`.
