# scholialang-spec

This repository contains the Scholia language specification and
conformance examples.

Scholia is a structured reasoning notation for agent traces. It is
designed to make reasoning artifacts readable, diffable, validateable,
and portable across tools.

Scholia v0.6 makes agent reasoning portable, inspectable, and reusable
across sessions using content-addressed reasoning traces. v0.6 is the v0.5
closed vocabulary plus a content-addressed substrate: optional
`canonical_id` hashes, a canonical-id-keyed DAG registry, and the three core
lazy-prelude modes `hash_only`, `hash_list`, and `inline`.

## Current v0.6 Scope

`scholialang-spec` is the canonical home for the v0.6 language contract:
the additive `canonical_id` substrate, canonical-id-keyed registry semantics,
canonical-id-aware `REFER` resolution, migration notes from v0.5, and the
three finalized lazy-prelude modes. Implementation packages and host tooling
should point readers here for normative v0.6 behavior.

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
- [`scholialang.org`](https://github.com/dougfirlabs/scholialang.org) -
  public website, launch kit, playground, and examples gallery

## Launch Links

- Public spec: https://scholialang.org/spec
- Launch article: https://scholialang.org/why-reasoning-needs-a-protocol-layer
- Eval summary: https://scholialang.org/eval-summary
- Playground: https://scholialang.org/playground

## Version

Current language version: `v0.6.0`.

`docs/scholia/SCHOLIA_v0.5_SPEC.md` is superseded by v0.6 and preserved
with a banner. `docs/scholia/SCHOLIA_v0.4_SPEC.md` is superseded; the
historical v0.4 draft is preserved with a banner at
`docs/scholia/legacy/SCHOLIA_v0.4_SPEC.md`. v0.6 is additive — v0.5 (and
v0.4) traces remain valid.

## License

The normative specification prose and documentation in this repository are
licensed under CC-BY-4.0. See `LICENSE` and `LICENSE-POLICY.md`.

Reference implementations, host integrations, MCP/LSP tooling, and package
code live in sibling repositories and are licensed separately, generally under
dual MIT OR Apache-2.0 terms.
