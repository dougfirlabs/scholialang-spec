# Scholia v0.4 → v0.5 migration guide

**Audience:** consumers of pre-v0.5 traces (validators, dashboards,
enrichers), maintainers of emitters that produce `<Finding>` /
`<Concluding>` atoms, and authors of runtime mirrors such as
`scholialang-mcp`.

**Target reading time:** ~10 minutes.

**Source of truth:** [`SCHOLIA_v0.5_SPEC.md`](SCHOLIA_v0.5_SPEC.md).
This document supersedes the v0.4 draft at
[`legacy/SCHOLIA_v0.4_SPEC.md`](legacy/SCHOLIA_v0.4_SPEC.md).

---

## §1 What changed (4 items)

v0.5 is an additive substrate-rebuild release. Pre-v0.5 traces parse
and validate cleanly under v0.5; the four items below describe what is
new, deprecated, or stricter for **fresh** v0.5 emission.

### §1.1 `<Concluding>` atom added

- **Kind:** new atom in the closed set. Catalog count: 31 → 32.
- **Category:** Evidence (alphabetical between `<Branch>` and
  `<Confidence>`).
- **Required attribute:** `for_goal` — the id of the `<Goal>` the
  Concluding closes.
- **Optional attributes:** `confidence` (float 0-1), `criticality`
  (one of `incidental` / `bridge` / `ledger` / `verifier` / `kernel`).
