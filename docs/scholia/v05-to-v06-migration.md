# Scholia v0.5 → v0.6 migration guide

**Audience:** consumers of pre-v0.6 traces (validators, dashboards,
enrichers), maintainers of emitters that produce Scholia atoms, authors
of runtime mirrors such as `scholialang-mcp`, and anyone wiring up
the v0.6 DAG registry or lazy canonical-prelude.

**Target reading time:** ~10 minutes.

**Source of truth:** [`SCHOLIA_v0.6_SPEC.md`](SCHOLIA_v0.6_SPEC.md),
authored to the 2026-06-06 golden-records compatibility manifest and the
published `scholialang` v0.6 implementation. This document supersedes the
v0.5 spec at [`SCHOLIA_v0.5_SPEC.md`](SCHOLIA_v0.5_SPEC.md) (preserved
with a banner).

---

## §0 TL;DR — the back-compat guarantee

**v0.6 is additive. Pre-v0.6 traces parse and validate cleanly under
v0.6 with zero changes.** The atom catalog is unchanged (32 kinds). The
new surfaces — `canonical_id`, `REFER:sha256`, the DAG registry, and the
3-mode lazy prelude — are **opt-in**. If your code only consumes v0.5
trace shapes, no migration is required; the only thing that changed for
you is that the validator now stamps `SCHOLIA_VALIDATOR_VERSION = 0.6.0`
and reports one additional (vacuous-on-absence) rule name.

The two experimental quality-recovery prelude arms are **not** v0.6 core
and are off by default (§5).

---

## §1 What changed (additive)

### §1.1 `canonical_id` — content-addressable identity

- **What:** every atom gains an optional `canonical_id` base attribute
  of the form `sha256:<12 hex>` — a SHA-256 over the atom's structural
  identity `{kind, content.strip(), attrs}` with provenance
  (`timestamp` / `wall_clock` / `run_id` / `sequence` / `instance`) and
  base bookkeeping (`id` / `children` / `operators`) excluded.
- **Why:** the same structural atom emitted from different
  sessions/hosts addresses to the same id, so a later session can reuse
  prior reasoning by hash instead of replaying it.
- **Who stamps it:** the parser, at parse time. Hand-built atoms get one
  via `compute_canonical_id(atom)`. A wire `canonical_id` that does not
  match the recompute is preserved verbatim so the validator can flag
  the tamper.
- **Back-compat:** a v0.5 atom that carries no `canonical_id` is
  unaffected — the `canonical_id_well_formed` rule is vacuous on
  absence.

### §1.2 `REFER:sha256` / `IMPLIES:sha256` operator forms

- **What:** `REFER` and `IMPLIES` gain a content-addressable target form
  (`REFER:sha256:<cid>`) alongside the v0.5 local-id form
  (`REFER:Finding_02`). No new operators.
- **Why:** a `REFER:sha256:<cid>` dereferences an atom that lives in the
  registry (a prior session), not necessarily in the current trace.
- **Resolution boundary:** the **structured attribute** form
  (`<Reference to="sha256:<cid>">`) resolves cleanly against the
  in-trace canonical_id index. A **bare inline** `REFER:sha256:<cid>`
  whose cid is not in the current trace is resolved by the **registry**
  (pass one to the validator) — a registry-less validator will flag it.
  See `SCHOLIA_v0.6_SPEC.md` §3.4. Emitters that want a cross-trace ref
  to validate clean without a registry should use the `to="sha256:<cid>"`
  attribute form or keep the referenced atom in-trace.

### §1.3 The DAG registry

- **What:** `scholialang.registry.Registry` — a `canonical_id`-keyed
  atom store with `REFER`/`IMPLIES`-derived `premise → conclusion` DAG
  edges. On-disk `{version, atoms, edges}` at
  `~/.scholia/registry.proofchain.json`.
- **Queries:** `ancestors`, `descendants`, `walk_chain` (proof chain),
  `to_proof_chain` (whole registry).
- **Back-compat:** a flat (no-`edges`) JSON file loads transparently as
  an empty-edge registry.

### §1.4 The lazy canonical-prelude — 3 core modes

- **What:** `build_canonical_prelude(prior_atoms, registry=None,
  mode="hash_list")` renders the prior-session atoms a later session
  sees. Core modes: `hash_only` (~30 c/atom), `hash_list` (default,
  ~70–100 c/atom, truncated preview), `inline` (full XML, the v0.5
  baseline).
- **Determinism (normative):** byte-identical input → byte-identical
  output; no LLM calls inside the renderer.

### §1.5 Validator additions

