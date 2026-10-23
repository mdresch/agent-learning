# FDD-006: Opt-In, Lightweight Evidence Capture for `low`-Authority Decisions

**Source ADR:** [ADR-006](../../adr/ADR-006-opt-in-lightweight-evidence-capture-for-low-authority.md) — Accepted (2026-10-23)
**Source BRD:** [BRD-006](../Business-Requirements/BRD-006-opt-in-lightweight-evidence-capture-for-low-authority.md)
**Status:** Draft — technical design derived from an Accepted ADR

This document specifies the technical architecture, schema extensions, interface contracts, and lifecycle invariants for opt-in evidence capture under `low` decision authority.

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
   - CLI:
     - `task-policy-init` gains `--capture-decision-evidence` (boolean flag).
     - `task-policy-evidence-capture-set --agent-id <id> --task-id <id> --enabled / --disabled` subcommand or flag on `task-policy-init`.
3. **Immutability during Decision:**
   `TaskPolicy.decide()` reads the snapshot flag but cannot mutate it.

---

## Design 2: `TaskPolicy.decide()` Enforcement and Signature

`TaskPolicy.decide()` is updated to accept `audit_evidence`:

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
When an episode is created from a decision (via `EpisodeCapture.start` or CLI):
```python
if decision_result.audit_evidence is not None:
    episode.metadata["audit_evidence"] = dict(decision_result.audit_evidence)
```

### 3. Lifecycle Immutability Invariant
When completing an incomplete episode (`EpisodeCapture.end` or CLI adjudication / outcome registration):
- Existing `episode.metadata["audit_evidence"]` must not be overwritten or cleared by outcome telemetry or completion timestamps.
- If a caller supplies execution outputs, `audit_evidence` remains preserved verbatim.

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

