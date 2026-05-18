# Architecture Decision Record
## App — Form Validation
**Validation Systems Group | Document 1 of 5**
**Status: Accepted**

---

## Context

The Validation Systems group requires a Django application that demonstrates layered form validation patterns in a realistic, inspectable way. The goal is not to build one production signup form. The goal is to build a form-validation lab that shows how validation rules, custom fields, HTMX partials, accessibility markup, field-level checks, full-form checks, formsets, file validation, and wizard state can fit together in one coherent Django project.

The app includes multiple demos: signup, address, payment, wizard, file upload, dynamic formset, and survey. Each demo exists to teach a different validation pattern. The system also includes a validator registry and a reference page so validation logic can be introspected rather than hidden inside scattered functions.

The decision was to implement the app as a Django 5 monolith with server-rendered templates, HTMX partial swaps, Alpine.js for small client-side UI behavior, self-hosted frontend assets, custom form fields, a validation service layer, privacy-preserving validation logs, and a CI pipeline that runs unit tests, coverage, linting, frontend build, migration checks, and Playwright E2E tests.

---

## Decisions

### Decision 1 — Django forms as the primary validation engine

**Chosen:** Build every demo around Django `forms.Form`, formsets, custom fields, `clean_<field>()`, `clean()`, and validators.

**Rejected:** A JavaScript-first validation library, a REST API validation layer, or hand-rolled request parsing.

**Reason:** Django forms expose the exact layered validation model this app is meant to teach: widget input, field cleaning, validators, `clean_<field>()`, form-level `clean()`, and error rendering. This keeps validation close to the server rules that actually protect data.

---

### Decision 2 — Validation lab over production integration

**Chosen:** Build a portfolio-style validation lab with realistic demos and documented production replacements.

**Rejected:** Directly integrating Stripe, Google Places, email verification APIs, hCaptcha, ClamAV, or external address-verification services.

**Reason:** The app teaches patterns. It intentionally avoids making real payment, identity, address, email, or malware-scanning integrations part of the demo. The README maps each lab behavior to likely production replacements, keeping the project honest about what is simulated and what is production-grade.

---

### Decision 3 — HTMX partials for validation feedback

**Chosen:** Use HTMX for field blur checks, country-dependent swaps, card brand detection, wizard steps, file scans, formset row insertion, survey passport toggling, toasts, spinners, and deep links.

**Rejected:** Full-page-only validation or a JavaScript SPA.

**Reason:** Validation UX benefits from local feedback. HTMX lets the server remain authoritative while returning only the field, panel, or step that changed. This keeps the frontend small and makes the backend validation path visible.

---

### Decision 4 — Single-field validation is not full-form validation

**Chosen:** `validate_single_field()` uses `clean_form_field()` to validate one field plus declared HTMX dependencies. It deliberately avoids full `clean()`.

**Rejected:** Running the entire form on every blur event.

**Reason:** Field blur validation should answer “is this field valid right now?” not “is the whole form complete?” Full-form cross-field rules still run on final submit. The architecture document explicitly separates field blur, file scan, full POST, wizard step, and wizard final revalidation paths.

---

### Decision 5 — Central field partial contract

**Chosen:** All field markup flows through `templates/forms/_field.html` via `{% render_bound_field form field %}` or `bound_field_context()`.

**Rejected:** Bare includes of `_field.html` with only `{field, state, message}` or one-off field markup in templates.

**Reason:** The field partial owns wrappers, unique IDs, live regions, ARIA targets, radio/checkbox fieldsets, labels, messages, and HTMX targets. Centralizing this avoids inconsistent markup and accessibility regressions. The README calls bare includes a bug because they omit required wrapper and ARIA context.

---

### Decision 6 — Validator registry for introspection

**Chosen:** Validators register themselves with names, descriptions, layers, and examples through a registry.

**Rejected:** Anonymous validator functions with no central metadata.

**Reason:** A validation lab should be able to explain its own rules. The registry powers validator reference views and demo rule lists. Forms declare `validator_names` so the UI can show which rules a demo is using.

---

### Decision 7 — Privacy-preserving validation logs

**Chosen:** Store only `form_name`, `field_name`, `error_code`, and `created_at` in `ValidationLog`.

**Rejected:** Persisting submitted field values or full form payloads.

**Reason:** The stats page needs aggregate validation failures, not personal data. Logging only error codes demonstrates observability without retaining passwords, CVV, passport numbers, uploaded file contents, or personal form submissions.

---

### Decision 8 — Optional dependency fallbacks

**Chosen:** Include fallbacks for optional local dependencies such as `django-htmx`, `phonenumbers`, and `python-magic`.

**Rejected:** Failing hard in constrained demo environments.

**Reason:** The project is a portfolio/demo app. It should be easy to run locally even when optional packages or native libraries are missing. Production should still install the full stack, but fallbacks keep development friction low.

---

