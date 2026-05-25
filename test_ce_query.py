"""
test_ce_query.py — Test the CE classification query through the full production pipeline.
Run: uv run python test_ce_query.py
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.logging_config import setup_pipeline_logging
setup_pipeline_logging()

from app.services.answer_service import answer_question

QUERY      = "Who raised the confusion about CE classification code?"
# QUERY      = "What are the topics discussed in previous meeting?"
# QUERY = "What discussion have to happen related to AI in previous meeting?"
# QUERY = "What was discussed about AI in the April 22nd meeting?"
QUERY = "What questions were raised in the first meeting?"
# QUERY = "What questions were raised in the first meeting?"
# QUERY = "What commitments were made in the previous meeting?"
# QUERY = "What was the full conversation about depreciation in the last meeting?"
# QUERY = "Did Bhavneet ask any questions in the April 22nd meeting?"
# QUERY = "What was the entire discussion on effort estimation in the last meeting?"
# QUERY = "Summarize everything discussed about forecasting in the first meeting"

PROJECT_ID = "proj_nolocode_001"

print("=" * 64)
print(f"  QUERY      : {QUERY}")
print(f"  PROJECT_ID : {PROJECT_ID}")
print("=" * 64)

result = answer_question(QUERY, PROJECT_ID)

print()
print("=" * 64)
print("  INTENT :", result["intent"])
print("=" * 64)
print()
print("  ANSWER:")
for line in result["answer"].split("\n"):
    print(f"    {line}")
print()
print("  SOURCES:")
for s in result["sources"]:
    print(f"    - {s['speaker_name']} | {s['meeting_title']} ({s['meeting_date']})")
print()
