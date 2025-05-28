# database.py
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///./web_app.db"  # ルート直下に SQLite ファイルを作成
engine = create_engine(DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    with Session(engine) as session:
        yield session
