---
artifact_id: scope-foundation-validate-scope
parent_plan_id: scope-management
baseline_id: PMP-BL-v1.0.0
route: foundation_artifact
governance_policy: approve-subsidiary-plan
substage: "6.A-4"
version: "1.0.0"
owner_role: "Project Manager"
depends_on: []
approval_status: approved
pmbok_process: "Validate Scope"
---

# Scope Foundation — Validate Scope (`PMP-BL-v1.0.0`)

PMBOK 8 **Scope Performance Domain** §2.2 — **Validate Scope**. Acceptance protocol and traceability for baseline `PMP-BL-v1.0.0`.

## Definition of Done (work package acceptance)

No deliverable enters the repository baseline until:

| Gate | Requirement |
| --- | --- |
| **Contract** | $AC_n$ formalized in `tests/test_*.py` |
| **RED first** | Contract tests fail before implementation |
| **Pure code** | Stdlib-first; no undeclared dependencies |
| **Green suite** | Full test collection and pass (Epic 34 decommission may block until resolved) |
| **Audit** | Story id and commit in `implementation-log.md` |
| **Review** | PR review complete; findings resolved |

## Requirements traceability (RTM convention)

Standalone RTM file is **deferred**; traceability is structural:

1. **Epic** — `docs/user-stories/epic-NN-*.md` links ADR, BRD, FDD, `PMP-BL-v1.0.0`.
2. **Story** — `## Story N.M` holds $AC_n$; tests named in epic or story.
3. **Work package** — Closing commit in `implementation-log.md`.
4. **Governance** — [docs/adr/README.md](../../../../adr/README.md) (Accepted ADR-001–038).

## Validation vs control

* **Validate Scope** confirms deliverables meet DoD and story contracts (close-out of a WBS row).
* **Monitor and Control Scope** compares ongoing requests to the baseline (see [Scope-Monitor-Control-Scope.md](Scope-Monitor-Control-Scope.md)).

Epic headers must cite this baseline id after Scope subsidiary approval at v1.2+.
