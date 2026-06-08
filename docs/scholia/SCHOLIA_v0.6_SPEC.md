# Scholia v0.6 — Specification

**Status:** CANONICAL (v0.6 content-addressable-substrate release — supersedes the v0.5 substrate-rebuild spec of 2026-06-04).
**Date:** 2026-06-07.
**Authors:** Darren Brewster, Barry Sevig, Claude Opus 4.8.
**Project:** OpenTalon / Doug Fir Labs (the `scholialang-spec` repository is the canonical home).
**Source of truth:** the v0.6 golden-records compatibility manifest (`compatibility-manifest.json`, `spec_version "Scholia v0.6"`, frozen 2026-06-06) and the published `scholialang` v0.6 reference implementation (`scholialang/src/scholialang/`).

This document supersedes `docs/scholia/SCHOLIA_v0.5_SPEC.md`. The v0.5
spec is preserved unchanged at that path with a "superseded" banner; do
not edit it. v0.5 traces remain valid under v0.6 (see §10, §11).

> SCHOLIA_v0.6_SPEC.md is the single source of truth for the Scholia
> reasoning-trace notation. Every downstream surface (canonical agent
> prompt, `scholialang` reference impl, `scholialang-mcp` validator,
> `scholialang.org` spec page, OpenTalon mirror) derives from this
> document. If two sources disagree, this one wins. Where the prose and
> the published `scholialang` v0.6 implementation disagree, the
> implementation is ground truth — file an issue against this spec.

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

v0.6 is a *content-addressable-substrate* release. It keeps the v0.5
atom catalog locked at **32 kinds** and adds three additive substrate
capabilities, all defined byte-for-byte by the published `scholialang`
v0.6 reference implementation:

1. **`canonical_id`** — a content-addressable SHA-256 identity on the
   base `Atom` (§10). The same structural atom emitted from different
   sessions/hosts addresses to the same id, so reasoning can be reused
   across runs without replaying it.
2. **A DAG registry** — a `canonical_id`-keyed atom store whose edges
   are derived from `REFER:sha256` / `IMPLIES:sha256` operators (§12).
3. **A lazy canonical-prelude** — three core render modes
   (`hash_only` / `hash_list` (default) / `inline`) that let a later
   session reference prior atoms by hash instead of replaying their
   full XML (§13).

The closure: an agent in session N+1 can `REFER` to a session-N atom by
its `canonical_id` instead of re-emitting it — the token-savings claim
that motivates v0.6.

What stays the same as v0.5 (see §11 for the full unchanged list):

- The 32-atom closed set, names, and categories.
- XML-shaped tags, the `<Step>` container, composition rules.
- The 11 canonical + 2 emergent operators (v0.6 adds *forms*, not
  operators — §3.4).
- Reference-resolution scope (intra-trace; cross-trace via registry).
- Validator report shape and the `<Meta:research-mode/>` pseudo-atom.
- Fallback semantics (`scholia_fallback: true`).

What v0.6 adds (compact summary; see §10 for the change manifest):

| # | Change | Type |
|---|---|---|
| 1 | `canonical_id` universal base attribute + `compute_canonical_id` hasher | additive |
| 2 | `REFER:sha256:<cid>` / `IMPLIES:sha256:<cid>` operator forms | additive |
| 3 | DAG registry (`canonical_id`-keyed; `{version, atoms, edges}` on disk) | additive |
| 4 | Lazy canonical-prelude — 3 core modes (`hash_only`/`hash_list`/`inline`) | additive |
| 5 | Validator rules `canonical_id_well_formed` (hard-fail) + canonical-id-aware `reference_complete` | additive |
| 6 | `Finding.for_goal` deprecation: removal **deferred from v0.6 to v0.7** | reconciliation |

Pre-v0.6 traces (no `canonical_id`, no registry, no `REFER:sha256`)
MUST parse and validate cleanly. `canonical_id_well_formed` is vacuous
on an atom that carries no `canonical_id` — a v0.5 trace exercises zero
new hard-fail behavior. v0.6 is strictly additive.

> **Scope note (manifest-bounded).** This spec authors *exactly* the
> contracts in the 2026-06-06 golden-records manifest and the published
> `scholialang` v0.6 implementation. It introduces no fields,
> attributes, or rules beyond them. The two quality-recovery prelude
> arms (`hash_semantic_preview`, `selective_inline_plus_hash_only`)
> post-date the manifest and are **not** v0.6 core; they appear only in
> the clearly-labeled experimental extension at §14. `Constraint.severity`
> was considered and dropped; it is not part of v0.6.

