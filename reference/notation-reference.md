# Scholia v0.5 — Notation Reference

**Status:** Canonical, derived from `reference/atoms_index.yaml` (v0.5).
**Spec:** see [`docs/scholia/SCHOLIA_v0.5_SPEC.md`](../docs/scholia/SCHOLIA_v0.5_SPEC.md) for the full v0.5 specification.

This document lists the 32 atoms in the Scholia v0.5 closed set with their attributes, body conventions, examples, and applicable validator rules. One section per atom; atoms within a category are alphabetical.

> **Generated file.** Edit `atoms_index.yaml` and regenerate via `python scripts/notation_reference_gen.py`. The consistency test in `tests/test_spec_consistency.py` enforces this on PR.

## Table of contents

- **Reasoning** — [`<Action>`](#action) · [`<Observation>`](#observation) · [`<Thinking>`](#thinking)
- **Evidence** — [`<Concluding>`](#concluding) · [`<Contradiction>`](#contradiction) · [`<Evidence>`](#evidence) · [`<Finding>`](#finding) · [`<Hypothesis>`](#hypothesis) · [`<Retract>`](#retract) · [`<Uncertainty>`](#uncertainty)
- **Control** — [`<Alternative>`](#alternative) · [`<Branch>`](#branch) · [`<Deciding>`](#deciding) · [`<Loop>`](#loop) · [`<Parallel>`](#parallel)
- **Reference** — [`<Implication>`](#implication) · [`<Print>`](#print) · [`<Reference>`](#reference) · [`<Storing>`](#storing)
- **Social** — [`<Handoff>`](#handoff) · [`<Question>`](#question) · [`<Review>`](#review)
- **Meta** — [`<Budget>`](#budget) · [`<Confidence>`](#confidence) · [`<Constraint>`](#constraint) · [`<Cost>`](#cost) · [`<EventRef>`](#eventref) · [`<Goal>`](#goal)
- **Primitives** — [`<Edge>`](#edge) · [`<Effect>`](#effect) · [`<Meta>`](#meta) · [`<Ref>`](#ref)

## §1 Reasoning

Atoms that describe the agent's reasoning posture — what it's thinking, observing, or doing.

### `<Action>` — external state change — must produce a Finding.

**Category:** §2 Reasoning &nbsp;·&nbsp; **Slug:** `action` &nbsp;·&nbsp; **Body:** free-text + nested atoms.

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `timestamp` | ISO-8601 | no | wall-clock at action time. |

**Example:**

```xml
<Action id="A_01" timestamp="2026-06-04T12:00:00-07:00">
  Edited <code>src/foo.py</code> to add new helper.
  <Finding id="F_01">Helper compiles.</Finding>
</Action>
```

**Validator rules:** `Action-recorded`, `Constraint-respected` (see §4 of the canonical spec).

### `<Observation>` — external input — command output, file contents, query result.

**Category:** §2 Reasoning &nbsp;·&nbsp; **Slug:** `observation` &nbsp;·&nbsp; **Body:** free-text + nested atoms.

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `timestamp` | ISO-8601 | no | wall-clock at observation. |
| `location` | file:start:end | no | code-graph anchor. |
| `confidence` | float | low | medium | high | no | epistemic strength of this observation. |

**Example:**

```xml
<Observation id="Obs_01" timestamp="2026-06-04T12:01:00-07:00" location="src/foo.py:42:58" confidence="0.9">
  Tests pass for module ``foo``.
</Observation>
```

**Validator rules:** `Reference-complete`, `Observation-locatable`, `Confidence-bounded` (see §4 of the canonical spec).

### `<Thinking>` — internal deliberation — not observing, not acting.

**Category:** §2 Reasoning &nbsp;·&nbsp; **Slug:** `thinking` &nbsp;·&nbsp; **Body:** free-text + nested atoms (Storing, Print, Hypothesis, etc.).

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |

**Example:**

```xml
<Thinking id="T_01">
  REFER:Obs_01. If tests pass, IMPLIES:F_01 holds.
  <Hypothesis id="H_01">Coverage is adequate.</Hypothesis>
</Thinking>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

## §2 Evidence

Atoms that carry epistemic claims — hypotheses, evidence, findings, and the closure atom.

### `<Concluding>` — chain-level epistemic close — resolves a Goal via cited atoms.

**Category:** §2 Evidence &nbsp;·&nbsp; **Slug:** `concluding` &nbsp;·&nbsp; **Body:** free-text containing one or more REFER: operators..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `for_goal` | string | yes | id of the Goal this Concluding closes. |
| `confidence` | float [0,1] | no | declared epistemic strength of the close. |
| `criticality` | incidental | bridge | ledger | verifier | kernel | no | declared closure-tier; defaults to max(cited findings' criticality). |

**Example:**

```xml
<Concluding id="C_01" for_goal="G_01" confidence="0.85" criticality="ledger">
  REFER:F_01 AND REFER:F_02 IMPLIES the migration is complete.
</Concluding>
```

**Validator rules:** `for_goal_resolves`, `refer_at_least_one`, `criticality_non_decreasing`, `no_action_in_concluding`, `single_active_concluding_per_goal`, `min_confidence_ceiling`, `Goal-declared` (see §4 of the canonical spec).

### `<Contradiction>` — two claims that cannot both be true; forces a Deciding.

**Category:** §2 Evidence &nbsp;·&nbsp; **Slug:** `contradiction` &nbsp;·&nbsp; **Body:** free-text + REFER: operators naming the contradicting atoms..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |

**Example:**

```xml
<Contradiction id="K_01">
  REFER:F_03 AND NOT REFER:F_03 — two prior Findings disagree on coverage.
</Contradiction>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Evidence>` — observation bearing on a Hypothesis (supports / refutes / neutral).

**Category:** §2 Evidence &nbsp;·&nbsp; **Slug:** `evidence` &nbsp;·&nbsp; **Body:** free-text.

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `for` | string | yes | id of the Hypothesis this Evidence bears on (Python field: for_ref). |
| `polarity` | supports | refutes | neutral | yes | direction of bearing. |

**Example:**

```xml
<Evidence id="E_01" for="H_01" polarity="supports">
  merge-tree produced no conflicts.
</Evidence>
```

**Validator rules:** `Hypothesis-evaluated` (see §4 of the canonical spec).

### `<Finding>` — conclusion drawn from evidence — evaluates a Hypothesis.

**Category:** §2 Evidence &nbsp;·&nbsp; **Slug:** `finding` &nbsp;·&nbsp; **Body:** free-text.

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `for_hyp` | string | no | id of the Hypothesis this Finding evaluates (v0.5 canonical). |
| `for_goal` | string | no | DEPRECATED in v0.5 — use for_hyp. Preserved through v0.6. |
| `status` | met | unmet | partially_met | met_late | no | closure status when closing a required Goal. |

**Example:**

```xml
<Finding id="F_01" for_hyp="H_01" status="met">All criteria passed.</Finding>
```

**Validator rules:** `Action-recorded`, `Goal-declared` (see §4 of the canonical spec).

### `<Hypothesis>` — explicit conjecture the agent intends to test.

**Category:** §2 Evidence &nbsp;·&nbsp; **Slug:** `hypothesis` &nbsp;·&nbsp; **Body:** free-text.

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |

**Example:**

```xml
<Hypothesis id="H_01">All tests pass under --timeout=10.</Hypothesis>
```

**Validator rules:** `Hypothesis-evaluated` (see §4 of the canonical spec).

### `<Retract>` — revoke a prior Finding (or downgrade-bypass for criticality).

**Category:** §2 Evidence &nbsp;·&nbsp; **Slug:** `retract` &nbsp;·&nbsp; **Body:** free-text.

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `target` | string | yes | id of the Finding/Concluding/Goal being retracted. |
| `reason` | string | no | short rationale for the retraction. |
| `replacement` | string | no | id of the replacing atom if any. |

**Example:**

```xml
<Retract id="R_01" target="G_01" reason="criticality reclassified to bridge after triage.">
  Goal G_01 moved off the kernel tier.
</Retract>
```

**Validator rules:** `Retract-consistent` (see §4 of the canonical spec).

### `<Uncertainty>` — confidence below 1 attached to a Finding, Hypothesis, or Evidence.

**Category:** §2 Evidence &nbsp;·&nbsp; **Slug:** `uncertainty` &nbsp;·&nbsp; **Body:** free-text rationale.

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `True` | string | no | id of the atom this Uncertainty annotates. |
| `confidence` | float [0,1] | low | medium | high | no | qualitative or numeric. |

**Example:**

```xml
<Uncertainty id="U_01" on="F_02" confidence="0.4">
  Coverage signal is weak — only 3 traces sampled.
</Uncertainty>
```

**Validator rules:** `Confidence-bounded` (see §4 of the canonical spec).

## §3 Control

Atoms that mark control-flow shape — decisions, branches, loops, parallel sub-traces.

### `<Alternative>` — explicitly rejected option inside a Deciding.

**Category:** §2 Control &nbsp;·&nbsp; **Slug:** `alternative` &nbsp;·&nbsp; **Body:** free-text.

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `label` | string | yes | short label for the alternative. |
| `rejected_because` | string | yes | why this option was not chosen. |

**Example:**

```xml
<Alternative id="Alt_01" label="rebase" rejected_because="lossy history">
  Rebase would flatten the commit chain.
</Alternative>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Branch>` — legal transition out of a Deciding.

**Category:** §2 Control &nbsp;·&nbsp; **Slug:** `branch` &nbsp;·&nbsp; **Body:** free-text + further atoms following the branch..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `of` | string | yes | id of the parent Deciding. |
| `label` | string | yes | the chosen branch label. |

**Example:**

```xml
<Branch id="Br_01" of="D_01" label="merge">
  Merge keeps both histories visible.
</Branch>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Deciding>` — action commitment branch point — chooses among alternatives.

**Category:** §2 Control &nbsp;·&nbsp; **Slug:** `deciding` &nbsp;·&nbsp; **Body:** free-text + Alternative children + Finding child declaring the chosen branch..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `options` | comma-list | no | labels of available options; long-form Alternative atoms are also accepted. |

**Example:**

```xml
<Deciding id="D_01" options="merge,rebase,squash">
  <Alternative label="rebase" rejected_because="lossy history"/>
  <Finding for_hyp="H_choice" status="met">Chose merge.</Finding>
</Deciding>
```

**Validator rules:** `Decision-closed` (see §4 of the canonical spec).

### `<Loop>` — iteration over a collection — binds one per-iteration variable.

**Category:** §2 Control &nbsp;·&nbsp; **Slug:** `loop` &nbsp;·&nbsp; **Body:** free-text + nested atoms — typically one or more Observation atoms per iteration..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `over` | string | yes | the collection being iterated. |
| `as` | string | yes | Python field: as_var; per-iteration variable name. |

**Example:**

```xml
<Loop id="L_01" over="tests" as="test">
  REFER:test — iterate over each test in the suite.
</Loop>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Parallel>` — concurrent independent atoms with no specified ordering.

**Category:** §2 Control &nbsp;·&nbsp; **Slug:** `parallel` &nbsp;·&nbsp; **Body:** free-text + nested atoms that must not depend on sibling order..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |

**Example:**

```xml
<Parallel id="P_01">
  <Observation id="Obs_a">checkout A</Observation>
  <Observation id="Obs_b">checkout B</Observation>
</Parallel>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

## §4 Reference

Atoms that link, store, or surface — long-form back-/forward-links and named-value memory.

### `<Implication>` — long-form forward-link — equivalent to inline IMPLIES:id.

**Category:** §2 Reference &nbsp;·&nbsp; **Slug:** `implication` &nbsp;·&nbsp; **Body:** free-text rationale (optional)..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `next` | string | yes | id of the implied atom. |

**Example:**

```xml
<Implication id="Imp_01" next="F_02">
  REFER:Obs_01 IMPLIES the next finding is met.
</Implication>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Print>` — one-line human-facing summary surfaced to the reader.

**Category:** §2 Reference &nbsp;·&nbsp; **Slug:** `print` &nbsp;·&nbsp; **Body:** single-line text.

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |

**Example:**

```xml
<Print id="Pr_01">Migration complete on branch feat/foo.</Print>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Reference>` — long-form back-link — equivalent to inline REFER:id.

**Category:** §2 Reference &nbsp;·&nbsp; **Slug:** `reference` &nbsp;·&nbsp; **Body:** free-text rationale (optional)..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `to` | string | yes | id of the referenced atom. |

**Example:**

```xml
<Reference id="Ref_01" to="F_01">See prior Finding F_01.</Reference>
```

**Validator rules:** `Reference-complete` (see §4 of the canonical spec).

### `<Storing>` — persist a named value to trace-local memory for later REFER.

**Category:** §2 Reference &nbsp;·&nbsp; **Slug:** `storing` &nbsp;·&nbsp; **Body:** empty.

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `name` | string | yes | key for later REFER:name. |
| `value` | string | yes | stored value. |

**Example:**

```xml
<Storing id="S_01" name="branch_head" value="abc123de"/>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

## §5 Social

Atoms that involve another agent — handoff, question, review.

### `<Handoff>` — pass work to another agent with a named package.

**Category:** §2 Social &nbsp;·&nbsp; **Slug:** `handoff` &nbsp;·&nbsp; **Body:** free-text — what is being handed off and why..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `to` | string | yes | receiving agent name. |
| `package` | string | no | named subset of state being passed. |
| `constraints` | comma-list | no | constraints that survive the handoff. |

**Example:**

```xml
<Handoff id="Ho_01" to="reviewer" package="merge_request" constraints="no_force_push">
  Passing merge to reviewer.
</Handoff>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Question>` — explicit request for external input.

**Category:** §2 Social &nbsp;·&nbsp; **Slug:** `question` &nbsp;·&nbsp; **Body:** free-text — the question itself..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `to` | string | yes | target of the question (e.g. operator). |
| `scope` | string | no | what scope the answer affects. |
| `default` | string | no | default if no answer arrives. |

**Example:**

```xml
<Question id="Q_01" to="operator" scope="merge_strategy" default="merge">
  Merge, rebase, or squash?
</Question>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Review>` — audit another agent's atom and produce a Finding.

**Category:** §2 Social &nbsp;·&nbsp; **Slug:** `review` &nbsp;·&nbsp; **Body:** free-text + a Finding child declaring the review outcome..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `of` | string | yes | id (or trace_id:atom_id) of the atom being reviewed. |
| `reviewer` | string | no | name of the reviewing agent. |

**Example:**

```xml
<Review id="Rv_01" of="F_07" reviewer="auditor">
  <Finding for_hyp="H_review" status="met">Approve.</Finding>
</Review>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

## §6 Meta

Atoms that carry trace-level metadata — goals, constraints, budgets, costs, confidence.

### `<Budget>` — declared spending envelope (tokens / actions / wall_clock_ms).

**Category:** §2 Meta &nbsp;·&nbsp; **Slug:** `budget` &nbsp;·&nbsp; **Body:** free-text rationale (optional)..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `for` | string | no | id of the atom this budget governs (Python field: for_ref). |
| `tokens` | int | no | token ceiling. |
| `actions` | int | no | action-count ceiling. |
| `wall_clock_ms` | int | no | wall-clock ceiling in ms. |

**Example:**

```xml
<Budget id="Bg_01" for="G_01" tokens="50000" wall_clock_ms="600000"/>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Confidence>` — qualitative or numeric confidence attached to another atom.

**Category:** §2 Meta &nbsp;·&nbsp; **Slug:** `confidence` &nbsp;·&nbsp; **Body:** free-text (optional)..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `True` | string | no | id of the atom this Confidence annotates. |
| `level` | float [0,1] | low | medium | high | no | qualitative or numeric strength. |
| `basis` | string | no | short rationale for the level. |

**Example:**

```xml
<Confidence id="Cf_01" on="F_02" level="0.85" basis="3 corroborating Observations"/>
```

**Validator rules:** `Confidence-bounded` (see §4 of the canonical spec).

### `<Constraint>` — hard rule in effect that subsequent decisions must respect.

**Category:** §2 Meta &nbsp;·&nbsp; **Slug:** `constraint` &nbsp;·&nbsp; **Body:** free-text — the constraint itself..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `scope` | string | no | what scope the constraint applies to. |

**Example:**

```xml
<Constraint id="Cn_01" scope="trace">No force-push to main.</Constraint>
```

**Validator rules:** `Constraint-respected` (see §4 of the canonical spec).

### `<Cost>` — observed expenditure (tokens / dollars / wall_clock_ms).

**Category:** §2 Meta &nbsp;·&nbsp; **Slug:** `cost` &nbsp;·&nbsp; **Body:** free-text rationale (optional)..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `for` | string | no | id of the atom this cost is attributed to (Python field: for_ref). |
| `tokens` | int | no | tokens spent. |
| `wall_clock_ms` | int | no | wall-clock spent in ms. |
| `dollars` | float | no | dollars spent. |

**Example:**

```xml
<Cost id="Co_01" for="G_01" tokens="42000" dollars="0.21"/>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<EventRef>` — pointer to an externally recorded run event.

**Category:** §2 Meta &nbsp;·&nbsp; **Slug:** `eventref` &nbsp;·&nbsp; **Body:** empty.

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `instance` | string | no | external system instance name. |
| `run_id` | string | no | external run id. |
| `sequence` | int | no | event sequence number. |
| `for` | string | no | id of the related local atom (Python field: for_ref). |
| `wall_clock` | ISO-8601 | no | wall-clock of the event. |

**Example:**

```xml
<EventRef id="Ev_01" instance="dashboard" run_id="abc123" sequence="42" wall_clock="2026-06-04T12:00:00Z"/>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Goal>` — target proposition the agent is pursuing — may declare criticality.

**Category:** §2 Meta &nbsp;·&nbsp; **Slug:** `goal` &nbsp;·&nbsp; **Body:** free-text — the Goal proposition..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `scope` | string | no | what scope the Goal applies to. |
| `priority` | required | optional | no | required Goals must be closed by a Finding/Concluding. |
| `success_criteria` | comma-list | no | what counts as met. |
| `related_constraints` | comma-list | no | ids of related Constraints. |
| `deadline` | ISO-8601 | no | wall-clock target. |
| `failure_modes` | comma-list | no | named ways the Goal can fail. |
| `criticality` | incidental | bridge | ledger | verifier | kernel | no | risk tier — feeds criticality_non_decreasing. |

**Example:**

```xml
<Goal id="G_01" scope="trace" priority="required" criticality="ledger" deadline="2026-06-05T00:00:00Z">
  Migrate Finding for_goal callers to for_hyp.
</Goal>
```

**Validator rules:** `Goal-declared`, `criticality_non_decreasing` (see §4 of the canonical spec).

## §7 Primitives

v0.3.1 schema-reserved hooks — edges, effects, refs, and step-level metadata.

### `<Edge>` — schema-reserved import / dependency edge on an Observation.

**Category:** §2 Primitives &nbsp;·&nbsp; **Slug:** `edge` &nbsp;·&nbsp; **Body:** free-text (optional)..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `type` | imports | depends | calls | tests | publishes | no | edge kind (Python field: edge_type). |
| `target` | string | no | target symbol / file / atom id. |

**Example:**

```xml
<Edge id="Ed_01" type="imports" target="numpy"/>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Effect>` — schema-reserved side-effect kind (io_write / network / subprocess / mutates_state / pure).

**Category:** §2 Primitives &nbsp;·&nbsp; **Slug:** `effect` &nbsp;·&nbsp; **Body:** free-text (optional)..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `kind` | io_write | network | subprocess | mutates_state | pure | no | effect classification (Python field: effect_kind). |

**Example:**

```xml
<Effect id="Ef_01" kind="io_write"/>
```

**Validator rules:** `Effect-classified` (see §4 of the canonical spec).

### `<Meta>` — schema-reserved Step-level metadata (e.g. criticality).

**Category:** §2 Primitives &nbsp;·&nbsp; **Slug:** `meta` &nbsp;·&nbsp; **Body:** free-text or the parser-recognized ``<Meta:research-mode/>`` pseudo-atom form..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `criticality` | incidental | bridge | ledger | verifier | kernel | no | Step-level risk tier. |

**Example:**

```xml
<Meta id="M_01" criticality="kernel"/>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

### `<Ref>` — schema-reserved generic reference sub-element with type / target.

**Category:** §2 Primitives &nbsp;·&nbsp; **Slug:** `ref` &nbsp;·&nbsp; **Body:** free-text (optional)..

| Attribute | Type | Required | Notes |
|---|---|---|---|
| `id` | string | no | trace-scoped identifier. |
| `type` | test_owner | doc | spec | no | reference kind (Python field: ref_type). |
| `target` | string | no | target id or path. |

**Example:**

```xml
<Ref id="Rf_01" type="test_owner" target="tests/unit/foo/test_bar.py"/>
```

**Validator rules:** none specific to this atom (general well-formedness applies).

---

*Generated by `scripts/notation_reference_gen.py` from `reference/atoms_index.yaml` (Scholia v0.5). If you found a drift between this doc and the canonical spec or the reference implementation, file an issue against `scholialang-spec`.*
