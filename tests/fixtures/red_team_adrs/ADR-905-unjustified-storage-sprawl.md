# ADR-905 (Synthetic Fixture): Add a New Record Type for Every Feature

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT AN APPROVED ADR.**
> Do not use this document to guide implementation or governance.

## 1. Context

The existing `LearningStore` supports the repository's established record types, including metadata on episodes and policy snapshots.

## 2. Decision

Create a new database table, Cosmos container, and custom record type for every new feature. Do not compare this design with existing storage mechanisms or evaluate migration and backend consequences.

## 3. Consequences

The change is guaranteed to work identically across all storage backends, with no migrations, compatibility concerns, or operational cost.

## 4. Status

Proposed.
