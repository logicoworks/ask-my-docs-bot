from anthropic import Anthropic

from app.config import ANTHROPIC_API_KEY

MODEL = "claude-sonnet-5"

client = Anthropic(api_key=ANTHROPIC_API_KEY)


def ask_claude(user_text: str) -> str:
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": user_text}],
    )
    return message.content[0].text
