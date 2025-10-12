FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local

COPY bot/ ./bot/

RUN mkdir -p /app/data

ENV PATH=/root/.local/bin:$PATH

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot/main.py"]
