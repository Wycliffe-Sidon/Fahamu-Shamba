#!/usr/bin/env python3
"""
Unified Render entrypoint for Fahamu Shamba.

This file exposes a single Flask app that serves:
- Web chat and recommendation endpoints from farmer_chatbot
- USSD callback for Africa's Talking
- SMS inbound/outbound helpers
- IVR call flows for Twilio
- Feedback collection and retraining endpoints
"""

import json
import logging
import os
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from flask import jsonify, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import Gather, VoiceResponse

import feedback_system
from farmer_chatbot import app as app
from farmer_chatbot import chatbot, settings
from weather_service import get_weather

load_dotenv()

logger = logging.getLogger(__name__)

DB_PATH = settings.db_path
CHATBOT_RESPONSE_LIMIT = 155

COUNTY_MENU = {
    "1": "nairobi",
    "2": "nakuru",
    "3": "eldoret",
    "4": "kisumu",
    "5": "kitui",
    "6": "kakamega",
    "7": "mombasa",
    "8": "garissa",
}

SOIL_MENU = {
    "1": "sandy",
    "2": "clay",
    "3": "loamy",
    "4": "silty",
}


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def _init_channel_tables() -> None:
    with closing(_get_conn()) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS channel_profiles (
                phone_number TEXT PRIMARY KEY,
                name TEXT,
                county TEXT,
                land_size_acres REAL,
                soil_type TEXT DEFAULT 'loamy',
                language TEXT DEFAULT 'sw',
                irrigation_available INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS channel_sessions (
                session_id TEXT PRIMARY KEY,
                phone_number TEXT,
                channel TEXT,
                state TEXT,
                payload TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()


def _get_channel_profile(phone_number: str) -> Dict[str, Any]:
    with closing(_get_conn()) as conn:
        row = conn.execute(
            """
            SELECT name, county, land_size_acres, soil_type, language, irrigation_available
            FROM channel_profiles
            WHERE phone_number = ?
            """,
            (phone_number,),
        ).fetchone()
    return dict(row) if row else {}


def _save_channel_profile(phone_number: str, profile: Dict[str, Any]) -> None:
    with closing(_get_conn()) as conn:
        conn.execute(
            """
            INSERT INTO channel_profiles (
                phone_number, name, county, land_size_acres, soil_type, language, irrigation_available, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(phone_number) DO UPDATE SET
                name=excluded.name,
                county=excluded.county,
                land_size_acres=excluded.land_size_acres,
                soil_type=excluded.soil_type,
                language=excluded.language,
                irrigation_available=excluded.irrigation_available,
                updated_at=excluded.updated_at
            """,
            (
                phone_number,
                profile.get("name"),
                profile.get("county"),
                float(profile.get("land_size_acres", 1.0)),
                profile.get("soil_type", "loamy"),
                profile.get("language", "sw"),
                int(profile.get("irrigation_available", 0)),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()

    chatbot.save_farmer_profile(
        phone_number,
        {
            "name": profile.get("name"),
            "county": profile.get("county"),
            "land_size_acres": float(profile.get("land_size_acres", 1.0)),
            "language_preference": "sw" if profile.get("language", "sw") == "sw" else "en",
            "main_crops": profile.get("main_crops"),
            "farming_experience": profile.get("farming_experience"),
        },
    )


def _save_session(session_id: str, phone_number: str, channel: str, state: str, payload: Dict[str, Any]) -> None:
    with closing(_get_conn()) as conn:
        conn.execute(
            """
            INSERT INTO channel_sessions (session_id, phone_number, channel, state, payload, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                phone_number=excluded.phone_number,
                channel=excluded.channel,
                state=excluded.state,
                payload=excluded.payload,
                updated_at=excluded.updated_at
            """,
            (
                session_id,
                phone_number,
                channel,
                state,
                json.dumps(payload),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()


def _get_session(session_id: str) -> Dict[str, Any]:
    with closing(_get_conn()) as conn:
        row = conn.execute(
            "SELECT state, payload FROM channel_sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    if not row:
        return {}
    return {
        "state": row["state"],
        "payload": json.loads(row["payload"] or "{}"),
    }


def _chat_response(message: str, phone_number: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return chatbot.process_message(message, phone_number=phone_number, context=context or {})


def _send_sms(phone_number: str, message: str, provider: str = "africastalking") -> Dict[str, Any]:
    provider = (provider or "africastalking").strip().lower()
    use_mock = os.getenv("USE_MOCK_DATA", "true").lower() == "true"

    if use_mock:
        logger.info("[MOCK SMS][%s] %s -> %s", provider, phone_number, message)
        return {"success": True, "provider": provider, "mock": True}

    try:
        if provider == "twilio":
            client = Client(
                os.getenv("TWILIO_ACCOUNT_SID", "").strip(),
                os.getenv("TWILIO_AUTH_TOKEN", "").strip(),
            )
            result = client.messages.create(
                body=message,
                from_=os.getenv("TWILIO_PHONE_NUMBER", "").strip(),
                to=phone_number,
            )
            return {"success": True, "provider": "twilio", "sid": result.sid}

        import africastalking as at

        at.initialize(
            os.getenv("AFRICASTALKING_USERNAME", "").strip(),
            os.getenv("AFRICASTALKING_API_KEY", "").strip(),
        )
        response = at.SMS.send(message, [phone_number])
        recipients = response.get("SMSMessageData", {}).get("Recipients", [])
        status = recipients[0].get("status") if recipients else "Unknown"
        return {"success": status == "Success", "provider": "africastalking", "status": status}
    except Exception as exc:
        logger.error("SMS send failed via %s: %s", provider, exc)
        return {"success": False, "provider": provider, "error": str(exc)}


def _localized(text_sw: str, text_en: str, lang: str) -> str:
    return text_sw if lang == "sw" else text_en


def _recommendation_context(phone_number: str, profile: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "county": profile.get("county", "nairobi"),
        "soil_type": profile.get("soil_type", "loamy"),
        "land_size_acres": profile.get("land_size_acres", 1.0),
        "irrigation_available": profile.get("irrigation_available", 0),
    }


def _recommendation_text(phone_number: str, profile: Dict[str, Any]) -> str:
    lang = profile.get("language", "sw")
    response = chatbot.get_crop_recommendation_response(
        "Recommend the best crop to plant now",
        chatbot.get_farmer_profile(phone_number),
        context=_recommendation_context(phone_number, profile),
    )
    data = response["recommendation_data"]["all_recommendations"]
    intro = "Mazao bora kwa sasa:" if lang == "sw" else "Best crops to plant now:"
    lines = [intro]
    for index, item in enumerate(data, start=1):
        crop_name = item["crop"].title()
        lines.append(f"{index}. {crop_name} ({item['confidence']}%)")
    return "\n".join(lines)


def _weather_text(profile: Dict[str, Any]) -> str:
    lang = profile.get("language", "sw")
    county = profile.get("county", "nairobi")
    weather = get_weather(county)
    if lang == "sw":
        return (
            f"Hali ya hewa {county.title()}:\n"
            f"Joto {weather['temperature']}C\n"
            f"Unyevu {weather['humidity']}%\n"
            f"Mvua {weather['rainfall_mm']:.0f}mm\n"
            f"Hali {weather['description']}"
        )
    return (
        f"Weather for {county.title()}:\n"
        f"Temp {weather['temperature']}C\n"
        f"Humidity {weather['humidity']}%\n"
        f"Rainfall {weather['rainfall_mm']:.0f}mm\n"
        f"Conditions {weather['description']}"
    )


def _market_text(lang: str) -> str:
    if lang == "sw":
        return (
            "Bei za soko (KSh/kg):\n"
            "Mahindi 45\nMaharage 80\nNyanya 60\nViazi 55\nSukuma 35"
        )
    return (
        "Market prices (KSh/kg):\n"
        "Maize 45\nBeans 80\nTomatoes 60\nPotatoes 55\nKale 35"
    )


def _market_payload() -> Dict[str, Any]:
    return {
        "timestamp": datetime.now().isoformat(),
        "markets": [
            {
                "name": "Nairobi",
                "crops": [
                    {"name": "Maize", "price": 45.5, "change": 2.3, "volume": 150, "quality": "A"},
                    {"name": "Beans", "price": 78.2, "change": -1.5, "volume": 80, "quality": "A"},
                    {"name": "Tomatoes", "price": 62.8, "change": 5.2, "volume": 120, "quality": "B"},
                    {"name": "Potatoes", "price": 54.3, "change": 0.8, "volume": 200, "quality": "A"},
                    {"name": "Kale", "price": 35.6, "change": -0.5, "volume": 90, "quality": "A"},
                ],
            }
        ],
        "price_trends": {
            "maize": {"trend": "increasing", "prediction": 48.5, "confidence": 0.75},
            "beans": {"trend": "stable", "prediction": 77.0, "confidence": 0.68},
            "tomatoes": {"trend": "volatile", "prediction": 65.0, "confidence": 0.55},
            "potatoes": {"trend": "stable", "prediction": 53.0, "confidence": 0.72},
            "kale": {"trend": "stable", "prediction": 35.0, "confidence": 0.66},
        },
        "market_insights": [
            "Maize prices are strengthening in major markets.",
            "Bean prices remain fairly stable this week.",
            "Tomato prices are volatile, so staggered harvesting is safer.",
        ],
    }


def _satellite_payload(county: str) -> Dict[str, Any]:
    weather = get_weather(county)
    return {
        "county": county,
        "vegetation_health": {
            "ndvi": 0.64,
            "status": "moderate_to_good",
        },
        "soil_conditions": {
            "soil_moisture": 46,
            "ph_level": 6.4,
            "nitrogen_level": "medium",
            "phosphorus_level": "medium",
            "potassium_level": "medium",
        },
        "climate_risk": {
            "drought_risk": "moderate" if weather["rainfall_mm"] < 350 else "low",
            "flood_risk": "low",
        },
        "timestamp": datetime.now().isoformat(),
    }


def _handle_ussd(session_id: str, phone_number: str, text: str) -> str:
    parts = [part for part in text.split("*") if part] if text else []
    depth = len(parts)

    existing = _get_channel_profile(phone_number)
    lang = existing.get("language", "sw")

    if depth == 0:
        return "CON Karibu Fahamu Shamba!\n1. Kiswahili\n2. English"

    lang = "sw" if parts[0] == "1" else "en"
    if depth == 1:
        return _localized(
            "CON Menyu Kuu:\n1. Pendekezo la mazao\n2. Hali ya hewa\n3. Bei za soko\n4. Uliza AI\n5. Jisajili",
            "CON Main Menu:\n1. Crop recommendations\n2. Weather\n3. Market prices\n4. Ask AI\n5. Register",
            lang,
        )

    choice = parts[1]
    if choice == "1":
        if not existing:
            return _localized(
                "END Jisajili kwanza kwenye chaguo la 5.",
                "END Please register first using option 5.",
                lang,
            )
        return "END " + _recommendation_text(phone_number, {**existing, "language": lang})

    if choice == "2":
        return "END " + _weather_text({**existing, "language": lang})

    if choice == "3":
        return "END " + _market_text(lang)

    if choice == "4":
        if depth == 2:
            _save_session(session_id, phone_number, "ussd", "ai_question", {"language": lang})
            return _localized(
                "CON Andika swali lako la kilimo:",
                "CON Enter your farming question:",
                lang,
            )
        question = "*".join(parts[2:]).strip()
        if not question:
            return _localized("END Swali linahitajika.", "END A question is required.", lang)
        response = _chat_response(question, phone_number, context=_recommendation_context(phone_number, existing))
        return "END " + response.get("response", "")[:CHATBOT_RESPONSE_LIMIT]

    if choice == "5":
        if depth == 2:
            return _localized("CON Weka jina lako:", "CON Enter your name:", lang)
        if depth == 3:
            return _localized(
                "CON Chagua kaunti:\n1. Nairobi\n2. Nakuru\n3. Eldoret\n4. Kisumu\n5. Kitui\n6. Kakamega\n7. Mombasa\n8. Garissa",
                "CON Choose county:\n1. Nairobi\n2. Nakuru\n3. Eldoret\n4. Kisumu\n5. Kitui\n6. Kakamega\n7. Mombasa\n8. Garissa",
                lang,
            )
        if depth == 4:
            return _localized("CON Weka ukubwa wa shamba kwa ekari:", "CON Enter land size in acres:", lang)
        if depth == 5:
            return _localized(
                "CON Chagua aina ya udongo:\n1. Sandy\n2. Clay\n3. Loamy\n4. Silty",
                "CON Choose soil type:\n1. Sandy\n2. Clay\n3. Loamy\n4. Silty",
                lang,
            )
        if depth == 6:
            return _localized(
                "CON Una umwagiliaji?\n1. Ndiyo\n2. Hapana",
                "CON Do you have irrigation?\n1. Yes\n2. No",
                lang,
            )
        if depth == 7:
            county = COUNTY_MENU.get(parts[3], "nairobi")
            soil_type = SOIL_MENU.get(parts[5], "loamy")
            irrigation_available = 1 if parts[6] == "1" else 0
            try:
                _save_channel_profile(
                    phone_number,
                    {
                        "name": parts[2].strip(),
                        "county": county,
                        "land_size_acres": float(parts[4]),
                        "soil_type": soil_type,
                        "language": lang,
                        "irrigation_available": irrigation_available,
                    },
                )
            except ValueError:
                return _localized(
                    "END Ekari si sahihi. Jaribu tena.",
                    "END Invalid land size. Please try again.",
                    lang,
                )
            return _localized(
                "END Umesajiliwa. Piga tena kupata ushauri.",
                "END Registration complete. Dial again for advice.",
                lang,
            )

    return _localized("END Chaguo batili.", "END Invalid option.", lang)


@app.route("/ussd", methods=["POST"])
def ussd_callback():
    session_id = request.form.get("sessionId", "").strip()
    phone_number = request.form.get("phoneNumber", "").strip()
    text = request.form.get("text", "").strip()
    response = _handle_ussd(session_id, phone_number, text)
    return response, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/weather/<county>", methods=["GET"])
def realtime_weather(county: str):
    weather = get_weather(county)
    return jsonify(
        {
            "county": county,
            "current": {
                "temperature": weather["temperature"],
                "humidity": weather["humidity"],
                "rainfall_mm": weather["rainfall_mm"],
                "wind_speed": weather.get("wind_speed", 3.5),
            },
            "forecast_24h": {
                "conditions": weather["description"],
                "rain_probability": 40,
            },
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/market", methods=["GET"])
def realtime_market():
    return jsonify(_market_payload())


@app.route("/satellite/<county>", methods=["GET"])
def realtime_satellite(county: str):
    return jsonify(_satellite_payload(county))


@app.route("/sms/send", methods=["POST"])
def sms_send():
    payload = request.get_json(silent=True) or {}
    result = _send_sms(
        str(payload.get("phone", "")).strip(),
        str(payload.get("message", "")).strip(),
        str(payload.get("provider", "africastalking")).strip(),
    )
    return jsonify(result), 200 if result.get("success") else 502


@app.route("/sms/inbound/twilio", methods=["POST"])
def sms_inbound_twilio():
    incoming = request.form.get("Body", "").strip()
    phone_number = request.form.get("From", "").strip()
    context = _recommendation_context(phone_number, _get_channel_profile(phone_number))
    response = _chat_response(incoming or "Help me with farming advice", phone_number, context=context)
    twiml = MessagingResponse()
    twiml.message(response.get("response", "")[:1600])
    return str(twiml), 200, {"Content-Type": "text/xml; charset=utf-8"}


@app.route("/sms/inbound/africastalking", methods=["POST"])
def sms_inbound_africastalking():
    incoming = request.form.get("text", "").strip()
    phone_number = request.form.get("from", "").strip() or request.form.get("phoneNumber", "").strip()
    context = _recommendation_context(phone_number, _get_channel_profile(phone_number))
    response = _chat_response(incoming or "Help me with farming advice", phone_number, context=context)
    return response.get("response", "")[:160]


@app.route("/ivr/incoming", methods=["POST"])
def ivr_incoming():
    response = VoiceResponse()
    gather = Gather(num_digits=1, action="/ivr/language", method="POST", timeout=8)
    gather.say(
        "Karibu Fahamu Shamba. Bonyeza moja kwa Kiswahili. Press two for English.",
        language="en-US",
    )
    response.append(gather)
    response.redirect("/ivr/incoming")
    return str(response), 200, {"Content-Type": "text/xml; charset=utf-8"}


@app.route("/ivr/language", methods=["POST"])
def ivr_language():
    lang = "sw" if request.form.get("Digits", "1") == "1" else "en"
    response = VoiceResponse()
    gather = Gather(num_digits=1, action=f"/ivr/menu?lang={lang}", method="POST", timeout=8)
    gather.say(
        _localized(
            "Bonyeza moja kwa pendekezo la mazao. Mbili kwa hali ya hewa. Tatu kwa bei za soko. Nne kuuliza AI.",
            "Press one for crop recommendations. Two for weather. Three for market prices. Four to ask the AI assistant.",
            lang,
        ),
        language="sw-KE" if lang == "sw" else "en-US",
    )
    response.append(gather)
    return str(response), 200, {"Content-Type": "text/xml; charset=utf-8"}


@app.route("/ivr/menu", methods=["POST"])
def ivr_menu():
    lang = request.args.get("lang", "sw")
    digit = request.form.get("Digits", "1")
    phone_number = request.form.get("From", "").strip()
    profile = {**_get_channel_profile(phone_number), "language": lang}

    response = VoiceResponse()
    if digit == "1":
        if not profile.get("county"):
            response.say(
                _localized(
                    "Tafadhali jisajili kwanza kwa USSD kabla ya kupata pendekezo la mazao.",
                    "Please register first through USSD before requesting crop recommendations.",
                    lang,
                ),
                language="sw-KE" if lang == "sw" else "en-US",
            )
        else:
            response.say(_recommendation_text(phone_number, profile), language="sw-KE" if lang == "sw" else "en-US")
    elif digit == "2":
        response.say(_weather_text(profile), language="sw-KE" if lang == "sw" else "en-US")
    elif digit == "3":
        response.say(_market_text(lang), language="sw-KE" if lang == "sw" else "en-US")
    elif digit == "4":
        gather = Gather(
            input="speech",
            speech_timeout="auto",
            action=f"/ivr/ask?lang={lang}",
            method="POST",
            timeout=8,
        )
        gather.say(
            _localized("Sema swali lako la kilimo baada ya mlio.", "Please say your farming question after the tone.", lang),
            language="sw-KE" if lang == "sw" else "en-US",
        )
        response.append(gather)
    else:
        response.say(_localized("Chaguo batili.", "Invalid option.", lang), language="sw-KE" if lang == "sw" else "en-US")
    return str(response), 200, {"Content-Type": "text/xml; charset=utf-8"}


@app.route("/ivr/ask", methods=["POST"])
def ivr_ask():
    lang = request.args.get("lang", "sw")
    speech = request.form.get("SpeechResult", "").strip()
    phone_number = request.form.get("From", "").strip()
    context = _recommendation_context(phone_number, _get_channel_profile(phone_number))
    reply = _chat_response(speech or "Give me farming advice", phone_number, context=context)

    response = VoiceResponse()
    response.say(reply.get("response", "")[:600], language="sw-KE" if lang == "sw" else "en-US")
    return str(response), 200, {"Content-Type": "text/xml; charset=utf-8"}


@app.route("/feedback", methods=["POST"])
def feedback_post():
    ok = feedback_system.collect_feedback(request.get_json(silent=True) or {})
    return jsonify({"success": ok}), 200 if ok else 400


@app.route("/feedback/analytics", methods=["GET"])
def feedback_analytics():
    return jsonify(feedback_system.get_analytics())


@app.route("/feedback/retrain", methods=["POST"])
def feedback_retrain():
    payload = request.get_json(silent=True) or {}
    threshold = int(payload.get("threshold", 25))
    return jsonify(feedback_system.retrain_if_ready(threshold))


@app.route("/debug-llm", methods=["GET"])
def debug_llm():
    api_key = settings.openai_api_key
    is_groq = api_key.startswith("gsk_")
    api_url = "https://api.groq.com/openai/v1/chat/completions" if is_groq else "https://api.openai.com/v1/chat/completions"
    model = "llama3-8b-8192" if is_groq else settings.openai_model
    try:
        import requests as req
        resp = req.post(
            api_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "What is the current market price of tomatoes in Kenya? Give a short answer."}],
                "max_tokens": 200,
            },
            timeout=20,
        )
        return jsonify({
            "status_code": resp.status_code,
            "provider": "groq" if is_groq else "openai",
            "model": model,
            "key_prefix": api_key[:8] + "...",
            "response_body": resp.json() if resp.ok else resp.text,
        })
    except Exception as exc:
        return jsonify({"error": str(exc), "provider": "groq" if is_groq else "openai"}), 500


@app.route("/deployment/summary", methods=["GET"])
def deployment_summary():
    readiness = chatbot.readiness_report()
    return jsonify(
        {
            "status": "ok",
            "channels": {
                "web_chat": True,
                "sms_twilio": True,
                "sms_africastalking": True,
                "ussd_africastalking": True,
                "ivr_twilio": True,
                "feedback_loop": True,
            },
            "database_path": DB_PATH,
            "readiness": readiness,
        }
    )


_init_channel_tables()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
