#!/usr/bin/env python3
"""
Fahamu Shamba - Farmer-Focused Chatbot with safer production defaults.
"""

import logging
import os
import re
import sqlite3
import threading
import time
from collections import defaultdict, deque
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, Optional

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request, session, redirect, url_for, flash, render_template
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


def get_recommendation_engine_class():
    from enhanced_recommendation_engine import EnhancedCropRecommendationEngine

    return EnhancedCropRecommendationEngine


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: Optional[str], default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _as_float(value: Optional[str], default: float) -> float:
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


def _looks_placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered:
        return True
    placeholder_markers = (
        "replace_with",
        "your_",
        "example",
        "changeme",
        "placeholder",
        "secret_key=",
    )
    return any(marker in lowered for marker in placeholder_markers)


class Settings:
    def __init__(self) -> None:
        self.flask_env = os.getenv("FLASK_ENV", "development").strip().lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        self.db_path = os.getenv("DB_PATH", "fahamu_shamba.db").strip()
        self.debug = _as_bool(os.getenv("DEBUG"), default=False)
        self.secret_key = os.getenv("SECRET_KEY", "").strip()
        self.rate_limit_per_minute = max(1, _as_int(os.getenv("RATE_LIMIT_PER_MINUTE"), 60))
        self.max_response_length = max(100, _as_int(os.getenv("MAX_RESPONSE_LENGTH"), 500))
        self.confidence_threshold = _as_float(os.getenv("CONFIDENCE_THRESHOLD"), 0.3)
        self.request_timeout = max(5, _as_int(os.getenv("OPENAI_TIMEOUT_SECONDS"), 25))
        self.data_service_url = os.getenv("DATA_SERVICE_URL", "").rstrip("/")
        self.allowed_origins = [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5002,http://127.0.0.1:5002").split(",")
            if origin.strip()
        ]
        self.service_api_key = os.getenv("FAHAMU_API_KEY", "").strip()
        self.max_message_length = max(50, _as_int(os.getenv("MAX_MESSAGE_LENGTH"), 1000))

    @property
    def openai_configured(self) -> bool:
        key = self.openai_api_key
        if _looks_placeholder(key):
            return False
        return key.startswith("sk-") or key.startswith("gsk_")

    @property
    def secret_configured(self) -> bool:
        return not _looks_placeholder(self.secret_key)

    @property
    def service_api_key_configured(self) -> bool:
        return not _looks_placeholder(self.service_api_key)

    @property
    def production_mode(self) -> bool:
        return self.flask_env == "production"

    @property
    def production_config_ok(self) -> bool:
        if not self.production_mode:
            return True
        return self.openai_configured and self.secret_configured and self.service_api_key_configured

    def validate(self) -> None:
        db_parent = Path(self.db_path).expanduser().resolve().parent
        db_parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.validate()

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.secret_key or "development-secret-key"
app.config["JSON_SORT_KEYS"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

CORS(
    app,
    resources={
        r"/chat": {"origins": settings.allowed_origins},
        r"/profile*": {"origins": settings.allowed_origins},
        r"/health*": {"origins": settings.allowed_origins},
        r"/login*": {"origins": settings.allowed_origins},
        r"/register*": {"origins": settings.allowed_origins},
        r"/logout*": {"origins": settings.allowed_origins},
    },
    supports_credentials=True,
)

TRANSLATIONS = {
    "en": {
        "title": "Fahamu Shamba",
        "rights": "All rights reserved.",
        "login_title": "Welcome Back",
        "login_subtitle": "Sign in to your farmer account",
        "email_username": "Email or Username",
        "email_username_placeholder": "Enter your email or username",
        "password": "Password",
        "password_placeholder": "Enter your password",
        "remember_me": "Remember me",
        "forgot_password": "Forgot password?",
        "login_button": "Sign In",
        "no_account": "Don't have an account?",
        "register_link": "Sign up",
        "mobile_access": "Mobile Access",
        "multilingual": "Multilingual Support",
        "secure": "Secure & Private",
        "register_title": "Create Account",
        "register_subtitle": "Join our farming community",
        "first_name": "First Name",
        "first_name_placeholder": "Enter your first name",
        "last_name": "Last Name",
        "last_name_placeholder": "Enter your last name",
        "email": "Email Address",
        "email_placeholder": "Enter your email address",
        "phone": "Phone Number",
        "phone_placeholder": "Enter your phone number",
        "confirm_password": "Confirm Password",
        "confirm_password_placeholder": "Confirm your password",
        "county": "County",
        "select_county": "Select your county",
        "agree_terms": "I agree to the",
        "terms_link": "Terms & Conditions",
        "newsletter": "Subscribe to newsletter",
        "register_button": "Create Account",
        "have_account": "Already have an account?",
        "login_link": "Sign in",
        "password_weak": "Weak",
        "password_medium": "Medium",
        "password_strong": "Strong",
        "required_field": "This field is required",
        "invalid_email": "Please enter a valid email address",
        "invalid_phone": "Please enter a valid phone number",
        "password_too_short": "Password must be at least 8 characters",
        "password_mismatch": "Passwords do not match",
        "password_weak_error": "Password is too weak",
        "terms_required": "You must agree to the terms and conditions",
        "invalid_name": "Name can only contain letters and spaces"
    },
    "sw": {
        "title": "Kuingia kwa Mkulima",
        "rights": "Haki zote zimehifadhiwa.",
        "login_title": "Karibu Tena",
        "login_subtitle": "Ingia kwenye akaunti yako ya mkulima",
        "email_username": "Barua pepe au Jina la mtumiaji",
        "email_username_placeholder": "Ingiza barua pepe au jina la mtumiaji",
        "password": "Nenosiri",
        "password_placeholder": "Ingiza nenosiri lako",
        "remember_me": "Nikumbuke",
        "forgot_password": "Umesahau nenosiri?",
        "login_button": "Ingia",
        "no_account": "Huna akaunti?",
        "register_link": "Jisajili",
        "mobile_access": "Upatikanaji wa Simu",
        "multilingual": "Msaada wa Lugha Nyingi",
        "secure": "Salama na Faragha",
        "register_title": "Tengeneza Akaunti",
        "register_subtitle": "Jiunge na jumuiya yetu ya wakulima",
        "first_name": "Jina la Kwanza",
        "first_name_placeholder": "Ingiza jina lako la kwanza",
        "last_name": "Jina la Mwisho",
        "last_name_placeholder": "Ingiza jina lako la mwisho",
        "email": "Anwani ya Barua Pepe",
        "email_placeholder": "Ingiza anwani yako ya barua pepe",
        "phone": "Nambari ya Simu",
        "phone_placeholder": "Ingiza nambari yako ya simu",
        "confirm_password": "Thibitisha Nenosiri",
        "confirm_password_placeholder": "Thibitisha nenosiri lako",
        "county": "Kaunti",
        "select_county": "Chagua kaunti yako",
        "agree_terms": "Ninakubali",
        "terms_link": "Sheria na Masharti",
        "newsletter": "Jisajili kwa jarida",
        "register_button": "Tengeneza Akaunti",
        "have_account": "Tayari una akaunti?",
        "login_link": "Ingia",
        "password_weak": "Dhaifu",
        "password_medium": "Wastani",
        "password_strong": "Imara",
        "required_field": "Uwanja huu unahitajika",
        "invalid_email": "Tafadhali ingiza anwani ya barua pepe sahihi",
        "invalid_phone": "Tafadhali ingiza nambari ya simu sahihi",
        "password_too_short": "Nenosiri lazima liwe na angalau vibambo 8",
        "password_mismatch": "Manenosiri hayafanani",
        "password_weak_error": "Nenosiri ni dhaifu sana",
        "terms_required": "Lazima ukubali sheria na masharti",
        "invalid_name": "Jina linaweza kuwa na herufi na nafasi tu"
    },
    "fr": {
        "title": "Connexion Agriculteur",
        "rights": "Tous droits réservés.",
        "login_title": "Bienvenue",
        "login_subtitle": "Connectez-vous à votre compte agriculteur",
        "email_username": "Email ou Nom d'utilisateur",
        "email_username_placeholder": "Entrez votre email ou nom d'utilisateur",
        "password": "Mot de passe",
        "password_placeholder": "Entrez votre mot de passe",
        "remember_me": "Se souvenir de moi",
        "forgot_password": "Mot de passe oublié?",
        "login_button": "Se connecter",
        "no_account": "Pas de compte?",
        "register_link": "S'inscrire",
        "mobile_access": "Accès Mobile",
        "multilingual": "Support Multilingue",
        "secure": "Sécurisé et Privé",
        "register_title": "Créer un compte",
        "register_subtitle": "Rejoignez notre communauté agricole",
        "first_name": "Prénom",
        "first_name_placeholder": "Entrez votre prénom",
        "last_name": "Nom de famille",
        "last_name_placeholder": "Entrez votre nom de famille",
        "email": "Adresse email",
        "email_placeholder": "Entrez votre adresse email",
        "phone": "Numéro de téléphone",
        "phone_placeholder": "Entrez votre numéro de téléphone",
        "confirm_password": "Confirmer le mot de passe",
        "confirm_password_placeholder": "Confirmez votre mot de passe",
        "county": "Comté",
        "select_county": "Sélectionnez votre comté",
        "agree_terms": "J'accepte les",
        "terms_link": "Termes et Conditions",
        "newsletter": "S'abonner à la newsletter",
        "register_button": "Créer un compte",
        "have_account": "Déjà un compte?",
        "login_link": "Se connecter",
        "password_weak": "Faible",
        "password_medium": "Moyen",
        "password_strong": "Fort",
        "required_field": "Ce champ est requis",
        "invalid_email": "Veuillez entrer une adresse email valide",
        "invalid_phone": "Veuillez entrer un numéro de téléphone valide",
        "password_too_short": "Le mot de passe doit contenir au moins 8 caractères",
        "password_mismatch": "Les mots de passe ne correspondent pas",
        "password_weak_error": "Le mot de passe est trop faible",
        "terms_required": "Vous devez accepter les termes et conditions",
        "invalid_name": "Le nom ne peut contenir que des lettres et des espaces"
    }
}

COUNTIES = [
    "Nairobi",
    "Mombasa",
    "Kisumu",
    "Nakuru",
    "Kiambu",
    "Uasin Gishu",
    "Meru",
    "Machakos",
    "Kajiado",
    "Migori",
    "Kitui",
    "Nyeri",
    "Embu"
]


def get_current_language() -> str:
    lang = request.args.get("lang") or session.get("language") or "en"
    if lang not in TRANSLATIONS:
        lang = "en"
    session["language"] = lang
    return lang


@app.context_processor
def inject_translations():
    return {
        "current_lang": get_current_language(),
        "translations": TRANSLATIONS,
        "counties": COUNTIES,
    }


def _render_auth_template(template_name: str, **context: Any):
    return render_template(template_name, **context)


class RateLimiter:
    def __init__(self, limit_per_minute: int) -> None:
        self.limit = limit_per_minute
        self._requests: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - 60
        with self._lock:
            bucket = self._requests[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return False
            bucket.append(now)
            return True


rate_limiter = RateLimiter(settings.rate_limit_per_minute)


class FarmerAgriculturalChatbot:
    """Specialized chatbot for Kenyan farmers with safer runtime behavior."""

    def __init__(self, config: Settings) -> None:
        self.settings = config
        self.openai_api_key = config.openai_api_key
        self.db_path = config.db_path
        self.data_service_url = config.data_service_url
        self.system_prompt = """You are a specialized agricultural AI assistant for Kenyan farmers. Your name is "Shamba Advisor".

IMPORTANT RULES:
1. ONLY answer questions related to agriculture, farming, crops, livestock, weather, markets, and farming techniques in Kenya.
2. If asked non-agricultural questions, politely decline and redirect to farming topics.
3. Provide practical, actionable advice suitable for Kenyan farming conditions.
4. Consider local context: climate zones, common crops, market conditions, and farming practices in Kenya.
5. Use simple language that farmers can understand.
6. When recommending crops, consider Kenya's climate zones and seasons.
7. Include specific advice for small-scale farmers with limited resources.
8. Prioritize farmer safety and sustainable practices."""
        self.recommendation_engine = None
        self.init_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self) -> None:
        with closing(self._get_connection()) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS farmer_profiles (
                    phone_number TEXT PRIMARY KEY,
                    name TEXT,
                    county TEXT,
                    land_size_acres REAL,
                    main_crops TEXT,
                    farming_experience INTEGER,
                    language_preference TEXT DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    username TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    phone_number TEXT,
                    county TEXT,
                    language_preference TEXT DEFAULT 'en',
                    newsletter_subscribed BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    phone_number TEXT,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    intent TEXT,
                    confidence REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
                """
            )
            self._ensure_columns(
                cursor,
                "farmer_profiles",
                {
                    "land_size_acres": "REAL",
                    "main_crops": "TEXT",
                    "farming_experience": "INTEGER",
                    "language_preference": "TEXT DEFAULT 'en'",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            )
            self._ensure_columns(
                cursor,
                "users",
                {
                    "username": "TEXT",
                    "phone_number": "TEXT",
                    "county": "TEXT",
                    "language_preference": "TEXT DEFAULT 'en'",
                    "newsletter_subscribed": "BOOLEAN DEFAULT 0",
                    "is_active": "BOOLEAN DEFAULT 1",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "last_login": "TIMESTAMP",
                },
            )
            self._ensure_columns(
                cursor,
                "chat_history",
                {
                    "user_id": "INTEGER",
                    "phone_number": "TEXT",
                    "intent": "TEXT",
                    "confidence": "REAL",
                    "timestamp": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                },
            )
            conn.commit()

    def _ensure_columns(self, cursor: sqlite3.Cursor, table_name: str, columns: Dict[str, str]) -> None:
        existing_columns = {
            row[1]
            for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        for column_name, column_type in columns.items():
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

    def _get_recommendation_engine(self):
        if self.recommendation_engine is not None:
            return self.recommendation_engine

        engine_class = get_recommendation_engine_class()
        engine = engine_class()
        try:
            engine.load_model("enhanced_crop_recommendation_model.pkl")
            logger.info("Enhanced recommendation model loaded successfully")
        except FileNotFoundError:
            logger.info("Enhanced recommendation model not found; training bootstrap model")
            data = engine.generate_enhanced_sample_data(400)
            engine.train(data)
            engine.save_model("enhanced_crop_recommendation_model.pkl")
        self.recommendation_engine = engine
        return engine

    def get_farmer_profile(self, phone_number: str) -> Dict[str, Any]:
        with closing(self._get_connection()) as conn:
            row = conn.execute(
                """
                SELECT name, county, land_size_acres, main_crops, farming_experience, language_preference
                FROM farmer_profiles
                WHERE phone_number = ?
                """,
                (phone_number,),
            ).fetchone()

        if not row:
            return {}

        return {
            "name": row["name"],
            "county": row["county"],
            "land_size_acres": row["land_size_acres"],
            "main_crops": row["main_crops"],
            "farming_experience": row["farming_experience"],
            "language_preference": row["language_preference"],
        }

    def save_farmer_profile(self, phone_number: str, profile: Dict[str, Any]) -> None:
        with closing(self._get_connection()) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO farmer_profiles
                (phone_number, name, county, land_size_acres, main_crops, farming_experience, language_preference)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    phone_number,
                    profile.get("name"),
                    profile.get("county"),
                    profile.get("land_size_acres"),
                    profile.get("main_crops"),
                    profile.get("farming_experience"),
                    profile.get("language_preference", "en"),
                ),
            )

    # Authentication methods
    def create_user(self, user_data: Dict[str, Any]) -> Optional[int]:
        """Create a new user account"""
        try:
            with closing(self._get_connection()) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users
                    (email, username, password_hash, first_name, last_name, phone_number, county, language_preference, newsletter_subscribed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_data['email'],
                        user_data.get('username'),
                        generate_password_hash(user_data['password']),
                        user_data['first_name'],
                        user_data['last_name'],
                        user_data.get('phone_number'),
                        user_data.get('county'),
                        user_data.get('language_preference', 'en'),
                        user_data.get('newsletter_subscribed', False)
                    )
                )
                user_id = cursor.lastrowid
                conn.commit()
                return user_id
        except sqlite3.IntegrityError:
            return None  # Email or username already exists

    def authenticate_user(self, identifier: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by email/username and password"""
        with closing(self._get_connection()) as conn:
            row = conn.execute(
                """
                SELECT id, email, username, password_hash, first_name, last_name, phone_number, county, language_preference, newsletter_subscribed
                FROM users
                WHERE (email = ? OR username = ?) AND is_active = 1
                """,
                (identifier, identifier)
            ).fetchone()

            if row and check_password_hash(row['password_hash'], password):
                # Update last login
                conn.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (row['id'],)
                )
                conn.commit()

                return {
                    'id': row['id'],
                    'email': row['email'],
                    'username': row['username'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'phone_number': row['phone_number'],
                    'county': row['county'],
                    'language_preference': row['language_preference'],
                    'newsletter_subscribed': row['newsletter_subscribed']
                }
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        with closing(self._get_connection()) as conn:
            row = conn.execute(
                """
                SELECT id, email, username, first_name, last_name, phone_number, county, language_preference, newsletter_subscribed
                FROM users
                WHERE id = ? AND is_active = 1
                """,
                (user_id,)
            ).fetchone()

            if row:
                return dict(row)
        return None

    def get_openai_response(
        self,
        message: str,
        farmer_profile: Dict[str, Any],
        image_data: Optional[str] = None,
    ) -> Dict[str, Any]:
        api_key = self.openai_api_key
        if not api_key:
            logger.warning("No API key configured; returning fallback response.")
            return self.get_fallback_response(message, reason="missing_api_key", image_supplied=bool(image_data))

        # Support both Groq (gsk_) and OpenAI (sk-) keys
        is_groq = api_key.startswith("gsk_")
        if is_groq:
            api_url = "https://api.groq.com/openai/v1/chat/completions"
            model = "llama3-8b-8192"
        else:
            api_url = "https://api.openai.com/v1/chat/completions"
            model = self.settings.openai_model

        context_prompt = f"""Farmer Profile:
- Name: {farmer_profile.get('name', 'Unknown')}
- Location: {farmer_profile.get('county', 'Unknown county, Kenya')}
- Land size: {farmer_profile.get('land_size_acres', 'Unknown')} acres
- Main crops: {farmer_profile.get('main_crops', 'Not specified')}
- Experience: {farmer_profile.get('farming_experience', 'Unknown')} years
- Language: {farmer_profile.get('language_preference', 'English')}

Current date: {datetime.now().strftime('%Y-%m-%d')}
Season: {self.get_current_season()}

Farmer's question: {message}

Provide helpful agricultural advice based on this farmer's specific context."""

        # Groq does not support image_url content type
        if is_groq or not image_data:
            user_content: Any = context_prompt
        else:
            user_content = [
                {"type": "text", "text": context_prompt},
                {"type": "image_url", "image_url": {"url": image_data}},
            ]

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_content},
            ],
            "max_tokens": min(self.settings.max_response_length, 800),
            "temperature": 0.5,
        }

        try:
            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.settings.request_timeout,
            )
            logger.info("LLM response status: %s provider: %s", response.status_code, "groq" if is_groq else "openai")
            if not response.ok:
                logger.error("LLM error body: %s", response.text[:500])
            response.raise_for_status()
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"].strip()
            is_agricultural = self.is_agricultural_response(ai_response)
            confidence = 0.9 if is_agricultural else max(0.2, self.settings.confidence_threshold)
            return {
                "response": ai_response[: self.settings.max_response_length * 4],
                "confidence": confidence,
                "intent": self.detect_intent(message),
                "is_agricultural": is_agricultural,
                "used_image": bool(image_data),
            }
        except requests.RequestException as exc:
            logger.error("LLM request failed (%s): %s", "groq" if is_groq else "openai", exc)
            return self.get_fallback_response(message, reason="provider_error", image_supplied=bool(image_data))
        except (KeyError, ValueError, TypeError) as exc:
            logger.error("LLM response parsing failed: %s", exc)
            return self.get_fallback_response(message, reason="provider_response_error", image_supplied=bool(image_data))

    def is_agricultural_response(self, response: str) -> bool:
        keywords = [
            "crop",
            "plant",
            "farm",
            "soil",
            "water",
            "rain",
            "weather",
            "maize",
            "beans",
            "potatoes",
            "tomatoes",
            "kale",
            "cabbage",
            "fertilizer",
            "pest",
            "disease",
            "harvest",
            "yield",
            "market",
            "price",
            "seed",
            "irrigation",
            "drought",
            "season",
            "kenya",
            "shamba",
            "kilimo",
            "mazao",
            "mbegu",
            "mvua",
            "hali ya hewa",
        ]
        lowered = response.lower()
        return any(keyword in lowered for keyword in keywords)

    def detect_intent(self, message: str) -> str:
        lowered = message.lower()
        if any(word in lowered for word in ["plant", "grow", "seed", "crop", "panda", "recommend", "best crop", "what should i plant", "nini ninapanda"]):
            return "planting_advice"
        if any(word in lowered for word in ["weather", "rain", "climate", "mvua"]):
            return "weather_query"
        if any(word in lowered for word in ["price", "market", "sell", "bei", "soko"]):
            return "market_query"
        if any(word in lowered for word in ["pest", "disease", "sick", "ugonjwa"]):
            return "pest_disease"
        if any(word in lowered for word in ["fertilizer", "soil", "mbolea", "ardhi"]):
            return "soil_fertility"
        if any(word in lowered for word in ["harvest", "yield", "mavuno"]):
            return "harvest_advice"
        return "general_agriculture"

    def get_current_season(self) -> str:
        month = datetime.now().month
        if month in [3, 4, 5]:
            return "Long rains season (March-May)"
        if month in [10, 11, 12]:
            return "Short rains season (October-December)"
        if month in [6, 7, 8, 9]:
            return "Dry season (June-September)"
        return "Hot season (January-February)"

    def _extract_county_from_text(self, message: str) -> Optional[str]:
        lowered = message.lower()
        for county in self._get_recommendation_engine().KENYA_COUNTIES:
            if county.replace("_", " ") in lowered or county in lowered:
                return county
        return None

    def _fetch_json(self, path: str) -> Dict[str, Any]:
        try:
            if self.data_service_url and "localhost:5007" not in self.data_service_url and "127.0.0.1:5007" not in self.data_service_url:
                response = requests.get(f"{self.data_service_url}{path}", timeout=5)
                response.raise_for_status()
                return response.json()
        except requests.RequestException as exc:
            logger.warning("Realtime data fetch failed for %s: %s", path, exc)
        return self._local_data_fallback(path)

    def _local_data_fallback(self, path: str) -> Dict[str, Any]:
        from weather_service import get_weather

        cleaned_path = path.strip().lower()
        if cleaned_path.startswith("/weather/"):
            county = cleaned_path.rsplit("/", 1)[-1] or "nairobi"
            weather = get_weather(county)
            return {
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
            }
        if cleaned_path == "/market":
            return {
                "markets": [
                    {
                        "name": "Nairobi",
                        "crops": [
                            {"name": "Maize", "price": 45.5},
                            {"name": "Beans", "price": 78.2},
                            {"name": "Tomatoes", "price": 62.8},
                            {"name": "Potatoes", "price": 54.3},
                            {"name": "Kale", "price": 35.6},
                            {"name": "Sorghum", "price": 55.0},
                        ],
                    }
                ],
                "price_trends": {
                    "maize": {"trend": "increasing"},
                    "beans": {"trend": "stable"},
                    "tomatoes": {"trend": "volatile"},
                    "potatoes": {"trend": "stable"},
                    "kale": {"trend": "stable"},
                    "sorghum": {"trend": "increasing"},
                },
                "market_insights": [
                    "Current market prices favor drought-resilient crops in drier counties."
                ],
            }
        if cleaned_path.startswith("/satellite/"):
            county = cleaned_path.rsplit("/", 1)[-1] or "nairobi"
            return {
                "county": county,
                "soil_conditions": {
                    "soil_moisture": 46,
                    "ph_level": 6.4,
                    "nitrogen_level": "medium",
                    "phosphorus_level": "medium",
                    "potassium_level": "medium",
                }
            }
        return {}

    def _collect_market_context(self) -> Dict[str, Any]:
        data = self._fetch_json("/market")
        market_prices: Dict[str, float] = {}
        market_trends: Dict[str, Dict[str, Any]] = {}
        if not data:
            return {"market_prices": market_prices, "market_trends": market_trends, "market_summary": "Market data unavailable"}

        price_buckets: Dict[str, list] = {}
        for market in data.get("markets", []):
            for crop in market.get("crops", []):
                name = str(crop.get("name", "")).lower()
                if not name:
                    continue
                price_buckets.setdefault(name, []).append(float(crop.get("price", 0)))
        for crop_name, prices in price_buckets.items():
            market_prices[crop_name] = round(sum(prices) / len(prices), 2)
        for crop_name, trend_info in (data.get("price_trends") or {}).items():
            market_trends[str(crop_name).lower()] = trend_info

        insights = data.get("market_insights") or []
        return {
            "market_prices": market_prices,
            "market_trends": market_trends,
            "market_summary": insights[0] if insights else "Using current average market prices",
        }

    def _build_farmer_conditions(
        self,
        message: str,
        farmer_profile: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        context = context or {}
        engine = self._get_recommendation_engine()
        county = (
            str(context.get("county") or "").strip().lower()
            or str(farmer_profile.get("county") or "").strip().lower()
            or self._extract_county_from_text(message)
            or "nairobi"
        )
        county_defaults = engine.KENYA_COUNTIES.get(
            county, engine.KENYA_COUNTIES["nairobi"]
        )

        weather_data = self._fetch_json(f"/weather/{county}")
        satellite_data = self._fetch_json(f"/satellite/{county}")
        market_context = self._collect_market_context()

        current_weather = weather_data.get("current", {})
        satellite_soil = satellite_data.get("soil_conditions", {})

        rainfall_mm = float(
            context.get("rainfall_mm")
            or current_weather.get("rainfall_mm")
            or county_defaults["avg_rainfall"]
        )
        temperature_c = float(
            context.get("temperature_c")
            or current_weather.get("temperature")
            or county_defaults["avg_temp"]
        )
        humidity_percent = float(context.get("humidity_percent") or current_weather.get("humidity") or 65)
        soil_ph = float(context.get("soil_ph") or satellite_soil.get("ph_level") or 6.5)
        soil_type = str(context.get("soil_type") or farmer_profile.get("soil_type") or "loamy").lower()
        land_size_acres = float(context.get("land_size_acres") or farmer_profile.get("land_size_acres") or 1.0)
        irrigation_available = int(context.get("irrigation_available", context.get("irrigation", 0)) or 0)
        fertilizer_use = int(context.get("fertilizer_use", 0) or 0)
        market_price_reference = 0.0
        if market_context["market_prices"]:
            market_price_reference = sum(market_context["market_prices"].values()) / len(market_context["market_prices"])

        return {
            "county": county,
            "soil_type": soil_type,
            "soil_ph": soil_ph,
            "rainfall_mm": rainfall_mm,
            "temperature_c": temperature_c,
            "humidity_percent": humidity_percent,
            "land_size_acres": land_size_acres,
            "irrigation_available": irrigation_available,
            "fertilizer_use": fertilizer_use,
            "market_price_kes": round(market_price_reference, 2) if market_price_reference else 50,
            "market_prices": market_context["market_prices"],
            "market_trends": market_context["market_trends"],
            "market_summary": market_context["market_summary"],
            "weather_summary": weather_data.get("forecast_24h", {}).get("conditions", "Seasonal weather pattern"),
            "soil_summary": {
                "soil_moisture": satellite_soil.get("soil_moisture"),
                "nitrogen_level": satellite_soil.get("nitrogen_level"),
                "phosphorus_level": satellite_soil.get("phosphorus_level"),
                "potassium_level": satellite_soil.get("potassium_level"),
            },
        }

    def get_crop_recommendation_response(
        self,
        message: str,
        farmer_profile: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        engine = self._get_recommendation_engine()
        farmer_conditions = self._build_farmer_conditions(message, farmer_profile, context)
        recommendations = engine.get_recommendations(farmer_conditions)
        top = recommendations["top_recommendation"]
        lines = [
            f"Best crop to plant now for {farmer_conditions['county'].title()}: {top['crop'].title()}",
            f"Confidence: {top['confidence']}%",
            f"Expected yield: {top['expected_yield_tons_per_acre']} tons/acre",
            f"Expected revenue: KES {int(top['expected_revenue_kes']):,}",
            f"Weather: {farmer_conditions['weather_summary']}",
            f"Soil pH: {farmer_conditions['soil_ph']}",
            f"Market signal: {farmer_conditions['market_summary']}",
            "",
            "Top options:",
        ]
        for idx, crop in enumerate(recommendations["all_recommendations"], 1):
            lines.append(
                f"{idx}. {crop['crop'].title()} - {crop['confidence']}% confidence, KES {int(crop['expected_revenue_kes']):,} revenue estimate, market trend: {crop['market_trend']}"
            )
        lines.append("")
        lines.append(f"Why: {top['reason']}")

        return {
            "response": "\n".join(lines)[: self.settings.max_response_length * 3],
            "confidence": round(top["confidence"] / 100, 2),
            "intent": "planting_advice",
            "is_agricultural": True,
            "used_recommendation_engine": True,
            "recommendation_data": recommendations,
            "input_conditions": farmer_conditions,
        }

    def get_fallback_response(
        self,
        message: str,
        reason: str = "fallback",
        image_supplied: bool = False,
    ) -> Dict[str, Any]:
        intent = self.detect_intent(message)
        fallback_responses = {
            "planting_advice": "For planting advice, consider your local climate and soil type. In Kenya, maize is commonly planted during the long rains (March-May) and short rains (October-December). Contact your local agricultural extension officer for specific recommendations.",
            "weather_query": "For weather information, listen to local radio forecasts or contact the Kenya Meteorological Department. Kenya generally has long rains in March to May and short rains in October to December.",
            "market_query": "For current market prices, check with local markets or the Ministry of Agriculture. Prices vary by region and season, so compare nearby markets before selling.",
            "pest_disease": "For pest and disease management, use certified seeds, practice crop rotation, and contact your local agricultural extension officer for treatment recommendations.",
            "soil_fertility": "For soil fertility, consider organic compost, crop rotation, and appropriate fertilizers based on soil tests. Your local agricultural office can help with soil testing.",
            "harvest_advice": "Harvest timing depends on crop maturity and local conditions. Harvest when the crop is mature and store it well to reduce post-harvest losses.",
        }
        default_response = "I'm here to help with agricultural questions. Please ask about crops, planting, weather, markets, pests, soil, or farming techniques in Kenya."
        if image_supplied:
            default_response = (
                "I can help with agriculture-related images such as crop diseases, pests, soil issues, weeds, and livestock concerns. "
                "Please include a short agriculture question with the image for the best advice."
            )
        return {
            "response": fallback_responses.get(
                intent,
                default_response,
            )[: self.settings.max_response_length],
            "confidence": max(0.4, self.settings.confidence_threshold),
            "intent": intent,
            "is_agricultural": True,
            "source": reason,
            "used_image": image_supplied,
        }

    def save_chat_history(self, phone_number: str, message: str, response: Dict[str, Any]) -> None:
        with closing(self._get_connection()) as conn:
            conn.execute(
                """
                INSERT INTO chat_history (phone_number, message, response, intent, confidence)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    phone_number,
                    message,
                    response["response"],
                    response.get("intent"),
                    response.get("confidence", 0.0),
                ),
            )

    def process_message(
        self,
        message: str,
        phone_number: Optional[str] = None,
        image_data: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        farmer_profile = self.get_farmer_profile(phone_number) if phone_number else {}
        intent = self.detect_intent(message)
        if intent == "planting_advice":
            response = self.get_crop_recommendation_response(message, farmer_profile, context=context)
        else:
            response = self.get_openai_response(message, farmer_profile, image_data=image_data)
        if phone_number:
            self.save_chat_history(phone_number, message, response)
        response["timestamp"] = datetime.now().isoformat()
        response["farmer_context"] = {
            "county": farmer_profile.get("county"),
            "land_size": farmer_profile.get("land_size_acres"),
            "experience": farmer_profile.get("farming_experience"),
        }
        return response

    def readiness_report(self) -> Dict[str, Any]:
        db_ok = True
        db_error = None
        try:
            with closing(self._get_connection()) as conn:
                conn.execute("SELECT 1").fetchone()
        except sqlite3.Error as exc:
            db_ok = False
            db_error = str(exc)
        api_key = self.settings.openai_api_key
        provider = "groq" if api_key.startswith("gsk_") else "openai" if api_key.startswith("sk-") else "none"
        return {
            "database_ok": db_ok,
            "database_error": db_error,
            "openai_configured": self.settings.openai_configured,
            "llm_provider": provider,
            "secret_configured": self.settings.secret_configured,
            "service_api_key_configured": self.settings.service_api_key_configured,
            "production_mode": self.settings.production_mode,
            "production_config_ok": self.settings.production_config_ok,
            "rate_limit_per_minute": self.settings.rate_limit_per_minute,
        }


chatbot = FarmerAgriculturalChatbot(settings)


def _request_identity() -> str:
    payload = request.get_json(silent=True) or {}
    phone = payload.get("phone_number") or payload.get("user_id")
    forwarded = request.headers.get("X-Forwarded-For", "")
    ip = forwarded.split(",")[0].strip() if forwarded else request.remote_addr or "unknown"
    return str(phone or ip)


def _require_service_api_key() -> Optional[Any]:
    if not settings.service_api_key:
        return None
    header = request.headers.get("X-API-Key", "").strip()
    if header == settings.service_api_key:
        return None
    return jsonify({"error": "Unauthorized"}), 401


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


# Authentication routes
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form
        identifier = data.get("identifier", "").strip()
        password = data.get("password", "")

        if not identifier or not password:
            error_message = "Email/username and password are required"
            if request.is_json:
                return jsonify({"error": error_message}), 400
            return _render_auth_template("login.html", error=error_message)

        user = chatbot.authenticate_user(identifier, password)
        if user:
            session["user_id"] = user["id"]
            session["user_email"] = user["email"]
            session["user_name"] = f"{user['first_name']} {user['last_name']}"
            if request.is_json:
                return jsonify({
                    "success": True,
                    "user": {
                        "id": user["id"],
                        "email": user["email"],
                        "name": f"{user['first_name']} {user['last_name']}",
                        "county": user["county"],
                        "language_preference": user["language_preference"]
                    }
                })
            return redirect(url_for("dashboard"))

        error_message = "Invalid credentials"
        if request.is_json:
            return jsonify({"error": error_message}), 401
        return _render_auth_template("login.html", error=error_message)

    return _render_auth_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.get_json(silent=True) or request.form

        required_fields = ["email", "first_name", "last_name", "password", "confirm_password"]
        for field in required_fields:
            if not data.get(field, "").strip():
                error_message = f"{field.replace('_', ' ').title()} is required"
                if request.is_json:
                    return jsonify({"error": error_message}), 400
                return _render_auth_template("register.html", error=error_message)

        if data["password"] != data["confirm_password"]:
            error_message = "Passwords do not match"
            if request.is_json:
                return jsonify({"error": error_message}), 400
            return _render_auth_template("register.html", error=error_message)

        if len(data["password"]) < 8:
            error_message = "Password must be at least 8 characters long"
            if request.is_json:
                return jsonify({"error": error_message}), 400
            return _render_auth_template("register.html", error=error_message)

        if not bool(data.get("terms", False)):
            error_message = "You must agree to the terms and conditions"
            if request.is_json:
                return jsonify({"error": error_message}), 400
            return _render_auth_template("register.html", error=error_message)

        user_data = {
            "email": data["email"].strip().lower(),
            "username": data.get("username", "").strip() or None,
            "first_name": data["first_name"].strip(),
            "last_name": data["last_name"].strip(),
            "password": data["password"],
            "phone_number": (data.get("phone_number") or data.get("phone") or "").strip() or None,
            "county": data.get("county", "").strip() or None,
            "language_preference": data.get("language_preference", "en"),
            "newsletter_subscribed": bool(data.get("newsletter_subscribed", data.get("newsletter", False)))
        }

        user_id = chatbot.create_user(user_data)
        if user_id:
            session["user_id"] = user_id
            session["user_email"] = user_data["email"]
            session["user_name"] = f"{user_data['first_name']} {user_data['last_name']}"
            if request.is_json:
                return jsonify({
                    "success": True,
                    "user": {
                        "id": user_id,
                        "email": user_data["email"],
                        "name": f"{user_data['first_name']} {user_data['last_name']}",
                        "county": user_data["county"],
                        "language_preference": user_data["language_preference"]
                    }
                })
            return redirect(url_for("dashboard"))

        error_message = "Email or username already exists"
        if request.is_json:
            return jsonify({"error": error_message}), 409
        return _render_auth_template("register.html", error=error_message)

    return _render_auth_template("register.html")


@app.route("/forgot-password")
def forgot_password():
    title = TRANSLATIONS[get_current_language()]["forgot_password"]
    message = "If you forget your password, please contact support or follow the reset link if available."
    return render_template("info.html", title=title, message=message)


@app.route("/terms")
def terms():
    title = TRANSLATIONS[get_current_language()]["terms_link"]
    message = "By using Fahamu Shamba, you agree to our terms and conditions. Please contact the site administrator to view the full terms document."
    return render_template("info.html", title=title, message=message)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = chatbot.get_user_by_id(session["user_id"])
    if not user:
        session.clear()
        return redirect(url_for("login"))

    return render_template("dashboard.html", user=user)


@app.route("/")
def index():
    return render_template_string(
        """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shamba Advisor</title>
    <style>
        :root {
            --bg-1: #143b2d;
            --bg-2: #95d26b;
            --panel: rgba(250, 252, 246, 0.95);
            --ink: #14211b;
            --muted: #627268;
            --line: #d7e2d7;
            --user: linear-gradient(135deg, #1e7a46, #0f5f37);
            --bot: #ffffff;
            --accent: #d89f3d;
            --danger: #9f3f2f;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0;
            min-height: 100vh;
            font-family: Georgia, "Segoe UI", sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at top left, rgba(216, 159, 61, 0.24), transparent 24%),
                radial-gradient(circle at bottom right, rgba(18, 77, 54, 0.35), transparent 28%),
                linear-gradient(140deg, var(--bg-1), var(--bg-2));
            display: grid;
            place-items: center;
            padding: 24px;
        }
        .shell {
            width: min(100%, 980px);
            min-height: min(92vh, 860px);
            display: grid;
            grid-template-columns: 290px minmax(0, 1fr);
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 28px;
            backdrop-filter: blur(16px);
            overflow: hidden;
            box-shadow: 0 26px 70px rgba(4, 18, 10, 0.35);
        }
        .aside {
            padding: 28px 24px;
            background: linear-gradient(180deg, rgba(10, 31, 23, 0.72), rgba(16, 53, 33, 0.52));
            color: #f1f7ee;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .badge {
            display: inline-flex;
            width: fit-content;
            padding: 7px 12px;
            border-radius: 999px;
            background: rgba(216, 159, 61, 0.18);
            border: 1px solid rgba(216, 159, 61, 0.32);
            font-size: 12px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .aside h1 {
            margin: 0;
            font-size: 34px;
            line-height: 1;
        }
        .aside p {
            margin: 0;
            color: rgba(241, 247, 238, 0.82);
            line-height: 1.5;
        }
        .hint-list {
            display: grid;
            gap: 10px;
            margin-top: 8px;
        }
        .hint {
            padding: 12px 14px;
            border-radius: 16px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.08);
            font-size: 14px;
            line-height: 1.4;
        }
        .main {
            display: flex;
            flex-direction: column;
            background: var(--panel);
        }
        .header {
            padding: 24px 28px 18px;
            border-bottom: 1px solid var(--line);
            display: flex;
            justify-content: space-between;
            align-items: end;
            gap: 16px;
        }
        .header h2 { margin: 0 0 6px; font-size: 26px; }
        .muted { color: var(--muted); font-size: 14px; line-height: 1.45; }
        .status {
            min-width: 150px;
            text-align: right;
            font-size: 13px;
            color: var(--muted);
        }
        .chat {
            flex: 1;
            overflow-y: auto;
            padding: 24px 28px 12px;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.5), rgba(244, 248, 241, 0.95)),
                repeating-linear-gradient(
                    -45deg,
                    rgba(20,59,45,0.02),
                    rgba(20,59,45,0.02) 8px,
                    rgba(255,255,255,0.02) 8px,
                    rgba(255,255,255,0.02) 16px
                );
        }
        .row {
            display: flex;
            margin-bottom: 16px;
        }
        .row.user { justify-content: flex-end; }
        .bubble {
            max-width: min(76%, 640px);
            border-radius: 22px;
            padding: 14px 16px;
            white-space: pre-wrap;
            line-height: 1.5;
            box-shadow: 0 10px 20px rgba(18, 33, 27, 0.08);
        }
        .row.bot .bubble {
            background: var(--bot);
            border: 1px solid var(--line);
        }
        .row.user .bubble {
            color: white;
            background: var(--user);
        }
        .meta {
            margin-top: 8px;
            font-size: 12px;
            color: var(--muted);
        }
        .upload-preview {
            margin-top: 10px;
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.2);
            width: min(220px, 100%);
            background: rgba(255,255,255,0.08);
        }
        .upload-preview img { width: 100%; display: block; }
        .composer {
            padding: 18px 20px 22px;
            border-top: 1px solid var(--line);
            background: rgba(255,255,255,0.7);
        }
        .preview-bar {
            display: none;
            align-items: center;
            gap: 14px;
            margin-bottom: 14px;
            padding: 12px;
            border: 1px dashed #b7c8b8;
            border-radius: 18px;
            background: #f7fbf5;
        }
        .preview-bar.active { display: flex; }
        .preview-bar img {
            width: 74px;
            height: 74px;
            object-fit: cover;
            border-radius: 16px;
            border: 1px solid var(--line);
        }
        .preview-copy { flex: 1; min-width: 0; }
        .preview-copy strong {
            display: block;
            margin-bottom: 4px;
            font-size: 14px;
        }
        .controls {
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }
        .input-stack {
            flex: 1;
            display: grid;
            gap: 10px;
        }
        textarea {
            width: 100%;
            min-height: 84px;
            resize: vertical;
            border: 1px solid #cad5ca;
            border-radius: 22px;
            padding: 16px 18px;
            font: inherit;
            color: var(--ink);
            background: #fff;
            outline: none;
        }
        .toolbar {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
        }
        .farm-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 10px;
        }
        .farm-grid label {
            display: grid;
            gap: 6px;
            font-size: 12px;
            color: var(--muted);
        }
        .farm-grid input, .farm-grid select {
            width: 100%;
            border: 1px solid #cad5ca;
            border-radius: 14px;
            padding: 10px 12px;
            font: inherit;
            background: #fff;
        }
        .tool-left, .tool-right {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        .button, .upload-button {
            border: 0;
            border-radius: 999px;
            padding: 12px 16px;
            cursor: pointer;
            font: inherit;
            transition: transform 0.15s ease, opacity 0.15s ease;
        }
        .button:hover, .upload-button:hover { transform: translateY(-1px); }
        .button:disabled, .upload-button:disabled { cursor: not-allowed; opacity: 0.55; transform: none; }
        .button.primary { background: #1f7a3d; color: #fff; min-width: 112px; }
        .button.secondary, .upload-button { background: #eef4ea; color: var(--ink); border: 1px solid var(--line); }
        .button.stop { background: #f7e6e3; color: var(--danger); border: 1px solid #ebc3bc; }
        .typing {
            display: none;
            margin: 0 28px 18px;
            color: var(--muted);
            font-size: 14px;
            align-items: center;
            gap: 10px;
        }
        .typing.active { display: flex; }
        .dots { display: inline-flex; gap: 5px; }
        .dot {
            width: 8px;
            height: 8px;
            border-radius: 999px;
            background: #7d8d7b;
            animation: bounce 1.1s infinite ease-in-out;
        }
        .dot:nth-child(2) { animation-delay: 0.15s; }
        .dot:nth-child(3) { animation-delay: 0.3s; }
        .hidden { display: none; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0.8); opacity: 0.45; }
            40% { transform: scale(1.05); opacity: 1; }
        }
        @media (max-width: 900px) {
            .shell { grid-template-columns: 1fr; }
            .aside { display: none; }
            .bubble { max-width: 100%; }
            .farm-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
    </style>
</head>
<body>
    <div class="shell">
        <aside class="aside">
            <span class="badge">Fahamu Shamba</span>
            <h1>Shamba Advisor</h1>
            <p>A focused agricultural assistant for Kenyan farmers. Ask about crops, pests, livestock, weather, markets, or upload an image for disease and field advice.</p>
            <div class="hint-list">
                <div class="hint">Ask in English or Kiswahili for planting, fertilizer, market timing, disease signs, and soil questions.</div>
                <div class="hint">Upload one field image to ask about leaf spots, wilting, pests, weeds, crop stress, or livestock visible symptoms.</div>
                <div class="hint">Use <strong>Stop response</strong> if you want to cancel waiting and ask a better follow-up immediately.</div>
            </div>
        </aside>
        <main class="main">
        <div class="header">
            <div>
                <h2>Instant farm support</h2>
                <div class="muted">Agriculture-only answers. Type a question, add a field image, and get focused guidance for Kenya.</div>
            </div>
            <div class="status" id="statusText">Ready for your next question.</div>
        </div>
        <div class="chat" id="chat">
            <div class="row bot">
                <div class="bubble">Karibu. Ask about crops, weather, pests, soil, livestock, or markets in Kenya. You can also upload an image for agriculture-related advice.</div>
            </div>
        </div>
        <div class="typing" id="typing">
            <span class="dots"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>
            <span>Shamba Advisor is preparing guidance...</span>
        </div>
        <div class="composer">
            <div class="preview-bar" id="previewBar">
                <img id="previewImage" alt="Selected farm upload preview" />
                <div class="preview-copy">
                    <strong>Image attached</strong>
                    <div class="muted">Ask about plant disease, pests, soil condition, weeds, or other agriculture-related issues in this image.</div>
                </div>
                <button class="button secondary" id="removeImage" type="button">Remove image</button>
            </div>
            <div class="controls">
                <div class="input-stack">
                    <div class="farm-grid">
                        <label>County
                            <select id="county">
                                <option value="nairobi">Nairobi</option>
                                <option value="nakuru">Nakuru</option>
                                <option value="eldoret">Eldoret</option>
                                <option value="kisumu">Kisumu</option>
                                <option value="kitui">Kitui</option>
                                <option value="kakamega">Kakamega</option>
                                <option value="mombasa">Mombasa</option>
                                <option value="garissa">Garissa</option>
                            </select>
                        </label>
                        <label>Soil type
                            <select id="soilType">
                                <option value="loamy">Loamy</option>
                                <option value="clay">Clay</option>
                                <option value="sandy">Sandy</option>
                                <option value="silty">Silty</option>
                                <option value="peaty">Peaty</option>
                            </select>
                        </label>
                        <label>Soil pH
                            <input id="soilPh" type="number" min="4" max="9" step="0.1" value="6.5" />
                        </label>
                        <label>Land acres
                            <input id="landSize" type="number" min="0.1" step="0.1" value="1.0" />
                        </label>
                        <label>Irrigation
                            <select id="irrigation">
                                <option value="0">No</option>
                                <option value="1">Yes</option>
                            </select>
                        </label>
                    </div>
                    <textarea id="message" maxlength="1000" placeholder="Ask an agriculture question. Example: My tomato leaves have yellow and brown spots. What disease could this be and what should I do?"></textarea>
                    <div class="toolbar">
                        <div class="tool-left">
                            <label class="upload-button" for="imageInput">Upload image</label>
                            <input class="hidden" id="imageInput" type="file" accept="image/*" />
                            <span class="muted" id="helperText">Instant responses for agriculture topics only.</span>
                        </div>
                        <div class="tool-right">
                            <button class="button stop" id="stop" type="button" disabled>Stop response</button>
                            <button class="button primary" id="send" type="button">Send</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        </main>
    </div>
    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('message');
        const send = document.getElementById('send');
        const stop = document.getElementById('stop');
        const typing = document.getElementById('typing');
        const statusText = document.getElementById('statusText');
        const imageInput = document.getElementById('imageInput');
        const previewBar = document.getElementById('previewBar');
        const previewImage = document.getElementById('previewImage');
        const removeImage = document.getElementById('removeImage');
        const helperText = document.getElementById('helperText');
        const countyInput = document.getElementById('county');
        const soilTypeInput = document.getElementById('soilType');
        const soilPhInput = document.getElementById('soilPh');
        const landSizeInput = document.getElementById('landSize');
        const irrigationInput = document.getElementById('irrigation');

        let currentController = null;
        let currentImageData = null;

        function scrollToBottom() {
            chat.scrollTop = chat.scrollHeight;
        }

        function setBusy(isBusy, copy = '') {
            send.disabled = isBusy;
            stop.disabled = !isBusy;
            typing.classList.toggle('active', isBusy);
            statusText.textContent = copy || (isBusy ? 'Responding now...' : 'Ready for your next question.');
        }

        function addMessage(text, type, extra = {}) {
            const row = document.createElement('div');
            row.className = `row ${type}`;

            const bubble = document.createElement('div');
            bubble.className = 'bubble';
            bubble.textContent = text;

            if (extra.image) {
                const preview = document.createElement('div');
                preview.className = 'upload-preview';
                const img = document.createElement('img');
                img.src = extra.image;
                img.alt = 'Uploaded farm image preview';
                preview.appendChild(img);
                bubble.appendChild(preview);
            }

            if (extra.meta) {
                const meta = document.createElement('div');
                meta.className = 'meta';
                meta.textContent = extra.meta;
                bubble.appendChild(meta);
            }

            row.appendChild(bubble);
            chat.appendChild(row);
            scrollToBottom();
        }

        function clearImage() {
            currentImageData = null;
            imageInput.value = '';
            previewImage.removeAttribute('src');
            previewBar.classList.remove('active');
            helperText.textContent = 'Instant responses for agriculture topics only.';
        }

        imageInput.addEventListener('change', () => {
            const [file] = imageInput.files;
            if (!file) {
                clearImage();
                return;
            }
            const reader = new FileReader();
            reader.onload = () => {
                currentImageData = reader.result;
                previewImage.src = currentImageData;
                previewBar.classList.add('active');
                helperText.textContent = 'Image ready. Ask what you want diagnosed or explained.';
            };
            reader.readAsDataURL(file);
        });

        removeImage.addEventListener('click', clearImage);

        stop.addEventListener('click', () => {
            if (currentController) {
                currentController.abort();
                currentController = null;
                setBusy(false, 'Response stopped. You can ask a new question.');
                addMessage('Response stopped. Ask a follow-up when you are ready.', 'bot');
            }
        });

        async function sendMessage() {
            const message = input.value.trim();
            if (!message && !currentImageData) return;

            if (!message && currentImageData) {
                addMessage('Please add a short agriculture question with the image so I know what to analyze.', 'bot');
                return;
            }

            addMessage(message, 'user', { image: currentImageData });
            const payload = {
                message,
                phone_number: 'web_user',
                image_data: currentImageData,
                context: {
                    county: countyInput.value,
                    soil_type: soilTypeInput.value,
                    soil_ph: soilPhInput.value,
                    land_size_acres: landSizeInput.value,
                    irrigation_available: irrigationInput.value
                }
            };

            input.value = '';
            const submittedImage = currentImageData;
            clearImage();
            currentController = new AbortController();
            setBusy(true, submittedImage ? 'Analyzing your image and question...' : 'Preparing your answer...');

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                    signal: currentController.signal
                });

                const data = await response.json();
                const metaParts = [];
                if (typeof data.confidence === 'number') {
                    metaParts.push(`Confidence ${(data.confidence * 100).toFixed(0)}%`);
                }
                if (data.used_image) {
                    metaParts.push('Image reviewed');
                }
                addMessage(data.response || data.error || 'No response available.', 'bot', {
                    meta: metaParts.join(' • ')
                });
                setBusy(false, 'Response ready.');
            } catch (error) {
                if (error.name !== 'AbortError') {
                    addMessage('Sorry, I could not complete that request. Please try again.', 'bot');
                    setBusy(false, 'There was a connection problem.');
                }
            } finally {
                currentController = null;
                if (!stop.disabled) {
                    setBusy(false);
                }
                input.focus();
            }
        }

        send.addEventListener('click', sendMessage);
        input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        });
    </script>
