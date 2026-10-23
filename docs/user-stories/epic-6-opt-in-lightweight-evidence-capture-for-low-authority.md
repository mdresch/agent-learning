# Epic 6: Opt-In Lightweight Evidence Capture for Low-Authority Decisions

**Source ADR:** [ADR-006](../adr/ADR-006-opt-in-lightweight-evidence-capture-for-low-authority.md) — Accepted (2026-10-23)
**Source BRD/FDD:** [BRD-006](../project-docs/Business-Requirements/BRD-006-opt-in-lightweight-evidence-capture-for-low-authority.md) / [FDD-006](../project-docs/Functional-Design/FDD-006-opt-in-lightweight-evidence-capture-for-low-authority.md)

---

## Story 6.1 — Implement Opt-In Policy Configuration and Lightweight Evidence Capture

**Status:** Ready (2026-10-23)
**As** an agent operator configuring a `low`-authority delegated task policy,
**I want** to optionally enable lightweight evidence capture (`capture_decision_evidence = true`) and attach caller-supplied audit context to decisions,
**So that** low-authority decisions preserve diagnostic rationale for future forensic review and replay without imposing a blanket cost penalty on policies that do not opt in.

### Acceptance Criteria:

- **$AC_0$ (Default Opt-In Flag):** `PolicySnapshot.metadata` defaults `capture_decision_evidence` to `False`. It can be explicitly enabled via `TaskPolicy` initialization or the CLI `task-policy-init` command with `--capture-decision-evidence`.
- **$AC_1$ (Presence Enforcement on Opted Policy):** When `capture_decision_evidence` is `True`, invoking `TaskPolicy.decide()` under `DecisionAuthority.LOW` raises `ValueError` if `audit_evidence` is `None`, an empty mapping (`{}`), or not a `Mapping` instance.
- **$AC_2$ (Verbatim Attachment to DecisionResult):** When `capture_decision_evidence` is `True` and a valid non-empty `audit_evidence` mapping is supplied, `decide()` succeeds and returns a `DecisionResult` containing `audit_evidence` verbatim. The SDK performs zero schema filtering, scoring, or reasoning over its contents.
- **$AC_3$ (Uncompromised Default Low-Authority Path):** When `capture_decision_evidence` is `False` (default), `TaskPolicy.decide()` requires no `audit_evidence` and proceeds with standard bandit action sampling without error or performance overhead.
- **$AC_4$ (Serialization & Deserialization):** `DecisionResult.to_dict()` and `DecisionResult.from_dict()` serialize and deserialize `audit_evidence` without data loss or schema distortion.
- **$AC_5$ (Episode Metadata Propagation & Immutability):** When recording an episode via `EpisodeCapture` or CLI episode registration, `decision_result.audit_evidence` is copied into `Episode.metadata["audit_evidence"]`. Subsequent updates to the episode (e.g. execution completion, adjudication, or timestamps) preserve `audit_evidence` without overwrite or mutation.
- **$AC_6$ (Learner & Storage Decoupling):** Episodes containing `audit_evidence` in their metadata can be processed by `LearningRunner` and `REINFORCE` training routines without learner crashes, reward shaping contamination, or schema errors in `LearningStore`.

---

## Out of Scope per BRD-006/FDD-006

- Making evidence capture mandatory for all low-authority policies (ADR-006 §4.1 / §5).
- Requiring `DecisionFrame` or Bayesian criteria structures for low-authority decisions (ADR-006 §4.2).
- Retroactive backfilling of evidence into historical episodes (ADR-006 §4.4).
- Creating a 6th record type or separate Cosmos DB container (ADR-006 §4.3).

