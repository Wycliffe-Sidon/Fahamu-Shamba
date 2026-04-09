# ✅ Fahamu Shamba - Deployment Checklist for Render

Complete this checklist before and during deployment.

## Pre-Deployment (Local Testing)

- [ ] **Code Review**
  - [ ] All Python syntax is correct
  - [ ] No placeholder values in code
  - [ ] No hardcoded credentials

- [ ] **Local Testing**
  - [ ] `python ai_model_training_pipeline.py` runs successfully
  - [ ] `python -m pytest` passes (if tests exist)
  - [ ] `docker compose build` completes without errors
  - [ ] `docker compose up` starts all services

- [ ] **Environment Setup**
  - [ ] `.env` file exists with real values (KEEP PRIVATE)
  - [ ] `.env.example` has placeholder values only
  - [ ] `.gitignore` includes `.env`

- [ ] **Git Repository**
  - [ ] Code committed to GitHub
  - [ ] No `.env` file in git
  - [ ] `build.sh` has execute permissions: `chmod +x build.sh`
  - [ ] All required files present

## Render Setup (Dashboard)

### Database
- [ ] **Create PostgreSQL Database**
  - [ ] Go to Render Dashboard > New > Database
  - [ ] Name: `fahamu-db`
  - [ ] PostgreSQL 14
  - [ ] Tier: Standard (or higher)
  - [ ] Copy connection string for later

### Web Services

For each service (chatbot, ivr, integration, realtime, feedback, ussd):

- [ ] **Create Web Service**
  - [ ] Environment: Python 3.11
  - [ ] Build Command: `./build.sh`
  - [ ] Start Command: `gunicorn -b 0.0.0.0:$PORT <app>:<app_name>`
  - [ ] Region: Frankfurt (or closest to Kenya)
  - [ ] Tier: Standard (min)

- [ ] **Set Environment Variables**
  ```
  FLASK_ENV=production
  DEBUG=false
  LOG_LEVEL=INFO
  DATABASE_URL=<paste PostgreSQL connection>
  PYTHONUNBUFFERED=true
  OPENAI_API_KEY=<from .env>
  TWILIO_ACCOUNT_SID=<from .env>
  TWILIO_AUTH_TOKEN=<from .env>
  TWILIO_PHONE_NUMBER=<from .env>
  AFRICASTALKING_USERNAME=<from .env>
  AFRICASTALKING_API_KEY=<from .env>
  SECRET_KEY=<from .env>
  ```

- [ ] **Attach Persistent Disk** (for model storage)
  - [ ] Mount Path: `/app/data`
  - [ ] Size: 5 GB
  - [ ] Apply

- [ ] **Set Dependency Order** (if applicable)
  - [ ] IVR depends on Chatbot
  - [ ] Integration depends on Chatbot

### Service URLs

After deployment, note the URLs:

- [ ] Chatbot: `https://fahamu-chatbot.onrender.com`
- [ ] IVR: `https://fahamu-ivr.onrender.com`
- [ ] Integration: `https://fahamu-integration.onrender.com`
- [ ] Realtime: `https://fahamu-realtime.onrender.com`
- [ ] USSD: `https://fahamu-ussd.onrender.com`
- [ ] Feedback: `https://fahamu-feedback.onrender.com`

## Twilio Configuration

- [ ] **Incoming Call Webhook**
  - [ ] Phone Number Settings
  - [ ] A Call Comes In: `https://fahamu-ivr.onrender.com/ivr/incoming`
  - [ ] Save

- [ ] **Test Voice Call**
  - [ ] Call the Twilio number
  - [ ] Should hear IVR greeting
  - [ ] Able to select options

## Africa's Talking Configuration

- [ ] **Incoming SMS Webhook**
  - [ ] Go to Applications > your app > Messaging
  - [ ] Callback URL: `https://fahamu-ussd.onrender.com/ussd`
  - [ ] Save

- [ ] **Test USSD**
  - [ ] Dial code (from .env)
  - [ ] Should receive menu via SMS

## Post-Deployment Testing

### Health Checks
- [ ] `curl https://fahamu-chatbot.onrender.com/health` → 200 OK
- [ ] `curl https://fahamu-ivr.onrender.com/health` → 200 OK
- [ ] Check other service URLs

