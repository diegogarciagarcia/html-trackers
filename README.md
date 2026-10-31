# HTML Trackers

Personal study and fitness trackers — standalone HTML files deployed on GitHub Pages with localStorage for state persistence.

## Live URL

Deployed via GitHub Pages (configured in the repo settings).

## Project Structure

```
/
├── .gitignore
├── README.md
├── build_index.py                       Generates index.html on every push (GitHub Actions)
├── .github/workflows/pages.yml          CI: rebuild index → deploy to GitHub Pages
├── public/
│   └── study/
│       ├── aws_dea_fast_track_tracker.html    AWS Data Engineer Associate (DEA-C01)
│       ├── aws_ml_associate_tracker.html      AWS ML Engineer Associate (MLA-C01)
│       ├── aws_sa_associate_tracker.html      AWS Solutions Architect Associate (SAA-C03)
│       └── dataexpert_bootcamp_tracker.html   DataExpert.io Community Bootcamp
├── old/                                 Archived trackers (not linked from index)
│   ├── gym_program.html
│   └── weekly_tracker.html
└── travel/
    ├── new_orleans_shopping_souvenirs.html
    └── new_orleans_trip_plan.html
```

## How It Works

### Storage

Each tracker saves its state to **localStorage** on every change. Data persists per browser/device. There is no server-side sync — all state lives in the browser.

### Auto-generated index

On every push to `main`, a GitHub Actions workflow runs `build_index.py`, which scans the repo for `*.html` files and generates a root `index.html` linking to each one. New pages appear automatically without manual edits.

## Deployment

Push to `main` → GitHub Actions rebuilds `index.html` → deploys to GitHub Pages.

The workflow is in `.github/workflows/pages.yml`.

## Tech Stack

- **Frontend:** Standalone HTML files with inline CSS/JS (no build step, no framework)
- **Hosting:** GitHub Pages
- **Storage:** Browser localStorage
- **CI:** GitHub Actions (`build_index.py` generates the index on every push)
