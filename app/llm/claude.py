import logging

from anthropic import Anthropic, APIError

from app.config import ANTHROPIC_API_KEY
from app.exceptions import LLMError

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "あなたはLINEのチャットで応答するアシスタントです。"
    "LINEはMarkdown記法を表示できないため、**太字**や見出し(#)、箇条書きの記号(-)などは使わず、"
    "プレーンテキストのみで簡潔に回答してください。"
)

logger = logging.getLogger(__name__)

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def ask_claude(user_text: str) -> str:
    """Claude APIにテキストを送り、回答を取得する。

    Args:
        user_text: ユーザーからの質問文（RAGの場合は参考文書を含めたプロンプト）。

    Returns:
        Claudeが生成した回答テキスト。

    Raises:
        LLMError: Claude APIの呼び出しに失敗した場合（レート制限・接続エラー等）。
    """
    try:
        message = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_text}],
        )
    except APIError as exc:
        logger.warning("Claude APIの呼び出しに失敗しました: %s", exc)
        raise LLMError("Claude APIの呼び出しに失敗しました") from exc

    text_blocks = [block.text for block in message.content if block.type == "text"]
    return "".join(text_blocks)