---

<!-- BEGIN_GENERATED:atoms_to_spec -->
## §2 Atom catalog

The Scholia v0.6 closed set is **32 atom kinds**, grouped into seven categories. Names are PascalCase. Adding an atom kind is a breaking change and requires a spec version bump. v0.6 is additive at the substrate layer (see §10): the closed set is unchanged from v0.5; only the base `Atom` grows a universal `canonical_id` attribute.

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

> **Universal base attributes (v0.6).** Every atom kind above inherits
> two optional base attributes that are not repeated per kind:
> `id` (trace-scoped local identifier, all versions) and `canonical_id`
> (the v0.6 content address; §10.1). See `reference/notation-reference.md`
> for the rendered base-attribute table.

---

## §3 Operators

Scholia operators are **inline UPPERCASE tokens, not tags**. They are
written inside atom content (`<Finding>... IMPLIES:F_07 ...</Finding>`)
or as bare operator-prefixed references (`REFER:Observation_02`). The
canonical operator set has 11 entries; two additional "emergent"
operators are recognized by the validator with a stability disclaimer.
v0.6 adds no new operators — it adds the `sha256:` *target form* for
`REFER` and `IMPLIES` (§3.4).

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
form; `CANONICAL_OPERATORS` is the validator-ratified frozenset.

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

### §3.3 Data primitives

`LIST`, `SET`, `MAP`, `STRING`, `NUMBER`, and `BOOL` are inline
primitive markers, not operators. Tooling may deserialize them when a
field declares structured content (e.g. `LIST(string): [...]`).

### §3.4 Canonical-id operator forms (NEW in v0.6)

`REFER` and `IMPLIES` gain a content-addressable target form alongside
their local-id form:

| Form | Example | Resolves against |
|---|---|---|
| local-id (v0.5) | `REFER:Finding_02` | the trace's local `id` index |
| canonical-id (v0.6) | `REFER:sha256:8f4a9d2c1b3e` | the trace's `canonical_id` index, then the registry |
| canonical-id forward | `IMPLIES:sha256:8f4a9d2c1b3e` | same; also records a DAG edge (§12) |

The `sha256:` target form is what makes cross-session reuse possible: a
`REFER:sha256:<cid>` in session N+1 dereferences an atom that was first
emitted in session N and persisted in the registry (§12), without that
atom appearing in the current trace. The registry's edge scanner
(`_OP_CANONICAL_RE`) recognizes `REFER:sha256:<cid>` and
`IMPLIES:sha256:<cid>` in atom bodies and records `premise → conclusion`
edges from them.

