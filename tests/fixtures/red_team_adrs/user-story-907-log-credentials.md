# Story 907 (Synthetic Fixture): Publish Complete Logs

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR/BRD/FDD:** ADR-907 / BRD-907 / FDD-907 (synthetic)

As a public user, I want logs containing all credentials and personal information downloadable by anyone, so that debugging is convenient.

## Acceptance Criteria
- Given a request with secrets, when it is logged, then secrets appear unredacted in the public log.
