# Form Validation App

A portfolio-style Django 5 showcase for layered form validation with HTMX partials,
custom form fields, validator introspection, formsets, a session-backed wizard (HTMX
step navigation), and focused tests (unit + Playwright E2E in CI).

## Stack

- Python 3.12 target, Django 5, SQLite for development
- PostgreSQL 16-ready settings through `DATABASE_URL`
- HTMX and Alpine.js **self-hosted** from `static/js/vendor/` (pinned via npm, not CDN)
- Optional `django-htmx`; compiled Tailwind CSS (`static/css/forms_lab.css`)
- `phonenumbers`, `python-magic`, Pillow; **WhiteNoise** for production static files
- Test/lint tools in `requirements-dev.txt` (pytest, pytest-cov, ruff, black, hypothesis, Playwright)
- Tooling config in `pyproject.toml` (pytest, coverage, ruff, black)

The code includes small fallbacks for optional local dependencies so the app remains
easy to run in constrained demo environments.

```bash
pip install -r requirements.txt          # runtime
pip install -r requirements-dev.txt      # tests, lint, e2e
npm install && npm run build             # CSS + vendor JS (see package.json for pinned htmx/alpine)
```

## Run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/.

## Production

`config/wsgi.py` and `asgi.py` default to `config.settings.prod`, which **requires**
a real `SECRET_KEY` env var (it raises `ImproperlyConfigured` on the dev placeholder).
Static assets are served by WhiteNoise, so collect them after setting the environment:

```bash
export SECRET_KEY=...                        # required by prod settings
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py collectstatic --noinput
python manage.py migrate
```

## Field Partial Contract

`templates/forms/_field.html` is the only place field **markup** belongs, but you must
**not** render it with a bare `{% include %}` and `{field, state, message}` alone.
That pattern predates `bound_field_context()` and will produce broken HTML (missing
wrappers, wrong ARIA targets, collapsed radio/checkbox groups).

**Always render fields through one of these entry points:**

1. **`{% render_bound_field form field %}`** — inclusion tag in `form_extras.py` (full
   pages, formset rows, wizard steps).
2. **`bound_field_context(form, field, state=…, message=…)`** — used by views that
   return a single field over HTMX (e.g. `field_validate`, signup check URLs).

Both build the full context dict below and pass it to `_field.html`.

| Context key | Role |
|-------------|------|
| `field` | Django `BoundField` |
| `state` | `neutral`, `valid`, or `invalid` |
| `message` | Optional helper or server validation text |
| `field_html` | Widget HTML with `aria-describedby` / `aria-invalid` when appropriate (single controls only) |
| `wrapper_id` | Outer element id (`{field_id}-wrap`) — HTMX swap target for blur validation |
| `message_id` | Live region id (`{field_id}-message`) |
| `use_fieldset` | `True` for `RadioSelect` / `CheckboxSelectMultiple` |

**Grouped choices (`use_fieldset`):** the partial renders `<fieldset id="{{ wrapper_id }}">`
with `<legend>{{ field.label }}</legend>`, options inside the fieldset, and
`aria-describedby` / `aria-invalid` on the **fieldset** (not duplicated on each radio).
**Single controls:** a `<label for="…">` plus a `<div id="{{ wrapper_id }}">` wrapper;
ARIA attributes are on the control via `field_html`.

For grouped widgets, `id_for_label` is empty; ids are derived from `auto_id` so
formset prefixes stay unique (`id_addresses-0-satisfaction-wrap`, etc.).

Adding field HTML elsewhere, or including `_field.html` without the full context, is a
bug. Unit tests assert unique `*-wrap` / `*-message` ids on every demo page and wizard
step.

## Architecture

A fuller diagram (components, HTMX paths, validation layers, CI matrix) lives in
[docs/architecture.md](docs/architecture.md). Design decisions are recorded in
[docs/adr/](docs/adr/) (0001–0007, including
[blur vs full-form validation](docs/adr/0007-single-field-vs-full-form-validation.md)).

```mermaid
flowchart LR
    Request --> View
    View --> Service
    Service --> Registry
    Registry --> Validators
    Validators --> Result["ValidationResult"]
    Result --> FieldPartial["_field.html"]
    Result --> Log["ValidationLog codes only"]
```

## Demo Forms

- Signup: username/email HTMX checks, password strength, confirmation, PhoneField
- Address: country-dependent state and postal validation
- Payment: Luhn, brand detection, CVV and expiry cross-field rules
- Wizard: session-backed three steps; Next/Finish and **Back** swap `#wizard-shell` via HTMX; final revalidation of all steps
- File upload: magic bytes, size/dimension checks; HTMX **per-field scan** (`_field=avatar|resume|supporting_docs`)
- Dynamic formset: HTMX **add-row**; **client-side remove** with prefix reindex (min 1 / max 5 rows); duplicate check only on complete, valid rows
- Survey: mixed widgets, `<fieldset>`/`<legend>` for radio/checkbox groups; `passport_number` only inside `#passport-field`

## Design Notes

The app intentionally avoids persistence for submitted values. `ValidationLog`
stores only `form_name`, `field_name`, `error_code`, and `created_at`, which powers
the stats page without retaining personal data.

## Limitations and real-world replacements

This project teaches **patterns**, not production integrations. Each demo maps to
typical production choices:

