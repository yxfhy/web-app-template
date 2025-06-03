"""チャットルーター"""

import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from utils.utils import SYSTEM_PROMPT, ChatBot, create_github_file

router = APIRouter(prefix="/chat", tags=["chat"])
templates = Jinja2Templates(directory="templates")

# グローバルなChatBotインスタンス
chatbot = None


class Message(BaseModel):
    message: str


class PushData(BaseModel):
    markdownBuffer: str


@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    """チャットページを表示"""
    global chatbot
    username = request.session.get("username", "ゲスト")
    # ChatBotインスタンスを生成
    if chatbot is None:
        chatbot = ChatBot(temperature=0.1)
    return templates.TemplateResponse(
        "chat.html", {"request": request, "username": username}
    )


@router.post("/send")
async def send_message(message: Message, request: Request):
    """メッセージを送信してAIの応答を取得"""
    global chatbot
    try:
        default_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages = request.session.get("chat_messages", default_messages)
        if chatbot is None:
            chatbot = ChatBot(temperature=0.1)
        chatbot.messages = messages
        response = chatbot.get_ai_messages(message.message)
        request.session["chat_messages"] = chatbot.messages
        return {"response": response}
    except Exception as e:
        return {"response": f"エラーが発生しました: {str(e)}"}


@router.post("/send/stream")
async def send_message_stream(message: Message, request: Request):
    """メッセージを送信してAIの応答をストリーミング形式で取得"""
    global chatbot
    try:
        default_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if chatbot is None:
            chatbot = ChatBot(temperature=0.1)

        async def generate():
            try:
                async for chunk in chatbot.get_ai_messages_stream(message.message):
                    data = {"chunk": chunk}
                    yield f"data: {json.dumps(data)}\n\n"
            finally:
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
    global chatbot
    if chatbot is not None:
        chatbot.clear_messages()
    request.session["chat_messages"] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return {"status": "success"}


@router.post("/push")
async def push_to_github(request: Request, data: PushData):

    # セッションからユーザー名を取得
    username = request.session.get("username")
    if not username or username != "yxfhy":
        raise HTTPException(status_code=403, detail="権限がありません")

    try:
        # GitHubにプッシュ
        result = create_github_file("yxfhy", "memo", data.markdownBuffer)
        return {"status": "success", "url": result["content"]["html_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
