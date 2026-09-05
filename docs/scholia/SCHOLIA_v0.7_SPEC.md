# Scholia v0.7 — Specification (PROPOSED)

**Status:** PROPOSED CANDIDATE — not ratified, not released. This
document records the exact additive Map/Event/Task contract offered for
review. Until it is accepted, `docs/scholia/SCHOLIA_v0.6_SPEC.md`
remains the canonical specification and the legacy projection
`reference/atoms_index.yaml` remains authoritative for the shipped
32-kind catalog.
**Date:** 2026-09-05.
**Grammar revision:** 0.7.0 (proposed) — the closed atom catalog grows
from 32 to 35 kinds; describing that as an unchanged 0.6.2 grammar
would be misleading, so the grammar axis bumps.
**Package revision:** 0.7.3 (proposed) — the reference-implementation
package/validator axis; distinct from the grammar axis and from any
separately pinned transport protocol version. No tag, upload, or
release accompanies this proposal.
**Authors:** Darren Brewster, Claude Opus 4.7.
**Project:** Doug Fir Labs (the `scholialang-spec` repository is the
canonical home).
**Source of truth once accepted:** this document, the current catalog
projection `reference/v0.7/atoms_index.yaml`, and the self-describing
semantic conformance suite `conformance/v0.7/semantic_atoms.json`.

> Nothing in this revision executes work or grants authority. Parsing
> or validating a `<Task>` never starts a task; recording an `<Event>`
> never delivers a notification; a `<Map>` never triggers evaluation,
> schema discovery, traversal, or network lookup.

---

## §1 Overview

Scholia v0.7 is an *additive semantic-vocabulary* proposal on top of
the v0.6.2 contract. Everything in v0.6.2 — the 32 legacy kinds, the
validator rules, canonical identity, the DAG registry, the lazy
prelude, and the `fingerprint=` revision — carries forward unchanged.
The proposal adds exactly three atom kinds:

1. **`<Map>`** — a named, homogeneous, finite typed mapping value
   (§4). Distinct from the inline `MAP` primitive, which is unchanged.
2. **`<Event>`** — a recorded occurrence (§5). Distinct from the
   existing `<EventRef>`, which remains the reference to an externally
   recorded event and is unchanged.
3. **`<Task>`** — a declarative work obligation with an
   author-asserted verdict (§6). Distinct from any runtime task handle.

Three identity boundaries are load-bearing throughout:

- **Semantic Task ≠ runtime task handle.** A `<Task>` records an
  obligation and a descriptive verdict. Runtime lifecycles (queued,
  working, input_required, cancelled, expired, paused) belong to the
  transport/runtime layer and are never inferred from, or collapsed
  into, the semantic status enum. Correlation is explicit and opaque
  (`runtime_ref`).
- **Semantic Event ≠ delivered notification.** An `<Event>` records
  that something occurred, keyed by `(source, occurrence_id)`. It is
  not a notification envelope and not the authoritative runtime event
  database. Correlation with external systems is explicit and opaque
  (`external_ref`).
- **Map ≠ arbitrary object bag.** A `<Map>` is a closed, homogeneous
  string-keyed mapping with a declared scalar/reference value type. It
  is not a topology, not a schema-discovery surface, and not a second
  free-form payload channel.

<!-- BEGIN_GENERATED:atoms_to_spec -->
## §2 Atom catalog

The PROPOSED Scholia v0.7 closed set is **35 atom kinds**, grouped into seven categories. Names are PascalCase. Adding an atom kind is a breaking change and requires a spec version bump — which is why this revision declares grammar 0.7.0 (distinct from package 0.7.3) rather than claiming the 0.6.2 grammar unchanged. The 32 legacy kinds keep their v0.6 semantics; the additions (`<Event>`, `<Map>`, `<Task>`) are proposed candidates until this specification is accepted.

### §2.1 Reasoning

