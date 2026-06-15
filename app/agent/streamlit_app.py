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

import base64
import json
import logging
import re
import sys
import time
from pathlib import Path

# ── sys.path: project root must be on the path before any imports ─────────────
_PROJECT_ROOT = Path(__file__).parent.parent.parent   # app/agent/ → app/ → project root
sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.agent import get_graph, reset_doc_accumulator, get_accumulated_docs
from app.agent.service import _build_sources, _extract_tool_calls
from app.agent._tool_utils import fmt_date
from app.agent.chat_store import get_chat_store
from app.core.storage.db import get_raw_collection
from app.core.retrieval import reset_corpus_cache
from app.logging_config import setup_pipeline_logging

# Wire up pipeline logging once at app startup.
# Writes to pipeline.log + stderr (the terminal where streamlit run was launched).
# Watch live:  tail -f pipeline.log
setup_pipeline_logging()

logger = logging.getLogger("app.agent.streamlit_app")


# ── Professional SVG avatars (replaces Streamlit's default emoji-in-coloured-box) ─
def _b64svg(svg: str) -> str:
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()

USER_AVATAR = _b64svg("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<circle cx="20" cy="20" r="20" fill="#2563EB"/>
<circle cx="20" cy="15" r="7" fill="white" opacity="0.95"/>
<ellipse cx="20" cy="33" rx="12" ry="9" fill="white" opacity="0.95"/>
</svg>""")

AI_AVATAR = _b64svg("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="12" fill="#1D4ED8"/>
<text x="20" y="27" font-family="system-ui,-apple-system,sans-serif"
      font-size="15" font-weight="700" fill="white" text-anchor="middle">AI</text>
</svg>""")


def _fmt_date(val) -> str:
    """Thin wrapper — delegates to the shared fmt_date() from _tool_utils."""
    return fmt_date(val)


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
/* ── Global ─────────────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] { background: #F0F4F8; }
[data-testid="stHeader"] {
    background: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

/* ── Dark professional sidebar ───────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #0F172A !important;
    border-right: none;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label { color: #94A3B8 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] strong,
section[data-testid="stSidebar"] b     { color: #F1F5F9 !important; }
section[data-testid="stSidebar"] hr    { border-color: #1E293B !important; }
section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #F1F5F9 !important; font-size: 1.4em !important;
}
section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {
    color: #64748B !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #1E293B !important;
    border-color: #334155 !important;
    color: #F1F5F9 !important;
}
section[data-testid="stSidebar"] button {
    background: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #CBD5E1 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] button:hover {
    background: #2563EB !important;
    border-color: #2563EB !important;
    color: #FFFFFF !important;
}

/* ── Chat message cards ───────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: #FFFFFF !important;
    border-radius: 14px !important;
    border: 1px solid #E2E8F0 !important;
    padding: 14px 18px 14px 14px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.02) !important;
    margin-bottom: 14px !important;
}

/* ── Tool call progress rows ──────────────────────────────────────────── */
.tool-row {
    background: #EFF6FF;
    border-left: 3px solid #2563EB;
    padding: 7px 14px;
    margin: 4px 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.87em;
    color: #1E40AF;
    font-weight: 500;
}
.tool-result {
    color: #64748B;
    font-size: 0.81em;
    padding-left: 20px;
    margin-bottom: 2px;
}

