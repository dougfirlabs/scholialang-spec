# Scholia - Notation Reference (v0.2 draft)

> *Scholia* (structured critical commentary) is a host application's public reasoning-trace notation: reasoning rendered in a form that can be audited, replayed, compared, and verified by agents or humans.

**Status:** v0.2 draft, cut 2026-04-21.
**Authors:** Darren Brewster + Claude Opus 4.7 (2026-04-20), v0.2 RSI run (2026-04-21)
**Project:** a host application / Doug Fir Labs

Scholia v0.2 defines 27 atoms in six categories. `<Meta:research-mode/>` is a parser-recognized pseudo-atom, not part of `ATOM_KINDS`.

---

## 1. Philosophy

Scholia is built on four premises:

1. **Reasoning is data.** Every inference step an agent takes can be represented as structured information.
2. **Readability is a feature.** The same representation that a parser accepts should read well to a human.
3. **Verification requires structure.** A structured trace can be checked for reference completeness, closed decisions, recorded actions, goal status, and related properties.
4. **Composition is essential.** An auditor's Scholia about an agent's Scholia is the canonical Monitor-over-Subject form.

## 2. Lexical structure

- Elements are written as `<Tagname>...</Tagname>` or self-closed `<Tagname/>`.
- Element names are PascalCase, except the pseudo-atom `<Meta:research-mode/>`.
- Attributes use quoted values. v0.2 accepts structured attributes on specific atoms.
- Content is free-form text or nested atoms.
- Operators and primitives are inline UPPERCASE tokens, not tags. Examples: `REFER:step_03`, `IMPLIES:Finding_04`, `LIST(string): [...]`.
- Identifiers are scoped to the enclosing trace.
- Comments use `<!-- ... -->`.

`timestamp` is valid only on `<Observation>` and `<Action>`, and must be ISO-8601. `deadline` on `<Goal>` and `wall_clock` on `<EventRef/>` are also ISO-8601.

## 3. The atom catalog

An atom is a first-class element with fixed semantics.

### 3a. Reasoning atoms

#### `<Thinking>` - internal deliberation

FOL role: proposition context under construction.

The agent is reasoning, not observing or acting. Content may contain hypotheses, references, implications, and prose.

#### `<Observation>` - external input

FOL role: observed ground fact or evidence source.

The agent is reading the world: command output, file contents, query result, or other external input.

```xml
<Observation id="Obs_01" timestamp="2026-04-21T12:00:00-07:00">
  <bash>"python -m pytest tests/unit/scholia"</bash>
</Observation>
```

#### `<Action>` - external state change

FOL role: state-transition event.

The agent is writing to the world: editing a file, pushing a commit, or sending a message. Must be accompanied by a `<Finding>`.

### 3b. Evidence atoms

#### `<Hypothesis>` - explicit conjecture

FOL role: proposition under test.

Names a proposition the agent will test.

#### `<Evidence>` - observation bearing on a hypothesis

FOL role: support/refutation relation.

References one or more hypotheses. `polarity` is `supports`, `refutes`, or `neutral`.

```xml
<Evidence for="H_01" polarity="refutes">merge-tree produced no conflicts.</Evidence>
```

#### `<Finding>` - conclusion drawn from evidence

FOL role: entailed or asserted conclusion.

A finding commits to a proposition. v0.2 adds optional `for_goal` and `status` fields so required Goals can be closed.

```xml
<Finding id="F_final" for_goal="G_01" status="met">All criteria passed.</Finding>
```

#### `<Contradiction>` - detected inconsistency

FOL role: inconsistent conjunction (`P AND NOT P`).

Records two claims that cannot both be true and should force a `<Deciding>`.

#### `<Uncertainty>` - confidence below 1

FOL role: uncertainty annotation on a proposition.

Attached to findings, hypotheses, or evidence. `confidence` is numeric in `[0, 1]` or qualitative.

#### `<Retract>` - revoke a prior finding

FOL role: withdrawal relation over an asserted conclusion.

Names the finding being retracted, the reason, and an optional replacement.

### 3c. Control atoms

#### `<Deciding>` - branch point

FOL role: finite case split.

The agent chooses among alternatives and must produce a `<Finding>` declaring the chosen path.

