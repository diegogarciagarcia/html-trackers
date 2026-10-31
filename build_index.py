#!/usr/bin/env python3
"""Scan the repo for *.html files and image folders, generate gallery pages
for each image folder, and build a root index.html linking everything.

Runs in CI on every push. New HTML files and image folders appear automatically.
"""
import os
import html
import datetime
import base64
import struct
import zlib

ROOT = os.path.dirname(os.path.abspath(__file__))

# Files/dirs to skip when listing links.
SKIP_FILES = {"index.html"}
SKIP_NAMES = {"test.html"}
SKIP_DIRS = {".git", ".github", "functions", "node_modules", "old"}

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
GENERATED_GALLERY_SUFFIX = "_gallery.html"


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def is_image(filename):
    return os.path.splitext(filename)[1].lower() in IMAGE_EXTS


def find_image_folders():
    """Return a dict of {relative_dir: [relative_image_paths]} for dirs that
    contain at least one image."""
    folders = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        images = sorted(f for f in filenames if is_image(f))
        if not images:
            continue
        rel_dir = os.path.relpath(dirpath, ROOT).replace(os.sep, "/")
        if rel_dir == ".":
            rel_dir = ""
        folders[rel_dir] = [
            (os.path.join(rel_dir, img) if rel_dir else img).replace(os.sep, "/")
            for img in images
        ]
    return folders


def gallery_path_for(rel_dir):
    """Return the relative path of the generated gallery HTML for a folder."""
    if not rel_dir:
        name = "root"
    else:
        name = rel_dir.replace("/", "_")
    return f"{name}{GENERATED_GALLERY_SUFFIX}"


