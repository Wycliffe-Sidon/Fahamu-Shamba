"""Bootstrap script - initializes DB and ML model at Docker build time."""
import logging
logging.basicConfig(level=logging.INFO)

from feedback_system import init_db as init_feedback_db
from farmer_chatbot import chatbot

init_feedback_db()
chatbot.init_database()

try:
    chatbot._get_recommendation_engine()
    print("Model bootstrap complete.")
except Exception as e:
    print(f"Model bootstrap warning (will retry at runtime): {e}")

print("Bootstrap complete.")
