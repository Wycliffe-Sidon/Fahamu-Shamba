FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_RETRIES=10

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check --retries 10 --timeout 100 -r requirements.txt

COPY . .

RUN mkdir -p /app/db

EXPOSE 5000 5001 5002 5004 5006 5007

CMD ["gunicorn", "-b", "0.0.0.0:5002", "farmer_chatbot:app"]
