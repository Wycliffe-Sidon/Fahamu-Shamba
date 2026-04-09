"""Bootstrap script - initializes DB at Docker build time."""
import logging
import os

logging.basicConfig(level=logging.INFO)

os.makedirs("/app/data", exist_ok=True)

try:
    from feedback_system import init_db as init_feedback_db
    init_feedback_db()
    print("Feedback DB initialized.")
except Exception as e:
    print(f"Feedback DB warning: {e}")

try:
    from farmer_chatbot import chatbot
    chatbot.init_database()
    print("Chatbot DB initialized.")
except Exception as e:
    print(f"Chatbot DB warning: {e}")

print("Bootstrap complete.")
