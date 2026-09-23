from datetime import datetime

import streamlit as st

from models import CriticResult, MAX_HISTORY_ENTRIES, HistoryEntry, SummaryResult


def init_history() -> None:
    if "history" not in st.session_state:
        st.session_state.history = []
    if "selected_entry_index" not in st.session_state:
        st.session_state.selected_entry_index = None


def _abstract_preview(abstract: str, max_length: int = 100) -> str:
    text = abstract.strip()
    if len(text) <= max_length:
        return text
    return f"{text[:max_length]}..."


def add_to_history(
    abstract: str,
    summary_length: str,
    topic: str | None,
    result: SummaryResult,
    source_label: str = "",
    critic: CriticResult | None = None,
) -> HistoryEntry:
    entry = HistoryEntry(
        timestamp=datetime.now(),
        abstract_preview=_abstract_preview(abstract),
        summary_length=summary_length,
        topic=topic,
        result=result,
        source_label=source_label,
        critic=critic,
    )
    st.session_state.history.insert(0, entry)
    st.session_state.history = st.session_state.history[:MAX_HISTORY_ENTRIES]
    st.session_state.selected_entry_index = 0
    return entry


def get_selected_entry() -> HistoryEntry | None:
    index = st.session_state.selected_entry_index
    if index is None:
        return None
    history = st.session_state.history
    if 0 <= index < len(history):
        return history[index]
    return None


def render_history_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Recent Summaries")

        if not st.session_state.history:
            st.caption("No summaries yet. Generate one to see it here.")
            return

        for index, entry in enumerate(st.session_state.history):
            time_label = entry.timestamp.strftime("%H:%M:%S")
            topic_label = f" · {entry.topic}" if entry.topic else ""
            button_label = f"{time_label} · {entry.summary_length}{topic_label}"

            if st.button(
                button_label,
                key=f"history_entry_{index}",
                use_container_width=True,
            ):
                st.session_state.selected_entry_index = index

            st.caption(entry.abstract_preview)
            st.divider()
