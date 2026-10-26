# FDD-036: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop

**Source ADR:** [ADR-036](../../adr/ADR-036-learning-methodology-examples-ledger-and-review-triage-loop.md) — Proposed (2026-10-26)  
**Source BRD:** [BRD-036](../Business-Requirements/BRD-036-learning-methodology-examples-ledger-and-review-triage-loop.md)  
**Status:** Draft (2026-10-26) — not yet approved; `approve-fdd` has not been run.  

---

## 1. Architecture & Component Placement

1. **Pure modules**, standard library only, in the style of `lessons_learned.py` and `tailoring.py`: `src/agent_learning/methodology_catalog.py`, `methodology_ledger.py` and `review_triage.py`. No file I/O, no storage access, no import of `pmbok/`. Callers pass text or plain data and receive dataclasses.
2. **Content, not code, for examples:** `examples/methodologies/catalog.json` and one directory per methodology under `examples/methodologies/<NN>-<slug>/`.
3. **Registers:** `docs/project-docs/Methodology-Best-Practice-Ledger.md` (new), and the existing `implementation-log.md` carries the S0 triage lines.
4. **Package export:** public names are re-exported from `agent_learning/__init__.py`.
5. **Reuse:** the reliability estimate calls `agent_learning.autonomy.wilson_lower_bound`. Nothing is duplicated.

---

## 2. Data Contract

### 2.1 Catalog entry
```python
class ExampleClass(str, Enum):
    RUNNABLE = "runnable"
    PROOF_OF_CONCEPT = "proof_of_concept"
    DOCUMENTED = "documented"

@dataclass(frozen=True)
class CatalogEntry:
    id: int                      # 1..32
    name: str
    state: str                   # copied from Ideation section 2.1
    example_class: ExampleClass
    adr: str | None              # e.g. "ADR-015"
    hypothesis: str | None       # e.g. "HYP-AL-009"
    path: str | None             # directory under examples/methodologies/, None for documented
    reason: str = ""             # required when documented
    reopening_condition: str = ""  # required when documented
```
**Class derivation** (`derive_class(state, adr)`): state in Implemented, example-only, partial or practiced gives `RUNNABLE`; a candidate with a Proposed ADR and no code gives `PROOF_OF_CONCEPT`; blocked, excluded, declined, not applicable, or candidate with no ADR gives `DOCUMENTED`. The state vocabulary is the one in the selection skill's index.

### 2.2 Ledger entry
```python
@dataclass(frozen=True)
class LedgerEntry:
    id: str                      # "BP-001"
    methodology: int             # catalog id
    practice: str
    preconditions: str
    applies_to: str              # "store" | "lessons-learned" | "both" | "other"
    evidence_class: str          # "source-doc" | "synthetic-demo" | "real-episodes"
    evidence_ref: str
    evidence_count: int
    status: str                  # "candidate" | "adopted" | "retired"
    supersedes: str | None
    links: tuple[str, ...]       # LL-### and HYP-AL-### identifiers
```

### 2.3 Triage record
```python
@dataclass(frozen=True)
class TriageRecord:
    finding_id: str              # "Q-12-3": reviewer initial, PR number, ordinal
    reviewer: str                # "amazon-q"
    pr: int
    claim_type: str              # logic error | crash risk | test gap | documentation | style | unknown
    verified: str                # yes | no | partial | unknown
    decision: str                # accepted | declined | deferred | unknown
    reason: str
    fix: str | None              # commit hash or None
    reconstructed: bool = False
```
The S0 line is `finding_id | claim type | verified: <v> | decision: <d> | <reason> | fix: <commit or none>`.

---

## 3. Behavior

1. **`validate_catalog(entries, ideation_states)`** raises `ValueError` listing the problem: a missing or duplicate id, an id outside 1 to 32, a class that differs from `derive_class`, a `documented` entry with an empty reason or reopening condition, or a path outside `examples/methodologies/`.
2. **`parse_ledger(text)`** parses the register and raises `ValueError` naming the entry for: an unknown enumeration value, an unknown methodology id, `adopted` with an evidence class other than `real-episodes`, or `supersedes` pointing at an unknown entry. The current state of an entry is the latest entry in its supersedes chain.
3. **`parse_triage_line(line)`** returns a `TriageRecord`, rejecting a line whose field is outside its vocabulary. A field written `unknown` is accepted as is.
4. **`to_episode_metadata(record)`** returns a plain dict of the record's fields and `reconstructed`. It imports nothing from `agent_learning.storage`.
5. **`reliability(records, reviewer, claim_type, z=1.96, min_cases=5)`** counts the reviewer's records of that claim type whose `verified` is `yes` or `no` (`partial` counts as `no`, `unknown` is excluded) and returns `Reliability(cases, verified, lower_bound)`. When `cases < min_cases`, `lower_bound` is `None`. It never returns a number it cannot support.
6. **Examples:** each example script prints a result and exits 0 offline; each runs in a temporary directory with a fixed seed where random. Each starts with the header in ADR-036 §4.2.

**Provisional:** `min_cases = 5` is a starting value, open for the maintainer to confirm (ADR-036 §8). The `partial` mapping is an interpretation, recorded here and in the tests.

---

## 4. Error Handling

| Scenario | Behavior |
|---|---|
| Catalog lists 31 or 33 entries | `ValueError` naming the missing or extra ids |
| Ledger entry adopted on `synthetic-demo` evidence | `ValueError` naming the entry |
| Triage line has an unrecognized claim type | `ValueError` naming the field and value |
| Reliability asked with too few cases | `lower_bound` is `None`, not 0 |
| An example run changes the catalog state | Not possible by design; a test asserts the catalog file is byte-identical after the runs |

---

## 5. Out of Scope

Building the unbuilt methodologies, any autonomy for accepting or declining findings, a `trace_id` on `Episode`, and creating the `triage-review-finding` or `route-review-finding` policies (they are declared when ADR-036 is accepted and Story 13.5 runs).