- **`<Action>`** — external state change — must produce a Finding.
- **`<Observation>`** — external input — command output, file contents, query result.
- **`<Thinking>`** — internal deliberation — not observing, not acting.

### §2.2 Evidence

- **`<Concluding>`** — chain-level epistemic close — resolves a Goal via cited atoms.
- **`<Contradiction>`** — two claims that cannot both be true; forces a Deciding.
- **`<Evidence>`** — observation bearing on a Hypothesis (supports / refutes / neutral).
- **`<Finding>`** — conclusion drawn from evidence — evaluates a Hypothesis.
- **`<Hypothesis>`** — explicit conjecture the agent intends to test.
- **`<Retract>`** — revoke a prior Finding (or downgrade-bypass for criticality).
- **`<Uncertainty>`** — confidence below 1 attached to a Finding, Hypothesis, or Evidence.

### §2.3 Control

- **`<Alternative>`** — explicitly rejected option inside a Deciding.
- **`<Branch>`** — legal transition out of a Deciding.
- **`<Deciding>`** — action commitment branch point — chooses among alternatives.
- **`<Loop>`** — iteration over a collection — binds one per-iteration variable.
- **`<Parallel>`** — concurrent independent atoms with no specified ordering.

### §2.4 Reference

- **`<Implication>`** — long-form forward-link — equivalent to inline IMPLIES:id.
- **`<Map>`** — PROPOSED v0.7 — a named, homogeneous, finite typed mapping value; not a topology, not an arbitrary object bag, distinct from the inline MAP primitive.
- **`<Print>`** — one-line human-facing summary surfaced to the reader.
- **`<Reference>`** — long-form back-link — equivalent to inline REFER:id.
- **`<Storing>`** — persist a named value to trace-local memory for later REFER.

### §2.5 Social

- **`<Handoff>`** — pass work to another agent with a named package.
- **`<Question>`** — explicit request for external input.
- **`<Review>`** — audit another agent's atom and produce a Finding.

### §2.6 Meta

- **`<Budget>`** — declared spending envelope (tokens / actions / wall_clock_ms).
- **`<Confidence>`** — qualitative or numeric confidence attached to another atom.
- **`<Constraint>`** — hard rule in effect that subsequent decisions must respect.
- **`<Cost>`** — observed expenditure (tokens / dollars / wall_clock_ms).
- **`<Event>`** — PROPOSED v0.7 — a recorded occurrence in the trace; not a delivered notification, not a transport envelope, and not the authoritative runtime event database.
- **`<EventRef>`** — pointer to an externally recorded run event.
- **`<Goal>`** — target proposition the agent is pursuing — may declare criticality.
- **`<Task>`** — PROPOSED v0.7 — a declarative work obligation with an author-asserted verdict; not a runtime task handle, and never a grant of execution authority.

### §2.7 Primitives

- **`<Edge>`** — schema-reserved import / dependency edge on an Observation.
- **`<Effect>`** — schema-reserved side-effect kind (io_write / network / subprocess / mutates_state / pure).
- **`<Meta>`** — schema-reserved Step-level metadata (e.g. criticality).
- **`<Ref>`** — schema-reserved generic reference sub-element with type / target.
<!-- END_GENERATED:atoms_to_spec -->

*§2 above is generated: `python scripts/atoms_to_spec.py --index
reference/v0.7/atoms_index.yaml --check docs/scholia/SCHOLIA_v0.7_SPEC.md`
must pass. The index-driven generator never imports the
implementation, so this proposed catalog renders identically before
and after a conforming implementation exists.*

---

## §3 Common model and validation boundary for the new kinds

The new kinds follow the existing pure dataclass style: subclasses of
`Atom`, `kind: ClassVar[str]`, explicit fields, and **no I/O or
execution** in constructors, parsing, validation, hashing, or
serialization. Required semantic fields may default to `None` at the
Python construction boundary, as existing dataclasses do; validation
must reject incomplete instances. Parsers must reject malformed field
shapes rather than silently discard them.