- **Semantics:** distinct from `<Deciding>`. `<Concluding>` makes an
  epistemic claim about a stated Goal ("the work is done, here's why");
  `<Deciding>` commits to an action among alternatives ("I'm going to
  do X"). Emitters that previously used `<Finding for_goal="...">` to
  close required Goals should migrate to `<Concluding>`.

**Migration:** existing traces are unchanged. Fresh emitters should
reach for `<Concluding>` when answering "is this Goal met?" and reach
for `<Deciding>` when answering "which option do we take?".

### §1.2 `<Finding>` migration: `for_goal` → `for_hyp`

- **What:** the canonical reference attribute on `<Finding>` is now
  `for_hyp`, not `for_goal`. A Finding evaluates a Hypothesis, not a
  Goal — the rename clarifies the semantic.
- **Backwards compatibility:** v0.4 traces containing
  `<Finding for_goal="...">` parse without warning. The parser routes
  the legacy attribute through `Finding.from_legacy()` which copies
  `for_goal` into `for_hyp` internally.
- **Deprecation warning:** fresh v0.5 code that programmatically
  constructs `Finding(for_goal=...)` emits a `DeprecationWarning` once
  per instance. Migrate call sites soon. (**Reconciled in v0.6:** the
  alias is **not** removed in v0.6 — the published v0.6 implementation
  keeps `for_goal` deprecated and **defers removal to v0.7**. See
  `SCHOLIA_v0.6_SPEC.md` §10.8 / §15.)

**Migration recipe** for emitter code:

```python
# Before (v0.4):
Finding(id="F_01", for_goal="G_01", status="met")

# After (v0.5):
Finding(id="F_01", for_hyp="H_01", status="met")
# (or, if you really mean a Goal-close — emit a Concluding instead:)
Concluding(id="C_01", for_goal="G_01")
```

**Migration recipe** for trace XML emission:

```xml
<!-- Before (v0.4): -->
<Finding for_goal="G_01" status="met">All criteria passed.</Finding>

<!-- After (v0.5): -->
<Finding for_hyp="H_01" status="met">Hypothesis met.</Finding>
<Concluding for_goal="G_01">
  REFER:F_01 IMPLIES the Goal is met.
</Concluding>
```

### §1.3 Six new validator rules

The v0.5 validator adds 6 rules on top of the 11 carried forward from
v0.4. Three hard-fail, three warning. **All six are gated on the
presence of `<Concluding>` atoms** — a v0.4 trace (no Concluding)
triggers zero new rules.

| Rule | Severity | What it checks |
|---|---|---|
| `for_goal_resolves` | error | every Concluding's `for_goal` resolves to a Goal in the trace |
| `refer_at_least_one` | error | every Concluding body has at least one `REFER:` operator |
| `criticality_non_decreasing` | error | Concluding's effective criticality is `>=` its Goal's tier (unless Retract bypasses) |
| `no_action_in_concluding` | warning | Concluding body must not contain modal verbs like `should`, `will`, `recommend`, `choose`, `propose` |
| `single_active_concluding_per_goal` | warning | at most one active Concluding per Goal (Retracted ones don't count) |
| `min_confidence_ceiling` | warning | declared `confidence` ≤ min of cited Findings/Evidence confidences |

The full rule definitions live in §4.2 of the canonical spec.

**Migration for vendored validators** (e.g. `scholialang-mcp`'s
vendored validator and private product mirrors):

- Add the 6 rule implementations following
  `scholialang/src/scholialang/validator.py` as the reference.
- Wire them into the existing rule dispatcher.
- Add a guard: if the trace contains no `<Concluding>`, short-circuit
  all six rules (this preserves v0.4 back-compat).
- Add tests for back-compat: every existing v0.4-shaped fixture must
  pass v0.5 validation with no new errors or warnings.

### §1.4 `criticality_non_decreasing` enforcement

- **What:** a `<Concluding>` with `criticality="bridge"` cannot close a
  `<Goal criticality="kernel">` unless the trace contains an explicit
  `<Retract target="G_01" reason="...">` documenting the downgrade.
- **Why:** prevents silent epistemic erosion. A kernel-class concern
  should not be resolved away as bridge-class without recorded
  justification.
- **The ladder:** `CRITICALITY_RANK = {incidental: 0, bridge: 1,
  ledger: 2, verifier: 3, kernel: 4}`. Available as a module-level
  constant on `scholialang.atoms`.
- **Elevation is permitted:** declared criticality > chain max does
  NOT trigger the rule. A trace can elevate (a `bridge` chain that
  discovers a kernel-class systemic concern can close with
  `criticality="kernel"`).

**Migration for runtime emitters:** start setting `criticality` on
`<Goal>` when the Goal is on the kernel / verifier / ledger / bridge
tier. Goals with no `criticality` skip the downgrade check (the rule
fires only when both ends are declared).

---

## §2 What did NOT change

If your code only depends on the items listed here, no migration is
required.

- XML-shaped tag syntax.
- The 28 atom kinds from v0.4 (all 31 atoms minus the v0.5 Concluding
  addition — Action, Alternative, Branch, Budget, Confidence,
  Constraint, Contradiction, Cost, Deciding, Edge, Effect, EventRef,
  Evidence, Goal, Handoff, Hypothesis, Implication, Loop, Meta,
  Observation, Parallel, Print, Question, Ref, Reference, Retract,
  Review, Storing, Thinking, Uncertainty — total 30, plus Finding for
  31).
- The 11 canonical + 2 emergent operators.
- The 11 validator rules carried forward (well-formed,
  reference-complete, decision-closed, action-recorded,
  hypothesis-evaluated, retract-consistent, constraint-respected,
  goal-declared, observation-locatable, effect-classified,
  confidence-bounded).
- Validator report shape (`{errors: [...], warnings: [...]}` with
  per-violation `rule`/`atom_id`/`message`/`severity` keys).
- `<Meta:research-mode/>` pseudo-atom semantics.
- Fallback semantics (`scholia_fallback: true` on validation failure).
- The `Step` container shape (`<Step id=... name=...>`).
- The v0.3.1 schema-reserved primitive hooks (`<Edge>`, `<Effect>`,
  `<Ref>`, `<Meta>`).

---

## §3 Step-by-step migration

For a typical consumer that has v0.4 emitters in production:

1. **Upgrade the parser / atoms package** to v0.5. v0.4 traces parse
   cleanly; no test should fail. If a test fails, file an issue
   against `scholialang` — the back-compat contract is violated.
2. **Add `Goal.criticality`** to existing Goal emitters when the Goal
   is on a tier you care about. This enables the
   `criticality_non_decreasing` rule but does not require Concluding
   adoption.
3. **Identify Finding emitters that close required Goals.** Pattern:
   `<Finding for_goal="G_..." status="met">`. Decide whether each one
   is really a Goal-close (migrate to `<Concluding>`) or a
   Hypothesis-evaluation that happened to reference a Goal (migrate
   `for_goal` → `for_hyp`).
4. **Add `<Concluding>` emission** to the agent's closure shape. The
   canonical pattern is in §6 of the spec doc; the at-a-glance form
   is in the atom card.
5. **Vendor / sync the v0.5 validator** wherever you have a copy.
   Reference: `scholialang/src/scholialang/validator.py`. Validators
   in `scholialang-mcp` and private product mirrors need coordinated ports.
6. **Run the test corpus** against your trace fixtures. Expected
   behavior: zero new errors for v0.4-shaped fixtures; new errors only
   on fresh v0.5 fixtures that exercise the new rules.
7. **Watch logs for `DeprecationWarning: Finding.for_goal`** — those
   are call sites to migrate before v0.6.

---

## §4 Migrating archival traces

**No action required.** Archival v0.4 traces are read-only history;
they remain valid v0.5 traces. The v0.5 parser routes legacy `for_goal`
through `Finding.from_legacy()` *without* emitting a deprecation
warning, so re-reading archival corpora does not spam logs.

If you re-emit archival traces for any reason (e.g. dashboard replay),
treat the re-emission as a fresh emit and apply the §3 migration to
the producer.

---

## §5 FAQ

**Q. Do my v0.4 dashboards break?**
A. No. The validator report shape is unchanged, and unknown rule names
in the `errors` / `warnings` arrays should be treated as pass-through.
If your dashboard hard-codes a rule-name allowlist, expand it to
include the 6 new rule names.

**Q. Can I emit v0.5 atoms in a trace consumed by a v0.4 validator?**
A. The v0.4 validator does not recognize `<Concluding>` (it will treat
it as an unknown kind and fail the well-formed rule). Upgrade
consumers to v0.5 before emitting v0.5-only atoms. Alternatively,
gate Concluding emission behind a config flag while the rollout
proceeds.

**Q. What about `<Decision>` — the singular form?**
A. There is no `<Decision>` atom in any version of Scholia. The
canonical name is `<Deciding>` (v0.2 onwards). If you see `<Decision>`
in third-party documentation, that's a misrepresentation predating the
v0.5 reconciliation. The 2026-06-04 drift audit flagged this; the v0.5
spec corrects it.

**Q. Will `<Finding for_goal="...">` keep working forever?**
A. It parses cleanly through v0.5 **and v0.6** — the alias stays
deprecated, not removed, in v0.6. **Removal is deferred to v0.7**
(reconciled against the published v0.6 implementation; see
`SCHOLIA_v0.6_SPEC.md` §10.8 / §15). Plan to migrate call sites before
v0.7; the `DeprecationWarning` surfaces the ones to fix.

**Q. What's the relationship between `<Concluding>` and `<Finding>`?**
A. `<Finding>` is granular ("this hypothesis evaluates to met").
`<Concluding>` is chain-level ("REFER:F_01 AND REFER:F_02 IMPLIES the
Goal is met"). One Goal closure produces zero-or-more Findings and
exactly one active Concluding.

---

## §6 References

- **Canonical spec:** [`SCHOLIA_v0.5_SPEC.md`](SCHOLIA_v0.5_SPEC.md).
- **Drift audit** (origin of this migration): see the 2026-06-04
  drift audit; it identified the 12 gaps this v0.5 release closes.
- **PRD bundle:** the `rsi-scholia-v0.5-*` PRDs in the private planning
  archive — PRD-01 added Concluding, PRD-02 added the six validator rules,
  PRD-03 reconciled the spec docs (this guide is part of PRD-03).
- **Reference impl:** `scholialang/src/scholialang/{atoms,validator}.py`.
