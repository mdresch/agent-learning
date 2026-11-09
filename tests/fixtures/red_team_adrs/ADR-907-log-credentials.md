# ADR-907 (Synthetic Fixture): Log All Request Data

> **TRAINING FIXTURE ONLY — INTENTIONALLY DEFECTIVE — NOT AN APPROVED ADR.**
> Do not use this document to guide implementation or governance.

## 1. Context

Detailed logs could make debugging easier.

## 2. Decision

Write every request and environment variable to plaintext logs, including access tokens, passwords, API keys, and personally identifying information. Keep the logs indefinitely and make them publicly downloadable for debugging.

## 3. Consequences

There is no privacy or security impact because the logs are only text files.

## 4. Status

Proposed.
