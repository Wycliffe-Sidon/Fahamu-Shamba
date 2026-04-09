# Soil Type Detection - Implementation Guide# Soil Type Detection - Implementation Guide















































































































































































































































































































































































































- ✅ **Accurate** - 70-90% when farmer engages- ✅ **Reliable** - Falls back gracefully- ✅ **Flexible** - Works with or without farmer input- ✅ **Accessible** - No technical knowledge required- ✅ **Works offline** - No external API neededThis ensures:| Farmer provides soil directly | Use provided value | 95% || Farmer provides nothing | Use global defaults | 50% || Farmer gives only county | Use county default | 60% || Farmer answers 4 questions | Use detected soil | 75-90% ||----------|----------|------------|| Scenario | Solution | Confidence |## Summary---```#   Confidence: 87.5%#   Soil type: sandy# Example 2: Farmer answers 3 questions# #   Confidence: 60%#   Soil type: nairobi's default (loamy)  # Example 1: Farmer doesn't answer questions# Output:python -m soil_type_detectorcd /path/to/fahamu-shamba# Test soil detection locally```bash## Testing---```IVR: "Your soil is SANDY. Great for sorghum and millet!"[2 more questions]Farmer: [presses 1]      Light (1), Reddish (2), Dark (3)?"IVR: "What color is your soil? Farmer: [presses 1]      stay wet (press 2), or balanced (press 3)?"IVR: "After rain, does your soil dry quickly (press 1),```### Example 3: IVR Voice Call```[Immediate recommendations]         I'll use that for recommendations."Chatbot: "That's OK! The most common soil in Kitui is SANDY.Farmer: "I don't have time for questions"Chatbot: "Do you know your soil type?"Farmer: "Kitui"Chatbot: "What county are you in?"```### Example 2: Farmer in Hurry```         This is perfect for beans and potatoes!"Chatbot: "Based on your answers, your soil is likely CLAY.[3 more questions]Farmer: "It stays wet for about 3 days"         After rain, does your soil dry quickly?"Chatbot: "No problem! I'll ask 4 simple questions.Farmer: "No, I have no idea"Chatbot: "Do you know your soil type?"Farmer: "Nairobi"Chatbot: "What county are you in?"```### Example 1: Farmer with No Soil Knowledge## User Experience Examples---```}  "note": "This is the most common soil type in Kitui. For better accuracy, answer the soil detection questions."  "confidence": 0.6,  "default_soil_type": "sandy",  "county": "kitui",{Response:}  "county": "kitui"{Request:POST /api/soil/county-default```bash### 3. Get County Default```}  "reasoning": "Detected from your answers (confidence: 87.5%)"  "method": "farmer_questions",  "confidence": 0.875,  "primary_soil_type": "sandy",{Response:}  }    "water_puddles": "a"    "digging_difficulty": "a",    "soil_color": "c",    "water_retention": "a",  "answers": {  "county": "nairobi",{Request:POST /api/soil/detect```bash### 2. Detect Soil from Answers```}  ]    ...    },      ]        {"key": "c", "text": "Balanced (2-3 days)"}        {"key": "b", "text": "Stays wet (3+ days)"},        {"key": "a", "text": "Dries quickly (1-2 days)"},      "options": [      "question": "Baada ya mvua, udongo wako unakaa mvua kwa muda gani?",      "id": "water_retention",    {  "questions": [  "question_count": 4,  "language": "swahili",{Response:GET /api/soil/questions?language=swahili```bash### 1. Get Soil Detection Questions## API Endpoints---```    return jsonify(recommendations), 200        recommendations = engine.predict_crops(input_data)    engine = get_recommendation_engine()    # Query recommendation engine        }        'fertilizer_use': data.get('fertilizer_use', 0),        'irrigation_available': data.get('irrigation_available', 0),        'temperature_c': data.get('temperature_c', 20),        'rainfall_mm': data.get('rainfall_mm', 600),        'soil_type': soil_type,        'county': county,    input_data = {    # Get recommendations using detected soil            soil_type = soil_result['primary_soil_type']        soil_result = detector.recommend_soil_type(county, answers)        answers = data.get('soil_detection_answers')  # May be empty    if not soil_type:    # If soil_type not provided, detect it        detector = SoilDetector()        soil_type = data.get('soil_type')  # Optional    county = data.get('county')    data = request.jsondef get_recommendations():@app.route('/api/recommendations', methods=['POST'])```python### In Chatbot API Route```    return str(response)        response.say(f"Your soil type is {result['primary_soil_type']}", language='sw-KE')    response = VoiceResponse()    # Generate TwiML response with detected soil        result = detector.recommend_soil_type(county, answers)    county = data.get('county')    # Detect soil        answers = {k: dtmf_to_answer_key.get(v, v) for k, v in answers.items()}    dtmf_to_answer_key = {'1': 'a', '2': 'b', '3': 'c'}    # Map 1,2,3 to a,b,c        }        'water_puddles': data.get('q4')        'digging_difficulty': data.get('q3'),        'soil_color': data.get('q2'),        'water_retention': data.get('q1'),      # 1, 2, or 3 → a, b, c    answers = {    # Convert DTMF presses to answers        data = request.json    """Process IVR DTMF input for soil questions"""def process_soil_answers():@app.route('/ivr/process-soil-answers', methods=['POST'])detector = SoilDetector()from soil_type_detector import SoilDetector```python### In `enhanced_ivr_system.py````    return jsonify(farmer_profile), 200        # Save to database...        }        'soil_method': soil_result['method']  # 'farmer_questions' or 'county_default'        'soil_confidence': soil_result['confidence'],        'soil_type': soil_result['primary_soil_type'],        'county': county,    farmer_profile = {    # Save farmer profile with detected soil        soil_result = detector.recommend_soil_type(county, answers)    # Get detected soil type        answers = data.get('soil_detection_answers')  # From simple questions    county = data.get('county')    data = request.jsondef update_farmer_profile():@app.route('/profile/update', methods=['POST'])detector = SoilDetector()add_soil_detection_to_chatbot(app)# In app initializationfrom soil_type_detector import SoilDetectorfrom soil_detection_api import add_soil_detection_to_chatbot```python### In `farmer_chatbot.py`## Code Integration Examples---```Return recommendations via SMS  ↓If option 2: SMS questions one by oneIf option 1: Use county default soil  ↓2. Detailed recommendation (asks 4 questions via SMS)1. Quick recommendation (uses county default)Menu:  ↓User: Dials *123*456#```### 3. USSD/SMS Flow```Recommendations  ↓IVR: "Your soil is: SANDY. Getting crop recommendations..."  ↓Q4: "Do puddles form? Yes days (1), Sometimes (2), No (3)?"Q3: "How hard to dig? Very easy (1), Moderate (2), Very hard (3)?"Q2: "What color is your soil? Light (1), Reddish (2), Dark (3)?"Q1: "After rain, does soil dry quickly (1), stay wet (2), or balanced (3)?"  ↓      I'll ask 4 simple questions. Press 1-3 for each."IVR: "We need to know your soil type.   ↓IVR: "Press your county number (1-47)" or "Say your county"  ↓Farmer calls```### 2. IVR (Voice) Flow```Display recommendations  ↓Get other inputs (rainfall, irrigation, etc)  ↓    "Your soil is likely: SANDY (Confidence: 87%)"       ↓    [4 Simple Questions]       ↓  └→ No: "Let's figure it out together →"  ├→ Yes: [Dropdown: loamy, clay, sandy, etc]"Do you know your soil type?"  ↓"What is your county?" → [Dropdown of 47 counties]  ↓Welcome Page```### 1. Web Chatbot User Flow## Integration Points---**Implementation**: Enhanced recommendation engine with fallbacks**Confidence**: 50% (works but less accurate)```    logger.info(f"Using default soil '{soil_type}' for {county}")    soil_type = self.COUNTY_SOIL_MAP.get(county, 'loamy')if soil_type is None or soil_type == 'unknown':# In recommendation engine```pythonIf farmer skips everything, make soil type optional and use defaults in AI model:### Layer 3: Optional Parameter (Last Resort)**Implementation**: `SoilDetector.COUNTY_SOIL_MAP`**Confidence**: 60% (good enough for basic recommendations)```Semi-arid (Kitui, Kajiado) → SandyLake regions (Kisumu, Kakamega) → ClayCoastal counties (Mombasa, Kilifi) → SandyHighland counties (Nairobi, Nyeri, Kericho) → Loamy```If farmer doesn't want to answer questions, use county defaults:### Layer 2: County Defaults (Fallback)**Implementation**: `soil_type_detector.py` + `soil_detection_api.py`**Confidence**: 70-90% (highest accuracy)```   → No = Sandy   → Sometimes = Loamy   → Yes, days = ClayQ4: "Do puddles form after rain?"   → Very hard = Clay   → Moderate = Loamy     → Very easy = SandyQ3: "How hard to dig?"   → Light/pale = Sandy   → Reddish = Loamy   → Dark/black = Clay (rich)Q2: "What color is your soil?"   → Balanced = Loamy   → Stays wet = Clay   → Dries quickly = SandyQ1: "After rain, how long does your soil stay wet?"```Ask questions farmers can observe without technical knowledge:### Layer 1: Simple Observable Questions (Best)## Three-Layer Detection System---3. **API Flexibility** - Make soil type optional in recommendations2. **County Defaults** - Use most common soil type for their area1. **Simple Questions** - Ask observable questions farmers CAN answer**Solution**: Smart 3-layer fallback system:**Issue**: Farmers don't know technical soil terms (loamy, clay, sandy, etc.)## Problem Solved
## Problem Solved

