import logging

import chromadb

from app.exceptions import VectorStoreError
from app.rag.chunker import Chunk
from app.rag.embeddings import embed_texts

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "documents"

logger = logging.getLogger(__name__)

_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(COLLECTION_NAME)


def add_document(filename: str, chunks: list[Chunk]) -> int:
    """文書のチャンクをEmbedding化してベクトルDBに登録する。

    同名ファイルが既に登録済みの場合は、先に削除してから登録し直す（上書き）。

    Args:
        filename: 文書のファイル名（識別子として使用）。
        chunks: 登録するチャンクのリスト。

    Returns:
        登録したチャンク数。

    Raises:
        VectorStoreError: ベクトルDBへの書き込みに失敗した場合。
    """
    delete_document(filename)

    embeddings = embed_texts([chunk.text for chunk in chunks])
    ids = [f"{filename}::{i}" for i in range(len(chunks))]
    metadatas = [{"filename": filename, "page_number": chunk.page_number} for chunk in chunks]
    documents = [chunk.text for chunk in chunks]

    try:
        _collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
    except Exception as exc:
        logger.warning("ベクトルDBへの登録に失敗しました: %s", exc)
        raise VectorStoreError("ベクトルDBへの登録に失敗しました") from exc
    return len(chunks)


def query_chunks(question_embedding: list[float], n_results: int = 5) -> list[dict]:
    """質問文のベクトルに類似するチャンクを検索する。

    Args:
        question_embedding: 質問文のベクトル表現。
        n_results: 取得する上位件数。

    Returns:
        類似チャンクのリスト（各要素は text/filename/page_number を持つ辞書）。
        登録済み文書が1件もない場合は空リストを返す。

    Raises:
        VectorStoreError: ベクトルDBの検索に失敗した場合。
    """
    try:
        if _collection.count() == 0:
            return []

        result = _collection.query(
            query_embeddings=[question_embedding],
            n_results=min(n_results, _collection.count()),
        )
    except Exception as exc:
        logger.warning("ベクトルDBの検索に失敗しました: %s", exc)
        raise VectorStoreError("ベクトルDBの検索に失敗しました") from exc

    matches = []
    for text, metadata in zip(result["documents"][0], result["metadatas"][0], strict=True):
        matches.append(
            {
                "text": text,
                "filename": metadata["filename"],
                "page_number": metadata["page_number"],
            }
        )
    return matches


def list_documents() -> dict[str, int]:
    """登録済み文書ごとのチャンク数を取得する。

    Returns:
        ファイル名をキー、チャンク数を値とする辞書。

    Raises:
        VectorStoreError: ベクトルDBの取得に失敗した場合。
    """
    try:
        result = _collection.get(include=["metadatas"])
    except Exception as exc:
        logger.warning("ベクトルDBの一覧取得に失敗しました: %s", exc)
        raise VectorStoreError("ベクトルDBの一覧取得に失敗しました") from exc

    counts: dict[str, int] = {}
    for metadata in result["metadatas"]:
        filename = metadata["filename"]
        counts[filename] = counts.get(filename, 0) + 1
    return counts


def fetch_all_chunks() -> list[dict]:
    """登録済みの全チャンクを、ファイル名・ページ番号順に取得する。

    文書全体が十分に小さい場合は、ベクトル検索を介さず全文をLLMに渡すために使う
    （`app.rag.qa` を参照）。上位k件の検索は「文書を横断して条件に合うものを挙げる」
    種類の質問に弱く、全文を渡せるならその方が精度が高い。

    Returns:
        全チャンクのリスト（各要素は text/filename/page_number を持つ辞書）。

    Raises:
        VectorStoreError: ベクトルDBの取得に失敗した場合。
    """
    try:
        result = _collection.get(include=["metadatas", "documents"])
    except Exception as exc:
        logger.warning("ベクトルDBの全件取得に失敗しました: %s", exc)
        raise VectorStoreError("ベクトルDBの全件取得に失敗しました") from exc

    # ChromaDBのget()は返却順を保証しないため、IDに埋め込んだ連番（`add_document`が付与）で
    # 元の文書の並びに復元する。全文をLLMに渡すときに前後の文脈が崩れないようにするため。
    chunks = [
        {
            "text": text,
            "filename": metadata["filename"],
            "page_number": metadata["page_number"],
            "index": int(chunk_id.rsplit("::", 1)[1]),
        }
        for chunk_id, text, metadata in zip(
            result["ids"], result["documents"], result["metadatas"], strict=True
        )
    ]
    chunks.sort(key=lambda c: (c["filename"], c["index"]))
    return chunks


def delete_document(filename: str) -> int:
    """指定したファイル名の文書をベクトルDBから削除する。

    Args:
        filename: 削除対象のファイル名。

    Returns:
        削除したチャンク数（該当なしの場合は0）。

    Raises:
        VectorStoreError: ベクトルDBの削除操作に失敗した場合。
    """
    try:
        result = _collection.delete(where={"filename": filename})
    except Exception as exc:
        logger.warning("ベクトルDBからの削除に失敗しました: %s", exc)
        raise VectorStoreError("ベクトルDBからの削除に失敗しました") from exc
    return result["deleted"]
