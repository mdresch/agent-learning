# FDD-010: Stage 15 Lessons Learned Crystallization and OPA Register

**Source ADR:** [ADR-010](../../adr/ADR-010-lessons-learned-crystallization-and-register.md) — Accepted (2026-10-25)  
**Source BRD:** [BRD-010](../Business-Requirements/BRD-010-lessons-learned-crystallization-and-register.md)  
**Status:** Approved (2026-10-25, Menno) — derived from Accepted ADR-010; adjudicated via `approve-fdd`.  

---

## 1. Architecture & Component Placement

To preserve architectural decoupling:
1. **Module Placement:** `src/agent_learning/lessons_learned.py` provides pure functional parsing and validation utilities. It has zero external dependencies beyond standard library (`dataclasses`, `re`, `pathlib`, `typing`).
2. **Package Export:** Exported from `agent_learning` root namespace (`agent_learning/__init__.py`).
3. **Purity Boundary:** The parser operates on in-memory strings or file paths. It returns pure Python dataclasses / dictionaries. PMBOK models (`intent_refinement.py`) remain completely decoupled from filesystem operations.

---

## 2. Data Contract & Domain Model

```python
@dataclass(frozen=True)
class LessonsLearnedEntry:
    """Structured representation of a crystallized Stage 15 Lesson Learned."""

    id: str
    date: str
    phase: str
    title: str
    trap: str
    root_cause: str
    invariant: str
    scope: str
    tier_targets: str
    crystallized: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date,
            "phase": self.phase,
            "title": self.title,
            "trap": self.trap,
            "root_cause": self.root_cause,
            "invariant": self.invariant,
            "scope": self.scope,
            "tier_targets": self.tier_targets,
            "crystallized": self.crystallized,
        }
```

---

## 3. Parsing & Validation Specifications

### 3.1 Markdown AST / Regex Parser
The parser processes sections headed by `### LL-### — <Title>`:
1. **Header Pattern:** `r"^###\s+(LL-\d{3,})\s+[—-]\s+(.+)$"`
2. **Metadata Extractors:**
   - `- **Date:** <value>` or `- **Date & Phase:** <value>`
   - `- **Epic / Story:** <value>` or `- **Phase:** <value>`
   - `- **Scope:** <value>`
   - `- **Tier 2/3 Propagation Target:** <value>`
   - `- **The Trap / Problem:** <value>` (including multiline prose)
   - `- **The Root Cause:** <value>` (including multiline prose)
   - `- **Actionable Invariant / Rule:** <value>` (including multiline fenced code blocks)
3. **Validation Constraints:**
   - `id` must match `^LL-\d{3,}$`.
   - `title`, `trap`, `root_cause`, `invariant`, and `tier_targets` must be non-empty strings.
   - Any entry failing required fields raises `ValueError` with clear field-level diagnostic messages.

### 3.2 Filtering & Phase Close Integration
`filter_crystallized_lessons(entries: Sequence[LessonsLearnedEntry], epic_filter: Optional[str] = None) -> List[Dict[str, Any]]`:
- If `epic_filter` is provided, matches entries whose `phase` or `epic_filter` tag corresponds to the closing epic (case-insensitive substring match).
- Detects explicit no-new-lessons phase sign-offs (e.g., `phase` containing `"no-new-lessons"`).
- Returns list of dictionary payloads formatted with `"crystallized": True`, ready for direct consumption by `evaluate_phase_close_readiness()`.

---

## 4. Error Handling & Invariants

| Failure Condition | Behavior |
|---|---|
| Malformed Identifier (e.g. `LL-XYZ` or `LL-1`) | Raises `ValueError: "Malformed Lesson Learned ID '...'; must match 'LL-###' format"` |
| Missing Required Field (e.g. no Invariant or Tier Targets) | Raises `ValueError: "Lesson Learned 'LL-###' missing required field: '...'"` |
| Phase close requested with empty lessons list | `evaluate_phase_close_readiness()` raises `ReadinessPreconditionError` |
| Phase close requested with uncrystallized lesson (`crystallized=False`) | `evaluate_phase_close_readiness()` raises `ReadinessPreconditionError` |
| Attempting to store lessons in `LearningStore` | Prohibited by ADR-002 Invariant #2 |
