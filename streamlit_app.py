import json
import re
import streamlit as st

from app.logging_config import setup_pipeline_logging
from app.services.answer_service import answer_question
from app.services.storage.db import get_raw_collection

setup_pipeline_logging()

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Meeting Intelligence",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Intent metadata ────────────────────────────────────────────────────────────
INTENT_META = {
    "decision_query":      {"label": "Decision",      "color": "#1E40AF", "bg": "#DBEAFE", "emoji": "🔵"},
    "commitment_query":    {"label": "Action Item",   "color": "#92400E", "bg": "#FEF3C7", "emoji": "🟠"},
    "question_query":      {"label": "Questions",     "color": "#5B21B6", "bg": "#EDE9FE", "emoji": "🟣"},
    "summary_query":       {"label": "Summary",       "color": "#065F46", "bg": "#D1FAE5", "emoji": "🟢"},
    "speaker_query":       {"label": "Speaker",       "color": "#0E7490", "bg": "#CFFAFE", "emoji": "🔷"},
    "timeline_query":      {"label": "Timeline",      "color": "#78350F", "bg": "#FEF9C3", "emoji": "🟡"},
    "analytical_query":    {"label": "Analytics",     "color": "#4D7C0F", "bg": "#ECFCCB", "emoji": "📊"},
    "attribution_query":   {"label": "Attribution",   "color": "#6D28D9", "bg": "#EDE9FE", "emoji": "🔍"},
    "contribution_query":  {"label": "Contribution",  "color": "#0369A1", "bg": "#E0F2FE", "emoji": "📈"},
    "topic_summary_query": {"label": "Topic Summary", "color": "#065F46", "bg": "#CCFBF1", "emoji": "📝"},
    "general_query":       {"label": "General",       "color": "#374151", "bg": "#F3F4F6", "emoji": "⚫"},
}

EXAMPLE_QUESTIONS = [
    "Give me a summary of the project so far",
    "What was decided about the ONCA forecasting numbers?",
    "What did Bhavneet say about the timeline?",
    "What action items were assigned and who is responsible?",
    "What did Harsh Vardhan explain about the two AI approaches?",
    "What did Ashpreet say about the multi-agent architecture?",
]

