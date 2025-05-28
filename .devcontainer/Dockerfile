# ─ 軽量な公式 Python イメージ ─────────────────────────
FROM python:3.11-slim

# 時刻設定やパッケージ設定画面などの 対話型プロンプトをスキップ 
# 自動化されたビルド処理を 止めずに最後まで実行 できるようにする役割
ARG DEBIAN_FRONTEND=noninteractive


WORKDIR /app


# curl を追加 ---------★
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
    
# ─ システム依存パッケージのインストール ─────────────────
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

# ─ Python 依存パッケージを requirements.txt からインストール ──

RUN pip install --no-cache-dir python-dotenv
 # 追加：openai パッケージをインストール
RUN pip install --no-cache-dir openai
RUN pip install  --no-cache-dir uvicorn
RUN pip install  --no-cache-dir fastapi
RUN pip install  --no-cache-dir python-multipart
RUN pip install  --no-cache-dir debugpy
RUN pip install  --no-cache-dir tweepy>=4.14
RUN pip install  --no-cache-dir jinja2
RUN pip install  --no-cache-dir sqlmodel passlib[bcrypt] itsdangerous
RUN pip install --no-cache-dir beautifulsoup4
RUN pip install --no-cache-dir requests

COPY . /app

# ─ コンテナがリッスンするポート ─────────────────────────
EXPOSE 8000 5678

CMD ["python", "app.py"]

