# Scholia v0.6 examples

A small corpus exercising the v0.6 content-addressable substrate. Every
`.xml` trace **validates clean** (no errors, no warnings) under the
published `scholialang` v0.6 validator. Reusable by the website gallery
(PRD-06).

Spec: [`../../docs/scholia/SCHOLIA_v0.6_SPEC.md`](../../docs/scholia/SCHOLIA_v0.6_SPEC.md).

## Traces

| File | Demonstrates |
|---|---|
| `canonical_id_basic.xml` | Every atom carries its `canonical_id` (`sha256:<12 hex>`), round-tripped through `compute_canonical_id`; `canonical_id_well_formed` passes. |
| `refer_sha256_reference.xml` | Reuse of a prior `<Finding>` by content address via `<Reference to="sha256:<cid>">` (the attribute form that resolves against the in-trace canonical_id index — see spec §3.4). |
| `registry_dag_chain.xml` | A `<Deciding>` + `<Concluding>` chain; the parser stamps canonical_ids, and the atoms feed the DAG registry and the lazy prelude. |

## Prelude samples (the 3 CORE modes)

Rendered by `validate_examples.py` over `registry_dag_chain.xml`:

| File | Mode | Cost |
|---|---|---|
| `prelude_hash_only.txt` | `hash_only` | maximally compact (~30 c/atom) |
| `prelude_hash_list.txt` | `hash_list` (**default**) | compact + truncated preview (~70–100 c/atom) |
| `prelude_inline.txt` | `inline` | v0.5 baseline, full XML |

The two experimental quality-recovery arms are **NOT** v0.6 core (spec
§14). A clearly-labeled sample of one of them is provided at
`prelude_EXPERIMENTAL_hash_semantic_preview.txt` for reference only.

## Validate / regenerate

With the published `scholialang` v0.6 importable
(`pip install -e <scholialang>`):

```
python examples/v06/validate_examples.py
```

This validates every trace, demonstrates the genuine cross-session
`REFER:sha256` resolution via the DAG registry (`resolve_refer` registry
path + `ancestors` / `walk_chain`), and regenerates the `prelude_*.txt`
samples. Exit code 0 iff everything passes. Deterministic; no LLM calls.

## A note on cross-session reuse vs. `validate()`

The published `validate(trace)` resolves references only against in-trace
indices (it does not take a registry). So a *bare inline*
`REFER:sha256:<cid>` to a cid that is not in the current trace is
resolved by the **registry** at runtime (via `resolve_refer`), not by
`validate()`. These example traces therefore keep referenced atoms
in-trace (or use the `to="sha256:<cid>"` attribute form) so they validate
clean standalone; `validate_examples.py` shows the registry-backed
cross-session path separately. See spec §3.4 and §13.3.