- **Added:** `canonical_id_well_formed` (hard-fail; vacuous on absence).
- **Modified:** `reference_complete` resolves `canonical_id`
  (`sha256:<hex>`) targets via the 4-path `resolve_refer` resolver
  (local id → in-trace canonical_id → registry → unresolved).
- **Version:** `SCHOLIA_VALIDATOR_VERSION` → `0.6.0`. Report shape
  unchanged (`{ok, errors, warnings, errors_by_rule, ...}`).

### §1.6 `Finding.for_goal` — disposition reconciled

The v0.5 docs said `for_goal` would be **removed in v0.6**. **It is
not.** The published v0.6 implementation keeps `Finding.for_goal`
**deprecated** (still read-accepted; still emits a `DeprecationWarning`
once per instance when set in Python). **Removal is deferred to v0.7.**
Migrate `Finding(for_goal=...)` → `Finding(for_hyp=...)` (or emit a
`<Concluding>` for a Goal-close) before v0.7. See
`SCHOLIA_v0.6_SPEC.md` §10.8 / §15.

---

## §2 What did NOT change

If your code only depends on the items here, no migration is required.

- The 32-atom closed set, names, categories (incl. the v0.5
  `<Concluding>` atom).
- XML-shaped tag syntax and the closed-set principle.
- The `<Step>` container shape.
- The 11 canonical + 2 emergent operators (v0.6 adds the `sha256:`
  *target form*, not new operators).
- Reference-resolution scope (intra-trace; cross-trace via registry).
- The validator report shape.
- The six v0.5 `<Concluding>`-scoped rules and the criticality ladder
  (`CRITICALITY_RANK`).
- Fallback semantics (`scholia_fallback: true`).
- The `<Meta:research-mode/>` pseudo-atom.
- The v0.3.1 schema-reserved primitive hooks.

---

## §3 Per-stakeholder recipes

### §3.1 Archival traces — **no action required**

Archival v0.5 (and v0.4) traces are read-only history; they remain valid
v0.6 traces. They carry no `canonical_id`, so `canonical_id_well_formed`
is vacuous on them. If you re-emit an archival trace (e.g. dashboard
replay), treat the re-emission as a fresh emit and apply the §3.2 emitter
recipe to the producer.

### §3.2 Emitters

Adopt the substrate incrementally; all of it is optional.

1. **Let the parser stamp `canonical_id`.** Parse through
   `scholialang.parser.parse` (or `parse_atom`) and the atom comes back
   with its `canonical_id` populated. For hand-built atoms, call
   `compute_canonical_id(atom)`. Do **not** invent your own hash — the
   contract is byte-for-byte cross-implementation (`SCHOLIA_v0.6_SPEC.md`
   §10.1).

   ```python
   from scholialang import parse, compute_canonical_id, Finding
   steps = parse(trace_xml)          # atoms come back with canonical_id stamped
   f = Finding(id="F_01", for_hyp="H_01", status="met", content="Met.")
   f.canonical_id = compute_canonical_id(f)   # hand-built path
   ```

2. **Reference prior reasoning by canonical_id.** To reuse a prior
   atom across sessions, emit a `REFER:sha256:<cid>` (registry-backed)
   or, for an in-trace/attribute reference that validates without a
   registry, a `<Reference to="sha256:<cid>">`.

   ```xml
   <!-- attribute form — resolves against the in-trace canonical_id index -->
   <Reference id="Ref_01" to="sha256:8f4a9d2c1b3e">Reuse the prior coverage finding.</Reference>
   ```

3. **Migrate `Finding(for_goal=...)` → `Finding(for_hyp=...)`** (or emit
   `<Concluding>` for a Goal-close). The `DeprecationWarning` surfaces
   the call sites. Removal is in v0.7, so this is not urgent — but do it.

4. **Choose a prelude mode** if you build cross-session preludes:
   `hash_list` (default) is the recommended balance; `hash_only` for
   maximum compaction; `inline` to reproduce the v0.5 transcript.

### §3.3 Validators

1. **Add `canonical_id_well_formed`.** Reference:
   `scholialang/src/scholialang/validator.py`,
   `check_canonical_id_well_formed`. Recompute `compute_canonical_id` and
   hard-fail on mismatch; **skip when `canonical_id is None`** (back-compat).
2. **Extend `reference_complete`** to resolve `canonical_id`
   (`sha256:<hex>`) targets via the in-trace canonical_id index, and via
   the registry when one is supplied (the 4-path `resolve_refer`).
