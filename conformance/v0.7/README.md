# Scholia v0.7 proposed semantic conformance fixtures

**Status: proposed candidate.** This directory carries the shared
cross-implementation fixture matrix for the PROPOSED additive
Map/Event/Task contract (`docs/scholia/SCHOLIA_v0.7_SPEC.md`, grammar
0.7.0 / package 0.7.3). Nothing here is ratified or released; the
v0.6.2 suites in `conformance/v0.6.2/` remain the shipped contract and
are unchanged.

## `semantic_atoms.json`

A self-describing suite (`suite_schema: semantic-atoms.v1`). Each case
declares:

- an exact stable `id` and its coverage `family`;
- the `format` of its payload — `xml` / `json` / `yaml` payloads are
  document *text*; `dict` payloads are the in-memory mapping input;
- for **negative** cases, the expected failure `phase` — `parse` (the
  input never becomes an atom: unknown kind/field, nonempty children,
  malformed or duplicate-key `entries`, non-string-list `operators`)
  versus `validate` (a constructed atom or trace is rejected: missing
  required fields, enum violations, typed-entry violations, ID shape
  and uniqueness, reference legality, occurrence uniqueness, canonical
  ID claims, grammar-profile rejection) — plus the `rule` code (see
  `rule_codes` in the suite metadata) and a `diagnostic_must_mention`
  subset the implementation's message must contain;
- for **positive** cases, round-trip expectations (XML→JSON→YAML→XML
  semantic equality with IDs, canonical IDs, typed values, operators,
  and empty children retained; repeated canonical JSON stable) and,
  where relevant, a canonical-`identity` relation (`equal` /
  `distinct`) between named atoms — within one payload or across
  `payload` / `payload_b`.

Consumers run **every** case with zero skips; the pinned counts in
`coverage` may not shrink silently. A negative parse case must fail in
the parse phase — translating parse failures into generic successful
negative outcomes is nonconforming.

The corrected inventory contains **204 cases: 36 positive, 168 negative**.
All original 106 IDs are retained in order; only two original positive
payloads were corrected to declare their referenced evidence. The
additional 98 cases strengthen numeric/duplicate-key decoder boundaries,
kind-by-format strictness, claimed-ID retention, local IDs, required
strings and semantic Task non-closure/non-result behavior.

`coverage-inventory.json` pins the complete ordered ID set, family and
format counts, and an exact mapping of 38 adversarial families to static
case IDs and runtime obligation IDs. Producer tests check fixture shape,
lexical reference declarations and coverage metadata; they do not run
an invented semantic validator.

Behaviors that cannot be represented safely in static fixtures are
declared in `runtime_obligations` (forced truncated-hash collisions,
no-side-effect probes under I/O denial, canonical-ID reference
resolution, the installed legacy-artifact probe, and packaging
parity); implementations claiming the proposed contract cover those in
their own suites.

Each of the 11 runtime obligations is a structured pending record with
`id`, `owner_gate`, `status`, `required_assertions`, `required_case_ids`,
and `receipt_fields`. The public owner is the reference implementation's
consumer gate. There is no runtime pass or placeholder successful
execution in a producer receipt. Consumers bind every required case to
actual executable node IDs and exact revision/artifact/import-origin
evidence. No-caller-mutation, identical-payload registry idempotence and
timestamp-provenance controls are distinct from forced collision tests.
Canonical references enumerate 96 concrete cases: all 35 permitted Map
target kinds and 13 typed Event/Task pairs, each in prior/forward order.

Raw JSON nonfinite tokens fail parse/`map_entries_shape`; nonfinite values
already decoded from legal YAML or true dictionary inputs fail
validate/`map_entries_typed`. Preserve raw duplicate-key strings rather
than normalizing them before a consumer tests decoder rejection.

Nothing in this suite executes work: parsing or validating a `<Task>`
never starts one; `runtime_ref` / `external_ref` are opaque
correlators, never dereferenced and never authority.
