# Changelog

## Unreleased — PROPOSED (awaiting operator contract approval)

- **Proposes** the additive `fingerprint=` attribute on location-bearing
  atoms (`docs/scholia/FINGERPRINT.md`): an optional `<algo>:<hex>` content
  hash of the source span named by `location`, letting trace claims about
  code re-verify mechanically (verifies / rebinds / span_mismatch / stale).
  The digest itself references 52X-B2's single definition (issue #524) and
  is **not** redefined here.
- Specs a single new validator rule, `fingerprint_well_formed` (hard-fail;
  vacuous when absent) — structural only; re-verification against source is
  a consumer concern. Ignore-if-absent follows the `canonical_id` precedent.
- Adds a shared, single-copy fixture corpus at
  `tests/fixtures/fingerprint/` (positive: valid, moved-symbol rebind,
  ignore-if-absent; negative: malformed hash, span mismatch, stale) plus a
  machine-readable `manifest.yaml`, consumed by `tests/test_fingerprint_fixtures.py`.
- **Nothing merged into the canonical v0.6 spec.** This is a proposal PR;
  adoption is at most a 0.6.x additive point revision and is gated on
  explicit operator contract approval.

## v0.6.2

- Corrects validator Rule 4, `action_recorded`, for recursive traces:
  a later cross-step Finding may record an Action through a direct
  `REFER`, or through one Observation/Evidence `REFER` hop.
- Accepts a later goal-closing Concluding that directly `REFER`s the
  Action and a generic `records_result` graph edge targeting the Action.
- Keeps provenance strict: chronological order alone is insufficient
  for a non-immediate result. Unrelated, order-only, and unclosed Action
  cases remain invalid.
- Adds the shared, self-describing conformance suite
  `conformance/v0.6.2/action_recorded.json` with nine positive and four
  negative cases, including explicit nested and legacy immediate-sibling
  coverage, plus implementation-independent integrity tests.
- Bumps the stated `SCHOLIA_VALIDATOR_VERSION` to `0.6.2` and adds
  `docs/scholia/v06.1-to-v06.2-migration.md`.
- No atom, attribute, operator, parser, or validator report-shape
  changes. Existing nested and immediate same-Step result forms remain
  valid.

## v0.6.1

- **Additive, non-breaking.** v0.6.0 traces and tooling stay valid;
  nothing is deprecated.
- Adds optional `status` (`met` / `unmet` / `partially_met`) to
  `<Concluding>` — the completion verdict on a goal-close, distinct from
  `confidence` (certainty) and `criticality` (load-bearing rank). A
  status-less `<Concluding>` stays valid. Updates `SCHOLIA_v0.6_SPEC.md`
  §6, `reference/atoms_index.yaml`, and regenerates `notation-reference.md`.
- Reconciles validator rule 8 (`goal_declared`): the rule and the
  `<Concluding>` attribute table now agree that `status` is an allowed
  attribute, resolving the v0.6.0 contradiction (rule named a `status`
  the table omitted, which the reference parser rejected). Adds a
  spec-consistency assertion for the agreement.
- Bumps the spec's stated `SCHOLIA_VALIDATOR_VERSION` `0.6.0` → `0.6.1`
  (§4, §10.7, §10.10). The published v0.6.0 build stamps `0.6.0`; the
  reconciliation build stamps `0.6.1`.
- Adds `compatibility-manifest.json` (golden-records) with a v0.6.1
  golden record for a status-bearing `<Concluding>`, appended without
  mutating the 2026-06-06 freeze; `spec_version` stays `"Scholia v0.6"`.
- Adds `docs/scholia/v06.0-to-v06.1-migration.md`.
- Extends the public-spec hygiene leak guard to scan `src/`, `tests/`,
  and `scripts/` (in addition to `docs/`) with a guard self-test, and
  scrubs internal references from `scripts/` and `tests/`.

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
