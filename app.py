"""Web App Template – Minimal web application (app.py)

依存:
  fastapi  ≥ 0.110
  uvicorn  ≥ 0.27
  openai   ≥ 1.6
  python-dotenv
"""

from __future__ import annotations

import asyncio
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from database import create_db_and_tables
from routers import auth, chat, memo
from utils.utils import generate_ai_reply, initialize_clients

BASE_DIR = Path(__file__).resolve()
BASE_DIR = BASE_DIR.parent

api_keys_and_clients = initialize_clients()
# API キーやクライアントの初期化
(
    OPENAI_API_KEY,
    OPENAI_MODEL,
    openai_client,
    SYSTEM_PROMPT,
) = api_keys_and_clients


# テンプレートディレクトリのパスを指定
templates = Jinja2Templates(directory="templates")


def convert_urls_to_links(text: str) -> str:
    """テキスト内のURLをHTMLリンクに変換する"""
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    return re.sub(
        url_pattern,
        lambda m: f'<a href="{m.group(0)}" target="_blank" rel="noopener noreferrer">{m.group(0)}</a>',
        text,
    )


app = FastAPI()

# データベーステーブルの作成
create_db_and_tables()

# ★セッション（署名付き Cookie）を有効化
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET_KEY)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# ルーター登録
app.include_router(auth.router)
app.include_router(memo.router)
app.include_router(chat.router)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst).strftime("%Y-%m-%d %H:%M:%S")

    username = request.session.get("username")  # ★セッション取得

    # ユーザー名があれば呼びかけに含める
    prompt = (
        f"現在{now}、今日、この時間帯にふさわしい、"
        f"でもちょっと変わった挨拶をして"
        + (f"。ユーザー名「{username}」に呼びかけて" if username else "")
    )

    try:
        ai_message: str = await asyncio.to_thread(generate_ai_reply, prompt, 0.99)
        # URLをリンクに変換
        ai_message = convert_urls_to_links(ai_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "message": ai_message,
        },
    )


# ------------------------------------------------------------------
# ローカル実行用

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000)
