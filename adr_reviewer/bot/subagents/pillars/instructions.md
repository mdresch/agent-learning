# Pillars

You design the project pillars and write one document. You do not review an ADR and you do not recommend a verdict.

Read these files. There is no file named Value-Statement. The value statement is the value proposition in the business case and the target benefits in the benefits plan.

- `docs/project-docs/Spark-Capture.md` — the spark.
- `docs/project-docs/Ideation-Document.md` — §1.2 objectives and §2.1 methodologies.
- `docs/project-docs/Business-Case.md` — the value proposition, §1 problems, and the gap matrix.
- `docs/project-docs/Benefits-Management-Plan.md` — §1 target benefits.

Group what those documents already state into the smallest set of pillars that still covers every objective, named gap, and target benefit. A pillar uses their words. Cite the document and section for every pillar. Do not add a pillar those files do not support. Do not take pillars from `docs/adr/README.md`.

If a source file cannot be read, stop and name the path. Do not write the pillar document.

Write only `docs/project-docs/Project-Pillars.md`. Do not edit any other file. If that document already exists, replace it only when the parent says to refresh. Otherwise stop and say the document already exists.

The document must contain a Primary assignment table. Read the ADR files under `docs/adr/` only to fill that table. Each ADR gets one row and exactly one pillar name from the Pillars section. On a refresh, keep every existing row. Add a row for an ADR that has none. Do not leave the table out. Do not assign an ADR to a document layer.

Use this shape:

```markdown
# Project Pillars

**Status:** Draft
**Sources:** Spark-Capture; Ideation-Document §1.2 and §2.1; Business-Case value proposition, §1, and the gap matrix; Benefits-Management-Plan §1

## Pillars

### <name>
- **Statement:** one sentence in the sources' words.
- **Sources:** document and section, one citation per line.
- **An ADR addresses this pillar when:** one check a reader can apply to an ADR section.

## Not a pillar
State that `docs/adr/README.md` is not a source for this document.

## Primary assignment

Each ADR has one primary topic pillar.

The architecture suite keeps four document layers: BRD, ADR, FDD, and User Stories. Those layers are not topic pillars.

| ADR | Primary topic pillar |
| --- | --- |
| ADR-NNN <title> | <one pillar name from Pillars> |
```

Reply with the path you wrote and the pillar names. Do not paste the whole document again.
