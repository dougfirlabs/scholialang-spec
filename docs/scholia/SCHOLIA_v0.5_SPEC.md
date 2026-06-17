# Scholia v0.5 — Specification (SUPERSEDED)

> **Superseded:** Scholia v0.6 is now canonical. Use
> [`SCHOLIA_v0.6_SPEC.md`](SCHOLIA_v0.6_SPEC.md) for current atom kinds,
> operators, validator rules, the `canonical_id` substrate, the DAG
> registry, the lazy canonical-prelude, and migration guidance. This v0.5
> document is preserved unchanged below as a historical record; do not
> edit it. v0.5 traces remain valid under v0.6 (v0.6 is additive). For
> migration from the v0.5 trace shape to v0.6, see
> [`v05-to-v06-migration.md`](v05-to-v06-migration.md).
>
> **Note (reconciled in v0.6):** the v0.5 text below states
> `Finding.for_goal` is "removed in v0.6." That is **superseded** — the
> published v0.6 implementation keeps `for_goal` **deprecated** and
> **defers removal to v0.7**. See `SCHOLIA_v0.6_SPEC.md` §10.8 / §15.

---

# Scholia v0.5 — Specification

**Status:** CANONICAL (v0.5 substrate rebuild — supersedes v0.4 draft of 2026-05-22).
**Date:** 2026-06-04.
**Authors:** Darren Brewster, Barry Sevig, Claude Opus 4.7.
**Project:** Doug Fir Labs (the `scholialang-spec` repository is the canonical home).

This document supersedes `docs/scholia/legacy/SCHOLIA_v0.4_SPEC.md`. The
v0.4 draft is preserved unchanged at that path with a "superseded"
banner; do not edit it.

> SCHOLIA_v0.5_SPEC.md is the single source of truth for the Scholia
> reasoning-trace notation. Every downstream surface (canonical agent
> prompt, `scholialang` reference impl, `scholialang-mcp` validator,
> `scholialang.org` spec page and runtime mirrors) derives from this
> document. If two sources disagree, this one wins.

---

## §1 Overview

Scholia is a reasoning-trace notation: XML-shaped atoms emitted inline
by an agent (or a human) during a task, parsed into a typed
intermediate representation, then validated against a closed-set
schema. The substrate has three goals:

1. **Reasoning is data.** Every inference step can be represented as
   structured information, in a shape an external auditor — agent or
   human — can read.
2. **Verification requires structure.** A structured trace can be
   checked for reference completeness, closed decisions, recorded
   actions, goal status, and epistemic closure.
3. **Composition is essential.** An auditor's Scholia about an agent's
   Scholia is the canonical Monitor-over-Subject form.

v0.5 is a *substrate-rebuild* release. It re-locks the atom catalog at
**32 kinds** (v0.4 had 31), adds the `Concluding` atom for epistemic
close, formalizes the criticality ladder (`incidental` < `bridge` <
`ledger` < `verifier` < `kernel`) as a runtime ordering, and adds six
new validator rules that enforce the substrate's structural promise.

What stays the same as v0.4:

- XML-shaped tags (a design choice that independently converged with
  a practitioner finding from within Anthropic, reported by Simon
  Willison, that HTML/XML-shaped tags work well for LLM memory).
- Validator + Adjudicator architecture.
- Fallback semantics (validation failure → prose-only with
  `scholia_fallback: true`).
- The v0.3.1 primitive hooks (`<Edge>`, `<Effect>`, `<Ref>`, `<Meta>`)
  are carried forward unchanged.

What v0.5 adds (compact summary; see §5 for the change manifest):

| # | Change | Type |
|---|---|---|
| 1 | `<Concluding>` atom added (epistemic close, distinct from `<Deciding>`) | additive |
| 2 | `<Finding>` migrates `for_goal` → `for_hyp` (deprecated alias preserved through v0.5; removed in v0.6) | semi-breaking (warning only) |
| 3 | `<Goal>` gains optional `criticality` attribute | additive |
| 4 | Six new validator rules (`for_goal_resolves`, `refer_at_least_one`, `criticality_non_decreasing`, `no_action_in_concluding`, `single_active_concluding_per_goal`, `min_confidence_ceiling`) | additive |
| 5 | `CRITICALITY_RANK` constant locked at five tiers | additive |
| 6 | Operator set documented at full 11 + 2 emergent (was understated in v0.4) | clarification |

Pre-v0.5 traces (no `<Concluding>`, `Finding` uses `for_goal`) MUST
parse and validate cleanly. The new validator rules are gated on the
presence of `<Concluding>` atoms — a v0.4 trace exercises zero new
rules.

