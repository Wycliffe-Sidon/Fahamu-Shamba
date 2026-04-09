"""
Fahamu Shamba - Setup Script
Run once to install dependencies, init DB, and train the initial model.
"""

import subprocess
import sys
import sqlite3
from pathlib import Path


def run(cmd: list, label: str) -> bool:
    print(f"\n[{label}]")
    try:
        subprocess.check_call(cmd)
        print(f"  OK")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  FAILED: {e}")
        return False


def init_db():
    print("\n[Init database]")
    conn = sqlite3.connect("fahamu_shamba.db")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS farmer_profiles (
            phone_number TEXT PRIMARY KEY,
            name TEXT, county TEXT,
            land_size REAL, soil_type TEXT,
            language TEXT DEFAULT 'sw'
        );
        CREATE TABLE IF NOT EXISTS ussd_sessions (
            session_id TEXT PRIMARY KEY,
            phone_number TEXT, current_menu TEXT,
            session_data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS farmer_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT, crop_name TEXT,
            actual_yield REAL, expected_yield REAL,
            satisfaction_rating INTEGER, feedback_text TEXT,
            feedback_channel TEXT DEFAULT 'ussd',
            processed INTEGER DEFAULT 0,
            feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS model_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT, accuracy REAL, samples INTEGER,
            trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()
    print("  OK")


def train_model():
    print("\n[Train initial model]")
    try:
        from recommendation_engine import generate_sample_data, CropRecommendationEngine
        data    = generate_sample_data(1000)
        engine  = CropRecommendationEngine()
        metrics = engine.train(data)
        engine.save_model("crop_recommendation_model.pkl")
        print(f"  Accuracy: {metrics['accuracy']:.3f}  Features: {metrics['n_features']}")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False


def main():
    print("=" * 50)
    print("  FAHAMU SHAMBA SETUP")
    print("=" * 50)

    steps = [
        run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            "Install dependencies"),
        run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
            "Download spaCy model"),
    ]

    init_db()
    steps.append(train_model())

    print("\n" + "=" * 50)
    passed = sum(steps)
    print(f"  {passed}/{len(steps)} steps completed")

    if all(steps):
        print("""
  SETUP COMPLETE. Next steps:
  1. Edit .env and add your API keys
  2. python demo.py              — run the demo
  3. python ussd_sms_integration.py  — start USSD/SMS (port 5000)
  4. python ivr_system.py            — start IVR (port 5001)
  5. python chatbot.py               — start chatbot (port 5002)
  6. python feedback_system.py       — start feedback (port 5004)
        """)
    else:
        print("\n  Some steps failed. Check errors above.")


if __name__ == "__main__":
    main()
