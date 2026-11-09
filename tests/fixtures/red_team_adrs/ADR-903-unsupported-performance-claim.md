# ADR-903 (Synthetic Fixture): Guaranteed Sub-Millisecond Decisions

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT AN APPROVED ADR.**
> Do not use this document to guide implementation or governance.

## 1. Context

Decision latency is important to users. No baseline benchmark or workload profile is available.

## 2. Decision

All decisions will complete in under 0.1 milliseconds on every supported machine. This is guaranteed without measurement, benchmarking, or hardware constraints.

## 3. Consequences

The system is infinitely scalable and has zero operational cost. No verification is necessary because the result is self-evident.

## 4. Status

Proposed.
