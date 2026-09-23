import streamlit as st

from config import MISSING_API_KEY_MESSAGE, get_openai_api_key, validate_input
from critic import generate_critique
from input_builder import build_source_label, count_sources
from llm import generate_summary
from models import HistoryEntry, SummaryGenerationError
from pdf_extractor import extract_text_from_pdfs
from ui.components import (
    inject_custom_css,
    render_footer,
    render_header,
    render_section_divider,
    show_error,
)
from ui.history import add_to_history, get_selected_entry, init_history, render_history_sidebar
from ui.input_form import render_input_form
from ui.results import render_results

st.set_page_config(page_title="MedLens", page_icon="🔬", layout="wide")
inject_custom_css()
init_history()
render_history_sidebar()

render_header()

form_data = render_input_form()

entry_to_display: HistoryEntry | None = None

if form_data.generate_clicked:
    if not get_openai_api_key():
        show_error(MISSING_API_KEY_MESSAGE)
    else:
        try:
            pdf_documents, skipped_pdfs = extract_text_from_pdfs(form_data.uploaded_pdfs)
            for filename in skipped_pdfs:
                st.warning(f"No extractable text in '{filename}'. Skipping this file.")
            validation_error, combined_text = validate_input(
                form_data.abstract, pdf_documents
            )
            if validation_error:
                show_error(validation_error)
            else:
                source_count = count_sources(form_data.abstract, pdf_documents)
                source_label = build_source_label(form_data.abstract, pdf_documents)
                spinner_label = (
                    "Extracting text, generating summary, and running quality review..."
                    if pdf_documents
                    else "Generating summary and running quality review..."
                )
                with st.spinner(spinner_label):
                    result = generate_summary(
                        combined_text,
                        form_data.summary_length,
                        form_data.topic,
                        source_count=source_count,
                    )
                    critic = generate_critique(combined_text, result)
                    entry_to_display = add_to_history(
                        combined_text,
                        form_data.summary_length,
                        form_data.topic,
                        result,
                        source_label=source_label,
                        critic=critic,
                    )
        except SummaryGenerationError as e:
            show_error(e.user_message)

if entry_to_display is None:
    entry_to_display = get_selected_entry()

if entry_to_display is not None:
    render_section_divider("Results")
    render_results(
        entry_to_display.result,
        entry_to_display.summary_length,
        entry_to_display.topic,
        source_label=entry_to_display.source_label,
        critic=entry_to_display.critic,
        generated_at=entry_to_display.timestamp,
    )

render_footer()
