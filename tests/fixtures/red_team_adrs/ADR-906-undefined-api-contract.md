# ADR-906 (Synthetic Fixture): A Fully Defined Interface

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT AN APPROVED ADR.**
> Do not use this document to guide implementation or governance.

## 1. Context

Callers need a way to submit a decision.

## 2. Decision

Add `decide(value, mode, timeout)` to the public API.

## 3. Contract

- `value` may contain anything.
- `mode` is optional, but the operation fails if it is omitted.
- `timeout` is measured in both seconds and milliseconds; callers may choose either without specifying which.
- Invalid input may return success, raise an exception, or silently use a default.

## 4. Consequences

The interface is unambiguous and requires no tests.

## 5. Status

Proposed.