3. **Keep rules 1–17 unchanged.** The v0.6 additions must not alter v0.5
   rule behavior. Add back-compat tests: every v0.5-shaped fixture must
   pass v0.6 validation with no new errors/warnings.
4. **Bump `SCHOLIA_VALIDATOR_VERSION` to `0.6.0`.** Vendored validators
   (`scholialang-mcp` and private product mirrors) need a coordinated port.

### §3.4 Consumers (dashboards, runners, registry/prelude users)

1. **Report shape is unchanged.** Existing consumers keep working. The
   new rule name `canonical_id_well_formed` appears in the breakdown;
   treat unknown rule names as pass-through (do not hard-code rule-name
   allowlists).
2. **The registry and prelude are opt-in.** A consumer that wants
   cross-session reuse instantiates a `Registry`, `put`s parsed atoms,
   and builds preludes with `build_canonical_prelude`. Nothing forces
   adoption.
3. **DAG walks fail-soft.** `ancestors` / `descendants` / `walk_chain`
   silently skip referenced-but-absent canonical_ids; `walk_chain`
   reports `is_complete=False` when a premise is missing.

---

## §4 Step-by-step migration

For a typical consumer with v0.5 emitters in production:

1. **Upgrade the parser / atoms package to v0.6.** v0.5 traces parse
   cleanly; no test should fail. If one does, file an issue against
   `scholialang` — the back-compat contract is violated.
2. **(Optional) Start persisting atoms to a `Registry`** if you want
   cross-session reuse. Parse → `registry.put(atom)`; canonical_ids and
   edges are derived for you.
3. **(Optional) Reference prior atoms by canonical_id** in fresh emits
   (§3.2). Prefer the attribute form for registry-less validation.
4. **Port the validator** wherever you vendor one (§3.3).
5. **Run your trace corpus.** Expected: zero new errors/warnings on
   v0.5-shaped fixtures; canonical-id rules fire only on fresh v0.6
   fixtures that carry a (deliberately mismatched) `canonical_id`.
6. **Watch logs for `DeprecationWarning: Finding.for_goal`** — migrate
   those call sites before v0.7.

---

## §5 Experimental recovery arms (opt-in, NOT v0.6 core)

Two additional prelude render modes — `hash_semantic_preview` and
`selective_inline_plus_hash_only` — were designed by the v0.6
quality-recovery work **after** the 2026-06-06 manifest was frozen. They
are **experimental**: excluded from `CORE_PRELUDE_MODES`, reachable only
via `build_canonical_prelude(..., allow_experimental=True)`, and may
change or be removed (or be promoted to core in a later point release).
They are deterministic (no in-harness LLM), like the core modes. **Do
not** treat them as finalized v0.6. Full contract:
`SCHOLIA_v0.6_SPEC.md` §14.

---

## §6 FAQ

**Q. Do my v0.5 dashboards break?**
A. No. The validator report shape is unchanged. Expand any hard-coded
rule-name allowlist to include `canonical_id_well_formed`.

**Q. Must I add `canonical_id` to my emitter?**
A. No. It is optional and the parser stamps it for you when you parse.
Cross-session reuse needs it; otherwise it is free to ignore.

**Q. My cross-trace `REFER:sha256:<cid>` fails reference_complete — why?**
A. A bare inline `REFER:sha256:<cid>` to a cid not in the current trace
is resolved by the **registry**; pass one to the validator. Without a
registry, use the structured `to="sha256:<cid>"` attribute form, or keep
the referenced atom in-trace. See `SCHOLIA_v0.6_SPEC.md` §3.4.

**Q. Is `Finding.for_goal` removed in v0.6?**
A. **No.** It stays deprecated; removal is **deferred to v0.7**. (The
v0.5 docs said v0.6 — that note is reconciled. See §1.6.)

**Q. Are the two recovery arms part of v0.6?**
A. No. They are experimental, opt-in, and post-date the manifest (§5).

**Q. Does `canonical_id` fold in child atoms?**
A. No. It hashes `{kind, content, attrs}` only; children are hashed
independently. A Merkle-DAG identity is a v0.7 non-goal.

---

## §7 References

- **Canonical spec:** [`SCHOLIA_v0.6_SPEC.md`](SCHOLIA_v0.6_SPEC.md).
- **Prior migration:** [`v04-to-v05-migration.md`](v04-to-v05-migration.md).
- **Golden-records manifest:** the 2026-06-06 v0.6 compatibility
  manifest (`spec_version "Scholia v0.6"`).
- **Reference impl:**
  `scholialang/src/scholialang/{atoms,parser,validator,registry,prelude}.py`.
