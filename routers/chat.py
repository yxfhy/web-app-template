"""チャットルーター"""

import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from utils.utils import SYSTEM_PROMPT, ChatBot, create_github_file

# アプリ起動時に一度だけ設定
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s [%(levelname)s] %(message)s"
)

router = APIRouter(prefix="/chat", tags=["chat"])
templates = Jinja2Templates(directory="templates")

# グローバルなChatBotインスタンス
chatbots = {}


class Message(BaseModel):
    message: str


class PushData(BaseModel):
    markdownBuffer: str


@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    """チャットページを表示"""
    username = request.session.get("username", "ゲスト")
    # ChatBotインスタンスをユーザーごとに生成
    if username not in chatbots:
        chatbots[username] = ChatBot(temperature=0.1)
        # ─────────────────────────────────────────────
        logging.warning(
            "⚠️ ChatBot new: 毎回インスタンス再生成中\n"
            "   • モデル接続・メモリを都度確保します（負荷↑）\n"
            "   • 同一ユーザーで別ウィンドウで開いたチャットも同一のインスタンスで処理されます！！！\n"
            "   • 履歴は Cookie セッション依存 → サイズ超過で消失の恐れ\n"
            "   • 多人数運用や長期保存が必要なら Redis / DB へ移行推奨\n"
            "   • メモリリーク防止の GC or TTL 設計を忘れずに"
        )
        # ─────────────────────────────────────────────
    return templates.TemplateResponse(
        "chat.html", {"request": request, "username": username}
    )


@router.post("/send")
async def send_message(message: Message, request: Request):
    """メッセージを送信してAIの応答を取得"""
    try:
        username = request.session.get("username", "ゲスト")
        default_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages = request.session.get("chat_messages", default_messages)
        if username not in chatbots:
            chatbots[username] = ChatBot(temperature=0.1)

            # ─────────────────────────────────────────────
            logging.warning(
                "⚠️ ChatBot new: 毎回インスタンス再生成中\n"
                "   • モデル接続・メモリを都度確保します（負荷↑）\n"
                "   • 履歴は Cookie セッション依存 → サイズ超過で消失の恐れ\n"
                "   • 多人数運用や長期保存が必要なら Redis / DB へ移行推奨\n"
                "   • メモリリーク防止の GC or TTL 設計を忘れずに"
            )
            # ─────────────────────────────────────────────
        chatbots[username].messages = messages
        response = chatbots[username].get_ai_messages(message.message)
        request.session["chat_messages"] = chatbots[username].messages
        return {"response": response}
    except Exception as e:
        return {"response": f"エラーが発生しました: {str(e)}"}


@router.post("/send/stream")
async def send_message_stream(message: Message, request: Request):
    """メッセージを送信してAIの応答をストリーミング形式で取得"""
    try:
        username = request.session.get("username", "ゲスト")
        default_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if username not in chatbots:
            chatbots[username] = ChatBot(temperature=0.1)

        async def generate():
            try:
                async for chunk in chatbots[username].get_ai_messages_stream(
                    message.message
                ):
                    data = {"chunk": chunk}
                    yield f"data: {json.dumps(data)}\n\n"
            finally:
                request.session["chat_messages"] = chatbots[username].messages

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        return StreamingResponse(
            iter([f"data: エラーが発生しました: {str(e)}\n\n"]),
            media_type="text/event-stream",
        )


@router.post("/clear")
async def clear_chat(request: Request):
    """チャット履歴をクリア"""
    username = request.session.get("username", "ゲスト")
    if username in chatbots:
        chatbots[username].clear_messages()
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
