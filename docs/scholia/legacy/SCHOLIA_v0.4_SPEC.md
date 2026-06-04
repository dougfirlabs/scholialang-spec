# Scholia v0.4 — Specification (LEGACY)

> **⚠️ SUPERSEDED — see [`SCHOLIA_v0.5_SPEC.md`](../SCHOLIA_v0.5_SPEC.md) for current canonical.**
>
> This document is preserved unchanged below as a historical record.
> It was the v0.4 draft (cut 2026-05-22) before the v0.5 substrate
> rebuild reconciled the spec across the four Doug Fir Labs repos.
> Do **not** consult this doc for current Scholia atom kinds, operator
> set, or validator rules; the v0.5 spec doc is the source of truth.
>
> For migration from v0.4 trace shape to v0.5, see
> [`v04-to-v05-migration.md`](../v04-to-v05-migration.md).
>
> The v0.4 draft notably named a closed set of 6 atoms (Step, Goal,
> Observation, Hypothesis, Finding, Concluding) when the reference
> implementation in fact had 31 atoms. The 2026-06-04 drift audit
> exposed this gap; the v0.5 reconciliation closes it. Future readers
> tracing why something differs between this doc and current Scholia
> should consult the drift audit and the v0.5 spec.

---

# Scholia v0.4 — Specification

