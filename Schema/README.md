# Form Validation Schemas

Simple JSON Schema files for the main Form Validation demo payloads.

These schemas are intentionally lightweight and are meant for documentation, contract checks, API examples, or front-end validation hints. Server-side Django validation remains the source of truth.

## Files

- `signup.schema.json`
- `address.schema.json`
- `payment.schema.json`
- `file-upload.schema.json`
- `formset.schema.json`
- `survey.schema.json`
- `wizard-step-1.schema.json`
- `wizard-step-2.schema.json`
- `wizard-step-3.schema.json`
- `validation-log.schema.json`
- `index.schema.json`

## Notes

- File uploads are represented as metadata objects because JSON Schema cannot directly model multipart file objects.
- Sensitive fields such as password, CVV, and passport number are included only as input contracts and should not be logged or persisted.
