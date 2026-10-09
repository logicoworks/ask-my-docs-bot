import logging

from openai import APIError, OpenAI

from app.config import OPENAI_API_KEY
from app.exceptions import EmbeddingError

MODEL = "text-embedding-3-small"

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """複数のテキストをベクトル表現に変換する。

    Args:
        texts: ベクトル化する文字列のリスト。

    Returns:
        入力と同じ順序のベクトル（embedding）のリスト。

    Raises:
        EmbeddingError: OpenAI Embeddings APIの呼び出しに失敗した場合。
    """
    try:
        response = client.embeddings.create(model=MODEL, input=texts)
    except APIError as exc:
        logger.warning("Embedding APIの呼び出しに失敗しました: %s", exc)
        raise EmbeddingError("Embedding APIの呼び出しに失敗しました") from exc
    return [item.embedding for item in response.data]


def embed_text(text: str) -> list[float]:
    """単一のテキストをベクトル表現に変換する。

    Args:
        text: ベクトル化する文字列。

    Returns:
        テキストのベクトル（embedding）。

    Raises:
        EmbeddingError: OpenAI Embeddings APIの呼び出しに失敗した場合。
    """
    return embed_texts([text])[0]
