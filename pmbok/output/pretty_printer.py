"""Markdown serializer for all internal PMBOK data models."""

from __future__ import annotations

import json

from pmbok.models.business_case import BusinessCase
from pmbok.models.ideation import IdeationSummary
from pmbok.models.pmbok import ProcessMap, ProjectArtifact
from pmbok.models.reporting import ProgressReport
from pmbok.process_registry import PMBOK_PROCESSES


# Build a lookup dict: process_id → PMBOKProcess
_PROCESS_LOOKUP = {p.process_id: p for p in PMBOK_PROCESSES}


class PrettyPrinter:
    """Serialize internal data models to human-readable markdown."""

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _section(self, title: str, content: str, level: int = 2) -> str:
        """Return a markdown section string."""
        hashes = "#" * level
        return f"{hashes} {title}\n\n{content}\n\n"

    def _bullet_list(self, items: list[str]) -> str:
        if not items:
            return "_None_"
        return "\n".join(f"- {item}" for item in items)

    # ------------------------------------------------------------------
    # Public render methods
    # ------------------------------------------------------------------

    def render_ideation_summary(self, summary: IdeationSummary) -> str:
        """Render an IdeationSummary as markdown."""
        parts: list[str] = []

        # Title / header
        parts.append(f"# {summary.title}\n\n")
        parts.append(f"**Version:** {summary.version}  \n")
        parts.append(f"**Approval Status:** {summary.approval_status.value}  \n")
        parts.append(f"**Session ID:** {summary.session_id}  \n")
        parts.append(f"**Created At:** {summary.created_at.isoformat()}  \n\n")

        parts.append(self._section("Problem Statement", summary.problem_statement))
        parts.append(self._section("Proposed Solution", summary.proposed_solution))
        parts.append(self._section("Key Goals", self._bullet_list(summary.key_goals)))

        assumptions_content = self._bullet_list(summary.assumptions) if summary.assumptions else "_None_"
        parts.append(self._section("Assumptions", assumptions_content))

        constraints_content = self._bullet_list(summary.constraints) if summary.constraints else "_None_"
        parts.append(self._section("Constraints", constraints_content))

        if summary.conflicts:
            rows = ["| Field | Source A | Value A | Source B | Value B | Resolved |",
                    "|---|---|---|---|---|---|"]
            for c in summary.conflicts:
                resolved = "Yes" if c.resolved else "No"
                rows.append(
                    f"| {c.field} | {c.source_a_id} | {c.value_a} "
                    f"| {c.source_b_id} | {c.value_b} | {resolved} |"
                )
            parts.append(self._section("Conflicts", "\n".join(rows)))
        else:
            parts.append(self._section("Conflicts", "_No conflicts detected._"))

        return "".join(parts)

    def render_business_case(self, case: BusinessCase) -> str:
        """Render a BusinessCase as markdown with all 7 required sections."""
        parts: list[str] = []

        parts.append("# Business Case\n\n")
        parts.append(f"**Version:** {case.version}  \n")
        parts.append(f"**Approval Status:** {case.approval_status.value}  \n")
        parts.append(f"**Created At:** {case.created_at.isoformat()}  \n\n")

        parts.append(self._section("Executive Summary", case.executive_summary))
        parts.append(self._section("Problem Statement", case.problem_statement))
        parts.append(self._section("Proposed Solution", case.proposed_solution))
        parts.append(self._section("Expected Benefits", self._bullet_list(case.expected_benefits)))

        # Estimated Costs — table
        cost_rows = [
            "| Label | Amount | Currency | Placeholder |",
            "|---|---|---|---|",
        ]
        for item in case.estimated_costs:
            amount = str(item.amount) if item.amount is not None else "—"
            placeholder = "Yes" if item.is_placeholder else "No"
            cost_rows.append(f"| {item.label} | {amount} | {item.currency} | {placeholder} |")
        parts.append(self._section("Estimated Costs", "\n".join(cost_rows)))

        parts.append(self._section("Key Risks", self._bullet_list(case.key_risks)))
        parts.append(self._section("Recommendation", case.recommendation))

        if case.placeholders:
            parts.append(self._section("Placeholders", self._bullet_list(case.placeholders)))

        return "".join(parts)

    def render_project_artifact(self, artifact: ProjectArtifact) -> str:
        """Render a ProjectArtifact as markdown."""
        parts: list[str] = []

        parts.append(f"# Artifact: {artifact.artifact_type}\n\n")
        parts.append(f"**Artifact Type:** {artifact.artifact_type}  \n")
        parts.append(f"**Process ID:** {artifact.process_id}  \n")
        parts.append(f"**Version:** {artifact.version}  \n")
        parts.append(f"**Run ID:** {artifact.run_id}  \n")
        parts.append(f"**Created At:** {artifact.created_at.isoformat()}  \n")
        if artifact.previous_version_id:
            parts.append(f"**Previous Version ID:** {artifact.previous_version_id}  \n")
        parts.append("\n")

        content_json = json.dumps(artifact.content, indent=2, default=str)
        parts.append(self._section("Content", f"```json\n{content_json}\n```"))

        # Render audit section if audit result is available
        if artifact.audit_result is not None:
            from pmbok.output.audit_renderer import AuditRenderer
            audit_markdown = AuditRenderer.render_audit_section(artifact.audit_result)
            parts.append(audit_markdown)

        return "".join(parts)

    def render_process_map(self, process_map: ProcessMap) -> str:
        """Render a ProcessMap as markdown with a table and summary count."""
        parts: list[str] = []

        parts.append("# Process Map\n\n")
        parts.append(f"**Run ID:** {process_map.run_id}  \n")
        parts.append(f"**Updated At:** {process_map.updated_at.isoformat()}  \n\n")

        # Table
        table_rows = [
            "| Process ID | Name | Knowledge Area | Process Group | Status |",
            "|---|---|---|---|---|",
        ]
        status_counts: dict[str, int] = {}
        for state in process_map.processes:
            proc = _PROCESS_LOOKUP.get(state.process_id)
            name = proc.name if proc else state.process_id
            knowledge_area = proc.knowledge_area.value if proc else "—"
            process_group = proc.process_group.value if proc else "—"
            status = state.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            table_rows.append(
                f"| {state.process_id} | {name} | {knowledge_area} | {process_group} | {status} |"
            )

        parts.append(self._section("Processes", "\n".join(table_rows)))

        # Summary count line
        total = len(process_map.processes)
        summary_parts = [f"**Total:** {total}"]
        for status_val, count in sorted(status_counts.items()):
            summary_parts.append(f"**{status_val.replace('_', ' ').title()}:** {count}")
        parts.append("**Summary:** " + " | ".join(summary_parts) + "\n\n")

        return "".join(parts)

    def render_progress_report(self, report: ProgressReport) -> str:
        """Render a ProgressReport as markdown with per-knowledge-area status counts."""
        parts: list[str] = []

        parts.append("# Progress Report\n\n")
        parts.append(f"**Run ID:** {report.run_id}  \n")
        parts.append(f"**Generated At:** {report.generated_at.isoformat()}  \n\n")

        # Per-knowledge-area table
        table_rows = [
            "| Knowledge Area | Not Started | In Progress | Complete | Blocked |",
            "|---|---|---|---|---|",
        ]
        for area, counts in report.by_knowledge_area.items():
            area_label = area.value if hasattr(area, "value") else str(area)
            table_rows.append(
                f"| {area_label} | {counts.not_started} | {counts.in_progress} "
                f"| {counts.complete} | {counts.blocked} |"
            )

        # Totals row
        t = report.total
        table_rows.append(
            f"| **Total** | **{t.not_started}** | **{t.in_progress}** "
            f"| **{t.complete}** | **{t.blocked}** |"
        )

        parts.append(self._section("Status by Knowledge Area", "\n".join(table_rows)))

        return "".join(parts)
