"""LINEへの返信メッセージ文言を集約するモジュール。

文言をハンドラーから切り離すことで、表現の統一やトーン調整を1箇所で完結できるようにする。
"""

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 非機能要件のファイルサイズ上限（10MB）に準拠

UNSUPPORTED_FILE_TYPE = "PDFファイルのみ対応しています。"
FILE_TOO_LARGE = "ファイルサイズが大きすぎます（10MBまでのPDFに対応しています）。"
PDF_PARSE_FAILED = (
    "PDFの解析に失敗しました。ファイルが破損しているか、暗号化されている可能性があります。"
)
NO_TEXT_EXTRACTED = "PDFからテキストを抽出できませんでした（画像のみのPDF等の可能性があります）。"
EXTERNAL_SERVICE_ERROR = (
    "現在、外部サービスが混み合っているか一時的に利用できません。"
    "しばらくしてから再度お試しください。"
)
UNEXPECTED_ERROR = "予期しないエラーが発生しました。しばらくしてから再度お試しください。"


def document_registered(file_name: str, chunk_count: int) -> str:
    """PDF登録完了時の案内メッセージを組み立てる。"""
    return f"「{file_name}」を登録しました（{chunk_count}件のチャンクに分割）。質問してください。"


def document_deleted(filename: str) -> str:
    """文書削除完了時の案内メッセージを組み立てる。"""
    return f"「{filename}」を削除しました。"


def document_not_found(filename: str) -> str:
    """削除対象の文書が見つからなかった場合の案内メッセージを組み立てる。"""
    return f"「{filename}」という文書は見つかりませんでした。"


def document_list(documents: dict[str, int]) -> str:
    """登録済み文書の一覧メッセージを組み立てる。

    Args:
        documents: ファイル名をキー、チャンク数を値とする辞書。
    """
    if not documents:
        return "登録済みの文書はありません。"
    lines = [f"・{name}（{count}チャンク）" for name, count in documents.items()]
    return "登録済みの文書:\n" + "\n".join(lines)
