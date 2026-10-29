# BRD-020: Explicit Policy Prior Warm-Starting

**Source ADR:** [ADR-020](../../adr/ADR-020-explicit-policy-prior-warm-starting.md) — Accepted (2026-10-28)  
**Governing Baseline:** none approved yet; cycle `CYC-001` (ADR-035, Accepted)  
**Status:** Approved (2026-10-29, Menno) — derived from Accepted ADR-020; adjudicated via `approve-brd` (robust utility 0.732, episode `a16c1f37-1c53-4b19-af1d-219e8bdc1b75`).  
**Stakeholders:** Menno (Sponsor/PM/maintainer); SDK adopters who start a new low-authority policy next to similar ones; auditors who must see which policy a starting point was copied from  

## Business Need

A new low-authority policy starts with every logit at zero and needs human supervision to learn what a similar, already-trained policy knows. ADR-020 decides a deliberate, recorded copy: a human names a donor policy and says which donor action each new action corresponds to, and the new policy starts from the donor's logits scaled down by a damping factor, so it begins informed but not certain. The copy changes nothing about what the new policy must earn: its own outcomes still decide whether it may act without a human. The expected saving in supervision is not measured and is what HYP-AL-008 tests. Nothing is built, and no converged donor exists today.

## Business Rules (BRU)

- **BRU-020-01 (Damped Copy):** The new policy's logit for an action is the donor's logit for the action it maps to, multiplied by the damping factor `tau`. `tau` lies in (0, 1]; the default is 0.70; a value above 1 or not positive is refused (ADR-020 §4.1, Invariant 2).
- **BRU-020-02 (Complete Declared Map):** Every action of the new policy is mapped, by a map a human supplies, to a distinct donor action. When the two policies have identical action ids the map may be omitted. The tool never infers a map (ADR-020 §4.1, Invariant 3).
- **BRU-020-03 (Donor Untouched):** The donor snapshot and its episodes are never changed, then or later. Updating the new policy never changes the donor (ADR-020 Invariant 1).
- **BRU-020-04 (Only A New Policy):** The copy applies only to a low-authority decision policy that is still cold: no update applied, no episodes seen, all logits zero, and no earlier warm start. Otherwise it is refused and nothing is written, so learned logits are never overwritten (FDD-020 J2).
- **BRU-020-05 (Recorded Lineage):** The new snapshot records the donor's policy id, task id and version, the damping factor, the action map, the time, and what kind of donor it was (ADR-020 §4.3; FDD-020 J3).
- **BRU-020-06 (No Borrowed Evidence):** Copied logits are not scored outcomes. The new policy still needs its own outcomes for the ADR-003 gate (ADR-020 §7 Invariant 5).
- **BRU-020-07 (Storage Boundary):** The transfer is recorded only in `PolicySnapshot.metadata`. Zero new `LearningStore` record types (ADR-020 Invariant 4; ADR-002).
- **BRU-020-08 (A New Version):** The copy produces a new snapshot version of the target policy, made active, so a decision made under the earlier version stays tied to it (FDD-020 J4).
- **BRU-020-09 (One Seeding Path):** A family meta-prior (ADR-019) is applied through the same command and the same damping rule, with the map taken from the new policy's declared `role_map`, so there is one way to seed a policy (FDD-020 J5).
- **BRU-020-10 (A Donor Is A Human Choice):** The tool checks that a donor is structurally usable (low authority, has logits, a valid map). Whether it is a good donor is the operator's judgement, and negative transfer remains possible; the tool records whether the donor's ADR-003 gate was met but does not block on it (ADR-020 §6 Negative; FDD-020 J1).
- **BRU-020-11 (No Claim Of Effectiveness):** No converged donor exists today (the `approve-*` policies are full authority). The first evidence is the arithmetic of the copy and that a copy leaves the target without autonomy credit. Nothing is claimed about reduced supervision (HYP-AL-008 stays open; ADR-020 §4.4).

## Stakeholder Success Metrics

| Metric | Target |
|---|---|
| Arithmetic | each new logit equals `tau` times the mapped donor logit to 1e-12 on tested cases; `tau = 1.0` reproduces the donor logits exactly |
| Damping | for a donor with unequal logits, a smaller `tau` gives a higher softmax entropy, on every tested pair of values |
| Refusals | 100% of `tau` outside (0, 1], incomplete or non-injective maps, maps to unknown donor actions, full-authority or logit-less donors, and non-cold targets are refused with a reason and write nothing |
| Isolation | 0 donor snapshots or episodes changed by a warm start (deep-equal before and after) |
| Lineage | 100% of warm-started snapshots carry the donor ids and version, the damping factor, the action map, the time and the donor kind |
| Gate separation | a warm-started policy with no episodes is not eligible under the ADR-003 gate |
| New version | the warm-started snapshot has the next version and is the active policy of the target task; the earlier version is kept unchanged |
| Meta-prior path | a meta-prior donor seeds the same values as the pure `seed_values` of FDD-019, damped by `tau` |
| Storage boundary | 0 new record types; 0 imports from `agent_learning.storage` in the pure module |

## Out of Scope

- Measuring whether a warm start reduces supervision (HYP-AL-008). It needs a real converged donor and a comparison against a cold start.
- Warm-starting Thompson policies, whose posterior is in Beta counts (FDD-015); this command covers logit policies and logit meta-priors only.
- Choosing or recommending a donor, or inferring an action map.
- Making the audit replay support a warm start; it is not a training run.
- A shared global weight vector, direct undamped copying above 1.0, and cold-start as the only option (ADR-020 §5).
