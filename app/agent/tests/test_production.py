import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

# ── Query to run  (edit this line to test a different question) ───────────────
QUERY      = "What did Ashpreet say about AI architecture?"
PROJECT_ID = "proj_nolocode_001"

# Uncomment one of these instead to switch queries:
# QUERY = "Give me the details about AI Architecture"
# QUERY = "What was discussed about the multi-agent system?"
# QUERY = "What was the impact on architecture after Redis implementation?"
# QUERY = "Which AI approach we are decided to go with?"
# QUERY = "What has Karan Middha contributed across all meetings?"
# QUERY = "What did Harsh Vardhan say about the stress test implementation?"
# QUERY = "What did the team decide about quantum computing implementation in the project?"

# ── Per-query log file (one isolated file per run, in app/agent/tests/logs/) ──
from app.logging_config import setup_query_file_logging
LOG_FILE = setup_query_file_logging(QUERY, PROJECT_ID)

SEP  = "=" * 70
THIN = "-" * 70

print(f"\n{SEP}")
print("  TEST PRODUCTION — QUERY RUNNER")
print(f"  Query   : {QUERY}")
print(f"  Project : {PROJECT_ID}")
print(f"  Log     : {LOG_FILE}")
print(SEP)

# ── App imports (after logging is wired up) ───────────────────────────────────
from app.agent.service import answer_query

res_query = answer_query(query=QUERY, project_id=PROJECT_ID)

# ── Print results ─────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  ANSWER")
print(SEP)
print(res_query["answer"])

print(f"\n{SEP}")
print(f"  SOURCES  ({len(res_query['sources'])} chunks)")
print(SEP)
for s in res_query["sources"]:
    ts = s.get("timestamp", "")
    ts_str = f"  [{ts}]" if ts else ""
    print(f"  [{s['chunk_num']}] {s['speaker_name']} | {s['meeting_title']} ({s['meeting_date']}){ts_str}")

print(f"\n{SEP}")
print(f"  TOOL CALLS  ({len(res_query['tool_calls'])})")
print(SEP)
for i, tc in enumerate(res_query["tool_calls"], 1):
    print(f"  {i}. {tc['tool']}")
    for k, v in tc["args"].items():
        print(f"       {k}: {v}")

if res_query.get("error"):
    print(f"\n  [ERROR] {res_query['error']}")

print(f"\n{SEP}")
print(f"  FULL LOG SAVED TO:")
print(f"  {LOG_FILE}")
print(SEP)