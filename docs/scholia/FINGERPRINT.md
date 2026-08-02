# Scholia `fingerprint=` — additive attribute for re-verifiable code claims

**Status:** PROPOSED — awaiting operator contract approval. NOT part of
the canonical v0.6 spec until this PR is approved and merged. At most a
**0.6.x** point revision (additive; see §7).
**Date:** 2026-08-02.
**Scope:** one optional attribute (`fingerprint=`) on location-bearing
atoms, its well-formedness rule, its ignore-if-absent semantics, and a
shared positive/negative fixture corpus.
**Depends on:** the upstream Atlas *fingerprint-grounding* definition
(52X-B2, tracked as issue #524). That work owns the **single** definition
of how a fingerprint is computed from a source span. This document does
**not** redefine it — it defines only the notation surface that carries
it and the semantics of its presence/absence in a trace.

---

## §1 Motivation

A Scholia trace can already pin a claim to code via
`<Observation location="file:start:end">` (see
[`CODE_GRAPH_METADATA.md`](CODE_GRAPH_METADATA.md)). But line spans are
*point-in-time* facts: the moment the source moves, the span is wrong,
and a reader cannot tell whether the trace's claim about that code still
holds. `location` says *where the symbol was*; it cannot say *whether it
is still the same symbol*.

A **fingerprint** is a content hash of the source span the atom refers
to. Carrying it alongside `location` lets a later consumer *mechanically
re-verify* the claim:

- **Symbol unchanged, span moved** → the line numbers are stale but the
  fingerprint still matches the symbol at its new span, so the consumer
  **rebinds** `location` and the claim survives the edit.
- **Symbol changed** → the fingerprint no longer matches, so the
  consumer knows the claim is **stale** and must not be trusted verbatim.

This turns "the trace said X about `foo.py:42:55`" from an unverifiable
assertion into a checkable one.

## §2 The attribute

```xml
<Observation id="Obs_03"
             location="src/example/foo.py:42:55"
             fingerprint="sha256:8f4a9d2c1b3e">
  Exports function foo; validated entrypoint.
</Observation>
```

- **Name:** `fingerprint`.
- **Value form:** `"<algo>:<hex>"`, matching the `canonical_id`
  precedent (`sha256:<hex>`). `algo` is a lowercase algorithm label
  (`sha256` for this revision); `hex` is lowercase hexadecimal. The
  concrete digest input — *which bytes of the span are hashed, and how* —
  is **defined once by 52X-B2** and is not restated here.
- **Optional.** Absence is valid and carries no claim (§4).
- **Where it may appear:** location-bearing atoms only. Today that is
  `<Observation>` (the only atom carrying `location`). If a future
  revision extends `location` to other kinds, `fingerprint` follows the
  same set. An atom **without** `location` **must not** carry
  `fingerprint` — a fingerprint with no span to bind to is meaningless
  and is rejected by the well-formedness rule (§3).

`fingerprint` is a companion to `location`, not a replacement:
`location` gives a human/tool a place to look; `fingerprint` lets the
tool confirm the place still holds the fingerprinted content.

## §3 Well-formedness rule (the only new validator behavior)

A single additive validator rule, mirroring `canonical_id_well_formed`:

**`fingerprint_well_formed`** *(hard-fail; vacuous when absent)* —

1. When an atom carries no `fingerprint`, the rule is **vacuous** (this
   is the ignore-if-absent guarantee — §4).
2. When present, the value must match `^[a-z0-9]+:[0-9a-f]+$` (an
   algorithm label, a colon, then lowercase hex). A value that is not
   well-formed (`sha256:NOTHEX`, a bare hash with no `algo:` prefix, an
   empty value) is a hard-fail.
3. When present, the atom **must** also carry a `location` (a fingerprint
   binds a span; with no span it is a hard-fail).

The rule is **purely structural**. It does **not** recompute the hash
against source — a notation validator has no access to the referenced
repository. **Re-verification** (does the fingerprint still match the
code?) is a **consumer-side** operation (§5), exactly as `location`
staleness is a consumer concern in `CODE_GRAPH_METADATA.md`, not a
validator rule.

> **Why not recompute in the validator?** The same reason `location`
> line numbers are not re-derived at validate time: the validator
> operates on the trace alone. Binding a trace to a working tree is the
> consumer's job (an atlas sweep, an audit tool). The notation layer
> guarantees the *shape*; the consumer guarantees the *match*.

## §4 Ignore-if-absent semantics

`fingerprint` is **strictly additive**:

- An atom **without** `fingerprint` is exactly as valid as it is today.
  `fingerprint_well_formed` is vacuous on it. No existing trace changes
  meaning or validity.
- Absence means **"no re-verification claim"**, not "verification
  failed". A consumer treats an un-fingerprinted `location` exactly as it
  does today (trust the span as a point-in-time hint).
- This is the **same additive posture** the v0.6 substrate used for
  `canonical_id`: a universal optional attribute whose validator rule is
  vacuous when the attribute is `None` (see
  [`SCHOLIA_v0.6_SPEC.md`](SCHOLIA_v0.6_SPEC.md) §4.3 / §10.1). The
  `canonical_id` precedent is the model this proposal follows
  deliberately.

### §4.1 Older-validator tolerance — an honest boundary

The word "additive" has two readings, and they differ under the
**published** reference parser. This proposal is explicit about which
guarantee it makes, because the published parser is **strict-closed-set**:
it enumerates the allowed wire attributes per atom kind and **rejects an
unknown attribute** rather than ignoring it.

| Reading | Holds? | Why |
|---|---|---|
| A fingerprint-aware validator accepts traces **with or without** `fingerprint`. | **Yes** — the strong guarantee. | The rule is vacuous when absent; well-formed when present. |
| A trace with `fingerprint` **stripped** validates clean under a pre-revision (fingerprint-unaware) validator. | **Yes** — `fingerprint` is non-load-bearing: it carries no reference that any other atom depends on, so removing it is lossless. | Demonstrated by the `ignore_if_absent` fixture (strip → validate). |
| A pre-revision **strict-closed-set** parser silently ignores an in-place `fingerprint` attribute. | **No.** | The published parser raises on unknown attributes. A strict validator must be *taught* the attribute (§7). This is precisely the situation `canonical_id` faced against a v0.5 strict parser — it too had to be added to the allowed set. |
| A **lenient / regex** consumer (e.g. a reverse-index pass that regex-scans for known attributes) ignores `fingerprint`. | **Yes.** | Such consumers read the attributes they know and drop the rest; an unknown attribute is invisible to them. |

**The honest summary for the operator gate:** "ignore-if-absent" is a
guarantee about *absence* (a trace without the attribute is untouched)
and about *load-bearing-ness* (the attribute can be stripped without
invalidating the trace). It is **not** a claim that today's strict
parser will accept the attribute in place — adopting the attribute is a
real, if minimal, **additive spec revision** (§7), just as `canonical_id`
was.

## §5 Consumer re-verification semantics (informative)

A consumer that *does* have the source tree can execute the
fingerprint. The three outcomes, and the fixtures that encode each:

| Outcome | Meaning | Fixture |
|---|---|---|
| **verifies** | Recomputing the fingerprint over the span at `location` matches the declared value. The claim holds as-is. | `positive/valid_fingerprint.xml` |
| **rebinds** | The span at `location` no longer matches, but the fingerprinted symbol is found elsewhere in the file (moved). The consumer updates `location` and the claim survives. | `positive/moved_symbol_rebind.xml` |
| **span_mismatch** | `location` points at lines that do not hold the fingerprinted symbol at all (the span and the fingerprint disagree at authoring time). | `negative/span_mismatch.xml` |
| **stale** | The fingerprinted content is gone from the file (the symbol was edited/deleted). The claim no longer re-verifies. | `negative/stale_fingerprint.xml` |

The **verifies / rebinds / span_mismatch / stale** verdicts are executed
by a consumer wired to 52X-B2's digest definition; they are **not**
computed by the notation validator (§3). The fixtures declare the
intended verdict and pair each trace with a source snippet so an
implementation can execute them end-to-end — see the fixture
`manifest.yaml`.

## §6 Fixtures

Shared, single-copy fixtures live at
[`../../tests/fixtures/fingerprint/`](../../tests/fixtures/fingerprint/):

- `positive/` — traces the proposed rule accepts (`valid_fingerprint`,
  `moved_symbol_rebind`, `ignore_if_absent`).
- `negative/` — traces or claims that fail (`malformed_hash` fails
  `fingerprint_well_formed`; `span_mismatch` and `stale_fingerprint`
  fail consumer re-verification).
- `manifest.yaml` — machine-readable index: per fixture, the trace file,
  the paired source snippet (where applicable), the expected verdict, and
  the reason.

They are placed **once, here**, for consumption by the `scholialang`
reference suite and any downstream implementation suite — no forks.

## §7 Adoption path (additive, ≤ 0.6.x)

To land this as a strict-closed-set-clean revision, an implementation
adds `fingerprint` to the allowed wire-attribute set for location-bearing
atoms — the same one-line widening that admitted `canonical_id`:

1. Add `fingerprint` to the location-bearing atom's field set (or to the
   parser's per-kind extra-wire-attrs), so the strict parser stops
   rejecting it.
2. Add the `fingerprint_well_formed` rule (§3) to the validator's rule
   set (hard-fail; vacuous when absent).
3. Leave every existing trace, rule, and the 32-atom closed set
   **unchanged**. No atom kind is added; no operator is added; no
   existing attribute changes meaning.

This is a substrate-attribute revision on the model of v0.6's
`canonical_id`, not a catalog change — hence "at most a 0.6.x point
revision".

## §8 Non-goals

- **Not** redefining the fingerprint digest — 52X-B2 owns the single
  definition.
- **Not** making the validator recompute hashes against source (§3).
- **Not** adding a new atom kind or operator.
- **Not** folding fingerprints into `canonical_id` — they answer
  different questions (`canonical_id` = identity of the *atom*;
  `fingerprint` = identity of the *code the atom points at*).
- **Not** extending `location` to new atom kinds (that is a separate
  proposal); `fingerprint` simply tracks wherever `location` is legal.

## §9 Operator contract-approval gate

This document is a **proposal**. Merging it — and any downstream
implementation of `fingerprint_well_formed` — is gated on explicit
operator contract approval (see the PR body checklist). Until then the
canonical v0.6 spec is unchanged and no validator ships the new rule.
