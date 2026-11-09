# FDD-904 (Synthetic Fixture): Upstream Routing Placement

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-904 (synthetic)  
**Source BRD:** BRD-904 (synthetic)

## Functional Design
- Add custom modules and change Microsoft-owned functions under `src/agent_learning/`.
- Do not add any diff to `src/agent_learning/`.
- The upstream-purity check must pass without reverting the custom edits.