---

<!-- BEGIN_GENERATED:atoms_to_spec -->
## §2 Atom catalog

The Scholia v0.5 closed set is **32 atom kinds**, grouped into seven categories. Names are PascalCase. Adding an atom kind is a breaking change and requires a spec version bump.

### §2.1 Reasoning

- **`<Action>`** — external state change (must produce a Finding).
- **`<Observation>`** — external input — command output, file contents, query result.
- **`<Thinking>`** — internal deliberation — not observing, not acting.

### §2.2 Evidence

- **`<Concluding>`** — chain-level epistemic close — resolves a Goal via cited atoms.
- **`<Contradiction>`** — two claims that cannot both be true; forces a Deciding.
- **`<Evidence>`** — observation bearing on a Hypothesis (supports / refutes / neutral).
- **`<Finding>`** — conclusion drawn from evidence; evaluates a Hypothesis.
- **`<Hypothesis>`** — explicit conjecture the agent intends to test.
- **`<Retract>`** — revoke a prior Finding (or downgrade-bypass for criticality).
- **`<Uncertainty>`** — confidence below 1 attached to a finding, hypothesis, or evidence.

### §2.3 Control

- **`<Alternative>`** — explicitly rejected option inside a Deciding.
- **`<Branch>`** — legal transition out of a Deciding.
- **`<Deciding>`** — action commitment branch point — chooses among alternatives.
- **`<Loop>`** — iteration over a collection, binding one per-iteration variable.
- **`<Parallel>`** — concurrent independent atoms with no specified ordering.

### §2.4 Reference

- **`<Implication>`** — long-form forward-link (equivalent to inline IMPLIES:id).
- **`<Print>`** — one-line human-facing summary surfaced to the reader.
- **`<Reference>`** — long-form back-link (equivalent to inline REFER:id).
- **`<Storing>`** — persist a named value to trace-local memory for later REFER.

### §2.5 Social

- **`<Handoff>`** — pass work to another agent with a named package.
- **`<Question>`** — explicit request for external input.
- **`<Review>`** — audit another agent's atom and produce a Finding.

### §2.6 Meta

- **`<Budget>`** — declared spending envelope (tokens / actions / wall_clock_ms).
- **`<Confidence>`** — qualitative or numeric confidence attached to another atom.
- **`<Constraint>`** — hard rule in effect that subsequent decisions must respect.
- **`<Cost>`** — observed expenditure (tokens / dollars / wall_clock_ms).
- **`<EventRef>`** — pointer to an externally recorded run event.
- **`<Goal>`** — target proposition the agent is pursuing; may declare criticality.

### §2.7 Primitives

- **`<Edge>`** — schema-reserved import / dependency edge on an Observation.
- **`<Effect>`** — schema-reserved side-effect kind (io_write / network / subprocess / mutates_state / pure).
- **`<Meta>`** — schema-reserved Step-level metadata (e.g. criticality).
- **`<Ref>`** — schema-reserved generic reference sub-element with type / target.
<!-- END_GENERATED:atoms_to_spec -->

> §2 above is generated by `scripts/atoms_to_spec.py` from the
> `scholialang/src/scholialang/atoms.py` impl. If you edit this section
> by hand, the consistency test (`tests/test_spec_consistency.py`)
> will fail. Regenerate with `python scripts/atoms_to_spec.py --out
> section2.md` and splice the result in.

---

## §3 Operators

Scholia operators are **inline UPPERCASE tokens, not tags**. They are
written inside atom content (`<Finding>... IMPLIES:F_07 ...</Finding>`)
or as bare operator-prefixed references (`REFER:Observation_02`). The
canonical operator set has 11 entries; two additional "emergent"
operators are recognized by the validator with a stability disclaimer.

### §3.1 Canonical operators

| Operator | Meaning | Example |
|---|---|---|
| `REFER` | dereference / back-link to another atom | `REFER:Finding_02` |
| `IMPLIES` | entailment / forward-link | `Observation_03 IMPLIES Finding_04` |
| `AND` | conjunction | `H_01 AND H_02` |
| `OR` | disjunction | `Finding_02 OR Finding_03` |
| `XOR` | exclusive disjunction | `path_A XOR path_B` |
| `NOT` | negation | `NOT Hypothesis_01` |
| `FORALL` | universal quantifier | `FORALL(branch IN branches)` |
| `EXISTS` | existential quantifier | `EXISTS(flake IN tests)` |
| `BEFORE` | temporal ordering | `Observation_03 BEFORE Deciding_04` |
| `AFTER` | temporal ordering | `Action_02 AFTER Finding_01` |
| `EQUALS` | value or identity equality | `hash EQUALS declared_hash` |