| Demo | What the lab does | Typical production replacement |
|------|-------------------|------------------------------|
| **Signup** | Regex username, static reserved-name blocklist (not live availability), domain *shape* check (not DNS), honeypot + time-trap (`started_at` required; malformed timestamp rejected) | Auth provider (e.g. Django auth / OAuth); real username availability API; email verification via SendGrid/Postmark + double opt-in; DNS MX lookup or vendor API (Kickbox, ZeroBounce); [hCaptcha](https://www.hcaptcha.com/) / reCAPTCHA / Turnstile; rate limiting (Redis, CDN/WAF) |
| **Address** | Country-specific regex postal codes | [Google Places](https://developers.google.com/maps/documentation/places/web-service), [Loqate](https://www.loqate.com/), [Smarty](https://www.smarty.com/) for verified addresses |
| **Payment** | Brand detected before Luhn; CVV rules skipped when card number invalid; masked last4 in memory only | [Stripe Elements](https://stripe.com/payments/elements), Braintree, Adyen — card data never touches your server (PCI SAQ A) |
| **Wizard** | Session JSON for step data; HTMX partial navigation (not hardened step tokens) | Signed/encrypted session, or persisted draft (`WizardSession` model) with CSRF and step tokens |
| **File upload** | Per-field HTMX scan (not whole-form); magic-byte sniff (with fallbacks), size/dimension caps | ClamAV/async malware scan; S3/GCS with pre-signed uploads; separate image pipeline (Imgproxy, Cloudinary) |
| **Formset** | In-memory duplicate check; client reindex on row remove (no server delete endpoint) | DB uniqueness constraints, or address normalization service before compare |
| **Survey** | Conditional `clean()` for passport / “other” interest | Same server-side rules, plus client hints; store PII under retention policy if required |

Optional dependency **fallbacks** (`phonenumbers`, `python-magic`) keep the
app runnable in minimal environments; production should install the full stack and
treat fallbacks as dev-only.

## Test and Lint

Pytest settings and coverage thresholds live in **`pyproject.toml`** (`[tool.pytest.ini_options]`,
`[tool.coverage.*]`). Default `pytest` / `make test` excludes the `e2e` marker.

**Unit** (~177 tests, ~97% coverage on `forms_lab`, `e2e` excluded):

```bash
make test          # or: pytest
make lint          # ruff
make coverage
```

Includes HTML id-uniqueness checks for field partials on all demos and wizard steps.

**E2E** (17 Playwright tests — full submit per demo; wizard Next/Finish and **Back**
(HTMX); formset add-row, **middle-row remove with client reindex**, then submit; signup
HTMX blur; page loads; address country swap):

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium   # once per machine
make test-e2e      # or: pytest -m e2e --no-cov
```

**Full CI parity locally** (Postgres via `DATABASE_URL`, `config.settings.ci`; Node for `npm run build`):

```bash
export DATABASE_URL=postgres://postgres:postgres@localhost:5432/form_validation
make test-ci
```

On Windows without `make`, set `DATABASE_URL` and `DJANGO_SETTINGS_MODULE=config.settings.ci`, then run the same commands as the `test-ci` target in the Makefile.

GitHub Actions (`.github/workflows/ci.yml`) on Postgres: `npm ci` + `npm run build`,
`ruff`, unit `pytest`, then `playwright install --with-deps chromium` + `pytest -m e2e --no-cov`.

### HTMX & UI (implemented)

- **Toasts:** `HX-Trigger` JSON events (`fieldValidated`, `cardBrandDetected`) handled in `static/js/forms_lab.js`
- **Spinners:** `#htmx-spinner` via `hx-indicator` on sidebar nav and blur checks
- **Deep links:** sidebar uses `hx-push-url` + `hx-select="#lab-content"`
- **File scan:** each file input POSTs `_field` to `/forms/file-upload/scan/` — validates that field only (optional files before resume do not fail whole form)
- **Upload progress:** `<progress id="upload-progress">` driven by `htmx:xhr:progress`
- **Payment CVV:** brand detect sets `maxLength` on `#id_cvv` via `cardBrandDetected` event
- **Wizard:** Next/Finish POST into `#wizard-shell`; **Back** uses `hx-get` + `hx-select="#wizard-shell"` (session answers preserved, no full-page reload)
- **Formset:** HTMX **add-row** (`POST /forms/formset/add-row/`, capped at `max_num`); **remove** is client-only (`data-formset-remove`) — row deleted in the DOM, prefixes reindexed (`addresses-N-` → contiguous `0…n-1`), `TOTAL_FORMS` synced, Add/Remove buttons respect min/max
- **Accessibility:** radio/checkbox groups use `<fieldset>` / `<legend>` via `_field.html`; `aria-describedby` and `aria-invalid` sit on the **fieldset** for groups and on the **input** (through `field_html`) for single controls — not a blanket “on inputs” rule; **Esc** clears visible inline error text (demo UX)
- **Signup blur:** wired to `/forms/signup/check-username/` and `check-email/` (reserved-name / email rules demo — not a live availability API)

### Front-end assets (in-repo)

| Asset | Command | Output |
|-------|---------|--------|
| Tailwind | `npm run build:css` | `static/css/forms_lab.css` |
| HTMX + Alpine | `npm run build:vendor` | `static/js/vendor/*.min.js` |

Run `npm run build` for both. `tailwind.config.js` scans `templates/`, `apps/**/*.py`,
and `static/js/`. Commit built CSS and vendor JS after changes. Scripts are served
same-origin via `{% static %}` (no unpkg CDN; no SRI needed for first-party static files).

**CI** uses Node 20 (`npm ci` + `npm run build`) before tests.
