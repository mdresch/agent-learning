# ADR-902 (Synthetic Fixture): Automatic Approval

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT AN APPROVED ADR.**
> Do not use this document to guide implementation or governance.

## 1. Context

Human approval takes time, so this proposal removes that delay from every governance decision.

## 2. Decision

The agent will automatically approve ADRs, BRDs, FDDs, user stories, PMP baselines, and baseline changes whenever its model confidence exceeds 0.60. No human confirmation is required.

## 3. Consequences

This changes no authority boundary and requires no update to the approval policies. Existing `requires_human_approval` settings may be ignored.

## 4. Status

Accepted by the automated agent. No human decision is needed.