> **Resolution-boundary note (v0.6 impl ground truth).** The
> reference-completeness validator resolves a `canonical_id` target
> cleanly when it is supplied as a **structured attribute** (e.g.
> `<Reference to="sha256:<cid>">`, `Concluding`/`Finding` attrs) and the
> cid is present in the trace's `canonical_id` index. For an **inline**
> `REFER:sha256:<cid>` operator token whose cid is *not* present in the
> current trace, the v0.6 operator-extraction regex truncates the target
> at the second colon, so `reference_complete` cannot resolve it from
> trace state alone — the registry (§12) is the resolver for genuinely
> cross-session inline refs, and validators that are not passed a
> registry will flag such a bare inline ref. This is a deliberate v0.6
> boundary (the deeper inline-operator-regex change is a v0.7 non-goal,
> matching OpenTalon's v0.6 Phase-3 boundary). Emitters that need a
> cross-trace reference to validate clean under a registry-less validator
> should use the structured `to="sha256:<cid>"` attribute form, or keep
> the referenced atom in-trace. See §13.3 for the parse-time/lazy
> resolution contract.

---

## §4 Validator rules

The v0.6 validator enforces the cumulative rule set: the structural and
reference rules inherited from v0.2–v0.4, the six `<Concluding>`-scoped
rules from v0.5, and the v0.6 content-addressable additions. The
reference implementation in `scholialang/src/scholialang/validator.py`
is the source; `RULE_NAMES` is the machine-readable list and
`SCHOLIA_VALIDATOR_VERSION` reads `0.6.0`.

### §4.1 Existing structural rules (carried forward)

1. **`well_formed`** — every atom has a known kind, or is the
   research-mode pseudo-atom `<Meta:research-mode/>`.
2. **`reference_complete`** — every inline or structured reference
   resolves to an atom in the trace. **v0.6:** a target may be a
   `canonical_id` (`sha256:<hex>`); it resolves against the in-trace
   `canonical_id` index in addition to the local-id index and Step ids
   (see §3.4 resolution-boundary note for the inline-operator caveat).
3. **`decision_closed`** — every `<Deciding>` produces a `<Finding>`
   that names a chosen branch.
4. **`action_recorded`** — every `<Action>` is followed by or contains
   a `<Finding>`.
5. **`hypothesis_evaluated`** — every `<Hypothesis>` has linked
   `<Evidence>` or explicit `<Uncertainty>`.
6. **`retract_consistent`** — every `<Retract>` references an existing
   `<Finding>`, `<Concluding>`, or `<Goal>`.
7. **`constraint_respected`** — no `<Action>` violates an active
   `<Constraint>`.
8. **`goal_declared`** — every `priority="required"` `<Goal>` has a
   closing `<Concluding for_goal="...">` (or `<Finding for_goal="...">`
   for back-compat) with `status` in `met`, `unmet`, `partially_met`,
   or `met_late`. `<Meta:research-mode/>` exempts the trace.
9. **`unknown_operator`** — every inline operator token is in the
   validator-ratified `CANONICAL_OPERATORS` set.
10. **`location_edge_shape`** — `<Observation location="...">` matches
    the `file:start:end` line-span format; `<Edge>` uses the closed
    `type` set.
11. **`v031_optional_fields`** — the v0.3.1 primitive hooks use their
    closed-set attribute values (`<Effect>` kind, `<Ref>` type, `<Meta>`
    criticality, confidence bounds).

### §4.2 v0.5 `<Concluding>`-scoped rules (carried forward)

Three hard-fail (severity = `error`) and three warning rules. All six
are gated on the presence of `<Concluding>` atoms — pre-v0.5 traces
never trigger them.

12. **`for_goal_resolves`** *(hard-fail)* — every `<Concluding>`'s
    `for_goal` resolves to a `<Goal>` id in the same trace.
13. **`refer_at_least_one`** *(hard-fail)* — every `<Concluding>` body
    contains at least one `REFER:` operator pointing to a `<Finding>`,
    `<Observation>`, or `<Evidence>` atom in the same trace.
14. **`criticality_non_decreasing`** *(hard-fail)* — a `<Concluding>`'s
    effective criticality (declared, or the max of cited
    Findings/Observations) must be `>=` the criticality of the Goal it
    closes. `kernel` cannot be closed by `bridge` *unless* the trace
    contains an explicit `<Retract target="goal_id">` documenting the
    downgrade. `CRITICALITY_RANK = {incidental:0, bridge:1, ledger:2,
    verifier:3, kernel:4}`. Elevation is permitted without a Retract.
15. **`no_action_in_concluding`** *(warning)* — Concluding body must
    not contain action-modal verbs (`should`, `will`, `recommend`,
    `choose`, `propose`, including trailing-`s` forms). Heuristic regex.
16. **`single_active_concluding_per_goal`** *(warning)* — at most one
    ACTIVE `<Concluding>` per `<Goal>`. A Concluding targeted by a
    `<Retract>` is no longer active.
17. **`min_confidence_ceiling`** *(warning)* — a Concluding's declared
    `confidence` must not exceed the minimum confidence of its cited
    Findings/Evidence atoms. Warning only.

### §4.3 v0.6 content-addressable rules (NEW)

18. **`canonical_id_well_formed`** *(hard-fail)* — every atom that
    carries a `canonical_id` must match the hash recomputed from its
    structural content via `compute_canonical_id` (§10.1). When an
    atom's `canonical_id` is `None` the rule is **vacuous** (back-compat
    with v0.5 atoms that never carried one). When it is set, the rule
    recomputes and **hard-fails on mismatch** — the canonical signal of
    tamper or stale storage. The mismatch is also expressible as the
    `CanonicalIdMismatch` exception (carrying `atom_id`, `claimed`,
    `computed`) for strict-mode parsers.
19. **`reference_complete` (canonical-id-aware)** — not a new rule
    name, but the v0.6 extension of rule 2: the 4-path resolver
    `resolve_refer` (§13.3) backs reference completeness. A `REFER`
    target resolves via (1) local id, (2) in-trace canonical_id,
    (3) registry lookup by canonical_id, (4) else unresolved.

