from dataclasses import dataclass

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


@dataclass
class Chunk:
    text: str
    page_number: int


def split_into_chunks(
    pages: list[str],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page_number, page_text in enumerate(pages, start=1):
        page_text = page_text.strip()
        if not page_text:
            continue

        start = 0
        while start < len(page_text):
            end = start + chunk_size
            chunk_text = page_text[start:end].strip()
            if chunk_text:
                chunks.append(Chunk(text=chunk_text, page_number=page_number))
            start += chunk_size - overlap

    return chunks
