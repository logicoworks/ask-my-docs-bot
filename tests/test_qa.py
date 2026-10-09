"""`app.rag.qa` のテスト：根拠の集め方とプロンプトの組み立てを検証する。

Embedding・ベクトルDB・Claude APIはいずれも差し替えて、外部通信なしで検証する。
"""

import pytest

from app.rag import qa


def _chunk(text: str, filename: str = "recipes.pdf", page_number: int = 1) -> dict:
    return {"text": text, "filename": filename, "page_number": page_number, "index": 0}


@pytest.fixture
def captured_prompt(monkeypatch):
    """Claudeに渡されたプロンプトを記録し、固定の回答を返すよう差し替える。"""
    captured: dict[str, str] = {}

    def fake_ask_claude(prompt: str) -> str:
        captured["prompt"] = prompt
        return "回答本文"

    monkeypatch.setattr(qa, "ask_claude", fake_ask_claude)
    return captured


def test_文書が登録されていなければ案内メッセージを返す(monkeypatch, captured_prompt):
    monkeypatch.setattr(qa, "fetch_all_chunks", lambda: [])

    answer = qa.answer_question("ワインに合うレシピを教えて")

    assert answer == qa.NO_DOCUMENTS_MESSAGE
    assert "prompt" not in captured_prompt, "文書がないときはLLMを呼ばない"


def test_文書が小さいときは検索せず全文を渡す(monkeypatch, captured_prompt):
    chunks = [
        _chunk("白ワインに合う魚料理", page_number=1),
        _chunk("牛肉の赤ワイン煮", page_number=2),
    ]
    monkeypatch.setattr(qa, "fetch_all_chunks", lambda: chunks)

    def fail_query(*args, **kwargs):
        raise AssertionError("小さい文書ではベクトル検索を呼ばない")

    monkeypatch.setattr(qa, "query_chunks", fail_query)
    monkeypatch.setattr(qa, "embed_text", fail_query)

    qa.answer_question("ワインに合うレシピを教えて")

    assert "白ワインに合う魚料理" in captured_prompt["prompt"]
    assert "牛肉の赤ワイン煮" in captured_prompt["prompt"]


def test_文書が大きいときはベクトル検索の結果を渡す(monkeypatch, captured_prompt):
    large = [_chunk("あ" * 1000) for _ in range(qa.FULL_CONTEXT_MAX_CHARS // 1000 + 1)]
    monkeypatch.setattr(qa, "fetch_all_chunks", lambda: large)
    monkeypatch.setattr(qa, "embed_text", lambda text: [0.1, 0.2, 0.3])

    requested: dict[str, int] = {}

    def fake_query(embedding, n_results):
        requested["n_results"] = n_results
        return [_chunk("検索で見つかった本文")]

    monkeypatch.setattr(qa, "query_chunks", fake_query)

    qa.answer_question("ワインに合うレシピを教えて")

    assert requested["n_results"] == qa.N_RESULTS
    assert "検索で見つかった本文" in captured_prompt["prompt"]
    assert "あ" * 1000 not in captured_prompt["prompt"], "全文は渡さない"


def test_プロンプトに質問文が含まれる(monkeypatch, captured_prompt):
    monkeypatch.setattr(qa, "fetch_all_chunks", lambda: [_chunk("本文")])

    qa.answer_question("ワインに合うレシピを教えて")

    assert "ワインに合うレシピを教えて" in captured_prompt["prompt"]


def test_プロンプトに出典のファイル名とページ番号が含まれる(monkeypatch, captured_prompt):
    monkeypatch.setattr(
        qa, "fetch_all_chunks", lambda: [_chunk("本文", filename="献立集.pdf", page_number=7)]
    )

    qa.answer_question("質問")

    assert "[献立集.pdf p.7]" in captured_prompt["prompt"]


def test_プロンプトが文書からの推論を許可している(monkeypatch, captured_prompt):
    # 「記載がないので答えられない」と返す症状は、プロンプトが推論を禁じていたことが原因だった。
    # 推論を許可する指示と、創作を禁じる指示が両方あることを確認する。
    monkeypatch.setattr(qa, "fetch_all_chunks", lambda: [_chunk("本文")])

    qa.answer_question("質問")

    prompt = captured_prompt["prompt"]
    assert "推論して回答する" in prompt
    assert "創作しない" in prompt


def test_LLMの回答がそのまま返る(monkeypatch, captured_prompt):
    monkeypatch.setattr(qa, "fetch_all_chunks", lambda: [_chunk("本文")])

    assert qa.answer_question("質問") == "回答本文"


def test_取得件数は5件より多い():
    # 1チャンク800文字で5件（4000文字）では、文書を横断して条件に合うものを挙げる
    # 質問に答えられないため、多めに取る設定であることを固定する。
    assert qa.N_RESULTS > 5
