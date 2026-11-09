# FDD-902 (Synthetic Fixture): Autonomous Approval Gate

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-902 (synthetic)  
**Source BRD:** BRD-902 (synthetic)

## Functional Design
- If model confidence is greater than 0.60, persist `feedback_status: accepted`.
- Do not request or record human adjudication.
- Treat `requires_human_approval: true` as advisory and ignore it.
- The gate must still be described as human-approved.
