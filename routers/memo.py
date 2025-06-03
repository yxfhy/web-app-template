import re
import uuid
from datetime import datetime, timedelta, timezone
from math import ceil

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.memo import MemoModel, create_memo, delete_memo, get_db, get_user_memos
from utils.utils import (
    create_github_file,
    delete_github_file,
    get_github_repo_contents,
    get_url_title,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def convert_urls_to_links(text: str) -> str:
    """テキスト内のURLをHTMLリンクに変換する"""
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'

    def replace_url(match):
        url = match.group(0)
        title = get_url_title(url)
        display_text = f"{title} ({url})" if title else url
        return (
            f'<a href="{url}" target="_blank" '
            f'rel="noopener noreferrer">{display_text}</a>'
        )

    return re.sub(url_pattern, replace_url, text)


# メモのデータモデル（API用）
class Memo(BaseModel):
    id: str
    content: str
    created_at: datetime
    username: str

    class Config:
        orm_mode = True


@router.get("/memo", response_class=HTMLResponse)
async def memo_page(
    request: Request,
    sort: str = "newest",
    limit: int = 10,  # デフォルトは10件
    page: int = 1,  # デフォルトは1ページ目
    search: str = None,  # 検索クエリ
    db: Session = Depends(get_db),
):
    # セッションからユーザー名を取得
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)

    # 表示件数の制限を10, 50のいずれかに制限
    if limit not in [10, 50]:
        limit = 10

    # ページ番号の制限（1以上）
    if page < 1:
        page = 1

    # ユーザーのメモを取得（検索クエリがある場合は検索）
    user_memos = get_user_memos(db, username, search)

    # 並び替え
    if sort == "oldest":
        user_memos.sort(key=lambda x: x.created_at)
    else:  # newest
        user_memos.sort(key=lambda x: x.created_at, reverse=True)

    # 総ページ数を計算
    total_memos = len(user_memos)
    total_pages = ceil(total_memos / limit)

    # ページ番号の制限（最大ページ数以下）
    if page > total_pages and total_pages > 0:
        page = total_pages

    # 表示するメモを取得
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    user_memos = user_memos[start_idx:end_idx]

    # ChatBotインスタンスを削除
    from routers import chat

    chat.chatbot = None  # noqa: E501

    return templates.TemplateResponse(
        "memo.html",
        {
            "request": request,
            "memos": user_memos,
            "sort": sort,
            "limit": limit,
            "page": page,
            "total_pages": total_pages,
            "total_memos": total_memos,
            "search": search,  # 検索クエリをテンプレートに渡す
        },
    )


@router.post("/memo")
async def create_memo_route(
    request: Request, content: str = Form(...), db: Session = Depends(get_db)
):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="ログインが必要です")

    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    memo_id = str(uuid.uuid4())

    # URLをリンクに変換
    content = convert_urls_to_links(content)

    create_memo(db, memo_id, content, now, username)
    return RedirectResponse(url="/memo", status_code=303)


@router.post("/memo/delete/{memo_id}")
async def delete_memo_route(
    request: Request, memo_id: str, db: Session = Depends(get_db)
):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="ログインが必要です")

    if not delete_memo(db, memo_id, username):
        raise HTTPException(
            status_code=404, detail="メモが見つからないか、削除権限がありません"
        )

    return RedirectResponse(url="/memo", status_code=303)


@router.post("/memo/push/{memo_id}")
async def push_memo_to_github(
    request: Request, memo_id: str, db: Session = Depends(get_db)
):
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="ログインが必要です")

    # メモを取得
    memo = db.query(MemoModel).filter(MemoModel.id == memo_id).first()
    if not memo:
        raise HTTPException(status_code=404, detail="メモが見つかりません")

    # メモの内容をマークダウン形式に変換
    content = memo.content
    # HTMLタグを削除してプレーンテキストに変換
    content = re.sub(r"<[^>]+>", "", content)
    # 作成日時を追加
    created_at = memo.created_at.strftime("%Y-%m-%d %H:%M:%S")
    content = f"# メモ\n\n{content}\n\n作成日時: {created_at}"

    try:
        # GitHubにプッシュ
        result = create_github_file("yxfhy", "memo", content)
        return {"status": "success", "url": result["content"]["html_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/memo/delete-all")
async def delete_all_memos(request: Request):
    """yxfhy/memoリポジトリの全メモを削除する"""
    # セッションからユーザー名を取得
    username = request.session.get("username")
    if not username or username != "yxfhy":
        raise HTTPException(status_code=403, detail="権限がありません")

    try:
        # リポジトリの全ファイルを取得
        contents = get_github_repo_contents("yxfhy", "memo")

        # 各ファイルを削除
        for item in contents:
            if item["type"] == "file" and item["name"].startswith("memo_"):
                delete_github_file(
                    owner="yxfhy", repo="memo", path=item["path"], sha=item["sha"]
                )

        return {"status": "success", "message": "全メモを削除しました"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
