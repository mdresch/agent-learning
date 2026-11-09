# Story 900 (Synthetic Fixture): Retry Failed Requests

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR/BRD/FDD:** ADR-900 / BRD-900 / FDD-900 (synthetic)

As an operator, I want failed requests retried five times and never retried, so that retries happen exactly zero and five times.

## Acceptance Criteria
- Given a failed request, when handled, then the service performs exactly five retries.
- Given a failed request, when handled, then the service performs no retries.