### Decision 9 — Self-host HTMX and Alpine assets

**Chosen:** Pin HTMX and Alpine through npm and copy them into `static/js/vendor/`; compile Tailwind to `static/css/forms_lab.css`.

**Rejected:** CDN-hosted scripts.

**Reason:** Same-origin static assets support stronger deployment discipline, avoid CDN runtime dependency, and keep CI able to verify built artifacts. The README explicitly notes that scripts are served first-party, so SRI is not needed for those local static files.

---

### Decision 10 — PostgreSQL CI parity with SQLite local convenience

**Chosen:** Local development uses SQLite by default; CI runs against PostgreSQL through `DATABASE_URL` and `config.settings.ci`.

**Rejected:** SQLite everywhere or requiring PostgreSQL for all local runs.

**Reason:** SQLite keeps local demos easy. PostgreSQL CI catches production-class database behavior. The CI settings file refuses to run without `DATABASE_URL`, making the parity path explicit.

---

## Consequences

**Positive:**
- The project demonstrates layered validation rather than one isolated form.
- Demos are discoverable through a centralized demo registry.
- HTMX makes validation feedback interactive while preserving server authority.
- `_field.html` creates consistent accessible field markup.
- Validator metadata powers rule reference pages.
- `ValidationLog` supports stats without storing sensitive data.
- Production settings harden cookies/static/security behavior.
- CI verifies frontend assets, migrations, unit tests, coverage, linting, and E2E behavior.

**Negative / Trade-offs:**
- The app has many demos, endpoints, partials, and validators, which increases maintenance cost.
- Single-field validation can confuse contributors unless they understand that form-level `clean()` is not run on blur.
- Formset removal is client-side and requires careful prefix reindexing.
- The project teaches patterns, not direct production integrations.
- Optional fallbacks are useful for demos but should not be mistaken for full production replacements.
- SQLite local and PostgreSQL CI/production are intentionally different.

---

## Alternatives Not Explored

- **React form builder:** Rejected because the point is Django server validation, not client state management.
- **API-only validation service:** Rejected because templates and field partial contracts are central to the lesson.
- **Persistent submitted examples:** Rejected for privacy and scope.
- **External production services:** Deferred because this is a validation-pattern lab.
- **All validation on blur:** Rejected because full form validation and field validation have different semantics.

---

*Constitution reference: Article 1 (Python fundamentals and architecture), Article 3.4 (medium project classification), Article 4 (engineering quality), Article 6 (verification), and Article 7 (progressive complexity).*

---


# Technical Design Document
## App — Form Validation
**Validation Systems Group | Document 2 of 5**

---

## Overview

Form Validation is a Django 5 validation showcase. It demonstrates custom fields, validator functions, validator introspection, HTMX partials, field-level validation, cross-field validation, session-backed wizard state, file-upload scanning, dynamic formsets, grouped-field accessibility, and privacy-preserving validation telemetry.

**Project package:** `config`  
**Primary app:** `apps.forms_lab`  
**Default local settings:** `config.settings.dev`  
**CI settings:** `config.settings.ci`  
**Production settings:** `config.settings.prod`  
**Local database:** SQLite  
**CI/production database:** PostgreSQL-ready through `DATABASE_URL`  
**Frontend:** Django templates, HTMX, Alpine.js, compiled Tailwind CSS  
**Telemetry model:** `ValidationLog`

---

## System Data Flow

```text
Browser
  ├── full page form POST
  ├── HTMX blur check
  ├── HTMX dependent field swap
  ├── HTMX wizard step
  ├── HTMX file scan
  └── HTMX formset add-row
       │
       ▼
apps.forms_lab.views
       │
       ├── services.validate_and_clean()
       ├── services.validate_single_field()
       ├── services.validate_file_upload_field()
       ├── build_artifact()
       └── direct partial rendering
       │
       ▼
Django forms / formsets / custom fields
       │
       ├── fields.PhoneField
       ├── validators.registry
       ├── validators.address
       ├── validators.payment
       ├── validators.files
       ├── validators.text
       ├── validators.email_rules
       ├── validators.antispam
       └── form clean()/clean_<field>()
       │
       ▼
ValidationResult + templates/forms/_field.html + partial templates
       │
       └── ValidationLog rows for invalid full submissions
```

---

## Module-Level Structure

```text
Form-Validation/
  manage.py
  config/
    settings/
      base.py
      dev.py
      prod.py
      ci.py
    urls.py
    wsgi.py
    asgi.py
  apps/forms_lab/
    models.py
    urls.py
    views.py
    services.py
    field_validation.py
    fields.py
    mixins.py
    middleware.py
    results.py
    context_processors.py
    forms/
      __init__.py
      signup.py
      address.py
      payment.py
      wizard.py
      file_upload.py
      formset.py
      survey.py
    validators/
      __init__.py
      registry.py
      address.py
      antispam.py
      email_rules.py
      files.py
      payment.py
      phone.py
      strength.py
      text.py
    templatetags/
      form_extras.py
    tests/
  templates/
    forms/_field.html
    forms_lab/
  static/
    src/forms_lab.input.css
    css/forms_lab.css
    js/forms_lab.js
    js/vendor/
  docs/
    architecture.md
    adr/
  package.json
  requirements.txt
  requirements-dev.txt
  pyproject.toml
  Makefile
```

