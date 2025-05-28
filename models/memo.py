from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class MemoModel(Base):
    __tablename__ = "memos"

    id = Column(String, primary_key=True)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    username = Column(String, nullable=False)


# データベースの初期化
engine = create_engine("sqlite:///memos.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_memo(
    db, memo_id: str, content: str, created_at: datetime, username: str
) -> MemoModel:
    db_memo = MemoModel(
        id=memo_id, content=content, created_at=created_at, username=username
    )
    db.add(db_memo)
    db.commit()
    db.refresh(db_memo)
    return db_memo


def get_user_memos(
    db, username: str, search_query: Optional[str] = None
) -> List[MemoModel]:
    query = db.query(MemoModel).filter(MemoModel.username == username)
    if search_query:
        query = query.filter(MemoModel.content.ilike(f"%{search_query}%"))
    return query.all()


def delete_memo(db, memo_id: str, username: str) -> bool:
    memo = (
        db.query(MemoModel)
        .filter(MemoModel.id == memo_id, MemoModel.username == username)
        .first()
    )
    if memo:
        db.delete(memo)
        db.commit()
        return True
    return False
