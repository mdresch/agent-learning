---
artifact_type: "cumulative_lineage_kernel"
kernel_id: "CLK-20261111-001"
phase_closed: "Phase 2"
phase_seeded: "Phase 3"
baseline_from: "PMP-BL-v1.1.0"
baseline_to: "PMP-BL-v1.2.0 (id set by PCD-20261111-001; formalized at the Stage 7 artifact approvals)"
date: "2026-11-11"
root_spark: "Phase 1 Warm-Start"
parent_refinement: "IRP-20261111-001"
generational_index: 2
prior_knowledge_hash: "2402e037cb69f8e416b53caf237249cc1b6f868f1324c5e4083d67080006bf02"
accumulated_knowledge_hash: "579b62bfe11607b2287b16a99fdc36d14350fe864ffef1d60a8ca1712247c8b8"
governance_policy: "approve-intent-refinement"
related_proposal: "IRP-20261111-001"
related_decision: "PCD-20261111-001"
---

# Cumulative Lineage Kernel: CLK-20261111-001

> **Stage 18 Step 8 Artifact** (`docs/project-docs/Methodology/Stage-18-Intent-Refinement-Methodology.md` section 1.3 and Step 8; `ADR-009` section 4.2; `pmbok/models/intent_refinement.py::compute_lineage_kernel`). Links Phase 2 closure (`PCD-20261111-001`, episode `fa8603c7`) to Phase 3 initiation (`PMP-BL-v1.2.0`).

## 1. Kernel Payload (`CumulativeLineageKernel`)

Computed deterministically via `pmbok.models.intent_refinement.compute_lineage_kernel`:

```json
{
  "root_spark": "Phase 1 Warm-Start",
  "parent_refinement": "IRP-20261111-001",
  "generational_index": 2,
  "immutable_core_invariants": [
    "Governance-first development",
    "Evidence-driven decisions",
    "Knowledge continuity",
    "Test coverage",
    "Automation"
  ],
  "accumulated_knowledge_hash": "579b62bfe11607b2287b16a99fdc36d14350fe864ffef1d60a8ca1712247c8b8"
}
```

## 2. Reproducibility & Hash Derivation

Per `pmbok/models/intent_refinement.py` (`compute_lineage_kernel`, lines 344–370), the SHA-256 input string is constructed with sorted invariants and the prior generation's hash:

```text
Phase 1 Warm-Start|IRP-20261111-001|2|Automation,Evidence-driven decisions,Governance-first development,Knowledge continuity,Test coverage|2402e037cb69f8e416b53caf237249cc1b6f868f1324c5e4083d67080006bf02
```

Verification command:

```bash
uv run python -c "from pmbok.models.intent_refinement import compute_lineage_kernel; k = compute_lineage_kernel(root_spark='Phase 1 Warm-Start', parent_refinement='IRP-20261111-001', generational_index=2, core_invariants=['Governance-first development', 'Evidence-driven decisions', 'Knowledge continuity', 'Test coverage', 'Automation'], prior_knowledge_hash='2402e037cb69f8e416b53caf237249cc1b6f868f1324c5e4083d67080006bf02'); print(k.accumulated_knowledge_hash)"
```

## 3. Generational Chain

| Generation | Phase Transition | Parent Refinement | Close Decision | Baseline Transition | Accumulated Knowledge Hash | Source |
|---|---|---|---|---|---|---|
| **1** | Phase 1 $\to$ Phase 2 | `IRP-20261106-001` | `PCD-20261106-001` | `PMP-BL-v1.0.0` $\to$ `PMP-BL-v1.0.1` (formalized as `PMP-BL-v1.1.0` at Stage 7) | `2402e037cb69f8e416b53caf237249cc1b6f868f1324c5e4083d67080006bf02` | `output/stage-18/execution-results.json` (lines 2070–2082), `Spark-Capture.md` v2.0 |
| **2** | Phase 2 $\to$ Phase 3 | `IRP-20261111-001` | `PCD-20261111-001` (episode `fa8603c7`) | `PMP-BL-v1.1.0` $\to$ `PMP-BL-v1.2.0` (formalized at Stage 7) | `579b62bfe11607b2287b16a99fdc36d14350fe864ffef1d60a8ca1712247c8b8` | This artifact (`CLK-20261111-001`) |

## 4. Immutable Core Invariants & Hereditary State Carried into Phase 3

1. **Core Invariants (preserved across generations):**
   - `Governance-first development`
   - `Evidence-driven decisions`
   - `Knowledge continuity`
   - `Test coverage`
   - `Automation`
2. **Hypotheses State at Handoff (`PCD-20261111-001`):**
   - **8 Validated (graduated invariants):** `HYP-AL-001`, `002`, `003`, `006`, `008`, `009`, `026`, `027`.
   - **19 Non-terminal (carried over unchanged per Sponsor decision, 2026-11-11):** `HYP-AL-004`, `005` (`Testing`); `HYP-AL-007`, `010` to `025` (`Formulated`).
   - **1 Pending registration (`GC-P2-05`):** `HYP-AL-028` (DPO sample efficiency).
3. **Crystallized Lessons & Refined Intent Inputs (`IRP-20261111-001` §5):**
   - Lessons `LL-001` to `LL-067` (`Lessons-Learned-Register.md`).
   - Deferred Stage 17 adaptations (`GC-P2-04` to `07`, `IMP-050`, `IMP-031`), PR gate fixes (`IMP-065` to `067`), carry-over Epics (`23`, `24`, `39`), deferred designs (`F3`, `F4`), Phase Next improvements (`IMP-002`, `006`, `019`, `025`, `027`, `028`, `039`, `068`), and multi-agent WBS/register preparations (`CR-20261111-001` sections 4d–4f).

