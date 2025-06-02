"""チャットルーター"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from utils.utils import SYSTEM_PROMPT, ChatBot

router = APIRouter(prefix="/chat", tags=["chat"])
templates = Jinja2Templates(directory="templates")


class Message(BaseModel):
    message: str


@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    """チャットページを表示"""
    # セッションからユーザー名を取得
    username = request.session.get("username", "ゲスト")
    return templates.TemplateResponse(
        "chat.html", {"request": request, "username": username}
    )


@router.post("/send")
async def send_message(message: Message, request: Request):
    """メッセージを送信してAIの応答を取得"""
    try:
        # セッションからメッセージ履歴を取得
        default_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages = request.session.get("chat_messages", default_messages)

        # ChatBotインスタンスを作成
        chatbot = ChatBot(temperature=0.1)
        chatbot.messages = messages

        # メッセージを送信して応答を取得
        response = chatbot.get_ai_messages(message.message)

        # 更新されたメッセージ履歴をセッションに保存
        request.session["chat_messages"] = chatbot.messages

        return {"response": response}
    except Exception as e:
        return {"response": f"エラーが発生しました: {str(e)}"}


@router.post("/send/stream")
async def send_message_stream(message: Message, request: Request):
    """メッセージを送信してAIの応答をストリーミング形式で取得"""
    try:
        # セッションからメッセージ履歴を取得
        default_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages = request.session.get("chat_messages", default_messages)

        # ChatBotインスタンスを作成
        chatbot = ChatBot(temperature=0.1)
        chatbot.messages = messages

        async def generate():
            try:
                async for chunk in chatbot.get_ai_messages_stream(message.message):
                    yield f"data: {chunk}\n\n"
            finally:
                # 更新されたメッセージ履歴をセッションに保存
                request.session["chat_messages"] = chatbot.messages

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        return StreamingResponse(
            iter([f"data: エラーが発生しました: {str(e)}\n\n"]),
            media_type="text/event-stream",
        )


@router.post("/clear")
async def clear_chat(request: Request):
    """チャット履歴をクリア"""
    # メッセージ履歴を初期化
    request.session["chat_messages"] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return {"status": "success"}
