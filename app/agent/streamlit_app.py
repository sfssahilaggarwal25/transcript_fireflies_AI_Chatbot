"""
production/streamlit_app.py — Production LangGraph Agent · Streamlit UI

Chat interface for the production pipeline only.

Features
--------
  - Live tool-call progress via graph.stream() — shows which tool is
    running, its arguments, and the first line of each result in real time.
  - Chunk citations panel below every answer — speaker, meeting, timestamp,
    content preview for each retrieved chunk.
  - Collapsed tool-trace expander showing the full agent reasoning path.
  - Project/meeting/speaker sidebar with live stats.

Run
---
  streamlit run production/streamlit_app.py
"""

import json
import re
import sys
import time
from pathlib import Path

# ── sys.path: project root must be on the path before any imports ─────────────
_PROJECT_ROOT = Path(__file__).parent.parent.parent   # app/agent/ → app/ → project root
sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.agent import get_graph, reset_doc_accumulator, get_accumulated_docs
from app.agent.service import _build_sources, _extract_tool_calls
from app.core.storage.db import get_raw_collection


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Meeting Intelligence · Production",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Constants ─────────────────────────────────────────────────────────────────

TOOL_META = {
    "search_transcripts":    {"icon": "🔍", "label": "Search Transcripts"},
    "get_meeting_summaries": {"icon": "📋", "label": "Get Meeting Summaries"},
    "list_meetings":         {"icon": "📅", "label": "List Meetings"},
    "list_speakers":         {"icon": "👥", "label": "List Speakers"},
    "count_signal_chunks":   {"icon": "🔢", "label": "Count Signal Chunks"},
}

ROLE_ICON = {
    "client":          "🔴",
    "project_manager": "🟡",
    "developer":       "🔵",
}

EXAMPLE_QUESTIONS = [
    "Summarize AI architecture discussions across all meetings",
    "What questions did Harsh Vardhan raise about AI architecture?",
    "What did Bhavneet commit to in the previous meeting?",
    "How many commitments were made across this project?",
    "What issues were raised about formulas in the last meeting?",
    "Who spoke the most in this project?",
]


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Tool call progress rows */
.tool-row {
    background: #F8FAFC;
    border-left: 3px solid #3B82F6;
    padding: 6px 12px;
    margin: 4px 0;
    border-radius: 0 6px 6px 0;
    font-size: 0.88em;
}
.tool-result {
    color: #6B7280;
    font-size: 0.82em;
    padding-left: 20px;
    margin-bottom: 2px;
}
/* Citation cards */
.citation-card {
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
}
/* Scope badge */
.scope-badge {
    display: inline-block;
    background: #DBEAFE;
    color: #1E40AF;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 0.78em;
    font-weight: 600;
    margin-bottom: 8px;
}
/* Citation anchor scroll offset — keeps the target card fully visible below
   Streamlit's sticky header when the user clicks a [N] citation link. */
