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
    query="What questions did Harsh Vardhan raise about the AI architecture approach?", project_id="proj_nolocode_001")

print('Query output ------------------')
print("Query Whole Result:", res_query)
print('Query output ------------------" )')
print("Answer:", res_query["answer"])
print("Sources:")   
for s in res_query["sources"]:
    print(f"  - {s['speaker_name']} | {s['meeting_title']} ({s['meeting_date']})")
print("Tool calls:")
for tc in res_query["tool_calls"]:
    print(f"  - {tc['tool']} with args {tc['args']}")   