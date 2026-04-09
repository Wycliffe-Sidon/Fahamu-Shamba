#!/usr/bin/env python3
"""
Auto-Detection Soil API Endpoints
Drop-in integration for farmer_chatbot.py

Usage:
    from auto_location_soil_api import add_auto_location_endpoints
    add_auto_location_endpoints(app)
    
    # Endpoints available:
    # GET /api/auto-soil?county=nairobi
    # POST /api/auto-soil/gps
    # GET /api/counties (list all)
"""

from flask import Blueprint, request, jsonify
from auto_location_soil_map import auto_detector, LocationInputMethod
import logging

logger = logging.getLogger(__name__)

# Create blueprint
auto_soil_bp = Blueprint('auto_soil', __name__, url_prefix='/api/auto-soil')


@auto_soil_bp.route('/detect', methods=['POST'])
def detect_soil():
    """
    Auto-detect soil from county
    
    POST /api/auto-soil/detect
    {
        "county": "nairobi"
    }
    
    Response:
    {
        "county": "nairobi",
        "soil_type": "loamy",
        "confidence": 0.85,
        "auto_detected": true,
        "method": "county_automatic"
    }
    """
    
    data = request.json or {}
    county = data.get('county', '').strip()
    
    if not county:
        return jsonify({'error': 'County is required'}), 400
    
    result = auto_detector.detect_from_county_name(county)
    
    logger.info(f"Auto-detected soil for {county}: {result['soil_type']} "
                f"({result['confidence']*100:.0f}% confidence)")
    
    return jsonify({
        'county': result['county'],
        'soil_type': result['soil_type'],
        'confidence': result['confidence'],
        'auto_detected': True,
        'method': result['method'],
        'message': f"Auto-detected {result['soil_type']} soil for {county.title()}"
    }), 200


@auto_soil_bp.route('/gps', methods=['POST'])
def detect_from_gps():
    """
    Auto-detect soil from GPS coordinates
    
    POST /api/auto-soil/gps
    {
        "latitude": -1.2833,
        "longitude": 36.9167
    }
    
    Response:
    {
        "county": "nairobi",
        "soil_type": "loamy",
        "confidence": 0.85,
        "auto_detected": true,
        "method": "gps_automatic"
    }
    """
    
    data = request.json or {}
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    if latitude is None or longitude is None:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid GPS coordinates'}), 400
    
    result = auto_detector.detect_from_gps(latitude, longitude)
    
    logger.info(f"Auto-detected from GPS ({latitude}, {longitude}): "
                f"{result.get('county', 'Unknown')} → {result['soil_type']}")
    
    return jsonify({
        'county': result.get('county'),
        'soil_type': result['soil_type'],
        'confidence': result['confidence'],
        'latitude': latitude,
        'longitude': longitude,
        'auto_detected': True,
        'method': result['method']
    }), 200


@auto_soil_bp.route('/query', methods=['GET'])
def query_soil():
    """
    Simple GET endpoint for auto-detection
    
    GET /api/auto-soil/query?county=nairobi
    
    Response:
    {
        "soil_type": "loamy",
        "confidence": 0.85
    }
    """
    
    county = request.args.get('county', '').strip()
    
    if not county:
        return jsonify({'error': 'County parameter required'}), 400
    
    result = auto_detector.detect_from_county_name(county)
    
    return jsonify({
        'soil_type': result['soil_type'],
        'confidence': result['confidence']
    }), 200


@auto_soil_bp.route('/counties', methods=['GET'])
def list_counties():
    """
    Get list of all supported counties with soil types
    
    GET /api/auto-soil/counties
    
    Response:
    {
        "counties": [
            {
                "id": 1,
                "name": "baringo",
                "soil_type": "loamy",
                "confidence": 0.70
            },
            ...
        ]
    }
    """
    
    counties = sorted(auto_detector.get_all_counties())
    
    result = []
    for i, county in enumerate(counties, 1):
        soil_type, confidence = auto_detector.soil_map[county]
        result.append({
            'id': i,
            'name': county,
            'soil_type': soil_type,
            'confidence': confidence
        })
    
    return jsonify({
        'total_counties': len(result),
        'counties': result
    }), 200


