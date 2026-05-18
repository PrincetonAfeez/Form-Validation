# ADR 0007: Single-Field vs Full-Form Validation

## Status

Accepted.

## Context

The lab supports two server validation paths:

1. **Full-form submit** — `validate_and_clean()` runs `Form.is_valid()` (or formset/wizard
   equivalents), including `clean()` cross-field rules, antispam, and logging.
2. **HTMX single-field blur** — `validate_single_field()` calls `clean_form_field()`,
   which validates one field (plus declared `htmx_field_dependencies`) without running
   `clean()`.

Users get fast feedback on blur, but cross-field and form-level rules only run on
full submit. We need a deliberate split so demos stay responsive without pretending
partial checks are complete.

The file-upload demo also needs incremental feedback when the user picks a file.
An earlier approach ran a whole-form check on scan, which failed optional fields
(e.g. `supporting_docs`) before required ones (e.g. `resume`) were filled — the same
class of false failures blur validation avoids.

## Decision

- Use **single-field cleaning** for HTMX blur/change endpoints (`field_validate`,
  dedicated signup check URLs) and for **file scan** (`file_upload_scan` →
  `validate_file_upload_field()`). These run field validators and `clean_<field>()`
  for the target (and dependency fields where declared), not `clean()`.
- **File scan contract:** the client POSTs `_field` with the input name; the view
  rejects unknown names and validates only that field via `clean_form_field()`.
  Do not call `validate_and_clean()` or `Form.is_valid()` on scan — optional uploads
  must not block scanning a different field.
- Use **full-form validation** for primary submit buttons, wizard steps, and
  `ValidationResult` / stats logging on submit.
- Declare **dependencies** on forms via `htmx_field_dependencies` (e.g. `country`
  before `postal_code`) so partial checks stay coherent.
- Document in the UI that blur and file-scan validation are incremental; the Result
  panel reflects full submit only.

## Consequences

**Pros:** Less work per HTMX request; clear teaching story (field vs form layers);
no false failures on empty sibling fields during blur or file scan.

**Cons:** Honeypot, time-trap, password match, and payment expiry/CVV rules are
invisible until submit unless the user completes the form. Clients must not treat
“Looks good” on one field as “form approved.”

**Mitigations:** E2E tests cover both paths (blur smoke + full submit per demo), run in
CI on every PR/push;
signup reserves username on blur but enforces match/antispam on POST only;
`test_file_upload_scan.py` asserts per-field scan behavior and rejects unknown `_field`.
