# Scholia v0.3.1 → v0.4-A migration guide

**Audience:** authors of downstream Scholia consumers — parsers,
diff tools, atlas dashboards, RSI trace readers.
**Scope:** v0.4-A introduces content-derived stable atom IDs. Every
other v0.4 enhancement (location, confidence, Edge, Effect, Ref, Meta)
was schema-reserved in v0.3.1 and has its own migration notes there.

## TL;DR

Treat atom IDs as opaque strings. Stop parsing them as `Kind_<int>`.
If you previously diffed atoms by ID and got noise across regeneration,
stop diffing by ID and start diffing by content key — or upgrade to
v0.4-A emitters and ID-based diff becomes reliable.

If you need to recompute or verify an atom's ID, call
`scholialang.stable_ids.derive_atom_id(kind, text)`.

## What changed

| Slot | v0.3 / v0.3.1 | v0.4-A |
|---|---|---|
| Sequence ID emission | `Goal_01`, `Observation_03` | Not emitted by the rewriter (the post-hoc remap pipeline rewrites them to stable form before persistence) |
| Stable ID emission | Not emitted | `Goal_a7f3e2c1` — derived from atom content via SHA-256 |
| Validator acceptance | Sequence form only | **Both** forms accepted (sequence form will be deprecated in v0.5) |
| `id` attribute contract | Local-positional within Step | Opaque string; content-derived when sourced from the v0.4 rewriter |
| `REFER`/`IMPLIES`/`NOT` operator targets | `IMPLIES:Observation_03` | `IMPLIES:Observation_a7f3e2c1` after the post-hoc remap |
| `for_goal`, `target`, `for_ref`, `next`, `of`, `on` reference attrs | Carry sequence IDs | Carry stable IDs after the post-hoc remap |
| `Step` container ID | `step_01` | **Unchanged** — Step IDs stay positional |

## What to do (by consumer role)

### Parsers

Already done. Both the `scholialang.parser` AST parser and any
custom parser that accepts arbitrary string `id` values will continue
to work. There is no format check on `id` at the parser layer.

If your parser regexes against `id="Goal_\d+"` style patterns, **drop
the format assumption**. Match against `id="([^"]+)"` and treat the
captured string as opaque.

### Diff tools

If you previously diffed Atlas artifacts by atom ID and saw spurious
"renamed atom" noise across regenerations, the noise should subside as
artifacts get re-swept under v0.4-A. Atoms whose content is unchanged
will land on the same stable ID across sweeps.

For mixed-version artifact corpora (some v0.3, some v0.4):

```python
from scholialang.stable_ids import derive_atom_id, is_stable_id

if not is_stable_id(atom.id):
    # v0.3 sequence ID. Diff by content key instead, OR recompute
    # the stable ID and use it as the diff key.
    diff_key = derive_atom_id(atom.kind, atom.content)
else:
    diff_key = atom.id
```

### Atlas dashboards

UI surfaces that display atom IDs should treat them as opaque tokens.
Don't render IDs in a way that implies the number portion has meaning
(e.g. "Goal #1, Goal #2"). The 8-hex suffix is a hash fragment, not a
sequence number.

If you display IDs for debugging, the bare `<8hex>` slice is fine —
truncate further if you need (e.g. the leading 4 chars) and document
that what you're showing is a hash prefix.

### RSI trace readers / downstream tooling that stores IDs

If your tool persists atom IDs as references (e.g. "this Slack alert
fires when atom `Goal_03` enters `unmet` status"), migrate those
references to content-stable form. The cleanest path:

1. Read the source artifact today
2. For each persisted reference, look up the atom and recompute:
   ```python
   from scholialang.stable_ids import derive_atom_id
   new_id = derive_atom_id(atom.kind, atom.content)
   ```
3. Update the persisted reference to use `new_id`

After migration, your references will continue to resolve correctly
across re-sweeps as long as the atom's content stays semantically
stable. If the content changes, your reference becomes stale — that's
the same failure mode you had before, just now made visible by a
changed ID rather than hidden behind a stable sequence number.

### Atom emitters (NOT the rewriter)

If your tool emits Scholia atoms directly (not via the a host application
rewriter), you have two options:

- **Option A (recommended):** emit sequence-form IDs (`Goal_01`) and
  pipe your output through `scholialang.stable_ids.remap_to_stable_ids`
  before persisting. This is the same code path the rewriter uses; you
  get stable IDs for free.
- **Option B:** call `derive_atom_id(kind, text)` yourself and emit
  the result as the `id` attribute. Slightly more work but no
  dependency on the remap pipeline.

In both cases, the validator accepts the output. Don't roll your own
hash function — the canonicalization rules
(operator-target stripping + whitespace collapse + lowercase) are
load-bearing and the algorithm is the single source of truth.

## Things NOT to do

- **Don't parse the format.** `Goal_a7f3e2c1.startswith("Goal_")` is
  the most you should assume. The 8-hex slice is implementation detail
  and may change length in future versions if collision rates demand
  it.
- **Don't try to compute a stable ID by hand.** The canonicalization
  has subtleties (operator-target stripping) that look minor and
  matter in practice. Always go through `derive_atom_id`.
- **Don't depend on stability across non-trivial source edits.** When
  the rewriter rephrases an atom, its ID drifts — that's expected, not
  a bug. If you need cross-version atom tracking, use the
  `git log -p`-style approach of diffing prose, not ID stickiness.
- **Don't rewrite v0.3 artifacts on disk just to update their IDs.**
  The validator accepts both forms; let v0.4-A artifacts pile up
  naturally as the next sweep regenerates them.

## See also

- `docs/scholia/STABLE_IDS.md` — the v0.4-A spec doc (algorithm,
  contract, semantics)
- `docs/scholia/SCHOLIA_v0.4_SPEC.md` — full v0.4 release plan
- `docs/scholia/MIGRATION_v0.3_to_v0.3.1.md` — the prior migration
  guide (schema-reservation step)
- `src/scholialang/stable_ids.py` — exported API