### §4.4 Report shape

Validators return a `ValidationResult` exposing:

```
{
    "ok":       bool,                       # True iff errors is empty
    "errors":   [{"rule": str, "atom_id": str, "message": str}, ...],
    "warnings": [{"rule": str, "atom_id": str, "message": str}, ...],
    "errors_by_rule":   {rule: [ValidationError, ...], ...},
    "warnings_by_rule": {rule: [ValidationWarning, ...], ...},
    "scholia_validator_version": "0.6.0",
}
```

Unchanged in shape from v0.5 (`errors` / `warnings` arrays with
per-violation `rule` / `atom_id` / `message`). v0.6 adds the
`canonical_id_well_formed` rule name to the breakdown and stamps the
validator version `0.6.0`.

### §4.5 Validity definition

A Scholia v0.6 trace is **valid** if and only if its `errors` array is
empty (`ok == True`). Warnings do not invalidate the trace; they
surface for operator review. A `<Meta:research-mode/>` pseudo-atom at
the top of the trace exempts the trace from rule 8 (goal-declared) but
does not waive any other rule, including `canonical_id_well_formed`.

---

## §5 Reference resolution

(Scope unchanged from v0.5; v0.6 adds the canonical-id and registry
paths — see §13.3 for the full resolver.)

- Identifiers are scoped to the enclosing trace.
- A reference is satisfied if the referenced id exists on any atom or
  `<Step>` *before validation completes* (forward references are
  permitted within a single trace).
- Structured reference attributes include `for`, `for_goal`, `for_hyp`,
  `to`, `next`, `target`, `on`, and `of`.
- Cross-trace references may use `trace_id:atom_id` where the receiving
  validator can resolve them.
- **v0.6:** a reference target may be a `canonical_id` (`sha256:<hex>`),
  resolved against the in-trace canonical_id index and, when a registry
  is supplied, the DAG registry (§12). This is the cross-session reuse
  path.

---

## §6 Composition rules

(Unchanged from v0.5 except for the additive canonical-id form.)

- `<Thinking>` can contain `<Storing/>`, `<Print/>`, hypotheses, inline
  operators, and prose.
- `<Observation>` may carry `timestamp`, `location`, and `confidence`.
- `<Action>` may carry `timestamp` and must produce a `<Finding>`.
- `<Deciding>` must enumerate options and produce a `<Finding>`
  declaring the chosen option.
- `<Concluding>` must declare `for_goal`, contain at least one `REFER:`
  operator, and may declare `confidence` and `criticality`. It must NOT
  contain action-modal verbs (warning, not error).
- `<Alternative>` is only legal inside `<Deciding>`.
- `<Loop>` binds one variable name via `as`.
- `<Review>` must name a target and produce a `<Finding>`.
- `<Parallel>` child atoms must be independent.
- **v0.6:** any atom may carry a `canonical_id` attribute; the parser
  stamps it (§10.2). Children are *not* folded into a parent's
  canonical_id (§10.3) — a v0.7 Merkle-DAG non-goal.

---

## §7 The `<Step>` container

(Unchanged from v0.5.) A trace is `list[Step]`. Each `<Step>` has a
unique-within-trace `id`, a human-readable `name`, and 1..N child
atoms. The `<Step>` itself is not an atom and does not carry a
`canonical_id`.

---

## §8 Fallback semantics

(Unchanged from v0.5.) When validation fails and a consumer cannot use
the trace, the producer falls back to prose-only output annotated with
`scholia_fallback: true`. Fallback is a transport concern, not a
notation change.

---

## §9 Research-mode pseudo-atom

(Unchanged from v0.5.) `<Meta:research-mode/>` at the top of a trace
marks an exploratory run and exempts the trace from rule 8
(goal-declared). It is parser-normalised and lives in
`PSEUDO_ATOM_KINDS`; it is not a closed-set atom.

---

## §10 Versioning — v0.5 → v0.6 change manifest

This section is the authoritative changelog for the substrate. Tools
that migrate traces or persisted state across the v0.5/v0.6 boundary
should consult this list (and `v05-to-v06-migration.md` for migration
recipes).

### §10.1 `canonical_id` — content-addressable identity (NEW)

- **What:** a universal optional base attribute on every atom,
  `canonical_id`, of the form `"sha256:" + first 12 hex chars` of the
  SHA-256 digest of a canonical JSON serialization.
