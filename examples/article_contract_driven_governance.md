# Beyond the Green Checkmark: How Contract-Driven Agent Skills Prevent, Signal, and Heal Regressions

*Why standard agent-generated tests create an illusion of correctness, and how the `implement-story` and `heal-contract-failure` framework enforces intent, catches "green defects," and compounds institutional memory.*

---

## 1. The Paradox of AI-Generated Green Checkmarks

In modern agentic development, watching an AI coding assistant write code and tests is intoxicating. The terminal spins, tests execute, and a wall of green checkmarks floods the screen. 

Yet, as engineering teams deploy coding agents into large production codebases, they hit an unsettling realization: **the green checkmarks mean less than they used to.**

Why? Because when the same agent authors both the production code and the test suite in a single turn, both are derived from the exact same internal, potentially flawed mental model of how the feature should behave. The tests do not validate reality; they merely confirm the agent’s own assumptions. If the model misinterprets an edge case, forgets a domain invariant, or assumes a dictionary key is always present, it writes tests that carefully assert its own misconception.

Even worse are **regressions**: an agent updates a function to satisfy a new prompt, silently inverts a boundary condition in an existing module, and writes a test that blesses the inverted behavior.

To build reliable software with autonomous agents, we cannot rely on unguided prompting or post-hoc guessing. We need an architectural governance framework.

In the `agent-learning` framework, this is achieved through two load-bearing, interlocking skills:
1. **`implement-story`**: A disciplined, multi-stage implementation loop enforcing specification gating, explicit intent declaration, and mandatory RED contracts.
2. **`heal-contract-failure`**: An intent-first diagnosis and repair loop designed to catch mechanical breakage, cross-epic regressions, and—most crucially—**"green defects."**

Here is how this architecture signals regressions, enforces intent, and compounds institutional memory across every change.

---

## 2. The Implementation Lifecycle (`implement-story`)

