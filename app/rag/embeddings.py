from openai import OpenAI

from app.config import OPENAI_API_KEY

MODEL = "text-embedding-3-small"

client = OpenAI(api_key=OPENAI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model=MODEL, input=texts)
    return [item.embedding for item in response.data]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
