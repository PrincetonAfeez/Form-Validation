# ADR 0002: Three Validation Layers

## Status

Accepted.

## Context

The app demonstrates client, field, and form-level validation. Without explicit
boundaries, checks drift into whichever layer is convenient.

## Decision

Client validation is ergonomic feedback only. Field validation owns type checks and
normalization. Form validation owns cross-field rules and defense in depth.

## Consequences

Every server-side rule remains authoritative, while HTMX and Alpine make feedback
faster without becoming security boundaries.
