from anthropic import Anthropic

from app.config import ANTHROPIC_API_KEY

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "あなたはLINEのチャットで応答するアシスタントです。"
    "LINEはMarkdown記法を表示できないため、**太字**や見出し(#)、箇条書きの記号(-)などは使わず、"
    "プレーンテキストのみで簡潔に回答してください。"
)

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def ask_claude(user_text: str) -> str:
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_text}],
    )
    text_blocks = [block.text for block in message.content if block.type == "text"]
    return "".join(text_blocks)
