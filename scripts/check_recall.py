"""
check_recall.py — Recall diagnostic for a topic query.

Compares:
  A) Ground truth: ALL chunks in ChromaDB that contain the topic keywords
  B) Pipeline result: what hybrid_retrieve actually returns for the same query

Gaps = chunks in A but not in B → retrieval is MISSING relevant content.

Usage:
    python scripts/check_recall.py
    python scripts/check_recall.py --query "payment gateway" --keywords payment gateway
"""
import sys
import argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

from app.logging_config import setup_pipeline_logging
setup_pipeline_logging()

from app.core.storage.db import get_raw_collection
from app.core.retrieval import hybrid_retrieve
from app.core.retrieval.base import reset_corpus_cache

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID = "proj_nolocode_001"
QUERY      = "AI Architecture"
KEYWORDS   = ["architecture", "ai architecture", "microservice", "agent", "rag"]
K          = 40   # same as standard preset

SEP  = "=" * 70
SEP2 = "-" * 70

# ── CLI args ──────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Recall check for a topic query")
parser.add_argument("--query",    default=QUERY,    help="Query to run through pipeline")
parser.add_argument("--keywords", nargs="+", default=KEYWORDS, help="Keywords to match in ChromaDB")
parser.add_argument("--k",        type=int, default=K, help="k for hybrid_retrieve")
args = parser.parse_args()

query    = args.query
keywords = [kw.lower() for kw in args.keywords]
k        = args.k


# ── Step A: Ground truth from ChromaDB ───────────────────────────────────────
print(f"\n{SEP}")
print(f"STEP A — Ground Truth: All ChromaDB chunks matching keywords")
print(f"  Project : {PROJECT_ID}")
print(f"  Keywords: {keywords}")
print(SEP)

collection = get_raw_collection()
results    = collection.get(
    where={"project_id": {"$eq": PROJECT_ID}},
    include=["documents", "metadatas"],
)

all_docs  = results.get("documents", [])
all_metas = results.get("metadatas", [])

ground_truth = []
for text, meta in zip(all_docs, all_metas):
    if meta.get("is_meeting_summary"):
        continue
    text_lower = text.lower()
    if any(kw in text_lower for kw in keywords):
        ground_truth.append((text, meta))

print(f"Total chunks in project : {len(all_docs)}")
print(f"Matched by keywords     : {len(ground_truth)}\n")

gt_chunk_ids = set()
for i, (text, meta) in enumerate(ground_truth, 1):
    cid      = meta.get("chunk_id", f"no-id-{i}")
    speaker  = meta.get("speaker_name", "?")
    meeting  = meta.get("meeting_title", "?")
    date     = meta.get("meeting_date", "?")
    preview  = text.replace("\n", " ").strip()[:120]
    gt_chunk_ids.add(cid)
    print(f"  [GT-{i:02d}] {speaker} | {meeting} ({date})")
    print(f"         {preview}")
    print()


# ── Step B: Pipeline result from hybrid_retrieve ──────────────────────────────
print(f"\n{SEP}")
print(f"STEP B — Pipeline Result: hybrid_retrieve(query={query!r}, k={k})")
print(SEP)

reset_corpus_cache()
pipeline_docs = hybrid_retrieve(
    query=query,
    project_id=PROJECT_ID,
    k=k,
)

pipeline_chunk_ids = set()
print(f"Chunks returned by pipeline: {len(pipeline_docs)}\n")
for i, doc in enumerate(pipeline_docs, 1):
    meta    = doc.metadata
    cid     = meta.get("chunk_id", f"no-id-{i}")
    speaker = meta.get("speaker_name", "?")
    meeting = meta.get("meeting_title", "?")
    date    = meta.get("meeting_date", "?")
    preview = doc.page_content.replace("\n", " ").strip()[:120]
    pipeline_chunk_ids.add(cid)
    print(f"  [P-{i:02d}] {speaker} | {meeting} ({date})")
    print(f"         {preview}")
    print()


# ── Step C: Gap analysis ──────────────────────────────────────────────────────
print(f"\n{SEP}")
print(f"STEP C — Gap Analysis: In Ground Truth but NOT in Pipeline (Recall Gaps)")
print(SEP)

missed_ids = gt_chunk_ids - pipeline_chunk_ids
missed     = [(t, m) for t, m in ground_truth if m.get("chunk_id") in missed_ids]

if not missed:
    print("  No gaps found — pipeline retrieved all keyword-matched chunks.")
else:
    print(f"  MISSED {len(missed)} chunks (in ChromaDB but not returned by pipeline):\n")
    for i, (text, meta) in enumerate(missed, 1):
        speaker = meta.get("speaker_name", "?")
        meeting = meta.get("meeting_title", "?")
        date    = meta.get("meeting_date", "?")
        preview = text.replace("\n", " ").strip()[:200]
        print(f"  [MISS-{i}] {speaker} | {meeting} ({date})")
        print(f"            {preview}")
        print()

# ── Step D: Noise analysis ────────────────────────────────────────────────────
print(f"\n{SEP}")
print(f"STEP D — Noise Analysis: In Pipeline but NOT in Ground Truth (False Positives)")
print(SEP)

extra_ids = pipeline_chunk_ids - gt_chunk_ids
extra     = [doc for doc in pipeline_docs if doc.metadata.get("chunk_id") in extra_ids]

if not extra:
    print("  No false positives — all pipeline chunks matched at least one keyword.")
else:
    print(f"  EXTRA {len(extra)} chunks (pipeline retrieved but no keyword match):\n")
    for i, doc in enumerate(extra, 1):
        meta    = doc.metadata
        speaker = meta.get("speaker_name", "?")
        meeting = meta.get("meeting_title", "?")
        date    = meta.get("meeting_date", "?")
        preview = doc.page_content.replace("\n", " ").strip()[:200]
        print(f"  [EXTRA-{i}] {speaker} | {meeting} ({date})")
        print(f"              {preview}")
        print()

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print(f"SUMMARY")
print(SEP)
recall    = len(pipeline_chunk_ids & gt_chunk_ids) / len(gt_chunk_ids) * 100 if gt_chunk_ids else 0
precision = len(pipeline_chunk_ids & gt_chunk_ids) / len(pipeline_chunk_ids) * 100 if pipeline_chunk_ids else 0
print(f"  Ground truth (keyword matched) : {len(ground_truth)} chunks")
print(f"  Pipeline retrieved             : {len(pipeline_docs)} chunks")
print(f"  Correctly retrieved            : {len(pipeline_chunk_ids & gt_chunk_ids)} chunks")
print(f"  MISSED (recall gaps)           : {len(missed)} chunks")
print(f"  EXTRA  (false positives)       : {len(extra)} chunks")
print(f"  Recall    : {recall:.1f}%   (how many relevant chunks did pipeline find?)")
print(f"  Precision : {precision:.1f}%   (of retrieved chunks, how many were relevant?)")
print()