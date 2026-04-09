#!/usr/bin/env python3
"""
Fahamu Shamba - Smart Soil Type Detection
Helps farmers identify soil type even if they don't know technical terms
"""

from enum import Enum
from typing import Dict, Optional

class SoilType(Enum):
    LOAMY = "loamy"
    CLAY = "clay"
    SANDY = "sandy"
    SILTY = "silty"
    PEATY = "peaty"

class SoilDetector:
    """Intelligent soil type detection without technical knowledge"""
    
    # County to common soil type mapping
    COUNTY_SOIL_MAP = {
        # Highland counties (loamy/clay)
        'nairobi': 'loamy', 'nyeri': 'loamy', 'kirinyaga': 'loamy',
        'muranga': 'loamy', 'kiambu': 'loamy', 'nakuru': 'loamy',
        'kericho': 'loamy', 'bomet': 'loamy', 'kimwarer': 'loamy',
        'nandi': 'loamy', 'uasin_gishu': 'loamy', 'trans_nzoia': 'loamy',
        
        # Coastal counties (sandy)
        'mombasa': 'sandy', 'kwale': 'sandy', 'kilifi': 'sandy',
        'tana_river': 'sandy', 'lamu': 'sandy', 'taita_taveta': 'sandy',
        
        # Lake/wet regions (clay)
        'kisumu': 'clay', 'homabay': 'clay', 'migori': 'clay',
        'nyamira': 'clay', 'kisii': 'clay', 'kakamega': 'clay',
        'vihiga': 'clay', 'bungoma': 'clay', 'busia': 'clay',
        'siaya': 'clay',
        
        # Semi-arid (sandy/loamy)
        'kitui': 'sandy', 'makueni': 'sandy', 'machakos': 'sandy',
        'kajiado': 'sandy', 'narok': 'sandy', 'laikipia': 'loamy',
        
        # Arid (sandy)
        'garissa': 'sandy', 'wajir': 'sandy', 'mandera': 'sandy',
        'isiolo': 'sandy', 'marsabit': 'sandy', 'turkana': 'sandy',
        'samburu': 'sandy',
        
        # Other
        'elgeyo_marakwet': 'loamy', 'baringo': 'loamy', 'west_pokot': 'loamy',
    }
    
    def __init__(self):
        self.simple_questions = [
            {
                'id': 'water_retention',
                'question': 'After rain, how long does your soil stay wet?',
                'english': 'After rain, how long does your soil stay wet?',
                'swahili': 'Baada ya mvua, udongo wako unakaa mvua kwa muda gani?',
                'options': {
                    'a': {'text': 'Dries quickly (1-2 days)', 'soil_type': 'sandy', 'score': 1},
                    'b': {'text': 'Stays wet (3+ days)', 'soil_type': 'clay', 'score': 3},
                    'c': {'text': 'Balanced (2-3 days)', 'soil_type': 'loamy', 'score': 2},
                }
            },
            {
                'id': 'soil_color',
                'question': 'What color is your soil?',
                'english': 'What color is your soil?',
                'swahili': 'Udongo wako una rangi gani?',
                'options': {
                    'a': {'text': 'Dark brown/black', 'soil_type': 'clay', 'score': 3},
                    'b': {'text': 'Reddish brown', 'soil_type': 'loamy', 'score': 2},
                    'c': {'text': 'Light/pale yellow', 'soil_type': 'sandy', 'score': 1},
                    'd': {'text': 'Don\'t know', 'soil_type': None, 'score': 0},
                }
            },
            {
                'id': 'digging_difficulty',
                'question': 'How hard is it to dig your soil with a shovel?',
                'english': 'How hard is it to dig your soil with a shovel?',
                'swahili': 'Je, ni ngumu kiasi gani kuchua udongo wako kwa koleo?',
                'options': {
                    'a': {'text': 'Very easy', 'soil_type': 'sandy', 'score': 1},
                    'b': {'text': 'Easily breakable but compact', 'soil_type': 'loamy', 'score': 2},
                    'c': {'text': 'Very hard/compact', 'soil_type': 'clay', 'score': 3},
                }
            },
            {
                'id': 'water_puddles',
                'question': 'Do water puddles form on your land after rain?',
                'english': 'Do water puddles form on your land after rain?',
                'swahili': 'Je, kumekuwa na madimbwi ya maji mahali ulipo baada ya mvua?',
                'options': {
                    'a': {'text': 'Yes, they stay for days', 'soil_type': 'clay', 'score': 3},
                    'b': {'text': 'Sometimes, disappear quickly', 'soil_type': 'loamy', 'score': 2},
                    'c': {'text': 'No, water drains immediately', 'soil_type': 'sandy', 'score': 1},
                }
            },
        ]
    
    def detect_from_county(self, county: str) -> str:
        """Get most common soil type for a county"""
        county_lower = county.lower().replace(' ', '_')
        return self.COUNTY_SOIL_MAP.get(county_lower, 'loamy')  # Default to loamy
    
    def detect_from_answers(self, answers: Dict[str, str]) -> tuple[str, float]:
        """
        Detect soil type from simple questions
        Returns: (soil_type, confidence_0_to_1)
        """
        if not answers:
            return None, 0.0
        
        scores = {
            'sandy': 0,
            'loamy': 0,
            'clay': 0,
            'silty': 0,
            'peaty': 0,
        }
        
        total_responses = 0
        
        # Score each response
        for question_id, answer_key in answers.items():
            question = next((q for q in self.simple_questions if q['id'] == question_id), None)
            if not question:
                continue
            
            option = question['options'].get(answer_key)
            if not option or not option['soil_type']:
                continue
            
            soil_type = option['soil_type']
            score = option['score']
            
            scores[soil_type] += score
            total_responses += 1
        
        if total_responses == 0:
            return None, 0.0
        
        # Find highest scoring soil type
        best_soil = max(scores.items(), key=lambda x: x[1])[0]
        confidence = scores[best_soil] / (total_responses * 3)  # Max score is 3 per Q
        
        return best_soil, min(confidence, 1.0)
    
    def recommend_soil_type(self, county: str, answers: Optional[Dict[str, str]] = None) -> Dict:
        """
        Smart soil detection combining county + answers
        """
        
        # Start with county default
        county_default = self.detect_from_county(county)
        
        recommendation = {
            'primary_soil_type': county_default,
            'confidence': 0.6,  # County default has 60% confidence
            'method': 'county_default',
            'reasoning': f"Most common soil type in {county.title()}"
        }
        
        # If farmer answered questions, use those
        if answers and len(answers) > 0:
            detected_soil, confidence = self.detect_from_answers(answers)
            
            if detected_soil and confidence > 0.4:
                recommendation.update({
                    'primary_soil_type': detected_soil,
                    'confidence': confidence,
                    'method': 'farmer_questions',
                    'reasoning': f"Detected from your answers (confidence: {confidence*100:.0f}%)"
                })
        
        return recommendation
    
    def get_simple_questions(self, language: str = 'english') -> list:
        """Get soil detection questions in specified language"""
        questions = []
        
        for q in self.simple_questions:
            question_text = q.get(language, q['english'])
            
            formatted_q = {
                'id': q['id'],
                'question': question_text,
                'options': []
            }
            
            for opt_key, opt_val in q['options'].items():
                formatted_q['options'].append({
                    'key': opt_key,
                    'text': opt_val['text']
                })
            
            questions.append(formatted_q)
        
        return questions

