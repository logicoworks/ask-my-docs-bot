"""`app.rag.chunker` のテスト：分割の境界条件とページ番号の対応を検証する。"""

import pytest

from app.rag.chunker import CHUNK_OVERLAP, CHUNK_SIZE, Chunk, split_into_chunks


def test_短いページは1チャンクになる():
    chunks = split_into_chunks(["こんにちは"])

    assert chunks == [Chunk(text="こんにちは", page_number=1)]


def test_空のページリストは空を返す():
    assert split_into_chunks([]) == []


def test_空文字と空白のみのページはスキップされる():
    chunks = split_into_chunks(["", "   \n\t ", "本文あり"])

    assert len(chunks) == 1
    assert chunks[0].text == "本文あり"


def test_ページ番号は1から始まり空ページを飛ばしても元の位置を保つ():
    chunks = split_into_chunks(["1ページ目", "", "3ページ目"])

    assert [c.page_number for c in chunks] == [1, 3]


def test_チャンクサイズと同じ長さのページは1チャンクに収まる():
    chunks = split_into_chunks(["あ" * CHUNK_SIZE])

    assert len(chunks) == 1
    assert len(chunks[0].text) == CHUNK_SIZE


def test_チャンクサイズを1文字超えると2チャンクに分かれる():
    chunks = split_into_chunks(["あ" * (CHUNK_SIZE + 1)])

    assert len(chunks) == 2


def test_隣接するチャンクは指定した文字数だけ重複する():
    text = "".join(str(i % 10) for i in range(CHUNK_SIZE * 2))
    chunks = split_into_chunks([text], chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)

    first, second = chunks[0], chunks[1]
    assert first.text[-CHUNK_OVERLAP:] == second.text[:CHUNK_OVERLAP]


def test_重複なしを指定すると連結して元のテキストに戻る():
    text = "".join(str(i % 10) for i in range(2500))
    chunks = split_into_chunks([text], chunk_size=1000, overlap=0)

    assert "".join(c.text for c in chunks) == text


def test_分割されたチャンクは全て同じページ番号を持つ():
    chunks = split_into_chunks(["あ" * (CHUNK_SIZE * 3)])

    assert len(chunks) > 1
    assert {c.page_number for c in chunks} == {1}


def test_複数ページがそれぞれ独立して分割される():
    chunks = split_into_chunks(["あ" * (CHUNK_SIZE + 1), "い" * (CHUNK_SIZE + 1)])

    assert [c.page_number for c in chunks] == [1, 1, 2, 2]


@pytest.mark.parametrize("overlap", [CHUNK_SIZE, CHUNK_SIZE + 1])
def test_重複がチャンクサイズ以上だと無限ループせずエラーになる(overlap):
    # `start += chunk_size - overlap` の加算量が0以下になると終了しないため、
    # 不正な引数は呼び出し時点で弾く必要がある。
    with pytest.raises(ValueError):
        split_into_chunks(["あ" * 100], chunk_size=CHUNK_SIZE, overlap=overlap)


@pytest.mark.parametrize("chunk_size", [0, -1])
def test_チャンクサイズが0以下だとエラーになる(chunk_size):
    with pytest.raises(ValueError):
        split_into_chunks(["あ" * 100], chunk_size=chunk_size, overlap=0)


def test_負の重複はエラーになる():
    with pytest.raises(ValueError):
        split_into_chunks(["あ" * 100], chunk_size=CHUNK_SIZE, overlap=-1)
