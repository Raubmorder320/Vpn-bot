FROM python:3.13-slim

RUN apt-get update && apt-get install -y curl unzip ca-certificates vnstat && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "bot.py"] 