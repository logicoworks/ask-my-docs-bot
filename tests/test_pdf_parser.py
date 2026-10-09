"""`app.rag.pdf_parser` のテスト：PDFの読み込み結果と失敗時の例外変換を検証する。"""

import zlib
from io import BytesIO

import pytest

from app.exceptions import PDFParseError
from app.rag.pdf_parser import extract_pages


def _build_pdf(page_texts: list[str]) -> bytes:
    """テスト用に、指定した文字列を各ページに描画した最小構成のPDFを組み立てる。

    外部のPDFファイルを同梱せずにテストを完結させるため、PDFの構造を直接書き出す。
    ASCIIのみ対応（日本語は埋め込みフォントが必要になるため扱わない）。
    """
    objects: list[bytes] = []
    page_count = len(page_texts)
    # オブジェクト番号: 1=Catalog, 2=Pages, 3=Font, 4以降=各ページのPage/Contents
    kids = " ".join(f"{4 + i * 2} 0 R" for i in range(page_count))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Count {page_count} /Kids [{kids}] >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for i, text in enumerate(page_texts):
        content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + i * 2} 0 R >>".encode()
        )
        objects.append(
            b"<< /Length "
            + str(len(content)).encode()
            + b" >>\nstream\n"
            + content
            + b"\nendstream"
        )

    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")

    xref_offset = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for offset in offsets:
        out.write(f"{offset:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode())
    out.write(f"startxref\n{xref_offset}\n%%EOF\n".encode())
    return out.getvalue()


def test_1ページのPDFからテキストを抽出する():
    pages = extract_pages(_build_pdf(["Hello RAG"]))

    assert len(pages) == 1
    assert "Hello RAG" in pages[0]


def test_ページ数と並び順が保たれる():
    pages = extract_pages(_build_pdf(["First page", "Second page", "Third page"]))

    assert len(pages) == 3
    assert "First page" in pages[0]
    assert "Second page" in pages[1]
    assert "Third page" in pages[2]


def test_テキストを持たないページは空文字になる():
    # extract_text()がNoneを返すケース。Noneのまま返すと後続のstrip()で落ちるため、
    # 空文字に正規化していることを確認する。
    pages = extract_pages(_build_pdf([""]))

    assert pages == [""] or pages[0] == ""


def test_PDFでないバイト列はPDFParseErrorになる():
    with pytest.raises(PDFParseError):
        extract_pages(b"this is not a pdf")


def test_空のバイト列はPDFParseErrorになる():
    with pytest.raises(PDFParseError):
        extract_pages(b"")


def test_壊れたPDFはPDFParseErrorになる():
    broken = _build_pdf(["Hello"])[:80]

    with pytest.raises(PDFParseError):
        extract_pages(broken)


def test_PDFParseErrorは元の例外を原因として保持する():
    # ログ調査時に元の例外を辿れるようにしているため、from句が維持されていることを確認する。
    with pytest.raises(PDFParseError) as exc_info:
        extract_pages(zlib.compress(b"not a pdf"))

    assert exc_info.value.__cause__ is not None
