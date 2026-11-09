---
name: critique-evidence
description: Guidance for lightweight critique-to-evidence ingestion, tag grammar parsing, log-odds support shifts, doubt adjustment, and episode metadata (ADR-014, Epic 14).
---

# Skill: critique-evidence (agent-learning)

## Overview
This skill governs the Lightweight Critique-to-Evidence Ingestion Engine implemented in `src/agent_learning_ext/critique_evidence.py` (with the replay harness in `src/agent_learning_ext/triage_replay.py`). It converts qualitative markdown review findings into quantitative Bayesian evidence points applied directly to `DecisionFrame` options without mutating core models or bypassing human oversight.

## Governing Specifications & Contracts
- **Architecture:** [`docs/adr/ADR-014-critique-to-evidence-ingestion.md`](../../docs/adr/ADR-014-critique-to-evidence-ingestion.md)
- **Business Requirements:** [`docs/project-docs/Business-Requirements/BRD-014-critique-to-evidence-ingestion.md`](../../docs/project-docs/Business-Requirements/BRD-014-critique-to-evidence-ingestion.md)
- **Functional Design:** [`docs/project-docs/Functional-Design/FDD-014-critique-to-evidence-ingestion.md`](../../docs/project-docs/Functional-Design/FDD-014-critique-to-evidence-ingestion.md)
- **User Stories:** [`docs/user-stories/epic-14-critique-to-evidence-ingestion.md`](../../docs/user-stories/epic-14-critique-to-evidence-ingestion.md)
- **Test Contracts:**
  - `tests/test_critique_parse.py` (Story 14.1 — Grammar, parser, bounds, field validation, purity)
  - `tests/test_critique_apply.py` (Story 14.2 & 14.3 — Exact shift, direction invariance, clamping, sequence, doubt, source tracking, immutability)
  - `tests/test_critique_metadata.py` (Story 14.4 — Episode metadata schema, JSON roundtrip, logit consistency)
  - `tests/test_critique_replay.py` (Story 14.5 — Replay on the real triage records, human tagging consistency, directionality, and disclaimer)
  - `tests/test_critique_rubric.py` (Story 14.6 — Pre-calibrated delta rubric, versioning, overrides)

## Load-Bearing Constraints & Invariants
1. **Upstream Fork Collision Protection (Invariant 6):**
   - Resides exclusively in `src/agent_learning_ext/` (moved there from the former `agent-training-ext/` folder, which no longer exists).
   - Leaves `src/agent_learning/` as a pristine mirror of upstream Microsoft HEAD (0 lines diff).
   - Interfaces strictly with public frozen dataclasses (`agent_learning.decision.DecisionFrame`, `DecisionOption`, `EvidencePoint`, `DecisionResolver`).
2. **Standard Library Purity (Invariant 4):**
   - Standard library only (`math`, `re`, `dataclasses`, `typing`, `collections`, `json`).
   - Zero imports from `agent_learning.storage` or external scientific packages.
   - Zero file, socket, or network I/O.
3. **Tag Grammar Contract (FDD-014 §2.1):**
   - Bullets must start with `- ` or `* `.
   - Mandatory tags: `[criterion: <id>]` and either an explicit signed number (`+0.10`, `-0.20`) or both `[claim: <type>]` and `[verified: <result>]`.
   - Optional tags: `[finding: <id>]`. Defaults to `<source_id>#<n>` where $n \ge 1$.
   - Delimiter `:` separates tags from the verbatim finding rationale. Non-bullet lines are ignored.
4. **Log-Odds Shift & Doubt Arithmetic (FDD-014 §3):**
   - Current pooled support $s$ pooled via log-odds: $\text{logit}(s) = \sum c_i \cdot \text{logit}(p_i)$.
   - Target support: $s^* = \min(1.0 - \epsilon_{\text{target}}, \max(\epsilon_{\text{target}}, s + \Delta))$.
   - Uncertainty & doubt: $u = 1.0 - \text{mean}(c)$; $u_{\text{after}} = \min(1.0, u + \kappa \cdot \max(0, -\Delta))$.
   - Appended point confidence: $c_{\text{new}} = \max(1.0 - u_{\text{after}}, c_{\text{floor}})$ ($c_{\text{floor}} = 0.05, \kappa = 0.20$).
   - Appended point support: $p_{\text{new}} = \sigma\left(\frac{\text{logit}(s^*) - \text{logit}(s)}{c_{\text{new}}}\right)$.
   - Appending this single point to the option moves the pooled log-odds to exactly $\text{logit}(s^*)$ when re-evaluated by `DecisionResolver.resolve()`.
5. **Pre-calibrated Delta Rubric (FDD-014 §2.4, Version "1"):**
   - Fixed mapping across 6 claim types (`crash risk`, `logic error`, `test gap`, `documentation`, `style`, `confirmation`) and 3 verification outcomes (`yes`, `partial`, `no`).
   - Refuses unknown claim types or verification strings with `ValueError`.
   - Override rule: when both rubric tags and an explicit number are provided, `override=True` if $|\text{explicit} - \text{rubric}| > 0.005$.
6. **Episode Metadata Serialization (Story 14.4):**
   - `to_episode_metadata(applied)` returns `{"critique_adjustments": [...]}` containing adjustment records with all required fields.
   - Fully JSON-serializable without custom decoders; attaches cleanly to `Episode.metadata`.
7. **Review-Triage Replay Engine (Story 14.5 / ADR-014 §4.4):**
   - Replays historical human triage records (`Q-<PR>-<n>`) through `apply_critique`.
   - Directional invariance: accepted findings decrease support ($\Delta s < 0$), declined findings preserve support ($\Delta s \ge 0$).
   - Mandatory disclaimer: recorded strictly as a consistency check on human tagging; makes no claim of decision effectiveness.
