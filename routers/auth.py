# routers/auth.py
import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlmodel import Session, select

from database import get_session
from models.user import User

router = APIRouter(tags=["auth"])

templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 環境変数の読み込み
load_dotenv()

# 管理パスワードを環境変数から取得
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
if not ADMIN_PASSWORD:
    raise ValueError("環境変数 ADMIN_PASSWORD が設定されていません")


# -------------------------------------------------------------------
# サインアップ
# -------------------------------------------------------------------
@router.get("/signup", response_class=HTMLResponse)
async def signup_get(request: Request):
    """サインアップフォーム表示"""
    return templates.TemplateResponse(
        "signup.html", {"request": request, "error": None}
    )


# @router.get("/signup", response_class=HTMLResponse)
# async def signup_get(request: Request):
#     """現在サインアップは受け付けていません。"""
#     return HTMLResponse(
#         "<h2>現在サインアップは受け付けていません。申し訳ございません。</h2>",
#         status_code=403
#     )


@router.post("/signup", response_class=HTMLResponse)
async def signup_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    admin_password: str = Form(...),
    session: Session = Depends(get_session),
):
    """ユーザー登録処理（重複チェック＋ハッシュ化保存）"""

    # 管理パスワードの検証
    if admin_password != ADMIN_PASSWORD:
        error = "管理パスワードが正しくありません。"
        return templates.TemplateResponse(
            "signup.html", {"request": request, "error": error}, status_code=400
        )

    if session.exec(select(User).where(User.username == username)).first():
        error = "そのユーザー名は既に使われています。"
        return templates.TemplateResponse(
            "signup.html", {"request": request, "error": error}, status_code=400
        )

    hashed_pw = pwd_context.hash(password)
    user = User(username=username, hashed_password=hashed_pw)
    session.add(user)
    session.commit()

    # サインアップ成功時に自動的にログイン状態にする
    request.session["user_id"] = user.id
    request.session["username"] = user.username

    # ポップアップ → ホーム
    html = """
    <script>
        alert('ユーザー登録が完了しました！');
        window.location.href = "/";
    </script>
    """
    return HTMLResponse(html, status_code=status.HTTP_200_OK)


# -------------------------------------------------------------------
# ログイン (/login 採用)
# -------------------------------------------------------------------
@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    """ログインフォーム表示"""
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    """認証してトップへリダイレクト、失敗なら同ページにエラー"""

    user: User | None = session.exec(
        select(User).where(User.username == username)
    ).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        error = "ユーザー名またはパスワードが違います。"
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": error}, status_code=400
        )

    # ★ログイン成功→セッションに保存
    request.session["user_id"] = user.id
    request.session["username"] = user.username

    # 認証成功時はトップページにリダイレクト
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


# ★ログアウト
@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


def login_required_yxfhy(request: Request) -> bool:
    if request.session.get("username") == "yxfhy":
        return True
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
