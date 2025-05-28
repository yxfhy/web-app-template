FROM python:3.11-slim

WORKDIR /app

# 必要なパッケージをインストール
RUN pip install --no-cache-dir \
    fastapi>=0.110.0 \
    uvicorn>=0.27.0 \
    openai>=1.6.0 \
    python-dotenv \
    jinja2 \
    sqlalchemy

# アプリケーションのファイルをコピー
COPY . .

# ポートを公開
EXPOSE 8000

# アプリケーションを起動
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"] 