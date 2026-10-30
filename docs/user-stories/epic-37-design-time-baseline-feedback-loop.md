# Epic 37: Design-Time Baseline Feedback Loop

**Source ADR:** [ADR-037](../adr/ADR-037-design-time-baseline-feedback-loop.md) — Accepted (2026-10-27)  
**Source BRD/FDD:** [BRD-037](../project-docs/Business-Requirements/BRD-037-design-time-baseline-feedback-loop.md) / [FDD-037](../project-docs/Functional-Design/FDD-037-design-time-baseline-feedback-loop.md)  
**Status:** Draft (2026-10-29) — derived from Accepted ADR-037, BRD-037 and FDD-037; not yet adjudicated via `approve-user-stories`.

Four stories. Each rule sits in one story (LL-012). Contract tests: `tests/test_evidence_basis.py` (37.1), `tests/test_baseline_feedback_item.py` (37.2), `tests/test_baseline_increment.py` (37.3), `tests/test_baseline_feedback_section.py` (37.4). Story 37.1 waits on FDD-037 §5 item 2. Stories 37.2 and 37.4 wait on item 1. BRU-037-03, BRU-037-04, and BRU-037-08 have no story: the existing pair is not wrapped in a new map, the revision package is assembled by a person, and lessons, Stage 17, and Stage 18 are not entered.

---

## Story 37.1 — Record design-time evidence on the existing governance call

**Status:** Draft — blocked on confirmation of FDD-037 §5 item 2  
**As** a governance reviewer,  
**I want** `evaluate_governance_diff` to record whether the finding is design-time or execution,  
**so that** a later episode can tell the two apart without a new policy.

### Acceptance Criteria

- **$AC_0$ (Default):** A call that omits `evidence_basis` puts `execution` on `audit_evidence`. The keys `source_task_id`, `classified_diff_type`, `robust_utility`, `runner_up_margin`, `criteria_supports`, and `target_artifact` are still present. No key other than `evidence_basis` is added.
- **$AC_1$ (Design-time):** The same call with `evidence_basis="design_time"` records `design_time` on the envelope. When the disposition stores an audit episode, `metadata["audit_evidence"]["evidence_basis"]` is `design_time`.
- **$AC_2$ (Halt):** A classify result of `NEEDS_USER_TIE_BREAK` or `NEEDS_USER_FEEDBACK` writes no episode, leaves `escalation_result` as `None`, and returns `audit_evidence` equal to `{"evidence_basis": "design_time"}` when that basis was passed, or `{"evidence_basis": "execution"}` when it was omitted.
- **$AC_3$ (Reader):** `read_evidence_basis` of a metadata dict with no key returns `execution`. A dict with `design_time` returns `design_time`. A dict with `other` raises `ValueError`.
- **$AC_4$ (Not a feature):** `DIFF_ACTIONS` and `ESCALATION_ACTIONS` are unchanged. A class in `PERMANENTLY_FROZEN_DIFF_TYPES` still yields disposition `escalate_to_human` when the basis is `design_time`. `evidence_basis` is not an action id.
- **$AC_5$ (Refusal):** `evidence_basis="both"` raises `ValueError` naming `evidence_basis`, and the classify policy's decide method is not called.

---

## Story 37.2 — A baseline feedback item cites documents and carries no numbers

**Status:** Draft — blocked on confirmation of FDD-037 §5 item 1  
**As** a governance reviewer,  
**I want** a design-time finding stored as a checked table row,  
**so that** it cannot pretend to be execution evidence or a new database entity.

### Acceptance Criteria

- **$AC_0$ (Row):** A mapping with `BFI-001`, stage 7, a non-empty document, one citation `docs/adr/ADR-008.md` section `4.4`, an empty classification, basis `design_time`, and status `open` returns a frozen `BaselineFeedbackItem` with those values.
- **$AC_1$ (Shape):** `BFI-1`, stage 9, an empty citation list, a citation with an empty section, basis `execution`, and status `draft` each raise `ValueError` naming the field. `BFI-1000` is accepted. Status `applied` and `closed` are accepted.
- **$AC_2$ (Class):** Classification `correction_note` is accepted. Classification `new_class` raises `ValueError`. An empty classification is accepted.
- **$AC_3$ (No numbers):** A mapping that also has `duration`, `cost`, or `estimated_date` raises `ValueError` naming that key. The dataclass has no such field.
- **$AC_4$ (Purity):** `baseline_feedback.py` imports no storage module and no `TaskPolicy`. The builder does not read the citation path from disk.

---

## Story 37.3 — Design-time bumps the patch, execution bumps the minor

**Status:** Draft  
**As** a governance reviewer,  
**I want** the next baseline id to follow the route,  
**so that** a design-time fix is not numbered as an adaptation.

### Acceptance Criteria

- **$AC_0$ (Patch):** `next_baseline_id("PMP-BL-v1.0.0", "design_time")` is `PMP-BL-v1.0.1`. `next_baseline_id("PMP-BL-v1.1.0", "design_time")` is `PMP-BL-v1.1.1`.
- **$AC_1$ (Minor):** `next_baseline_id("PMP-BL-v1.0.0", "execution")` is `PMP-BL-v1.1.0`. `next_baseline_id("PMP-BL-v1.0.3", "execution")` is `PMP-BL-v1.1.0`.
- **$AC_2$ (Major stays):** Both bases leave the major number unchanged. No input in this story produces `PMP-BL-v2.0.0`.
- **$AC_3$ (Refusal):** `PMP-BL-v1.0`, `v1.0.0`, and an empty string raise `ValueError`. Basis `both` raises `ValueError`.
- **$AC_4$ (Formatter only):** The function takes the current id and the basis. It has no parameter for a plan id, a package, or a Charter limit.

---

## Story 37.4 — The pending-feedback section names both loops

**Status:** Draft — blocked on Story 37.2  
**As** a maintainer of the future PMP builder,  
**I want** one function that renders the baseline-feedback section,  
**so that** the ported builder can emit it without editing the legacy generator.

### Acceptance Criteria

- **$AC_0$ (Heading):** `pending_feedback_section(())` starts with `## Baseline Feedback (Stage 7-8 → 6)`. The body names the design-time path and the execution path, including Stage 17 on the execution path only.
- **$AC_1$ (None):** The empty call renders one table row whose citation cell is `None` and whose other cells are empty.
- **$AC_2$ (Rows):** Two items render two data rows, in input order, with no `None` row. A citation `docs/adr/ADR-008.md` section `4.4` appears as `docs/adr/ADR-008.md#4.4`. Two citations on one item are joined with `; `.
- **$AC_3$ (Columns):** The header row names `bfi_id`, `stage`, `document`, `citation`, `classification`, `evidence_basis`, and `status`.
- **$AC_4$ (Unwired):** The function writes no file. `baseline_feedback.py` does not import the legacy `pmbok` package. `Project-Management-Plan.md` is not modified by this story.

---

## Out of Scope for this epic

- A new task id, or a change to the seven diff classes or the three escalation actions.
- Using `evidence_basis` as a bandit feature.
- Mapping classes to editorial, upstream, PM, or Steering.
- Building `approve-pmp` or writing the revision package to disk.
- Deciding when a patch id is recorded.
- Editing the legacy generator, the current PMP, or the SIDPA template.
- Re-logging old Adaptation Plans.
- Checking BFI uniqueness across cycles.
- Lessons learned, Stage 17, and Stage 18.
