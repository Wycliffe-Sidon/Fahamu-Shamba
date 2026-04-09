#!/usr/bin/env python3
"""
Unit tests for the farmer chatbot service.
"""

import unittest
from unittest.mock import patch

import farmer_chatbot


class FarmerChatbotTests(unittest.TestCase):
    def setUp(self):
        self.client = farmer_chatbot.app.test_client()

    def test_chat_requires_message(self):
        response = self.client.post("/chat", json={})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Message is required")

    def test_chat_rate_limit_can_be_hit(self):
        with patch.object(farmer_chatbot.rate_limiter, "is_allowed", return_value=False):
            response = self.client.post("/chat", json={"message": "How do I plant maize?"})
        self.assertEqual(response.status_code, 429)

    def test_chat_success_uses_chatbot_processor(self):
        payload = {
            "response": "Plant maize during the long rains.",
            "confidence": 0.8,
            "intent": "planting_advice",
            "is_agricultural": True,
        }
        with patch.object(farmer_chatbot.chatbot, "process_message", return_value=payload):
            response = self.client.post("/chat", json={"message": "How do I plant maize?", "phone_number": "+254700000000"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["response"], payload["response"])

    def test_process_message_routes_planting_queries_to_recommendation_engine(self):
        recommendation_payload = {
            "response": "Best crop to plant now for Kitui: Sorghum",
            "confidence": 0.88,
            "intent": "planting_advice",
            "is_agricultural": True,
        }
        with patch.object(farmer_chatbot.chatbot, "detect_intent", return_value="planting_advice"):
            with patch.object(farmer_chatbot.chatbot, "get_crop_recommendation_response", return_value=recommendation_payload) as mock_recommend:
                response = farmer_chatbot.chatbot.process_message(
                    "What is the best crop to plant in Kitui?",
                    context={"county": "kitui", "soil_type": "sandy"},
                )
        self.assertEqual(response["intent"], "planting_advice")
        mock_recommend.assert_called_once()

    def test_chat_accepts_image_payload(self):
        payload = {
            "response": "This looks like early blight on tomato leaves.",
            "confidence": 0.85,
            "intent": "pest_disease",
            "is_agricultural": True,
            "used_image": True,
        }
        image_data = "data:image/png;base64,ZmFrZQ=="
        with patch.object(farmer_chatbot.chatbot, "process_message", return_value=payload) as mock_process:
            response = self.client.post(
                "/chat",
                json={"message": "What disease is this?", "phone_number": "+254700000000", "image_data": image_data},
            )
        self.assertEqual(response.status_code, 200)
        mock_process.assert_called_once_with("What disease is this?", "+254700000000", image_data=image_data, context={})

    def test_chat_rejects_non_image_uploads(self):
        response = self.client.post("/chat", json={"message": "Check this file", "image_data": "data:text/plain;base64,ZmFrZQ=="})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Only image uploads are supported.")

    def test_profile_requires_api_key_when_configured(self):
        with patch.object(farmer_chatbot.settings, "service_api_key", "secret-key"):
            response = self.client.post("/profile", json={"phone_number": "+254700000000"})
        self.assertEqual(response.status_code, 401)

    def test_recommend_crops_endpoint_returns_structured_data(self):
        payload = {
            "response": "Best crop to plant now for Nairobi: Beans",
            "confidence": 0.91,
            "intent": "planting_advice",
            "recommendation_data": {"top_recommendation": {"crop": "beans"}},
            "is_agricultural": True,
        }
        with patch.object(farmer_chatbot.chatbot, "get_crop_recommendation_response", return_value=payload):
            response = self.client.post("/recommend-crops", json={"county": "nairobi", "soil_type": "loamy"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["recommendation_data"]["top_recommendation"]["crop"], "beans")

    def test_health_endpoint_reports_status(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("database_ok", data)


if __name__ == "__main__":
    unittest.main()
