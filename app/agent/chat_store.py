"""
chat_store.py — PostgreSQL-backed chat history store.

Responsibilities
----------------
  - Persist sessions (one per project / browser session) and turns (Q&A pairs).
  - Provide get_llm_messages() for loading history into the LangGraph initial_state.
  - Provide get_last_non_project_scope() for scope inheritance across turns.
  - Expose get_chat_store() singleton — returns None if DATABASE_URL is not set
    or PostgreSQL is unreachable (M3/F3 — chat history is optional).

Failure contract
----------------
  Every public method is wrapped in try/except.  On any DB error the method
  returns a safe empty value ([], None, 0) and logs a warning — the query
  pipeline always continues.  See the degradation table in the plan.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import psycopg2
import psycopg2.extras
from langchain_core.messages import AIMessage, HumanMessage

logger = logging.getLogger(__name__)


# ── Schema ────────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id   TEXT        PRIMARY KEY,
    project_id   TEXT        NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS turns (
    id               SERIAL      PRIMARY KEY,
    session_id       TEXT        NOT NULL
                     REFERENCES sessions(session_id) ON DELETE CASCADE,
    turn_index       INTEGER     NOT NULL,
    human_content    TEXT        NOT NULL,
    ai_content       TEXT        NOT NULL,
    sources_json     JSONB,
    tool_calls_json  JSONB,
    num_chunks       INTEGER,
    scope_type       TEXT,
    scope_ids_json   JSONB,
    scope_where_json JSONB,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(session_id, turn_index)
);

CREATE INDEX IF NOT EXISTS idx_turns_session
    ON turns(session_id, turn_index);

CREATE INDEX IF NOT EXISTS idx_sessions_project
    ON sessions(project_id, updated_at DESC);
"""


# ── ChatStore ─────────────────────────────────────────────────────────────────

