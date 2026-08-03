# `fingerprint=` shared fixtures

Positive and negative fixtures for the additive
`fingerprint=` attribute on location-bearing atoms. Contract:
[`../../../docs/scholia/FINGERPRINT.md`](../../../docs/scholia/FINGERPRINT.md).

These live **once, here**, for consumption by the `scholialang` reference
suite and any downstream implementation suite — no forks. The
machine-readable index is [`manifest.yaml`](manifest.yaml).

> **Status:** APPROVED and MERGED. The contract is part of the canonical
> spec as an additive substrate revision; the reference validator ships the
> `fingerprint_well_formed` rule as of `scholialang` 0.7.1.

## Layout

```
fingerprint/
  manifest.yaml            index: fixture → source, layer, expected verdict, reason
  positive/
    valid_fingerprint.xml    fingerprint matches source span         → verifies
    moved_symbol_rebind.xml  span stale, fingerprint matches (moved)  → rebinds
    ignore_if_absent.xml     mixed with/without; strips clean         → older-validator tolerance
  negative/
    malformed_hash.xml       value not <algo>:<hex>                   → malformed (notation)
    span_mismatch.xml        location span ≠ fingerprinted symbol     → span_mismatch (consumer)
    stale_fingerprint.xml    fingerprinted content gone from source   → stale (consumer)
  sources/
    foo_v1.py                snapshot the fingerprints were authored against
    foo_v2_moved.py          foo() moved (rebind case)
    foo_v3_edited.py         foo() edited (stale case)
```

## Two failure layers

The fixtures deliberately separate the two places a fingerprint claim can
fail (spec §3 vs §5):

- **notation** — decided by the `fingerprint_well_formed` rule on the
  trace alone, no source access. `malformed_hash` is the negative here.
  This layer is executable **today** with a regex (see `well_formed_regex`
  in the manifest).
- **consumer** — decided by recomputing the fingerprint over source using
  **52X-B2's single digest definition** (issue #524). `span_mismatch` and
  `stale_fingerprint` are the negatives; `valid_fingerprint` and
  `moved_symbol_rebind` are the positives. Each is paired with a `source:`
  snippet as the input.

## Honest scope note (no silent truncation)

The fingerprint hex values in the traces are **illustrative placeholders**.
The real digest is 52X-B2's to compute and is **not** reproduced here (hard
constraint: one definition, not redefined). So:

- The **notation** layer (well-formedness, ignore-if-absent, strips-clean)
  is fully executable in this repo and is exercised by
  `tests/test_fingerprint_fixtures.py`.
- The **consumer** verdicts (`verifies` / `rebinds` / `span_mismatch` /
  `stale`) are **declared intent** in the manifest, to be executed by an
  implementation wired to 52X-B2's definition. They are not recomputed by
  this repo's notation validator.

## Older-validator tolerance

`ignore_if_absent.xml` is the tolerance demonstrator. `fingerprint` is
**non-load-bearing**: no atom REFERs it, so stripping every `fingerprint`
attribute is lossless. The test strips them and asserts the result parses
and validates clean under the **published** `scholialang` v0.6 validator —
proving the attribute can be dropped by a pre-revision consumer without
invalidating the trace. Note the boundary (spec §4.1): a strict-closed-set
parser must be *taught* the attribute to accept it **in place**, exactly as
it had to be taught `canonical_id`.
