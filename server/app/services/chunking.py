import re

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into retrieval-sized chunks.

    Strategy:
    1. Respect structure: split on line breaks (paragraphs, list items, headings).
    2. Pack consecutive paragraphs into one chunk until it would exceed `chunk_size`.
    3. A paragraph that is too long on its own is split on sentence boundaries,
       and a sentence that is still too long is split on word boundaries.
    4. Each new chunk starts with the last ~`overlap` characters of the previous
       one, so a fact spanning a boundary still appears whole in some chunk.

    Chunks are therefore at most about `chunk_size + overlap` characters.
    """
    chunks: list[str] = []
    current = ""
    for piece in _split_into_pieces(text, chunk_size):
        candidate = f"{current}\n{piece}" if current else piece
        if len(candidate) <= chunk_size:
            current = candidate
            continue
        chunks.append(current)
        tail = _tail(current, overlap)
        current = f"{tail}\n{piece}" if tail else piece
    if current:
        chunks.append(current)
    return chunks


def _split_into_pieces(text: str, max_length: int) -> list[str]:
    """Break text into paragraphs/sentences/word-runs that each fit in `max_length`."""
    pieces: list[str] = []
    for paragraph in (line.strip() for line in text.splitlines()):
        if not paragraph:
            continue
        if len(paragraph) <= max_length:
            pieces.append(paragraph)
            continue
        for sentence in _SENTENCE_BOUNDARY.split(paragraph):
            if len(sentence) <= max_length:
                pieces.append(sentence)
            else:
                pieces.extend(_split_on_words(sentence, max_length))
    return pieces


def _split_on_words(text: str, max_length: int) -> list[str]:
    parts: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if len(candidate) <= max_length:
            current = candidate
            continue
        if current:
            parts.append(current)
        # A single "word" longer than a chunk (e.g. a giant URL): hard-split it.
        while len(word) > max_length:
            parts.append(word[:max_length])
            word = word[max_length:]
        current = word
    if current:
        parts.append(current)
    return parts


def _tail(text: str, length: int) -> str:
    """The last ~`length` characters of `text`, starting at a word boundary."""
    if length <= 0:
        return ""
    if len(text) <= length:
        return text
    tail = text[-length:]
    return tail.split(" ", 1)[1] if " " in tail else tail
