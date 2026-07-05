from fastapi import FastAPI, Header, HTTPException, Request
from linebot.v3.exceptions import InvalidSignatureError

from app.line.handler import handler

app = FastAPI()


@app.post("/callback")
async def callback(request: Request, x_line_signature: str = Header(...)) -> str:
    body = await request.body()
    try:
        handler.handle(body.decode(), x_line_signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"