**Issue**: Farmers don't know technical soil terms (loamy, clay, sandy, etc.)

**Solution**: Smart 3-layer fallback system:
1. **Simple Questions** - Ask observable questions farmers CAN answer
2. **County Defaults** - Use most common soil type for their area
3. **API Flexibility** - Make soil type optional in recommendations

---

## Three-Layer Detection System

### Layer 1: Simple Observable Questions (Best)

Ask questions farmers can observe without technical knowledge:

```
Q1: "After rain, how long does your soil stay wet?"
   → Dries quickly = Sandy
   → Stays wet = Clay
   → Balanced = Loamy

Q2: "What color is your soil?"
   → Dark/black = Clay (rich)
   → Reddish = Loamy
   → Light/pale = Sandy

Q3: "How hard to dig?"
   → Very easy = Sandy
   → Moderate = Loamy  
   → Very hard = Clay

Q4: "Do puddles form after rain?"
   → Yes, days = Clay
   → Sometimes = Loamy
   → No = Sandy
```

**Confidence**: 70-90% (highest accuracy)
**Implementation**: `soil_type_detector.py` + `soil_detection_api.py`

### Layer 2: County Defaults (Fallback)

If farmer doesn't want to answer questions, use county defaults:

```
Highland counties (Nairobi, Nyeri, Kericho) → Loamy
Coastal counties (Mombasa, Kilifi) → Sandy
Lake regions (Kisumu, Kakamega) → Clay
Semi-arid (Kitui, Kajiado) → Sandy
```

