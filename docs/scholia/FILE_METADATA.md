# Scholia v0.4-C — file-level metadata

Three closely-related metadata categories that the Scholia rewriter
attaches to per-file atoms so downstream agents can route work
intelligently:

* **Risk flags** — `<Meta criticality="..."/>` on the Step.
* **Side effects** — `<Effect kind="..."/>` on Observations.
* **Test ownership** — `<Ref type="test_owner" target="..."/>` on
  Observations.

All three are optional. A v0.3 atom (no `<Meta>`, no `<Effect>`, no
`<Ref>`) remains a valid v0.4-C atom. The rewriter populates the
slots only when ground-truth sources resolve.

## Risk flags — `<Meta criticality="..."/>`

Operator-curated. The manifest at `.scholia/criticality.yaml` (repo
root) maps file globs to a criticality level from the closed set:

* `kernel` — the verifier, ledger, bridge, and core verifier-grade
  code. Casual edits regress the system; require review.
* `verifier` — code that proves correctness of other code (Scholia
  validator, adjudicator). Edits here change trust semantics.
* `ledger` — append-only persistence (KB store, Events stream). Edits
  affect the audit trail.
* `bridge` — code that crosses a trust boundary (auth gateway,
  external API adapter, external proof-graph conversion).
* `incidental` — everything else. The default — absence of `<Meta>`
  is semantically equivalent.

See [`CRITICALITY.md`](CRITICALITY.md) for the manifest authoring
guide.

The rewriter emits `<Meta criticality="..."/>` only when the manifest
classifies the file explicitly. A file outside the manifest's globs
gets no `<Meta>` element — the absence-means-incidental contract
keeps low-stakes files un-cluttered.

## Side effects — `<Effect kind="..."/>`

AST-detected. The rewriter calls `scholialang.effects.detect_effects`
on the file's Python source and threads the result into the prompt;
Gemma emits one `<Effect kind="..."/>` per detected kind from the
closed set:

* `io_write` — `open(..., 'w'/'a'/'x'/...)`, `Path.write_text`,
  `Path.write_bytes`.
* `network` — `requests.*`, `urllib.*`, `http.client.*`, `socket.*`,
  `aiohttp.*`, `httpx.*`.
* `subprocess` — `subprocess.run/Popen/call/...`, `os.system`,
  `os.popen`, `os.exec*`, `os.spawn*`.
* `mutates_state` — `global` statements OR module-level assignments
  after the first def/class boundary.
* `pure` — emitted exactly when none of the above is detected.

Detection is best-effort and static. Runtime indirection (`run =
getattr(os, 'system'); run(...)`) is intentionally missed — readable
rules beat exhaustive coverage. The rewriter prompt asks the model
to confirm or refine the detected list, so a false positive can be
overridden by reading the actual source.

Non-Python files don't get an `<Effect>` annotation under v0.4-C
(future PRDs may add language-specific detectors). The closed set
itself is language-agnostic; only the detector is language-specific.

## Test ownership — `<Ref type="test_owner" target="..."/>`

For a Python source file under the repo, three priority sources
resolve test ownership:

1. **`.scholia/test_ownership.yaml`** — operator override (YAML
   mapping of repo-relative source paths to lists of test paths).
   Highest priority.
2. **`.scholia/coverage_map.json`** — coverage-derived mapping
   (JSON object of source paths to lists of test paths). Used when
   the override is silent.
3. **Name-convention heuristic** — for `src/foo.py`, the rewriter
   globs `tests/**/test_foo.py` and `tests/**/foo_test.py`. Used
   when both override and coverage are silent.

A source with no override, no coverage, and no name-convention match
emits no `<Ref>` — absence is the v0.4-C contract for "we don't know
which tests own this file."

Sample override file:

```yaml
# .scholia/test_ownership.yaml
src/scholialang/validator.py:
  - tests/unit/scholia/test_validator.py
  - tests/unit/scholia/test_validator_v031.py
  - tests/unit/scholia/test_validator_v04C.py
src/example/atlas/scholia_rewriter.py:
  - tests/unit/atlas/test_scholia_rewriter.py
  - tests/integration/atlas/test_scholia_rewriter_v04C.py
```

## Worked example

For `src/scholialang/validator.py` with:

* `.scholia/criticality.yaml` listing it under `kernel`
* AST detection returning `["pure"]` (no I/O, no subprocess, no
  network, no module-state mutation)
* Override file naming `tests/unit/scholia/test_validator.py`

…the rewriter prompt receives a FILE METADATA block:

```text
CRITICALITY: kernel
EFFECTS: pure
TEST_OWNERSHIP: tests/unit/scholia/test_validator.py
```

…and the emitted atoms shape up to:

```scholia
<Step id="step_01">
  <Meta criticality="kernel"/>
  <Goal id="Goal_01" scope="trace" priority="required">Scholia validator entry point.</Goal>
  <Observation id="Observation_01">Exports validate(trace) running nine rules.<Effect kind="pure"/></Observation>
  <Observation id="Observation_02">Tested by tests/unit/scholia/test_validator.py.<Ref type="test_owner" target="tests/unit/scholia/test_validator.py"/></Observation>
  <Finding id="Finding_01" for_goal="Goal_01" status="met">A pure-function validator, IMPLIES:Observation_01.</Finding>
</Step>
```

## Validator enforcement

The validator's `RULE_V031_OPTIONAL_FIELDS` rule (added in v0.3.1)
enforces strict closed-set values:

* Unknown `<Meta criticality>` rejects.
* Unknown `<Effect kind>` rejects.
* Unknown `<Ref type>` rejects.

The parser mirrors the same rules on the wire-form input path.
Adding a new value to any closed set requires a Scholia spec version
bump (next would be v0.5).

## References

* [`SCHOLIA_v0.3.1_SPEC.md`](SCHOLIA_v0.3.1_SPEC.md) — primitive-hook
  schema reservations.
* [`SCHOLIA_v0.4_SPEC.md`](SCHOLIA_v0.4_SPEC.md) — full v0.4
  enhancement program.
* [`CRITICALITY.md`](CRITICALITY.md) — operator manifest authoring
  guide.
