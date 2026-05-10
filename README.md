# HTML Trackers

Personal study and fitness trackers — standalone HTML files deployed on Cloudflare Pages with serverless API functions for cross-device state sync.

## Live URL

`https://html-trackers.diegogarciagarcia.workers.dev`

## Project Structure

```
/
├── .gitignore
├── README.md
├── public/                              ← Static files (Cloudflare Pages build output)
│   ├── index.html                       Landing page with links to all trackers
│   ├── tracker-sync.js                  Client-side sync module (localStorage + KV)
│   ├── gym/
│   │   ├── gym_program.html             Training program + cheat sheet + session log
│   │   └── weekly_tracker.html          Weekly session logger (3 tabs)
│   └── study/
│       ├── aws_dea_fast_track_tracker.html    AWS Data Engineer Associate (DEA-C01)
│       ├── aws_ml_associate_tracker.html      AWS ML Engineer Associate (MLA-C01)
│       ├── aws_sa_associate_tracker.html      AWS Solutions Architect Associate (SAA-C03)
│       └── dataexpert_bootcamp_tracker.html   DataExpert.io Community Bootcamp
└── functions/                           ← Cloudflare Pages Functions (API)
    └── api/
        ├── _middleware.js               Auth + CORS middleware for all /api/ routes
        ├── keys.js                      GET /api/keys — list stored keys
        └── state/
            └── [key].js                 GET/PUT /api/state/:key — read/write state
```

## How It Works

### Storage layers

1. **localStorage** (immediate) — each tracker saves state on every change, works offline
2. **Cloudflare KV** (server) — `tracker-sync.js` transparently syncs state to KV for cross-device access

### Data flow

- **On page load:** fetches latest state from KV → writes to localStorage → tracker renders
- **On every change:** saves to localStorage immediately → debounces 2s → pushes to KV
- **Offline:** localStorage keeps working, sync resumes when connection returns

### Sync keys

| Tracker | KV Key | localStorage pattern |
|---------|--------|---------------------|
| Weekly Training | `weekly-training` | Single blob: `weeklyTrainingTracker.v3` |
| DEA Fast Track | `aws-dea-fast-track` | Prefix: `dea_*` |
| ML Associate | `aws-ml-associate` | Prefix: `mla_*` |
| SA Associate | `aws-sa-associate` | Prefix: `saa_*` |
| DataExpert Bootcamp | `dataexpert-bootcamp` | Single blob: `de_bootcamp_tracker_v1` |

### Gym program live data

The gym program (`gym_program.html`) reads from the weekly tracker's data to show:
- **Last Used** — weight from the most recent session for each exercise
- **Highest** — maximum weight ever logged for each exercise
- **Session Log** — read-only tab showing all logged sessions

## Deployment

This project deploys via **Cloudflare Pages** connected to a GitHub repo.

### GitHub → Cloudflare Pages (automatic)

Push to `main` branch → Cloudflare auto-deploys.

**Pages settings:**
- Build command: (empty)
- Build output directory: `public`
- Root directory: `/`

### Cloudflare Pages dashboard setup (one-time)

1. **Settings → Bindings → KV namespace**
   - Variable name: `TRACKER_STATE`
   - Select your KV namespace

2. **Settings → Environment variables**
   - Name: `AUTH_TOKEN`
   - Value: your secret token (encrypt it)

### Browser setup (one-time per device)

Open any tracker page, click the sync status pill (bottom-right corner), enter your AUTH_TOKEN.

## API Endpoints

All require `Authorization: Bearer <token>` header.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/state/:key` | Read tracker state |
| PUT | `/api/state/:key` | Write tracker state (JSON body) |
| GET | `/api/keys` | List all stored keys |

### Test with curl

```bash
# Read (use single quotes if token has special chars)
curl -s -H 'Authorization: Bearer YOUR_TOKEN' https://html-trackers.diegogarciagarcia.workers.dev/api/state/weekly-training

# Write
curl -s -X PUT -H 'Authorization: Bearer YOUR_TOKEN' -H 'Content-Type: application/json' \
  -d '{"test":true}' https://html-trackers.diegogarciagarcia.workers.dev/api/state/test-key

# List keys
curl -s -H 'Authorization: Bearer YOUR_TOKEN' https://html-trackers.diegogarciagarcia.workers.dev/api/keys
```

## Local Development

```bash
# Run everything locally (Pages + Functions)
npx wrangler pages dev public

# With KV binding for local testing
npx wrangler pages dev public --kv TRACKER_STATE
```

Create a `.dev.vars` file for local secrets:
```
AUTH_TOKEN=your-local-test-token
```

## Tech Stack

- **Frontend:** Standalone HTML files with inline CSS/JS (no build step, no framework)
- **Hosting:** Cloudflare Pages (static assets)
- **API:** Cloudflare Pages Functions (serverless)
- **Storage:** Cloudflare Workers KV (key-value store)
- **Sync:** Custom `tracker-sync.js` module (intercepts localStorage, debounces to KV)