---

## Component Dependency Graph

```text
config.urls
  └── apps.forms_lab.urls

apps.forms_lab.urls
  └── apps.forms_lab.views

views.py
  ├── forms.DEMOS / WIZARD_STEPS
  ├── forms.address.AddressForm
  ├── forms.file_upload.FileUploadForm
  ├── forms.formset.PreviousAddressFormSet
  ├── forms.survey.SurveyForm
  ├── services.build_artifact
  ├── services.validate_and_clean
  ├── services.validate_single_field
  ├── services.validate_file_upload_field
  ├── templatetags.form_extras.bound_field_context
  ├── validators.describe / all_validators
  ├── validators.payment.detect_card_brand
  └── models.ValidationLog

services.py
  ├── forms.DEMO_BY_SLUG
  ├── forms.PreviousAddressFormSet
  ├── field_validation.clean_form_field
  ├── models.ValidationLog
  └── results.ValidationResult

forms/*
  ├── django.forms
  ├── mixins.HTMXFormMixin / TailwindFormMixin
  ├── fields.PhoneField
  └── validators/*

validators/*
  └── validators.registry.register

templates/forms/_field.html
  └── form_extras.bound_field_context / render_bound_field
```

---

## Core Data Structures

### `ValidationLog`

```python
class ValidationLog(models.Model):
    form_name = models.CharField(max_length=64)
    field_name = models.CharField(max_length=64, blank=True, null=True)
    error_code = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
```

Indexes:
- `form_name`, `field_name`, `error_code`
- `created_at`

Purpose:
- powers validation stats
- avoids storing submitted user values

---

### `DemoDefinition`

```python
@dataclass(frozen=True)
class DemoDefinition:
    slug: str
    title: str
    kind: str
    form_class: Any | None
    demonstrates: tuple[str, ...]
    validator_names: tuple[str, ...]
```

Registered demos:
- signup
- address
- payment
- wizard
- file-upload
- formset
- survey

---

### `ValidationResult`

```python
@dataclass
class ValidationResult:
    form_name: str
    is_valid: bool
    cleaned_data: dict[str, Any]
    errors: dict[str, list[str]]
    form: Any | None
    message: str
```

Used by full submit and file-scan paths to carry form state, cleaned data, error dictionaries, and user-facing messages.

---

### `ValidatorInfo`

```python
@dataclass(frozen=True)
class ValidatorInfo:
    name: str
    callable: Callable
    description: str
    layer: str
    examples: tuple[str, ...]
```

Stored in an ordered registry. Used by reference pages and demo rule lists.

---

### `PhoneField`

Custom `forms.CharField` that normalizes phone input into E.164 form. It uses `phonenumbers` when available and falls back to regex/digit normalization when not installed.

---

## Form Demo Reference

### Signup

Features:
- username regex
- reserved username blocklist
- email validators
- password strength validator
- password confirmation
- `PhoneField`
- honeypot
- time trap
- HTMX username/email blur checks
- Alpine password strength meter attributes

Sensitive cleaned data redacted by service serialization:
- password
- confirm_password

---

### Address

Features:
- country choices: US, CA, GB
- country-dependent state/province choices
- country-aware postal-code validation
- Canadian postal-code normalization
- HTMX country change partial
- HTMX postal-code validation with country dependency

---

### Payment

Features:
- card number normalization
- card brand detection
- Luhn checksum
- masked last four return value
- expiry month/year validation
- brand-specific CVV validation
- HTMX card brand detection event

Important behavior:
- CVV validation is skipped when the card number is already invalid.
- Cleaned card number is masked.

---

### Wizard

Features:
- three step forms
- session-backed `wizard_state`
- per-step validation before moving forward
- HTMX step partial swaps
- Back navigation through `form_detail?step=N`
- final revalidation of all session steps

---

### File Upload

Features:
- avatar optional image
- resume required PDF
- supporting docs multiple file field
- per-file size validation
- magic-byte validation
- image dimension checks for images
- HTMX per-field file scan through `_field`

---

### Dynamic Formset

Features:
- Django formset with management form
- min 1 row
- max 5 rows
- HTMX add row
- client-side remove with prefix reindex
- duplicate previous address validation
- per-row postal validation

---

### Survey

Features:
- radio satisfaction
- checkbox interests
- other-option rule
- date/time/color/range widgets
- optional phone normalization
- passport conditional field
- no-HTML and profanity text validators
- HTMX passport reveal/hide
- fieldset/legend accessibility for grouped controls

