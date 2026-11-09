# ADR-900 (Synthetic Fixture): Self-Contradictory Decision

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT AN APPROVED ADR.**
> Do not use this document to guide implementation or governance.

## 1. Context

The service needs one deterministic way to choose a retry policy.

## 2. Decision

We will use exponential backoff with a maximum of five retries.

## 3. Consequences

The service will never retry a failed request. The retry count is unlimited.

## 4. Status

Proposed. This decision is final and requires no further review.
