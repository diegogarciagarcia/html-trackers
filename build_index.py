#!/usr/bin/env python3
"""Scan the repo for *.html files and generate a root index.html with a link to each.

Runs in CI on every push. New HTML files appear automatically; no manual edits.
"""
import os
import html
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))

# Files/dirs to skip when listing links.
SKIP_FILES = {"index.html"}          # don't link the generated index to itself
SKIP_NAMES = {"test.html"}           # scaffolding/test pages
SKIP_DIRS = {".git", ".github", "functions", "node_modules"}


def find_html():
    found = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".html"):
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


def build():
    files = find_html()
    groups = {}
    for rel in files:
        groups.setdefault(group_label(rel), []).append(rel)

    cards_html = []
    for grp in sorted(groups, key=lambda g: (g == "Root", g.lower())):
        label = html.escape(grp.replace("_", " ").title() if grp != "Root" else "Top level")
        cards_html.append(f'    <div class="section-label">{label}</div>')
        cards_html.append('    <div class="grid">')
        for rel in groups[grp]:
            href = html.escape(rel)
            title = html.escape(title_from(rel))
            path = html.escape(rel)
            cards_html.append(
                f'      <a class="link-card" href="{href}">\n'
                f'        <span class="card-title">{title}</span>\n'
                f'        <span class="card-path">{path}</span>\n'
                f'      </a>'
            )
        cards_html.append('    </div>')
    cards = "\n".join(cards_html) if files else '    <p class="empty">No HTML files yet. Add one and push.</p>'

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    count = len(files)
    plural = "s" if count != 1 else ""

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
      <p>{count} page{plural} &middot; auto-updated on every push</p>
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
    print(f"Wrote {out} with {count} link(s).")
    for rel in files:
        print("  -", rel)


if __name__ == "__main__":
    build()