---

## Function Reference

### `get_demo(slug)`

Returns a demo definition from `DEMO_BY_SLUG`; raises `ObjectDoesNotExist` if missing.

---

### `build_artifact(slug, data=None, files=None, step=1, initial=None)`

Builds the appropriate artifact:
- formset for `formset`
- step form for `wizard`
- regular form for ordinary demos

---

### `validate_and_clean(slug, payload, files=None)`

Runs full form/formset validation.

If valid:
- serializes cleaned data
- redacts sensitive fields

If invalid:
- collects errors
- logs error codes to `ValidationLog`

Returns `ValidationResult`.

---

### `validate_single_field(slug, field_name, payload, files=None)`

Builds a form, validates one field through `clean_form_field()`, and returns:
- form
- bound field
- state: `valid` or `invalid`
- message

---

### `validate_file_upload_field(field_name, payload, files=None)`

Validates one file-upload field only. This prevents optional missing file fields from failing a scan for another field.

---

### `clean_form_field(form, field_name)`

Validates one bound field plus declared `htmx_field_dependencies`.

Steps:
1. ensure field exists
2. clean dependencies first
3. run field clean
4. run `clean_<field>()` if present
5. return cleaned value and first error message

Does not run full `form.clean()`.

---

### `bound_field_context(form, field, state=None, message=None)`

Builds the full context expected by `_field.html`:
- wrapper id
- message id
- field HTML
- state
- message
- `use_fieldset`

Uses fieldset behavior for `RadioSelect` and `CheckboxSelectMultiple`.

---

### `render_bound_field(form, field)`

Template inclusion tag that renders `_field.html` with complete context.

---

### `detect_card_brand(value)`

Detects:
- amex
- visa
- mastercard
- discover
- unknown

---

### `validate_luhn(value)`

Validates card numbers using Luhn checksum after stripping separators.

---

### `collect_errors(artifact)`

Normalizes form or formset errors into a dictionary.

---

### `log_validation_errors(slug, artifact)`

Converts validation errors into `ValidationLog` rows and bulk creates them. Database failures are logged as warnings, not raised to the user.

---

## Error Handling Strategy

- Unknown demo slug raises 404.
- Unknown single-field name raises 404.
- Unknown file-scan field raises 404.
- Invalid wizard step raises 404.
- Full validation failure returns a rendered form with errors and records validation log rows.
- Field validation failure returns `_field.html` with invalid state and message.
- Formset add-row at max row count returns 204.
- ValidationLog database write errors are caught and logged as warnings.
- Production settings fail fast if `SECRET_KEY` remains the dev placeholder.

---

## External Dependencies

### Runtime

| Dependency | Purpose |
|---|---|
| Django | Web framework and form system |
| django-htmx | Optional HTMX request middleware |
| django-environ | Environment parsing |
| phonenumbers | Phone normalization |
| python-magic | MIME/magic-byte support |
| Pillow | Image dimension checks |
| psycopg | PostgreSQL driver |
| whitenoise | Production static file serving |

### Development / Testing

| Dependency | Purpose |
|---|---|
| pytest | Unit test runner |
| pytest-django | Django pytest integration |
| pytest-cov / coverage | Coverage enforcement |
| hypothesis | Property-style testing support |
| Playwright / pytest-playwright | Browser E2E tests |
| ruff | Linting |
| black | Formatting |

### Node

| Dependency | Purpose |
|---|---|
| tailwindcss | CSS build |
| htmx.org | Vendored HTMX file |
| alpinejs | Vendored Alpine file |

---

## Concurrency Model

The app is a synchronous Django application. It uses normal request/response processing and database writes. There are no background workers, task queues, websockets, or async views. CI and E2E tests exercise the synchronous paths with PostgreSQL and Chromium.

---

## Known Limitations

- Demo validations are educational, not replacements for production vendors.
- Signup availability is a reserved-name demo, not a real account lookup.
- Email checks are domain-shape oriented, not full deliverability verification.
- Payment demo does not process real cards and should be replaced by Stripe/Braintree/Adyen in production.
- File scan is not malware scanning.
- Formset row removal is client-side and depends on JS reindexing.
- Wizard state is session JSON and not hardened with signed step tokens.
- Optional dependency fallbacks are intended for constrained local demos, not production.

---

## Verification Summary

The project verifies:
- validation rules through unit tests
- field partial wrapper/message id uniqueness
- wizard step behavior
- HTMX field blur behavior
- file scan paths
- formset add/remove/reindex behavior
- accessibility behavior for grouped controls
- Playwright E2E flows
- frontend build artifacts
- PostgreSQL CI execution
- coverage threshold through pytest configuration

---

*Constitution reference: Article 4 (engineering quality), Article 6 (behavior verification), Article 7 (progressive complexity), and Article 8 (valid learner work).*

---


# Interface Design Specification
## App — Form Validation
**Validation Systems Group | Document 3 of 5**