[id^="src-"] {
    scroll-margin-top: 80px;
}
</style>
""", unsafe_allow_html=True)


# ── Data helpers ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=120)
def load_projects() -> dict:
    with open(_PROJECT_ROOT / "projects.json", "r", encoding="utf-8") as f:
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

        meetings: dict = {}
        speakers: dict = {}
        for m in metas:
            if m.get("is_meeting_summary"):
                continue
            mid = m.get("meeting_id")
            if mid and mid not in meetings:
                meetings[mid] = {
                    "num":   m.get("meeting_number", 0),
                    "title": m.get("meeting_title", "Unknown"),
                    "date":  m.get("meeting_date", ""),
                }
            name = m.get("speaker_name")
            if name and name not in speakers:
                speakers[name] = m.get("speaker_role", "unknown")

        sorted_meetings = sorted(meetings.values(), key=lambda x: x["date"])
        return {
            "chunk_count":   len([m for m in metas if not m.get("is_meeting_summary")]),
            "meeting_count": len(meetings),
            "speaker_count": len(speakers),
            "meetings":      sorted_meetings,
            "speakers":      speakers,
        }
    except Exception as e:
        st.error(f"[DEBUG] get_project_stats failed: {e}")
        return {
            "chunk_count": 0, "meeting_count": 0, "speaker_count": 0,
            "meetings": [], "speakers": {},
        }


def _scope_label(scope_type: str, scope_ids, project_id: str) -> str:
    """Resolve scope to a human-readable label for the UI."""
    if scope_type == "project" or not scope_ids:
        return "All meetings (project-wide)"
    if scope_type == "date_range":
        return "Date-range filtered"
    # scope_type == "meeting" — resolve IDs to titles
    try:
        collection = get_raw_collection()
        labels = []
        for mid in scope_ids:
            res = collection.get(
                where={"$and": [
                    {"project_id": {"$eq": project_id}},
                    {"meeting_id": {"$eq": mid}},
                ]},
                include=["metadatas"],
                limit=1,
            )
            m = (res.get("metadatas") or [{}])[0]
            title = m.get("meeting_title", mid)
            date  = m.get("meeting_date", "")
            num   = m.get("meeting_number", "")
            labels.append(f"Meeting #{num}: {title} ({date})")
        return ", ".join(labels)
    except Exception:
        return f"{len(scope_ids)} meeting(s)"


def _fmt_tool_args(args: dict) -> str:
    """Compact readable summary of tool arguments for the progress display."""
    parts = []
    if "query" in args:
        parts.append(f'"{args["query"]}"')
    if "speaker_name" in args:
        parts.append(f'speaker: {args["speaker_name"]}')
    if "signal_filter" in args:
        parts.append(f'signal: {args["signal_filter"]}')
    if "k" in args and int(args["k"]) != 15:
        parts.append(f'k={args["k"]}')
    if "meeting_title" in args and args["meeting_title"]:
        parts.append(f'meeting: {args["meeting_title"]}')
    return " · ".join(parts) if parts else "(auto-scoped)"


# ── Citation linkifier ────────────────────────────────────────────────────────

def _linkify_citations(text: str, num_chunks: int) -> str:
    """
    Convert the LLM answer (markdown + [N] citations) into pure HTML.

    WHY full conversion is required
    --------------------------------
    st.markdown(text, unsafe_allow_html=True) stops processing markdown syntax
    (**bold**, - bullets) the moment it encounters any block-level HTML element
    (like <ul> or <a>). This causes **headings** to render as literal asterisks
    and bold text inside <li> items to disappear.

    The only reliable fix is to convert EVERY markdown construct to HTML ourselves
    so no markdown syntax survives — Streamlit just renders the resulting HTML.

    Conversion pipeline
    -------------------
    1. [N]       → <a href="#src-N"> superscript citation links
    2. **text**  → <strong>text</strong>   (inline bold AND section headings)
    3. Line scan:
       a. Standalone <strong>heading</strong> line → styled <p> heading block
       b. Consecutive - / * bullet lines       → compact single-line <ul><li>
       c. Consecutive regular text lines        → <p> with <br> between lines
       d. Empty lines                           → paragraph separator (skipped;
                                                  margins on blocks provide spacing)
    """
    # ── 1. [N] → anchor link ─────────────────────────────────────────────────
    # Timestamps like [02:34] are safe — the colon inside the brackets means
    # \[(\d{1,3})\] never matches them (it requires ] immediately after the digits).
    def _replacer(m):
        n = int(m.group(1))
        if 1 <= n <= num_chunks:
            return (
                f'<a href="#src-{n}" '
                f'style="color:#2563EB;font-weight:700;font-size:0.82em;'
                f'text-decoration:none;vertical-align:super;">[{n}]</a>'
            )
        return m.group(0)
    text = re.sub(r'\[(\d{1,3})\]', _replacer, text)

    # ── 2. **text** → <strong>text</strong> ─────────────────────────────────
    # Must run BEFORE the line scan so bold text inside bullet items is already
    # HTML when the <li> element is built. re.sub without DOTALL means . never
    # crosses newlines — **heading** only matches on a single line.
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

    # ── 3. Line-by-line structural conversion ────────────────────────────────
    lines    = text.split('\n')
    segments: list[str] = []
    i = 0

    def _is_bold_heading(s: str) -> bool:
        """True when the entire stripped string is <strong>…</strong> — a section heading."""
        return bool(re.match(r'^<strong>.+</strong>$', s.strip()))

    def _heading_html(content: str) -> str:
        return (
            f'<p style="font-weight:700;font-size:1.0em;'
            f'margin:0.9em 0 0.2em 0;padding:0;">{content.strip()}</p>'
        )

    while i < len(lines):
        raw      = lines[i]
        stripped = raw.strip()

        # 3d. Empty line
        if not stripped:
            i += 1
            continue

        # 3a. Standalone heading: entire line is <strong>…</strong>
        if _is_bold_heading(stripped):
            segments.append(_heading_html(stripped))
            i += 1
            continue

        # 3b. Bullet or heading-bullet
        if stripped.startswith('- ') or stripped.startswith('* '):
            content = stripped[2:].strip()

            # Heading-bullet: "- **Section Title**" — the entire bullet body is bold.
            # Promote to a heading <p> (no bullet dot) so headings are visually
            # distinct from the sub-items that follow them.
            if _is_bold_heading(content):
                segments.append(_heading_html(content))
                i += 1
                continue

            # Regular bullet list — collect consecutive non-heading bullet lines.
            # Stop as soon as a heading-bullet is encountered so it gets its own <p>.
            items: list[str] = []
            while i < len(lines):
                s = lines[i].strip()
                if not (s.startswith('- ') or s.startswith('* ')):
                    break                                   # non-bullet line
                c = s[2:].strip()
                if _is_bold_heading(c):
                    break                                   # heading-bullet → end list
                items.append(f'<li style="margin-bottom:0.3em;">{c}</li>')
                i += 1
            if items:
                segments.append(
                    '<ul style="margin:0.4em 0 0.5em 1.2em;padding:0;">'
                    + ''.join(items)
                    + '</ul>'
                )
            continue

        # 3c. Regular text paragraph — collect consecutive non-special lines.
        para: list[str] = []
        while i < len(lines):
            s = lines[i].strip()
            if not s:                                       # blank → end paragraph
                break
            if s.startswith('- ') or s.startswith('* '):   # bullet → new block
                break
            if _is_bold_heading(s):                        # heading → new block
                break
            para.append(s)
            i += 1
        if para:
            segments.append(
                '<p style="margin:0.3em 0;">'
                + '<br>'.join(para)
                + '</p>'
            )

    return '\n'.join(segments)


# ── Render helpers ────────────────────────────────────────────────────────────

def render_sources(sources: list[dict]):
    """
    Render chunk citations below the answer.
    Each source shows: speaker, meeting, date, timestamp, content preview.
    """
    if not sources:
        return

    with st.expander(
        f"📎 {len(sources)} source{'s' if len(sources) > 1 else ''}",
        expanded=True,
    ):
        for i, s in enumerate(sources):
            anchor_id = s.get("chunk_num", i + 1)
            display_n = s.get("chunk_num", i + 1)

            # Anchor div so [N] links in answer can scroll here
            st.markdown(f'<div id="src-{anchor_id}"></div>', unsafe_allow_html=True)

            ts_str = f" &nbsp;·&nbsp; ⏱ `{s['timestamp']}`" if s.get("timestamp") else ""

            if s.get("is_summary"):
                header = (
                    f"**[{display_n}] 📋 Meeting Summary** &nbsp;·&nbsp; "
                    f"📅 {s['meeting_title']} &nbsp;·&nbsp; "
                    f"`{s['meeting_date']}`" + ts_str
                )
            else:
                header = (
                    f"**[{display_n}] 👤 {s['speaker_name']}** &nbsp;·&nbsp; "
                    f"📅 {s['meeting_title']} &nbsp;·&nbsp; "
                    f"`{s['meeting_date']}`" + ts_str
                )

            st.markdown(header, unsafe_allow_html=True)

            if s.get("content_preview"):
                preview = s["content_preview"]
                suffix  = "…" if len(preview) >= 200 else ""
                st.caption(f"❝ {preview}{suffix}")

            if i < len(sources) - 1:
                st.divider()


def render_tool_trace(tool_calls: list[dict]):
    """
    Collapsed expander showing all tool calls the agent made.
    Visible after the answer — user can expand to see the reasoning path.
    """
    if not tool_calls:
        return
    n = len(tool_calls)
    label = f"🛠️ Agent used {n} tool call{'s' if n > 1 else ''}"
    with st.expander(label, expanded=False):
        for i, tc in enumerate(tool_calls, 1):
            meta    = TOOL_META.get(tc["tool"], {"icon": "🔧", "label": tc["tool"]})
            args_str = _fmt_tool_args(tc.get("args", {}))
            st.markdown(f"**{i}. {meta['icon']} {meta['label']}** &nbsp;—&nbsp; {args_str}", unsafe_allow_html=True)


def render_chat_history(msg: dict):
    """Render a stored chat message (from session_state) without re-running."""
    with st.chat_message("user"):
        st.markdown(msg["question"])
    with st.chat_message("assistant"):
        num_chunks = msg.get("num_context_chunks", len(msg.get("sources", [])))
        st.markdown(_linkify_citations(msg["answer"], num_chunks), unsafe_allow_html=True)
        render_sources(msg.get("sources", []))
        render_tool_trace(msg.get("tool_calls", []))


# ── Core: streaming graph run ─────────────────────────────────────────────────

def run_and_stream(query: str, project_id: str) -> dict:
    """
    Invoke the LangGraph agent using graph.stream() so the UI updates live.

    Streaming behaviour:
      query_scope node  → shows scope resolved (meeting name or "all meetings")
      agent node        → shows each tool call + its arguments as LLM decides them
      tools node        → shows first line of each tool result (Found N chunks…)
      final agent node  → no tool_calls → answer generated, status closes

    Returns the same dict shape as service.answer_query():
      answer, sources, tool_calls, num_context_chunks, error
    """
    reset_doc_accumulator()
    graph = get_graph()

    initial_state = {
        "messages":      [HumanMessage(content=query)],
        "project_id":    project_id,
        "scope_where":   None,
        "scope_ids":     None,
        "scope_type":    "project",
        "recommended_k": 15,
    }

    t_start      = time.time()
    all_messages: list = []   # accumulated across all node updates (add_messages reducer)
    error: str | None  = None

    try:
        # st.status() shows a live spinner that collapses to "Done in Xs" on completion.
        with st.status("🤖 Agent thinking...", expanded=True) as status:

            for chunk in graph.stream(initial_state):
                for node_name, node_output in chunk.items():

                    # ── Accumulate messages ──────────────────────────────────
                    # add_messages reducer means each node only emits NEW messages.
                    # We extend our local list to get the full thread.
                    for msg in node_output.get("messages", []):
                        all_messages.append(msg)

                    # ── query_scope: show resolved scope ─────────────────────
                    if node_name == "query_scope":
                        scope_type = node_output.get("scope_type", "project")
                        scope_ids  = node_output.get("scope_ids")
                        label      = _scope_label(scope_type, scope_ids, project_id)
                        st.write(f"✅ **Scope:** {label}")

                    # ── agent: show each tool call the LLM decided to make ───
                    elif node_name == "agent":
                        for msg in node_output.get("messages", []):
                            if isinstance(msg, AIMessage):
                                for tc in getattr(msg, "tool_calls", []):
                                    args     = {k: v for k, v in tc["args"].items() if k != "state"}
                                    meta     = TOOL_META.get(tc["name"], {"icon": "🔧", "label": tc["name"]})
                                    args_str = _fmt_tool_args(args)
                                    st.write(f"{meta['icon']} **{meta['label']}** — {args_str}")

                    # ── tools: show first line of each tool result ───────────
                    elif node_name == "tools":
                        for msg in node_output.get("messages", []):
                            if isinstance(msg, ToolMessage) and msg.content:
                                first_line = msg.content.split("\n")[0].strip()
                                if first_line:
                                    st.write(f"&nbsp;&nbsp;&nbsp;↳ {first_line[:130]}")

            elapsed = round(time.time() - t_start, 1)
            status.update(
                label=f"✅ Done in {elapsed}s",
                state="complete",
                expanded=False,
            )

    except Exception as exc:
        error = str(exc)
        st.error(f"Agent error: {exc}", icon="❌")

    # ── Extract final answer ──────────────────────────────────────────────────
    answer = ""
    for msg in reversed(all_messages):
        if isinstance(msg, AIMessage) and msg.content:
            raw = msg.content
            if isinstance(raw, str):
                answer = raw
            elif isinstance(raw, list):
                # Gemini extended-thinking: content is a list of typed blocks
                text_parts = [
                    b["text"] for b in raw
                    if isinstance(b, dict) and b.get("type") == "text"
                ]
                answer = "\n".join(text_parts).strip()
            if answer:
                break

    if not answer and not error:
        answer = "I could not generate an answer. Please try rephrasing your question."

    # ── Build sources from accumulated docs ───────────────────────────────────
    docs       = get_accumulated_docs()
    sources    = _build_sources(docs)
    tool_calls = _extract_tool_calls(all_messages)

    return {
        "answer":             answer,
        "sources":            sources,
        "tool_calls":         tool_calls,
        "num_context_chunks": len(docs),
        "error":              error,
    }


# ── Session state init ────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_project_id" not in st.session_state:
    st.session_state.active_project_id = None


# ── Load project list ─────────────────────────────────────────────────────────
projects      = load_projects()
project_names = {v["project_name"]: k for k, v in projects.items()}


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🚀 AI Meeting Intel")
    st.caption("Production LangGraph Agent")
    st.divider()

    selected_name = st.selectbox("Project", options=list(project_names.keys()))
    selected_id   = project_names[selected_name]

    # Clear chat when project changes
    if st.session_state.active_project_id != selected_id:
        st.session_state.active_project_id = selected_id
        st.session_state.messages = []
        st.cache_data.clear()

    st.divider()

    # Project stats
    stats = get_project_stats(selected_id)
    c1, c2, c3 = st.columns(3)
    c1.metric("Meetings",  stats["meeting_count"])
    c2.metric("Speakers",  stats["speaker_count"])
    c3.metric("Chunks",    stats["chunk_count"])

    st.divider()

    # Meeting list
    if stats["meetings"]:
        st.markdown("**📅 Meetings**")
        for m in stats["meetings"]:
            st.markdown(f"- **#{m['num']}** {m['title']}  \n  `{m['date']}`")

    st.divider()

    # Speaker list with role icons
    if stats["speakers"]:
        st.markdown("**👥 Speakers**")
        for name, role in sorted(stats["speakers"].items()):
            icon = ROLE_ICON.get(role, "⚪")
            st.markdown(f"{icon} {name}")

    st.divider()

    # Quick-start guide
    with st.expander("💡 What can I ask?", expanded=False):
        st.markdown("""
