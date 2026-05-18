# Architecture

High-level layout of the Form Validation lab. See [README](../README.md) for how to run and test the app.

## System overview

```mermaid
flowchart TB
    subgraph client [Browser]
        Page[Demo form pages]
        HTMX[HTMX partial swaps]
        Alpine[Alpine.js password meter]
    end

    subgraph django [Django — apps.forms_lab]
        Views[views.py]
        Services[services.py]
        FieldVal[field_validation.py]
        Forms[forms/*]
        Fields[fields.py]
        Registry[validators/registry.py]
        Validators[validators/*]
        Results[results.py]
        Log[(ValidationLog)]
    end

    subgraph templates [Templates]
        FieldPartial["forms/_field.html"]
        Partials[forms_lab/partials/*]
    end

    Page --> Views
    HTMX --> Views
    Views --> Services
    Views --> Forms
    Services --> Forms
    Services --> FieldVal
    FieldVal --> Forms
    Forms --> Fields
    Forms --> Registry
    Registry --> Validators
    Services --> Results
    Services --> Log
    Views --> FieldPartial
    Views --> Partials
    Forms --> FieldPartial
```

## Request paths

| Path | Purpose |
|------|---------|
| Full POST | `form_detail` → `validate_and_clean()` → entire form / formset |
| HTMX field blur | `field_validate` → `validate_single_field()` → `clean_form_field()` |
| HTMX helpers | Country change, card brand, wizard step, file scan, formset rows |

## Validation layers

```mermaid
flowchart LR
    L1[Widget / HTML5] --> L2[Field validators]
    L2 --> L3["clean_<field>()"]
    L3 --> L4["clean() cross-field"]
    L4 --> L5[Service serialization + log]

    Registry[(Validator registry)] -.-> L2
    Registry -.-> L3
    Registry -.-> L4
```

## Data retained

Submitted field values are **not** stored. Only `ValidationLog` rows (`form_name`, `field_name`, `error_code`, `created_at`) are persisted for the stats demo.

## CI and tests

| Layer | Command | CI |
|-------|---------|-----|
| Unit + coverage | `pytest` (default excludes `e2e`) | Yes |
| Browser E2E | `pytest -m e2e --no-cov` | Yes (Chromium, `--with-deps` on Linux) |
| CSS build | `npm run build:css` | Yes, before tests |
| Lint | `ruff check apps config` | Yes |

Settings: `config.settings.ci` with Postgres (`DATABASE_URL`). Local quick runs use
`config.settings.dev` (SQLite) via `pyproject.toml` (`[tool.pytest.ini_options]`).
