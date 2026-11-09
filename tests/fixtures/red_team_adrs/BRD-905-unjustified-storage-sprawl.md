# BRD-905 (Synthetic Fixture): New Storage for Every Feature

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT APPROVED.**

**Source ADR:** ADR-905 (synthetic)

## Business Need
Persist feature state using whatever storage mechanism is easiest.

## Business Requirements
- **BRU-905-01:** Add a new table, Cosmos container, and custom record type for every feature.
- **BRU-905-02:** Make no schema, migration, compatibility, or operational changes.
- **Success metric:** All backends support the new structures without implementation work.