**🔍 Specific content**
> What questions did Harsh raise about AI?

**📋 Meeting overviews**
> What was discussed in the previous meeting?

**🔢 Counts**
> How many commitments were made in this project?

**👥 Speaker focus**
> Who spoke the most? What did Bhavneet commit to?

**📅 Cross-meeting**
> What was decided in the last 3 meetings?

**📎 Documents**
> What files were shared by the client?
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
    f"### 🚀 AI Meeting Intelligence"
    f"&nbsp;&nbsp;"
    f'<span style="font-size:14px;color:#6B7280;font-weight:400;">'
    f"Production Agent — {selected_name}"
    f"</span>",
    unsafe_allow_html=True,
)
st.caption(
    "Multi-hop LangGraph agent · Gemini 2.5 Flash · "
    "Hybrid retrieval (dense + BM25 + RRF) · Live tool progress"
)
st.divider()

# ── Render chat history ───────────────────────────────────────────────────────
for msg in st.session_state.messages:
    render_chat_history(msg)


# ── Empty state: example question buttons ────────────────────────────────────
if not st.session_state.messages:
    st.markdown("#### Ask a question or try one of these:")
    cols = st.columns(3)
    for i, question in enumerate(EXAMPLE_QUESTIONS):
        with cols[i % 3]:
            if st.button(question, key=f"ex_{i}", use_container_width=True):
                with st.chat_message("user"):
                    st.markdown(question)
                with st.chat_message("assistant"):
                    result = run_and_stream(question, selected_id)
                    st.markdown(
                        _linkify_citations(result["answer"], result["num_context_chunks"]),
                        unsafe_allow_html=True,
                    )
                    render_sources(result["sources"])
                    render_tool_trace(result["tool_calls"])
                st.session_state.messages.append({
                    "question":           question,
                    "answer":             result["answer"],
                    "sources":            result["sources"],
                    "tool_calls":         result["tool_calls"],
                    "num_context_chunks": result["num_context_chunks"],
                })
                st.rerun()


# ── Chat input ─────────────────────────────────────────────────────────────────
if prompt := st.chat_input(f"Ask anything about {selected_name} meetings..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        result = run_and_stream(prompt, selected_id)
        st.markdown(
            _linkify_citations(result["answer"], result["num_context_chunks"]),
            unsafe_allow_html=True,
        )
        render_sources(result["sources"])
        render_tool_trace(result["tool_calls"])
    st.session_state.messages.append({
        "question":           prompt,
        "answer":             result["answer"],
        "sources":            result["sources"],
        "tool_calls":         result["tool_calls"],
        "num_context_chunks": result["num_context_chunks"],
    })
    st.rerun()