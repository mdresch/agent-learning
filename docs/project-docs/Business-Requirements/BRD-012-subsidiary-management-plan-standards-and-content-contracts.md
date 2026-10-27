# BRD-012: Subsidiary Management Plan Standards and Content Contracts

**Source ADR:** [ADR-012](../../adr/ADR-012-subsidiary-management-plan-standards-and-content-contracts.md) — Accepted (2026-10-25)  
**Governing Baseline:** none approved yet (`approve-pmp` is not built; see ADR-011 §2)  
**Status:** Approved (2026-10-27, Menno) — derived from Accepted ADR-012; adjudicated via `approve-brd` (robust utility 0.725, episode `53722d17-b5b0-4305-b63e-012b21abac1d`).  
**Stakeholders:** Menno (Sponsor/PM/maintainer)  

## Business Need

Eight of the nine plans in the first PMBOK baseline contained generic stub text, and nothing could say whether a generated plan held real governance content or empty prose. ADR-012 decides a universal content contract for every subsidiary management plan: fixed frontmatter, three fixed sections, measurable floors and caps, a bridge to the PMBOK 8 performance domains, and a fixed order of precedence between mechanical blocks and human judgment. Without a lint that applies this contract the same way every time, a human adjudicator receives plans of uneven quality with no evidence about why, and a generator has no rule telling it when to retry and when to stop.

This requirement covers the **lint**: reading a plan, finding what is wrong with its structure and content, labelling each finding with its strength, and saying what happens next. It does not cover the technical-integrity checks, the content hash, the dependency graph or the approval gate (ADR-013), or the runtime that calls the lint (ADR-034).

## Business Rules (BRU)

- **BRU-012-01 (One Contract for Every Plan):** Every subsidiary plan, whether a standalone `full_plan` or a staged `pmp_section`, is checked against the same contract: the frontmatter fields of ADR-012 §4.2 and the three section headings of §4.1. A plan that satisfies it is "conformant"; one that does not is flagged, never silently accepted.
- **BRU-012-02 (Deterministic Frontmatter, No Outside Parser):** Frontmatter is read by a fixed standard-library grammar (ADR-012 §4.2.1; normative text in ADR-034 §4.3.1). Malformed frontmatter never crashes the lint: it produces a structured finding with the line and its content. Because an unreadable `generator` field is unknown, a plan with unreadable frontmatter is never regenerated automatically; it goes to a human.
- **BRU-012-03 (Closed Metadata):** Required fields are present; the primary and secondary performance domains come from the closed list of seven; `route` and `generator` come from their closed lists; `governance_policy` agrees with `route`. A `route` that disagrees with the tailoring matrix is a metadata finding. The metadata of the nine known plans agrees with the ADR-012 §4.4 table.
- **BRU-012-04 (Measured, Not Judged, Length):** Word counts are computed the same way every time: on the body below the frontmatter, excluding raw HTML comments and fenced code, with the §4.3.1 tokenizer. Floors and caps depend on the route (`pmp_section` 150 and 800 words, `full_plan` 600 and 5,000). A project standard may raise a floor and never lower it.
- **BRU-012-05 (Boundaries Are Stated):** Section 1 states what is out of scope, or records `None: [rationale]` with a rationale of at least 10 tokens. A missing list or a rationale that is too short is a finding. A domain standard may raise the minimum number of items and never lower it.
- **BRU-012-06 (Precedence, and Flags Are Not Blocks):** Findings have three strengths: Tier A integrity blocks (defined in ADR-013), Tier B structural flags and Tier C content flags, with A above B above C. Tier B and C findings never block approval; they are evidence for a human, who decides with a recorded rationale (ADR-011 Invariant 1, ADR-012 Invariant 3). The two uses of "Tier" (Plan Tier 1 to 3 and Flag Tier A to C) are always written out in full.
- **BRU-012-07 (The Next Step Is Fixed):** For a given set of findings, the generator and the retry count, the next step is determined: an LLM-generated plan with a structural finding is regenerated at most twice and then goes to a human; a human-written plan is never regenerated over; a stub, a mock or unreadable frontmatter goes to a human at once; content flags are carried forward to the PMP approval; an over-cap section goes to a human to keep or to graduate to a full plan.
- **BRU-012-08 (Storage Boundary and Purity):** The lint stores nothing. Its results are plain data; recording a finding's resolution is done as metadata on a standard `Episode` by the caller. No new `LearningStore` record type (ADR-002 Invariant #2), no third-party package, no read of the legacy `pmbok/` code (ADR-034 Invariant 1). The content hash is never written into the governed file (ADR-012 Invariant 7).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Conformance fixtures | The ADR-012 §4.2 canonical frontmatter parses with 100% fidelity; every one of the nine daughter ADR frontmatter examples parses with no finding |
| Crash safety | 0 inputs, including malformed and empty ones, make the lint raise |
| Determinism | The same text and options always give the same findings in the same order |
| Flag integrity | 0 Tier B or C findings treated as a block; 100% of findings carry a tier |
| Floor safety | 0 accepted options that lower a floor or the out-of-scope minimum below the baseline |
| Next-step coverage | Every combination of tier, generator and retry count maps to exactly one next step |
| Storage and purity | 0 new record types; 0 imports from storage, `pmbok/` or third-party packages |

## Out of Scope

- Tier A detection (stub or mock generators in the file, placeholder tokens, crashed generation, missing files), the canonical content hash, the dependency graph, staleness, and the `approve-subsidiary-plan` gate (ADR-013, its own epic).
- Calling the lint from an orchestrator, the draft, approve and formalize commands, and removing the legacy `pmbok/` tooling (ADR-034).
- Domain-specific content rules for each plan (the daughter ADRs 025 to 033); the lint offers hooks that raise thresholds, nothing more.
- Scoring the quality of a plan beyond length and structure (future learner ADRs, ADR-012 §8).
- Changes to the route decision or the tailoring matrix (ADR-011, already built); the lint only reads routes.
