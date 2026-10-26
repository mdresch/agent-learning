# Epic 36: Learning Methodology Examples, Best-Practice Ledger and the Review-Triage Learning Loop

**Source ADR:** [ADR-036](../adr/ADR-036-learning-methodology-examples-ledger-and-review-triage-loop.md) — Accepted (2026-10-26)  
**Source BRD/FDD:** [BRD-036](../project-docs/Business-Requirements/BRD-036-learning-methodology-examples-ledger-and-review-triage-loop.md) / [FDD-036](../project-docs/Functional-Design/FDD-036-learning-methodology-examples-ledger-and-review-triage-loop.md)  
**Status:** Approved (2026-10-26, Menno) — derived from Accepted ADR-036; adjudicated via `approve-user-stories` (robust utility 0.769, episode `80fe8a45-29a0-4a52-baa9-476f70d88209`).  The epic number follows the source ADR number, as Epic 11 follows ADR-011.  

---

## Story 36.1 — The Catalog and Its Integrity Check

**Status:** Approved (2026-10-26, Menno) — derived from Accepted ADR-036, BRD-036 and FDD-036; adjudicated via `approve-user-stories` (episode `80fe8a45-29a0-4a52-baa9-476f70d88209`). Completed (2026-10-26) — implemented in feat/story-36.1 with contract tests in tests/test_methodology_catalog.py.  
**As** a maintainer, **I want** a catalog entry for each of the 32 methodologies with a class derived from its state, **so that** no methodology is silently missing or mislabeled.

### Acceptance Criteria:
- **$AC_0$ (Complete):** `validate_catalog()` raises `ValueError` naming the ids when the entries are not exactly 1 to 32, each once.
- **$AC_1$ (Class Follows State):** `derive_class()` maps each state to its class per FDD-036 §2.1, and `validate_catalog()` raises when an entry's class differs from the derived class.
- **$AC_2$ (Documented Needs a Reason):** a `documented` entry with an empty `reason` or `reopening_condition` raises `ValueError`.
- **$AC_3$ (Paths):** every non-null `path` exists under `examples/methodologies/`; a path outside it raises.
- **$AC_4$ (Pure):** `methodology_catalog.py` imports nothing from `agent_learning.storage`.

---

## Story 36.2 — Runnable Examples for What Exists

**Status:** Approved (2026-10-26, Menno) — derived from Accepted ADR-036, BRD-036 and FDD-036; adjudicated via `approve-user-stories` (episode `80fe8a45-29a0-4a52-baa9-476f70d88209`). Completed (2026-10-26) — implemented in feat/story-36.2 with contract tests in tests/test_methodology_examples.py.  
**As** an adopter, **I want** to run an example of each implemented, example-only, partial or practiced methodology, **so that** I can see how it behaves before using it.

### Acceptance Criteria:
- **$AC_0$ (Coverage):** each of #2, #3, #4, #5, #6, #12, #19, #20, #21 has a directory with `README.md` and `example.py`, and its catalog entry is `runnable`.
- **$AC_1$ (Header):** each script begins with the labeling header of ADR-036 §4.2, including `DATA: SYNTHETIC` and `NOT EVIDENCE`.
- **$AC_2$ (Runs):** each script exits 0 offline within a time limit, in a temporary directory.
- **$AC_3$ (Isolation):** no file under `src/` imports from `examples/`, and a run leaves the real store and the catalog file unchanged.

---

## Story 36.3 — Proof-of-Concept Sketches for the ADR-Backed Candidates

**Status:** Approved (2026-10-26, Menno) — derived from Accepted ADR-036, BRD-036 and FDD-036; adjudicated via `approve-user-stories` (episode `80fe8a45-29a0-4a52-baa9-476f70d88209`). Completed (2026-10-26) — implemented in feat/story-36.3 with contract tests in tests/test_methodology_sketches.py.  
**As** a maintainer, **I want** a clearly labeled sketch for each candidate that has a Proposed ADR, **so that** the design can be examined without claiming it works.

### Acceptance Criteria:
- **$AC_0$ (Coverage):** each of #8 to #11, #13 to #15, #17, #22, #23 has a directory with `README.md` and `sketch.py`, and its catalog entry is `proof_of_concept`.
- **$AC_1$ (Header):** each script carries the labeling header with `CODE: sketch`.
- **$AC_2$ (Deterministic):** each sketch runs offline with a fixed seed and exits 0, using the standard library and the public SDK only.
- **$AC_3$ (Falsification):** each README states the falsification criterion from its hypothesis and the real data needed to test it.
- **$AC_4$ (State Untouched):** running every sketch leaves each methodology's `state` in the catalog unchanged.

