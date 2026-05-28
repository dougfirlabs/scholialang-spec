# Scholia v0.3.1 — Minimal-But-Extensible Primitive Hooks

**Status:** approved (2026-05-22)
**Authors:** Claude Opus 4.7 (RSI run)
**Predecessor:** Scholia v0.3 (shipped — closed-set validator, 11 operators ratified)
**Successor:** Scholia v0.4 (DRAFT — `docs/scholia/SCHOLIA_v0.4_SPEC.md`)

---

## Why this point release exists

v0.3 is operationally proven (1,529 atoms validated in the 2026-05-22
production backend sweep, 99.3% success rate) but Codex's read-only analysis
(see `docs/reports/2026-05-22-codex-atlas-token-analysis.md`) named
eight enhancements that would graduate Scholia from "orientation-grade"
to "precision-refactor-grade." Those enhancements compose into Scholia
v0.4.

If v0.4 atoms shipped before v0.3 consumers had a permissive parser,
every external tool reading Scholia would break. The standards-body
discipline is to define the interface FIRST, populate LATER. v0.3.1 is
that interface release: it RESERVES the schema slots without changing
any emitter. The rewriter continues emitting v0.3 atoms unmodified.

## Backwards-compatibility promise

Every v0.3 atom that parsed and validated before this release MUST
parse and validate unchanged after this release. The corpus-replay
regression test (`tests/integration/scholia/test_corpus_replay.py`)
exists to enforce that promise.

## Reserved schema slots

v0.3.1 reserves seven primitive hooks. Each is optional; absence is
the normal v0.3 shape; presence is the v0.4 shape.

### 1. `id` attribute on atoms — semantic shift reserved

| Aspect | v0.3 | v0.3.1 | v0.4 |
|---|---|---|---|
| Allowed values | `Goal_01`, `Obs_03`, etc. (sequence form) | Either sequence form OR content-hash form | Content-hash form (sequence form deprecated in v0.5) |
| Validator behavior | Accepts | Accepts both | Accepts both; warns on sequence form post-adoption |
| Emitter behavior | Sequence form | Sequence form (no change) | Content-hash form |

The semantic shift is migration-only — v0.3.1 readers accept either,
so v0.4 emitters land non-breaking. **v0.3.1 does not change the
emitter.**

### 2. `location` attribute on `<Observation>` — line span

```xml
<Observation id="Obs_03" location="src/foo.py:42:55" timestamp="...">
  Function `bar` is defined here.
</Observation>
```

- **Format**: `"file:start:end"` where `start` and `end` are 1-indexed
  line numbers. `file` is a repo-relative path.
- **Validation**: when present, MUST match the regex
  `^[^:]+:\d+:\d+$`. Validator rejects malformed values.
- **Absence**: no semantics inferred — v0.3 atoms simply lack the
  attribute.
- **Population**: v0.4-B (`code-graph-metadata`) populates from
  pyright/AST-walk; v0.3.1 emitters MUST NOT populate.

### 3. `confidence` attribute on `<Observation>` — uncertainty

```xml
<Observation id="Obs_03" confidence="0.85">
  Module-level imports appear unused.
</Observation>
```

- **Format**: float string in `[0.0, 1.0]`.
- **Validation**: parser raises `ScholiaParseError` on out-of-range
  or non-float values; validator emits `RULE_V031_OPTIONAL_FIELDS`
  error on AST-reconstituted traces with the same defect.
- **Absence**: semantically equivalent to `1.0` (unstated = confident).
- **Population**: v0.4-D (`confidence-scoring`) populates; v0.3.1
  emitters MUST NOT populate.
- **Relation to existing `<Uncertainty>`/`<Confidence>` atoms**: the
  attribute is a per-observation inline form; the atoms remain the
  long-form way to attach uncertainty/confidence to any atom. The
  inline attribute is preferred for v0.4 rewriter output because it
  doesn't require a separate atom round-trip through the validator.

### 4. `<Edge type="..." target="..."/>` sub-element on `<Observation>` — dependency graph

```xml
<Observation id="Obs_03" location="src/foo.py:42:55">
  Function bar dispatches to baz.
  <Edge type="depends_on" target="src/baz.py"/>
  <Edge type="imports" target="scholialang.atoms"/>
</Observation>
```

- **Attributes**:
  - `type` ∈ {`depends_on`, `imports`, `references`} (closed set).
  - `target` is a string — repo-relative path or import-path. v0.3.1
    does NOT validate target resolution (it is not a Scholia atom id).
- **Absence**: no edges inferred.
- **Multiplicity**: zero or more `<Edge>` children per `<Observation>`.
- **Population**: v0.4-B; v0.3.1 emitters MUST NOT populate.

### 5. `<Effect kind="..."/>` sub-element on `<Observation>` — side effects

```xml
<Observation id="Obs_03" location="src/network/client.py:10:80">
  Module performs HTTP requests on import.
  <Effect kind="network"/>
  <Effect kind="io_write"/>
</Observation>
```

- **Attribute**: `kind` ∈ {`io_write`, `network`, `subprocess`,
  `mutates_state`, `pure`} (closed set).