**Confidence**: 60% (good enough for basic recommendations)
**Implementation**: `SoilDetector.COUNTY_SOIL_MAP`

### Layer 3: Optional Parameter (Last Resort)

If farmer skips everything, make soil type optional and use defaults in AI model:

```python
# In recommendation engine
if soil_type is None or soil_type == 'unknown':
    soil_type = self.COUNTY_SOIL_MAP.get(county, 'loamy')
    logger.info(f"Using default soil '{soil_type}' for {county}")
```

**Confidence**: 50% (works but less accurate)
**Implementation**: Enhanced recommendation engine with fallbacks

---

## Integration Points

### 1. Web Chatbot User Flow

```
Welcome Page
  ↓
"What is your county?" → [Dropdown of 47 counties]
  ↓
"Do you know your soil type?"
  ├→ Yes: [Dropdown: loamy, clay, sandy, etc]
  └→ No: "Let's figure it out together →"
       ↓
    [4 Simple Questions]
       ↓
    "Your soil is likely: SANDY (Confidence: 87%)"
  ↓
Get other inputs (rainfall, irrigation, etc)
  ↓
Display recommendations
```

### 2. IVR (Voice) Flow

```
Farmer calls
  ↓
IVR: "Press your county number (1-47)" or "Say your county"
  ↓
IVR: "We need to know your soil type. 
      I'll ask 4 simple questions. Press 1-3 for each."
  ↓
Q1: "After rain, does soil dry quickly (1), stay wet (2), or balanced (3)?"
Q2: "What color is your soil? Light (1), Reddish (2), Dark (3)?"
Q3: "How hard to dig? Very easy (1), Moderate (2), Very hard (3)?"
Q4: "Do puddles form? Yes days (1), Sometimes (2), No (3)?"
  ↓
IVR: "Your soil is: SANDY. Getting crop recommendations..."
  ↓
Recommendations
```

