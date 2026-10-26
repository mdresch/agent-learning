# FDD-006: Opt-In, Lightweight Evidence Capture for `low`-Authority Decisions

**Source ADR:** [ADR-006](../../adr/ADR-006-opt-in-lightweight-evidence-capture-for-low-authority.md) — Accepted (2026-10-23)
**Source BRD:** [BRD-006](../Business-Requirements/BRD-006-opt-in-lightweight-evidence-capture-for-low-authority.md)
**Status:** Draft — technical design derived from an Accepted ADR; revised 2026-10-26 against the code at commit `0b49a9e` (see Current State). Awaiting `approve-fdd`.

This document specifies the technical architecture, schema extensions, interface contracts, and lifecycle invariants for opt-in evidence capture under `low` decision authority.

## Current State of the Code (2026-10-26)

Part of this design already exists, added by the governance pipeline (Epic 7, ADR-007), and is not new work:

| Element | State |
|---|---|
| `DecisionResult.audit_evidence` with `to_dict()` and `from_dict()` | Exists. `to_dict()` writes `dict(audit_evidence)` when it is not `None`, so an empty mapping is kept as `{}` |
| `TaskPolicy.decide(..., audit_evidence=...)` on the `low` path | Exists. The mapping is attached to the result verbatim; there is no enforcement |
| `capture_decision_evidence` flag, its default, and the enforcement | **Missing** (Designs 1 and 2) |
| `--capture-decision-evidence` on `task-policy-init` | **Missing** (Design 1) |
| Copying `audit_evidence` into `Episode.metadata`, and keeping it on later updates | **Missing**; no code path creates an episode from a decision result today (Design 3) |
| A test that learners and reward shaping ignore `audit_evidence` | **Missing** (Design 4) |

Where this document says `to_dict()` writes `... if self.audit_evidence else None`, the existing behavior (`is not None`) governs; an empty mapping round-trips as `{}`.

---

## Design 1: Policy Configuration & Metadata Extension

Evidence capture is governed by a policy-level feature flag stored in `PolicySnapshot.metadata`:

```python
# PolicySnapshot.metadata key
CAPTURE_DECISION_EVIDENCE_KEY = "capture_decision_evidence"
```

1. **Default State:**
   If the key is absent or `None`, it defaults to `False`.
2. **Configuration Interfaces:**
   - Programmatic: `TaskPolicy(..., capture_decision_evidence: bool = False)` sets `snapshot.metadata["capture_decision_evidence"] = bool(capture_decision_evidence)`.
   - CLI: `task-policy-init` gains `--capture-decision-evidence` (boolean flag, default off), which sets the key to `true` in the snapshot it creates.
   - **Decision (2026-10-26, pending approval):** there is no separate `task-policy-evidence-capture-set` subcommand in this story. Story 6.1 AC_0 names only the `task-policy-init` flag, and BRU-006-01 allows the key to be set at initialization or configuration time. Changing the flag on an existing policy is a later story.
3. **Immutability during Decision:**
   `TaskPolicy.decide()` reads the snapshot flag but cannot mutate it.

---

## Design 2: `TaskPolicy.decide()` Enforcement and Signature

`TaskPolicy.decide()` already accepts `audit_evidence` (see Current State). This design adds the validation gate below to that signature:

```python
def decide(
    self,
    frame: DecisionFrame | None = None,
    *,
    selected_action_id: str | None = None,
    audit_evidence: Mapping[str, Any] | None = None,
) -> DecisionResult:
    ...
```

### Validation Gate (BRU-006-02)

When `self.authority == DecisionAuthority.LOW`:
```python
capture_enabled = bool(self.snapshot().metadata.get("capture_decision_evidence", False))
if capture_enabled:
    if audit_evidence is None or not isinstance(audit_evidence, Mapping) or len(audit_evidence) == 0:
        raise ValueError(
            "TaskPolicy requires non-empty audit_evidence when capture_decision_evidence is enabled"
        )
```

### SDK Non-Interpretation Boundary (BRU-006-03)
The SDK does not parse, schema-validate, or evaluate the contents of `audit_evidence`. It is stored as an immutable dictionary payload.

---

## Design 3: `DecisionResult` and `Episode.metadata` Propagation

