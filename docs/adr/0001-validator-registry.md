# ADR 0001: Validator Registry vs Hard-coded Imports

## Status

Accepted.

## Context

The UI needs to show the validation rules active for each demo form. Hard-coded
imports make validation easy to call, but they do not give the app a single
introspectable source of truth.

## Decision

Validators register under stable names in `apps/forms_lab/validators/registry.py`.
Forms reference validators with `get("namespace.name")`, and pages use registry
metadata for the rules and reference panels.

## Consequences

The app can list every rule, swap implementations behind stable names, and keep
form modules focused on behavior instead of documentation wiring.