---

## Public Web Interface

| Method | Path | View | Description |
|---|---|---|---|
| `GET` | `/` | `index` | Demo index |
| `GET/POST` | `/forms/<slug>/` | `form_detail` | Full demo page and full submit |
| `POST` | `/forms/<slug>/field/<name>/` | `field_validate` | HTMX single-field validation |
| `POST` | `/forms/signup/check-username/` | `signup_check_username` | Signup username blur check |
| `POST` | `/forms/signup/check-email/` | `signup_check_email` | Signup email blur check |
| `POST` | `/forms/address/country-change/` | `address_country_change` | Re-render dependent country fields |
| `POST` | `/forms/payment/brand-detect/` | `payment_brand_detect` | Card brand panel + HX trigger |
| `POST` | `/forms/wizard/step/<n>/` | `wizard_step` | Wizard next/finish step |
| `POST` | `/forms/file-upload/scan/` | `file_upload_scan` | One file field scan |
| `POST` | `/forms/formset/add-row/` | `formset_add_row` | Add formset row |
| `POST` | `/forms/survey/toggle-passport/` | `survey_toggle_passport` | Passport dependent field partial |
| `GET` | `/stats/` | `stats` | Validation failure stats |
| `GET` | `/reference/` | `reference` | Validator reference |
| any | `/admin/` | Django admin | Admin |

---

## Invocation Syntax

### Local run

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

### Frontend build

```bash
npm install
npm run build
```

Equivalent subcommands:

```bash
npm run build:css
npm run build:vendor
```

Outputs:
- `static/css/forms_lab.css`
- `static/js/vendor/htmx.min.js`
- `static/js/vendor/alpine.min.js`

---

### Production static and migration sequence

```bash
export SECRET_KEY=...
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py collectstatic --noinput
python manage.py migrate
```

---

## Demo Slugs

| Slug | Kind | Description |
|---|---|---|
| `signup` | form | Username, email, password, phone, antispam |
| `address` | form | Country-dependent address validation |
| `payment` | form | Card brand, Luhn, CVV, expiry |
| `wizard` | wizard | Three-step session-backed wizard |
| `file-upload` | form | File scan, size, MIME, image dimensions |
| `formset` | formset | Dynamic previous-address formset |
| `survey` | form | Mixed widgets and conditional fields |

---

## Field Partial Contract

`templates/forms/_field.html` requires the full context built by:

```django
{% render_bound_field form field %}
```

or:

```python
bound_field_context(form, field, state="valid", message="Looks good.")
```

Required context keys:
- `form`
- `field`
- `field_html`
- `wrapper_id`
- `message_id`
- `state`
- `message`
- `use_fieldset`

States:
```text
neutral
valid
invalid
```

Grouped widgets use `<fieldset>` and `<legend>` with ARIA attributes on the fieldset. Single controls use label + wrapper with ARIA attributes on the control.

---

## Input Contract

### Full form submit

Endpoint:

```text
POST /forms/<slug>/
```

Accepts normal Django form data for the selected demo. File upload accepts `multipart/form-data`.

Result:
- valid: success message and cleaned-data display
- invalid: form errors and validation log rows

---

### Single field validation

Endpoint:

```text
POST /forms/<slug>/field/<name>/
```

Accepts the current form payload. Only the named field and declared dependencies are cleaned.

Result:
- `_field.html` partial
- `HX-Trigger` JSON event named `fieldValidated`

---

### File scan

Endpoint:

```text
POST /forms/file-upload/scan/
```

Required POST value:

```text
_field=avatar|resume|supporting_docs
```

Encoding:

```text
multipart/form-data
```

Validates only that field.

---

### Wizard

Endpoint:

```text
POST /forms/wizard/step/<n>/
```

Valid steps:
```text
1, 2, 3
```

Step data is stored in session as `wizard_state`. Step 3 revalidates all prior steps.

---

### Formset add row

Endpoint:

```text
POST /forms/formset/add-row/
```

Reads:

```text
addresses-TOTAL_FORMS
```

Returns:
- new row partial when under max
- 204 when at max

---

## Output Contract

### Field validation response

Headers include:

```text
HX-Trigger: {"fieldValidated": {"field": "...", "state": "valid|invalid", "message": "..."}}
```

Body:
- rendered `forms/_field.html`

---

### Payment brand response

Headers include:

```text
HX-Trigger: {"cardBrandDetected": {"cvvLength": 3|4, "brand": "..."}}
```

Body:
- rendered payment brand partial

---

### Stats page

Renders top validation failures grouped by:
- form name
- field name
- error code
- count

---

### Reference page

Renders all validator registry entries with metadata.

---

## Exit Code Reference

