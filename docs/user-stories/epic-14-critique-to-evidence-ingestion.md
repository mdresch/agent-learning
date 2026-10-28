# Epic 14: Lightweight Critique-to-Evidence Ingestion

**Source ADR:** [ADR-014](../adr/ADR-014-critique-to-evidence-ingestion.md) — Accepted (2026-10-28)  
**Source BRD/FDD:** [BRD-014](../project-docs/Business-Requirements/BRD-014-critique-to-evidence-ingestion.md) / [FDD-014](../project-docs/Functional-Design/FDD-014-critique-to-evidence-ingestion.md)  
**Status:** Draft (2026-10-28) — stories derived from Accepted ADR-014, BRD-014 and FDD-014; not yet adjudicated through `approve-user-stories`. The epic number follows the source ADR number, as Epic 11 follows ADR-011.  

Five stories build the pure module `src/agent_learning/critique_evidence.py`. Each rule sits in exactly one story's criteria (LL-012). Contract tests are `tests/test_critique_parse.py` (14.1), `tests/test_critique_apply.py` (14.2 and 14.3) and `tests/test_critique_metadata.py` (14.4). Story 14.5 is data work and has no test file.

**Stories 14.2 to 14.4 are unblocked.** Menno confirmed FDD-014 §4 (D1 to D5) on 2026-10-28 and ADR-014 was amended to match. ADR-014 §4.4 as first accepted failed BRU-014-03: it made a defect finding raise the pooled support. The stories below build the corrected mechanism of FDD-014 §3.

Fixture used by the criteria below ("the base frame"): one option with two evidence points on one criterion, (support 0.8, confidence 0.8) and (support 0.7, confidence 0.9). The resolver pools them to 0.8666.

---

## Story 14.1 — The Tag Grammar and Parser

**Status:** Draft  
**As** a reviewer, **I want** my tagged findings read exactly as written, **so that** no number is ever guessed on my behalf.

### Acceptance Criteria:
- **$AC_0$ (Grammar):** `parse_critique(text, source_id)` returns one `CritiqueDelta` per bullet of the form in FDD-014 §2.1, in line order, with the rationale kept verbatim. Lines that are not bullets are ignored.
- **$AC_1$ (No Guessing):** a bullet without a `[criterion: ...]` tag, or without a signed number, raises `ValueError` naming the line number.
- **$AC_2$ (Bounds):** a delta of `-1.20` or `+1.01` raises `ValueError`; `-1.00` and `+1.00` are accepted.
- **$AC_3$ (Fields):** an empty rationale, an invalid finding id, or an invalid `source_id` raises `ValueError`.
- **$AC_4$ (Finding Ids):** a bullet with `[finding: Q-34-1]` keeps that id; one without gets `<source_id>#<n>`, where `n` counts the bullets from 1.
- **$AC_5$ (Pure):** `critique_evidence.py` imports nothing from `agent_learning.storage` and performs no file I/O.

---

## Story 14.2 — Moving the Pooled Support by the Delta

**Status:** Draft  
**As** a maintainer, **I want** a finding's delta to move the criterion's pooled support by exactly that delta, **so that** a defect never raises a score and a confirmation never lowers it.

### Acceptance Criteria:
- **$AC_0$ (Exact Shift):** on the base frame, a delta of -0.20 gives a pooled support of 0.6666 and +0.10 gives 0.9666, each within 1e-9 of `clip(before + delta)`, measured through `DecisionResolver.resolve()` and not through the module's own arithmetic.
- **$AC_1$ (Direction):** over a grid of base supports and deltas, a negative delta never raises the pooled support, a positive delta never lowers it, and a zero delta leaves it unchanged.
- **$AC_2$ (Clamp):** deltas of -0.9 and +0.9 on the base frame land within 1e-6 of 0 and 1, and the appended point's support is a valid value in [0, 1].
- **$AC_3$ (Sequence):** two deltas on one criterion (-0.20, then -0.10) are applied in order, each against the pooled support left by the previous one, and end at `before - 0.30` within 1e-9.

---

## Story 14.3 — Doubt, Traceability and Validation

**Status:** Draft  
**As** an auditor, **I want** every appended point to name its finding and nothing else to change, **so that** I can trace each score change and trust the rest of the frame.

### Acceptance Criteria:
- **$AC_0$ (Doubt):** the appended point's confidence is `max(1 - u_after, 0.05)`, where `u_after = min(1, u + kappa * max(0, -delta))` and `u = 1 - mean(confidence)` of the criterion's points at that step, including points appended by earlier deltas in the same call. A positive delta leaves `u_after = u`.
- **$AC_1$ (Source):** every appended point has the source `critique:<finding_id>`, and every point of the input frame is present unchanged in the output.
- **$AC_2$ (No Mutation):** the input frame is equal to its earlier copy after `apply_critique`; the output is a new object.
- **$AC_3$ (Validation):** `ValueError` for an unknown criterion, an unknown option, a criterion with no evidence on the option, the same finding id twice for one criterion, a finding id already used as a source, and `kappa` outside [0.1, 0.5].
- **$AC_4$ (Resolver Accepts It):** the resolver accepts every output frame, including one with the minimum confidence of 0.05 and one whose appended point has a support within 1e-6 of 0 or 1 (the point's own support may round to exactly 1.0; the pooled support never reaches the edge, because the target is clamped).

---

## Story 14.4 — Episode Metadata

**Status:** Draft  
**As** a maintainer, **I want** the applied adjustments stored as plain metadata on the episode, **so that** the audit trail needs no new record type.

### Acceptance Criteria:
- **$AC_0$ (Shape):** `to_episode_metadata(applied)` returns `{"critique_adjustments": [...]}` with one entry per delta holding the fields of FDD-014 §2.2.
- **$AC_1$ (JSON Safe):** the result survives `json.dumps` and `json.loads` unchanged, and floats are not converted to strings.
- **$AC_2$ (Consistent):** for each entry, `support_after` equals the pooled support of the output frame within 1e-9, and `point_confidence` equals the appended point's confidence.
- **$AC_3$ (Storage Boundary):** attaching the result to an `Episode` and storing it in an in-memory store adds no record type and round-trips the metadata.

---

## Story 14.5 — Replay on the Real Triage Records

**Status:** Draft — blocked until the original Amazon Q comments are exported from the PR threads (ADR-014 §4.4, test data gap).  
**As** a maintainer, **I want** the 30 real review-triage records tagged by a person and run through the module, **so that** I can see whether the deltas point the way the human decisions did.

### Acceptance Criteria:
- **$AC_0$ (Real Source):** the findings come from the records in `implementation-log.md` read with `review_triage.find_triage_lines`, with the original comment text exported beside each.
- **$AC_1$ (Tagged By A Person):** every criterion tag and delta is entered by a named person, and the name is recorded; the module never proposes them.
- **$AC_2$ (Declined Findings):** a finding the human *declined* in triage is one the human judged not to be a real defect, so its recorded delta is zero or positive and never negative; applying it does not lower the pooled support of the criterion it names. Any declined finding tagged with a negative delta is listed, not hidden.
- **$AC_3$ (Accepted Findings):** a finding the human *accepted* in triage was a real defect, so its recorded delta is negative, and applying it lowers the pooled support by that delta.
- **$AC_4$ (Not Evidence Of Effectiveness):** the result is recorded as a consistency check on the tagging. It makes no claim that the method improves decisions (HYP-AL-005 stays open).
