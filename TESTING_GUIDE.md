# 🧪 FAHAMU SHAMBA - COMPLETE TESTING & RETESTING GUIDE

## 📋 TABLE OF CONTENTS
1. [System Cleanup](#system-cleanup)
2. [Start All Services](#start-all-services)
3. [Local Testing](#local-testing)
4. [External Testing Setup](#external-testing-setup)
5. [Africa's Talking Testing](#africas-talking-testing)
6. [Twilio Testing](#twilio-testing)
7. [Troubleshooting](#troubleshooting)

---

## 🗑️ SYSTEM CLEANUP

### ✅ **Removed Unnecessary Files:**
- `add_health_endpoints.py` ❌
- `demo.py` ❌
- `models.py` ❌
- `quick_start.py` ❌
- `start_all.py` ❌
- `start_all_fixed.py` ❌
- `start_all_services.py` ❌
- `start_services.bat` ❌
- `fixed_start.bat` ❌
- `enhanced_start.bat` ❌
- `final_start.bat` ❌
- `recommendation_engine.py` ❌
- `crop_recommendation_model.pkl` ❌
- `chatbot.py` ❌

### ✅ **Essential Files Remaining:**
- `enhanced_recommendation_engine.py` ✅
- `enhanced_chatbot.py` ✅
- `ussd_sms_integration.py` ✅
- `ivr_system.py` ✅
- `feedback_system.py` ✅
- `simple_mobile.py` ✅
- `mobile_app.py` ✅
- `test_services.py` ✅
- `test_ussd.py` ✅
- `test_ivr.py` ✅

---

## 🚀 STEP 1: START ALL SERVICES

### **Run the Clean Startup Script:**
```bash
start_fahamu_shamba.bat
```

### **Expected Output:**
```
🌾 FAHAMU SHAMBA - AGRICULTURAL ADVISORY PLATFORM
📱 Starting Mobile App (Port 5003)...
💬 Starting Enhanced Chatbot (Port 5002)...
📱 Starting USSD Service (Port 5000)...
📞 Starting IVR System (Port 5001)...
📊 Starting Feedback System (Port 5004)...

✅ Mobile App: RUNNING
✅ Enhanced Chatbot: RUNNING
✅ USSD Service: RUNNING
✅ IVR System: RUNNING
✅ Feedback System: RUNNING
```

---

## 🧪 STEP 2: LOCAL TESTING

### **Test All Services Locally:**

#### **Option A: Test Dashboard**
```bash
python test_services.py
```
Then open: http://localhost:5005

#### **Option B: Individual Tests**
```bash
# Test USSD Service
python test_ussd.py

# Test IVR Service  
python test_ivr.py
```

#### **Option C: Manual Browser Tests**
- **Mobile App:** http://localhost:5003
- **Chatbot:** http://localhost:5002
- **Health Checks:**
  - USSD: http://localhost:5000/health
  - IVR: http://localhost:5001/health
  - Feedback: http://localhost:5004/health

### **Expected Local Test Results:**
```
✅ USSD Service Status: 200
Response: CON Karibu Fahamu Shamba!...

✅ IVR Service Status: 200  
Response: <?xml version="1.0" encoding="UTF-8"?><Response>...
```

---

## 🌐 STEP 3: EXTERNAL TESTING SETUP

### **Start ngrok for External Access:**

#### **Terminal 1: USSD Service**
```bash
ngrok http 5000
```

#### **Terminal 2: IVR Service**
```bash
ngrok http 5001
```

### **Copy Your ngrok URLs:**
```
USSD: https://abc123.ngrok.io
IVR:  https://def456.ngrok.io
```

---

## 📱 STEP 4: AFRICA'S TALKING CONFIGURATION

### **Login to Africa's Talking:**
1. **URL:** https://account.africastalking.com/
2. **Username:** `Sandbox`
3. **Password:** Your sandbox password

### **Configure USSD Service:**
1. **Navigate:** USSD → Your USSD Service
2. **Service Name:** `Fahamu Shamba`
3. **USSD Code:** `*384*96#`
4. **Callback URL:** `https://YOUR_NGROK_URL.ngrok.io/ussd`
5. **Response Type:** `JSON`
6. **Country:** `Kenya`
7. **Click:** Save

### **Configure SMS Service:**
1. **Navigate:** SMS → SMS Configuration
2. **Callback URL:** `https://YOUR_NGROK_URL.ngrok.io/sms`
3. **Default Response:** `Enabled`
4. **Click:** Save

---

## 📞 STEP 5: TWILIO CONFIGURATION

### **Login to Twilio:**
1. **URL:** https://console.twilio.com/
2. **Account SID:** `<your_twilio_account_sid>`
3. **Auth Token:** `<your_twilio_auth_token>`

### **Configure Phone Number:**
1. **Navigate:** Phone Numbers → Active Numbers
2. **Click on:** `<your_twilio_phone_number>`

#### **Voice Configuration:**
- **A CALL COMES IN:** `Webhook`
- **Webhook URL:** `https://YOUR_NGROK_URL.ngrok.io/ivr/incoming`
- **HTTP Method:** `POST`

#### **Messaging Configuration:**
- **A MESSAGE COMES IN:** `Webhook`
- **Webhook URL:** `https://YOUR_NGROK_URL.ngrok.io/sms`
- **HTTP Method:** `POST`

3. **Click:** Save

---

## 🧪 STEP 6: AFRICA'S TALKING TESTING

### **🔍 ISSUE: SIMULATION WORKS BUT PHONE DOESN'T**

This is a common Africa's Talking sandbox issue. Here's how to fix it:

#### **Solution 1: Use Kenya Phone Number**
1. **In Africa's Talking Console:** Go to Account → Settings
2. **Add your Kenya phone number** (with +254 prefix)
3. **Verify the number** via SMS code
4. **Test again** with your verified Kenya number

#### **Solution 2: Check Sandbox Credits**
1. **Go to:** Account → Billing
2. **Ensure you have sandbox credits**
3. **Top up if needed** (free for testing)

#### **Solution 3: Correct USSD Code**
1. **Use:** `*384*96#` (Kenya sandbox code)
2. **Don't use:** Custom codes in sandbox

#### **Solution 4: Test with Different Network**
1. **Try different network** (Safaricom, Airtel, Telkom)
2. **Some networks have sandbox restrictions**

### **Testing Steps:**

#### **Step 1: Test Webhook Directly**
```bash
curl -X POST https://YOUR_NGROK_URL.ngrok.io/ussd \
  -d "sessionId=TEST123&phoneNumber=+254712345678&text=&networkCode=63902"
```

#### **Step 2: Test with Online Simulator**
1. **Go to:** Africa's Talking USSD Simulator
2. **Enter:** `*384*96#`
3. **Click:** Simulate

#### **Step 3: Test with Real Phone**
1. **Dial:** `*384*96#` from your Kenya phone
2. **Expected:**
   ```
   *384*96#
   → Karibu Fahamu Shamba!
   → 1. Kiswahili  2. English
   
   Press 1
   → 1. Pendekezo la mazao
   → 2. Hali ya hewa
   → 3. Bei za soko
   ```

---

## 📞 STEP 7: TWILIO TESTING

### **Testing Options:**

#### **Option 1: Free Console Testing (Recommended)**
1. **Go to:** Twilio Console → Phone Numbers → Active Numbers
2. **Click on:** `<your_twilio_phone_number>`
3. **Find:** "Make a call to this number" section
4. **Enter your phone number**
5. **Click:** "Call"
6. **Answer when it rings**

#### **Option 2: Real Call Testing**
1. **Call:** `<your_twilio_phone_number>` from any phone
2. **Cost:** ~$0.01/minute from trial balance
3. **Trial balance:** Usually $15+ (plenty for testing)

### **Expected IVR Flow:**
```
Call <your_twilio_phone_number>
→ "Karibu Fahamu Shamba. Bonyeza moja kwa Kiswahili. Bonyeza mbili kwa Kiingereza."

Press 2 (English)
→ "Welcome to Fahamu Shamba. Press one for crop recommendations..."

Press 1
→ "Please enter your county code..."
```

---

## 🔧 STEP 8: TROUBLESHOOTING

### **If Africa's Talking Doesn't Work on Phone:**

#### **Check 1: Phone Number Verification**
- ✅ Phone number added to Africa's Talking account
- ✅ Number verified via SMS
- ✅ Using Kenya phone number (+254...)

#### **Check 2: Sandbox Settings**
- ✅ Using correct USSD code: `*384*96#`
- ✅ Sandbox credits available
- ✅ Webhook URL correct: `https://xxx.ngrok.io/ussd`

#### **Check 3: Network Issues**
- ✅ Try different network (Safaricom preferred)
- ✅ Check network coverage
- ✅ Try different time of day

#### **Check 4: Account Status**
- ✅ Account is in sandbox mode
- ✅ USSD service is active
- ✅ No account restrictions

### **If Twilio Doesn't Work:**

#### **Check 1: Webhook Configuration**
- ✅ URL: `https://xxx.ngrok.io/ivr/incoming`
- ✅ Method: `POST`
- ✅ ngrok running on port 5001

#### **Check 2: ngrok Status**
- ✅ ngrok shows active connections
- ✅ HTTPS URL working
- ✅ Port forwarding correct

#### **Check 3: Service Status**
- ✅ IVR service running on port 5001
- ✅ Health check: `http://localhost:5001/health`
- ✅ No errors in service logs

---

## ✅ SUCCESS VERIFICATION

### **Local Tests Should Pass:**
- [ ] All services start without errors
- [ ] Health checks return 200 OK
- [ ] Test scripts pass successfully
- [ ] Mobile app loads correctly
- [ ] Chatbot responds properly

### **External Tests Should Pass:**
- [ ] Africa's Talking simulator works
- [ ] Africa's Talking real phone works
- [ ] Twilio console call works
- [ ] Twilio real call works
- [ ] SMS confirmations sent

### **End-to-End Workflow:**
- [ ] USSD → Recommendation → SMS confirmation
- [ ] IVR → Voice menu → SMS summary
- [ ] Feedback collection → Analytics
- [ ] All channels integrated

---

## 🎯 FINAL TESTING CHECKLIST

### **Before Testing:**
- [ ] Run `start_fahamu_shamba.bat`
- [ ] Verify all services running
- [ ] Start ngrok on ports 5000 & 5001
- [ ] Configure webhooks with ngrok URLs

### **During Testing:**
- [ ] Test local services first
- [ ] Test webhooks directly
- [ ] Test with simulators
- [ ] Test with real phones

### **After Testing:**
- [ ] Check ngrok logs for requests
- [ ] Verify SMS confirmations sent
- [ ] Test feedback collection
- [ ] Document any issues

---

## 🚀 READY FOR PRODUCTION!

When all tests pass:
1. ✅ **System is clean and optimized**
2. ✅ **All services working perfectly**
3. ✅ **External integration functional**
4. ✅ **Real phone testing successful**
5. ✅ **End-to-end workflow verified**

**Your Fahamu Shamba platform is ready for real farmers!** 🌾
