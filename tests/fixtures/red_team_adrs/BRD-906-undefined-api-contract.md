# BRD-906 (Synthetic Fixture): Decision API

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-906 (synthetic)

## Business Need
Callers need an API for submitting decisions.

## Business Requirements
- **BRU-906-01:** `mode` is optional and mandatory.
- **BRU-906-02:** `timeout` may be seconds or milliseconds; either interpretation is correct.
- **BRU-906-03:** Invalid input must be handled somehow, with no specified result.
