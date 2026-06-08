# scholialang-spec

This repository contains the Scholia language specification and
conformance examples.

Scholia is a structured reasoning notation for agent traces. It is
designed to make reasoning artifacts readable, diffable, validateable,
and portable across tools.

## Contents

- `docs/scholia/SCHOLIA_v0.6_SPEC.md` - canonical Scholia v0.6 spec
  (canonical_id substrate, DAG registry, 3-mode lazy prelude)
- `docs/scholia/SCHOLIA_v0.5_SPEC.md` - superseded v0.5 spec (archived,
  preserved with a banner)
- `docs/scholia/v05-to-v06-migration.md` - migration notes for emitters,
  validators, consumers, and archival traces
- `docs/scholia/v04-to-v05-migration.md` - prior migration notes
- `reference/atom-card-v0.5.md` - one-page atom catalog (32 kinds,
  unchanged through v0.6; carries the canonical_id note)
- `reference/notation-reference.md` - generated per-atom reference (v0.6)
- `docs/notation/` - earlier notation reference, extensions, and policy docs
- `examples/v06/` - v0.6 fixture traces (canonical_id, REFER:sha256, the
  3 core prelude modes)
- `examples/` - fixture traces used by reference implementations

## Related Repositories

- [`scholialang`](https://github.com/dougfirlabs/scholialang) - Python
  reference implementation
- [`scholialang-mcp`](https://github.com/dougfirlabs/scholialang-mcp) -
  MCP and LSP protocol tooling

## Version

Current language version: `v0.6.0`.

`docs/scholia/SCHOLIA_v0.5_SPEC.md` is superseded by v0.6 and preserved
with a banner. `docs/scholia/SCHOLIA_v0.4_SPEC.md` is superseded; the
historical v0.4 draft is preserved with a banner at
`docs/scholia/legacy/SCHOLIA_v0.4_SPEC.md`. v0.6 is additive — v0.5 (and
v0.4) traces remain valid.
