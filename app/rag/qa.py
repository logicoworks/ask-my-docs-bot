"""質問応答（RAG）のオーケストレーション：検索した文書チャンクを根拠にLLMで回答を生成する。"""

from app.llm.claude import ask_claude
from app.rag.embeddings import embed_text
from app.rag.vectorstore import query_chunks

N_RESULTS = 5

PROMPT_TEMPLATE = """あなたはユーザーがLINEで送った文書について回答するアシスタントです。
以下の「参考文書」の内容だけを根拠にして、質問に日本語で答えてください。
参考文書に答えが見つからない場合は、正直に「文書内に該当する情報が見つかりませんでした」と答えてください。

# 参考文書
{context}

# 質問
{question}
"""


def answer_question(question: str) -> str:
    """質問文に類似する文書チャンクを検索し、それを根拠にLLMで回答を生成する。

    Args:
        question: ユーザーからの質問文。

    Returns:
        LLMが生成した回答。登録済み文書が1件もない場合は案内メッセージを返す。

    Raises:
        EmbeddingError: 質問文のベクトル化に失敗した場合。
        VectorStoreError: ベクトルDBの検索に失敗した場合。
        LLMError: Claude APIの呼び出しに失敗した場合。
    """
    question_embedding = embed_text(question)
    matches = query_chunks(question_embedding, n_results=N_RESULTS)

    if not matches:
        return "まだ文書が登録されていません。PDFファイルを送ってから質問してください。"

    context = "\n\n".join(f"[{m['filename']} p.{m['page_number']}]\n{m['text']}" for m in matches)
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    return ask_claude(prompt)
