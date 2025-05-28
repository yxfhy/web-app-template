import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.memo import MemoModel, create_memo, delete_memo, get_db, get_user_memos

router = APIRouter()
templates = Jinja2Templates(directory="templates")


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
    request: Request, sort: str = "newest", db: Session = Depends(get_db)
):
    # セッションからユーザー名を取得
    username = request.session.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=303)

    # ユーザーのメモを取得
    user_memos = get_user_memos(db, username)

    # 並び替え
    if sort == "oldest":
        user_memos.sort(key=lambda x: x.created_at)
    else:  # newest
        user_memos.sort(key=lambda x: x.created_at, reverse=True)

    return templates.TemplateResponse(
        "memo.html", {"request": request, "memos": user_memos, "sort": sort}
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
