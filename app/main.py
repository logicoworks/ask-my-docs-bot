"""FastAPIアプリケーションのエントリーポイント（LINE Webhookの受け口）。"""

import logging

from fastapi import FastAPI, Header, HTTPException, Request
from linebot.v3.exceptions import InvalidSignatureError

from app.line.handler import handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(...)) -> str:
    """LINEからのWebhookを受信するエンドポイント。"""
    body = await request.body()
    try:
        handler.handle(body.decode(), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature") from None
    except Exception:
        # 個々のメッセージハンドラー内の例外は app.line.handler.handle_errors で捕捉済みだが、
        # Webhook処理自体で想定外のエラーが起きた場合に備える。
        # ここで500を返すとLINEプラットフォームが再送を繰り返すため、ログに残した上で200を返す。
        logger.exception("Webhook処理中に予期しないエラーが発生しました")
    return "OK"
