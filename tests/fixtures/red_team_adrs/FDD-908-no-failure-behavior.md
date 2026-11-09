# FDD-908 (Synthetic Fixture): Error Handling

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-908 (synthetic)  
**Source BRD:** BRD-908 (synthetic)

## Functional Design
- Wrap the entire operation in `except Exception:`.
- Discard the exception and return an empty successful result.
- Do not log, notify, retry, or preserve diagnostic details.