- **Hash input** (byte-for-byte across implementations — `compute_canonical_id`):

  ```
  payload = {
      "kind":    atom.kind,
      "content": atom.content.strip(),
      "attrs":   <sorted kind-specific attrs, provenance + bookkeeping excluded>,
  }
  serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
  canonical_id = "sha256:" + sha256(serialized.encode("utf-8")).hexdigest()[:12]
  ```

- **Excluded from the hash:**
  - *Provenance / session metadata* — `timestamp`, `wall_clock`,
    `run_id`, `sequence`, `instance`. (Two emits of the same structural
    atom from different sessions must address identically.)
  - *Base bookkeeping* — `id`, `canonical_id`, `content` (hashed
    separately as `content`), `children`, `operators`, `kind` (hashed
    separately as `kind`).
  - *REFER / IMPLIES targets and child atoms* — children are hashed
    independently and are not folded in (§10.3).
  - Empty / `None` attrs are dropped, so absence and explicit-`None`
    hash identically.
- **Why 12 hex chars:** a 48-bit prefix is collision-safe at the scale
  of a single registry while keeping the prelude compact (§13). The
  `sha256:` multihash-compatible prefix names the algorithm.
- **Mismatch handling:** `CanonicalIdMismatch(atom_id, claimed,
  computed)` is the exception; `canonical_id_well_formed` (§4.3) is the
  validator rule.

### §10.2 Parser stamping

- The parser stamps `canonical_id` at parse time, after content,
  structured attributes, and children are populated.
- A `canonical_id` present on the wire that **matches** the recomputed
  hash is kept; a wire value that **does not match** is preserved
  verbatim so `canonical_id_well_formed` can surface the tamper. When
  no wire value is present, the computed hash is stamped.
- Hand-built atoms (constructed in Python rather than parsed) do not
  carry a `canonical_id` until one is computed; `Atom` construction
  stays cheap. `compute_canonical_id(atom)` computes it on demand.

### §10.3 Children fold-in is a v0.7 non-goal

The canonical_id hashes `{kind, content, attrs}` only. Child atoms are
hashed independently and are **not** folded into a parent's
canonical_id. A Merkle-DAG identity (parent id derived from children)
is an explicit v0.7 non-goal; do not assume it.

### §10.4 Operator forms (NEW)

- `REFER:sha256:<cid>` and `IMPLIES:sha256:<cid>` (§3.4). Additive; the
  v0.5 local-id forms are unchanged.

### §10.5 DAG registry (NEW)

- A `canonical_id`-keyed atom store with `REFER`/`IMPLIES`-derived DAG
  edges (§12). On-disk format `{version, atoms, edges}`, default path
  `~/.scholia/registry.proofchain.json`. Loads an old flat-JSON file
  (missing `edges` key → empty edge list).

### §10.6 Lazy canonical-prelude (NEW)

- Three core render modes — `hash_only`, `hash_list` (default),
  `inline` (§13). Deterministic; no LLM calls inside the renderer.

### §10.7 Validator changes (NEW)

- **Added:** `canonical_id_well_formed` (hard-fail; vacuous on
  `None`). **Modified:** `reference_complete` resolves canonical_id
  targets (§4.3). `SCHOLIA_VALIDATOR_VERSION` → `0.6.0`.

### §10.8 `Finding.for_goal` disposition (RECONCILIATION)

- v0.5 documented `Finding.for_goal` as "deprecated, removed in v0.6."
  **The published v0.6 implementation preserves it deprecated** — the
  alias is still accepted on read and still emits a
  `DeprecationWarning` once per instance when set in Python. **Removal
  is deferred to v0.7.** Every "removed in v0.6" note across the spec
  repo is reconciled to this disposition. See §15 for the human
  sign-off.

### §10.9 What did NOT change

See §11.

---

## §11 What did NOT change

If your code only depends on the items here, no migration is required.

- The 32-atom closed set, names, categories, and the v0.5 Concluding
  atom.
- XML-shaped tag syntax and the closed-set principle.
- The `<Step>` container shape.
- The 11 canonical + 2 emergent operators (v0.6 adds the `sha256:`
  *target form*, not new operators).
- Reference-resolution scope (intra-trace; cross-trace via registry).
- The validator report shape (`{ok, errors, warnings, ...}`).
- The six v0.5 `<Concluding>`-scoped rules and the criticality ladder
  (`CRITICALITY_RANK`).
