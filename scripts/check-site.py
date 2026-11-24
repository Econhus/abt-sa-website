#!/usr/bin/env python3
"""Static checks for the abt-sa.com website (no external dependencies).

Checks every .html file in the repository (except legacy files listed in EXCLUDED):
  - <title>, <meta name="description">, <link rel="canonical"> and the GA4 tag
    (googletagmanager.com/gtag) are present
  - exactly one <h1>
  - every <img> has an alt attribute
  - no broken local links or images (href / src / srcset)
  - the page is listed in sitemap.xml

Usage:  python3 scripts/check-site.py
Prints "OK" and exits 0 on success; otherwise prints the problems and exits 1.
"""

import os
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_HOSTS = {"abt-sa.com", "www.abt-sa.com"}
GA4_MARKER = "googletagmanager.com/gtag"

# Legacy / test files: never edited, never checked.
EXCLUDED = {
    "_test-sharpen2.html",
    "index-old-backup.html",
    "abt-index-v6-clients-logos.html",
}
SKIP_DIRS = {".git", "node_modules", ".github"}
SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "sms:", "whatsapp:")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.has_title = False
        self.has_description = False
        self.has_canonical = False
        self.h1_count = 0
        self.imgs_without_alt = []
        self.refs = []  # (attribute, value, line)

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        line = self.getpos()[0]
        if tag == "title":
            self.has_title = True
        elif tag == "meta" and a.get("name", "").lower() == "description" and a.get("content", "").strip():
            self.has_description = True
        elif tag == "link" and "canonical" in a.get("rel", "").lower().split() and a.get("href", "").strip():
            self.has_canonical = True
        elif tag == "h1":
            self.h1_count += 1
        if tag == "img" and "alt" not in a:
            self.imgs_without_alt.append((a.get("src", "?"), line))
        for attr in ("href", "src"):
            if attr in a and tag not in ("base",):
                self.refs.append((attr, a[attr], line))
        for attr in ("srcset",):
            if attr in a:
                for part in a[attr].split(","):
                    url = part.strip().split(" ")[0]
                    if url:
                        self.refs.append((attr, url, line))

    handle_startendtag = handle_starttag


def html_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.lower().endswith(".html"):
                rel = os.path.relpath(os.path.join(dirpath, name), ROOT).replace(os.sep, "/")
                if rel not in EXCLUDED:
                    yield rel


def sitemap_paths():
    """Return the set of repo-relative file paths listed in sitemap.xml."""
    path = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(path):
        return None
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    paths = set()
    for loc in ET.parse(path).getroot().findall("s:url/s:loc", ns):
        p = unquote(urlsplit((loc.text or "").strip()).path).lstrip("/")
        if p == "" or p.endswith("/"):
            p += "index.html"
        paths.add(p)
    return paths


def resolve_local(page_rel, url):
    """Return the target file path for a local URL, or None if it is external/ignored."""
    url = url.strip()
    if not url or url.startswith("#") or url.lower().startswith(SKIP_SCHEMES):
        return None
    parts = urlsplit(url)
    if parts.scheme or parts.netloc:
        if parts.scheme in ("http", "https", "") and parts.netloc.lower() in SITE_HOSTS:
            path = parts.path or "/"
        else:
            return None  # external
    else:
        path = parts.path
        if not path:
            return None  # "?query" or "#frag" only
    path = unquote(path)
    if path.startswith("/"):
        target = os.path.join(ROOT, path.lstrip("/"))
    else:
        target = os.path.join(ROOT, os.path.dirname(page_rel), path)
    target = os.path.normpath(target)
    if path.endswith("/") or os.path.isdir(target):
        target = os.path.join(target, "index.html")
    return target


def main():
    problems = []
    listed = sitemap_paths()
    if listed is None:
        problems.append("sitemap.xml: file not found")
        listed = set()

    files = sorted(html_files())
    for rel in files:
        with open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace") as f:
            text = f.read()
        p = PageParser()
        p.feed(text)

        if not p.has_title:
            problems.append(f"{rel}: missing <title>")
        if not p.has_description:
            problems.append(f"{rel}: missing <meta name=\"description\">")
        if not p.has_canonical:
            problems.append(f"{rel}: missing <link rel=\"canonical\">")
        if GA4_MARKER not in text:
            problems.append(f"{rel}: missing GA4 tag ({GA4_MARKER})")
        if p.h1_count != 1:
            problems.append(f"{rel}: expected exactly 1 <h1>, found {p.h1_count}")
        for src, line in p.imgs_without_alt:
            problems.append(f"{rel}:{line}: <img src=\"{src}\"> has no alt attribute")
        seen = set()
        for attr, url, line in p.refs:
            target = resolve_local(rel, url)
            if target and not os.path.exists(target) and (url, line) not in seen:
                seen.add((url, line))
                problems.append(f"{rel}:{line}: broken local {attr} -> {url}")
        if rel not in listed:
            problems.append(f"{rel}: not listed in sitemap.xml")

    if problems:
        print(f"Found {len(problems)} problem(s) in {len(files)} page(s):")
        for msg in problems:
            print(f"  - {msg}")
        return 1
    print(f"OK ({len(files)} pages checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
