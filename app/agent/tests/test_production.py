import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# ── Load env vars + wire up pipeline logging before any app imports ───────────
from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

from app.logging_config import setup_pipeline_logging
setup_pipeline_logging()

# ── App imports (after logging is ready) ─────────────────────────────────────
from app.agent.service import answer_query

# from app.agent import get_graph
# from langchain_core.messages import HumanMessage

# # Run the graph directly to inspect full final state
# graph = get_graph()
# final_state = graph.invoke({
#     "messages":    [HumanMessage(content="What questions were raised in the first meeting?")],
#     "project_id":  "proj_nolocode_001",
#     "scope_where":   None,
#     "scope_ids":     None,
#     "scope_type":    "project",
#     "recommended_k": 15,
# })

# # This is AFTER query_scope_node ran — shows the REAL resolved scope
# print("scope_type :", final_state["scope_type"])
# print("scope_ids  :", final_state["scope_ids"])
# print("scope_where:", final_state["scope_where"])
# print("recommended_k:", final_state["recommended_k"])



res_query = answer_query(
    # query="Give me the details about AI Architecture",
    # query="What was discussed about the multi-agent system?",
    # query="What was the impact on architecture after Redis implementation?",
    # query="Which AI approach we are decided to go with?",
    # query="What has Karan Middha contributed across all meetings?",
    # query="What did Harsh Vardhan say about the stress test implementation?",
    query="What did Ashpreet say about AI architecture?",
    # query="What did the team decide about quantum computing implementation in the project?",
    project_id="proj_nolocode_001",
)

SEP = "=" * 70
print(f"\n{SEP}")
print("ANSWER")
print(SEP)
print(res_query["answer"])

print(f"\n{SEP}")
print(f"SOURCES  ({len(res_query['sources'])} chunks)")
print(SEP)
for s in res_query["sources"]:
    print(f"  [{s['chunk_num']}] {s['speaker_name']} | {s['meeting_title']} ({s['meeting_date']}) {s.get('timestamp','')}")

print(f"\n{SEP}")
print(f"TOOL CALLS  ({len(res_query['tool_calls'])})")
print(SEP)
for tc in res_query["tool_calls"]:
    print(f"  - {tc['tool']} | {tc['args']}")

if res_query.get("error"):
    print(f"\n[ERROR] {res_query['error']}")   