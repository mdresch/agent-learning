# FDD-037: Design-Time Baseline Feedback Loop

**Source ADR:** [ADR-037](../../adr/ADR-037-design-time-baseline-feedback-loop.md) — Accepted (2026-10-27)  
**Source BRD:** [BRD-037](../Business-Requirements/BRD-037-design-time-baseline-feedback-loop.md)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-037 and BRD-037; not yet adjudicated via `approve-fdd`. §5 interpretations are not confirmed.

---

## 1. Architecture and Component Placement

1. **`evidence_basis`** is a keyword-only argument on `evaluate_governance_diff` in `src/agent_learning/governance.py`. The function already builds the `audit_evidence` envelope and, for an autonomous disposition, the audit episode. This change adds one key. It does not add a policy, a record type, or a logit.
2. **BFI, version bump, and section text** live in `src/agent_learning/pmbok/baseline_feedback.py`. That module is pure: standard library only. It does not import `LearningStore`, `TaskPolicy`, or the legacy `pmbok` package.
3. **Unchanged callers.** Every current call omits the new argument and therefore records `execution`. `DIFF_ACTIONS`, `ESCALATION_ACTIONS`, and `PERMANENTLY_FROZEN_DIFF_TYPES` stay as Epic 7 left them.
4. **Not here.** Charter limits, the moment a patch id is recorded, `approve-pmp`, and the legacy generator.

---

## 2. Data Contract

```python
EVIDENCE_BASES: tuple[str, ...] = ("design_time", "execution")
DEFAULT_EVIDENCE_BASIS: str = "execution"

# baseline_feedback.py
BFI_ID = re.compile(r"^BFI-\d{3,}$")
BFI_STATUSES: tuple[str, ...] = ("open", "applied", "closed")
BFI_STAGES: tuple[int, ...] = (7, 8)
FORBIDDEN_KEYS: frozenset[str] = frozenset({"duration", "cost", "estimated_date"})

@dataclass(frozen=True)
class Citation:
    path: str       # relative, no leading slash
    section: str    # non-empty

@dataclass(frozen=True)
class BaselineFeedbackItem:
    bfi_id: str
    stage: int
    document: str
    citations: tuple[Citation, ...]   # at least one
    classification: str                # empty, or one of DIFF_ACTIONS
    evidence_basis: str                # always "design_time"
    status: str                        # one of BFI_STATUSES
```

`classification` empty means not yet classified. A non-empty value must be one of the seven existing diff action ids. There is no eighth class.

---

## 3. Behavior

### 3.1 `evaluate_governance_diff(..., evidence_basis="execution")` (BRU-037-01, BRU-037-06)

The argument is keyword-only. Omitted, it is `execution`. A value outside `EVIDENCE_BASES` raises `ValueError` naming `evidence_basis`, before the classify policy is called.

On the path that builds the envelope today, `audit_evidence["evidence_basis"]` is that value. The keys already present stay: `source_task_id`, `classified_diff_type`, `robust_utility`, `runner_up_margin`, `criteria_supports`, `target_artifact`. No other key is added. When an audit episode is stored, its `metadata["audit_evidence"]` is that same dict, so the key is on the episode.

On the halt path (`NEEDS_USER_TIE_BREAK` or `NEEDS_USER_FEEDBACK`), no episode is written and the escalation policy is not called. The returned `audit_evidence` is exactly `{"evidence_basis": <value>}`. That is the whole envelope, because the classification envelope is not built on this path.

`read_evidence_basis(metadata) -> str` returns `metadata["evidence_basis"]` when the key is present and valid. A missing key returns `execution`. A present key outside the closed list raises `ValueError`.

The escalation policy is still called as `decide(audit_evidence=envelope)` on the non-halt, non-frozen path. `evidence_basis` is inside that dict. It is not passed as its own argument, and it is not an action id. A class in `PERMANENTLY_FROZEN_DIFF_TYPES` still sets disposition `escalate_to_human` when the basis is `design_time`.

### 3.2 `baseline_feedback_item(mapping) -> BaselineFeedbackItem` (BRU-037-02, BRU-037-05)

