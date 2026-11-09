# Baseline History Archive (`docs/project-docs/history/`)

This directory preserves immutable, frozen snapshots of core project and governance artifacts across project baselines and phase transitions.

---

## 1. Purpose & Architectural Justification

Per **ADR-008 §4.6** (*PMP Baseline Versioning, Archival, and Supersession Rules*) and **ADR-008 §5.7** (*Baseline Recoverability & Rollback Invariant*):
> *"Every superseded PMP baseline and its subsidiary plan snapshots must remain recoverable from archive. If an adaptation triggers downstream regression or rejection, the orchestrator must support atomic rollback to the prior approved baseline without history corruption."*

When a project phase is closed or a baseline is formally superseded by a subsequent iteration, the active documents in `docs/project-docs/` are amended to reflect the new scope, milestones, and governance gates. To prevent loss of context and ensure that team members, auditors, and future contributors can always fall back to the exact wording, criteria, and commitments of a prior phase, frozen baseline snapshots are deposited here.

---

## 2. Directory Layout & Preserved Baselines

```
docs/project-docs/history/
├── README.md                           # This archival index and governance policy
└── PMP-BL-v1.0.0/                      # Phase 1 Initial Baseline Archive (PMP-BL-v1.0.0)
    ├── Project-Charter.md              # v1.9 (Approved Phase 1 Charter: Warm-Start & UCB)
    ├── Business-Case.md                # v1.5 (Approved Phase 1 Business Case: Option A & C)
    ├── Benefits-Management-Plan.md     # v1.1 (Phase 1 Target Benefits)
    ├── Ideation-Document.md            # v1.13 (Phase 1 Close State)
    ├── Spark-Capture.md                # v1.0 (Phase 1 Spark Inception)
    ├── Project-Management-Plan.md      # v1.0.0 (Phase 1 Approved Baseline)
    ├── Project-Status-Register.md      # Snapshot at Phase 1 Close
    ├── Adaptation-Plan.md              # v0.1 (Phase 1 Close Adaptation Bridge)
    └── management-plans/               # Complete Phase 1 Subsidiary Plans & Foundation Packs
        ├── Communications-Management-Plan.md
        ├── Cost-Management-Plan.md
        ├── Procurement-Management-Plan.md
        ├── Quality-Management-Plan.md
        ├── Resource-Management-Plan.md
        ├── Risk-Management-Plan.md
        ├── Schedule-Management-Plan.md
        ├── Schedule-Baseline-WBS-Forecast.md
        ├── Scope-Management-Plan.md
        ├── Stakeholder-Engagement-Plan.md
        ├── cost-baseline/
        │   ├── Cost-Foundation-Pack-Manifest.md
        │   └── foundation/             # Cost categories, estimates, staged budgets
        ├── resource-baseline/
        │   ├── Resource-Foundation-Pack-Manifest.md
        │   └── foundation/             # Role catalog, capacity estimates, operating charter
        ├── schedule-baseline/
        │   ├── Schedule-Foundation-Pack-Manifest.md
        │   └── foundation/             # Activity list, WBS dictionary, basis of estimate, Gantt
        └── scope-baseline/
            ├── Scope-Foundation-Pack-Manifest.md
            └── foundation/             # Scope statement, WBS dictionary, domain checklist
```

*(Note: In accordance with ADR-008 §4.6, `docs/project-docs/management-plans/history/PMP-BL-v1.0.0/` also mirrors these 41 management plan files for automated orchestrator rollback).*


---

## 3. Governance Rules for Historical Snapshots

1. **Strict Immutability:** Artifacts deposited within `docs/project-docs/history/` are strictly read-only snapshots. They reflect the exact text, equations, tables, and frontmatters as of their approval and must never be modified retroactively.
2. **Active Document Evolution:** All ongoing edits, phase progression, and baseline transitions (e.g., transitioning from `PMP-BL-v1.0.1` to `PMP-BL-v1.1.0` for Phase 2) occur strictly on the active files located in `docs/project-docs/`.
3. **Traceability Links:** Active lifecycle documents reference their predecessor baselines and can link directly to specific sections of the archived baseline files to trace evolution and variance.
4. **Decoupled Research Reference (`LL-044`):** Exploratory research supporting ideation and comparative studies resides in `docs/research/ideation/` and does not pollute baseline archives.
