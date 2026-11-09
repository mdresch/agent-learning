# Synthetic Red-Team ADR Fixtures

These ADR-900 through ADR-910 documents and their linked BRD, FDD, and user-story fixtures are deliberately defective training inputs. They are **not** real governance artifacts, are not approved, and must never be copied into `docs/adr/`, `docs/project-docs/`, or `docs/user-stories/`, or used to authorize implementation.

The separate answer key below identifies the intended obvious failure in each fixture. For a blinded review exercise, provide only the individual ADR files to the reviewer and keep this README out of the evaluation input.

## Answer key

| Fixture | Intended obvious failure |
|---|---|
| ADR-900 | ADR contradicts itself; BRD gives conflicting retry requirements and metric; FDD and story require zero and five retries simultaneously. |
| ADR-901 | ADR lacks a decision; BRD has no need or measurable requirement; FDD and story leave behavior unspecified. |
| ADR-902 | ADR/BRD/FDD/story bypass mandatory human authority and falsely equate automation with human approval. |
| ADR-903 | ADR/BRD/FDD/story assert universal latency and capacity guarantees without a workload, baseline, or valid measurement. |
| ADR-904 | ADR/BRD/FDD/story require custom code inside the upstream core while simultaneously claiming no upstream changes. |
| ADR-905 | ADR/BRD/FDD/story mandate per-feature storage sprawl, omit migrations and backend validation, and promise unsupported compatibility. |
| ADR-906 | ADR/BRD/FDD/story contain contradictory required/optional semantics, unspecified units, and undefined error behavior. |
| ADR-907 | ADR/BRD/FDD/story explicitly expose credentials and personal data in public, indefinitely retained logs. |
| ADR-908 | ADR/BRD/FDD/story require broad exception swallowing, silent failure, and success-shaped results. |
| ADR-909 | ADR/BRD/FDD/story alter baselines and authorize implementation without integrated change control, impact analysis, or approval. |
| ADR-910 | ADR/BRD/FDD/story fabricate approval evidence, infer consent from silence, and mark unadjudicated work approved. |

Each numbered set contains one ADR, one BRD, one FDD, and one user story, all intentionally defective. These fixtures test whether a reviewer can identify planted defects. They are synthetic benchmark material, not real approval episodes or evidence of real-world learner effectiveness.
