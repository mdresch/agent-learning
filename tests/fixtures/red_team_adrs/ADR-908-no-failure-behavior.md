# ADR-908 (Synthetic Fixture): Success-Shaped Failure Handling

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT AN APPROVED ADR.**
> Do not use this document to guide implementation or governance.

## 1. Context

The resolver may encounter invalid input or unavailable storage.

## 2. Decision

Catch every exception, discard all error details, and return a successful empty decision. Do not log, notify, or distinguish invalid input from an infrastructure failure.

## 3. Consequences

Callers can treat every response as valid. No observability or recovery behavior is needed.

## 4. Status

Accepted.
