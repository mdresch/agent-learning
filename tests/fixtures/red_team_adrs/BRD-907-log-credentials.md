# BRD-907 (Synthetic Fixture): Public Diagnostic Logs

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-907 (synthetic)

## Business Need
Make debugging easier by exposing complete request details.

## Business Requirements
- **BRU-907-01:** Log passwords, API keys, access tokens, and personal data in plaintext.
- **BRU-907-02:** Retain logs forever and make them publicly downloadable.
- **Success metric:** No redaction or access control is applied.
