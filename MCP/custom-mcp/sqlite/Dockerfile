FROM python:3.11-slim

WORKDIR /app

# 必要なパッケージのインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# アプリケーションのコピー
COPY src/ /app/src/
COPY setup.py /app/
COPY README.md /app/

# 依存関係のインストール
RUN pip install --no-cache-dir -e .

# データディレクトリの作成
RUN mkdir -p /data

# 環境変数の設定
ENV PYTHONPATH=/app/src
ENV SQLITE_DB_PATH=/data/db.sqlite

# ボリュームの設定
VOLUME ["/data"]

# サーバーの起動
CMD ["python", "-m", "mcp_server_sqlite"]