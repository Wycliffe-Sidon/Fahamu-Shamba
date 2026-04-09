# Fahamu Shamba Deployment Guide

## 1. Render deployment

1. Push this project to GitHub.
2. In Render, create a new `Web Service` from the repository.
3. Confirm:
   - Build command: `./build.sh`
   - Start command: `gunicorn -b 0.0.0.0:$PORT app:app`
4. Add these environment variables:
   - `FLASK_ENV=production`
   - `DEBUG=false`
   - `SECRET_KEY=<strong-random-secret>`
   - `FAHAMU_API_KEY=<internal-api-key>`
   - `OPENAI_API_KEY=<your-openai-key>`
   - `OPENAI_MODEL=gpt-4o-mini`
   - `DB_PATH=/app/data/fahamu_shamba.db`
   - `MODEL_DATA_DIR=/app/data`
   - `MODEL_PATH=/app/data/enhanced_crop_recommendation_model.pkl`
   - `TRAINING_DATA_PATH=/app/data/fahamu_shamba_training_data.csv`
   - `TWILIO_ACCOUNT_SID=<twilio-sid>`
   - `TWILIO_AUTH_TOKEN=<twilio-auth-token>`
   - `TWILIO_PHONE_NUMBER=<twilio-number>`
   - `AFRICASTALKING_USERNAME=<at-username>`
   - `AFRICASTALKING_API_KEY=<at-api-key>`
   - `OPENWEATHER_API_KEY=<openweather-key>`
   - `USE_MOCK_DATA=false`
5. Add a persistent disk mounted at `/app/data`.
6. Deploy and confirm:
   - `/health`
   - `/deployment/summary`
   - `/chat`
   - `/ussd`
   - `/ivr/incoming`

## 2. Twilio IVR and SMS

Use Twilio for voice IVR and optionally SMS.

### Voice / IVR

1. Buy or connect a Twilio voice-capable number.
2. In the Twilio number settings, set the incoming voice webhook to:
   - `https://<your-render-domain>/ivr/incoming`
   - Method: `POST`
3. Save the number configuration.
4. Call the number and verify:
   - Language selection works
   - Menu options work
   - AI speech question flow works

### SMS

1. In the same Twilio number settings, set the messaging webhook to:
   - `https://<your-render-domain>/sms/inbound/twilio`
   - Method: `POST`
2. Send an SMS to the number and confirm the chatbot replies.

## 3. Africa's Talking USSD and SMS

Use Africa's Talking for USSD and optionally SMS.

### USSD

1. In the Africa's Talking dashboard, create or activate a USSD service code.
2. Set the USSD callback URL to:
   - `https://<your-render-domain>/ussd`
3. If available for your code, set the USSD events URL to a logging endpoint you control.
4. Test the menu flow in the Africa's Talking simulator first.
5. After sandbox validation, move the code live and keep the same callback URL.

### SMS

1. Configure the inbound SMS callback URL to:
   - `https://<your-render-domain>/sms/inbound/africastalking`
2. For outbound SMS from the app, call:
   - `POST /sms/send`
   - JSON body: `{"phone":"+2547XXXXXXXX","message":"...", "provider":"africastalking"}`

## 4. Recommended production checks

1. Open `https://<your-render-domain>/health` and confirm status is `ok`.
2. Open `https://<your-render-domain>/deployment/summary` and confirm all channels show `true`.
3. Test web chat with a crop recommendation query.
4. Test USSD registration, weather, market prices, and AI question flow.
5. Test Twilio IVR and SMS.
6. Submit farmer feedback to `/feedback` and confirm analytics at `/feedback/analytics`.

## 5. Important note on USSD providers

This codebase supports:

- Twilio: IVR and SMS
- Africa's Talking: USSD and SMS

For deployment planning, use Africa's Talking as the primary USSD provider for Kenya.
