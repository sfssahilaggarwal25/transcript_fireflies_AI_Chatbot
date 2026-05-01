
def create_chunks(sentences, meeting_meta):
    """
    Production-level chunking for multi-speaker meeting transcripts (Fireflies).
    
    Strategy:
    - Hard speaker boundary: one chunk = one speaker only
    - Short utterances are buffered with the pending speaker, NOT emitted immediately
    - A chunk is only saved when it has enough content (MIN_CHARS) OR it's the last thing left
    - Micro-chunks below HARD_MIN are discarded entirely (garbage)
    - Size checked BEFORE adding to prevent overflow
    """
    chunks = []
    current_chunk = []
    current_speaker = None
    sequence = 1

    MAX_CHARS = 250   # flush if chunk would exceed this
    MIN_CHARS = 80    # don't save a chunk unless it's at least this long...
    HARD_MIN = 15     # ...unless forced; but NEVER save anything below this (pure garbage)

    def flush_chunk(force=False):
        nonlocal current_chunk, sequence

        if not current_chunk:
            return

        chunk_text = " ".join(current_chunk).strip()

        # Always discard pure garbage regardless of force
        if len(chunk_text) < HARD_MIN:
            current_chunk = []
            return

        # Skip undersized chunks unless we have no choice (end of transcript / speaker change)
        if len(chunk_text) < MIN_CHARS and not force:
            return  # keep buffering, don't save yet

        chunks.append({
            "chunk_id": f"{meeting_meta['meeting_id']}_{sequence}",
            "meeting_id": meeting_meta["meeting_id"],
            "meeting_title": meeting_meta["title"],
            "date": meeting_meta["date"],
            "speaker": current_speaker,
            "sequence": sequence,
            "text": chunk_text,
            "text_length": len(chunk_text),
        })

        sequence += 1
        current_chunk = []  # clean reset — no overlap

    for s in sentences:
        text = s["text"].strip()
        speaker = s["speaker_name"]

        # Hard garbage filter — catches "Sa.", "La.", "Ok.", single words
        if len(text) < 8:
            continue

        # Speaker boundary
        if speaker != current_speaker:
            flush_chunk(force=True)   # flush old speaker's buffer
            current_chunk = []        # guaranteed clean state
            current_speaker = speaker

        # Size guard: check BEFORE adding
        projected = " ".join(current_chunk + [text])
        if len(projected) > MAX_CHARS:
            flush_chunk(force=True)

        current_chunk.append(text)

    # Final flush — save whatever's left
    flush_chunk(force=True)

    return chunks