"""
Audit Result Rendering.

Renders audit results to Markdown format for display in artifacts and reports.
"""

from pmbok.models.audit import AuditResult, AuditSeverity


class AuditRenderer:
    """Renders audit results to markdown."""

    @staticmethod
    def render_audit_section(audit_result: AuditResult) -> str:
        """
        Render a complete audit section in Markdown.

        Args:
            audit_result: The audit result to render

        Returns:
            Markdown string
        """
        lines = []

        # Header
        lines.append("\n## Quality Audit Results")
        lines.append(f"*Policy Set Applied: {audit_result.policy_set_applied}*\n")

        # Compliance Score Section
        lines.append("### Compliance Score")
        lines.append(
            f"- **Score**: {audit_result.compliance_score:.1f}% ({audit_result.compliance_tier.value})"
        )
        lines.append(f"- **Audit Timestamp**: {audit_result.audit_timestamp.isoformat()}\n")

        # Confidence Score Section
        lines.append("### Confidence Score")
        lines.append(f"- **Score**: {audit_result.confidence_score:.1f}%")
        lines.append("- **Basis**:")
        for key, value in audit_result.confidence_basis.items():
            formatted_key = key.replace("_", " ").title()
            if isinstance(value, float):
                lines.append(f"  - {formatted_key}: {value:.1%}" if key.endswith("_rate") or key.endswith("_contribution") else f"  - {formatted_key}: {value:.3f}")
            else:
                lines.append(f"  - {formatted_key}: {value}")
        lines.append("")

        # Criterion Scores Breakdown
        if audit_result.criterion_scores:
            lines.append("### Compliance Criteria Breakdown")
            lines.append("| Criterion | Score | Passed | Total | Weight |")
            lines.append("|-----------|-------|--------|-------|--------|")
            for cs in audit_result.criterion_scores:
                lines.append(
                    f"| {cs.name} | {cs.score:.1f}% | {cs.checks_passed} | {cs.checks_total} | {cs.weight:.0%} |"
                )
            lines.append("")

        # Findings Section
        if audit_result.findings:
            lines.append("### Findings")
            lines.append(
                f"- **Total**: {audit_result.total_findings} "
                f"(Critical: {audit_result.critical_count}, "
                f"Warning: {audit_result.warning_count}, "
                f"Info: {audit_result.info_count})\n"
            )

            # Group findings by severity
            for severity in [AuditSeverity.CRITICAL, AuditSeverity.WARNING, AuditSeverity.INFO]:
                severity_findings = [
                    f for f in audit_result.findings if f.severity == severity
                ]
                if severity_findings:
                    lines.append(f"#### {severity.value} Findings")
                    for finding in severity_findings:
                        lines.append(f"- **[{finding.code}]** {finding.message}")
                        if finding.affected_fields:
                            lines.append(
                                f"  - Affected Fields: {', '.join(finding.affected_fields)}"
                            )
                        if finding.remediation:
                            lines.append(f"  - Remediation: {finding.remediation}")
                    lines.append("")
        else:
            lines.append("### Findings")
            lines.append("No audit findings. Artifact passes all compliance checks.\n")

        # Summary
        lines.append("### Audit Summary")
        lines.append(
            f"This artifact has been validated against the **{audit_result.policy_set_applied}** policy "
            f"at {audit_result.audit_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}."
        )
        lines.append(f"Compliance Score: **{audit_result.compliance_score:.1f}%** ({audit_result.compliance_tier.value})")
        lines.append(f"Confidence Level: **{audit_result.confidence_score:.1f}%**")

        return "\n".join(lines)

    @staticmethod
    def render_audit_summary(audit_result: AuditResult) -> str:
        """
        Render a brief audit summary (one-liner format).

        Args:
            audit_result: The audit result to render

        Returns:
            Short summary string
        """
        return (
            f"✓ Audit: {audit_result.compliance_score:.0f}% compliance "
            f"({audit_result.compliance_tier.value}) | "
            f"Confidence: {audit_result.confidence_score:.0f}% | "
            f"Findings: {audit_result.critical_count} critical, "
            f"{audit_result.warning_count} warnings"
        )

    @staticmethod
    def render_findings_table(audit_result: AuditResult) -> str:
        """
        Render findings in tabular format.

        Args:
            audit_result: The audit result to render

        Returns:
            Markdown table string
        """
        if not audit_result.findings:
            return "No findings."

        lines = []
        lines.append("| Severity | Code | Message | Fields |")
        lines.append("|----------|------|---------|--------|")

        for finding in audit_result.findings:
            fields_str = ", ".join(finding.affected_fields) if finding.affected_fields else "-"
            # Escape pipe characters in message
            message = finding.message.replace("|", "\\|")
            lines.append(
                f"| {finding.severity.value} | {finding.code} | {message} | {fields_str} |"
            )

        return "\n".join(lines)

    @staticmethod
    def render_compliance_scorecard(audit_result: AuditResult) -> str:
        """
        Render a compliance scorecard view.

        Args:
            audit_result: The audit result to render

        Returns:
            Markdown scorecard string
        """
        lines = []
        lines.append("## Compliance Scorecard")
        lines.append("")
        lines.append(f"**Overall Compliance**: {audit_result.compliance_score:.1f}% ({audit_result.compliance_tier.value})")
        lines.append(f"**Confidence**: {audit_result.confidence_score:.1f}%")
        lines.append(f"**Policy**: {audit_result.policy_set_applied}")
        lines.append("")

        if audit_result.criterion_scores:
            lines.append("**Criterion Scores**:")
            for cs in audit_result.criterion_scores:
                # Create a simple bar chart representation
                bar_length = 20
                filled = int(bar_length * cs.score / 100)
                bar = "█" * filled + "░" * (bar_length - filled)
                lines.append(
                    f"- {cs.name}: [{bar}] {cs.score:.0f}% ({cs.checks_passed}/{cs.checks_total})"
                )

        return "\n".join(lines)