The common wire attributes for new kinds are `id` and optional
`canonical_id`, plus the kind-specific fields in §4–§6. JSON/YAML
retain the existing `kind`, `content`, `operators`, and `children`
structural keys. `operators` must be a list of strings; no coercion
from arbitrary objects.

**No nested children.** New kinds have no nested child atoms in this
revision: nonempty `children` is rejected at parse time. This avoids
claiming that child structure is covered by a canonical hash which
historically excludes children. Relationships use explicit reference
fields instead.

**Required trace-local IDs.** Each new-kind atom requires an `id`
whose prefix matches its kind — `Map_`, `Event_`, or `Task_` —
followed by one or more ASCII letters, digits, or underscores.
Existing IDs such as `Goal_01` retain their existing acceptance rules.
An ID collision involving at least one new atom is an error anywhere
in the trace, including against a Step or legacy atom ID. Legacy-only
duplicate handling is not retroactively changed by this revision.

**Optional strings.** Every named optional string field, when present,
must be nonempty after checking whitespace; its original bytes and
case are preserved rather than silently normalized. Omitted and null
optional fields are equivalent.

**Closed field sets.** Unknown fields on each new kind are rejected
across XML, JSON, YAML, and dictionary input. Malformed
Python-constructed new atoms are rejected in `validate()` using the
same structural rules. Old parsing/serialization behavior is not
globally tightened without an explicit regression justification.

**References.** Local reference fields contain an exact declared atom
ID or canonical ID. They resolve against the complete trace (forward
references allowed) and must land on the target kinds declared in
§4–§6. Opaque external references (`external_ref`, `runtime_ref`) are
nonempty strings and are **never** interpreted as a local ID,
dereferenced, used for execution, or treated as proof of identity or
authority. No new generic Edge enum values or legacy reference
semantics are introduced.

## §4 `<Map>` — a typed mapping value

A Map is a named-in-the-trace, homogeneous, finite mapping from
nonempty string keys to one declared scalar/reference type. It is
distinct from the existing inline `MAP` primitive and does not change
primitive parsing.

| Field | Requirement | Contract |
| --- | --- | --- |
| `id` | Required | `Map_` + `[A-Za-z0-9_]+` |
| `value_type` | Required | Exactly `string`, `integer`, `boolean`, or `atom_ref` |
| `entries` | Required | Object/mapping, possibly empty; unique, nonempty string keys |
| `content` | Optional body | Human explanation, not a second data payload |

Values must all match `value_type`. `string` permits strings including
empty strings. `integer` requires a true integer (not bool), in the
interoperable JSON exact-integer range `-(2^53-1)` through `2^53-1`.
`boolean` requires bool exactly. `atom_ref` requires nonempty string
references resolving to a declared atom of any kind other than Step; a
Map must not refer to itself. Nested objects, arrays, nulls, floats,
NaN, infinities, nonstring keys, and mixed types are rejected. Map
does not imply evaluation, schema discovery, traversal, or network
lookup.

**Wire encodings.** XML represents entries as a JSON object in the
escaped `entries` attribute. JSON/YAML represent entries as an actual
mapping, never a Python repr or a JSON-encoded string. XML output uses
canonical JSON for this attribute: sorted string keys, compact
separators, Unicode preserved before XML escaping. Duplicate keys are
rejected when decoding the embedded JSON. JSON/YAML full-trace loaders
must also detect duplicate mapping keys before they are silently
overwritten; if a loader must reject duplicate keys for legacy
documents too (because duplicates have already destroyed information),
that is documented narrowly as malformed-input rejection and proven
against valid-legacy-corpus parity.

```xml
<Map id="Map_inputs" value_type="string" entries="{&quot;format&quot;:&quot;xml&quot;,&quot;target&quot;:&quot;fixture&quot;}">Inputs to the declared task.</Map>
```

**Identity.** Map canonical identity includes `value_type`, `entries`,
and `content` under the unchanged existing hash algorithm. Entry
insertion order is not identity; key/value changes are. The four value
types deliberately avoid speculative heterogeneous or recursively
typed syntax; a later schema revision can extend the closed set
explicitly.

