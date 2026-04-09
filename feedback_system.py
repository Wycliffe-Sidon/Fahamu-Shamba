"""
Fahamu Shamba - Feedback Loop System
Collects farmer yield reports and retrains the enhanced recommendation model.
"""

import logging
import os
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_DIR = os.getenv("MODEL_DATA_DIR", os.getenv("APP_DATA_DIR", "."))
DB_PATH = os.getenv("DB_PATH", "fahamu_shamba.db")
MODEL_PATH = os.getenv("MODEL_PATH", os.path.join(DATA_DIR, "enhanced_crop_recommendation_model.pkl"))
TRAINING_DATA_PATH = os.getenv("TRAINING_DATA_PATH", os.path.join(DATA_DIR, "fahamu_shamba_training_data.csv"))


def get_engine_class():
    from enhanced_recommendation_engine import EnhancedCropRecommendationEngine

    return EnhancedCropRecommendationEngine


def get_conn():
    parent = Path(DB_PATH).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    with closing(get_conn()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS farmer_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT,
                county TEXT,
                recommended_crop TEXT,
                crop_name TEXT,
                actual_yield REAL,
                expected_yield REAL,
                satisfaction_rating INTEGER,
                feedback_text TEXT,
                feedback_channel TEXT DEFAULT 'web',
                soil_type TEXT,
                soil_ph REAL,
                rainfall_mm REAL,
                temperature_c REAL,
                humidity_percent REAL,
                market_price_kes REAL,
                land_size_acres REAL,
                irrigation_available INTEGER DEFAULT 0,
                fertilizer_use INTEGER DEFAULT 0,
                processed INTEGER DEFAULT 0,
                feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS model_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT,
                accuracy REAL,
                samples INTEGER,
                trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        _ensure_columns(
            conn,
            "farmer_feedback",
            {
                "county": "TEXT",
                "recommended_crop": "TEXT",
                "crop_name": "TEXT",
                "actual_yield": "REAL",
                "expected_yield": "REAL",
                "satisfaction_rating": "INTEGER",
                "feedback_text": "TEXT",
                "feedback_channel": "TEXT DEFAULT 'web'",
                "soil_type": "TEXT",
                "soil_ph": "REAL",
                "rainfall_mm": "REAL",
                "temperature_c": "REAL",
                "humidity_percent": "REAL",
                "market_price_kes": "REAL",
                "land_size_acres": "REAL",
                "irrigation_available": "INTEGER DEFAULT 0",
                "fertilizer_use": "INTEGER DEFAULT 0",
                "processed": "INTEGER DEFAULT 0",
                "feedback_date": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            },
        )
        conn.commit()


def _ensure_columns(conn: sqlite3.Connection, table_name: str, columns: Dict[str, str]) -> None:
    existing_columns = {
        row[1]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    for column_name, column_type in columns.items():
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def _normalize_feedback(data: Dict) -> Dict:
    return {
        "phone_number": data.get("phone_number"),
        "county": (data.get("county") or "nairobi").lower(),
        "recommended_crop": (data.get("recommended_crop") or data.get("crop_name") or "").lower(),
        "crop_name": (data.get("crop_name") or data.get("recommended_crop") or "").lower(),
        "actual_yield": data.get("actual_yield"),
        "expected_yield": data.get("expected_yield"),
        "satisfaction_rating": data.get("satisfaction_rating"),
        "feedback_text": data.get("feedback_text"),
        "feedback_channel": data.get("feedback_channel", "web"),
        "soil_type": (data.get("soil_type") or "loamy").lower(),
        "soil_ph": float(data.get("soil_ph", 6.5)),
        "rainfall_mm": float(data.get("rainfall_mm", 600)),
        "temperature_c": float(data.get("temperature_c", 22)),
        "humidity_percent": float(data.get("humidity_percent", 65)),
        "market_price_kes": float(data.get("market_price_kes", 50)),
        "land_size_acres": float(data.get("land_size_acres", 1.0)),
        "irrigation_available": int(data.get("irrigation_available", 0)),
        "fertilizer_use": int(data.get("fertilizer_use", 0)),
    }


def collect_feedback(data: Dict) -> bool:
    try:
        record = _normalize_feedback(data)
        if not record["crop_name"]:
            raise ValueError("crop_name or recommended_crop is required")

        with closing(get_conn()) as conn:
            conn.execute(
                """
                INSERT INTO farmer_feedback (
                    phone_number, county, recommended_crop, crop_name, actual_yield, expected_yield,
                    satisfaction_rating, feedback_text, feedback_channel, soil_type, soil_ph,
                    rainfall_mm, temperature_c, humidity_percent, market_price_kes, land_size_acres,
                    irrigation_available, fertilizer_use
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["phone_number"],
                    record["county"],
                    record["recommended_crop"],
                    record["crop_name"],
                    record["actual_yield"],
                    record["expected_yield"],
                    record["satisfaction_rating"],
                    record["feedback_text"],
                    record["feedback_channel"],
                    record["soil_type"],
                    record["soil_ph"],
                    record["rainfall_mm"],
                    record["temperature_c"],
                    record["humidity_percent"],
                    record["market_price_kes"],
                    record["land_size_acres"],
                    record["irrigation_available"],
                    record["fertilizer_use"],
                ),
            )
            conn.commit()
        logger.info("Feedback saved from %s", record.get("phone_number"))
        return True
    except Exception as exc:
        logger.error("collect_feedback error: %s", exc)
        return False


def _load_base_training_data(engine) -> pd.DataFrame:
    path = Path(TRAINING_DATA_PATH)
    if path.exists():
        return pd.read_csv(path)
    return engine.generate_enhanced_sample_data(1200)


def retrain_if_ready(threshold: int = 25) -> Dict:
    init_db()
    with closing(get_conn()) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM farmer_feedback WHERE processed=0 AND actual_yield IS NOT NULL",
            conn,
        )

    if len(df) < threshold:
        return {"retrained": False, "reason": f"Need {threshold} samples, have {len(df)}"}

    rows = []
    engine_class = get_engine_class()
    for _, row in df.iterrows():
        county = str(row["county"] or "nairobi").lower()
        engine_ref = engine_class()
        county_defaults = engine_ref.KENYA_COUNTIES.get(county, engine_ref.KENYA_COUNTIES["nairobi"])
        baseline_yield = max(float(row["expected_yield"] or 0), 0.1)
        actual_yield = max(float(row["actual_yield"] or baseline_yield), 0.1)
        rows.append(
            {
                "county": county,
                "crop": row["crop_name"],
                "soil_type": row["soil_type"] or "loamy",
                "soil_ph": float(row["soil_ph"] or 6.5),
                "rainfall_mm": float(row["rainfall_mm"] or county_defaults["avg_rainfall"]),
                "temperature_c": float(row["temperature_c"] or county_defaults["avg_temp"]),
                "humidity_percent": float(row["humidity_percent"] or 65),
                "altitude_m": county_defaults["altitude"],
                "land_size_acres": float(row["land_size_acres"] or 1.0),
                "irrigation_available": int(row["irrigation_available"] or 0),
                "fertilizer_use": int(row["fertilizer_use"] or 0),
                "pest_disease_risk": 0.25 if (row["satisfaction_rating"] or 3) >= 3 else 0.45,
                "market_price_kes": float(row["market_price_kes"] or 50),
                "demand_index": 0.75 if (row["satisfaction_rating"] or 3) >= 4 else 0.55,
                "actual_yield_tons_per_acre": actual_yield,
                "success": 1 if actual_yield >= baseline_yield * 0.8 else 0,
            }
        )

    feedback_df = pd.DataFrame(rows)
    engine = engine_class()
    combined = pd.concat([_load_base_training_data(engine), feedback_df], ignore_index=True)
    metrics = engine.train(combined)
    engine.save_model(MODEL_PATH)
    combined.to_csv(TRAINING_DATA_PATH, index=False)

    with closing(get_conn()) as conn:
        ids = ",".join(str(i) for i in df["id"].tolist())
        conn.execute(f"UPDATE farmer_feedback SET processed=1 WHERE id IN ({ids})")
        conn.execute(
            "INSERT INTO model_versions (version, accuracy, samples) VALUES (?,?,?)",
            (
                datetime.now().strftime("v%Y%m%d_%H%M"),
                float(metrics["test_accuracy"]),
                len(combined),
            ),
        )
        conn.commit()

    logger.info("Model retrained. Accuracy: %.3f", metrics["test_accuracy"])
    return {"retrained": True, "metrics": metrics, "feedback_used": len(df)}


def get_analytics() -> Dict:
    init_db()
    with closing(get_conn()) as conn:
        summary = conn.execute(
            "SELECT COUNT(*), AVG(satisfaction_rating) FROM farmer_feedback"
        ).fetchone()
        crop_stats = pd.read_sql_query(
            """
            SELECT crop_name, COUNT(*) as count, AVG(satisfaction_rating) as avg_rating
            FROM farmer_feedback
            GROUP BY crop_name
            """,
            conn,
        ).to_dict("records")

    return {
        "total_feedback": summary[0] or 0,
        "avg_satisfaction": round(summary[1] or 0, 2),
        "crop_stats": crop_stats,
        "model_exists": Path(MODEL_PATH).exists(),
    }


app = Flask(__name__)
CORS(app)
init_db()


@app.route("/feedback", methods=["POST"])
def post_feedback():
    ok = collect_feedback(request.json or {})
    return jsonify({"success": ok}), 200 if ok else 400


@app.route("/feedback/analytics", methods=["GET"])
def analytics():
    return jsonify(get_analytics())


@app.route("/feedback/retrain", methods=["POST"])
def retrain():
    threshold = int((request.json or {}).get("threshold", 25))
    return jsonify(retrain_if_ready(threshold))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "feedback", "model_exists": Path(MODEL_PATH).exists()})


if __name__ == "__main__":
    print("[FEEDBACK] Running on http://0.0.0.0:5004")
    print("  Endpoints: POST /feedback  |  GET /feedback/analytics  |  POST /feedback/retrain  |  GET /health")
    app.run(debug=False, host="0.0.0.0", port=5004)
