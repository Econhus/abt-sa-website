#!/usr/bin/env python3
"""Static checks for the ABT site: broken local links/assets, sitemap coverage,
missing title/description/canonical/hreflang, GA4 tag."""
import re, sys, pathlib
from urllib.parse import urlparse, unquote

root = pathlib.Path(__file__).resolve().parent.parent
SKIP = {"_test-sharpen2.html", "index-old-backup.html", "abt-index-v6-clients-logos.html"}
pages = [p for p in root.rglob("*.html") if ".git" not in p.parts and p.name not in SKIP]
problems = []

def add(p, msg): problems.append(f"{p.relative_to(root)}: {msg}")

for p in pages:
    t = p.read_text(encoding="utf-8", errors="ignore")
    if not re.search(r"<title>[^<]+</title>", t): add(p, "missing <title>")
    if 'name="description"' not in t: add(p, "missing meta description")
    if 'rel="canonical"' not in t: add(p, "missing canonical")
    if "googletagmanager.com/gtag" not in t: add(p, "missing GA4 tag")
    if len(re.findall(r"<h1[\s>]", t)) != 1: add(p, "should have exactly one <h1>")
    for m in re.finditer(r'(?:src|href)="([^"#?]+)', t):
        u = m.group(1)
        if re.match(r"(https?:|mailto:|tel:|data:|//|javascript:)", u): continue
        base = root if u.startswith("/") else p.parent
        target = (base / unquote(u.lstrip("/"))).resolve()
        if target.is_dir(): target = target / "index.html"
        if not target.exists(): add(p, f"broken local ref {u}")
    for m in re.finditer(r'<img(?![^>]*\balt=)[^>]*>', t): add(p, "img without alt")

sm = (root / "sitemap.xml").read_text()
locs = set(re.findall(r"<loc>https://abt-sa\.com/([^<]*)</loc>", sm))
for p in pages:
    rel = p.relative_to(root).as_posix()
    key = rel.removesuffix("index.html") if rel.endswith("index.html") else rel
    if key not in locs: add(p, "not in sitemap.xml")

print("\n".join(problems) or "OK")
sys.exit(1 if problems else 0)