## §5 `<Event>` — a recorded occurrence

| Field | Requirement | Contract |
| --- | --- | --- |
| `id` | Required | `Event_` + `[A-Za-z0-9_]+` |
| `source` | Required | Opaque producer namespace; not authentication evidence |
| `occurrence_id` | Required | Opaque ID unique within source for this occurrence |
| `event_type` | Required | Nonempty classification token matching `[A-Za-z][A-Za-z0-9_.-]*`; producer-defined vocabulary, not a new atom kind |
| `timestamp` | Optional | RFC3339-shaped timestamp with explicit timezone; naive or impossible date/time values rejected; excluded from canonical identity as existing timestamp provenance is excluded |
| `for_task` | Optional local ref | Task only |
| `for_action` | Optional local ref | Action only |
| `for_goal` | Optional local ref | Goal only |
| `effect_ref` | Optional local ref | Effect only; does not execute the effect |
| `map_ref` | Optional local ref | Map only |
| `external_ref` | Optional opaque string | External event/resource correlation, no dereference |
| `content` | Required body | Nonempty description of what was recorded |

**Occurrence identity.** The pair `(source, occurrence_id)` identifies
an occurrence. Two Event atoms with the same pair in one trace are
rejected, even if their bodies match; transport deduplication belongs
upstream of semantic insertion. Distinct `occurrence_id` values
produce distinct canonical IDs even for otherwise identical prose, so
reusing a pair with contradictory content is never a silent
last-write-wins. The canonical hash remains a structural content
address, not a replacement for the occurrence key.

**Coexistence with `<EventRef>`.** EventRef remains the
external-event reference kind with `instance` / `run_id` / `sequence`
/ `for` / `wall_clock` unchanged. An EventRef may point at an Event
using its existing local `for` relationship where legacy reference
resolution already permits it; it never changes kind and gains no new
automatic interpretation. Event is neither a transport notification
envelope nor the authoritative runtime event database.

```xml
<Event id="Event_reviewed" source="review-worker" occurrence_id="review-17" event_type="review.completed" for_task="Task_review" map_ref="Map_inputs">The review result was recorded.</Event>
```

## §6 `<Task>` — declarative work semantics

| Field | Requirement | Contract |
| --- | --- | --- |
| `id` | Required | `Task_` + `[A-Za-z0-9_]+` |
| `status` | Required | Exactly `open`, `satisfied`, `unsatisfied`, or `withdrawn` |
| `for_goal` | Optional local ref | Goal only |
| `input_map` | Optional local ref | Map only |
| `output_map` | Optional local ref | Map only |
| `action_ref` | Optional local ref | Action only |
| `evidence_ref` | Optional local ref | Observation, Evidence, Finding, or Concluding only |
| `runtime_ref` | Optional opaque string | Correlates a separately authorized runtime task, never creates or controls one |
| `content` | Required body | Nonempty description of the work obligation |

**Status semantics.** `open` means the recorded obligation has no
semantic verdict; `satisfied` is an author's assertion that it was
met; `unsatisfied` asserts it was not met; `withdrawn` records that
the obligation was withdrawn. These are descriptive claims — not
enforcement, authorization, acceptance of proof, or runtime execution
states. A satisfied Task does **not** close a required Goal,
substitute for a Finding/Concluding, excuse an Action without a
recorded result, or declare a runtime task completed. Existing closure
rules remain authoritative. Runtime states such as `queued`,
`working`, `input_required`, `cancelled`, `expired`, and `paused` stay
in the runtime/transport task contract and are never inferred from
this enum. This compact verdict model intentionally differs from
runtime task status; adapters must maintain explicit correlations, and
a one-to-one enum translation is not implied.

**Evidence discipline.** `evidence_ref` is required when status is
`satisfied` or `unsatisfied`, so the verdict has an explicit
reference; validation checks shape, resolution, and target kind — not
the truth of the evidence. No evidence reference is required for
`open` or `withdrawn`.

