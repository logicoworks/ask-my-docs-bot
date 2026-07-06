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
    question_embedding = embed_text(question)
    matches = query_chunks(question_embedding, n_results=N_RESULTS)

    if not matches:
        return "まだ文書が登録されていません。PDFファイルを送ってから質問してください。"

    context = "\n\n".join(
        f"[{m['filename']} p.{m['page_number']}]\n{m['text']}" for m in matches
    )
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    return ask_claude(prompt)