**Status:** DRAFT (no implementation work begins until this spec is approved)
**Date:** 2026-05-22
**Authors:** Claude Opus 4.7 (synthesizing Codex's enhancement list)
**Prerequisite:** Scholia v0.3.1 (minimal-but-extensible primitive hooks) must ship first. See `.ralph/rsi/rsi-scholia-v0.3.1-primitive-hooks.json`.

---

## Why v0.4 exists

Codex's read-only analysis of the t42 backend Atlas sweep (preserved at `docs/reports/2026-05-22-codex-atlas-token-analysis.md`) named eight enhancements that would graduate Scholia from "excellent for orientation and triage" to "operationally sufficient for precise refactors":

1. Stable atom IDs that survive regeneration
2. Exported symbols with line spans
3. Imported symbols / dependency edges
4. Side effects and mutation targets
5. Test ownership: which tests exercise this file
6. Risk flags: security, persistence, networking, subprocess, eval, filesystem writes
7. "Do not edit casually" markers for kernel, verifier, ledger, bridge files
8. Confidence or uncertainty per Observation

These collectively define Scholia v0.4. v0.3.x stays **intentionally minimal** — atoms are typed reasoning containers, not symbol tables. v0.4 expands the atomic carrier to include machine-precise metadata that downstream tooling can compute over.

## What stays the same as v0.3

- Closed-set operator vocabulary: `IMPLIES`, `REFER`, `NOT`, plus emergent `FLIP` / `SURFACE`
- Closed-set atom kinds: `Step`, `Goal`, `Observation`, `Hypothesis`, `Finding`, `Concluding`
- XML-shaped tags (per `project_scholia_convergence_anthropic` — Anthropic's HTML-memory research validated this from a different angle)
- Validator + Adjudicator architecture
- Fallback semantics (validation failure → prose-only with `scholia_fallback: true`)

## What v0.4 adds (BREAKING vs ADDITIVE classification)

| # | Enhancement | Type | Spec slot (v0.3.1) | Migration path |
|---|---|---|---|---|
| 1 | **Stable atom IDs** | **Breaking** | `id` attribute schema reserved in v0.3.1, value format changes in v0.4 | v0.3.1 readers accept both `Goal_01` and content-hash forms; v0.4 emits hash form. Validator allows either through v0.4; deprecates sequence form in v0.5. |
| 2 | **Exported symbols + line spans** | Additive | `<Observation location="file:start:end">` attribute | New attribute, optional. v0.3.x atoms have no `location`; v0.4 atoms may. Validator treats absence as "no location info available." |
| 3 | **Imported symbols / edges** | Additive | `<Edge type="..." target="..."/>` sub-element | New child element on Observations. v0.3.x atoms have no edges; v0.4 atoms may. |
| 4 | **Side effects** | Additive | `<Effect kind="..."/>` sub-element on Observations | New child element. Closed set of `kind` values: `io_write`, `network`, `subprocess`, `mutates_state`, `pure`. |
| 5 | **Test ownership** | Additive | `<Ref type="test_owner" target="path/to/test.py"/>` sub-element | Uses generic Ref sub-element introduced in v0.3.1. v0.4 populates with `type="test_owner"`. |
| 6 | **Risk flags** | Additive | `<Meta criticality="..."/>` sub-element on Step | Closed set of `criticality` values: `kernel`, `verifier`, `ledger`, `bridge`, `incidental`. Default `incidental` if absent. |
| 7 | **"Do not edit casually" markers** | Additive | Same as #6 — `criticality != "incidental"` IS the marker | No separate primitive; piggy-backs on #6. |
| 8 | **Confidence per Observation** | Additive | `<Observation confidence="0.85">` attribute | Float `0.0`-`1.0`. Validator accepts any float in range; rejects out-of-range. Default semantically equivalent to `1.0` (unstated = confident). |

**Headline:** 6 of the 8 enhancements are purely additive — existing v0.3 atoms remain valid v0.4 atoms. Only **stable atom IDs** require a migration semantic; the v0.3.1 schema reservation makes that migration non-breaking until v0.5.

## v0.3.1 → v0.4 release ordering

The order is **strictly enforced** because v0.4 atoms produced before v0.3.1 ships would be unreadable by current consumers.

```
Today: Scholia v0.3 (shipped — 1,529 atoms validated in t42 sweep)
   │
   ↓
v0.3.1: minimal-but-extensible primitive hooks
   │  - Validator accepts all v0.4 attributes/sub-elements as OPTIONAL
   │  - Schema documents the reserved field names
   │  - No tool POPULATES the new fields yet
   │  - Backwards-compatible with all v0.3 atoms
   │
   ↓
v0.4 (parallel-shippable enhancements):
   │  - v0.4-A: stable atom IDs (foundation; ship first)
   │  - v0.4-B: code-graph metadata (symbols + edges)
   │  - v0.4-C: file-level metadata (risk flags + test ownership + side effects)
   │  - v0.4-D: confidence scoring (uncertainty propagation)
   │
   └─→ v0.5 future: deprecate sequence-form atom IDs (post-v0.4 adoption)
```

## v0.4 MVP cut

**MUST ship together to call it v0.4:**
- Stable atom IDs (v0.4-A) — without these, downstream tooling can't diff atoms across regenerations
- v0.3.1 prerequisites (already gated)

**SHOULD ship in v0.4 sequence:**
- Code-graph metadata (v0.4-B) — symbol line spans + dependency edges. Highest operational value for runtime-atlas use case.

**MAY ship in v0.4 sequence or v0.4.x patches:**
- File-level metadata (v0.4-C) — risk flags, test ownership, side effects
- Confidence scoring (v0.4-D) — uncertainty propagation

## Non-goals for v0.4

- No new atom kinds (Step / Goal / Observation / Hypothesis / Finding / Concluding stay the closed set)
- No new operators beyond IMPLIES / REFER / NOT (plus emergent FLIP / SURFACE if those stabilize)
- No format change (XML-in-fenced-block stays; no JSON variant)
- No required population of new fields by the rewriter — emitters MAY populate, validators MUST accept absence
- No backwards-incompatible breakage of v0.3 atoms

## Open questions to resolve before any v0.4 implementation PRD lands

1. **Stable atom ID derivation function** — content-hash over what exactly? (Atom text? File-path-prefixed? Position-stable across edits?) Stable IDs that survive non-trivial source edits are non-trivial. May need to pick a "best-effort stable" semantic.
2. **Location accuracy** — line spans are computed at sweep time from source. Source then changes. Atoms become stale at the file-edit level. v0.4-B needs to clarify staleness semantics: "best at sweep time; may drift if source has changed since sweep."
3. **Confidence scoring source** — does the rewriter compute confidence from prompt-engineered self-assessment? From validator outcomes? From cross-validation across multiple sweeps? v0.4-D needs to pick.
4. **Risk-flag authority** — does the rewriter detect kernel/verifier/ledger files heuristically (e.g. by file path), or does the project supply an explicit registry? Probably the latter (manifest file under `.scholia/criticality.yaml`).
5. **Test ownership detection** — pyright/coverage integration vs structural heuristics (e.g., `tests/foo.py` tests `src/foo.py`)? Latter is cheap; former is accurate. May start cheap and refine.

These questions are the SPEC's job to lock down BEFORE v0.4 implementation PRDs land. If you're reading this and any of the above is unspecified, the spec is incomplete.

---

## Companion artifacts

- `docs/reports/2026-05-22-codex-atlas-token-analysis.md` — the analysis this spec answers
- `.ralph/rsi/rsi-scholia-v0.3.1-primitive-hooks.json` — the foundational PRD
- `.ralph/rsi/rsi-scholia-v0.4-stable-atom-ids.json` — v0.4-A
- `.ralph/rsi/rsi-scholia-v0.4-code-graph-metadata.json` — v0.4-B
- `.ralph/rsi/rsi-scholia-v0.4-file-metadata.json` — v0.4-C
- `.ralph/rsi/rsi-scholia-v0.4-confidence-scoring.json` — v0.4-D
- `docs/reports/2026-05-22-convergent-reading.md` — produced by the tri-source synthesis PRD
