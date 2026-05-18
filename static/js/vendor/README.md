# Vendor JavaScript

Pinned copies of HTMX and Alpine, copied from npm by `npm run build:vendor`.
Commit these files after upgrading versions in `package.json`.

| File | npm package | Version |
|------|-------------|---------|
| `htmx.min.js` | `htmx.org` | see `package.json` |
| `alpine.min.js` | `alpinejs` | see `package.json` |

Served via Django `{% static %}` (same origin) — no CDN or SRI required for these assets.