**Immutability.** A status change creates a new immutable Task atom
with a new local ID and new canonical identity rather than mutating an
accepted historical atom in place. No persistent task-entity key,
transition machine, dependency graph, retry model, or scheduler is
introduced in the core.

```xml
<Task id="Task_review" status="open" input_map="Map_inputs" runtime_ref="opaque-task-handle">Review the fixture output.</Task>
```

## §7 Canonical identity, round trips, and collisions

`compute_canonical_id` stays byte-identical for legacy atoms:
`sha256:` plus the first 12 lowercase hex digits of the existing
canonical JSON hash. Stable local IDs keep the independent
`<Kind>_<8hex>` text-derived convenience format; canonical IDs are not
renamed to `Map_` / `Event_` / `Task_` forms. New kinds participate in
hashing through their explicit dataclass fields and the existing kind
discriminator. No global changes are made to provenance exclusions or
empty-value handling.

For new kinds, XML/JSON/YAML decoding validates field shapes before
hashing. A missing `canonical_id` is computed after all fields are
populated. An explicitly claimed ID is preserved long enough for the
existing canonical-ID validation to report mismatches; a tampered
claim is never silently replaced. A shared pure normalization helper
returns a validated copy with a missing `canonical_id` computed;
deserializers return this normalized value and serializers encode this
normalized copy. Serialization never mutates the caller's object. An
explicit mismatched `canonical_id` remains a validation failure, not
an opportunity to repair the claim silently.

**Collisions.** When a new atom's `canonical_id` equals an existing
atom's ID but the full canonical structural payload differs, that is a
reported canonical collision; records are never overwritten or merged.
Identical payloads may share canonical identity across distinct local
references, except that the Event occurrence-pair duplicate rule still
applies. The 48-bit prefix does not make collisions impossible; a
conforming implementation must expose a test seam through which a
forced truncated-hash collision is exercised. Registry collision
hardening is scoped to preventing contradictory overwrites, with
existing registry behavior preserved.

**Round trips.** Round-trip acceptance means equal semantic field
values, operators, IDs, canonical IDs, and children (empty for these
new kinds), plus stable canonical JSON on repeated encode/decode.
Identical original whitespace, YAML quoting, or XML attribute order is
not promised. Existing legacy golden canonical identities remain
byte-identical.

## §8 Versions, grammar profiles, and unsupported consumers

Proposed package/validator release metadata is **0.7.3**, matching
current parity rules across `pyproject`, `__version__`, and
`SCHOLIA_VALIDATOR_VERSION`. No tags, uploads, or releases are
authorized by this proposal.

Proposed grammar revision is **0.7.0**, distinct from package 0.7.3
and from any separately pinned transport protocol. The closed atom
catalog grows from 32 to 35; claiming this remains the unchanged
0.6.2 grammar would be misleading. The historical 0.6.2 spec and its
frozen corpus are preserved unchanged; this document and
`reference/v0.7/atoms_index.yaml` are the normative current
projection, and consistency tests are version-aware rather than
editing historical expectations.

**Legacy input.** New consumers accept existing legacy traces
unchanged. A conforming implementation provides an explicit
grammar-profile validation entry point that rejects new kinds under a
selected legacy 0.6.2 profile, and rejects an unknown future profile,
with a structured unsupported-version diagnostic
(`grammar_profile_unsupported`). The normal 0.7.3 parser may default
to the current supported grammar for unversioned local input; callers
crossing a negotiated boundary must pass/check the profile explicitly.

**Already-released consumers.** An already-released 0.7.2 consumer
cannot be retrofitted by this change: its unknown-kind parse failure
is the observed fallback. Adapters must negotiate the advertised
kind/grammar contract first and surface unsupported
capability/version rather than down-convert `Map` to `Storing`,
`Event` to `EventRef`, or `Task` to `Action`. Conformance testing
exercises the actual installed old artifact and reports its real
exception separately from the adapter's structured unsupported
diagnostic.

