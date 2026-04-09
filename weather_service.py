"""
Fahamu Shamba - Weather Service
Fetches real weather data from OpenWeatherMap API.
Falls back to mock data when USE_MOCK_DATA=true or API call fails.
"""

import os
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Kenya county approximate coordinates
COUNTY_COORDS = {
    'nairobi':   (-1.2921, 36.8219),
    'mombasa':   (-4.0435, 39.6682),
    'kisumu':    (-0.1022, 34.7617),
    'nakuru':    (-0.3031, 36.0800),
    'eldoret':   (0.5143,  35.2698),
    'thika':     (-1.0332, 37.0693),
    'nyeri':     (-0.4167, 36.9500),
    'meru':      (0.0467,  37.6490),
    'kakamega':  (0.2827,  34.7519),
    'garissa':   (-0.4532, 39.6461),
    'default':   (-1.2921, 36.8219),  # Nairobi as fallback
}

MOCK_WEATHER = {
    'temperature': 22.0,
    'humidity': 65,
    'rainfall_mm': 450,
    'description': 'Partly cloudy',
    'wind_speed': 3.5,
    'source': 'mock',
}


def get_weather(county: str = 'nairobi') -> dict:
    """
    Fetch current weather for a Kenya county.
    Returns real data if OPENWEATHER_API_KEY is set and USE_MOCK_DATA=false,
    otherwise returns mock data.
    """
    use_mock = os.getenv('USE_MOCK_DATA', 'true').lower() == 'true'
    api_key  = os.getenv('OPENWEATHER_API_KEY', '')

    if use_mock or not api_key or api_key == 'your_openweather_api_key':
        logger.info(f"[MOCK WEATHER] Returning mock data for {county}")
        return {**MOCK_WEATHER, 'county': county}

    lat, lon = COUNTY_COORDS.get(county.lower(), COUNTY_COORDS['default'])
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    )

    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return {
            'county':      county,
            'temperature': data['main']['temp'],
            'humidity':    data['main']['humidity'],
            'rainfall_mm': data.get('rain', {}).get('1h', 0) * 30,  # scale to monthly estimate
            'description': data['weather'][0]['description'].title(),
            'wind_speed':  data['wind']['speed'],
            'source':      'openweathermap',
        }
    except Exception as e:
        logger.warning(f"Weather API failed ({e}), using mock data")
        return {**MOCK_WEATHER, 'county': county}


def weather_summary(county: str, lang: str = 'en') -> str:
    """Return a human-readable weather summary string."""
    w = get_weather(county)
    if lang == 'sw':
        return (
            f"Hali ya hewa - {county.title()}:\n"
            f"Joto: {w['temperature']}°C\n"
            f"Unyevu: {w['humidity']}%\n"
            f"Mvua (makadirio): {w['rainfall_mm']:.0f}mm\n"
            f"Hali: {w['description']}"
        )
    return (
        f"Weather - {county.title()}:\n"
        f"Temp: {w['temperature']}°C\n"
        f"Humidity: {w['humidity']}%\n"
        f"Rainfall (est): {w['rainfall_mm']:.0f}mm\n"
        f"Conditions: {w['description']}"
    )


if __name__ == '__main__':
    for county in ['nairobi', 'mombasa', 'kisumu']:
        print(weather_summary(county, 'en'))
        print()
