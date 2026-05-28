# Migrating Scholia consumers from v0.3 → v0.3.1

**Audience:** anyone building tooling that reads, validates, or
transforms Scholia traces. Includes a host application's own modules, partner
integrations, and future external adopters.
**Companion spec:** [`SCHOLIA_v0.3.1_SPEC.md`](SCHOLIA_v0.3.1_SPEC.md).
**Downstream:** [`SCHOLIA_v0.4_SPEC.md`](SCHOLIA_v0.4_SPEC.md) — the
release that will populate v0.3.1's reserved fields.

---

## 1. What changed

v0.3.1 is a **schema reservation release**. The validator gained
permissive support for seven optional primitive hooks; the rewriter
gained nothing. Operationally:

- New optional `<Observation>` attributes: `location`, `confidence`.
- New optional sub-elements on `<Observation>`: `<Edge>`, `<Effect>`,
  `<Ref>`.
- New optional sub-element on `<Step>`: `<Meta criticality="...">`.
- New module-level validator constant `SCHOLIA_VALIDATOR_VERSION =
  "0.3.1"`.
- `ValidationResult` now carries a `scholia_validator_version` field.
- New validator rule `RULE_V031_OPTIONAL_FIELDS` re-validates closed-
  set values on AST-reconstituted traces.
- The atom catalog grew from 27 → 31 atoms (added: `Edge`, `Effect`,
  `Ref`, `Meta`).

No v0.3 atom that validated before this release stops validating
after. The corpus-replay regression test
(`tests/integration/scholia/test_corpus_replay.py`) enforces that.

## 2. What to do

### If you write tools that PARSE Scholia traces

- **Be permissive with attributes you don't recognise on a known
  atom kind.** v0.3.1 added `location` and `confidence` to
  `<Observation>`. v0.4 may add more. Treat unknown attributes as
  opaque pass-through rather than fatally rejecting.
- **Be permissive with sub-elements you don't recognise.** v0.3.1
  added `<Edge>`, `<Effect>`, `<Ref>`, `<Meta>` as new closed-set
  atom kinds. v0.4 may add others. Treat unknown atom kinds as
  opaque rather than fatally rejecting — surface a warning, not a
  hard failure.
- **Branch on `scholia_validator_version`** when your code's behavior
  depends on whether the trace went through a v0.3.1+ validator.
  Older traces validated against the v0.3 validator will lack this
  field; default to `"0.3"` in that case.

### If you write tools that EMIT Scholia traces

- **Do not populate the v0.3.1-reserved fields yet.** Population is
  v0.4's job. The rewriter has not been updated; tools that
  hand-author traces must wait for the v0.4 implementation PRDs to
  land (`rsi-scholia-v0.4-stable-atom-ids`,
  `rsi-scholia-v0.4-code-graph-metadata`, etc.).
- **Authoring guidance for human/agent authors** is in
  [`docs/notation/NOTATION_REFERENCE.md`](../notation/NOTATION_REFERENCE.md)
  §13.

### If you write tools that TRANSFORM Scholia traces

- **Round-trip the new fields, even if you don't interpret them.**
  Strip-and-re-emit transformers should preserve `location`,
  `confidence`, and the new sub-elements verbatim. Losing them
  silently makes the transformer lossy in a way that matters once
  v0.4 emitters land.

## 3. What NOT to do

- **Do not emit v0.4-shaped fields prematurely.** The validator
  accepts them, but no consumer is wired to interpret them, and
  prematurely populating means future v0.4 emitters will have to
  reconcile two distinct populating regimes. The whole point of
  v0.3.1 is to ship the slot before anyone fills it.
- **Do not relax the strict closed-set contract on parse.** v0.3.1
  is still a closed-vocabulary notation — arbitrary attribute and
  sub-element extensions are NOT accepted. New fields require a
  spec bump (v0.5+) and a new release.
- **Do not treat absence of `<Effect>` as equivalent to
  `<Effect kind="pure"/>`.** Absence is "unknown"; explicit
  `pure` is an asserted observation. The semantic distinction
  matters for downstream risk analysis.
- **Do not treat absence of `<Meta criticality="...">` as anything
  other than `incidental`.** That is the documented default in the
  spec.

## 4. When to upgrade

| You're a... | When to upgrade your parser/consumer to v0.3.1 |
|---|---|
| a host application contributor | Already done by this PRD; just sync. |
| Downstream tool inside the a host application repo | When your code path next imports from `scholialang.validator` — the API is backwards-compatible, so no code change required unless you read `errors_by_rule` and want to surface the new rule. |
| External adopter | **Before** the v0.4 emitter ships in your environment. Specifically: before the first `feat(scholia): v0.4` PR lands in a release you consume. |

## 5. Forward-compatibility checklist for tooling authors

If your code touches Scholia traces, confirm each of these before
declaring v0.3.1 compatibility:

- [ ] Parser does not reject `<Observation location="...">` or
  `<Observation confidence="...">`.
- [ ] Parser does not reject `<Edge>`, `<Effect>`, `<Ref>`, or
  `<Meta>` as unknown atom kinds.
- [ ] Transformer round-trips the above attributes and sub-elements
  losslessly.
- [ ] If you compute per-atom hashes or diffs, include or exclude the
  new fields **deliberately** — not by accident of which iterator you
  used.
- [ ] If you display traces to humans, decide whether to surface the
  new fields or hide them when absent.
- [ ] If you branch on validator output, read `scholia_validator_version`
  (default to `"0.3"` for traces from older validators).
- [ ] Your test corpus includes at least one trace WITH the new
  fields and one trace WITHOUT, both validating successfully.

## 6. Related artifacts

- [`SCHOLIA_v0.3.1_SPEC.md`](SCHOLIA_v0.3.1_SPEC.md) — canonical
  field-by-field contract.
- [`SCHOLIA_v0.4_SPEC.md`](SCHOLIA_v0.4_SPEC.md) — what v0.3.1's
  reservations feed into.
- [`../notation/NOTATION_REFERENCE.md`](../notation/NOTATION_REFERENCE.md)
  §13 — operator-facing authoring guidance.
- [`../reports/2026-05-22-codex-atlas-token-analysis.md`](../reports/2026-05-22-codex-atlas-token-analysis.md)
  — Codex's analysis that motivated the v0.3.1+v0.4 sequence.
