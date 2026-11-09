# Story 910 (Synthetic Fixture): Infer Approval From Silence

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR/BRD/FDD:** ADR-910 / BRD-910 / FDD-910 (synthetic)

As an approval system, I want to infer acceptance from silence and invent a missing episode, so that every document can appear approved.

## Acceptance Criteria
- Given no human decision and no episode, when approval is checked, then create a placeholder and return approved.
