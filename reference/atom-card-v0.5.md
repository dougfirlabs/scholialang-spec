# Scholia v0.5 — Atom Card

**Status:** Canonical reference card. Derived from
[`docs/scholia/SCHOLIA_v0.5_SPEC.md`](../docs/scholia/SCHOLIA_v0.5_SPEC.md).
Embeddable as an iframe from `scholialang.org/spec/` and from
`scholialang-mcp` IDE tooltips.

The Scholia v0.5 closed set is **32 atom kinds** organized into
**seven categories**. The full per-atom reference (attributes, body,
examples, validator rules) lives in
[`notation-reference.md`](notation-reference.md). This card is the
one-page glance.

---

## §1 — Reasoning (3 atoms)

| Atom | Role |
|---|---|
| `<Action>` | External state change. Must produce a Finding. |
| `<Observation>` | External input — command output, file contents, query result. |
| `<Thinking>` | Internal deliberation — not observing, not acting. |

## §2 — Evidence (7 atoms)

| Atom | Role |
|---|---|
| `<Concluding>` | **NEW in v0.5.** Chain-level epistemic close — resolves a Goal via cited atoms. |
| `<Contradiction>` | Two claims that cannot both be true; forces a Deciding. |
| `<Evidence>` | Observation bearing on a Hypothesis (supports / refutes / neutral). |
| `<Finding>` | Conclusion drawn from evidence; evaluates a Hypothesis. |
| `<Hypothesis>` | Explicit conjecture the agent intends to test. |
| `<Retract>` | Revoke a prior Finding (or downgrade-bypass for criticality). |
| `<Uncertainty>` | Confidence below 1 attached to a Finding/Hypothesis/Evidence. |

## §3 — Control (5 atoms)

| Atom | Role |
|---|---|
| `<Alternative>` | Explicitly rejected option inside a Deciding. |
| `<Branch>` | Legal transition out of a Deciding. |
| `<Deciding>` | Action commitment branch point — chooses among alternatives. |
| `<Loop>` | Iteration over a collection (binds one per-iteration variable). |
| `<Parallel>` | Concurrent independent atoms with no specified ordering. |

## §4 — Reference (4 atoms)

| Atom | Role |
|---|---|
| `<Implication>` | Long-form forward-link (equivalent to inline `IMPLIES:id`). |
| `<Print>` | One-line human-facing summary surfaced to the reader. |
| `<Reference>` | Long-form back-link (equivalent to inline `REFER:id`). |
| `<Storing>` | Persist a named value to trace-local memory for later REFER. |

## §5 — Social (3 atoms)

| Atom | Role |
|---|---|
| `<Handoff>` | Pass work to another agent with a named package. |
| `<Question>` | Explicit request for external input. |
| `<Review>` | Audit another agent's atom and produce a Finding. |

## §6 — Meta (6 atoms)

| Atom | Role |
|---|---|
| `<Budget>` | Declared spending envelope (tokens / actions / wall_clock_ms). |
| `<Confidence>` | Qualitative or numeric confidence attached to another atom. |
| `<Constraint>` | Hard rule in effect that subsequent decisions must respect. |
| `<Cost>` | Observed expenditure (tokens / dollars / wall_clock_ms). |
| `<EventRef>` | Pointer to an externally recorded run event. |
| `<Goal>` | Target proposition. May declare `criticality`. |

## §7 — Primitives (4 atoms, v0.3.1 schema-reserved)

| Atom | Role |
|---|---|
| `<Edge>` | Import / dependency edge on an Observation. |
| `<Effect>` | Side-effect kind (`io_write`/`network`/`subprocess`/`mutates_state`/`pure`). |
| `<Meta>` | Step-level metadata (e.g. `criticality`). |
| `<Ref>` | Generic reference sub-element (`type`/`target`). |

---

## Operators (11 canonical + 2 emergent)

Operators are inline UPPERCASE tokens, not tags.

**Canonical:** `REFER`, `IMPLIES`, `AND`, `OR`, `XOR`, `NOT`,
`FORALL`, `EXISTS`, `BEFORE`, `AFTER`, `EQUALS`.

**Emergent (provisional):** `FLIP`, `SURFACE`.

## Criticality ladder

`incidental` < `bridge` < `ledger` < `verifier` < `kernel`.

Enforced by validator rule `criticality_non_decreasing`: a
`<Concluding>` cannot close a `<Goal>` at a lower tier without an
explicit `<Retract>`.

## At-a-glance closure pattern

```xml
<Step id="step_01" name="resolve migration">
  <Goal id="G_01" priority="required" criticality="ledger">
    Migrate Finding for_goal callers to for_hyp.
  </Goal>
  <Hypothesis id="H_01">Every call-site moved.</Hypothesis>
  <Observation id="Obs_01">grep returned zero matches.</Observation>
  <Evidence id="E_01" for="H_01" polarity="supports">REFER:Obs_01.</Evidence>
  <Finding id="F_01" for_hyp="H_01">All migrated.</Finding>
  <Concluding id="C_01" for_goal="G_01" criticality="ledger">
    REFER:F_01 IMPLIES the migration is complete.
  </Concluding>
</Step>
```

---

*Card v0.5 — sourced from `reference/atoms_index.yaml`. The
[full notation reference](notation-reference.md) has attributes,
examples, and validator rules per atom. The
[canonical spec](../docs/scholia/SCHOLIA_v0.5_SPEC.md) has §3
operators, §4 validator rules, and the v0.4→v0.5 change manifest.*