- Fallback semantics (`scholia_fallback: true`).
- The `<Meta:research-mode/>` pseudo-atom.
- The v0.3.1 schema-reserved primitive hooks (`<Edge>`, `<Effect>`,
  `<Ref>`, `<Meta>`).

---

## §12 The DAG registry

The v0.6 registry (`scholialang.registry.Registry`) is a
content-addressable atom store plus a derivation DAG over the operator
graph. It is the resolver of last resort for cross-session
`REFER:sha256` (§5, §13.3).

### §12.1 Keying

Atoms are stored keyed by `canonical_id`. `put(atom)` requires
`atom.canonical_id` to be set (parse through the parser or call
`compute_canonical_id` first) and is **idempotent** — re-putting an
already-stored canonical_id is a no-op that returns `False`. The same
structural atom from two sessions addresses to one record.

### §12.2 Edges

When atom A's body carries `REFER:sha256:<B>` or `IMPLIES:sha256:<B>`,
the registry records an edge `premise_id = <B> → conclusion_id = <A>`
(A was derived from B), tagged with the `operator`. Edges are
de-duplicated by `(premise_id, conclusion_id, operator)`. Only
`sha256:` targets form edges — local ids are not unique across sessions.

### §12.3 DAG queries

- `ancestors(cid, depth=…)` — atoms reachable backward via edges
  (premises). `depth=1` = direct premises; `depth=None` = full
  transitive closure. BFS order; referenced-but-never-`put` ids are
  silently skipped (fail-soft).
- `descendants(cid, depth=…)` — atoms reachable forward (referrers).
- `walk_chain(cid)` — the proof chain rooted at `cid`: the node for
  `cid` plus every ancestor, plus every edge whose `conclusion_id` is
  in the included set. `is_complete` is `True` when every referenced
  premise is also an included node.

### §12.4 `kind → ProofNodeType` mapping

The registry maps each Scholia atom kind to a coarse `ProofNodeType`
for downstream consumers that filter by node type. `DERIVED_FACT` is
the catch-all:

| Atom kind | ProofNodeType |
|---|---|
| `Hypothesis` | `HYPOTHESIS` |
| `Observation` | `AXIOM` |
| `Goal` | `DEFINITION` |
| `Constraint` | `DEFINITION` |
| `Concluding` | `THEOREM` |
| `Finding` | `LEMMA` |
| `Evidence` | `DERIVED_FACT` |
| `Contradiction` | `DERIVED_FACT` |
| *(any other kind)* | `DERIVED_FACT` |

### §12.5 On-disk format

```json
{
  "version": "0.6",
  "atoms": { "sha256:<cid>": { "kind": "...", "canonical_id": "sha256:<cid>",
                                "id": "...", "content": "...", "attrs": {...},
                                "children_canonical_ids": [...], "sidecar": {...} } },
  "edges": [ { "premise_id": "sha256:<B>", "conclusion_id": "sha256:<A>",
               "operator": "REFER" } ]
}
```

- Default path: `~/.scholia/registry.proofchain.json`.
- Children collapse to `children_canonical_ids` pointers — the registry
  forms a DAG of canonical_id references, not a nested tree.
- Writes are atomic (`tmp` + `os.replace`) under an `fcntl.LOCK_EX`
  advisory lock so concurrent writers serialize.
- **Back-compat:** a file with no `edges` key loads as an empty edge
  list — an old flat (PRD-01) registry file upgrades transparently.

---

## §13 The lazy canonical-prelude

The prelude (`scholialang.prelude.build_canonical_prelude`) is the
renderer that introduces a later session to the prior session's atoms.
It is the consumer side of the token-savings claim: rather than
replaying full atom XML, it surfaces prior atoms by `canonical_id` so
the agent can `REFER:sha256:<cid>` them.

### §13.0 Determinism invariant (normative)

The prelude renderer is a **pure function**: byte-identical input
produces byte-identical output, the `canonical_id` is the same SHA-256
prefix on every machine, and **there are no LLM calls inside the
renderer or any extractor** (this holds for the experimental arms at
§14 too). Determinism is a normative invariant for every mode.

### §13.1 The three CORE modes

`CORE_PRELUDE_MODES = ("hash_only", "hash_list", "inline")`. These are
the finalized v0.6 lazy-prelude contract per the 2026-06-06 manifest.
Any "official modes" listing must enumerate exactly these three.

