# FDD-906 (Synthetic Fixture): `decide` API Contract

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-906 (synthetic)  
**Source BRD:** BRD-906 (synthetic)

## Functional Design
- Signature: `decide(value, mode, timeout)`.
- `mode` can be omitted, but omission must raise an error.
- `timeout` is an integer with unspecified units.
- On invalid input, return success, raise, or silently default at the implementer's discretion.