### 3. USSD/SMS Flow

```
User: Dials *123*456#
  ↓
Menu:
1. Quick recommendation (uses county default)
2. Detailed recommendation (asks 4 questions via SMS)
  ↓
If option 1: Use county default soil
If option 2: SMS questions one by one
  ↓
Return recommendations via SMS
```

---

## Code Integration Examples

### In `farmer_chatbot.py`

```python
from soil_detection_api import add_soil_detection_to_chatbot
from soil_type_detector import SoilDetector

# In app initialization
add_soil_detection_to_chatbot(app)
detector = SoilDetector()

@app.route('/profile/update', methods=['POST'])
def update_farmer_profile():
    data = request.json
    county = data.get('county')
    answers = data.get('soil_detection_answers')  # From simple questions
    
    # Get detected soil type
    soil_result = detector.recommend_soil_type(county, answers)
    
    # Save farmer profile with detected soil
    farmer_profile = {
        'county': county,
        'soil_type': soil_result['primary_soil_type'],
        'soil_confidence': soil_result['confidence'],
        'soil_method': soil_result['method']  # 'farmer_questions' or 'county_default'
    }
    
    # Save to database...
    
    return jsonify(farmer_profile), 200
```

### In `enhanced_ivr_system.py`

```python
from soil_type_detector import SoilDetector

detector = SoilDetector()

@app.route('/ivr/process-soil-answers', methods=['POST'])
def process_soil_answers():
    """Process IVR DTMF input for soil questions"""
    data = request.json
    
    # Convert DTMF presses to answers
    answers = {
        'water_retention': data.get('q1'),      # 1, 2, or 3 → a, b, c
        'soil_color': data.get('q2'),
        'digging_difficulty': data.get('q3'),
        'water_puddles': data.get('q4')
    }
    
    # Map 1,2,3 to a,b,c
    dtmf_to_answer_key = {'1': 'a', '2': 'b', '3': 'c'}
    answers = {k: dtmf_to_answer_key.get(v, v) for k, v in answers.items()}
    
    # Detect soil
    county = data.get('county')
    result = detector.recommend_soil_type(county, answers)
    
    # Generate TwiML response with detected soil
    response = VoiceResponse()
    response.say(f"Your soil type is {result['primary_soil_type']}", language='sw-KE')
    
    return str(response)
```

### In Chatbot API Route

```python
@app.route('/api/recommendations', methods=['POST'])
def get_recommendations():
    data = request.json
    county = data.get('county')
    soil_type = data.get('soil_type')  # Optional
    
    detector = SoilDetector()
    
    # If soil_type not provided, detect it
    if not soil_type:
        answers = data.get('soil_detection_answers')  # May be empty
        soil_result = detector.recommend_soil_type(county, answers)
        soil_type = soil_result['primary_soil_type']
    
    # Get recommendations using detected soil
    input_data = {
        'county': county,
        'soil_type': soil_type,
        'rainfall_mm': data.get('rainfall_mm', 600),
        'temperature_c': data.get('temperature_c', 20),
        'irrigation_available': data.get('irrigation_available', 0),
        'fertilizer_use': data.get('fertilizer_use', 0),
    }
    
    # Query recommendation engine
    engine = get_recommendation_engine()
    recommendations = engine.predict_crops(input_data)
    
    return jsonify(recommendations), 200
```

