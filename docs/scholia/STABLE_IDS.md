# Scholia v0.4-A — Stable Atom IDs

**Status:** Shipped 2026-05-22
**Spec source:** `docs/scholia/SCHOLIA_v0.4_SPEC.md` (v0.4 enhancement #1)
**Prerequisite:** Scholia v0.3.1 primitive hooks (the `id` attribute schema reservation)
**Authors:** Claude Opus 4.7 (per `.ralph/rsi/rsi-scholia-v0.4-stable-atom-ids.json`)

---

## What v0.4-A delivers

Atom IDs are now derived from atom content. The same atom kind with the
same canonical content produces the same ID on every Atlas sweep, on
every machine, at every point in time. Downstream tooling can diff
atoms across sweeps reliably and reference atoms by ID across artifacts.

```
v0.3:  <Goal id="Goal_01">…</Goal>            # sequence — unstable across sweeps
v0.4:  <Goal id="Goal_a7f3e2c1">…</Goal>      # content-hash — stable
```

The 8-hex suffix is a truncated SHA-256 of the atom's canonical text.
Collision probability at the scale at hand (~1,500 atoms per repo, 2^32
ID space) is negligible.

## Derivation algorithm

```python
from scholialang.stable_ids import derive_atom_id

stable_id = derive_atom_id(kind="Goal", text="Provide a tiny date helper utility module.")
# → "Goal_<8 lowercase hex chars>"
```

Internally:

1. **Canonicalize text** (`canonicalize_text`):
   - Strip `OP:atom_id` tokens — for any closed-set operator
     (`AND`, `OR`, `XOR`, `NOT`, `IMPLIES`, `REFER`, `FORALL`,
     `EXISTS`, `BEFORE`, `AFTER`, `EQUALS`), drop the `:target` suffix
     so just the bare operator name remains. This makes an atom's
     identity invariant under remapping of other atoms' IDs.
   - Strip leading/trailing whitespace
   - Lowercase
   - Collapse internal whitespace (newlines, tabs, multiple spaces) to
     a single space
2. **Hash**: SHA-256 over the UTF-8 encoded canonical text
3. **Truncate**: take the first 8 hex chars
4. **Format**: `f"{kind}_{hex8}"` — e.g. `"Goal_a7f3e2c1"`

The function is pure. No system clock, no random seed, no environment
variables. Same `(kind, text)` always returns the same ID.

## Stability semantics

There are three operational definitions of "stable" — only the first
is a strict contract.

| Property | Status | Definition |
|---|---|---|
| **Deterministic given identical input** | Strict contract | Same `(kind, text)` always returns the same ID, anywhere, anytime. |
| **Stable across regeneration when source is unchanged** | Practical contract | If the rewriter is deterministic and the source file hasn't changed, both sweeps emit the same canonical atom text and the IDs match. |
| **Stable across non-trivial source edits** | Out of scope | When the source changes such that the rewriter produces materially different prose, IDs drift. Downstream tooling should treat drifted IDs as new atoms. |

### Why operator-target stripping is in canonicalization

A `Finding` atom whose content is
``A leaf utility module, IMPLIES:Observation_03.`` references another
atom by ID. The post-hoc remap pipeline rewrites
`IMPLIES:Observation_03` → `IMPLIES:Observation_a7f3e2c1`. Without
operator-target stripping, the Finding's text changes between the
pre-remap and post-remap form, so its hash changes too — and a
downstream consumer that re-hashed the stored text would get a
different ID than the one stored on the atom. That breaks the
downstream-recomputation contract.

Stripping the target leaves the operator (`IMPLIES`) but drops the
specific ID it points at. The Finding's identity now depends only on
its own prose, not on which specific atoms it references. The
structural fact "this Finding implies something" is preserved in the
canonical form (the bare `IMPLIES`); only the target dependency is
shed.

### Step IDs are NOT remapped

`<Step id="step_01">` IDs are positional — they're a container index,
not content. The remap pipeline leaves them alone. Downstream tools
that reference a Step should expect a positional `step_<N>` ID.

## Downstream recomputation contract

Any external tool that has an atom's stored text can recompute its
stable ID directly:

```python
from scholialang.stable_ids import derive_atom_id

# I have an atom from disk; I want to verify its ID:
atom_text = atom.content   # the stored text
expected_id = derive_atom_id(atom.kind, atom_text)
assert atom.id == expected_id   # holds for v0.4 emitter output
```

This contract is exercised by
`tests/integration/scholia/test_stable_ids_resweep.py::test_downstream_can_recompute_stable_id_from_atom_text`.
If you hit a case where the assertion fails, the canonicalization
algorithm has been broken — file an issue.

## Backwards compatibility

| Era | Atom ID shape | v0.4 validator | v0.4 rewriter emission |
|---|---|---|---|
| v0.3 (pre-2026-05-22) | `Goal_01`, `Observation_03` | Accepted | NOT emitted |
| v0.3.1 (2026-05-22) | `Goal_01` reserved as opaque-string-shaped | Accepted | NOT emitted |
| v0.4-A (this release) | `Goal_a7f3e2c1` | Accepted | Emitted by default |
| v0.5 (future) | `Goal_a7f3e2c1` only | Sequence form deprecation TBD | `Goal_a7f3e2c1` only |

**The validator continues to accept sequence-form IDs.** Atlas artifacts
written under v0.3 do not need to be regenerated to remain valid under
v0.4. New artifacts from v0.4 sweeps use content-stable IDs; old
artifacts retain whatever IDs they were written with.

Downstream consumers SHOULD treat atom IDs as opaque strings — never
parse the format expecting one shape or the other. Use
`scholialang.stable_ids.is_stable_id(value)` to disambiguate
v0.3 vs v0.4 forms when needed.

## How the rewriter pipeline uses this

The post-hoc remap is a single line in
`src/example/atlas/scholia_rewriter.py::rewrite_to_scholia`, sitting
between codeblock extraction and validation:

```python
candidate = _strip_codeblock(_extract_text(result))
candidate, _ = remap_to_stable_ids(candidate)   # ← v0.4-A remap step
ok, structural_errors = _validate_codeblock(candidate)
```

The rewriter prompt was deliberately **not** changed. Gemma still
emits sequence-style placeholder IDs (`Goal_01`, `Observation_03`); the
post-hoc remap rewrites them. This decision keeps the prompt simple
and exercises the same code path whether Gemma cooperated on IDs or
not — the safety net is the only path.

`remap_to_stable_ids` is idempotent: a codeblock whose IDs are already
in stable form passes through unchanged. This means it's safe to call
the remap multiple times during integration or migration.

## Re-sweep proof

`tests/integration/scholia/test_stable_ids_resweep.py` proves the
stability contract end-to-end:

* **`test_resweep_unchanged_atoms_have_identical_ids`** — two sweeps
  with identical Gemma output produce bit-identical codeblocks.
* **`test_resweep_whitespace_drift_yields_identical_ids`** — when
  Gemma's output drifts only in whitespace/case, the canonical text is
  the same and the IDs match.
* **`test_resweep_text_drift_drifts_only_affected_atom`** — when one
  atom is genuinely rephrased across sweeps, ONLY that atom's ID
  drifts; every other atom keeps its ID.

## See also

- `docs/scholia/SCHOLIA_v0.4_SPEC.md` — full v0.4 spec
- `docs/scholia/MIGRATION_v0.3.1_to_v0.4-A.md` — migration guide for
  downstream tooling
- `docs/notation/NOTATION_REFERENCE.md` — Scholia notation reference
- `src/scholialang/stable_ids.py` — implementation
- `tests/unit/scholia/test_stable_ids.py` — derivation unit tests
- `tests/unit/atlas/test_scholia_rewriter_stable_ids.py` — rewriter
  pipeline tests
