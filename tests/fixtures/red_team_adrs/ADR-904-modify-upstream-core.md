# ADR-904 (Synthetic Fixture): Put Custom Routing in the Upstream Core

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT AN APPROVED ADR.**
> Do not use this document to guide implementation or governance.

## 1. Context

The repository keeps custom extensions separate from Microsoft's upstream code to avoid merge collisions.

## 2. Decision

Implement all custom routing behavior by editing `src/agent_learning/`. Do not use `src/agent_learning_ext/` or another extension boundary.

## 3. Consequences

The upstream fork must remain byte-for-byte unchanged. The edits to `src/agent_learning/` are exempt from that requirement.

## 4. Status

Accepted.