```xml
<Deciding id="D_01">
  options = LIST:
    - "ship"
    - "defer"
  <Alternative label="defer" rejected_because="Goal is required today"/>
  <Branch of="D_01" label="ship"/>
  <Finding>chose ship</Finding>
</Deciding>
```

Short-form input is accepted and desugared at parse time:

```xml
<Deciding id="D_02" options="ship, defer" chose="ship">tests are green</Deciding>
```

Serializers and renderers emit only the canonical long form.

#### `<Alternative>` - explicitly rejected option

FOL role: negated candidate in a case split.

Only valid inside `<Deciding>`. Carries `label` and `rejected_because`.

#### `<Branch>` - legal transition out of a `<Deciding>`

FOL role: selectable case label.

Each branch names a legal option and can imply later atoms.

#### `<Loop>` - iteration over a collection

FOL role: bounded universal traversal.

References a collection via `over` and binds a per-iteration name via `as`.

#### `<Parallel>` - concurrent independent atoms

FOL role: unordered conjunction.

Child atoms execute without specified ordering and must not depend on sibling order.

### 3d. Reference atoms

#### `<Storing/>` - persist a value to trace-local memory

FOL role: symbol binding.

Stores a named value for later `REFER:` use.

#### `<Print/>` - emit to the human reader

FOL role: non-semantic presentation annotation.

Surfaces a one-line human-facing summary.

#### `<Reference>` - explicit back-link

FOL role: identity/dereference relation.

Long-form equivalent of inline `REFER:id`.

#### `<Implication>` - explicit forward-link

FOL role: entailment edge.

Long-form equivalent of inline `IMPLIES:id`.

### 3e. Social atoms

#### `<Handoff>` - pass work to another agent

FOL role: delegation relation.

Names the receiving agent, package, and constraints.

#### `<Question>` - request for external input

FOL role: open proposition awaiting value.

Carries target, scope, and optional default.

#### `<Review>` - audit another agent's atom

FOL role: meta-evaluation relation.

References another trace or atom and produces its own `<Finding>`.

### 3f. Meta atoms

#### `<Constraint>` - hard rule in effect

FOL role: restriction on valid-state space.

Constrains subsequent decisions and actions.

#### `<Goal>` - target proposition the agent is pursuing

FOL role: target proposition under pursuit.

Declares what the trace or step is trying to accomplish.

```xml
<Goal id="G_01" scope="trace" priority="required">
  Ship Scholia v0.2 extensions.
  success_criteria = LIST:
    - "All v0.2 atoms parse and roundtrip"
    - "Validator rule 8 passes"
  related_constraints = LIST:[REFER:C_01]
  deadline = "2026-04-21T23:59:59-07:00"
  failure_modes = LIST:
    - "Required tests fail"
</Goal>
```

`scope` is `trace` or `step`; `priority` is `required` or `optional`.

#### `<Confidence>` - confidence score on another atom

FOL role: confidence annotation on a proposition.

Dual of `<Uncertainty>`, attached positively via `on`, `level`, and `basis`.

#### `<EventRef/>` - sidecar link to an Events-stream row

FOL role: temporal/event identity relation.

Links an atom or step to a host application GUI event instrumentation.

```xml
<EventRef instance="ot_A" run_id="rsi-20260420-230348" sequence="42" for="Obs_01" wall_clock="2026-04-20T23:03:48-07:00"/>
```

#### `<Budget/>` - declared resource cap

FOL role: resource upper-bound relation.

Declares caps for a Goal, Step, or atom.

```xml
<Budget for="G_01" tokens="50000" actions="20" wall_clock_ms="600000"/>
```

#### `<Cost/>` - measured resource consumption

FOL role: resource measurement relation.

Records measured consumption, usually after an `<Action>`.

```xml
<Cost for="A_01" tokens="1820" wall_clock_ms="4300" dollars="0.12"/>
```

#### `<Meta:research-mode/>` - pseudo-atom marker

FOL role: validation-mode annotation outside the atom vocabulary.

Marks exploratory traces where the operator intentionally opts out of declared-goal expectations. It is recognized by the parser but excluded from `ATOM_KINDS`.

### 3g. FOL projectability - why these tags exist

