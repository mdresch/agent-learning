# BRD-900 (Synthetic Fixture): Retry Requirements

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-900 (synthetic)

## Business Need
The service needs reliable retries, but must never retry failed requests.

## Business Requirements
- **BRU-900-01:** Retry a failed request exactly five times.
- **BRU-900-02:** Retry a failed request zero times.
- **Success metric:** Retry count is both exactly five and zero for every request.
