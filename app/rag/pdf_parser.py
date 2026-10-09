import logging
from io import BytesIO

import pdfplumber

from app.exceptions import PDFParseError

logger = logging.getLogger(__name__)


def extract_pages(pdf_bytes: bytes) -> list[str]:
    """PDFの各ページからテキストを抽出する。

    Args:
        pdf_bytes: PDFファイルのバイナリデータ。

    Returns:
        ページごとのテキストのリスト（ページ番号順、1ページ目がインデックス0）。

    Raises:
        PDFParseError: 暗号化・破損などでPDFとして読み込めなかった場合。
    """
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            return [page.extract_text() or "" for page in pdf.pages]
    except Exception as exc:
        # pdfplumber/pdfminerは暗号化・破損ファイル等で多様な例外を送出し、
        # 公開APIとして安定した例外クラス一覧がないため、ここでは広く捕捉して
        # アプリ内共通のPDFParseErrorに変換する。
        logger.warning("PDFの解析に失敗しました: %s", exc)
        raise PDFParseError("PDFの解析に失敗しました") from exc
