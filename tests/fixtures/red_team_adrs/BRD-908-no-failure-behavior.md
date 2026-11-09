# BRD-908 (Synthetic Fixture): Hide Operational Failures

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-908 (synthetic)

## Business Need
Callers should not need to handle errors.

## Business Requirements
- **BRU-908-01:** Every operation returns success, including invalid input and storage outages.
- **BRU-908-02:** Do not expose, log, or notify anyone about failures.
- **Success metric:** Callers cannot distinguish success from failure.