The `scholialang.atoms.Operator` enum lists these in machine-readable
form.

### §3.2 Emergent operators (provisional)

Two operators surfaced from RSI runs at sufficient frequency that the
validator recognizes them but their semantics are still being studied.
They are **provisional** — emitters may produce them; consumers must
treat them as opaque inline tokens until their semantics are locked in
a future point release.

| Operator | Provisional meaning |
|---|---|
| `FLIP` | reverse the polarity of a prior atom (`FLIP:Finding_02` flips status from `met` to `unmet`). |
| `SURFACE` | promote an internal Thinking atom into a public-facing observation, e.g. for human review. |

Provenance: 2026-05-16 RSI-atlas-mcp-rsi-driver-parity run reached for
both tokens during structured-emission. They are tracked via
`squeakaroni/detectors/grammar_emergence/` for stability before
elevation to canonical.

### §3.3 Data primitives

`LIST`, `SET`, `MAP`, `STRING`, `NUMBER`, and `BOOL` are inline
primitive markers, not operators. Tooling may deserialize them when a
field declares structured content (e.g. `LIST(string): [...]`).

---

## §4 Validator rules

The v0.5 validator enforces 17 rules: the 11 existing structural rules
inherited from v0.2-v0.4, and 6 new rules introduced by PRD-02 that
govern `<Concluding>` semantics and criticality ordering.

### §4.1 Existing structural rules (carried forward from v0.4)

1. **Well-formed** — every atom has a known kind, or is the
   research-mode pseudo-atom `<Meta:research-mode/>`.
2. **Reference-complete** — every inline or structured reference
   resolves to an atom in the trace.
3. **Decision-closed** — every `<Deciding>` produces a `<Finding>` that
   names a chosen branch.
4. **Action-recorded** — every `<Action>` is followed by or contains a
   `<Finding>`.
5. **Hypothesis-evaluated** — every `<Hypothesis>` has linked
   `<Evidence>` or explicit `<Uncertainty>`.
6. **Retract-consistent** — every `<Retract>` references an existing
   `<Finding>` (or, in v0.5, an existing `<Concluding>` or `<Goal>`).
7. **Constraint-respected** — no `<Action>` violates an active
   `<Constraint>`.
8. **Goal-declared** — every `priority="required"` `<Goal>` has a
   `<Finding for_goal="...">` (v0.4) or `<Concluding for_goal="...">`
   (v0.5) with `status` in `met`, `unmet`, `partially_met`, or
   `met_late`. `<Meta:research-mode/>` exempts the trace from this rule.
9. **Observation-locatable** — every `<Observation>` that asserts a
   code-graph fact has a `location` attribute or an embedded `<Edge>`
   pointing at one.
10. **Effect-classified** — `<Effect>` sub-elements use the closed
    `kind` set: `io_write`, `network`, `subprocess`, `mutates_state`,
    `pure`.
11. **Confidence-bounded** — any numeric `confidence` attribute is in
    `[0.0, 1.0]`. Qualitative levels use the closed set
    `{low, medium, high}`.

### §4.2 New v0.5 rules (PRD-02)

Three hard-fail (severity = `error`) and three warning rules. All six
are gated on the presence of `<Concluding>` atoms in the trace — pre-
v0.5 traces never trigger them.

12. **`for_goal_resolves`** *(hard-fail)* — every `<Concluding>`'s
    `for_goal` attribute must resolve to a `<Goal>` id present in the
    same trace.
13. **`refer_at_least_one`** *(hard-fail)* — every `<Concluding>` body
    must contain at least one `REFER:` operator pointing to a
    `<Finding>`, `<Observation>`, or `<Evidence>` atom in the same
    trace.
14. **`criticality_non_decreasing`** *(hard-fail)* — a `<Concluding>`'s
    effective criticality (declared, or the max of cited
    Findings/Observations if not declared) must be `>=` the criticality
    of the Goal it closes. `kernel` cannot be closed by `bridge`
    *unless* the trace contains an explicit
    `<Retract target="goal_id">` documenting the downgrade.
    `CRITICALITY_RANK = {incidental:0, bridge:1, ledger:2, verifier:3, kernel:4}`.
    Elevation (declared criticality > chain max) is permitted without a
    Retract.
