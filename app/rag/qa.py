"""質問応答（RAG）のオーケストレーション：検索した文書チャンクを根拠にLLMで回答を生成する。"""

from app.llm.claude import ask_claude
from app.rag.embeddings import embed_text
from app.rag.vectorstore import fetch_all_chunks, query_chunks

# ベクトル検索で取得するチャンク数。1チャンク800文字なので、20件で約16000文字。
# 少なすぎると「文書を横断して条件に合うものを挙げる」質問に答えられないため、
# 絞り込みは検索側ではなくLLM側に任せる方針で多めに取る。
N_RESULTS = 20

# 登録済み文書の総文字数がこれ以下なら、ベクトル検索を介さず全文をLLMに渡す。
# 上位k件の検索は、質問の条件が文書中の語と一致しない場合（例：材料から「ワインに合う」
# ものを選ぶ）に原理的に弱い。全文が収まるなら渡した方が確実に精度が高い。
FULL_CONTEXT_MAX_CHARS = 100_000

PROMPT_TEMPLATE = """あなたはユーザーがLINEで送った文書について回答するアシスタントです。

以下のルールに従って回答してください。

1. 「参考文書」に書かれている内容を根拠に回答する。文書に書かれていない事実を創作しない。
2. 質問の条件が文書に直接書かれていなくても、文書の記述から判断できることは推論して回答する。
   条件に当てはまるものを文書の中から選び出す質問であれば、記述内容から判断して挙げる。
3. 回答には、根拠にした箇所のファイル名とページ番号を添える。
4. 文書の内容からどう判断しても答えられない場合にのみ、
   「文書内に該当する情報が見つかりませんでした」と答える。

# 参考文書
{context}

# 質問
{question}
"""

NO_DOCUMENTS_MESSAGE = "まだ文書が登録されていません。PDFファイルを送ってから質問してください。"


def _format_context(chunks: list[dict]) -> str:
    """チャンクのリストを、出典付きのプロンプト用テキストに整形する。"""
    return "\n\n".join(f"[{c['filename']} p.{c['page_number']}]\n{c['text']}" for c in chunks)


def _collect_context_chunks(question: str) -> list[dict]:
    """回答の根拠として渡すチャンクを集める。

    登録済み文書が十分に小さければ全文を返し、大きければ質問に類似する上位件数を返す。

    Args:
        question: ユーザーからの質問文。

    Returns:
        根拠として渡すチャンクのリスト。登録済み文書が1件もない場合は空リスト。
    """
    all_chunks = fetch_all_chunks()
    if not all_chunks:
        return []

    total_chars = sum(len(chunk["text"]) for chunk in all_chunks)
    if total_chars <= FULL_CONTEXT_MAX_CHARS:
        return all_chunks

    question_embedding = embed_text(question)
    return query_chunks(question_embedding, n_results=N_RESULTS)


def answer_question(question: str) -> str:
    """登録済み文書を根拠に、質問への回答をLLMで生成する。

    Args:
        question: ユーザーからの質問文。

    Returns:
        LLMが生成した回答。登録済み文書が1件もない場合は案内メッセージを返す。

    Raises:
        EmbeddingError: 質問文のベクトル化に失敗した場合。
        VectorStoreError: ベクトルDBの取得・検索に失敗した場合。
        LLMError: Claude APIの呼び出しに失敗した場合。
    """
    chunks = _collect_context_chunks(question)

    if not chunks:
        return NO_DOCUMENTS_MESSAGE

    prompt = PROMPT_TEMPLATE.format(context=_format_context(chunks), question=question)
    return ask_claude(prompt)
