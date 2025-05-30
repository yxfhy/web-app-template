"""ファイルアップロード・ダウンロード機能"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from database import get_session
from models.file import FileModel, create_file, delete_file, get_user_files
from routers.auth import login_required_yxfhy

router = APIRouter(prefix="/file-drop", tags=["file-drop"])
templates = Jinja2Templates(directory="templates")

# アップロードディレクトリの設定
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# 静的ファイルのマウント
router.mount("/files", StaticFiles(directory=str(UPLOAD_DIR.absolute())), name="files")


@router.get("/", response_class=HTMLResponse)
async def file_drop_page(request: Request, db: Session = Depends(get_session)):
    """ファイルドロップページを表示"""
    # yxfhyユーザーのみアクセス可能
    login_required_yxfhy(request)

    # ユーザーのファイル一覧を取得
    username = request.session.get("username")
    files = get_user_files(db, username)

    return templates.TemplateResponse(
        "file_drop.html",
        {
            "request": request,
            "files": files,
        },
    )


@router.get("/download/{file_id}")
async def download_file(
    request: Request,
    file_id: str,
    db: Session = Depends(get_session),
):
    """ファイルをダウンロード"""
    # yxfhyユーザーのみアクセス可能
    login_required_yxfhy(request)

    # ファイル情報を取得
    file = db.exec(select(FileModel).where(FileModel.id == file_id)).first()
    if not file:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    # ファイルパスを取得
    file_path = UPLOAD_DIR / file.stored_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    # ファイルをダウンロード
    return FileResponse(
        path=file_path,
        filename=file.original_filename,
        media_type="application/octet-stream",
    )


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
):
    """ファイルをアップロード"""
    # yxfhyユーザーのみアクセス可能
    login_required_yxfhy(request)

    username = request.session.get("username")

    # ファイル名を安全に生成
    original_filename = file.filename
    file_extension = Path(original_filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # ファイルを保存
    file_path = UPLOAD_DIR / unique_filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # データベースに記録
    create_file(
        db,
        file_id=str(uuid.uuid4()),
        original_filename=original_filename,
        stored_filename=unique_filename,
        created_at=datetime.now(),
        username=username,
    )

    return RedirectResponse(url="/file-drop", status_code=303)


@router.post("/delete/{file_id}")
async def delete_file_route(
    request: Request,
    file_id: str,
    db: Session = Depends(get_session),
):
    """ファイルを削除"""
    # yxfhyユーザーのみアクセス可能
    login_required_yxfhy(request)

    # ファイル情報を取得
    file = db.exec(select(FileModel).where(FileModel.id == file_id)).first()
    if not file:
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    # ファイルを削除
    file_path = UPLOAD_DIR / file.stored_filename
    if file_path.exists():
        file_path.unlink()

    # データベースから削除
    delete_file(db, file_id)

    return RedirectResponse(url="/file-drop", status_code=303)
