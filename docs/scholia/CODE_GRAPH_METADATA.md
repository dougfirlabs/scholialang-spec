# Scholia v0.4-B — Code-Graph Metadata

**Status:** Shipped (PRD `rsi-scholia-v0.4-code-graph-metadata`)
**Date:** 2026-05-22
**Scope:** Two of the eight v0.4 enhancements from the Codex Atlas analysis — exported symbols with line spans, and imported symbols / dependency edges.

This document is the operational contract for the location attribute, the Edge sub-element, and the reverse-index pass. Tooling that consumes Atlas artifacts should read this — the format spec (`SCHOLIA_v0.4_SPEC.md`) describes the *what*, this doc describes the *how it gets there* and the *what to do when it's stale*.

## TL;DR

```xml
<Observation id="Observation_03" location="src/example/foo.py:42:118">
  Exports class Foo; entrypoint used by the runner.
  <Edge type="depends_on" target="example.bar"/>
  <Edge type="depends_on" target="pathlib"/>
</Observation>
```

The `location` attribute and the `<Edge>` sub-elements are **AST-derived ground truth**, not model inference. A deterministic AST walk produces them; the Gemma4 rewriter is instructed to copy them verbatim, never invent them.

## Location attribute

### Format

```
location="<repo-relative-path>:<start-line>:<end-line>"
```

* `<repo-relative-path>` — slash-separated, no leading `./`. Absolute paths are rejected by the validator.
* `<start-line>` — 1-indexed line number where the symbol's `def`/`class` statement appears.
* `<end-line>` — 1-indexed inclusive line number of the last line of the symbol's body.
* Both line numbers are positive integers; `:0:` is rejected.

The validator rule is `RULE_LOCATION_EDGE_SHAPE` in `src/scholialang/validator.py`; the regex helper is `is_valid_location` in `src/scholialang/atoms.py`.

### What carries a location?

Only `<Observation>` carries a `location` today. The atom describes an exported symbol; the location pins the symbol's definition span. Multi-symbol files emit multiple Observations, one per exported symbol.

### What does NOT carry a location?

* `<Finding>`, `<Goal>`, `<Step>` — these are reasoning containers, not symbol records. v0.5 may extend.
* Observations describing whole-file invariants (no single span). Absence of `location` is valid v0.3 shape and is preserved.
* Re-exports without a fresh definition (the importer should reference the canonical location via `<Edge>` instead).

### Staleness behavior

Line numbers are point-in-time facts about the source file the atlas was generated against. When the source moves but the atlas hasn't been re-swept, the location is *wrong*. Consumers should:

1. Read `artifact.metadata["source_hash"]` (or equivalent) to detect drift.
2. Fall back to symbol-name lookup if the line span doesn't point at a `def`/`class` keyword.
3. Never persist location values back into the source file — they are atlas-only.

The atlas sweep regenerates locations on every full sweep; the incremental sweep regenerates them for every changed file. There is no separate refresh pass.

## Edge sub-element

### Format

```xml
<Edge type="depends_on" target="example.foo"/>
<Edge type="referenced_by" target="src/bar.py"/>
```

Attribute order is tolerant — both `type=...,target=...` and `target=...,type=...` validate. Self-closing form is required (no body).

### Closed set of edge types

```python
V04B_EDGE_TYPES = frozenset({
    "depends_on",      # this file imports / uses the target
    "referenced_by",   # the target imports / uses this file
    "imports",         # reserved — alias for depends_on in v0.5
    "references",      # reserved — non-import textual reference
})
```

The validator rejects any other `type` value (e.g. `"calls"`, `"includes"`). When v0.5 introduces new edge types they will be added to this set.

### Target semantics

* **Module-shaped target** (`example.foo`, `pathlib`): looked up via the reverse-index module resolver. Unresolvable module names are kept on the source artifact but produce no reverse edge.
* **Path-shaped target** (`src/foo.py`): used verbatim. The reverse-index pass matches the path directly against the artifact source paths.
* **Empty / whitespace-only target**: rejected by the validator.

### Edge directionality

* `depends_on` edges are emitted *on the importer*. Example: `src/a.py` imports `example.b` ⇒ `src/a.py`'s artifact gets `<Edge type="depends_on" target="example.b"/>`.
* `referenced_by` edges are emitted *on the target*, via the reverse-index pass. They live in `artifact.metadata["referenced_by"]`, NOT in the Scholia codeblock — see the next section.

## Reverse-index pass

### Why metadata, not in-Scholia