</body>
</html>
        """
    )


@app.route("/chat", methods=["POST"])
def chat():
    try:
        if not rate_limiter.is_allowed(_request_identity()):
            return jsonify({"error": "Rate limit exceeded. Please try again in a minute."}), 429

        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).strip()
        phone_number = data.get("phone_number")
        image_data = data.get("image_data")
        context = dict(data.get("context", {}) or {})
        for key in [
            "county",
            "soil_type",
            "soil_ph",
            "rainfall_mm",
            "temperature_c",
            "humidity_percent",
            "land_size_acres",
            "irrigation_available",
            "fertilizer_use",
        ]:
            if key in data and key not in context:
                context[key] = data.get(key)

        if not message:
            return jsonify({"error": "Message is required"}), 400
        if len(message) > settings.max_message_length:
            return jsonify({"error": f"Message must be {settings.max_message_length} characters or less."}), 400
        if image_data is not None:
            image_data = str(image_data).strip()
            if image_data and not image_data.startswith("data:image/"):
                return jsonify({"error": "Only image uploads are supported."}), 400

        response = chatbot.process_message(message, phone_number, image_data=image_data or None, context=context)
        return jsonify(response)
    except sqlite3.Error as exc:
        logger.error("Database error while processing chat: %s", exc)
        return (
            jsonify(
                {
                    "error": "Database temporarily unavailable",
                    "response": "Sorry, our records service is temporarily unavailable. Please try again shortly.",
                    "confidence": 0.0,
                }
            ),
            503,
        )
    except Exception as exc:
        logger.exception("Unexpected chat error: %s", exc)
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "response": "Sorry, I encountered an error. Please try again.",
                    "confidence": 0.0,
                }
            ),
            500,
        )


@app.route("/profile", methods=["POST"])
def update_profile():
    auth_error = _require_service_api_key()
    if auth_error:
        return auth_error

    try:
        data = request.get_json(silent=True) or {}
        phone_number = str(data.get("phone_number", "")).strip()
        if not phone_number:
            return jsonify({"error": "Phone number is required"}), 400

        profile = {
            "name": data.get("name"),
            "county": data.get("county"),
            "land_size_acres": data.get("land_size_acres"),
            "main_crops": data.get("main_crops"),
            "farming_experience": data.get("farming_experience"),
            "language_preference": data.get("language_preference", "en"),
        }
        chatbot.save_farmer_profile(phone_number, profile)
        return jsonify({"success": True, "message": "Profile updated successfully"})
    except sqlite3.Error as exc:
        logger.error("Profile update database error: %s", exc)
        return jsonify({"error": "Failed to update profile"}), 503


@app.route("/profile/<phone_number>", methods=["GET"])
def get_profile(phone_number: str):
    auth_error = _require_service_api_key()
    if auth_error:
        return auth_error

    try:
        profile = chatbot.get_farmer_profile(phone_number)
        return jsonify(profile)
    except sqlite3.Error as exc:
        logger.error("Profile fetch database error: %s", exc)
        return jsonify({"error": "Failed to get profile"}), 503


@app.route("/recommend-crops", methods=["POST"])
def recommend_crops():
    try:
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "Recommend the best crop to plant now")).strip()
        phone_number = data.get("phone_number")
        context = dict(data.get("context", {}) or {})
        for key in [
            "county",
            "soil_type",
            "soil_ph",
            "rainfall_mm",
            "temperature_c",
            "humidity_percent",
            "land_size_acres",
            "irrigation_available",
            "fertilizer_use",
        ]:
            if key in data and key not in context:
                context[key] = data.get(key)
        farmer_profile = chatbot.get_farmer_profile(phone_number) if phone_number else {}
        response = chatbot.get_crop_recommendation_response(message, farmer_profile, context=context)
        return jsonify(response)
    except Exception as exc:
        logger.exception("Recommendation error: %s", exc)
        return jsonify({"error": "Failed to generate crop recommendations"}), 500


@app.route("/debug-llm", methods=["GET"])
def debug_llm():
    """Test the LLM connection directly."""
    api_key = settings.openai_api_key
    is_groq = api_key.startswith("gsk_")
    api_url = "https://api.groq.com/openai/v1/chat/completions" if is_groq else "https://api.openai.com/v1/chat/completions"
    model = "llama3-8b-8192" if is_groq else settings.openai_model
    try:
        resp = requests.post(
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
            "response_body": resp.json() if resp.ok else resp.text,
        })
    except Exception as exc:
        return jsonify({"error": str(exc), "provider": "groq" if is_groq else "openai"}), 500


@app.route("/health", methods=["GET"])
def health():
    report = chatbot.readiness_report()
    return jsonify(
        {
            "status": "ok",
            "service": "farmer_chatbot",
            "timestamp": datetime.now().isoformat(),
            **report,
        }
    )


@app.route("/health/ready", methods=["GET"])
def readiness():
    report = chatbot.readiness_report()
    status_code = 200 if report["database_ok"] else 503
    return jsonify(report), status_code


if __name__ == "__main__":
    print("FAHAMU SHAMBA - FARMER CHATBOT")
    print("=" * 50)
    port = int(os.getenv("PORT", "5002"))
    print(f"Starting on http://localhost:{port}")
    if not settings.openai_configured:
        print("WARNING: OPENAI_API_KEY is missing. The service will use fallback answers.")
    if settings.production_mode and not settings.production_config_ok:
        print("WARNING: Production mode is enabled but one or more required secrets are placeholders or missing.")
    app.run(debug=settings.debug, host="0.0.0.0", port=port)
