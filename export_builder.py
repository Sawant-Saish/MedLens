from datetime import datetime

from models import CriticResult, NOT_SPECIFIED, SummaryResult

ISSUE_TYPE_LABELS = {
    "unsupported_claim": "Unsupported Claim",
    "out_of_context": "Out of Context",
    "overstated": "Overstated",
}


def build_markdown_report(
    result: SummaryResult,
    length: str,
    topic: str | None,
    source_label: str,
    generated_at: datetime,
    critic: CriticResult | None = None,
) -> str:
    lines = [
        "# MedLens — Medical Literature Summary Report",
        "",
        f"**Generated:** {generated_at.strftime('%Y-%m-%d %H:%M')}",
        f"**Summary Length:** {length}",
        f"**Sources:** {source_label or 'N/A'}",
    ]
    if topic:
        lines.append(f"**Topic / Keyword:** {topic}")
    lines.extend(["", "---", ""])

    if result.title and result.title != NOT_SPECIFIED:
        lines.extend([f"## Title\n\n{result.title}", ""])

    sections = [
        ("Research Objective", result.objective),
        ("Study Type", result.study_type),
        ("Population", result.population),
        ("Methodology", result.methodology),
        ("Research / Clinical Relevance", result.clinical_or_research_relevance),
        ("Conclusion", result.conclusion),
    ]
    for title, content in sections:
        lines.extend([f"## {title}", "", content or NOT_SPECIFIED, ""])

    lines.append("## Key Findings")
    lines.append("")
    if result.key_findings:
        lines.extend(f"- {item}" for item in result.key_findings)
    else:
        lines.append(f"*{NOT_SPECIFIED}*")
    lines.append("")

    lines.append("## Limitations")
    lines.append("")
    if result.limitations:
        lines.extend(f"- {item}" for item in result.limitations)
    else:
        lines.append(f"*{NOT_SPECIFIED}*")
    lines.append("")

    if topic and result.topic_relevance.status:
        lines.extend([
            "## Topic Relevance",
            "",
            f"**Status:** {result.topic_relevance.status}",
            f"**Justification:** {result.topic_relevance.justification}",
            "",
        ])

    if critic:
        lines.extend([
            "---",
            "",
            "## Quality Review (Critic Score)",
            "",
            critic.assessment or "No assessment provided.",
            "",
            f"- **Overall Score:** {critic.overall_score} / 100",
            f"- **Factual Consistency:** {critic.factual_consistency_score} / 100",
            f"- **Coverage:** {critic.coverage_score} / 100",
            f"- **Faithfulness:** {critic.faithfulness_score} / 100",
            "",
            "### Flagged Issues",
            "",
        ])
        if critic.flagged_issues:
            for issue in critic.flagged_issues:
                label = ISSUE_TYPE_LABELS.get(
                    issue.issue_type, issue.issue_type.replace("_", " ").title()
                )
                lines.extend([
                    f"**[{label}]** {issue.statement}",
                    f"> {issue.explanation}",
                    "",
                ])
        else:
            lines.append("No unsupported or out-of-context statements were flagged.")
        lines.append("")

    lines.extend([
        "---",
        "",
        "*MedLens is a research-assistance tool. Not for medical diagnosis or treatment.*",
    ])
    return "\n".join(lines)