15. **`no_action_in_concluding`** *(warning)* — Concluding body must
    not contain modal verbs that signal action commitment (`should`,
    `will`, `recommend`, `choose`, `propose`, including trailing-`s`
    forms). Heuristic regex — false positives possible; agents
    disambiguate by emitting a `<Deciding>` instead.
16. **`single_active_concluding_per_goal`** *(warning)* — at most one
    ACTIVE `<Concluding>` per `<Goal>`. A Concluding that has been
    targeted by a `<Retract target="conc_id">` is no longer active and
    does not count.
17. **`min_confidence_ceiling`** *(warning)* — a Concluding's declared
    `confidence` must not exceed the minimum confidence of its cited
    Findings/Evidence atoms (or sibling `<Uncertainty on="atom_id">` /
    `<Confidence on="atom_id">`). Warning only — captures epistemic
    overreach but does not block the trace.

### §4.3 Report shape

Validators return:

```
{
    "errors":   [{"rule": str, "atom_id": str|None, "message": str, "severity": "error"}, ...],
    "warnings": [{"rule": str, "atom_id": str|None, "message": str, "severity": "warning"}, ...],
}
```

Unchanged from v0.4. v0.5 rules slot into the existing structure.

### §4.4 Validity definition

A Scholia v0.5 trace is **valid** if and only if its `errors` array is
empty. Warnings do not invalidate the trace; they surface for operator
review. A `<Meta:research-mode/>` pseudo-atom at the top of the trace
exempts the trace from rule 8 (goal-declared) but does not waive any
other rule.

---

## §5 Versioning — v0.4 → v0.5 change manifest

This section is the authoritative changelog for the substrate. Tools
that migrate traces or persisted state across the v0.4/v0.5 boundary
should consult this list (and `v04-to-v05-migration.md` for migration
recipes).

### §5.1 Catalog changes

- **Added: `<Concluding>`.** Epistemic-close atom. Required attribute:
  `for_goal`. Optional: `confidence` (0.0-1.0), `criticality` (one of
  `incidental` / `bridge` / `ledger` / `verifier` / `kernel`). The atom
  is *distinct* from `<Deciding>` (which commits to one action among
  alternatives); `<Concluding>` makes no choice and prescribes no
  action. Catalog count: 31 → 32.
- **Migrated: `<Finding>` `for_goal` → `for_hyp`.** A Finding evaluates
  a Hypothesis, not a Goal; the rename clarifies the semantic. Both
  attributes are accepted on read in v0.5. Setting `for_goal` via the
  Python constructor in v0.5 code emits a `DeprecationWarning` once
  per instance. Removal target: v0.6. Migration helper:
  `Finding.from_legacy({"for_goal": ...})`.
- **Added: `<Goal>.criticality`** (optional). Permits the
  `criticality_non_decreasing` rule to compare both ends of the
  closure chain. Pre-v0.5 traces (no criticality on Goal) skip that
  rule's downgrade check.

### §5.2 Operator changes

- No additions or removals. The 11 canonical operators (AND, OR, XOR,
  NOT, IMPLIES, REFER, FORALL, EXISTS, BEFORE, AFTER, EQUALS) and the
  2 emergent operators (FLIP, SURFACE) were always implemented; v0.4
  spec doc only documented `REFER`, `IMPLIES`, `NOT` + emergent. v0.5
  brings the spec doc in line with the impl.

### §5.3 Validator changes

- **Added: 6 new rules** (see §4.2). Three hard-fail, three warning.
  All six gated on `<Concluding>` presence.
- **Modified: rule 6 (Retract-consistent)** now accepts `<Goal>` and
  `<Concluding>` as legal Retract targets (was Finding-only in v0.4).
- **Modified: rule 8 (Goal-declared)** accepts `<Concluding
  for_goal="...">` as a Goal-closer in v0.5; `<Finding for_goal="...">`
  is still accepted for v0.4 back-compat.

### §5.4 Runtime / constant changes

- **Added: `CRITICALITY_RANK`** — module-level dict on
  `scholialang.atoms` with the five-tier ordering. Consumed by
  `criticality_non_decreasing` and any downstream tool that needs to
  reason about the ladder.

### §5.5 What did NOT change

- XML-shaped tag syntax.
- Closed-set principle.
- Fallback semantics (`scholia_fallback: true`).
- Step container shape (§6).
- Reference resolution rules (§7).
- Composition rules (§8).
- Validator report shape.
- The `<Meta:research-mode/>` pseudo-atom.

---

## §6 Migration guide

