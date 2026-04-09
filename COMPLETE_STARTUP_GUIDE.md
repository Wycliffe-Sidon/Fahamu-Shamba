# FAHAMU SHAMBA - STARTUP AND DEPLOYMENT GUIDE

## Current Services

The currently supported core services are:

1. `farmer_chatbot.py`
   Runs the main chatbot API on port `5002`

2. `chatbot_integration_service.py`
   Runs the channel integration API on port `5006`

## Before You Start

1. Activate the virtual environment:

```powershell
cd C:\Users\Kipruto\Desktop\FAHAMU-SHAMBA
.\fahamu_env\Scripts\activate
```

2. Confirm required environment values in `.env`:

```env
OPENAI_API_KEY=...
SECRET_KEY=...
FAHAMU_API_KEY=...
ALLOWED_ORIGINS=...
```

3. Install dependencies if needed:

```powershell
python -m pip install -r requirements.txt
```

## Local Startup

Open two terminals.

Terminal 1:

```powershell
cd C:\Users\Kipruto\Desktop\FAHAMU-SHAMBA
.\fahamu_env\Scripts\activate
python farmer_chatbot.py
```

Terminal 2:

```powershell
cd C:\Users\Kipruto\Desktop\FAHAMU-SHAMBA
.\fahamu_env\Scripts\activate
python chatbot_integration_service.py
```

## Health Checks

After startup, verify these endpoints:

1. Main chatbot:

```powershell
curl http://localhost:5002/health
curl http://localhost:5002/health/ready
```

2. Integration service:

```powershell
curl http://localhost:5006/health
```

Expected result:

- `5002/health` returns `200`
- `5002/health/ready` returns `200`
- `5006/health` returns `200` only when the chatbot service is already running

## Production Run Commands

Use a real process manager in production. Example commands:

```powershell
gunicorn -b 0.0.0.0:5002 farmer_chatbot:app
gunicorn -b 0.0.0.0:5006 chatbot_integration_service:app
```

## Production Checklist

1. Replace all placeholder values in `.env`
2. Rotate provider credentials before go-live
3. Set `ALLOWED_ORIGINS` to your real frontend domain
4. Keep `.env` out of source control
5. Put both services behind HTTPS and a reverse proxy
6. Confirm Twilio and Africa's Talking webhooks point to public HTTPS URLs, not localhost
7. Run:

```powershell
python -m unittest test_farmer_chatbot.py test_chatbot_integration.py
```

## Notes

- The older guide commands such as `python chatbot.py`, `quick_start.py`, and `start_services.bat` are not the current supported startup path for the validated chatbot stack.
- If you want the wider IVR, USSD, mobile, and feedback services productionized too, those should be verified separately.
