# abt-sa-website

Static Arabic (RTL) marketing site for ABT (abt-sa.com), a contractor in Arar / Jeddah, Saudi Arabia. Plain HTML/CSS/JS plus one PHP endpoint (`contact.php`). No build step.

## Layout
- `index.html` Arabic home; `en/index.html` English home. `blog/` and `en/blog/` mirror each other (same filenames).
- `muqawil-*-jeddah.html` Jeddah landing pages. `assets/` images (prefer `.webp`).
- `sitemap.xml` and `robots.txt` must be updated whenever a page is added.
- `_test-sharpen2.html`, `index-old-backup.html`, `abt-index-v6-clients-logos.html` are old drafts; do not edit or link them.

## Rules
- Arabic is the primary language: keep `lang="ar" dir="rtl"`; every Arabic blog post needs an English twin in `en/blog/`.
- Every page needs one `<h1>`, title, meta description, canonical, GA4 tag, and `alt` on all images.
- Do not change `contact.php` validation or the honeypot field without asking; never commit secrets or recipient emails.
- Run `python3 scripts/check-site.py` before committing; it must print `OK`.

## Preview
`python3 -m http.server 8000` (the PHP form will not work there; use `php -S localhost:8000` if PHP is installed).
