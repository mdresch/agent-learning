# FDD-035: Cycle Identification and Cross-Cycle Artifact Traceability

**Source ADR:** [ADR-035](../../adr/ADR-035-cycle-identification-and-cross-cycle-artifact-traceability.md) — Proposed (2026-10-26)  
**Source BRD:** [BRD-035](../Business-Requirements/BRD-035-cycle-identification-and-cross-cycle-artifact-traceability.md)  
**Status:** Draft (2026-10-29) — derived from Proposed ADR-035 and BRD-035; not yet adjudicated via `approve-fdd`. §5 interpretations are not confirmed. Adjudication waits until ADR-035 is accepted.

---

## 1. Architecture and Component Placement

1. **Cycle checks** live in `src/agent_learning/pmbok/cycle.py`. `lint_plan` calls the frontmatter flag function when a governed plan is linted. The register validator is a separate function. It is not a plan lint.
2. **Hash neutrality** is an addition to `VOLATILE_KEYS` in `src/agent_learning/pmbok/standards.py`, consumed by the Epic 13 `strip_volatile_frontmatter`. The two new keys are `cycle_id` and `baseline_id`. The existing four keys stay.
3. **Purity:** standard library plus existing `LintFlag`. No file I/O, no `LearningStore`, no network. The caller reads the register text and the episode metadata and passes them in.
4. **Already satisfied elsewhere:** canonical hashing, apart from the two new volatile keys, stays Epic 13. Plan grammar stays Epic 12. `cycle_id` is a flat scalar, so the ADR-034 §4.3.1 grammar does not change.

---

## 2. Data Contract

```python
CYCLE_ID = re.compile(r"^CYC-\d{3,}$")
BASELINE_ID = re.compile(r"^PMP-BL-v\d+\.\d+\.\d+$")
STATES = ("OPEN", "CLOSED_BASELINED", "ROLLED_BACK", "ABANDONED")
TRIGGERS = ("initial", "adaptation", "refinement")
PIN_MARKS = ("live", "reconstructed", "unrecoverable")

@dataclass(frozen=True)
class Pin:
    artifact: str          # relative path, no leading slash
    version: str
    content_hash: str      # 64 lowercase hex, or the token "unrecoverable"
    mark: str              # one of PIN_MARKS

@dataclass(frozen=True)
class CycleRow:
    cycle_id: str
    state: str
    date: str              # YYYY-MM-DD
    trigger: str           # empty on a terminal row, or one of TRIGGERS
    episode_ref: str
    baseline_id: str       # empty except on CLOSED_BASELINED
    opening_pin_set: tuple[Pin, ...]
    closing_pin_set: tuple[Pin, ...]
    prior_cycle: str       # empty or a cycle_id

@dataclass(frozen=True)
class LookupHit:
    cycle_id: str
    source: str            # "pin" | "episode" | "frontmatter"
    row: CycleRow          # the latest row for cycle_id
```

The register is a Markdown table whose header is exactly:

`| cycle_id | state | date | trigger | episode_ref | baseline_id | opening_pin_set | closing_pin_set | prior_cycle |`

A pin cell holds zero or more pins separated by `; `. Each pin is `artifact|version|content_hash|mark`. An empty cell is an empty tuple. `mark` `unrecoverable` requires `content_hash` to be the token `unrecoverable`. `live` and `reconstructed` require 64 lowercase hex.

---

## 3. Behavior

### 3.1 `read_baseline(fields) -> str | None` (BRU-035-01)

`fields` is the parsed frontmatter mapping. When `baseline_id` is present, return it. Otherwise return `pmp_baseline` when present, otherwise `pmp_baseline_id`, otherwise `None`. The returned text is not format-checked here.

### 3.2 Volatile keys (BRU-035-02)

`VOLATILE_KEYS` becomes `("last_modified", "generated_at", "governance_hash", "approval_ref", "cycle_id", "baseline_id")`. `strip_volatile_frontmatter` already strips every name in that tuple. A plan whose only edit is `cycle_id` or `baseline_id` keeps its canonical hash. A body-word edit still changes it. Alias keys `pmp_baseline` and `pmp_baseline_id` are not volatile. Changing an alias still changes the hash, which is why new artifacts use `baseline_id`.

### 3.3 `parse_register(text) -> tuple[CycleRow, ...]` (BRU-035-03, BRU-035-04)

Reads the one table. A missing header, a missing column, or a pin that breaks §2 raises `ValueError` naming the row number. The function does not write the file.

### 3.4 `validate_register(rows) -> list[str]` (BRU-035-03, BRU-035-04)

Returns messages, in this order, and does not stop at the first. An empty row list returns `[]`.

1. The first introduced id is not `CYC-001`.
2. A newly introduced id is not exactly one greater than the highest id already introduced.
3. A `cycle_id` has a first row whose state is not `OPEN`.
4. A `cycle_id` has more than two rows, or has a second row whose state is not `CLOSED_BASELINED`, `ROLLED_BACK`, or `ABANDONED`.
5. More than one `cycle_id` has latest state `OPEN`.
6. A row has an empty `episode_ref`, or a `date` that is not `YYYY-MM-DD`.
7. An `OPEN` row whose `trigger` is not one of `TRIGGERS`.
8. A `CLOSED_BASELINED` row with an empty `baseline_id`, a `baseline_id` that fails `BASELINE_ID`, or an empty `closing_pin_set`.
9. A `ROLLED_BACK` or `ABANDONED` row whose `closing_pin_set` is non-empty, or whose `baseline_id` is non-empty.
10. A `prior_cycle` that is non-empty and does not match `CYCLE_ID`, or that names an id with no earlier row.