class ChatStore:
    """Thin wrapper around a single psycopg2 connection."""

    def __init__(self, database_url: str) -> None:
        self._url  = database_url
        self._conn = None   # lazy-initialised by _get_conn()

    # ── Connection management ─────────────────────────────────────────────────

    def _get_conn(self):
        """
        F2 FIX: Reconnect-on-failure.

        PostgreSQL closes idle connections after ~30-60 min.
        Strategy: check if connection is alive with a cheap SELECT 1 ping.
        If the ping fails (dead connection) reconnect once before giving up.
        """
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(self._url)
            self._conn.autocommit = False
            return self._conn
        try:
            with self._conn.cursor() as cur:
                cur.execute("SELECT 1")
            return self._conn
        except psycopg2.OperationalError:
            try:
                self._conn = psycopg2.connect(self._url)
                self._conn.autocommit = False
                return self._conn
            except Exception:
                self._conn = None
                raise

    # ── Schema init ───────────────────────────────────────────────────────────

    def ensure_tables(self) -> None:
        """Create tables and indexes if they don't exist yet."""
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(_DDL)
        conn.commit()
        logger.info("chat_store | tables ready")

    # ── Session management ────────────────────────────────────────────────────

    def create_session(self, project_id: str) -> Optional[str]:
        """
        Create a new session row and return its session_id (uuid4 hex).
        Returns None on DB failure (M2).
        """
        try:
            session_id = uuid.uuid4().hex
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sessions (session_id, project_id) VALUES (%s, %s)",
                    (session_id, project_id),
                )
            conn.commit()
            logger.info("chat_store | session created: %s (project=%s)", session_id, project_id)
            return session_id
        except Exception as e:
            logger.warning("chat_store | create_session failed: %s", e)
            if self._conn:
                try:
                    self._conn.rollback()
                except Exception:
                    pass
            return None

    # ── Turn persistence ──────────────────────────────────────────────────────

    def save_turn(
        self,
        session_id:  str,
        turn_index:  int,
        human:       str,
        ai:          str,
        sources:     list,
        tool_calls:  list,
        num_chunks:  int,
        scope_type:  str,
        scope_ids:   Optional[list],
        scope_where: Optional[dict],
    ) -> None:
        """
        Persist one Q&A turn.  Also bumps sessions.updated_at.
        Silent no-op on DB failure (M2) — answer already delivered to user.
        """
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO turns
                        (session_id, turn_index, human_content, ai_content,
                         sources_json, tool_calls_json, num_chunks,
                         scope_type, scope_ids_json, scope_where_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (session_id, turn_index) DO NOTHING
                    """,
                    (
                        session_id, turn_index, human, ai,
                        json.dumps(sources)     if sources     is not None else None,
                        json.dumps(tool_calls)  if tool_calls  is not None else None,
                        num_chunks,
                        scope_type,
                        json.dumps(scope_ids)   if scope_ids   is not None else None,
                        json.dumps(scope_where) if scope_where is not None else None,
                    ),
                )
                cur.execute(
                    "UPDATE sessions SET updated_at = NOW() WHERE session_id = %s",
                    (session_id,),
                )
            conn.commit()
        except Exception as e:
            logger.warning(
                "chat_store | save_turn failed (turn lost from history): %s", e
            )
            if self._conn:
                try:
                    self._conn.rollback()
                except Exception:
                    pass

    # ── History loading ───────────────────────────────────────────────────────

    def get_llm_messages(
        self,
        session_id: str,
        max_turns:  int = 5,
    ) -> list:
        """
        Return the last max_turns Q&A pairs as LangChain messages
        [HumanMessage, AIMessage, HumanMessage, AIMessage, ...] oldest first.

        ToolMessages and intermediate AIMessages with tool_calls are NOT stored —
        only the final human query and the final AI text answer per turn.

        Returns [] on DB failure (M2) — query proceeds without history context.
        """
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT human_content, ai_content
                    FROM   turns
                    WHERE  session_id = %s
                    ORDER  BY turn_index DESC
                    LIMIT  %s
                    """,
                    (session_id, max_turns),
                )
                rows = cur.fetchall()

            # Rows arrive newest-first; reverse to oldest-first for the LLM
            messages = []
            for row in reversed(rows):
                human = (row["human_content"] or "").strip()
                ai    = (row["ai_content"]    or "").strip()
                if human and ai:
                    messages.append(HumanMessage(content=human))
                    messages.append(AIMessage(content=ai))
            return messages
        except Exception as e:
            logger.warning("chat_store | get_llm_messages failed: %s — no history", e)
            return []

    # ── Scope inheritance ─────────────────────────────────────────────────────

    def get_last_non_project_scope(self, session_id: str) -> Optional[dict]:
        """
        M5 FIX: Find the most recent turn that had a specific scope
        (scope_type != 'project'), scanning ALL turns — not just the last N.

        This lets scope inheritance work correctly even when many project-wide
        turns separate the current query from the last scoped query.

        Example:
          Turn 1:  scope_type=meeting, scope_ids=[meeting_005]
          Turns 2-9: scope_type=project (broad queries)
          Turn 10: "What was decided in that meeting?"
          → This method returns Turn 1's scope → Meeting #5 correctly inherited.

        Returns None on DB failure or no prior scoped turn (M2).
        """
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT scope_type, scope_ids_json, scope_where_json
                    FROM   turns
                    WHERE  session_id = %s
                      AND  scope_type IS NOT NULL
                      AND  scope_type != 'project'
                    ORDER  BY turn_index DESC
                    LIMIT  1
                    """,
                    (session_id,),
                )
                row = cur.fetchone()

            if not row:
                return None

            scope_ids   = row["scope_ids_json"]
            scope_where = row["scope_where_json"]

            # psycopg2 RealDictCursor returns JSONB as Python objects already
            # but be defensive in case they come back as strings
            if isinstance(scope_ids, str):
                scope_ids = json.loads(scope_ids)
            if isinstance(scope_where, str):
                scope_where = json.loads(scope_where)

            return {
                "scope_type":  row["scope_type"],
                "scope_ids":   scope_ids,
                "scope_where": scope_where,
            }
        except Exception as e:
            logger.warning("chat_store | get_last_non_project_scope failed: %s", e)
            return None

    # ── Display turns (Streamlit re-render) ───────────────────────────────────

    def get_display_turns(self, session_id: str) -> list[dict]:
        """
        Return all turns for Streamlit chat history re-render on page refresh.
        Each dict mirrors what run_and_stream() appends to st.session_state.messages.
        Returns [] on DB failure (M2).
        """
        try:
            conn = self._get_conn()
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT human_content, ai_content,
                           sources_json, tool_calls_json, num_chunks
                    FROM   turns
                    WHERE  session_id = %s
                    ORDER  BY turn_index ASC
                    """,
                    (session_id,),
                )
                rows = cur.fetchall()

            result = []
            for row in rows:
                sources    = row["sources_json"]    or []
                tool_calls = row["tool_calls_json"] or []
                if isinstance(sources, str):
                    sources = json.loads(sources)
                if isinstance(tool_calls, str):
                    tool_calls = json.loads(tool_calls)
                result.append({
                    "question":           row["human_content"] or "",
                    "answer":             row["ai_content"]    or "",
                    "sources":            sources,
                    "tool_calls":         tool_calls,
                    "num_context_chunks": row["num_chunks"] or 0,
                })
            return result
        except Exception as e:
            logger.warning("chat_store | get_display_turns failed: %s", e)
            return []

    # ── Turn index ────────────────────────────────────────────────────────────

    def get_next_turn_index(self, session_id: str) -> int:
        """
        Return the next turn_index for a session (= COUNT of existing turns).
        Returns 0 on DB failure so the first attempted save uses index 0 (M2).
        ON CONFLICT DO NOTHING in save_turn handles any rare race condition.
        """
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM turns WHERE session_id = %s",
                    (session_id,),
                )
                row = cur.fetchone()
            return int(row[0]) if row else 0
        except Exception as e:
            logger.warning("chat_store | get_next_turn_index failed: %s", e)
            return 0

    # ── Session deletion ──────────────────────────────────────────────────────

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session and all its turns (ON DELETE CASCADE).
        Used by "Clear Chat" button.  Silent no-op on failure (M2).
        """
        try:
            conn = self._get_conn()
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM sessions WHERE session_id = %s",
                    (session_id,),
                )
            conn.commit()
            logger.info("chat_store | session deleted: %s", session_id)
        except Exception as e:
            logger.warning("chat_store | delete_session failed: %s", e)
            if self._conn:
                try:
                    self._conn.rollback()
                except Exception:
                    pass


# ── Singleton ─────────────────────────────────────────────────────────────────

_STORE: Optional[ChatStore] = None
_STORE_DISABLED: bool = False   # True only when DATABASE_URL is not set (permanent)


def get_chat_store() -> Optional[ChatStore]:
    """
    Return the ChatStore singleton, or None when chat history is unavailable.

    Two distinct failure modes (F3 FIX):
      PERMANENT  — DATABASE_URL not set → set _STORE_DISABLED=True, never retry.
      TRANSIENT  — PostgreSQL temporarily down → return None this call only,
                   retry next call (DB may have recovered).

    All callers guard with:
        if store := get_chat_store():
            store.some_method(...)
    """
    global _STORE, _STORE_DISABLED

    if _STORE_DISABLED:
        return None                         # DATABASE_URL not configured — permanent

    if _STORE is not None:
        return _STORE

    url = os.getenv("DATABASE_URL")
    if not url:
        logger.info(
            "chat_store | DATABASE_URL not set — running stateless (no chat history)"
        )
        _STORE_DISABLED = True              # permanent — no point retrying
        return None

    try:
        store = ChatStore(url)
        store.ensure_tables()
        _STORE = store
        logger.info("chat_store | initialised — chat history enabled")
        return _STORE
    except Exception as e:
        logger.warning(
            "chat_store | init failed (%s) — history disabled for this call, will retry",
            e,
        )
        # Do NOT set _STORE_DISABLED — transient failure, PostgreSQL may recover
        return None