- **Default**: absence is NOT equivalent to `pure` — it is "unknown."
  Explicit `<Effect kind="pure"/>` asserts purity.
- **Multiplicity**: zero or more `<Effect>` children per `<Observation>`.
- **Population**: v0.4-C; v0.3.1 emitters MUST NOT populate.

### 6. `<Ref type="..." target="..."/>` sub-element on `<Observation>` — typed cross-references

```xml
<Observation id="Obs_03" location="src/foo.py:42:55">
  <Ref type="test_owner" target="tests/unit/foo/test_bar.py::test_bar"/>
  <Ref type="doc_owner" target="docs/reference/foo.md"/>
</Observation>
```

- **Attributes**:
  - `type` ∈ {`test_owner`, `doc_owner`} (closed set).
  - `target` is a string — file path, test selector, or doc anchor.
    v0.3.1 does NOT validate target resolution.
- **Multiplicity**: zero or more `<Ref>` children per `<Observation>`.
- **Distinction from `<Reference>`**: `<Reference to="...">` is the
  v0.1 long-form back-link to an atom id. `<Ref type="..." target="...">`
  is a typed external reference to a file/test/doc artifact. They are
  separate atoms with different roles.
- **Population**: v0.4-C; v0.3.1 emitters MUST NOT populate.

### 7. `<Meta criticality="..."/>` sub-element on `<Step>` — risk flag

```xml
<Step id="step_03" name="Verifier path edit">
  <Meta criticality="verifier"/>
  <Observation id="Obs_03">...</Observation>
</Step>
```

- **Attribute**: `criticality` ∈ {`kernel`, `verifier`, `ledger`,
  `bridge`, `incidental`} (closed set).
- **Default**: absence is semantically equivalent to `incidental`.
- **Distinction from `<Meta:research-mode/>` pseudo-atom**: the
  pseudo-atom remains parser-recognized as before (`PSEUDO_ATOM_KINDS`);
  the bare `<Meta>` is a new closed-set atom in v0.3.1 and is
  registered in `ATOM_KINDS`. The two never collide because pseudo-
  atom normalization (`_normalise_pseudo_atoms`) only matches the
  exact `<Meta:research-mode/>` literal.
- **Multiplicity**: zero or one `<Meta>` per Step (v0.3.1 does not
  forbid multiples, but v0.4 emitters SHOULD emit at most one).
- **"Do not edit casually" derived signal**: `criticality !=
  "incidental"` IS the marker; no separate `do_not_edit` attribute.
- **Population**: v0.4-C; v0.3.1 emitters MUST NOT populate.

## Validator changes

The validator (`src/scholialang/validator.py`) gains:

1. A new module-level constant `SCHOLIA_VALIDATOR_VERSION = "0.3.1"`.
2. A new rule `RULE_V031_OPTIONAL_FIELDS = "v031_optional_fields"`
   that re-validates the closed-set values on the AST. This is a
   defensive layer for traces reconstituted from JSON/YAML; the
   parser raises `ScholiaParseError` on the same defects when input
   comes through XML-ish.
3. `ValidationResult` now carries a `scholia_validator_version` field
   so downstream tools can branch on validator version.
4. `check_reference_complete` skips the `target` attribute on `<Edge>`
   and `<Ref>` atoms because their target is a file path / test
   selector / doc anchor, not an in-trace atom id.

## Backwards-compatibility verification

- `tests/integration/scholia/test_corpus_replay.py` loads every
  fixture under `tests/fixtures/scholia/v03_known_corpus/` (mixed
  parse + JSON forms) and asserts 100% validation pass.
- `tests/unit/scholia/test_validator_v031.py` exhaustively covers
  per-field acceptance + rejection.

## What v0.3.1 explicitly does NOT do

- **Does NOT modify the rewriter**: no new fields are emitted.
  Population is v0.4's job.
- **Does NOT introduce new operators**: closed-set operator vocabulary
  unchanged.
- **Does NOT change Step/Goal/Observation/Hypothesis/Finding/Concluding
  semantics**: those atoms gain only optional attributes / sub-elements.
- **Does NOT allow arbitrary attribute extension**: the strict closed
  set still holds. Unknown attributes/sub-elements outside the
  v0.3.1 schema are rejected (or silently dropped by the parser when
  the lenient legacy code path applies — see `_apply_attrs`). The
  validator's strict-closed-set contract is preserved.

## Migration paths

See `docs/scholia/MIGRATION_v0.3_to_v0.3.1.md` for the consumer-side
checklist. Authoring guidance for operators / agents writing Scholia
is in `docs/notation/NOTATION_REFERENCE.md` under the v0.3.1 section.

## Companion artifacts

- `docs/reports/2026-05-22-codex-atlas-token-analysis.md` — Codex's
  read-only enhancement analysis that motivated v0.3.1 + v0.4.
- `docs/scholia/SCHOLIA_v0.4_SPEC.md` — what v0.3.1's reservations
  feed into.
- `docs/scholia/MIGRATION_v0.3_to_v0.3.1.md` — consumer-side
  migration guide.
- `docs/notation/NOTATION_REFERENCE.md` §13 — operator-facing
  authoring guidance for v0.3.1.
