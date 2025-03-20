FROM python:3.12-slim

WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Pythonパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -U

# アプリケーションコードをコピー
COPY . .

# Gradioアプリを起動
EXPOSE 7860
CMD ["python", "app.py"]