This section is a brief migration sketch. The full migration recipe
(per-trace, per-tool, per-API) lives in
`docs/scholia/v04-to-v05-migration.md`.

### §6.1 Migrating archival traces

- **No action required.** v0.4 traces parse cleanly under the v0.5
  parser. `Finding` atoms with `for_goal` are routed through
  `Finding.from_legacy()` which copies the attribute to `for_hyp`
  without emitting a deprecation warning (archival traces should not
  spam logs).

### §6.2 Migrating live emitters

- **Move `Finding(for_goal=...)` → `Finding(for_hyp=...)`** at the call
  site. The DeprecationWarning surfaces this in test logs.
- **Reach for `<Concluding>`** when the agent's reasoning has produced
  a multi-atom answer to a stated Goal. Pre-v0.5 emitters used
  `<Finding for_goal="...">` for this role; v0.5 emitters should
  produce a `<Concluding>` citing the Findings instead.
- **Set `criticality` on `<Goal>`** when the Goal is on the kernel /
  verifier / ledger / bridge tier — this enables
  `criticality_non_decreasing` to catch silent downgrades.

### §6.3 Migrating validators

- **Add the 6 new rules.** The reference impl in
  `scholialang/src/scholialang/validator.py` is the source. Tools that
  vendor their own validator (`scholialang-mcp` and private product mirrors)
  need a coordinated port.
- **No rule removed.** Backports of the new rules into a v0.4-shaped
  validator should not alter rule 1-11 behavior.

### §6.4 Migrating consumers (dashboards, runners)

- **Report shape is unchanged.** Existing consumers continue to work.
- **New rule names** appear in the `errors` / `warnings` arrays. Sort
  / filter logic should treat unknown rule names as pass-through (do
  not hard-code rule-name allowlists).

---

## §7 Reference resolution

(Unchanged from v0.4 — included here for self-containedness.)

- Identifiers are scoped to the enclosing trace.
- A reference is satisfied if the referenced id exists on any atom or
  `<Step>` *before validation completes* (forward references are
  permitted within a single trace).
- Structured reference attributes include `for`, `for_goal`, `for_hyp`,
  `to`, `next`, `target`, `on`, and `of`.
- Cross-trace references may use `trace_id:atom_id` where the
  receiving validator can resolve them.

---

## §8 Composition rules

(Unchanged from v0.4 except as noted.)

- `<Thinking>` can contain `<Storing/>`, `<Print/>`, hypotheses, inline
  operators, and prose.
- `<Observation>` may carry `timestamp`, `location`, and `confidence`
  attributes.
- `<Action>` may carry `timestamp` and must produce a `<Finding>`.
- `<Deciding>` must enumerate options and produce a `<Finding>`
  declaring the chosen option.
- **`<Concluding>` (v0.5)** must declare `for_goal`, contain at least
  one `REFER:` operator, and may declare `confidence` and
  `criticality`. It must NOT contain Action-modal verbs (warning,
  not error).
- `<Alternative>` is only legal inside `<Deciding>`.
- `<Loop>` binds one variable name via `as`.
- `<Review>` must name a target and produce a `<Finding>`.
- `<Parallel>` child atoms must be independent.

---

## §9 Companion artifacts

- **Atom card** (`reference/atom-card-v0.5.md`) — single-page
  embeddable summary of the 32-atom catalog. Linked from
  `scholialang.org/spec/`.
- **Notation reference** (`reference/notation-reference.md`) — full
  per-atom catalog with XML shape, attributes, body convention,
  examples, and which validator rules apply. Generated from
  `reference/atoms_index.yaml`.
- **Migration doc** (`docs/scholia/v04-to-v05-migration.md`) — recipes
  for moving traces, emitters, and validators across the v0.4/v0.5
  boundary.
- **Legacy spec** (`docs/scholia/legacy/SCHOLIA_v0.4_SPEC.md`) —
  preserved v0.4 draft with a "superseded" banner. Read for history;
  do not consult for current canonical.
- **Consistency test** (`tests/test_spec_consistency.py`) — asserts
  this document stays in sync with the `scholialang.atoms` impl on PR.
- **Reference implementation** (`scholialang/src/scholialang/`) — the
  Python package that owns the atom dataclasses, parser, and
  validator. Other implementations should match its semantics.

---

*Generated portions of §2 derive from `scholialang.atoms._ATOM_CLASSES`
via `scripts/atoms_to_spec.py`. Do not edit §2 by hand; regenerate.
Hand-written sections may be edited freely with PR review.*
