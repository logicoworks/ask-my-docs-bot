import chromadb

from app.rag.chunker import Chunk
from app.rag.embeddings import embed_texts

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "documents"

_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(COLLECTION_NAME)


def add_document(filename: str, chunks: list[Chunk]) -> int:
    delete_document(filename)

    embeddings = embed_texts([chunk.text for chunk in chunks])
    ids = [f"{filename}::{i}" for i in range(len(chunks))]
    metadatas = [{"filename": filename, "page_number": chunk.page_number} for chunk in chunks]
    documents = [chunk.text for chunk in chunks]

    _collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
    return len(chunks)


def query_chunks(question_embedding: list[float], n_results: int = 5) -> list[dict]:
    if _collection.count() == 0:
        return []

    result = _collection.query(
        query_embeddings=[question_embedding],
        n_results=min(n_results, _collection.count()),
    )

    matches = []
    for text, metadata in zip(result["documents"][0], result["metadatas"][0]):
        matches.append(
            {
                "text": text,
                "filename": metadata["filename"],
                "page_number": metadata["page_number"],
            }
        )
    return matches


def list_documents() -> dict[str, int]:
    result = _collection.get(include=["metadatas"])
    counts: dict[str, int] = {}
    for metadata in result["metadatas"]:
        filename = metadata["filename"]
        counts[filename] = counts.get(filename, 0) + 1
    return counts


def delete_document(filename: str) -> int:
    result = _collection.delete(where={"filename": filename})
    return result["deleted"]