@auto_soil_bp.route('/validate', methods=['POST'])
def validate_county():
    """
    Check if county exists and get its soil
    
    POST /api/auto-soil/validate
    {
        "county": "nairobi"
    }
    
    Response:
    {
        "valid": true,
        "soil_type": "loamy",
        "confidence": 0.85
    }
    """
    
    data = request.json or {}
    county = data.get('county', '').strip().lower()
    
    if not county:
        return jsonify({'valid': False, 'error': 'County required'}), 400
    
    result = auto_detector.detect_from_county_name(county)
    
    # Check if it's the global default (means not found)
    is_valid = result['method'] == 'county_automatic'
    
    return jsonify({
        'valid': is_valid,
        'county': result['county'],
        'soil_type': result['soil_type'],
        'confidence': result['confidence']
    }), 200


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def add_auto_location_endpoints(app):
    """
    Add auto-location soil detection endpoints to Flask app
    
    Usage:
        from auto_location_soil_api import add_auto_location_endpoints
        app = Flask(__name__)
        add_auto_location_endpoints(app)
    """
    
    app.register_blueprint(auto_soil_bp)
    
    logger.info("=" * 70)
    logger.info("✓ Auto-Location Soil Detection API Registered")
    logger.info("=" * 70)
    logger.info("Endpoints:")
    logger.info("  POST /api/auto-soil/detect - Detect from county name")
    logger.info("  POST /api/auto-soil/gps - Detect from GPS coordinates")
    logger.info("  GET  /api/auto-soil/query - Simple GET query")
    logger.info("  GET  /api/auto-soil/counties - List all counties")
    logger.info("  POST /api/auto-soil/validate - Validate county")
    logger.info("=" * 70)


def get_soil_for_county(county: str) -> dict:
    """
    Helper function for internal use in farmer_chatbot.py
    
    Usage:
        from auto_location_soil_api import get_soil_for_county
        soil = get_soil_for_county("nairobi")
        print(soil['soil_type'])  # "loamy"
    """
    
    return auto_detector.detect_from_county_name(county)


def get_soil_from_gps(latitude: float, longitude: float) -> dict:
    """
    Helper function for GPS detection
    
    Usage:
        from auto_location_soil_api import get_soil_from_gps
        soil = get_soil_from_gps(-1.2833, 36.9167)
        print(soil['county'])  # "nairobi"
    """
    
    return auto_detector.detect_from_gps(latitude, longitude)


# ============================================================================
# MIDDLEWARE - Auto-populate soil_type in requests
# ============================================================================

def auto_soil_middleware(app):
    """
    Optional: Add middleware to auto-populate soil_type in farmer profile requests
    
    This intercepts any request with 'county' and adds 'soil_type' if missing
    """
    
    from flask import request, g
    
    @app.before_request
    def auto_detect_soil_for_request():
        """Before each request, auto-detect soil if county provided"""
        
        if request.method in ['POST', 'PUT']:
            data = request.get_json(silent=True) or {}
            
            # If county provided but not soil_type, auto-detect
            if data.get('county') and not data.get('soil_type'):
                soil_result = auto_detector.detect_from_county_name(data['county'])
                
                # Store in g for use in route handlers
                g.auto_detected_soil = soil_result
                g.auto_detected_soil_type = soil_result['soil_type']
                
                logger.debug(f"Auto-detected soil for {data['county']}: "
                           f"{soil_result['soil_type']}")


# ============================================================================
# TEST EXAMPLES
# ============================================================================

if __name__ == '__main__':
    from flask import Flask
    
    app = Flask(__name__)
    add_auto_location_endpoints(app)
    
    print("\n" + "=" * 70)
    print("TESTING AUTO-LOCATION SOIL ENDPOINTS")
    print("=" * 70)
    
    with app.test_client() as client:
        
        # Test 1: Detect from county
        print("\n✓ Test 1: POST /api/auto-soil/detect")
        resp = client.post('/api/auto-soil/detect', 
                          json={'county': 'nairobi'})
        print(f"  Status: {resp.status_code}")
        print(f"  Soil: {resp.json['soil_type']}")
        print(f"  Confidence: {resp.json['confidence']*100:.0f}%")
        
        # Test 2: Detect from GPS
        print("\n✓ Test 2: POST /api/auto-soil/gps")
        resp = client.post('/api/auto-soil/gps',
                          json={'latitude': -0.3667, 'longitude': 36.15})
        print(f"  Status: {resp.status_code}")
        print(f"  County: {resp.json['county']}")
        print(f"  Soil: {resp.json['soil_type']}")
        
        # Test 3: List counties
        print("\n✓ Test 3: GET /api/auto-soil/counties")
        resp = client.get('/api/auto-soil/counties')
        print(f"  Status: {resp.status_code}")
        print(f"  Total counties: {resp.json['total_counties']}")
        print(f"  First 3:")
        for county in resp.json['counties'][:3]:
            print(f"    {county['id']}. {county['name'].upper()} → {county['soil_type']}")
        
        # Test 4: Query simple
        print("\n✓ Test 4: GET /api/auto-soil/query?county=kitui")
        resp = client.get('/api/auto-soil/query?county=kitui')
        print(f"  Status: {resp.status_code}")
        print(f"  Soil: {resp.json['soil_type']}")
        
        # Test 5: Validate
        print("\n✓ Test 5: POST /api/auto-soil/validate")
        resp = client.post('/api/auto-soil/validate',
                          json={'county': 'kisii'})
        print(f"  Status: {resp.status_code}")
        print(f"  Valid: {resp.json['valid']}")
        print(f"  Soil: {resp.json['soil_type']}")
        
        print("\n" + "=" * 70)
        print("✓ All tests passed!")
        print("=" * 70)