| Command | Success | Failure |
|---|---:|---:|
| `python manage.py runserver` | 0 on clean exit | non-zero on import/config error |
| `python manage.py migrate` | 0 | non-zero on DB/migration failure |
| `python manage.py collectstatic` | 0 | non-zero on static config error |
| `pytest` | 0 | non-zero on test failure or coverage failure |
| `pytest -m e2e --no-cov` | 0 | non-zero on E2E failure |
| `ruff check apps config` | 0 | non-zero on lint failure |
| `black --check .` | 0 | non-zero on formatting failure |
| `npm run build` | 0 | non-zero on Node/Tailwind/vendor-copy failure |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Operationally | Selects settings module |
| `SECRET_KEY` | Required in prod | Production refuses placeholder secret |
| `DEBUG` | No | Debug toggle |
| `ALLOWED_HOSTS` | Prod | Comma-separated hosts |
| `DATABASE_URL` | CI/prod | PostgreSQL URL |
| `POSTGRES_DB` | Optional fallback | Used when DATABASE_URL is Postgres without django-environ parsing |
| `POSTGRES_USER` | Optional fallback | Postgres user |
| `POSTGRES_PASSWORD` | Optional fallback | Postgres password |
| `POSTGRES_HOST` | Optional fallback | Postgres host |
| `POSTGRES_PORT` | Optional fallback | Postgres port |
| `SECURE_SSL_REDIRECT` | Prod optional | HTTPS redirect toggle |

---

## Configuration Files

### `requirements.txt`

Runtime dependencies for Django, HTMX middleware, environment parsing, phone validation, magic-byte support, image support, PostgreSQL, and WhiteNoise.

---

### `requirements-dev.txt`

Includes runtime plus pytest, coverage, Hypothesis, Playwright, Ruff, and Black.

---

### `package.json`

Scripts:
- `build:css`
- `build:vendor`
- `build`

Pinned frontend dependencies:
- Alpine.js
- HTMX
- Tailwind CSS

---

### `pyproject.toml`

Configures:
- Python range
- package metadata
- Black
- Ruff
- pytest
- coverage
- E2E marker

---

## Side Effects

| Operation | Side Effect |
|---|---|
| Invalid full submit | Writes `ValidationLog` rows |
| Wizard step valid | Writes serialized step data to session |
| Wizard final submit | Revalidates all session steps |
| File scan | Validates uploaded file field but does not persist files |
| Formset add row | Returns a new row partial |
| Formset remove | Client deletes DOM row and reindexes prefixes |
| `npm run build` | Rewrites CSS/vendor static assets |
| Production static collection | Writes collected static files to `staticfiles/` |

---

## Usage Examples

### Signup blur validation

```text
POST /forms/signup/check-username/
```

Returns a rendered username field with state and message.

---

### Address country swap

```text
POST /forms/address/country-change/
country=CA
```

Returns dependent state/province and postal field partials.

---

### Payment brand detection

```text
POST /forms/payment/brand-detect/
card_number=378282246310005
```

Returns brand panel and `cardBrandDetected` trigger with CVV length 4.

---

### File scan

```text
POST /forms/file-upload/scan/
_field=resume
```

Validates only the resume file field.

---

### Wizard completion

```text
POST /forms/wizard/step/3/
```

Validates step 3 and then revalidates all session-stored wizard steps.

---

*Constitution reference: Article 4 (clear input/output boundaries), Article 6 (verification), and Article 8 (understandable and verifiable work).*

---


# Runbook
## App — Form Validation
**Validation Systems Group | Document 4 of 5**

---

## Requirements

### Local

- Python 3.12+
- pip
- virtual environment support
- SQLite
- Node 20+ and npm if rebuilding assets

### CI / production parity

- PostgreSQL 16
- `DATABASE_URL`
- Node 20
- Playwright Chromium for E2E

### Production

- non-placeholder `SECRET_KEY`
- `DJANGO_SETTINGS_MODULE=config.settings.prod`
- `collectstatic` run before serving
- WhiteNoise installed

---

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
npm install
npm run build
python manage.py migrate
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

## Running Tests

### Default unit/coverage suite

```bash
pytest
```

Default pytest excludes E2E through the configured marker expression.

---

### Lint

```bash
ruff check apps config
```

---

### Coverage

```bash
pytest --cov=apps.forms_lab --cov-report=term-missing
```

The configured threshold is 85%.

---

### E2E

```bash
python -m playwright install chromium
pytest -m e2e --no-cov
```

---

### CI parity with PostgreSQL

```bash
export DATABASE_URL=postgres://postgres:postgres@localhost:5432/form_validation
export DJANGO_SETTINGS_MODULE=config.settings.ci
npm run build
python manage.py migrate --noinput
ruff check apps config
pytest
pytest -m e2e --no-cov
```

---

## Production Setup

```bash
export SECRET_KEY=...
export DJANGO_SETTINGS_MODULE=config.settings.prod
python manage.py collectstatic --noinput
python manage.py migrate
```

Production fails if `SECRET_KEY` is missing or equal to `dev-only-change-me`.

---