The public atom vocabulary is shaped so traces can be projected into ordinary first-order-logic-friendly structures: propositions, relations, references, case splits, resource bounds, and state-transition events. These one-line role hints are orientation for readers and tool authors. They are not a formal semantics and do not expose private adjudication mechanics. The design goal is practical: every atom should have a clear logical job, so validators and Monitors can reason about traces without treating the notation as unconstrained prose.

## 4. Logical operators

| Operator | Meaning | Example |
| --- | --- | --- |
| `AND` | Conjunction | `H_01 AND H_02` |
| `OR` | Disjunction | `Finding_02 OR Finding_03` |
| `XOR` | Exclusive disjunction | `path_A XOR path_B` |
| `NOT` | Negation | `NOT Hypothesis_01` |
| `IMPLIES` | Entailment | `Observation_03 IMPLIES Finding_04` |
| `REFER` | Dereference | `REFER:Finding_02` |
| `FORALL` | Universal quantifier | `FORALL(branch IN branches)` |
| `EXISTS` | Existential quantifier | `EXISTS(flake IN tests)` |
| `BEFORE` | Temporal ordering | `Observation_03 BEFORE Deciding_04` |
| `AFTER` | Temporal ordering | `Action_02 AFTER Finding_01` |
| `EQUALS` | Value or identity equality | `hash EQUALS declared_hash` |

## 5. Data primitives

`LIST`, `SET`, `MAP`, `STRING`, `NUMBER`, and `BOOL` are inline primitive markers. Tooling may deserialize them when a field declares structured content.

## 6. The `<Step>` anatomy

A Step wraps one coherent atomic advance.

```xml
<Step id="Step_03" name="Per-branch divergence">
  <Observation id="Observation_02">...</Observation>
  <Finding id="Finding_03">...</Finding>
</Step>
```

Each Step has `id`, `name`, and 1..N child atoms.

## 7. Reference resolution

- Identifiers are scoped to the enclosing trace.
- A reference is satisfied if the referenced id exists on any atom or Step before validation completes.
- Structured reference attributes include `for`, `for_goal`, `to`, `next`, `target`, `on`, and `of`.
- Cross-trace references may use `trace_id:atom_id` where the receiving validator can resolve them.

## 8. Composition rules

- `<Thinking>` can contain `<Storing/>`, `<Print/>`, hypotheses, inline operators, and prose.
- `<Observation>` may carry `timestamp`.
- `<Action>` may carry `timestamp` and must produce a `<Finding>`.
- `<Deciding>` must enumerate options and produce a `<Finding>` declaring the chosen option.
- `<Alternative>` is only legal inside `<Deciding>`.
- `<Loop>` binds one variable name.
- `<Review>` must name a target and produce a `<Finding>`.
- `<Parallel>` child atoms must be independent.

## 9. Validity rules

A Scholia trace is valid if all of the following hold:

1. **Well-formed:** every atom has a known kind, or is the research-mode pseudo-atom.
2. **Reference-complete:** every inline or structured reference resolves.
3. **Decision-closed:** every `<Deciding>` produces a `<Finding>` that names a branch.
4. **Action-recorded:** every `<Action>` is followed by or contains a `<Finding>`.
5. **Hypothesis-evaluated:** every `<Hypothesis>` has linked `<Evidence>` or explicit `<Uncertainty>`.
6. **Retract-consistent:** every `<Retract>` references an existing `<Finding>`.
7. **Constraint-respected:** no `<Action>` violates an active `<Constraint>`.
8. **Goal-declared:** every `priority="required"` `<Goal>` has a `<Finding for_goal="...">` with status `met`, `unmet`, `partially_met`, or `met_late`. `<Meta:research-mode/>` exempts the trace from this rule.

v0.1 traces without Goals remain valid under v0.2.

## 10. Serializations

The same Scholia semantics can be written as XML-ish text, JSON, or YAML. JSON is the canonical machine AST; YAML is config-friendly; XML-ish is optimized for human readability.

## 11. Extension policy

v0.2 does not allow arbitrary user-defined atoms. New atoms require proposal docs under `docs/notation/extensions/`, atom dataclasses, parser/serializer/validator/renderer support as needed, and tests.