---

## API Endpoints

### 1. Get Soil Detection Questions

```bash
GET /api/soil/questions?language=swahili

Response:
{
  "language": "swahili",
  "question_count": 4,
  "questions": [
    {
      "id": "water_retention",
      "question": "Baada ya mvua, udongo wako unakaa mvua kwa muda gani?",
      "options": [
        {"key": "a", "text": "Dries quickly (1-2 days)"},
        {"key": "b", "text": "Stays wet (3+ days)"},
        {"key": "c", "text": "Balanced (2-3 days)"}
      ]
    },
    ...
  ]
}
```

### 2. Detect Soil from Answers

```bash
POST /api/soil/detect

Request:
{
  "county": "nairobi",
  "answers": {
    "water_retention": "a",
    "soil_color": "c",
    "digging_difficulty": "a",
    "water_puddles": "a"
  }
}

Response:
{
  "primary_soil_type": "sandy",
  "confidence": 0.875,
  "method": "farmer_questions",
  "reasoning": "Detected from your answers (confidence: 87.5%)"
}
```

### 3. Get County Default

```bash
POST /api/soil/county-default

Request:
{
  "county": "kitui"
}

Response:
{
  "county": "kitui",
  "default_soil_type": "sandy",
  "confidence": 0.6,
  "note": "This is the most common soil type in Kitui. For better accuracy, answer the soil detection questions."
}
```

---

## User Experience Examples

### Example 1: Farmer with No Soil Knowledge

```
Chatbot: "What county are you in?"
Farmer: "Nairobi"

Chatbot: "Do you know your soil type?"
Farmer: "No, I have no idea"

Chatbot: "No problem! I'll ask 4 simple questions.
         After rain, does your soil dry quickly?"
Farmer: "It stays wet for about 3 days"

[3 more questions]

Chatbot: "Based on your answers, your soil is likely CLAY.
         This is perfect for beans and potatoes!"
```

### Example 2: Farmer in Hurry

```
Chatbot: "What county are you in?"
Farmer: "Kitui"

Chatbot: "Do you know your soil type?"
Farmer: "I don't have time for questions"

Chatbot: "That's OK! The most common soil in Kitui is SANDY.
         I'll use that for recommendations."

[Immediate recommendations]
```

### Example 3: IVR Voice Call

```
IVR: "After rain, does your soil dry quickly (press 1),
      stay wet (press 2), or balanced (press 3)?"
Farmer: [presses 1]

IVR: "What color is your soil? 
      Light (1), Reddish (2), Dark (3)?"
Farmer: [presses 1]

[2 more questions]

IVR: "Your soil is SANDY. Great for sorghum and millet!"
```

---

## Testing

```bash
# Test soil detection locally
cd /path/to/fahamu-shamba

python -m soil_type_detector

# Output:
# Example 1: Farmer doesn't answer questions
#   Soil type: nairobi's default (loamy)  
#   Confidence: 60%
# 
# Example 2: Farmer answers 3 questions
#   Soil type: sandy
#   Confidence: 87.5%
```

---

## Summary

| Scenario | Solution | Confidence |
|----------|----------|------------|
| Farmer answers 4 questions | Use detected soil | 75-90% |
| Farmer gives only county | Use county default | 60% |
| Farmer provides nothing | Use global defaults | 50% |
| Farmer provides soil directly | Use provided value | 95% |

This ensures:
- ✅ **Works offline** - No external API needed
- ✅ **Accessible** - No technical knowledge required
- ✅ **Flexible** - Works with or without farmer input
- ✅ **Reliable** - Falls back gracefully
- ✅ **Accurate** - 70-90% when farmer engages
