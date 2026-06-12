"""app.core — Shared infrastructure used by both pipelines.

Contains:
  storage/     — ChromaDB access (db, chunk_store, project_store)
  retrieval/   — Hybrid BM25+dense retrieval, reranking, all retrieval modes
  transcript/  — Chunking, normalization, meeting metadata
  embeddings/  — Gemini embedding model
  vector_store/ — Chroma store wrapper
  documents/   — LangChain Document mapper
  scope.py     — Meeting scope / temporal filter resolution
"""
