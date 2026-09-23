from datetime import datetime
from io import BytesIO

from fpdf import FPDF

from models import CriticResult, NOT_SPECIFIED, SummaryResult

ISSUE_TYPE_LABELS = {
    "unsupported_claim": "Unsupported Claim",
    "out_of_context": "Out of Context",
    "overstated": "Overstated",
}


def _sanitize_text(text: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2022": "-",
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


class MedLensReportPDF(FPDF):
    def header(self) -> None:
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(30, 58, 95)
        self.cell(0, 8, "MedLens", ln=True, align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 5, "Medical Literature Summary Report", ln=True, align="C")
        self.ln(4)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-18)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(
            0,
            4,
            "MedLens is a research-assistance tool. Not for medical diagnosis or treatment.",
            align="C",
        )
        self.cell(0, 4, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str) -> None:
        self.ln(2)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(30, 58, 95)
        self.cell(0, 7, title, ln=True)
        self.set_text_color(0, 0, 0)

    def section_body(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10)
        self.multi_cell(self.epw, 5, _sanitize_text(text))
        self.ln(2)

    def bullet_list(self, items: list[str]) -> None:
        self.set_font("Helvetica", "", 10)
        if not items:
            self.set_x(self.l_margin)
            self.multi_cell(self.epw, 5, _sanitize_text(NOT_SPECIFIED))
            self.ln(2)
            return
        for item in items:
            self.set_x(self.l_margin)
            self.multi_cell(self.epw, 5, _sanitize_text(f"- {item}"))
        self.ln(2)


def build_summary_pdf(
    result: SummaryResult,
    length: str,
    topic: str | None,
    source_label: str,
    generated_at: datetime,
    critic: CriticResult | None = None,
) -> bytes:
    pdf = MedLensReportPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Report Information", ln=True)
    pdf.set_font("Helvetica", "", 10)
    metadata = [
        f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M')}",
        f"Summary Length: {length}",
        f"Sources: {source_label or 'N/A'}",
    ]
    if topic:
        metadata.append(f"Topic / Keyword: {topic}")
    for line in metadata:
        pdf.cell(0, 5, _sanitize_text(line), ln=True)
    pdf.ln(4)

    if result.title and result.title != NOT_SPECIFIED:
        pdf.section_title("Title")
        pdf.section_body(result.title)

    pdf.section_title("Research Objective")
    pdf.section_body(result.objective)

    pdf.section_title("Study Type")
    pdf.section_body(result.study_type)

    pdf.section_title("Population")
    pdf.section_body(result.population)

    pdf.section_title("Methodology")
    pdf.section_body(result.methodology)

    pdf.section_title("Key Findings")
    pdf.bullet_list(result.key_findings)

    pdf.section_title("Research / Clinical Relevance")
    pdf.section_body(result.clinical_or_research_relevance)

    pdf.section_title("Conclusion")
    pdf.section_body(result.conclusion)

    pdf.section_title("Limitations")
    pdf.bullet_list(result.limitations)

    if topic and result.topic_relevance.status:
        pdf.section_title("Topic Relevance")
        pdf.section_body(
            f"Status: {result.topic_relevance.status}\n"
            f"Justification: {result.topic_relevance.justification}"
        )

    if critic:
        pdf.add_page()
        pdf.section_title("Quality Review (Critic Score)")
        pdf.section_body(critic.assessment or "No assessment provided.")
        pdf.set_font("Helvetica", "", 10)
        scores = [
            ("Overall Score", critic.overall_score),
            ("Factual Consistency", critic.factual_consistency_score),
            ("Coverage", critic.coverage_score),
            ("Faithfulness", critic.faithfulness_score),
        ]
        for label, score in scores:
            pdf.cell(60, 6, _sanitize_text(label), border=0)
            pdf.cell(0, 6, _sanitize_text(f"{score} / 100"), ln=True)

        pdf.ln(3)
        pdf.section_title("Flagged Issues")
        if critic.flagged_issues:
            for issue in critic.flagged_issues:
                issue_label = ISSUE_TYPE_LABELS.get(
                    issue.issue_type, issue.issue_type.replace("_", " ").title()
                )
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "B", 10)
                pdf.multi_cell(
                    pdf.epw, 5, _sanitize_text(f"[{issue_label}] {issue.statement}")
                )
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "I", 9)
                pdf.multi_cell(pdf.epw, 5, _sanitize_text(issue.explanation))
                pdf.ln(2)
        else:
            pdf.section_body("No unsupported or out-of-context statements were flagged.")

    buffer = BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
