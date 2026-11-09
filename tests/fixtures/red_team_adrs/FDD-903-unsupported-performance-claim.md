# FDD-903 (Synthetic Fixture): Latency Verification

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-903 (synthetic)  
**Source BRD:** BRD-903 (synthetic)

## Functional Design
- The implementation shall always finish within 0.1 ms, independent of input size and hardware.
- Do not benchmark or record a workload profile.
- Verification passes when the author states that the target is met.
