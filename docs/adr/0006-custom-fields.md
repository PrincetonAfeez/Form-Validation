# ADR 0006: Custom Form Fields vs Stock Fields

## Status

Accepted.

## Context

Some checks only answer whether input is valid. Others also normalize the value
into a better application shape.

## Decision

Use validators for pure checks. Use custom form fields when validation and
normalization belong together. `PhoneField` parses user input and returns E.164.

## Consequences

Downstream code receives correctly shaped values and does not repeat parsing logic.
