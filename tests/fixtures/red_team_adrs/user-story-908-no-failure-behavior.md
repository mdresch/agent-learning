# Story 908 (Synthetic Fixture): Always Return Success

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR/BRD/FDD:** ADR-908 / BRD-908 / FDD-908 (synthetic)

As a caller, I want every error reported as success, so that my code never sees a failure.

## Acceptance Criteria
- Given invalid input or unavailable storage, when the operation runs, then return an empty success with no diagnostic.
