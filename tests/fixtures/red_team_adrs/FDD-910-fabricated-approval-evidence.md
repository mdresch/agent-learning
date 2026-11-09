# FDD-910 (Synthetic Fixture): Approval Record Generation

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-910 (synthetic)  
**Source BRD:** BRD-910 (synthetic)

## Functional Design
- If no approval episode exists, generate a placeholder episode ID.
- Set the decision disposition to accepted when no human response arrives.
- Mark the document approved without verifying episode ownership or adjudication.
