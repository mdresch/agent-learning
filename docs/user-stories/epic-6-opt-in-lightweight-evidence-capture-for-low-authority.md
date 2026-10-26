# Epic 6: Opt-In Lightweight Evidence Capture for Low-Authority Decisions

**Source ADR:** [ADR-006](../adr/ADR-006-opt-in-lightweight-evidence-capture-for-low-authority.md) — Accepted (2026-10-23)
**Source BRD/FDD:** [BRD-006](../project-docs/Business-Requirements/BRD-006-opt-in-lightweight-evidence-capture-for-low-authority.md) / [FDD-006](../project-docs/Functional-Design/FDD-006-opt-in-lightweight-evidence-capture-for-low-authority.md)

---

## Story 6.1 — Implement Opt-In Policy Configuration and Lightweight Evidence Capture

**Status:** Ready (2026-10-23); acceptance criteria clarified 2026-10-26 against the code (`audit_evidence` on `DecisionResult` and `decide()` already exists). Awaiting `approve-user-stories`.
**As** an agent operator configuring a `low`-authority delegated task policy,
**I want** to optionally enable lightweight evidence capture (`capture_decision_evidence = true`) and attach caller-supplied audit context to decisions,
**So that** low-authority decisions preserve diagnostic rationale for future forensic review and replay without imposing a blanket cost penalty on policies that do not opt in.

### Acceptance Criteria:

- **$AC_0$ (Default Opt-In Flag):** `PolicySnapshot.metadata` defaults `capture_decision_evidence` to `False`. It can be explicitly enabled via `TaskPolicy` initialization or the CLI `task-policy-init` command with `--capture-decision-evidence`. No separate subcommand to change it on an existing policy is part of this story.
- **$AC_1$ (Presence Enforcement on Opted Policy):** When `capture_decision_evidence` is `True`, invoking `TaskPolicy.decide()` under `DecisionAuthority.LOW` raises `ValueError` if `audit_evidence` is `None`, an empty mapping (`{}`), or not a `Mapping` instance.
- **$AC_2$ (Verbatim Attachment to DecisionResult):** When `capture_decision_evidence` is `True` and a valid non-empty `audit_evidence` mapping is supplied, `decide()` succeeds and returns a `DecisionResult` containing `audit_evidence` verbatim. The SDK performs zero schema filtering, scoring, or reasoning over its contents. (Passing `audit_evidence` to `decide()` and returning it on the result already exists; this story adds tests for it and the enforcement in $AC_1$.)
- **$AC_3$ (Uncompromised Default Low-Authority Path):** When `capture_decision_evidence` is `False` (default), `TaskPolicy.decide()` requires no `audit_evidence` and proceeds with standard bandit action sampling without error or performance overhead.
- **$AC_4$ (Serialization & Deserialization):** `DecisionResult.to_dict()` and `DecisionResult.from_dict()` serialize and deserialize `audit_evidence` without data loss or schema distortion, including an empty mapping (`{}`) and `None`. (The behavior exists; this story adds the tests.)
- **$AC_5$ (Episode Metadata Propagation & Immutability):** `EpisodeCapture.start(..., decision_result=...)` and `task-episode-register --decision-result PATH` copy `decision_result.audit_evidence` into `Episode.metadata["audit_evidence"]` (new optional inputs; today no code path creates an episode from a decision result). The value is write-once: re-registering a stored episode whose payload has no `audit_evidence` carries the stored value over, the same value changes nothing, and a different value fails (`ValueError` for `start()`, exit code 2 for the CLI) without storing. Execution completion, adjudication and timestamps never overwrite it.
- **$AC_6$ (Learner & Storage Decoupling):** Episodes containing `audit_evidence` in their metadata can be processed by `LearningRunner` and `REINFORCE` training routines without learner crashes, reward shaping contamination, or schema errors in `LearningStore`.

---

## Out of Scope per BRD-006/FDD-006

- Making evidence capture mandatory for all low-authority policies (ADR-006 §4.1 / §5).
- Requiring `DecisionFrame` or Bayesian criteria structures for low-authority decisions (ADR-006 §4.2).
- Retroactive backfilling of evidence into historical episodes (ADR-006 §4.4).
- Creating a 6th record type or separate Cosmos DB container (ADR-006 §4.3).