---

## Story 36.4 — The Best-Practice Ledger

**Status:** Approved (2026-10-26, Menno) — derived from Accepted ADR-036, BRD-036 and FDD-036; adjudicated via `approve-user-stories` (episode `80fe8a45-29a0-4a52-baa9-476f70d88209`).  
**As** a maintainer, **I want** an append-only ledger of practices per methodology with an honest evidence class, **so that** only practices backed by real episodes become adopted.

### Acceptance Criteria:
- **$AC_0$ (Schema):** `parse_ledger()` raises `ValueError` naming the entry for an unknown enumeration value or an unknown methodology id.
- **$AC_1$ (Adoption Needs Real Episodes):** an `adopted` entry whose `evidence_class` is not `real-episodes`, or whose `evidence_count` is below the declared tier's outcome gate, raises.
- **$AC_2$ (Append-Only):** a status change is a new entry with `supersedes` naming an existing entry; an unknown `supersedes` raises; the latest in the chain is current.
- **$AC_3$ (Links):** every `LL-###` and `HYP-AL-###` link resolves to an existing identifier.
- **$AC_4$ (Pure):** `methodology_ledger.py` imports nothing from `agent_learning.storage`.

---

## Story 36.5 — The Review-Triage Learning Loop

**Status:** Approved (2026-10-26, Menno) — derived from Accepted ADR-036, BRD-036 and FDD-036; adjudicated via `approve-user-stories` (episode `80fe8a45-29a0-4a52-baa9-476f70d88209`).  
**As** the maintainer triaging automated-review findings, **I want** each decision recorded in a fixed shape and turned into evidence for the next one, **so that** the project learns from its own build loop without any learned accept or decline.

### Acceptance Criteria:
- **$AC_0$ (Record Shape):** `parse_triage_line()` returns a `TriageRecord` and raises `ValueError` for a field outside its vocabulary; `unknown` is accepted.
- **$AC_1$ (Episode Metadata):** `to_episode_metadata()` returns a plain dict and `review_triage.py` imports nothing from `agent_learning.storage`, so no record type is added.
- **$AC_2$ (Reliability Evidence):** `reliability()` returns the Wilson lower bound for a reviewer and claim type, excludes `unknown` records, counts `partial` as not verified, and returns `lower_bound = None` below `min_cases`.
- **$AC_3$ (No Guessing):** a backfilled record has `reconstructed = True` and any field not shown by the repository history reads `unknown`.
- **$AC_4$ (Triage Shape Keeps a Human):** `docs/policy-shapes/triage-review-finding.actions.json` lists exactly `accept_and_amend`, `decline_with_reason` and `defer_to_human`, and `triage-review-finding.profile.json` loads with `ComplexityProfile.from_dict` with `requires_human_approval` true.
- **$AC_5$ (Routing Shape Is Separate):** `docs/policy-shapes/route-review-finding.actions.json` lists only `verify_logic_claims_first`, `verify_test_claims_first` and `verify_documentation_claims_first`, with no accept or decline action, and `route-review-finding.profile.json` loads with `ComplexityProfile.from_dict`.
- **$AC_6$ (Nothing Sets the Decision):** a test builds records, calls `reliability()` and `to_episode_metadata()`, and asserts every record's `decision` is unchanged.

---

## Story 36.6 — Tailoring for the Store and Lessons Learned, and Template Propagation

**Status:** Approved (2026-10-26, Menno) — derived from Accepted ADR-036, BRD-036 and FDD-036; adjudicated via `approve-user-stories` (episode `80fe8a45-29a0-4a52-baa9-476f70d88209`).  
**As** a maintainer, **I want** a tailoring matrix of candidate pairings and its propagation to the template, **so that** new projects start from methodologies matched to their store and lessons learned.

### Acceptance Criteria:
- **$AC_0$ (Pairings):** every row of the matrix names a catalog id that exists, a need for the store or lessons learned, and a falsification criterion, and is marked `hypothesis`.
- **$AC_1$ (Ledger Link):** every pairing links to a ledger entry with status `candidate`.
- **$AC_2$ (Propagation):** the catalog layout, the ledger template and the matrix are present in `sidpa-template` and its integrity tests pass.
- **$AC_3$ (Recap):** this epic's last story ends with the ADR-010 breakout recap recorded in the Lessons-Learned Register.