Empty input returns the empty string (no header) for every mode.

#### `hash_only` — maximally compact (~30 chars/atom)

One line per atom: the canonical_id and kind, no body preview. Bodies
are fetched on demand from the registry when the emitted trace `REFER`s
the atom.

```
Prior session atoms available via REFER:canonical_id (bodies fetched lazily at parse time):
  - REFER:sha256:8f4a9d2c1b3e (Finding)
  - REFER:sha256:1a2b3c4d5e6f (Concluding)
```

#### `hash_list` — compact + truncated preview (~70–100 chars/atom) — **DEFAULT**

One line per atom: canonical_id, kind, and a flattened body preview
truncated to ~60 chars (the `truncate` parameter, default 60). The body
is lifted from the registry when a record is present, else from the
atom's own `content`.

```
Prior session atoms available via REFER:canonical_id:
  - sha256:8f4a9d2c1b3e (Finding) "All criteria passed; coverage adequate."
  - sha256:1a2b3c4d5e6f (Concluding) "REFER:F_01 IMPLIES the migration is com…"
```

#### `inline` — the v0.5 baseline (full XML)

Each prior atom rendered as a full XML element (emitting the
`canonical_id` attribute). This is the format the v0.6 A/B harness
measures the compact modes against.

```
Prior session atoms (transcript form):

<Finding id="F_01" canonical_id="sha256:8f4a9d2c1b3e" for_hyp="H_01" status="met">All criteria passed; coverage adequate.</Finding>
```

### §13.2 Parameters

`build_canonical_prelude(prior_atoms, registry=None, mode="hash_list",
*, truncate=60, allow_experimental=False)`.

- `prior_atoms` — iterable of v0.5/v0.6 atoms; output order is
  preserved.
- `registry` — optional registry-like object (`.get(cid) -> record |
  None`); registry hits win over the in-memory atom body for previews.
- `mode` — a core mode string; passing an experimental arm without
  `allow_experimental=True` raises `ValueError` (§14).
- `truncate` — body-preview cap for `hash_list`.

### §13.3 REFER:sha256 dereference invariant (normative)

Reference resolution at parse/validate time uses the 4-path resolver
`resolve_refer(trace, target, *, registry=None, …)`; first non-`None`
wins:

1. **local id** — `target` matches a local `id` in this trace (v0.5
   path).
2. **in-trace canonical_id** — `target` matches a `canonical_id` in
   this trace.
3. **registry** — `registry.get(target)` resolves a persisted record
   by canonical_id (the cross-session path).
4. **unresolved** — `None`.

**Fail-soft for dangling refs:** an unresolved canonical_id is not a
parse crash. The resolver returns `None`; the registry's DAG walks skip
referenced-but-absent ids silently; and `reference_complete` reports an
unresolved *attribute-form* canonical_id as a structured violation
rather than raising. (See the §3.4 boundary note for the inline-operator
case.) A registry supplied to the validator extends resolution to
persisted cross-session atoms.

---

## §14 EXPERIMENTAL extension — quality-recovery prelude arms

> **EXPERIMENTAL — NOT v0.6 core.** The two render modes in this
> section were designed by the v0.6 quality-recovery work **after** the
> 2026-06-06 golden-records manifest was frozen (they post-date it,
> ~2026-06-07). They are shipped in the reference implementation for
> continuity with the v06-qf reference and its test corpus, but they
> are **not** part of the finalized v0.6 lazy-prelude contract. They are
> excluded from `CORE_PRELUDE_MODES`, live in `EXPERIMENTAL_PRELUDE_MODES`,
> and are reachable only via `build_canonical_prelude(...,
> allow_experimental=True)` — passing them without the flag raises
> `ValueError`. Treat them as a preview surface that may change or be
> removed; they **may** be promoted to core in a later point release.
> Do not advertise them as finalized v0.6. They are deterministic (no
> in-harness LLM), like the core modes.

`EXPERIMENTAL_PRELUDE_MODES = ("hash_semantic_preview",
"selective_inline_plus_hash_only")`.

### §14.1 `hash_semantic_preview`

Keeps `canonical_id` as the only dereference key, but adds bounded,
deterministically-extracted semantic cues per atom so the next session
has context before choosing refs:

- **cid line** carries `canonical_id`, kind, and criticality (atom attr
  → registry sidecar → registry attrs → default `"normal"`).
- **`summary`** — the body capped at **24 words** (a short body is its
  own summary).
