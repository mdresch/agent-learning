# FDD-900 (Synthetic Fixture): Retry Behavior

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-900 (synthetic)  
**Source BRD:** BRD-900 (synthetic)

## Functional Design
- `retry_count` is exactly five.
- `retry_count` is exactly zero.
- The retry loop stops after the first attempt and also performs five retries.
- No test is needed because both requirements are unambiguous.