Inverting edges into Scholia would require re-running Gemma4 (expensive) or splicing into the already-validated codeblock (risky). The reverse-index pass takes a third path:

1. Read every artifact's Scholia codeblock (regex-extract `depends_on` edges).
2. Invert to `{target_path: [importer_paths]}`.
3. Write the inverted entries into `artifact.metadata["referenced_by"]`.

Downstream tools that want "which files import me?" read `artifact.metadata["referenced_by"]` — a sorted list of repo-relative source paths.

### Pass orchestration

Defined in `src/example/atlas/code_graph/reverse_index.py`:

* `extract_depends_on(scholia_codeblock)` — regex scan, returns the list of `target` values.
* `build_module_resolver(artifacts, repo_root)` — `{module_name: source_path}` lookup.
* `compute_reverse_index(artifacts, module_resolver)` — inverts to `{target: sorted([importers])}`.
* `apply_referenced_by(artifacts_by_source, reverse_index)` — mutates `artifact.metadata` in place.
* `run_reverse_index_pass(artifacts, repo_root)` — orchestration entry point.

The orchestrator (`src/example/atlas/orchestrator.py`) calls the pass once, immediately after Scholia enrichment, then writes each updated artifact back to disk via `write_atlas`.

### Performance

O(n) in artifact count. Single regex scan per artifact + single hash-map insert per edge. For the a host application tree (~700 artifacts) total cost is ~50ms; no quadratic walks.

### Cycles

`A depends on B` and `B depends on A` both produce a `referenced_by` entry on the other. The inversion is symmetric — no cycle elimination. Self-imports (`A depends on A`) are silently dropped to avoid noisy edges.

## AST-walk semantics

### Python (shipped)

`src/example/atlas/code_graph/python_ast.py` walks the file via `ast.parse` and emits:

* **Top-level `def` / `async def` / `class`** — one symbol per definition.
* **Nested methods** (one level inside `class`) — emitted as `Class.method`. Deeper nesting is summarized to the enclosing class.
* **Imports** — `from x import y, z` → one edge per `(module, name)` pair; `import x` → one edge per dotted name. Relative imports preserve their leading dots in the `module` field.
* **Best-effort call graph** — `_call_target_name` extracts the called callable's name for downstream consumption. Not validator-enforced.

Parse failures (syntax errors, encoding issues) populate `SymbolMap.parse_error` and the atlas falls back to prose-only — no atoms get a location.

### TypeScript, TSX (stub)

`src/example/atlas/code_graph/typescript.py` emits a no-op `SymbolMap` and logs a warning at sweep time. Locations and edges are absent until a real walker lands in a follow-up PRD.

### Lean (stub)

`src/example/atlas/code_graph/lean.py` — same as TypeScript. Warning-only.

### Language coverage matrix

| Language | Adapter | Location | Edges | Notes |
|----------|---------|----------|-------|-------|
| Python (`.py`) | `python_ast.py` | ✅ | ✅ | AST-based, deterministic |
| TypeScript (`.ts`, `.tsx`) | `typescript.py` | ❌ | ❌ | Stub — warns at sweep time |
| Lean (`.lean`) | `lean.py` | ❌ | ❌ | Stub — warns at sweep time |
| Other | (none) | ❌ | ❌ | Atom emission proceeds without code-graph metadata |

## Failure modes

| Symptom | Cause | Recovery |
|---------|-------|----------|
| Location regex rejected at validate time | Gemma4 invented a line range or path | Validation fails → fallback to prose-only. Re-sweep with current source. |
| Edge type rejected at validate time | Gemma4 invented an edge type outside the closed set | Same — validation fails, prose-only fallback. |
| `referenced_by` empty for a file you know is imported | Importer's `depends_on` target is a name the resolver can't reach (third-party, dynamic import) | Expected. Reverse-index only tracks edges between artifacts in the sweep. |
| Location line numbers point at the wrong code | Source moved since the last sweep | Re-run the host application's atlas sweep (full) or incremental sweep for the changed files. |

## See also

* `SCHOLIA_v0.4_SPEC.md` — full v0.4 spec covering all eight enhancements.
* `src/example/atlas/code_graph/` — adapter implementations.
* `src/scholialang/atoms.py` — `Edge` atom + `V04B_EDGE_TYPES` + helpers.
* `src/scholialang/validator.py` — `check_location_edge_shape` rule.
* `tests/unit/atlas/test_python_ast_walker.py` — V04B-00 coverage.
* `tests/unit/atlas/test_reverse_index.py` — V04B-03 coverage.
* `tests/unit/scholia/test_validator_v04B.py` — V04B-02 coverage.