# Integration example for Flask app
def create_soil_detection_form(language: str = 'english'):
    """Create HTML form for soil detection"""
    detector = SoilDetector()
    questions = detector.get_simple_questions(language)
    
    html = f"""
    <form id="soil-detection-form">
        <h3>🌱 Help Us Understand Your Soil</h3>
        <p>We'll ask {len(questions)} simple questions to identify your soil type.</p>
    """
    
    for q in questions:
        html += f'<div class="question">\n'
        html += f'  <label><strong>{q["question"]}</strong></label>\n'
        html += f'  <div class="options">\n'
        
        for opt in q['options']:
            html += f'    <label><input type="radio" name="{q["id"]}" value="{opt["key"]}"> {opt["text"]}</label>\n'
        
        html += f'  </div>\n</div>\n'
    
    html += """
    </form>
    <button onclick="submitSoilForm()" class="btn btn-primary">Detect My Soil Type</button>
    <script>
    function submitSoilForm() {
        const formData = new FormData(document.getElementById('soil-detection-form'));
        const answers = Object.fromEntries(formData);
        
        // Send to backend
        fetch('/api/detect-soil', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({county: getCounty(), answers: answers})
        })
        .then(r => r.json())
        .then(data => {
            document.getElementById('soil-result').innerHTML = 
                `Your soil type: <strong>${data.primary_soil_type}</strong> 
                (Confidence: ${(data.confidence*100).toFixed(0)}%)`;
        });
    }
    </script>
    """
    
    return html

if __name__ == '__main__':
    detector = SoilDetector()
    
    # Example: Farmer from Nairobi doesn't answer questions
    print("Example 1: Farmer doesn't answer questions")
    result = detector.recommend_soil_type('nairobi')
    print(f"  Soil type: {result['primary_soil_type']}")
    print(f"  Confidence: {result['confidence']*100:.0f}%")
    print(f"  Method: {result['method']}\n")
    
    # Example: Farmer answers questions
    print("Example 2: Farmer answers 3 questions")
    answers = {
        'water_retention': 'a',  # Dries quickly
        'soil_color': 'c',       # Light/pale
        'digging_difficulty': 'a'  # Very easy
    }
    result = detector.recommend_soil_type('kitui', answers)
    print(f"  Soil type: {result['primary_soil_type']}")
    print(f"  Confidence: {result['confidence']*100:.0f}%")
    print(f"  Method: {result['method']}")
    print(f"  Reasoning: {result['reasoning']}")