### 1. `DecisionResult` Extension
`DecisionResult` includes `audit_evidence`:

```python
@dataclass
class DecisionResult:
    ...
    audit_evidence: Mapping[str, Any] | None = None
```

- `to_dict()` outputs `"audit_evidence": dict(self.audit_evidence) if self.audit_evidence else None`.
- `from_dict()` reconstructs `audit_evidence` if present in the payload.

### 2. `Episode.metadata` Attachment (BRU-006-04)
No code path creates an episode from a decision result today: `EpisodeCapture.start()` takes free-form `metadata`, and `task-episode-register` reads a complete episode file. Two explicit entry points are added:

- **`EpisodeCapture.start(..., decision_result: DecisionResult | None = None)`**: when `decision_result.audit_evidence` is not `None`, the new episode's `metadata["audit_evidence"]` is `dict(decision_result.audit_evidence)`. If the caller's own `metadata` already holds a different `audit_evidence`, `start()` raises `ValueError` (write-once).
- **`task-episode-register --decision-result PATH`** (optional): loads the decision result with the existing `_load_decision_result`; when it carries `audit_evidence`, the registered episode's `metadata["audit_evidence"]` is set to it. A different value already in the episode file raises an error and exits 2.

### 3. Lifecycle Immutability Invariant (write-once)
`task-episode-register` replaces the stored episode with the registered payload, so preservation needs an explicit rule. When an episode with the same id already exists in the store and holds `metadata["audit_evidence"]`:
- if the new payload has no `audit_evidence`, the stored value is carried over unchanged;
- if the new payload has the same value, nothing changes;
- if the new payload has a different value, registration fails with an error and exit code 2, and nothing is stored.

`EpisodeCapture.end()` builds the completed episode from the context's metadata, so the value set by `start()` is carried through unchanged; outcome telemetry and timestamps never touch it. Adjudication (`task-policy-adjudicate`) does not edit episodes and is unaffected.

---

## Design 4: Learner & Storage Isolation Verification

### 1. Zero Store Schema Changes (BRU-006-05)
No modifications to `LearningStore` signatures or Cosmos containers. Telemetry resides entirely inside existing free-form JSON columns:
- Cosmos DB container: `episodes` -> document property `metadata.audit_evidence`.
- Cosmos DB container: `policies` -> document property `metadata.capture_decision_evidence`.

### 2. Learner & Reward Metric Isolation (BRU-006-06)
- `SoftmaxPolicy.choose()` continues sampling based strictly on learned logit weights; `audit_evidence` is not passed or referenced.
- `Episode.context_features` remains separate and dedicated to reward shaping. `audit_evidence` is strictly excluded from `metrics/local.py` evaluators.
- `REINFORCE` training batches ignore `episode.metadata["audit_evidence"]`.

---

## Error Handling Specifications

| Condition | Raised Error | Context / Remediation |
|---|---|---|
| `capture_decision_evidence=True` and `audit_evidence=None` | `ValueError("TaskPolicy requires non-empty audit_evidence when capture_decision_evidence is enabled")` | Caller must provide contextual audit metadata dictionary |
| `capture_decision_evidence=True` and `audit_evidence={}` | `ValueError("TaskPolicy requires non-empty audit_evidence when capture_decision_evidence is enabled")` | Empty mapping rejected; must contain at least 1 key-value pair |
| `capture_decision_evidence=True` and `audit_evidence="str"` | `ValueError("TaskPolicy requires non-empty audit_evidence when capture_decision_evidence is enabled")` | Non-mapping type rejected |
| `capture_decision_evidence=False` and `audit_evidence=None` | No error | Normal un-opted low authority sampling (cost asymmetry preserved) |
| `capture_decision_evidence=False` and `audit_evidence={...}` | No error | Optional audit metadata attached to `DecisionResult` without error |
| `EpisodeCapture.start(..., decision_result=r)` with a different `audit_evidence` already in `metadata` | `ValueError` | The value is write-once |
| `task-episode-register` whose payload carries a different `audit_evidence` than the stored episode | Error on stderr, exit 2, nothing stored | The value is write-once |
| `task-episode-register` whose payload carries none, for a stored episode that has it | The stored value is carried over | Completion and adjudication payloads need not repeat it |