## Standard Operating Procedures

### Add a new demo

1. Create a form module under `apps/forms_lab/forms/`.
2. Add validators or reuse registry functions.
3. Add `validator_names` and `demonstrates` metadata.
4. Register the form in `forms/__init__.py` through `DemoDefinition`.
5. Add templates or partials.
6. Add tests for form validation, field partial IDs, and E2E if interactive.
7. Update documentation/reference text.

---

### Add a validator

1. Implement the validator in `apps/forms_lab/validators/`.
2. Decorate it with `@register(...)` or call `register_callable(...)`.
3. Give it a stable name, layer, description, and examples.
4. Add it to a form’s `validator_names` where relevant.
5. Add unit tests and reference-page coverage.

---

### Modify field rendering

1. Edit `templates/forms/_field.html`.
2. Keep `bound_field_context()` contract intact.
3. Preserve unique `wrapper_id` and `message_id` behavior.
4. Preserve fieldset behavior for radio/checkbox groups.
5. Run unit tests and E2E tests.

---

### Rebuild frontend assets

```bash
npm run build
```

Verify:

```bash
test -f static/css/forms_lab.css
test -f static/js/vendor/htmx.min.js
test -f static/js/vendor/alpine.min.js
```

---

## Health Checks

### App loads

```text
GET /
```

Healthy:
- 200 OK
- demo list visible

---

### Demo loads

```text
GET /forms/signup/
GET /forms/address/
GET /forms/payment/
GET /forms/wizard/
GET /forms/file-upload/
GET /forms/formset/
GET /forms/survey/
```

Healthy:
- 200 OK
- form visible
- field wrappers have unique IDs

---

### Field validation works

```text
POST /forms/signup/check-username/
```

Healthy:
- 200 OK
- `_field.html` partial returned
- `HX-Trigger` includes `fieldValidated`

---

### Stats works

```text
GET /stats/
```

Healthy:
- top validation failures render from `ValidationLog`

---

### Reference works

```text
GET /reference/
```

Healthy:
- validator registry entries render

---

## Expected Output Samples

### Field validation trigger

```json
{
  "fieldValidated": {
    "field": "username",
    "state": "invalid",
    "message": "That username is unavailable."
  }
}
```

---

### Card brand trigger

```json
{
  "cardBrandDetected": {
    "cvvLength": 4,
    "brand": "amex"
  }
}
```

---

### Validation log string

```text
signup.username: unavailable
```

---

## Known Failure Modes

### Production refuses to start

**Trigger:** `SECRET_KEY` missing or still set to `dev-only-change-me`.

**Resolution:** Set a unique production secret.

---

### CI settings fail immediately

**Trigger:** `config.settings.ci` used without `DATABASE_URL`.

**Resolution:** Set PostgreSQL `DATABASE_URL`.

---

### Field partial renders broken markup

**Trigger:** Bare include of `_field.html` without full context.

**Resolution:** Use `{% render_bound_field form field %}` or `bound_field_context()`.

---

### Postal code blur fails because country is missing

**Trigger:** Single-field validation without required dependency data.

**Resolution:** Ensure dependency fields are included in HTMX payload; `htmx_field_dependencies` cleans country first.

---

### Formset duplicate check misses or misfires

**Trigger:** Client remove did not reindex prefixes or `TOTAL_FORMS` correctly.

**Resolution:** Verify JS reindexing and management form state.

---

### File scan validates too much

**Trigger:** Calling full form validation instead of `validate_file_upload_field()`.

**Resolution:** Use `/forms/file-upload/scan/` with `_field`.

---

### E2E fails locally

**Trigger:** Playwright Chromium not installed.

**Resolution:**

```bash
python -m playwright install chromium
```

---

## Troubleshooting Decision Tree

```text
Page does not load
  ├── Django settings wrong?
  │     └── use config.settings.dev locally
  ├── migrations missing?
  │     └── python manage.py migrate
  └── static build missing?
        └── npm run build

Field validation broken
  ├── Wrong field partial entry point?
  │     └── use render_bound_field or bound_field_context
  ├── Missing HTMX payload dependency?
  │     └── include dependent fields
  └── Unknown field/demo?
        └── check URL slug/name

Production broken
  ├── Placeholder SECRET_KEY?
  │     └── set real SECRET_KEY
  ├── Static files missing?
  │     └── collectstatic
  └── Database URL missing?
        └── configure DATABASE_URL

CI broken
  ├── Node assets missing?
  │     └── npm ci && npm run build
  ├── Postgres not available?
  │     └── check DATABASE_URL/service
  ├── Lint failure?
  │     └── ruff check apps config
  └── E2E browser missing?
        └── playwright install --with-deps chromium
```

---

## Maintenance Notes