/* ── Source citation cards ────────────────────────────────────────────── */
.citation-card {
    background: #FAFAFA;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.citation-client     { border-left: 4px solid #EF4444; }
.citation-pm         { border-left: 4px solid #F59E0B; }
.citation-developer  { border-left: 4px solid #2563EB; }
.citation-summary    { border-left: 4px solid #8B5CF6; }

/* ── Scope badge ──────────────────────────────────────────────────────── */
.scope-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #EFF6FF;
    color: #1D4ED8;
    padding: 3px 12px;
    border-radius: 999px;
    font-size: 0.78em;
    font-weight: 600;
    border: 1px solid #BFDBFE;
    margin-bottom: 10px;
}

/* ── Example question buttons ─────────────────────────────────────────── */
[data-testid="stButton"] button {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    color: #374151 !important;
    font-size: 0.87em !important;
    text-align: left !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    transition: all 0.15s ease !important;
    padding: 10px 14px !important;
}
[data-testid="stButton"] button:hover {
    border-color: #93C5FD !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.14) !important;
    color: #1D4ED8 !important;
}

/* ── Chat input ───────────────────────────────────────────────────────── */
[data-testid="stChatInputTextArea"] textarea {
    border-radius: 12px !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    font-size: 0.95em !important;
}
[data-testid="stChatInputTextArea"] textarea:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.10) !important;
}

/* ── Dividers ─────────────────────────────────────────────────────────── */
hr { border-color: #E2E8F0 !important; }

/* ── Citation anchor scroll offset ───────────────────────────────────── */
[id^="src-"] { scroll-margin-top: 90px; }
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
                    "date":  _fmt_date(m.get("meeting_date", "")),
                }
            name = m.get("speaker_name")
            if name and name not in speakers:
                speakers[name] = m.get("speaker_role", "unknown")

        sorted_meetings = sorted(meetings.values(), key=lambda x: str(x.get("date", "")))
        return {
            "chunk_count":   len([m for m in metas if not m.get("is_meeting_summary")]),
            "meeting_count": len(meetings),
            "speaker_count": len(speakers),
            "meetings":      sorted_meetings,
            "speakers":      speakers,
        }
    except Exception:
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
            date  = _fmt_date(m.get("meeting_date", ""))
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

def _linkify_citations(text: str, num_chunks: int, msg_id: str = "") -> str:
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
    _prefix = f"src-{msg_id}-" if msg_id else "src-"

    def _replacer(m):
        n = int(m.group(1))
        if 1 <= n <= num_chunks:
            return (
                f'<a href="#{_prefix}{n}" style="'
                f'display:inline-flex;align-items:center;justify-content:center;'
                f'min-width:17px;height:17px;padding:0 4px;'
                f'background:#2563EB;color:#FFFFFF;border-radius:4px;'
                f'font-size:0.65em;font-weight:700;text-decoration:none;'
                f'vertical-align:super;margin:0 2px;cursor:pointer;'
                f'line-height:1;">{n}</a>'
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

_ROLE_ACCENT = {
    "client":          "#EF4444",
    "project_manager": "#F59E0B",
    "developer":       "#3B82F6",
    "summary":         "#8B5CF6",
    "unknown":         "#64748B",
}


def render_sources(sources: list[dict], msg_id: str = ""):
    """
    Render chunk citations below the answer — Perplexity-style.

    Each card shows:
      - numbered blue badge matching the inline [N] citation
      - speaker name + role-coloured left border
      - meeting title + date as secondary metadata
      - timestamp pill
      - the actual transcript excerpt as a styled blockquote (the real proof)

    Always visible — no expander needed.
    """
    if not sources:
        return

    # ── Section header ────────────────────────────────────────────────────────
    n_label = f"{len(sources)} Source{'s' if len(sources) > 1 else ''} Used"
    st.markdown(f"""
<div style="margin-top:22px;margin-bottom:14px;display:flex;
            align-items:center;gap:10px;">
  <span style="flex:1;height:1px;background:#E2E8F0;display:block;"></span>
  <span style="font-size:0.7em;font-weight:700;color:#94A3B8;
               text-transform:uppercase;letter-spacing:0.1em;white-space:nowrap;">
    {n_label}
  </span>
  <span style="flex:1;height:1px;background:#E2E8F0;display:block;"></span>
</div>
""", unsafe_allow_html=True)

    _prefix = f"src-{msg_id}-" if msg_id else "src-"

    # ── One card per source ───────────────────────────────────────────────────
    for s in sources:
        n        = s.get("chunk_num", 1)
        speaker  = s.get("speaker_name", "Unknown")
        role     = s.get("speaker_role", "unknown")
        meeting  = s.get("meeting_title", "Unknown Meeting")
        date     = _fmt_date(s.get("meeting_date", ""))
        ts       = s.get("timestamp")
        preview  = (s.get("content_preview") or "").strip()
        is_summ  = s.get("is_summary", False)

        accent   = _ROLE_ACCENT.get("summary" if is_summ else role, "#64748B")

        ts_badge = (
            f'<span style="background:#EFF6FF;color:#2563EB;padding:2px 8px;'
            f'border-radius:999px;font-size:0.72em;font-weight:600;'
            f'white-space:nowrap;">⏱ {ts}</span>'
        ) if ts else ""

        # Escape HTML special chars in the transcript excerpt
        safe_preview = (
            preview
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        suffix = "…" if len(preview) >= 350 else ""

        st.markdown(f"""
<div id="{_prefix}{n}" style="
    display:flex; gap:14px;
    background:#FFFFFF;
    border:1px solid #E2E8F0;
    border-left:4px solid {accent};
    border-radius:10px;
    padding:14px 16px;
    margin-bottom:10px;
    box-shadow:0 1px 3px rgba(0,0,0,0.05);
    scroll-margin-top:80px;
">
  <div style="flex-shrink:0;width:26px;height:26px;background:{accent};
              border-radius:6px;display:flex;align-items:center;
              justify-content:center;color:#FFFFFF;font-size:0.75em;
              font-weight:700;margin-top:2px;">{n}</div>
  <div style="flex:1;min-width:0;">
    <div style="display:flex;align-items:center;gap:8px;
                flex-wrap:wrap;margin-bottom:3px;">
      <span style="font-weight:700;color:#0F172A;font-size:0.92em;">
        {"📋 Meeting Summary" if is_summ else speaker}
      </span>
      {ts_badge}
    </div>
    <div style="color:#64748B;font-size:0.78em;margin-bottom:10px;">
      {meeting}&nbsp;·&nbsp;{date}
    </div>
    <div style="background:#F8FAFC;border-radius:7px;padding:11px 14px;
                font-size:0.875em;color:#334155;line-height:1.65;
                border:1px solid #E9EEF4;">
      <span style="color:{accent};font-size:1.1em;font-weight:700;
                   margin-right:4px;">"</span>{safe_preview}{suffix}<span
        style="color:{accent};font-size:1.1em;font-weight:700;
               margin-left:2px;">"</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


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


def render_chat_history(msg: dict, msg_id: str = ""):
    """Render a stored chat message (from session_state) without re-running."""
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(msg["question"])
    with st.chat_message("assistant", avatar=AI_AVATAR):
        num_chunks = msg.get("num_context_chunks", len(msg.get("sources", [])))
        st.markdown(_linkify_citations(msg["answer"], num_chunks, msg_id), unsafe_allow_html=True)
        render_sources(msg.get("sources", []), msg_id)
        render_tool_trace(msg.get("tool_calls", []))


# ── Core: streaming graph run ─────────────────────────────────────────────────

def run_and_stream(
    query:      str,
    project_id: str,
    session_id: str | None = None,
) -> dict:
    """
    Invoke the LangGraph agent using graph.stream() so the UI updates live.

    Streaming behaviour:
      query_scope node  → shows scope resolved (meeting name or "all meetings")
      agent node        → shows each tool call + its arguments as LLM decides them
      tools node        → shows first line of each tool result (Found N chunks…)
      final agent node  → no tool_calls → answer generated, status closes

    Chat history:
      Loads last 5 turns from PostgreSQL and prepends them to initial_state messages.
      After a successful answer, saves the turn to PostgreSQL.
      session_id=None → stateless mode (no history load/save).

    Returns the same dict shape as service.answer_query():
      answer, sources, tool_calls, num_context_chunks, error
    """
    reset_doc_accumulator()
    reset_corpus_cache()

    logger.info(
        "══ NEW QUERY ══ | project=%s | session=%s\n          query: %s",
        project_id, session_id or "stateless", query,
    )

    # ── [1] Load conversation history ────────────────────────────────────────
    store = get_chat_store()   # None if DATABASE_URL not set (M3)
    history_messages = []
    if store and session_id:
        history_messages = store.get_llm_messages(session_id, max_turns=5)
        logger.info(
            "[1] HISTORY  — %d messages (%d prior turns) loaded | session=%s",
            len(history_messages), len(history_messages) // 2, session_id,
        )
    else:
        logger.info("[1] HISTORY  — stateless (no session / no DB)")

    graph = get_graph()
    initial_state = {
        "messages":      history_messages + [HumanMessage(content=query)],
        "project_id":    project_id,
        "session_id":    session_id,
        "scope_where":   None,
        "scope_ids":     None,
        "scope_type":    "project",
        "recommended_k": 15,
    }

    # F4 FIX: initialise scope fields before streaming starts.
    # query_scope node fires once (first node) and emits these in its chunk.
    # We capture them here so save_turn gets the correct scope for inheritance.
    # Without this, every turn would be saved with scope_type="project" and
    # history inheritance would never work from the Streamlit path.
    final_scope_type:  str        = "project"
    final_scope_ids:   list | None = None
    final_scope_where: dict | None = None

    t_start      = time.time()
    all_messages: list    = []
    error:        str | None = None

    try:
        with st.status("🤖 Agent thinking...", expanded=True) as status:

            for chunk in graph.stream(initial_state):
                for node_name, node_output in chunk.items():

                    # ── Accumulate messages ──────────────────────────────────
                    for msg in node_output.get("messages", []):
                        all_messages.append(msg)

                    # ── query_scope: capture scope + show badge ──────────────
                    if node_name == "query_scope":
                        final_scope_type  = node_output.get("scope_type", "project")
                        final_scope_ids   = node_output.get("scope_ids")
                        final_scope_where = node_output.get("scope_where")
                        label = _scope_label(final_scope_type, final_scope_ids, project_id)
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

    # ── Save turn to PostgreSQL (only on success, F1/M2 pattern) ─────────────
    if store and session_id and answer and not error:
        turn_index = store.get_next_turn_index(session_id)
        store.save_turn(
            session_id=session_id,
            turn_index=turn_index,
            human=query,
            ai=answer,
            sources=sources,
            tool_calls=tool_calls,
            num_chunks=len(docs),
            scope_type=final_scope_type,
            scope_ids=final_scope_ids,
            scope_where=final_scope_where,
        )

    elapsed_ms = round((time.time() - t_start) * 1000)
    logger.info(
        "══ DONE (%dms) ══ | tools=%d | docs=%d | answer=%d chars | project=%s | session=%s",
        elapsed_ms, len(tool_calls), len(docs), len(answer),
        project_id, session_id or "stateless",
    )

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
if "session_id" not in st.session_state:
    st.session_state.session_id = None


# ── Load project list ─────────────────────────────────────────────────────────
projects      = load_projects()
project_names = {v["project_name"]: k for k, v in projects.items()}


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div style="padding:16px 0 20px;">
  <div style="color:#F1F5F9;font-size:1.05em;font-weight:700;letter-spacing:-0.3px;">
    Meeting Intelligence
  </div>
  <div style="color:#475569;font-size:0.76em;margin-top:3px;font-weight:500;
              letter-spacing:0.04em;text-transform:uppercase;">
    AI · LangGraph Agent
  </div>
</div>
""", unsafe_allow_html=True)
    st.divider()

    selected_name = st.selectbox("Project", options=list(project_names.keys()))
    selected_id   = project_names[selected_name]

    # ── Session lifecycle ─────────────────────────────────────────────────────
    _store = get_chat_store()   # None when DATABASE_URL not set (M3)

    if st.session_state.active_project_id != selected_id:
        # Project switched → create a new session for the new project.
        # Old session is abandoned in PostgreSQL (not deleted) — M7.
        # updated_at on the old session row records when it was last used.
        st.session_state.active_project_id = selected_id
        st.session_state.session_id = (
            _store.create_session(selected_id) if _store else None
        )
        st.session_state.messages = []
        st.cache_data.clear()

    elif st.session_state.session_id is None and _store:
        # First load of this project in this browser tab — create a session.
        st.session_state.session_id = _store.create_session(selected_id)

    # ── Load history on page refresh ─────────────────────────────────────────
    # If session_id exists and messages list is empty (e.g. after page refresh),
    # reload prior turns from PostgreSQL so the chat window is not blank.
    if (
        st.session_state.session_id
        and _store
        and not st.session_state.messages
    ):
        prior_turns = _store.get_display_turns(st.session_state.session_id)
        if prior_turns:
            st.session_state.messages = prior_turns

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
        # Delete the current session (cascades to all turns) and create a fresh one.
        # M2: delete_session is a silent no-op on DB failure.
        if _store and st.session_state.session_id:
            _store.delete_session(st.session_state.session_id)
        st.session_state.session_id = (
            _store.create_session(selected_id) if _store else None
        )
        st.session_state.messages = []
        st.rerun()
    if col_b.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()


# ── Main area ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #1E3A5F 0%, #1D4ED8 100%);
    border-radius: 16px;
    padding: 22px 28px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
">
  <div>
    <div style="color:#93C5FD;font-size:0.72em;font-weight:600;
                letter-spacing:0.1em;text-transform:uppercase;margin-bottom:5px;">
      AI Meeting Intelligence
    </div>
    <div style="color:#FFFFFF;font-size:1.35em;font-weight:700;line-height:1.2;">
      {selected_name}
    </div>
    <div style="color:#BFDBFE;font-size:0.82em;margin-top:6px;">
      Ask anything about your meetings — decisions, commitments, speakers, timelines
    </div>
  </div>
  <div style="display:flex;gap:16px;margin-left:24px;">
    <div style="text-align:center;background:rgba(255,255,255,0.1);
                border-radius:10px;padding:10px 16px;">
      <div style="color:#FFFFFF;font-size:1.4em;font-weight:700;line-height:1;">
        {stats["meeting_count"]}
      </div>
      <div style="color:#93C5FD;font-size:0.7em;font-weight:500;margin-top:2px;">
        Meetings
      </div>
    </div>
    <div style="text-align:center;background:rgba(255,255,255,0.1);
                border-radius:10px;padding:10px 16px;">
      <div style="color:#FFFFFF;font-size:1.4em;font-weight:700;line-height:1;">
        {stats["speaker_count"]}
      </div>
      <div style="color:#93C5FD;font-size:0.7em;font-weight:500;margin-top:2px;">
        Speakers
      </div>
    </div>
    <div style="text-align:center;background:rgba(255,255,255,0.1);
                border-radius:10px;padding:10px 16px;">
      <div style="color:#FFFFFF;font-size:1.4em;font-weight:700;line-height:1;">
        {stats["chunk_count"]}
      </div>
      <div style="color:#93C5FD;font-size:0.7em;font-weight:500;margin-top:2px;">
        Segments
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Render chat history ───────────────────────────────────────────────────────
for _i, msg in enumerate(st.session_state.messages):
    render_chat_history(msg, msg_id=f"m{_i}")


# ── Empty state: example question buttons ────────────────────────────────────
if not st.session_state.messages:
    st.markdown(
        '<p style="color:#64748B;font-size:0.9em;margin-bottom:12px;">'
        'Try one of these to get started:</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    for i, question in enumerate(EXAMPLE_QUESTIONS):
        with cols[i % 3]:
            if st.button(question, key=f"ex_{i}", use_container_width=True):
                _new_msg_id = f"m{len(st.session_state.messages)}"
                with st.chat_message("user", avatar=USER_AVATAR):
                    st.markdown(question)
                with st.chat_message("assistant", avatar=AI_AVATAR):
                    result = run_and_stream(question, selected_id, st.session_state.session_id)
                    st.markdown(
                        _linkify_citations(result["answer"], result["num_context_chunks"], _new_msg_id),
                        unsafe_allow_html=True,
                    )
                    render_sources(result["sources"], _new_msg_id)
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
if prompt := st.chat_input(f"Ask about decisions, commitments, or anything from {selected_name} meetings..."):
    _new_msg_id = f"m{len(st.session_state.messages)}"
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar=AI_AVATAR):
        result = run_and_stream(prompt, selected_id, st.session_state.session_id)
        st.markdown(
            _linkify_citations(result["answer"], result["num_context_chunks"], _new_msg_id),
            unsafe_allow_html=True,
        )
        render_sources(result["sources"], _new_msg_id)
        render_tool_trace(result["tool_calls"])
    st.session_state.messages.append({
        "question":           prompt,
        "answer":             result["answer"],
        "sources":            result["sources"],
        "tool_calls":         result["tool_calls"],
        "num_context_chunks": result["num_context_chunks"],
    })
    st.rerun()