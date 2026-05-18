# ADR 0004: Honeypot and Time Trap

## Status

Accepted.

## Context

This demo needs a lightweight spam-defense pattern without adding third-party
CAPTCHA services or account flows.

## Decision

Use a hidden honeypot field and a timestamp-based time trap as documented
validators. The signup form uses the honeypot; the time trap remains available in
the catalog for forms that need it.

## Consequences

The pattern is privacy-preserving and simple to test. It is not a replacement for
rate limiting in production.