- Keep submitted values out of persistent logs.
- Keep sensitive serialization redaction list updated.
- Preserve field partial contract and ARIA behavior.
- Add validators through the registry.
- Keep full-submit validation separate from blur validation.
- Run E2E tests after changing HTMX flows.
- Rebuild and commit CSS/vendor assets after frontend dependency changes.
- Treat optional fallbacks as local convenience, not production substitutes.
- Keep README production replacement table current.

---

*Constitution reference: Article 6 (behavior verification), Article 5 (constraints and trade-offs), and Article 8 (verifiable learner work).*

---


# Lessons Learned
## App — Form Validation
**Validation Systems Group | Document 5 of 5**

---

## Why This Design Was Chosen

This design was chosen because form validation is easier to misunderstand than it first appears. A single signup form would not show enough. The app needed to show field validators, form-level rules, cross-field rules, dependency-aware blur validation, file validation, grouped-widget accessibility, formset management, session-backed wizard state, and validation telemetry.

Django forms were the right foundation because they already model this layered behavior. HTMX was the right interaction layer because validation feedback can be local and responsive without moving the source of truth into JavaScript. The validator registry was added so the app can explain itself, not just validate input.

The most important architectural distinction is between full-form validation and single-field validation. Blur checks should not produce whole-form required errors. Full submit should still run every form-level rule. Separating these paths is the difference between a useful validation UI and a noisy one.

---

## What Was Intentionally Omitted

**Real account availability:** Signup checks use reserved-name logic, not a live user table.

**Email deliverability API:** Email validation demonstrates shape/disposable/domain-style checks, not real inbox verification.

**Real payment processing:** Payment validation teaches Luhn, brand, CVV, and expiry rules; production should use Stripe Elements or equivalent.

**Malware scanning:** File upload uses size, magic bytes, and dimensions; production should use antivirus or asynchronous scanning.

**Persistent submitted values:** The app stores error codes only.

**Server-side formset row deletion endpoint:** Removal is client-side with prefix reindexing.

**Hardened wizard tokens:** Wizard state uses session JSON, appropriate for the demo but not hardened as a production onboarding flow.

---

## Biggest Weakness

The biggest weakness is conceptual complexity. The app intentionally shows many validation patterns at once. That is useful for a portfolio lab, but future contributors must understand which layer they are changing: validator, field, form, service, view, partial, HTMX event, or client-side reindexing.

The second weakness is the field partial contract. Centralizing markup is the right decision, but it means every caller must use the correct rendering entry point. A bare include can silently break wrapper IDs, messages, and ARIA behavior. The README and tests reduce that risk, but do not eliminate it.

The third weakness is that several demos intentionally simulate production behaviors. That is acceptable because the README names the real-world replacements, but the distinction must remain clear.

---

## Scaling Considerations

**If more demos are added:**
- Add a `DemoDefinition` entry.
- Keep validator metadata complete.
- Add field partial ID tests.
- Add E2E coverage for unique interaction patterns.

**If the lab becomes production validation infrastructure:**
- Replace simulated rules with external services.
- Add rate limiting.
- Add audit and privacy documentation.
- Add stricter storage/retention rules.
- Add real malware scanning for uploads.

**If validators grow:**
- Group registry entries by domain.
- Add version metadata.
- Add reference-page filters.
- Consider validator examples as executable tests.

**If HTMX complexity grows:**
- Create more response helpers.
- Keep full submit and field submit paths documented.
- Add snapshot tests for partial contracts.

---

## What the Next Refactor Would Be

1. **Add schema-style documentation for every demo** — list fields, dependencies, full-submit rules, HTMX-only routes, and redaction behavior.

2. **Create a shared HTMX response helper** — reduce repeated header/partial logic in views.

3. **Add validator registry grouping** — make the reference page easier to browse by layer and domain.

4. **Add automated field partial contract tests for new forms** — fail fast when a new demo breaks wrapper/message ID rules.

5. **Add optional rate limiting** — especially around file scans and field blur endpoints if the app becomes public.

---

## What This Project Taught

- **Validation is layered.** Widget constraints, field validators, custom fields, `clean_<field>()`, `clean()`, formsets, and service serialization all have different jobs.

- **Blur validation should be scoped.** Running full-form validation on every field blur creates noisy UX and false failures.

- **Accessibility belongs in the rendering contract.** Radio and checkbox groups need fieldsets and legends; ARIA behavior cannot be an afterthought.

- **Logging can be useful without storing sensitive data.** Error-code telemetry supports stats while respecting privacy.

- **HTMX is effective when the server owns validation.** The server returns field partials, panels, and steps; the browser swaps them.

- **Demo apps need honesty.** The README’s “real-world replacements” table makes clear which parts are teaching tools and which would need production services.

- **Tests protect architecture.** Coverage, E2E flows, ID uniqueness checks, and CI asset checks keep the many small pieces from drifting.

---

*Constitution v2.0 checklist: This document satisfies Article 5 (trade-off documentation), Article 6 (verification), and Article 7 (progressive complexity) for Form Validation.*
