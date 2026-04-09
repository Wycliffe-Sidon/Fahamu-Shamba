# Fahamu Shamba - Render Deployment Guide

## Overview
This guide explains how to deploy Fahamu Shamba to Render with proper AI model and database persistence.

## Key Changes for Production

### 1. **Database Persistence**
- **Local Development**: SQLite (easy, no setup)
- **Render Production**: PostgreSQL (persistent across restarts)
- The app automatically detects and uses the correct database via `DATABASE_URL`

### 2. **AI Model Persistence**
- Model is trained during the **build phase** (not runtime)
- Stored in `/app/data` directory (persistent disk)
- If model file is missing, chatbot auto-trains a bootstrap model (fallback)

### 3. **File Structure**
```
/app/
  ├── data/                    # Persistent disk (Render)
  │   └── enhanced_crop_recommendation_model.pkl
  ├── fahamu_shamba.db         # SQLite (local only)
  └── source code files
```

## Deployment Steps

### Step 1: Push Code to GitHub
```bash
git init
git add .
git commit -m "Initial commit for Render deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fahamu-shamba.git
git push -u origin main
```

### Step 2: Create Render Services

#### Option A: Use render.yaml (Recommended)
```bash
# Connect your GitHub repo to Render
# Render automatically reads render.yaml and creates all services
```

#### Option B: Manual Setup in Render Dashboard
1. **Create PostgreSQL Database**
   - Go to Render Dashboard > New > Database
   - Name: `fahamu-db`
   - PostgreSQL 14
   - Copy the connection string

2. **Create Web Services** (for each service: chatbot, IVR, integration, etc.)
   - Environment: Python
   - Build Command: `./build.sh`
   - Start Command: `gunicorn -b 0.0.0.0:$PORT farmer_chatbot:app`
   - Environment Variables:
     ```
     FLASK_ENV=production
     DEBUG=false
     DATABASE_URL=<paste PostgreSQL connection string>
     PYTHONUNBUFFERED=true
     ```
   - Attach persistent disk:
     - Mount Path: `/app/data`
     - Size: 5 GB

### Step 3: Set Environment Variables
Required variables in Render Dashboard:

```
OPENAI_API_KEY=sk_... (if using GPT)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
AFRICASTALKING_API_KEY=...
AFRICASTALKING_USERNAME=...
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
DEBUG=false
```

## Accessing Your Deployed Services

After deployment, services are accessible at:

- **Chatbot**: `https://fahamu-chatbot.onrender.com`
- **IVR System**: `https://fahamu-ivr.onrender.com`
- **Integration Service**: `https://fahamu-integration.onrender.com`
- **USSD Service**: `https://fahamu-ussd.onrender.com`

### User Access

#### 1. **Via Twilio IVR (Voice)**
- Call the Twilio number connected to your IVR service
- Navigate menus to get crop recommendations
- IVR system routes to the chatbot backend

#### 2. **Via USSD (SMS)**
- Dial `*123*456#` (your USSD code)
- Get instant recommendations via SMS

#### 3. **Via Web Chatbot**
- Visit the chatbot URL
- Type questions to get recommendations
- Chat history is stored in PostgreSQL

#### 4. **Via API Integration**
```bash
curl https://fahamu-integration.onrender.com/api/recommendations \
  -H "Content-Type: application/json" \
  -d '{
    "county": "nairobi",
    "rainfall_mm": 800,
    "temperature_c": 18,
    "soil_ph": 6.5
  }'
```

## Model Training Details

### Training Pipeline (ai_model_training_pipeline.py)
- **Algorithm**: Random Forest + Gradient Boosting (chooses best)
- **Training Data**: 10,000 synthetic historical records
- **Features**: Weather (rainfall, temp, humidity) + Soil (pH, moisture, nutrients) + Farm (size, irrigation, fertilizer)
- **Output**: Crop recommendations with confidence scores
- **Accuracy**: ~75-85% on test set

### Automatic Bootstrap Training
If the main model file is missing:
1. Chatbot detects missing model on first request
2. Generates 400 sample training records
3. Trains lightweight bootstrap model
4. Saves for future use
5. **This takes ~5-10 seconds on first request**

## Monitoring & Troubleshooting

### Check Service Health
```bash
# Chatbot health
curl https://fahamu-chatbot.onrender.com/health

# IVR health
curl https://fahamu-ivr.onrender.com/health
```

### View Logs
- Render Dashboard > Web Service > Logs
- Look for `✅` (success) or `❌` (error) indicators

### Common Issues

#### Issue: "Model file not found"
- **Cause**: Model training failed during build
- **Solution**: 
  - Check build logs in Render
  - Model will be auto-trained on first request (slower)

#### Issue: "Database connection error"
- **Cause**: DATABASE_URL not set
- **Solution**: 
  - Set DATABASE_URL env var to PostgreSQL connection string
  - Or restart service to trigger rebuild

#### Issue: Service slow on first request
- **Cause**: Bootstrap model training (if main model missing)
- **Solution**: Be patient, subsequent requests are fast

## Best Practices

1. **Keep Secrets Secure**
   - Never commit API keys to GitHub
   - Use Render environment variables
   - Use `.env.example` for reference

2. **Monitor Usage**
   - Check database size monthly
   - Clean up old chat history if needed
   - Monitor API quota for Twilio/AfricasTalking

3. **Update Model Regularly**
   - Re-deploy to trigger model retraining
   - Add new training data as you get farmer feedback
   - A/B test different models

## Scale Your Deployment

- **Add more services**: Add sections to `render.yaml`
- **Increase disk space**: Modify `sizeGB` in render.yaml
- **Upgrade database**: Render Dashboard > Database > Change Plan
- **Load balancing**: Upgrade services to Pro plan

## Support

- **Render Docs**: https://render.com/docs
- **Twilio Docs**: https://www.twilio.com/docs
- **Flask Docs**: https://flask.palletsprojects.com

---

**Last Updated**: April 2026
