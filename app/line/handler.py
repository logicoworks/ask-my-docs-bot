import logging
from collections.abc import Callable
from functools import wraps

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
from app.exceptions import AppError, EmbeddingError, LLMError, PDFParseError, VectorStoreError
from app.line import messages
from app.rag.chunker import split_into_chunks
from app.rag.pdf_parser import extract_pages
from app.rag.qa import answer_question
from app.rag.vectorstore import add_document, delete_document, list_documents

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

logger = logging.getLogger(__name__)

LIST_COMMAND = "一覧"
DELETE_PREFIX = "削除 "

# AppErrorのサブクラスごとに、ユーザーに返す案内メッセージを切り替える。
# PDFParseErrorはユーザーのファイル起因、それ以外は外部サービス起因として区別する。
ERROR_MESSAGES: dict[type[AppError], str] = {
    PDFParseError: messages.PDF_PARSE_FAILED,
    EmbeddingError: messages.EXTERNAL_SERVICE_ERROR,
    LLMError: messages.EXTERNAL_SERVICE_ERROR,
    VectorStoreError: messages.EXTERNAL_SERVICE_ERROR,
}


def handle_errors(func: Callable[[MessageEvent], None]) -> Callable[[MessageEvent], None]:
    """イベントハンドラーの例外を捕捉し、ユーザーへエラーメッセージを返す共通処理。

    詳細なエラー内容はログにのみ残し、LINEへの返信は簡潔な案内文に統一する。
    """

    @wraps(func)
    def wrapper(event: MessageEvent) -> None:
        try:
            func(event)
        except AppError as exc:
            reply_text = ERROR_MESSAGES.get(type(exc), messages.UNEXPECTED_ERROR)
            logger.warning("%s: %s", func.__name__, exc)
            reply(event.reply_token, reply_text)
        except Exception:
            logger.exception("%sで予期しないエラーが発生しました", func.__name__)
            reply(event.reply_token, messages.UNEXPECTED_ERROR)

    return wrapper


def reply(reply_token: str, text: str) -> None:
    """LINEのreply APIでテキストメッセージを1件返信する。"""
    with ApiClient(configuration) as api_client:
        MessagingApi(api_client).reply_message(
            ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=text)])
        )


@handler.add(MessageEvent, message=TextMessageContent)
@handle_errors
def handle_text_message(event: MessageEvent) -> None:
    """テキストメッセージを受信し、コマンドまたは質問として処理する。"""
    text = event.message.text.strip()

    if text == LIST_COMMAND:
        reply_text = messages.document_list(list_documents())
    elif text.startswith(DELETE_PREFIX):
        filename = text[len(DELETE_PREFIX) :].strip()
        deleted_count = delete_document(filename)
        if deleted_count > 0:
            reply_text = messages.document_deleted(filename)
        else:
            reply_text = messages.document_not_found(filename)
    else:
        reply_text = answer_question(text)

    reply(event.reply_token, reply_text)


@handler.add(MessageEvent, message=FileMessageContent)
@handle_errors
def handle_file_message(event: MessageEvent) -> None:
    """ファイルメッセージを受信し、PDFであれば解析してベクトルDBに登録する。"""
    file_name = event.message.file_name

    if not file_name.lower().endswith(".pdf"):
        reply(event.reply_token, messages.UNSUPPORTED_FILE_TYPE)
        return

    if event.message.file_size > messages.MAX_FILE_SIZE_BYTES:
        reply(event.reply_token, messages.FILE_TOO_LARGE)
        return

    with ApiClient(configuration) as api_client:
        pdf_bytes = bytes(MessagingApiBlob(api_client).get_message_content(event.message.id))

    pages = extract_pages(pdf_bytes)
    chunks = split_into_chunks(pages)

    if not chunks:
        reply(event.reply_token, messages.NO_TEXT_EXTRACTED)
        return

    add_document(file_name, chunks)
    reply(event.reply_token, messages.document_registered(file_name, len(chunks)))