# ── Data helpers ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_projects() -> dict:
    with open("projects.json", "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=120)
def get_project_stats(project_id: str) -> dict:
    try:
        collection = get_raw_collection()
        results = collection.get(
            where={"project_id": {"$eq": project_id}},
            include=["metadatas"],
        )
        metas = results.get("metadatas", [])
        meetings = sorted(
            {(m.get("meeting_title", ""), m.get("meeting_date", ""))
             for m in metas if m.get("meeting_id") and not m.get("is_meeting_summary")},
            key=lambda x: x[1],
        )
        speakers = sorted({
            m.get("speaker_name")
            for m in metas
            if m.get("speaker_name") and not m.get("is_meeting_summary")
        })
        return {
            "chunk_count": len([m for m in metas if not m.get("is_meeting_summary")]),
            "meeting_count": len(meetings),
            "speaker_count": len(speakers),
            "meetings": meetings,
            "speakers": speakers,
        }
    except Exception:
        return {"chunk_count": 0, "meeting_count": 0, "speaker_count": 0,
                "meetings": [], "speakers": []}


# ── Render helpers ─────────────────────────────────────────────────────────────
def intent_badge_html(intent: str) -> str:
    m = INTENT_META.get(intent, INTENT_META["general_query"])
    return (
        f'<span style="background:{m["bg"]};color:{m["color"]};'
        f'padding:3px 12px;border-radius:999px;font-size:12px;font-weight:600;">'
        f'{m["emoji"]} {m["label"]}</span>'
    )


def _linkify_citations(text: str, num_sources: int) -> str:
    """
    Convert inline [n] citation markers into anchor links, then convert
    markdown bullet lines (- item or * item) into HTML <ul><li> so they render
    correctly when the whole block is passed to st.markdown(unsafe_allow_html=True).
    Without this, mixing HTML <a> tags with markdown bullets breaks rendering.
    Single newlines are converted to <br> so numbered list items and sub-bullets
    never collapse into one run-on paragraph.
    """
    def replacer(m):
        n = int(m.group(1))
        if 1 <= n <= num_sources:
            return (
                f'<a href="#src-{n}" '
                f'style="color:#2563EB;font-weight:700;font-size:0.82em;'
                f'text-decoration:none;vertical-align:super;">[{n}]</a>'
            )
        return m.group(0)
    # Match [n] (1–3 digits) that is NOT followed by a colon (timestamps are [16:39] style)
    text = re.sub(r'\[(\d{1,3})\](?!:)', replacer, text)

    # Convert markdown bullet lines (- or *) into HTML list so they survive unsafe_allow_html
    lines = text.split('\n')
    out, in_list = [], False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                out.append('<ul style="margin:0.4em 0 0.4em 1.2em;padding:0;">')
                in_list = True
            out.append(f'<li style="margin-bottom:0.3em;">{stripped[2:]}</li>')
        else:
            if in_list:
                out.append('</ul>')
                in_list = False
            out.append(line)
    if in_list:
        out.append('</ul>')

    # Convert all newlines to <br> so numbered items and sub-bullets never
    # collapse into a single paragraph under unsafe_allow_html rendering.
    result = '\n'.join(out)
    result = re.sub(r'\n{2,}', '<br><br>', result)
    result = result.replace('\n', '<br>')
    return result


def render_sources(sources: list[dict]):
    if not sources:
        return
    with st.expander(f"📎 {len(sources)} source{'s' if len(sources) > 1 else ''}", expanded=True):
        for i, s in enumerate(sources):
            # Use chunk_num so the anchor id matches the [n] citation the LLM wrote.
            # e.g. LLM wrote [6] → anchor id="src-6" → clicking scrolls here.
            anchor_id = s.get("chunk_num", i + 1)
            display_n = s.get("chunk_num", i + 1)
            st.markdown(f'<div id="src-{anchor_id}"></div>', unsafe_allow_html=True)

            ts_str = f" &nbsp;·&nbsp; ⏱ `{s['timestamp']}`" if s.get("timestamp") else ""

            if s.get("is_summary"):
                st.markdown(
                    f"**[{display_n}] 📋 Meeting Summary** &nbsp;·&nbsp; "
                    f"📅 {s['meeting_title']} &nbsp;·&nbsp; "
                    f"`{s['meeting_date']}`"
                    + ts_str
                )
            else:
                st.markdown(
                    f"**[{display_n}] {s['speaker_name']}** &nbsp;·&nbsp; "
                    f"📅 {s['meeting_title']} &nbsp;·&nbsp; "
                    f"`{s['meeting_date']}`"
                    + ts_str,
                    unsafe_allow_html=True,
                )
            if s.get("content_preview"):
                st.caption(f"❝ {s['content_preview']}{'…' if len(s.get('content_preview','')) == 200 else ''}")
            if i < len(sources) - 1:
                st.divider()


_NOT_FOUND_PREFIXES = ("No meeting was found", "I couldn't find relevant")

def render_chat_message(msg: dict):
    with st.chat_message("user"):
        st.markdown(msg["question"])
    with st.chat_message("assistant"):
        st.markdown(intent_badge_html(msg["intent"]), unsafe_allow_html=True)

        # Show approximate-date notice above the answer
        if msg.get("notice"):
            st.info(msg["notice"], icon="📅")

        answer = msg["answer"]
        sources = msg["sources"]

        if any(answer.startswith(p) for p in _NOT_FOUND_PREFIXES):
            st.warning(answer, icon="⚠️")
        elif sources:
            # Use total context chunk count as the ceiling so citations like [6], [8]
            # are converted to links even when there are fewer deduplicated sources.
            num_ctx = msg.get("num_context_chunks", len(sources))
            st.markdown(_linkify_citations(answer, num_ctx), unsafe_allow_html=True)
        else:
            st.markdown(answer)

        render_sources(sources)


def ask_and_store(question: str, project_id: str):
    try:
        result = answer_question(question, project_id)
        st.session_state.messages.append({
            "question":           question,
            "answer":             result["answer"],
            "intent":             result["intent"],
            "sources":            result["sources"],
            "notice":             result.get("notice"),
            "num_context_chunks": result.get("num_context_chunks", len(result["sources"])),
        })
    except Exception as e:
        st.session_state.messages.append({
            "question":           question,
            "answer":             f"Something went wrong: {str(e)}",
            "intent":             "general_query",
            "sources":            [],
            "notice":             None,
            "num_context_chunks": 0,
        })


# ── Session state init ─────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = None

# ── Load data ──────────────────────────────────────────────────────────────────
projects = load_projects()
project_names = {v["project_name"]: k for k, v in projects.items()}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 AI Meeting Intel")
    st.caption("Ask questions about past meetings.")
    st.divider()

    # Project selector
    selected_name = st.selectbox("Project", options=list(project_names.keys()))
    selected_id = project_names[selected_name]

    # Clear chat and cache when project changes
    if st.session_state.active_project_id != selected_id:
        st.session_state.active_project_id = selected_id
        st.session_state.messages = []
        st.cache_data.clear()

    st.divider()

    # Stats
    stats = get_project_stats(selected_id)
    c1, c2, c3 = st.columns(3)
    c1.metric("Meetings", stats["meeting_count"])
    c2.metric("Speakers", stats["speaker_count"])
    c3.metric("Chunks", stats["chunk_count"])

    st.divider()

    # Meetings
    if stats["meetings"]:
        st.markdown("**📅 Meetings**")
        for title, date in stats["meetings"]:
            st.markdown(f"- {title}  \n  `{date}`")

    st.divider()

    # Speakers
    if stats["speakers"]:
        st.markdown("**👥 Speakers**")
        speaker_roles = projects.get(selected_id, {}).get("speakers", {})
        role_icon = {"client": "🔴", "project_manager": "🟡", "developer": "🔵"}
        for speaker in stats["speakers"]:
            role = speaker_roles.get(speaker, "unknown")
            icon = role_icon.get(role, "⚪")
            st.markdown(f"{icon} {speaker}")

    st.divider()

    # Query type guide
    with st.expander("💡 What can I ask?"):
        st.markdown("""
**🔵 Decisions**
> What was decided about the ONCA numbers?

**🟠 Action Items**
> What did Project Manager SFS commit to?

**🟢 Summary**
> Give me a summary of the project so far

**🟣 Questions Raised**
> What questions did Bhavneet raise?

**🔷 Speaker**
> What did Harsh Vardhan explain about the AI approaches?

**🟡 Timeline**
> What is the deadline for the forecast module?

**⚫ General**
> What was discussed about the stress test?
        """)

    st.divider()

    col_a, col_b = st.columns(2)
    if col_a.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if col_b.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Main area ──────────────────────────────────────────────────────────────────
st.markdown(
    f"### AI Meeting Intelligence &nbsp;&nbsp;"
    f'<span style="font-size:14px;color:#6B7280;font-weight:400;">— {selected_name}</span>',
    unsafe_allow_html=True,
)
st.caption("Answers are grounded in real transcript data. Every response includes the source meeting and speaker.")
st.divider()

# Render existing chat history
for msg in st.session_state.messages:
    render_chat_message(msg)

# Empty state — show example question buttons
if not st.session_state.messages:
    st.markdown("#### Ask a question or try one of these:")
    st.markdown("")
    cols = st.columns(3)
    for i, question in enumerate(EXAMPLE_QUESTIONS):
        with cols[i % 3]:
            if st.button(question, key=f"ex_{i}", use_container_width=True):
                with st.spinner("Thinking..."):
                    ask_and_store(question, selected_id)
                st.rerun()

# Chat input
if prompt := st.chat_input(f"Ask anything about {selected_name} meetings..."):
    with st.spinner("Thinking..."):
        ask_and_store(prompt, selected_id)
    st.rerun()
