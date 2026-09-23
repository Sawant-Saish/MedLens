from datetime import datetime

import streamlit as st

from export_builder import build_markdown_report
from models import CriticResult, NOT_SPECIFIED, SummaryResult
from pdf_export import build_summary_pdf
from ui.components import render_card

ISSUE_TYPE_LABELS = {
    "unsupported_claim": "Unsupported Claim",
    "out_of_context": "Out of Context",
    "overstated": "Overstated",
}


def _display_text(value: str) -> None:
    text = value.strip() if value and value.strip() else NOT_SPECIFIED
    if text == NOT_SPECIFIED:
        st.markdown(f"*{text}*")
    else:
        st.markdown(text)


def _display_bullets(items: list[str]) -> None:
    cleaned = [item.strip() for item in items if item and item.strip()]
    if not cleaned:
        st.markdown(f"*{NOT_SPECIFIED}*")
        return
    st.markdown("\n".join(f"- {item}" for item in cleaned))


def _format_relevance_status(status: str) -> str:
    normalized = status.strip().lower()
    if not normalized:
        return ""
    if normalized.startswith("not relevant"):
        return "❌ Not Relevant"
    if normalized.startswith("relevant"):
        return "✅ Relevant"
    return status.strip()


def _score_color(score: int) -> str:
    if score >= 80:
        return "#16a34a"
    if score >= 60:
        return "#ca8a04"
    return "#dc2626"


def _render_topic_relevance(result: SummaryResult) -> None:
    relevance = result.topic_relevance
    status_display = _format_relevance_status(relevance.status)
    justification = relevance.justification.strip() if relevance.justification else ""

    with render_card("Topic Relevance", "🔍"):
        if status_display:
            st.markdown(f"**Status:** {status_display}")
        if justification:
            st.markdown("**Justification:**")
            st.markdown(f'"{justification}"')
        if not status_display and not justification:
            st.markdown(f"*{NOT_SPECIFIED}*")


def _render_critic_score(critic: CriticResult) -> None:
    with render_card("Quality Review (Critic Score)", "📝"):
        score_color = _score_color(critic.overall_score)
        st.markdown(
            f"**Overall Score:** "
            f'<span style="color:{score_color}; font-size:1.4rem; font-weight:700;">'
            f"{critic.overall_score}/100</span>",
            unsafe_allow_html=True,
        )
        if critic.assessment:
            st.markdown(critic.assessment)

        col1, col2, col3 = st.columns(3)
        col1.metric("Factual Consistency", f"{critic.factual_consistency_score}/100")
        col2.metric("Coverage", f"{critic.coverage_score}/100")
        col3.metric("Faithfulness", f"{critic.faithfulness_score}/100")

        st.markdown("#### Flagged Issues")
        if critic.flagged_issues:
            for issue in critic.flagged_issues:
                label = ISSUE_TYPE_LABELS.get(
                    issue.issue_type,
                    issue.issue_type.replace("_", " ").title(),
                )
                st.warning(
                    f"**[{label}]** {issue.statement}\n\n*{issue.explanation}*"
                )
        else:
            st.success("No unsupported or out-of-context statements were flagged.")


def _render_download_section(
    result: SummaryResult,
    length: str,
    topic: str | None,
    source_label: str | None,
    generated_at: datetime,
    critic: CriticResult | None,
) -> None:
    st.markdown("#### Download Report")
    label = source_label or "N/A"
    markdown_report = build_markdown_report(
        result, length, topic, label, generated_at, critic
    )
    pdf_bytes = build_summary_pdf(
        result, length, topic, label, generated_at, critic
    )
    timestamp = generated_at.strftime("%Y%m%d_%H%M%S")

    col_pdf, col_md = st.columns(2)
    with col_pdf:
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=f"medlens_report_{timestamp}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
    with col_md:
        st.download_button(
            label="Download Markdown",
            data=markdown_report,
            file_name=f"medlens_report_{timestamp}.md",
            mime="text/markdown",
            use_container_width=True,
        )


def render_results(
    result: SummaryResult,
    length: str,
    topic: str | None = None,
    source_label: str | None = None,
    critic: CriticResult | None = None,
    generated_at: datetime | None = None,
) -> None:
    display_time = generated_at or datetime.now()
    st.markdown('<div class="medlens-results-section">', unsafe_allow_html=True)

    with render_card("AI Medical Literature Summary", "📋"):
        if result.title and result.title != NOT_SPECIFIED:
            st.markdown(f"**{result.title}**")
        st.markdown(f"**Summary length:** {length}")
        if source_label:
            st.markdown(f"**Sources:** {source_label}")
        if topic:
            st.markdown(f"**Topic / keyword:** {topic}")

    with render_card("Research Objective", "🎯"):
        _display_text(result.objective)

    col_study, col_population = st.columns(2)
    with col_study:
        with render_card("Study Type", "🔬"):
            _display_text(result.study_type)
    with col_population:
        with render_card("Population", "👥"):
            _display_text(result.population)

    with render_card("Methodology", "⚗️"):
        _display_text(result.methodology)

    with render_card("Key Findings", "📊"):
        _display_bullets(result.key_findings)

    with render_card("Research / Clinical Relevance", "💡"):
        _display_text(result.clinical_or_research_relevance)

    with render_card("Conclusion", "✅"):
        _display_text(result.conclusion)

    with render_card("Limitations", "⚠️"):
        _display_bullets(result.limitations)

    if topic and topic.strip():
        _render_topic_relevance(result)

    if critic:
        _render_critic_score(critic)

    _render_download_section(
        result, length, topic, source_label, display_time, critic
    )

    st.markdown("</div>", unsafe_allow_html=True)
