from __future__ import annotations

from typing import Any, Dict, Iterable, List


class MarkdownServiceReviewReportGenerator:
    """Generates copy/pasteable operational readiness review reports."""

    def generate(self, review: Dict[str, Any]) -> str:
        scores = review.get("scores", {})
        findings = review.get("findings", [])
        approvals = review.get("approval_required_actions", [])
        lines: List[str] = []
        lines.append(f"# ARIA Service Review — {review.get('service_id')} ({review.get('environment')})")
        lines.append("")
        lines.append("## Executive Summary")
        lines.append(review.get("executive_summary", "No summary available."))
        lines.append("")
        lines.append("## Scorecard")
        lines.append("| Area | Grade | Score | Blockers |")
        lines.append("|---|---:|---:|---|")
        for name, score in scores.items():
            blockers = ", ".join(score.get("blockers", [])) or "-"
            lines.append(f"| {name} | {score.get('grade')} | {score.get('numeric_score')} | {blockers} |")
        lines.append("")
        lines.append("## Findings")
        if not findings:
            lines.append("No findings detected.")
        for finding in findings:
            lines.append(f"### {finding.get('severity')} — {finding.get('title')}")
            lines.append(f"- Category: `{finding.get('category')}`")
            lines.append(f"- Recommendation: {finding.get('recommendation', {}).get('summary', 'Review manually.')}")
            impact = finding.get("impact", {})
            if impact:
                lines.append(f"- Technical impact: {impact.get('technical_impact', '-')}")
                lines.append(f"- Business impact: {impact.get('business_impact', '-')}")
            evidence = finding.get("evidence", [])
            if evidence:
                lines.append("- Evidence:")
                for item in evidence[:5]:
                    lines.append(f"  - `{item.get('source')}:{item.get('path')}` observed `{item.get('observed')}`, expected `{item.get('expected')}`")
            lines.append("")
        lines.append("## Approval Required Actions")
        if not approvals:
            lines.append("No approval-gated actions required.")
        else:
            for approval in approvals:
                lines.append(f"- {approval.get('risk_level', 'medium').upper()}: {approval.get('reason')} — approver: {approval.get('approver_role')}")
        lines.append("")
        lines.append("## Agents")
        lines.append(f"- Ran: {', '.join(review.get('agents_run', []))}")
        lines.append(f"- Not run by design: {', '.join(review.get('agents_not_run', []))}")
        return "\n".join(lines) + "\n"
