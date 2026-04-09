#!/bin/bash
# Fahamu Shamba - Render Build Script

set -e

echo "FAHAMU SHAMBA BUILD"
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm --quiet || echo "spaCy model already present"

echo "Bootstrapping database and model..."
python - <<'PY'
import logging

from feedback_system import init_db as init_feedback_db
from farmer_chatbot import chatbot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_feedback_db()
chatbot.init_database()

try:
    chatbot._get_recommendation_engine()
    logger.info("Recommendation engine ready")
except Exception as exc:
    logger.warning("Model bootstrap will continue at runtime: %s", exc)
PY

echo "Build complete."
