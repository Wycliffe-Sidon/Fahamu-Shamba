FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DEFAULT_TIMEOUT=100
ENV PIP_RETRIES=10
ENV PORT=10000
ENV DB_PATH=/app/data/fahamu_shamba.db
ENV MODEL_DATA_DIR=/app/data
ENV MODEL_PATH=/app/data/enhanced_crop_recommendation_model.pkl
ENV TRAINING_DATA_PATH=/app/data/fahamu_shamba_training_data.csv
ENV USE_MOCK_DATA=true

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --disable-pip-version-check --retries 10 --timeout 100 -r requirements.txt

COPY . .

RUN mkdir -p /app/data && \
    python -c "
from feedback_system import init_db as init_feedback_db
from farmer_chatbot import chatbot
init_feedback_db()
chatbot.init_database()
try:
    chatbot._get_recommendation_engine()
except Exception as e:
    print(f'Model bootstrap warning: {e}')
print('Bootstrap complete')
"

EXPOSE 10000

CMD gunicorn -b 0.0.0.0:${PORT} --timeout 120 --workers 1 app:app
