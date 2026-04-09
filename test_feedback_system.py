#!/usr/bin/env python3
"""
Unit tests for the feedback retraining service.
"""

import os
import unittest
import uuid
from unittest.mock import patch

import pandas as pd

import feedback_system


class FakeEngine:
    KENYA_COUNTIES = {
        "nairobi": {"altitude": 1795, "avg_rainfall": 850, "avg_temp": 18},
        "kitui": {"altitude": 1100, "avg_rainfall": 500, "avg_temp": 24},
    }

    def generate_enhanced_sample_data(self, n_samples=1200):
        return pd.DataFrame(
            [
                {
                    "county": "nairobi",
                    "crop": "maize",
                    "soil_type": "loamy",
                    "soil_ph": 6.4,
                    "rainfall_mm": 800,
                    "temperature_c": 19,
                    "humidity_percent": 65,
                    "altitude_m": 1795,
                    "land_size_acres": 1.0,
                    "irrigation_available": 0,
                    "fertilizer_use": 1,
                    "pest_disease_risk": 0.2,
                    "market_price_kes": 45,
                    "demand_index": 0.7,
                    "actual_yield_tons_per_acre": 2.6,
                    "success": 1,
                },
                {
                    "county": "kitui",
                    "crop": "sorghum",
                    "soil_type": "sandy",
                    "soil_ph": 6.1,
                    "rainfall_mm": 480,
                    "temperature_c": 24,
                    "humidity_percent": 58,
                    "altitude_m": 1100,
                    "land_size_acres": 2.0,
                    "irrigation_available": 0,
                    "fertilizer_use": 0,
                    "pest_disease_risk": 0.3,
                    "market_price_kes": 52,
                    "demand_index": 0.6,
                    "actual_yield_tons_per_acre": 2.0,
                    "success": 1,
                },
            ]
        )

    def train(self, data):
        self.trained_rows = len(data)
        return {"test_accuracy": 0.92}

    def save_model(self, filename):
        with open(filename, "w", encoding="utf-8") as handle:
            handle.write("fake-model")


class FeedbackSystemTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = os.path.join(os.getcwd(), "test_artifacts", f"feedback_{uuid.uuid4().hex}")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.db_path = os.path.join(self.temp_dir, "feedback.db")
        self.model_path = os.path.join(self.temp_dir, "model.pkl")
        self.training_path = os.path.join(self.temp_dir, "training.csv")

        self.patches = [
            patch.object(feedback_system, "DB_PATH", self.db_path),
            patch.object(feedback_system, "MODEL_PATH", self.model_path),
            patch.object(feedback_system, "TRAINING_DATA_PATH", self.training_path),
        ]
        for patcher in self.patches:
            patcher.start()
        feedback_system.init_db()

    def tearDown(self):
        for patcher in reversed(self.patches):
            patcher.stop()
        for path in [self.db_path, self.model_path, self.training_path]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.isdir(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_collect_feedback_persists_record(self):
        ok = feedback_system.collect_feedback(
            {
                "phone_number": "+254700000001",
                "county": "kitui",
                "crop_name": "sorghum",
                "actual_yield": 1.8,
                "expected_yield": 2.0,
            }
        )
        self.assertTrue(ok)
        analytics = feedback_system.get_analytics()
        self.assertEqual(analytics["total_feedback"], 1)

    def test_retrain_if_ready_uses_enhanced_engine(self):
        feedback_system.collect_feedback(
            {
                "phone_number": "+254700000001",
                "county": "kitui",
                "recommended_crop": "sorghum",
                "crop_name": "sorghum",
                "actual_yield": 1.8,
                "expected_yield": 2.0,
                "soil_type": "sandy",
                "soil_ph": 6.1,
                "rainfall_mm": 470,
                "temperature_c": 25,
                "humidity_percent": 55,
                "market_price_kes": 58,
            }
        )
        with patch.object(feedback_system, "get_engine_class", return_value=FakeEngine):
            result = feedback_system.retrain_if_ready(threshold=1)
        self.assertTrue(result["retrained"])
        self.assertTrue(os.path.exists(self.model_path))


if __name__ == "__main__":
    unittest.main()