**Catalog agreement.** Public `__all__`, `_ATOM_CLASSES`,
`ATOM_KINDS`, `KNOWN_KINDS`, `KIND_SPECIFIC_FIELDS`, the schema/index/
reference surfaces, and installed artifacts must agree on the 35-kind
current catalog. A separately named immutable legacy catalog/profile
may be kept. Only the new atom classes and the deliberate public
contract constants/helpers are exported; no runtime transport classes
enter the core.

## §9 Proposed validator rule codes

The following rule codes are proposed for the new kinds. Legacy rules
keep their existing names and behavior. `parse`-phase rules reject
input before an atom exists; `validate`-phase rules reject a
constructed atom or trace.

| Rule code | Phase | Contract |
| --- | --- | --- |
| `semantic_unknown_field` | parse | unknown field on a new kind in XML/JSON/YAML/dict input |
| `semantic_children_empty` | parse | nonempty `children` on a new kind |
| `semantic_operators_list` | parse | `operators` on a new kind not a list of strings (no coercion from arbitrary objects) |
| `map_entries_shape` | parse | `entries` not a mapping / encoded-string where a mapping is required / nonstring or duplicate keys |
| `semantic_id_shape` | validate | missing new-kind `id`, wrong prefix, or illegal characters |
| `semantic_id_unique` | validate | ID collision involving at least one new atom, anywhere in the trace |
| `map_required_fields` | validate | missing `entries` or `value_type` on a constructed Map |
| `map_value_type` | validate | `value_type` outside the closed four-value set |
| `map_entries_typed` | validate | value violating the declared `value_type` (mixed types, bool-as-integer, out-of-range integer, float/null/list/object values, empty key) |
| `map_ref_resolves` | validate | `atom_ref` entry dangling, resolving to a Step, or self-referential |
| `event_required_fields` | validate | missing `source` / `occurrence_id` / `event_type` / nonempty body |
| `event_type_token` | validate | `event_type` failing `[A-Za-z][A-Za-z0-9_.-]*` |
| `event_timestamp_shape` | validate | naive, malformed, or impossible `timestamp` |
| `event_occurrence_unique` | validate | duplicate `(source, occurrence_id)` pair in one trace |
| `task_required_fields` | validate | missing `status` / nonempty body |
| `task_status_enum` | validate | status outside `open / satisfied / unsatisfied / withdrawn` (runtime states rejected) |
| `task_evidence_required` | validate | `satisfied` / `unsatisfied` without a resolving `evidence_ref` |
| `semantic_ref_target_kind` | validate | declared reference field dangling or resolving to a non-permitted kind |
| `canonical_id_well_formed` | validate | existing rule, unchanged: malformed or mismatched claimed `canonical_id` |
| `grammar_profile_unsupported` | validate | new kind under an explicit legacy 0.6.2 profile, or an unknown profile |

An unknown atom *kind* stays a parse-time rejection under the existing
closed-set behavior (referenced by conformance fixtures as
`unknown_kind`); it is listed here for completeness, not changed.

## §10 Conformance

The self-describing suite `conformance/v0.7/semantic_atoms.json`
carries the positive and negative fixture matrix for this proposal:
exact case IDs, kind and feature coverage, input format, payload,
expected failure phase (parse versus validate), rule code, required
diagnostic subset, and round-trip/identity expectations. It is
registered append-only in `compatibility-manifest.json`. Cases whose
behavior cannot be represented safely in static fixtures (forced
truncated-hash collisions, forbidden-I/O probes, installed-artifact
probes of an old consumer) are declared there as runtime obligations
for the implementing consumer's own suite.

Migration notes: `docs/scholia/v06.2-to-v07-migration.md`.

---

*This is a proposed candidate document. Acceptance, merge, release,
and any change to the canonical status of the v0.6.2 contract are
separate, explicit decisions that this document does not make.*
