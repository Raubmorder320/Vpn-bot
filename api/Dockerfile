FROM python:3.13-slim

# vnstat: читает базу трафика хоста (каталог /var/lib/vnstat монтируется из хоста)
RUN apt-get update && apt-get install -y --no-install-recommends vnstat && rm -rf /var/lib/apt/lists/*

# Бинарник xray берём из официального образа (multi-stage COPY):
# нужен для генерации ключей (xray x25519), проверки конфига (xray -test)
# и добавления пользователей в работающий xray через его API (xray api adu)
COPY --from=teddysun/xray:latest /usr/bin/xray /usr/local/bin/xray

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
