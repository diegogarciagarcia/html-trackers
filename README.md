# HTML Trackers

Personal study, fitness, and travel trackers — standalone HTML files deployed on GitHub Pages. Each tracker saves progress to `localStorage` in the browser.

## Project Structure

```
/
├── .github/workflows/pages.yml          CI: rebuild index → deploy to GitHub Pages
├── .nojekyll                            Tells GitHub Pages to skip Jekyll processing
├── build_index.py                       Generates index.html + gallery pages on every push
├── study/
│   ├── aws_dea_fast_track_tracker.html  AWS Data Engineer Associate (DEA-C01)
│   ├── aws_ml_associate_tracker.html    AWS ML Engineer Associate (MLA-C01)
│   ├── aws_sa_associate_tracker.html    AWS Solutions Architect Associate (SAA-C03)
│   └── dataexpert_bootcamp_tracker.html DataExpert.io Community Bootcamp
├── travel/
│   ├── new_orleans_shopping_souvenirs.html
│   └── new_orleans_trip_plan.html
└── old/                                 Archived / superseded trackers (excluded from index)
    ├── gym_program.html
    ├── index.html
    └── weekly_tracker.html
```

## How It Works

### Storage

Each tracker saves state to **localStorage** on every change. Data persists per browser/device — there is no server-side sync.

### Auto-generated index

On every push to `main`, a GitHub Actions workflow runs `build_index.py`. The script:

1. Walks the repo looking for `*.html` files and image folders
2. For each folder containing images (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`), generates a gallery page with thumbnails and a lightbox viewer
3. Builds a root `index.html` linking to every HTML page and gallery, grouped by folder

New HTML files and image folders appear on the site automatically — no manual edits needed.

### Image galleries

Drop images into any folder (e.g. `photos/`, `travel/pics/`) and push. The build script generates a `<folder>_gallery.html` page with:

- Responsive thumbnail grid
- Click-to-zoom lightbox with keyboard nav (← → Esc)
- Auto-linked from the index under a "📷 Galleries" section

Gallery pages are generated at build time and gitignored — only the source images are committed.

## Deployment

Push to `main` → GitHub Actions runs `build_index.py` → uploads the repo root as a GitHub Pages artifact → deploys.

The workflow lives at `.github/workflows/pages.yml`.

## Tech Stack

- **Frontend:** Standalone HTML files with inline CSS/JS (no build step, no framework)
- **Hosting:** GitHub Pages
- **Storage:** Browser localStorage
- **CI:** GitHub Actions (auto-generates `index.html` and gallery pages on every push)