A message names the `cycle_id` and the rule number. `parse_register` has already rejected a broken pin, so this function does not re-check pin marks.

### 3.5 `lookup(content_hash, episode_cycle_id, frontmatter_cycle_id, frontmatter_baseline_id, rows) -> LookupHit | None` (BRU-035-05)

Stop at the first hit.

1. **Pin.** The last row, in list order, that contains `content_hash` on a pin whose mark is `live` or `reconstructed`. `unrecoverable` pins are not hits. The hit's row is the latest row for that `cycle_id`, which may be a later row than the pin row.
2. **Episode.** Used only when step 1 missed and `episode_cycle_id` is not `None`. When that id has a row, the hit's source is `episode`. When it has no row, `lookup` returns `None` and does not try step 3.
3. **Frontmatter.** Used only when steps 1 and 2 missed and `frontmatter_cycle_id` is not `None`. The id must be present in `rows`, and `frontmatter_baseline_id` must equal the latest row's `baseline_id`, including both empty.

`None` means none of the three sources hit. A present episode id that is absent from the register does not fall through to frontmatter. That case is a mismatch in §3.6.

### 3.6 `linkage_flags(frontmatter_cycle_id, frontmatter_baseline_id, rows, episode_cycle_id) -> list[LintFlag]` (BRU-035-01, BRU-035-06)

Tier B, in this order.

1. `frontmatter_cycle_id` is not `None` and fails `CYCLE_ID`. Code `INVALID_METADATA`, message `cycle_id is malformed`.
2. `frontmatter_baseline_id` is not `None` and not empty and fails `BASELINE_ID`. Code `INVALID_METADATA`, message `baseline_id is malformed`. An omitted baseline (`None` or empty) produces no baseline-format finding.
3. When steps 1 and 2 produced no finding, and `lookup` would select a register row, a frontmatter `cycle_id` or `baseline_id` that differs from that latest row. Code `TRACEABILITY_MISMATCH`, message `frontmatter linkage disagrees with the register`, naming each differing field.
4. When the episode id is not `None` and is absent from `rows`, or the episode id differs from the cycle a pin hit selected. Code `TRACEABILITY_MISMATCH`, message `episode linkage disagrees with the register`. This finding does not replace steps 1 and 2.

Flags do not include the closure refusal. That is §3.7.

### 3.7 `closure_refused(register_cycle_id, register_baseline_id, episode_cycle_id, episode_baseline_id) -> bool` (BRU-035-06)

Returns `True` when both cycle ids are non-empty and differ, or both baseline ids are non-empty and differ. Returns `False` when either side of a pair is empty. The caller treats `True` as a refusal to append a `CLOSED_BASELINED` row. This function does not write.

### 3.8 Bootstrap shape (BRU-035-08)

A single `OPEN` row for `CYC-001`, trigger `initial`, a non-empty `episode_ref`, an empty `baseline_id`, and an opening pin marked `reconstructed` or `unrecoverable`, passes `validate_register`. The module does not create `Cycle-Register.md`.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| Register text with no matching header | `ValueError` from `parse_register` |
| Pin mark other than the three, or a live pin whose hash is not 64 hex | `ValueError` naming the row |
| `unrecoverable` pin with a hex hash | `ValueError` naming the row |
| Two `OPEN` cycles | `validate_register` message, rule 5 |
| Hash found in a pin | `lookup` source `pin`; frontmatter is not consulted |
| Episode id set and absent from the register | `lookup` returns `None`; `linkage_flags` adds `TRACEABILITY_MISMATCH` |
| Empty baseline on an `OPEN` cycle | No `INVALID_METADATA` |
| `closure_refused` is `True` | Caller appends no row; the function writes nothing |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-035. Stories 35.2 and 35.3 wait on item 1.

1. **The register table and the pin cell are the grammar above.** The ADR names the fields and not the Markdown cell. Pins are `artifact|version|content_hash|mark`, separated by `; `. Marks are `live`, `reconstructed`, and `unrecoverable`.
2. **A pin hit uses the last matching row in file order, then reports the latest row of that cycle.** An `unrecoverable` pin is never a hash hit.
3. **An episode id that the register does not contain does not fall through to frontmatter.** It is `TRACEABILITY_MISMATCH`.
4. **Alias keys stay in the hash.** Only `baseline_id` and `cycle_id` are volatile. `pmp_baseline` and `pmp_baseline_id` remain readability aliases.
5. **`validate_register` returns messages. It does not raise for a structurally illegal but parseable register.** Broken syntax raises from `parse_register`.
6. **This epic does not write `Cycle-Register.md` and does not recover git blobs.** A test builds the `CYC-001` `OPEN` shape in memory.
7. **Closure refusal is a boolean, not a lint flag.** Frontmatter disagreement stays Tier B.

## 6. Out of Scope

Same boundary as BRD-035. `cycle.py` does not import storage and does not open the register file itself. It does not edit ADR-008, ADR-012, or ADR-013.
