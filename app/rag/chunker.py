"""PDFから抽出したテキストを、Embedding生成に適した単位に分割する。"""

from dataclasses import dataclass

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


@dataclass
class Chunk:
    """分割されたテキストの断片と、その出典ページ番号。"""

    text: str
    page_number: int


def split_into_chunks(
    pages: list[str],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[Chunk]:
    """ページごとのテキストを、固定長・オーバーラップ付きのチャンクに分割する。

    ページ単位で分割することで、検索結果からページ番号（出典）を復元できるようにする。
    オーバーラップを持たせるのは、チャンクの境界で文脈が途切れて検索精度が落ちるのを防ぐため。

    Args:
        pages: ページごとのテキスト（`pdf_parser.extract_pages`の出力）。
        chunk_size: 1チャンクあたりの最大文字数。
        overlap: 隣接チャンク間で重複させる文字数。

    Returns:
        ページ番号付きのチャンクのリスト。空ページはスキップされる。
    """
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
