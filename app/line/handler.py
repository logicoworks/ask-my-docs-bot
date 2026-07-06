from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    MessagingApiBlob,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import FileMessageContent, MessageEvent, TextMessageContent

from app.config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET
from app.rag.chunker import split_into_chunks
from app.rag.pdf_parser import extract_pages
from app.rag.qa import answer_question
from app.rag.vectorstore import add_document, delete_document, list_documents

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

LIST_COMMAND = "一覧"
DELETE_PREFIX = "削除 "


def reply(reply_token: str, text: str) -> None:
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=text)])
        )


@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event: MessageEvent) -> None:
    text = event.message.text.strip()

    if text == LIST_COMMAND:
        reply_text = format_document_list()
    elif text.startswith(DELETE_PREFIX):
        filename = text[len(DELETE_PREFIX) :].strip()
        deleted_count = delete_document(filename)
        if deleted_count > 0:
            reply_text = f"「{filename}」を削除しました。"
        else:
            reply_text = f"「{filename}」という文書は見つかりませんでした。"
    else:
        reply_text = answer_question(text)

    reply(event.reply_token, reply_text)


@handler.add(MessageEvent, message=FileMessageContent)
def handle_file_message(event: MessageEvent) -> None:
    file_name = event.message.file_name

    if not file_name.lower().endswith(".pdf"):
        reply(event.reply_token, "PDFファイルのみ対応しています。")
        return

    with ApiClient(configuration) as api_client:
        pdf_bytes = bytes(MessagingApiBlob(api_client).get_message_content(event.message.id))

    pages = extract_pages(pdf_bytes)
    chunks = split_into_chunks(pages)

    if not chunks:
        reply(
            event.reply_token,
            "PDFからテキストを抽出できませんでした（画像のみのPDF等の可能性があります）。",
        )
        return

    add_document(file_name, chunks)
    reply(
        event.reply_token,
        f"「{file_name}」を登録しました（{len(chunks)}件のチャンクに分割）。質問してください。",
    )


def format_document_list() -> str:
    documents = list_documents()
    if not documents:
        return "登録済みの文書はありません。"
    lines = [f"・{name}（{count}チャンク）" for name, count in documents.items()]
    return "登録済みの文書:\n" + "\n".join(lines)
