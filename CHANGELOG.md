# Changelog

## v0.6.0

- Adds canonical `docs/scholia/SCHOLIA_v0.6_SPEC.md` (content-addressable
  substrate release). Authored to the 2026-06-06 golden-records
  compatibility manifest and byte-for-byte to the published `scholialang`
  v0.6 implementation.
- Adds the universal `canonical_id` base attribute
  (`sha256:<12 hex>` over `{kind, content.strip(), attrs}`, provenance
  excluded), the `compute_canonical_id` hasher contract, and the
  `canonical_id_well_formed` validator rule (hard-fail; vacuous on
  absence).
- Adds the `REFER:sha256:<cid>` / `IMPLIES:sha256:<cid>` operator forms.
- Specs the DAG registry (canonical_id-keyed; `{version, atoms, edges}`
  at `~/.scholia/registry.proofchain.json`; kind→ProofNodeType mapping;
  loads old flat JSON) and the canonical-id-aware `reference_complete`
  resolver.
- Specs the lazy canonical-prelude with the 3 core modes
  (`hash_only` / `hash_list` (default) / `inline`); determinism is a
  normative invariant.
- Adds a clearly-labeled EXPERIMENTAL extension (§14) for the 2
  quality-recovery arms (`hash_semantic_preview`,
  `selective_inline_plus_hash_only`), explicitly post-dating the manifest
  and not v0.6 core.
- Reconciles the `Finding.for_goal` disposition: **deprecated, removal
  deferred to v0.7** (not removed in v0.6), matching the impl; adds a
  human sign-off checkbox (§15).
- Bumps `reference/atoms_index.yaml` to v0.6 (documents `canonical_id`
  as a universal base attribute) and regenerates `notation-reference.md`
  and spec §2. Adds `docs/scholia/v05-to-v06-migration.md` and
  `examples/v06/`. Marks v0.5 superseded but preserved.
- 32-atom closed set unchanged; v0.5 traces remain valid.

## v0.5.0

- Adds canonical `docs/scholia/SCHOLIA_v0.5_SPEC.md`.
- Adds the v0.5 `Concluding` atom, `Finding.for_hyp`, `Goal.criticality`,
  the criticality ladder, and six new validator rules.
- Adds generated v0.5 atom card, notation reference, atom index, generators,
  and spec consistency test.
- Preserves the v0.4 draft under `docs/scholia/legacy/`.

## v0.4.0

- Initial standalone Scholia specification release.
- Includes v0.3.1 primitive hooks, v0.4 metadata extensions, migration
  notes, and conformance examples.
