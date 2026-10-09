"""アプリケーション内で発生しうるエラーを分類するための例外クラス群。

外部サービス（LLM/Embedding/ベクトルDB）やユーザー入力起因のエラーを区別することで、
呼び出し側（`app/line/handler.py`）でエラーの種類ごとに適切な案内メッセージを出し分けられるようにする。
"""


class AppError(Exception):
    """アプリケーション内で送出する例外の基底クラス。"""


class PDFParseError(AppError):
    """PDFの解析に失敗したときに送出する（暗号化・破損したファイル等）。"""


class EmbeddingError(AppError):
    """Embedding API（OpenAI）の呼び出しに失敗したときに送出する。"""


class LLMError(AppError):
    """LLM API（Claude）の呼び出しに失敗したときに送出する。"""


class VectorStoreError(AppError):
    """ベクトルDB（ChromaDB）の操作に失敗したときに送出する。"""
