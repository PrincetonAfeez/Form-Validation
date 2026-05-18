# ADR 0003: ValidationResult Dataclass

## Status

Accepted.

## Context

Views need consistent outcomes from normal forms, formsets, wizard steps, and HTMX
field checks.

## Decision

The service layer returns `ValidationResult` objects instead of raising validation
exceptions for control flow.

## Consequences

Views stay thin. Tests can assert structured outcomes. Error logging is centralized
inside the service layer.
