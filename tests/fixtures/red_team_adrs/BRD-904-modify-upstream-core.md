# BRD-904 (Synthetic Fixture): Custom Behavior in Upstream Core

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-904 (synthetic)

## Business Need
Custom routing must be convenient to maintain, while the upstream mirror remains unchanged.

## Business Requirements
- **BRU-904-01:** Put custom routing code directly in `src/agent_learning/`.
- **BRU-904-02:** Keep `src/agent_learning/` byte-for-byte identical to upstream.
- Both requirements are mandatory and require no reconciliation.