## 12. Known open questions

1. **Signing.** Should atoms support cryptographic signing for provenance?
2. **Streaming.** Should traces support append-only streaming semantics for live monitoring?
3. **Grammar.** Should the XML-ish form get a formal EBNF or should JSON Schema be canonical?
4. **Goal success criteria.** Should `success_criteria` remain prose or become a restricted DSL?
5. **Budget enforcement.** Should v0.3 add rule 9: Cost must not exceed declared Budget?

---

## 13. v0.3.1 — reserved primitive hooks (do not emit yet)

v0.3.1 reserves seven schema slots that v0.4 emitters will populate. The validator accepts them as **optional** — absence is the v0.3 shape and stays valid. Operators / agents authoring Scholia by hand **MUST NOT** populate these fields; the rewriter will fill them in v0.4. Canonical spec: [`docs/scholia/SCHOLIA_v0.3.1_SPEC.md`](../scholia/SCHOLIA_v0.3.1_SPEC.md). Companion v0.4 design doc: [`docs/scholia/SCHOLIA_v0.4_SPEC.md`](../scholia/SCHOLIA_v0.4_SPEC.md).

| Reservation | Wire form | Closed set | Status |
|---|---|---|---|
| `id` semantic | `<Atom id="...">` | sequence form OR content-hash form | reserved for v0.4 (v0.3 emitters keep sequence form) |
| `location` on `<Observation>` | `<Observation location="file:start:end">` | regex `^[^:]+:\d+:\d+$` | reserved for v0.4 — do not emit yet |
| `confidence` on `<Observation>` | `<Observation confidence="0.85">` | float `[0.0, 1.0]` | reserved for v0.4 — do not emit yet |
| `<Edge type="..." target="..."/>` | sub-element on `<Observation>` | `type` ∈ {`depends_on`, `imports`, `references`} | reserved for v0.4 — do not emit yet |
| `<Effect kind="..."/>` | sub-element on `<Observation>` | `kind` ∈ {`io_write`, `network`, `subprocess`, `mutates_state`, `pure`} | reserved for v0.4 — do not emit yet |
| `<Ref type="..." target="..."/>` | sub-element on `<Observation>` | `type` ∈ {`test_owner`, `doc_owner`} | reserved for v0.4 — do not emit yet |
| `<Meta criticality="..."/>` | sub-element on `<Step>` | `criticality` ∈ {`kernel`, `verifier`, `ledger`, `bridge`, `incidental`} | reserved for v0.4 — do not emit yet |

`<Ref>` is **not** a rename of `<Reference>`. `<Reference to="...">` is the v0.1 long-form intra-trace back-link to an atom id; `<Ref type="..." target="...">` is a typed external pointer (file path / test selector / doc anchor) that the reference-completeness validator does not resolve.

`<Meta>` is **not** a rename of `<Meta:research-mode/>`. The pseudo-atom remains in `PSEUDO_ATOM_KINDS` (parser-normalised to `<Meta_research_mode/>`); the bare `<Meta>` tag is a new atom in `ATOM_KINDS` carrying a `criticality` attribute.

## 14. Appendix - changelog

- **v0.3.1** (2026-05-22): Reserved seven primitive hooks for v0.4 — schema-only, no emitter changes. Validator carries `scholia_validator_version="0.3.1"`. See [`SCHOLIA_v0.3.1_SPEC.md`](../scholia/SCHOLIA_v0.3.1_SPEC.md) and [`MIGRATION_v0.3_to_v0.3.1.md`](../scholia/MIGRATION_v0.3_to_v0.3.1.md).
- **v0.2** (2026-04-21): Added [`<Goal>`](extensions/v0.2-goal-atom.md), [`timestamp` + `<EventRef/>`](extensions/v0.2-temporal.md), [`<Cost/>` + `<Budget/>`](extensions/v0.2-cost-budget.md), [`<Alternative>`](extensions/v0.2-alternative.md), short-form [`<Deciding>`](extensions/v0.2-deciding-shorthand.md), rule 8, research-mode marker, and FOL-role hints.
- **v0.1** (2026-04-20): Initial draft. 22 atoms across 6 categories, 11 operators, 6 primitives.
