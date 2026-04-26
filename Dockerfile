FROM python:3.13-slim
RUN apt-get update && apt-get install -y curl unzip ca-certificates vnstat && rm -rf /var/lib/apt/lists/*

RUN curl -L -O https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip && unzip Xray-linux-64.zip xray -d /usr/local/bin/ && chmod +x /usr/local/bin/xray && rm Xray-linux-64.zip

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python3", "bot.py"] 