### Voice Test (Twilio IVR)
- [ ] Place test phone call
- [ ] Hear greeting in English/Swahili
- [ ] Navigate menu (press 1-3)
- [ ] Get crop recommendations
- [ ] Conversation recorded in database

### SMS Test (Africa's Talking USSD)
- [ ] Dial USSD code
- [ ] Receive menu via SMS
- [ ] Reply with option
- [ ] Get recommendations
- [ ] Message logged in database

### Web Chatbot Test
- [ ] Visit `https://fahamu-chatbot.onrender.com`
- [ ] Enter farmer details
- [ ] Submit form
- [ ] Receive top 5 crop recommendations
- [ ] See confidence scores and reasoning

### API Test
```bash
curl -X POST https://fahamu-integration.onrender.com/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "county": "nairobi",
    "rainfall_mm": 800,
    "temperature_c": 18,
    "soil_ph": 6.5,
    "irrigation_available": 1
  }'
```
- [ ] Returns 200 OK
- [ ] Includes crop recommendations
- [ ] Has confidence scores

### Database Test
- [ ] Check chat history in PostgreSQL
- [ ] Verify farmer profiles are saved
- [ ] Check USSD/Voice session logs

## Logging & Monitoring

- [ ] **View Logs**
  - [ ] Render Dashboard > Web Service > Logs
  - [ ] Look for `✅` (success) or `❌` (errors)
  - [ ] Check build.sh model training output

- [ ] **Check Model Status**
  - [ ] Logs show "Model loaded" or "Model trained"
  - [ ] If "bootstrap model", training took ~5-10 sec

- [ ] **Monitor Resources**
  - [ ] CPU usage < 50%
  - [ ] Memory usage < 500MB
  - [ ] Disk usage < 2GB

## Production Maintenance

### Weekly
- [ ] Check Render logs for errors
- [ ] Monitor database size
- [ ] Review API usage/limits

### Monthly
- [ ] Backup chat history (export from PostgreSQL)
- [ ] Review user feedback
- [ ] Consider model retraining

### Quarterly
- [ ] Add new training data from farmer feedback
- [ ] Retrain AI model (redeploy)
- [ ] Update service URLs in Twilio/AT if changed

## Emergency Procedures

### Service Crashes
1. [ ] Check Render logs for error
2. [ ] Restart service (Render Dashboard > Restart)
3. [ ] If persistent, check environment variables

### Model Won't Load
1. [ ] Check build.sh output in logs
2. [ ] Verify `/app/data` disk is attached
3. [ ] System will bootstrap fallback model (slower)

### Database Connection Issues
1. [ ] Verify DATABASE_URL env var is set
2. [ ] Check PostgreSQL is running (Render Dashboard)
3. [ ] Restart all web services

### Out of Memory
1. [ ] Restart service
2. [ ] Upgrade Render plan to Standard or higher
3. [ ] Clear old chat history

## Success Indicators

✅ **You're ready if:**
- [ ] All services deployed and showing "Live"
- [ ] Health checks return 200 OK
- [ ] Voice calls work (IVR responds)
- [ ] USSD works (menu via SMS)
- [ ] Web chatbot works (recommendations display)
- [ ] API endpoint works (returns JSON)
- [ ] Database has chat history
- [ ] Logs show no critical errors
- [ ] Model loaded successfully

## Documentation

- [ ] Keep `RENDER_DEPLOYMENT.md` updated
- [ ] Keep `IVR_CHATBOT_ACCESS_GUIDE.md` for reference
- [ ] Update `.env.example` with new variables
- [ ] Document any custom changes

## Security Checklist

- [ ] `.env` is in `.gitignore` (never commit secrets)
- [ ] API keys rotated before public launch
- [ ] HTTPS enforced (Render default)
- [ ] Rate limiting enabled (in .env)
- [ ] Database backups configured (Render auto-backups)
- [ ] Logs don't contain sensitive data

## Budgeting

Before going live, estimate Render costs:

- [ ] PostgreSQL database: ~$7/month
- [ ] 6 web services @ Standard: ~$42/month (7x6)
- [ ] Persistent storage (5GB each): included in plan
- [ ] **Total**: ~$50/month (varies by usage)

---

**Last Updated**: April 8, 2026
**Deploy Date**: _______________
**Notes**: ___________________
