#!/usr/bin/env python3
"""
Fahamu Shamba - Soil Detection API Integration
Flask endpoints for soil type detection with smart fallbacks
"""

from flask import Blueprint, request, jsonify
from soil_type_detector import SoilDetector
import logging

logger = logging.getLogger(__name__)

soil_bp = Blueprint('soil', __name__, url_prefix='/api/soil')
detector = SoilDetector()

@soil_bp.route('/detect', methods=['POST'])
def detect_soil():
    """
    Detect soil type from farmer input
    
    Request:
    {
        "county": "nairobi",
        "answers": {
            "water_retention": "a",
            "soil_color": "c",
            "digging_difficulty": "a"
        }
    }
    
    Response:
    {
        "primary_soil_type": "sandy",
        "confidence": 0.85,
        "method": "farmer_questions",
        "reasoning": "Detected from your answers (confidence: 85%)"
    }
    """
    
    data = request.json or {}
    county = data.get('county', '').strip()
    answers = data.get('answers', {})
    
    if not county:
        return jsonify({'error': 'County is required'}), 400
    
    # Get soil recommendation
    result = detector.recommend_soil_type(county, answers if answers else None)
    
    logger.info(f"Soil detection for {county}: {result['primary_soil_type']} "
                f"({result['confidence']*100:.0f}% confidence via {result['method']})")
    
    return jsonify(result), 200

@soil_bp.route('/questions', methods=['GET'])
def get_soil_questions():
    """
    Get soil detection questions
    
    Query params:
        language: 'english' or 'swahili' (default: english)
    
    Response:
    {
        "questions": [
            {
                "id": "water_retention",
                "question": "After rain, how long does your soil stay wet?",
                "options": [
                    {"key": "a", "text": "Dries quickly (1-2 days)"},
                    {"key": "b", "text": "Stays wet (3+ days)"},
                    {"key": "c", "text": "Balanced (2-3 days)"}
                ]
            },
            ...
        ]
    }
    """
    
    language = request.args.get('language', 'english').lower()
    if language not in ['english', 'swahili']:
        language = 'english'
    
    questions = detector.get_simple_questions(language)
    
    return jsonify({
        'language': language,
        'question_count': len(questions),
        'questions': questions
    }), 200

@soil_bp.route('/county-default', methods=['POST'])
def county_default():
    """
    Get default soil type for a county (no questions needed)
    
    Request:
    {
        "county": "nairobi"
    }
    
    Response:
    {
        "county": "nairobi",
        "default_soil_type": "loamy",
        "confidence": 0.6,
        "note": "This is the most common soil type for this county"
    }
    """
    
    data = request.json or {}
    county = data.get('county', '').strip()
    
    if not county:
        return jsonify({'error': 'County is required'}), 400
    
    soil_type = detector.detect_from_county(county)
    
    return jsonify({
        'county': county,
        'default_soil_type': soil_type,
        'confidence': 0.6,
        'note': f'This is the most common soil type in {county.title()}. '
                'For better accuracy, answer the soil detection questions.'
    }), 200

# Integration with existing farmer_chatbot.py
def add_soil_detection_to_chatbot(app):
    """
    Add soil detection endpoints to Flask app
    
    Usage:
        from farmer_chatbot import app
        from soil_detection_api import add_soil_detection_to_chatbot
        add_soil_detection_to_chatbot(app)
    """
    app.register_blueprint(soil_bp)
    logger.info("Soil detection API endpoints registered:")
    logger.info("  POST /api/soil/detect - Detect soil with answers")
    logger.info("  GET /api/soil/questions - Get detection questions")
    logger.info("  POST /api/soil/county-default - Get county default")

# Integrate with recommendation engine
def get_recommendation_with_soil_detection(county: str, answers=None, other_params=None):
    """
    Get crop recommendations with smart soil detection
    
    Args:
        county: Farmer's county
        answers: Dict of soil detection question answers (optional)
        other_params: Dict of other parameters (rainfall, temperature, etc)
    
    Returns:
        Dict with recommendations
    """
    
    # Detect soil type
    soil_result = detector.recommend_soil_type(county, answers)
    soil_type = soil_result['primary_soil_type']
    
    # Prepare input for recommendation engine
    input_data = {
        'county': county,
        'soil_type': soil_type,
    }
    
    # Add other parameters if provided
    if other_params:
        input_data.update(other_params)
    
    # Get recommendations (assuming you have recommendation engine)
    # recommendations = recommendation_engine.predict_crops(input_data)
    
    return {
        'soil_detection': soil_result,
        'input_data': input_data,
        # 'recommendations': recommendations  # Add when integrated
    }

if __name__ == '__main__':
    from flask import Flask
    
    app = Flask(__name__)
    add_soil_detection_to_chatbot(app)
    
    # Test endpoint
    with app.test_client() as client:
        print("Testing soil detection API...")
        
        # Test 1: Get questions
        print("\n1. Get soil detection questions:")
        resp = client.get('/api/soil/questions?language=english')
        print(f"   Status: {resp.status_code}")
        print(f"   Questions: {resp.json['question_count']}")
        
        # Test 2: County default
        print("\n2. Get county default soil type:")
        resp = client.post('/api/soil/county-default', 
                          json={'county': 'nairobi'})
        print(f"   Status: {resp.status_code}")
        print(f"   Soil type: {resp.json['default_soil_type']}")
        
        # Test 3: Detect with answers
        print("\n3. Detect soil from farmer answers:")
        resp = client.post('/api/soil/detect',
                          json={
                              'county': 'kitui',
                              'answers': {
                                  'water_retention': 'a',
                                  'soil_color': 'c',
                                  'digging_difficulty': 'a'
                              }
                          })
        print(f"   Status: {resp.status_code}")
        print(f"   Detected: {resp.json['primary_soil_type']}")
        print(f"   Method: {resp.json['method']}")