The `implement-story` skill turns ad-hoc agent coding into a deterministic, audit-logged manufacturing line. It operates in strict, non-skippable stages:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THE IMPLEMENT-STORY LOOP                        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
       [Step 0: Worktree Isolation] (Branch: feat/story-<X.Y>)
                                    │
                                    ▼
       [Step 1: Ingest Hierarchy]   (ADR > BRD/FDD > User Story)
                                    │
                                    ▼
       [Step 1b: Pre-Flight Gate]   (scripts/spec_gate.py)
       * Adversarial audit of acceptance criteria
       * Bounds, None-safety, empty collections, Bayesian readiness
                                    │
                                    ▼
       [Step 2: State Intent]       (Intent / Scope / Encoded Contract / Out-of-Scope)
                                    │
                                    ▼
       [Step 3: Contract (RED)]     (Mandatory failing pytest per criterion)
                                    │
                                    ▼
       [Step 4: Component Skill]    (Update .claude/skills/<component>/SKILL.md)
                                    │
                                    ▼
       [Step 5: Implement (GREEN)]  (Minimal code — zero speculative generalization)
                                    │
                                    ▼
       [Step 6: Full-Suite Gate]    (Full regression suite execution)
                                    │
                                    ▼
       [Step 8: Adversarial PR Gate] (External Review bot + scripts/pr_gate.py)
                                    │
                                    ▼
       [Step 9: Breakout Recap]     (Lessons Learned OPA Register: LL-###)
```

### Stage 1b: The Pre-Flight Specification Gate
Before any code or test is written, the story is audited by an automated Bayesian specification gatekeeper:
```bash
uv run python scripts/spec_gate.py <X.Y>
```
The spec gate audits the story against common agent failure modes:
* **Specification Completeness:** Are all return types and state transitions explicit?
* **None-Safety & Boundary Invariants:** What happens on empty collections, null inputs, or non-finite numbers ($+\infty, -\infty, \text{NaN}$)?
* **Upstream Fork Purity:** Does the change violate core architectural boundaries?

If the specification has ambiguities, **the gate halts the process**. The agent is not permitted to guess. All recommended interpretations ($I_1, I_2, \dots$) must be documented explicitly in the test header docstrings.

### Stage 2 & 3: Intent Declaration and Mandatory RED Contracts
Before touching code, the agent must output a formal **Intent Declaration**:
1. **Intent:** The business or architectural problem being solved.
2. **Scope:** Exactly which modules are modified.
3. **Contract to Encode:** The concrete assertions to be added.
4. **Explicitly Out of Scope:** Guardrails preventing speculative feature creep.

The agent then writes a contract test for each Acceptance Criterion and **must observe it fail (RED)**. Tests cannot be written after the fact to retroactively match an implementation.

---

## 3. How Regressions Are Signalled

In our framework, a regression is not just a red build in CI. Regressions are categorized into four distinct triggers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FOUR REGRESSION TRIGGERS                        │
├────────────────────────────┬───────────────────────────────────────────┤
│ 1. Mechanical Failure      │ Test runner throws an AssertionError,      │
│    (RED)                   │ type-check breaks, or unhandled exception.│
├────────────────────────────┼───────────────────────────────────────────┤
│ 2. The "Green Defect"      │ Tests pass (GREEN), but an adversarial    │
│    (Latent Defect)         │ reviewer exposes a logical flaw or bypass.│
├────────────────────────────┼───────────────────────────────────────────┤
│ 3. Cross-Epic Regression   │ A change in module A silently breaks a     │
│    (Foreign Contract)      │ foreign contract in module B.             │
├────────────────────────────┼───────────────────────────────────────────┤
│ 4. Dependency Bump Drift   │ A package update passes neutral checks    │
│    (Third-Party Breakage)  │ but alters runtime precision or APIs.     │
└────────────────────────────┴───────────────────────────────────────────┘
```

### The Most Dangerous Case: The "Green Defect"
The most deceptive failure in AI coding occurs when **all tests are green, but the code is wrong**.

*Example:* An agent writes an expense claim approval function. It writes a test with valid expenses and asserts `status == APPROVED`. All tests pass. 
However, an adversarial reviewer inspects the code and notices that if a claim has an empty expense list or negative amounts, the validation short-circuits and still marks it `APPROVED`.

In naive agent workflows, the developer tells the agent: *"Hey, fix that bug,"* and the agent patches the `if` statement directly. 

In our framework, this is strictly forbidden. A passing test suite with a latent defect is formally designated as a **Contract Incompleteness Failure**.

---

## 4. The Healing Loop (`heal-contract-failure`)

When any regression or green defect is signalled, the agent does not start tweaking production code. It invokes **`heal-contract-failure`**, a five-step discipline loop:

```
[Regression Signalled: Mechanical, Green Defect, or Foreign Breakage]
                               │
                               ▼
               ┌───────────────────────────────┐
               │ 1. Re-validate Intent fresh   │
               │    (Trace back to ADR/FDD)    │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │ 2. Expose Contract: Make it   │
               │    RED before touching code!  │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │ 3. Update Component Skill     │
               │    (.claude/skills/<c>/SKILL) │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │ 4. Minimal Implementation     │
               │    Fix to satisfy contract    │
               └───────────────┬───────────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │ 5. Full-Suite Regression Gate │
               │    (Verify all epics green)   │
               └───────────────────────────────┘
```

### Rule 1: Never Touch Code Without a Failing Contract (Make it RED)
If an adversarial review or edge-case discovery exposes a defect:
* The agent is prohibited from modifying the implementation.
* It must first construct a new contract test reproducing the defect (e.g. passing empty claims or inverted operations).
* The test must run and be **observed failing (RED)** against the current code.
* Only once the contract fails can the agent touch the implementation to bring it to **GREEN**.

### Rule 2: Cross-Epic Regression Attribution
When an agent implements a feature in Module A and a test breaks in Module B:
* **The Anti-Pattern:** Modifying Module B's test to make it pass.
* **The Law:** The current change in Module A is presumed guilty. The agent must attribute the regression, determine what unexpected coupling occurred, and **narrow the diff in Module A** rather than altering the foreign contract.

### Rule 3: The Hard-Stop Escalation Boundary
If reaching GREEN requires weakening, skipping, or bypassing an assertion, an lint rule, or an architectural boundary, the heal loop halts immediately and escalates to human review. The loop is capped at **3 bounded attempts**—repeated churn without new information triggers an immediate escalation.

---

## 5. Adversarial Review & The Bayesian PR Gate

How do regressions get caught if the authoring agent is blind to them? Through **decoupled external review**.

In Stage 8 of `implement-story`:
1. The agent pushes its branch and triggers an external reviewer bot (e.g., Amazon Q or a distinct review agent):
   ```bash
   gh pr comment <n> --body "/q review"
   ```
2. The reviewer inspects only the Git diff and PR description—it has no access to the authoring agent's internal reasoning.
3. Every reviewer finding is triaged into structured claims: `crash risk`, `logic error`, `test gap`, or `style`.
4. The **Bayesian PR Gatekeeper (`scripts/pr_gate.py`)** runs:
   ```bash
   uv run python scripts/pr_gate.py <n>
   ```
   The gatekeeper translates reviewer critique into Bayesian log-odds shifts and doubt inflation ($\kappa = 0.20$). If serious crash risks or test gaps remain unaddressed, the decision utility drops below the non-negotiable $+0.05$ threshold, and **the pull request is blocked from merging**.

---

## 6. Compounding Institutional Memory

The fatal flaw of unguided coding agents is that they have **zero institutional memory**. An agent that spends two hours debugging a subtle floating-point precision bug in a payment calculator will happily reintroduce that exact same bug next week in a different file.

Our governance framework prevents this through two persistent artifacts:

### 1. Component Skills (`.claude/skills/<component>/SKILL.md`)
Every story or heal pass must update the relevant component skill. If an edge case is discovered (e.g. *"criterion weights must sum to 1.0; non-finite floats trigger ValueError"*), it is documented as a load-bearing constraint in the component skill. Future agents loading that component receive the constraint directly in their system prompt.

### 2. The Lessons Learned Register (`LL-###`)
Governed by ADR-010, the end of each development cycle triggers a formal breakout recap. Lessons are categorized by:
* **Title & Trap:** What surprising behavior caught the agent?
* **Root Cause:** Why did the failure occur?
* **Rule:** What invariant must be preserved?
* **Propagation Target:** Which skills or automated pre-flight checks must inherit this rule?

---

## Conclusion: Engineering Discipline for Autonomous Agents

Autonomous coding agents are formidable engines of code generation, but generation without governance is a liability. 

Left to themselves:
* Agents test only what they remember to build.
* They celebrate green checkmarks on incomplete specifications.
* They patch symptoms rather than codifying contracts.

By implementing structured skills like **`implement-story`** and **`heal-contract-failure`**, we introduce the missing half of the equation: **contract-driven rigor**. 

By forcing intent declaration, pre-flight specification gating, mandatory RED contracts, adversarial review gates, and compounding component memory, we transform coding agents from unpredictable code generators into reliable, disciplined software engineering partners.

