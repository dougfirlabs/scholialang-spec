# Governance

Scholia uses an RFC-style process for language changes.

## Change Types

- Editorial: clarifies wording without changing validator behavior.
- Additive: adds optional syntax or metadata while preserving existing traces.
- Breaking: changes parsing, validation, or semantics for existing traces.

## RFC Outline

Each language RFC should include:

- Motivation
- Proposed syntax or semantic change
- Compatibility impact
- Migration path
- Validator impact
- Fixture examples
- Reference implementation work

Breaking changes require a migration document and coordinated changes in
`scholialang`.

