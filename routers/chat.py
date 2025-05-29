"""チャットルーター"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from utils.utils import generate_ai_reply

router = APIRouter(prefix="/chat", tags=["chat"])
templates = Jinja2Templates(directory="templates")


class Message(BaseModel):
    message: str


@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    """チャットページを表示"""
    return templates.TemplateResponse("chat.html", {"request": request})


@router.post("/send")
async def send_message(message: Message):
    """メッセージを送信してAIの応答を取得"""
    try:
        response = generate_ai_reply(message.message, temperature=0.1)
        return {"response": response}
    except Exception as e:
        return {"response": f"エラーが発生しました: {str(e)}"}