Builds one item from a mapping. Raises `ValueError` naming the field when:

- `bfi_id` fails `BFI_ID`
- `stage` is not 7 or 8
- `document` is empty
- `citations` is empty, or a citation path is empty, absolute, or a section is empty
- `evidence_basis` is not `design_time`
- `status` is not one of `BFI_STATUSES`
- `classification` is not empty and not one of `DIFF_ACTIONS`
- any key in `FORBIDDEN_KEYS` is present

The function does not read a file and does not write a store. It does not check that the cited path exists.

### 3.3 `next_baseline_id(current, evidence_basis) -> str` (BRU-037-07)

`current` matches `PMP-BL-v<major>.<minor>.<patch>`, each part a non-negative integer without a leading plus. `design_time` returns the same major and minor with patch + 1. `execution` returns the same major, minor + 1, and patch 0. Any other basis raises `ValueError`. A string that is not that shape raises `ValueError`. The major number is never incremented. Examples: `PMP-BL-v1.0.0` becomes `PMP-BL-v1.0.1` or `PMP-BL-v1.1.0`; `PMP-BL-v1.0.3` under `execution` becomes `PMP-BL-v1.1.0`; `PMP-BL-v1.1.0` under `design_time` becomes `PMP-BL-v1.1.1`.

The function does not look at plans, packages, or the Charter. It does not decide whether this call is allowed.

### 3.4 `pending_feedback_section(items) -> str` (BRU-037-09)

Returns Markdown. The heading line is `## Baseline Feedback (Stage 7-8 → 6)`. The prose names both routes: design-time (Stage 7-8, BFI, Stage 16, Stage 6, patch) and execution (Stages 9-15, Stage 16, Stage 17, Stage 6, minor). Then a table with columns `bfi_id`, `stage`, `document`, `citation`, `classification`, `evidence_basis`, `status`.

Zero items produce one data row whose `citation` cell is `None` and whose other cells are empty. One or more items produce one row each, citations joined by `; ` as `path#section`, and no `None` row. Items are rendered in input order. The function does not write a file and does not import the legacy generator.

---

## 4. Error Handling

| Situation | Behavior |
|---|---|
| `evidence_basis` omitted | Recorded as `execution` |
| `evidence_basis` other than the two names | `ValueError` before classify runs |
| Tie-break or needs-feedback halt | No episode; envelope is exactly `{"evidence_basis": <value>}` |
| Metadata with no `evidence_basis` key | `read_evidence_basis` returns `execution` |
| Metadata with an unknown basis | `ValueError` |
| Frozen diff class, basis `design_time` | Disposition `escalate_to_human` |
| BFI mapping with `duration`, `cost`, or `estimated_date` | `ValueError` naming the key |
| BFI with `evidence_basis` `execution` | `ValueError` |
| Baseline id `PMP-BL-v1.0` | `ValueError` |
| Empty item list | Section contains one `None` citation row |

---

## 5. Interpretations to Confirm

These are not verbatim in ADR-037. Story 37.1 waits on item 2. Stories 37.2 and 37.4 wait on item 1.

1. **BFI shape.** The id matches `BFI-` plus at least three digits. Status is `open`, `applied`, or `closed`. Stage is 7 or 8. Classification is empty or one of the seven existing diff action ids. Every BFI's basis is `design_time`. Uniqueness per cycle or per baseline is not checked.
2. **The halt envelope carries the basis and nothing else.** The classification envelope is not built when the classify call halts. A later reader of that in-memory result still sees the basis. No episode is written on that path.
3. **`next_baseline_id` only formats.** ADR-037 §8 item 2, when a patch is recorded, stays open. The function is not that decision.
4. **The four landing places stay a human reading.** Charter approval limits are not in this repository. There is no function from the seven classes to editorial, upstream, PM, or Steering.
5. **The section function is not wired to the legacy generator.** ADR-034's ported builder is the caller, and it does not exist yet.

## 6. Out of Scope

Same boundary as BRD-037. `baseline_feedback.py` does not import storage. `governance.py` gains one argument and one reader. It does not gain a task id.
