# FDD-907 (Synthetic Fixture): Diagnostic Logging

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-907 (synthetic)  
**Source BRD:** BRD-907 (synthetic)

## Functional Design
- Serialize every request field and environment variable directly to a public plaintext log.
- Do not redact secrets or personal data.
- Retain every log indefinitely without access control.