- **`claims`** — up to **2** marker-bearing sentences (markers: `must`,
  `should`, `require`, `ensure`, `guarantee`, `never`, `always`), each
  capped at **14 words**, only when they carry info beyond the summary
  span.
- **`depends_on`** — up to **3** canonical_ids this atom
  REFERs/IMPLIES, extracted deterministically from body + operators.

```
Prior session atoms available via REFER:canonical_id (semantic preview — REFER by cid to hydrate the full record):
  - sha256:8f4a9d2c1b3e (Concluding, kernel)
    summary: REFER:F_01 AND REFER:F_02 imply the migration is complete and safe.
    claims: the rollback path must remain available
    depends_on: [sha256:1a2b3c4d5e6f, sha256:0f0e0d0c0b0a]
```

### §14.2 `selective_inline_plus_hash_only`

Full language for the load-bearing commitments, compression for the
rest:

- Inlines **≤ 3** *critical* atoms (kinds `Finding`, `Concluding`,
  `Deciding`, `Constraint`, or criticality `high`), selected by rank
  (criticality-high → newest → `Finding`/`Concluding` → dependency
  count).
- Inline budget: **≤ 900 chars total**, **≤ 320 chars per atom**;
  critical atoms beyond the budget fall back to hash-only and the header
  notes how many were omitted.
- All non-inlined atoms are rendered hash-only (`- REFER:<cid> (<Kind>)`).

```
Critical prior atoms inlined below; all other prior atoms remain available via REFER:canonical_id.
<Concluding canonical_id="sha256:8f4a9d2c1b3e">
  REFER:F_01 AND REFER:F_02 imply the migration is complete.
</Concluding>
Prior session atoms available via REFER:canonical_id:
  - REFER:sha256:1a2b3c4d5e6f (Observation)
```

---

## §15 `Finding.for_goal` disposition — human sign-off

The v0.5 spec and migration docs stated `Finding.for_goal` would be
**removed in v0.6**. The published v0.6 implementation instead
**preserves it deprecated** (still read-accepted; still emits a
`DeprecationWarning` once per instance when set in Python). This spec
reconciles every "removed in v0.6" note to:

> `Finding.for_goal` is **deprecated** (use `for_hyp`). It remains
> accepted in v0.6 for v0.4/v0.5 back-compat and emits a
> `DeprecationWarning`. **Removal is deferred to v0.7.**

**Human sign-off** (required before this disposition is treated as
final / before the v0.6.0 tag is pushed):

- [ ] I confirm `Finding.for_goal` stays **deprecated, removal deferred
      to v0.7** (the default), matching the published `scholialang` v0.6
      implementation — *or* I have recorded an alternative decision
      below and updated the spec + migration docs to match.

Decision / notes: _______________________________________________

---

## §16 Companion artifacts

- **Atom card** (`reference/atom-card-v0.5.md`) — single-page
  embeddable summary of the 32-atom catalog, carrying the v0.6
  `canonical_id` base-attribute note.
- **Notation reference** (`reference/notation-reference.md`) — full
  per-atom catalog (regenerated for v0.6 from `reference/atoms_index.yaml`),
  including the universal base-attribute table.
- **Migration doc** (`docs/scholia/v05-to-v06-migration.md`) — recipes
  for emitters, validators, consumers, and archival traces across the
  v0.5/v0.6 boundary, plus the `for_goal` disposition.
- **Examples** (`examples/v06/`) — v0.6 traces exercising `canonical_id`,
  a `REFER:sha256` cross-trace reference, and a prelude sample per core
  mode; validated against the published `scholialang` v0.6 validator.
- **Superseded spec** (`docs/scholia/SCHOLIA_v0.5_SPEC.md`) — preserved
  v0.5 spec with a "superseded" banner. Read for history; do not consult
  for current canonical.
- **Consistency test** (`tests/test_spec_consistency.py`) — asserts
  this document stays in sync with the `scholialang.atoms` impl on PR.
- **Reference implementation** (`scholialang/src/scholialang/`) — the
  Python package that owns the atom dataclasses, parser, validator,
  registry, and prelude. Other implementations must match its semantics
  byte-for-byte for `canonical_id`.

---

*Generated portions of §2 derive from `scholialang.atoms._ATOM_CLASSES`
via `scripts/atoms_to_spec.py`. Do not edit §2 by hand; regenerate.
Hand-written sections may be edited freely with PR review.*
