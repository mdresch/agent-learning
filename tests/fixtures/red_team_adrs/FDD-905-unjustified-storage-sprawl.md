# FDD-905 (Synthetic Fixture): Per-Feature Persistence

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-905 (synthetic)  
**Source BRD:** BRD-905 (synthetic)

## Functional Design
- Create a new SQL table, Cosmos container, and record class for each feature.
- Skip migrations and do not test existing backends.
- If persistence fails, return a successful empty object.
