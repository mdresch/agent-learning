# Project Pillars

**Status:** Draft
**Sources:** Spark-Capture; Ideation-Document §1.2 and §2.1; Business-Case value proposition, §1, and the gap matrix; Benefits-Management-Plan §1

## Pillars

### Frozen-model, in-process learning
- **Statement:** Keep the foundation model frozen, and let an agent improve a recurring decision with an in-process policy layer and no GPU training job.
- **Sources:**
  - Spark-Capture, "The spark" and "Why now"
  - Ideation-Document §1.2, objective 1
- **An ADR addresses this pillar when:** it decides how a recurring decision is learned or resolved without a fine-tune job.

### Earned, auditable autonomy
- **Statement:** Autonomy is earned and auditable, never assumed: a decision runs unsupervised only after it clears a named, inspectable bar, and every such decision traces to the evidence that cleared it.
- **Sources:**
  - Ideation-Document §1.2, objective 2
  - Business-Case, value proposition
  - Spark-Capture, "The spark" (prompt hacks that cannot be audited)
- **An ADR addresses this pillar when:** it decides the bar an unsupervised decision must clear, or how that decision traces to the evidence that cleared it.

### One TaskPolicy for statistical and reasoned resolution
- **Statement:** Statistical and reasoned resolution stay under one TaskPolicy, chosen for the decision's shape. Today that choice is fixed at task-policy-init; the named gap is a per-instance choice when the shape genuinely varies.
- **Sources:**
  - Ideation-Document §1.2, objective 3
  - Business-Case §2, "Routing between `low` and `full` authority" (methodology #17)
- **An ADR addresses this pillar when:** it decides how low and full authority share one policy, or how a request chooses between them.

### Packaged contextual learning
- **Statement:** Close the gap between example-only and packaged contextual learning, so ContextualSoftmaxPolicy has an exported, documented learner and CLI path.
- **Sources:**
  - Ideation-Document §1.2, objective 4
  - Ideation-Document §2.1, methodology #4
  - Benefits-Management-Plan §1a, "Real second case beyond SocialEngage" (the unpackaged contextual-bandit gap)
- **An ADR addresses this pillar when:** it decides how contextual learning moves from an example into the packaged SDK.

### An honest place against SFT, RLVR, and ERL
- **Statement:** Give adopters an honest, complete answer to where this sits relative to SFT, RLVR, and ERL, covering all five learning and resolution variants, not only the low-authority bandit.
- **Sources:**
  - Ideation-Document §1.2, objective 5
- **An ADR addresses this pillar when:** it decides what this SDK does, and does not do, relative to supervised fine-tuning, reinforcement learning from verifiable rewards, or experience-reflection-retry learning.

### Critique becomes evidence
- **Statement:** Rich textual feedback is generated and then discarded, because REINFORCE consumes only a scalar reward. Critique should convert into DecisionFrame evidence or pairwise preference data.
- **Sources:**
  - Business-Case §1, problem 1
  - Business-Case §2, "Learning from textual critique" (methodologies #8 and #13)
- **An ADR addresses this pillar when:** it decides how textual critique becomes evidence or pairwise preference data without changing the foundation-model weights.

### A new policy inherits a similar policy's prior
- **Statement:** A new policy should inherit priors from a structurally similar converged policy instead of starting from a uniform prior, so later policies cost fewer manual reviews and less integration effort.
- **Sources:**
  - Business-Case §1, problem 2
  - Business-Case §2, "Cold-start cost for a new policy" (methodologies #14 and #15)
  - Benefits-Management-Plan §1a, "Fewer total manual reviews" (HYP-AL-008)
  - Benefits-Management-Plan §1a, "Lower integration friction for every future policy" (HYP-AL-008)
- **An ADR addresses this pillar when:** it decides how a new policy starts from a similar policy's converged state.

### A repair path for a stuck low-authority decision
- **Statement:** A low-authority decision that is stuck on sparse or skewed evidence needs a packaged, confidence-interval bandit repair that does not switch the authority mode. A second case is a static provider-priority ranking that could become a UCB or Thompson bandit.
- **Sources:**
  - Business-Case §1, problem 3
  - Business-Case §2, "Repair path for a stuck low-authority decision" (methodologies #9, #10, and #11)
  - Benefits-Management-Plan §1a, "A packaged repair path" (HYP-AL-009)
  - Benefits-Management-Plan §1a, "Real second case beyond SocialEngage" (HYP-AL-009)
  - Spark-Capture, "The spark" (confidence bounds and reinforcement bandits)
- **An ADR addresses this pillar when:** it decides a sample-efficient bandit that can cross the autonomy gate on positive-only or skewed evidence without leaving low authority.

### A hosted layer someone would pay for
- **Statement:** A hosted governance-as-a-service layer, distinct from the free SDK, is a target benefit only. It is not yet validated, and it is not a claim.
- **Sources:**
  - Benefits-Management-Plan §1b (HYP-AL-011)
- **An ADR addresses this pillar when:** it decides a hosted service that adopters would pay for, as distinct from the free SDK.

## Primary assignment

Each ADR has one primary topic pillar. A second topic may be named in the ADR, but the assignment below is the primary.

The architecture suite keeps four document layers: BRD, ADR, FDD, and User Stories. Those layers are not topic pillars.

| ADR | Primary topic pillar |
| --- | --- |
| ADR-001 Decision authority model | One TaskPolicy for statistical and reasoned resolution |
| ADR-002 Storage backend strategy | Frozen-model, in-process learning |
| ADR-003 Evidence-gated autonomy thresholds | Earned, auditable autonomy |
| ADR-004 Authority-migration snapshot | One TaskPolicy for statistical and reasoned resolution |
| ADR-005 Decision-progress comparison | Earned, auditable autonomy |
| ADR-006 Lightweight evidence capture | Earned, auditable autonomy |
| ADR-007 Paired diff classification | One TaskPolicy for statistical and reasoned resolution |
| ADR-008 PMBOK lifecycle and adaptation loop | Earned, auditable autonomy |
| ADR-009 Intent refinement | Earned, auditable autonomy |
| ADR-010 Lessons-learned register | Critique becomes evidence |
| ADR-011 Tailoring and route decision | Earned, auditable autonomy |
| ADR-012 Plan content contracts | Earned, auditable autonomy |
| ADR-013 Subsidiary-plan approval gates | Earned, auditable autonomy |
| ADR-014 Critique-to-evidence ingestion | Critique becomes evidence |
| ADR-015 Thompson sampling | A repair path for a stuck low-authority decision |
| ADR-016 UCB | A repair path for a stuck low-authority decision |
| ADR-017 Epsilon-greedy | A repair path for a stuck low-authority decision |
| ADR-018 Pairwise preference | Critique becomes evidence |
| ADR-019 Meta-prior compilation | A new policy inherits a similar policy's prior |
| ADR-020 Warm-starting | A new policy inherits a similar policy's prior |
| ADR-021 Authority ensemble routing | One TaskPolicy for statistical and reasoned resolution |
| ADR-022 Scored-search compilation | Frozen-model, in-process learning |
| ADR-023 Dueling-bandit ranking | Critique becomes evidence |
| ADR-024 Methodology selection | Frozen-model, in-process learning |
| ADR-025 Scope plan standard | Earned, auditable autonomy |
| ADR-026 Schedule plan standard | Earned, auditable autonomy |
| ADR-027 Cost plan standard | Earned, auditable autonomy |
| ADR-028 Risk plan standard | Earned, auditable autonomy |
| ADR-029 Quality plan standard | Earned, auditable autonomy |
| ADR-030 Resource plan standard | Earned, auditable autonomy |
| ADR-031 Stakeholder plan standard | Earned, auditable autonomy |
| ADR-032 Communications plan standard | Earned, auditable autonomy |
| ADR-033 Procurement plan standard | Earned, auditable autonomy |
| ADR-034 Tooling decommission | Frozen-model, in-process learning |
| ADR-035 Cycle traceability | Earned, auditable autonomy |
| ADR-036 Methodology catalog and review triage | An honest place against SFT, RLVR, and ERL |
| ADR-037 Design-time baseline feedback | Earned, auditable autonomy |
| ADR-038 Packaged contextual learning | Packaged contextual learning |

A hosted layer someone would pay for has no ADR.

## Not a pillar
`docs/adr/README.md` is not a source for this document. Its four-pillar manifesto is not a project pillar here.
