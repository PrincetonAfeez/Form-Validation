# ADR 0005: Function Validators vs Class Validators

## Status

Accepted.

## Context

Django supports plain validator functions and class-based validators. The demo
should show when each is appropriate.

## Decision

Use functions for one-off form validation. Use `@deconstructible` classes for
configurable validators that may need migration serialization, such as reusable
model-field validators.

## Consequences

`validate_password_strength` shows the simple path. `PasswordStrengthValidator`
shows the configurable, migration-safe path.