def build_gallery(rel_dir, image_paths):
    """Generate a self-contained gallery HTML page for one image folder."""
    title = html.escape(rel_dir if rel_dir else "Root")
    count = len(image_paths)
    plural = "s" if count != 1 else ""

    cards = []
    for img in image_paths:
        fname = html.escape(os.path.basename(img))
        href = html.escape(img)
        cards.append(
            f'      <a class="img-card" href="{href}" target="_blank">\n'
            f'        <img src="{href}" alt="{fname}" loading="lazy" />\n'
            f'        <span class="img-name">{fname}</span>\n'
            f'      </a>'
        )
    cards_html = "\n".join(cards)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Gallery — {title}</title>
  <style>
    :root {{
      --bg:#f5f7fb; --card:#fff; --text:#172033; --muted:#667085;
      --border:#e5e7eb; --accent:#2563eb; --shadow:0 10px 30px rgba(15,23,42,.08);
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{ --bg:#0f172a; --card:#1e293b; --text:#e2e8f0; --muted:#94a3b8; --border:#334155; }}
    }}
    * {{ box-sizing:border-box; margin:0; }}
    body {{ background:var(--bg); color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif; line-height:1.5; }}
    .app {{ max-width:1100px; margin:0 auto; padding:22px; }}
    header {{ background:linear-gradient(135deg,#1d4ed8,#0f172a); color:#fff;
      border-radius:24px; padding:32px; margin-bottom:28px; box-shadow:var(--shadow); text-align:center; }}
    header h1 {{ font-size:30px; letter-spacing:-.04em; margin-bottom:4px; }}
    header p {{ color:#dbeafe; font-size:15px; }}
    .back {{ display:inline-block; margin-bottom:18px; color:var(--accent); text-decoration:none;
      font-weight:600; font-size:14px; }}
    .back:hover {{ text-decoration:underline; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:16px; }}
    @media (max-width:640px) {{ .grid {{ grid-template-columns:repeat(2,1fr); gap:10px; }} }}
    .img-card {{ background:var(--card); border:1px solid var(--border); border-radius:16px;
      overflow:hidden; box-shadow:var(--shadow); text-decoration:none; color:var(--text);
      transition:transform .15s ease,box-shadow .15s ease; display:flex; flex-direction:column; }}
    .img-card:hover {{ transform:translateY(-3px); box-shadow:0 14px 36px rgba(15,23,42,.13); }}
    .img-card img {{ width:100%; aspect-ratio:1/1; object-fit:cover; display:block; background:var(--border); }}
    .img-name {{ padding:10px 12px; font-size:12px; color:var(--muted);
      font-family:ui-monospace,SFMono-Regular,Menlo,monospace; white-space:nowrap;
      overflow:hidden; text-overflow:ellipsis; }}
    footer {{ text-align:center; color:var(--muted); font-size:12px; margin-top:36px; }}

    /* Lightbox */
    .lightbox {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.88);
      z-index:1000; align-items:center; justify-content:center; padding:20px; cursor:zoom-out; }}
    .lightbox.open {{ display:flex; }}
    .lightbox img {{ max-width:100%; max-height:90vh; object-fit:contain; border-radius:12px; cursor:default; }}
    .lb-close {{ position:fixed; top:16px; right:20px; color:#fff; font-size:28px; cursor:pointer;
      background:rgba(0,0,0,.5); border:none; border-radius:50%; width:40px; height:40px;
      display:flex; align-items:center; justify-content:center; z-index:1001; }}
    .lb-nav {{ position:fixed; top:50%; color:#fff; font-size:32px; cursor:pointer;
      background:rgba(0,0,0,.4); border:none; border-radius:50%; width:44px; height:44px;
      display:flex; align-items:center; justify-content:center; z-index:1001; transform:translateY(-50%); }}
    .lb-prev {{ left:16px; }}
    .lb-next {{ right:16px; }}
    .lb-counter {{ position:fixed; bottom:20px; left:50%; transform:translateX(-50%);
      color:#cbd5e1; font-size:14px; z-index:1001; }}
  </style>
</head>
<body>
  <div class="app">
    <a class="back" href="index.html">← Back to index</a>
    <header>
      <h1>📷 {title}</h1>
      <p>{count} image{plural}</p>
    </header>
    <div class="grid">
{cards_html}
    </div>
    <footer>Auto-generated gallery</footer>
  </div>

  <!-- Lightbox -->
  <div class="lightbox" id="lb">
    <button class="lb-close" id="lb-close">&times;</button>
    <button class="lb-nav lb-prev" id="lb-prev">&#8249;</button>
    <button class="lb-nav lb-next" id="lb-next">&#8250;</button>
    <img id="lb-img" src="" alt="" />
    <div class="lb-counter" id="lb-counter"></div>
  </div>

  <script>
    (function() {{
      const imgs = Array.from(document.querySelectorAll('.img-card'));
      const lb = document.getElementById('lb');
      const lbImg = document.getElementById('lb-img');
      const lbCounter = document.getElementById('lb-counter');
      let idx = 0;

      function show(i) {{
        idx = (i + imgs.length) % imgs.length;
        lbImg.src = imgs[idx].href;
        lbImg.alt = imgs[idx].querySelector('.img-name').textContent;
        lbCounter.textContent = (idx + 1) + ' / ' + imgs.length;
      }}

      imgs.forEach(function(card, i) {{
        card.addEventListener('click', function(e) {{
          e.preventDefault();
          show(i);
          lb.classList.add('open');
        }});
      }});

      lb.addEventListener('click', function(e) {{
        if (e.target === lb) lb.classList.remove('open');
      }});
      document.getElementById('lb-close').addEventListener('click', function() {{
        lb.classList.remove('open');
      }});
      document.getElementById('lb-prev').addEventListener('click', function(e) {{
        e.stopPropagation(); show(idx - 1);
      }});
      document.getElementById('lb-next').addEventListener('click', function(e) {{
        e.stopPropagation(); show(idx + 1);
      }});
      document.addEventListener('keydown', function(e) {{
        if (!lb.classList.contains('open')) return;
        if (e.key === 'Escape') lb.classList.remove('open');
        if (e.key === 'ArrowLeft') show(idx - 1);
        if (e.key === 'ArrowRight') show(idx + 1);
      }});
    }})();
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# HTML finder (existing logic)
# ---------------------------------------------------------------------------

def find_html():
    found = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".html"):
                continue
            # Skip generated gallery pages
            if fn.endswith(GENERATED_GALLERY_SUFFIX):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace(os.sep, "/")
            if rel in SKIP_FILES or fn in SKIP_NAMES:
                continue
            found.append(rel)
    return sorted(found)


def title_from(rel):
    base = os.path.basename(rel)[:-5]  # drop .html
    return base.replace("_", " ").replace("-", " ").strip().title()


def group_label(rel):
    parts = rel.split("/")
    return parts[0] if len(parts) > 1 else "Root"


# ---------------------------------------------------------------------------
# Index builder
# ---------------------------------------------------------------------------

def build():
    # --- Step 1: generate gallery pages for image folders ---
    image_folders = find_image_folders()
    gallery_files = []
    for rel_dir, images in sorted(image_folders.items()):
        gallery_rel = gallery_path_for(rel_dir)
        gallery_html = build_gallery(rel_dir, images)
        out_path = os.path.join(ROOT, gallery_rel)
        with open(out_path, "w") as f:
            f.write(gallery_html)
        gallery_files.append(gallery_rel)
        print(f"  gallery: {gallery_rel} ({len(images)} images)")

    # --- Step 2: find all HTML pages (excluding generated galleries) ---
    files = find_html()
    groups = {}
    for rel in files:
        groups.setdefault(group_label(rel), []).append(rel)

    # --- Step 3: add gallery pages as a "Galleries" group ---
    if gallery_files:
        groups["📷 Galleries"] = gallery_files

    # --- Step 4: build the index ---
    cards_html = []
    for grp in sorted(groups, key=lambda g: (g == "Root", "📷" in g, g.lower())):
        label = html.escape(grp.replace("_", " ").title() if grp not in ("Root", "📷 Galleries") else grp)
        if label == "Root":
            label = "Top level"
        cards_html.append(f'    <div class="section-label">{label}</div>')
        cards_html.append('    <div class="grid">')
        for rel in groups[grp]:
            href = html.escape(rel)
            title = html.escape(title_from(rel))
            path = html.escape(rel)
            # Gallery cards get a camera icon
            if rel.endswith(GENERATED_GALLERY_SUFFIX):
                folder_name = rel.replace(GENERATED_GALLERY_SUFFIX, "").replace("_", "/")
                if folder_name == "root":
                    folder_name = "(root)"
                title = f"📷 {html.escape(folder_name)}"
            cards_html.append(
                f'      <a class="link-card" href="{href}">\n'
                f'        <span class="card-title">{title}</span>\n'
                f'        <span class="card-path">{path}</span>\n'
                f'      </a>'
            )
        cards_html.append('    </div>')
    cards = "\n".join(cards_html) if groups else '    <p class="empty">No HTML files yet. Add one and push.</p>'

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total = len(files) + len(gallery_files)
    plural = "s" if total != 1 else ""

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>My HTML Pages</title>
  <style>
    :root {{
      --bg:#f5f7fb; --card:#fff; --text:#172033; --muted:#667085;
      --border:#e5e7eb; --accent:#2563eb; --shadow:0 10px 30px rgba(15,23,42,.08);
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{ --bg:#0f172a; --card:#1e293b; --text:#e2e8f0; --muted:#94a3b8; --border:#334155; }}
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--bg); color:var(--text);
      font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif; line-height:1.5; }}
    .app {{ max-width:860px; margin:0 auto; padding:22px; }}
    header {{ background:linear-gradient(135deg,#1d4ed8,#0f172a); color:#fff;
      border-radius:24px; padding:32px; margin-bottom:28px; box-shadow:var(--shadow); text-align:center; }}
    header h1 {{ margin:0 0 8px; font-size:34px; letter-spacing:-.04em; }}
    header p {{ margin:0; color:#dbeafe; font-size:15px; }}
    .section-label {{ font-size:13px; font-weight:800; text-transform:uppercase;
      letter-spacing:.06em; color:var(--muted); margin:28px 0 12px; padding-left:4px; }}
    .grid {{ display:grid; grid-template-columns:repeat(2,1fr); gap:16px; }}
    @media (max-width:640px) {{ .grid {{ grid-template-columns:1fr; }} }}
    .link-card {{ background:var(--card); border:1px solid var(--border); border-radius:20px;
      padding:22px; box-shadow:var(--shadow); text-decoration:none; color:var(--text);
      transition:transform .15s ease,box-shadow .15s ease; display:flex; flex-direction:column; gap:6px; }}
    .link-card:hover {{ transform:translateY(-3px); box-shadow:0 14px 36px rgba(15,23,42,.13); }}
    .card-title {{ font-size:17px; font-weight:700; }}
    .card-path {{ font-size:12px; color:var(--muted); font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}
    .empty {{ color:var(--muted); text-align:center; padding:40px; }}
    footer {{ text-align:center; color:var(--muted); font-size:12px; margin-top:36px; }}
  </style>
</head>
<body>
  <div class="app">
    <header>
      <h1>My HTML Pages</h1>
      <p>{total} page{plural} &middot; auto-updated on every push</p>
    </header>
{cards}
    <footer>Generated {stamp} by GitHub Actions</footer>
  </div>
</body>
</html>
"""
    out = os.path.join(ROOT, "index.html")
    with open(out, "w") as f:
        f.write(page)
    print(f"Wrote {out} with {total} link(s).")
    for rel in files:
        print("  -", rel)
    for rel in gallery_files:
        print("  - [gallery]", rel)


if __name__ == "__main__":
    build()
