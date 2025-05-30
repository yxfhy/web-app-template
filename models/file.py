"""ファイルモデル"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, Session, SQLModel, select


class FileModel(SQLModel, table=True):
    """ファイルモデル"""

    id: str = Field(primary_key=True)
    original_filename: str
    stored_filename: str
    created_at: datetime
    username: str


def create_file(
    db: Session,
    file_id: str,
    original_filename: str,
    stored_filename: str,
    created_at: datetime,
    username: str,
) -> FileModel:
    """ファイルを作成"""
    file = FileModel(
        id=file_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        created_at=created_at,
        username=username,
    )
    db.add(file)
    db.commit()
    db.refresh(file)
    return file


def get_user_files(db: Session, username: str) -> list[FileModel]:
    """ユーザーのファイル一覧を取得"""
    return db.exec(
        select(FileModel)
        .where(FileModel.username == username)
        .order_by(FileModel.created_at.desc())
    ).all()


def delete_file(db: Session, file_id: str) -> None:
    """ファイルを削除"""
    file = db.exec(select(FileModel).where(FileModel.id == file_id)).first()
    if file:
        db.delete(file)
        db.commit()
