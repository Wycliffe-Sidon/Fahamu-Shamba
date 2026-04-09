#!/usr/bin/env python3
"""
Auto-Detection Soil Map - Location-Based (GPS + County)
Automatically detect soil type from location without manual input
"""

from typing import Dict, Tuple, Optional, Any
import math
import logging

logger = logging.getLogger(__name__)

class AutoLocationSoilDetector:
    """
    Automatically detect soil type from location (GPS or county name)
    When farmer provides location, soil type is determined instantly without extra steps
    """
    
    # County boundary approximations (lat/lon center points in Kenya)
    COUNTY_COORDINATES = {
        'mombasa': (4.0435, 39.6682),
        'kwale': (-4.2333, 39.6167),
        'kilifi': (-3.2833, 39.8333),
        'tanariver': (-2.4667, 40.3167),
        'lamu': (-2.2667, 40.9),
        'taita-taveta': (-3.4833, 38.4167),
        'garissa': (-0.4422, 39.6422),
        'wajir': (1.7421, 40.0589),
        'mandera': (3.9369, 41.8623),
        'marsabit': (2.7149, 37.9910),
        'isiolo': (0.3516, 37.5833),
        'samburu': (0.6143, 37.0954),
        'turkana': (3.5833, 35.8667),
        'westpokot': (1.4, 35.2333),
        'elgeyo-marakwet': (0.6, 35.3),
        'nandi': (0.3833, 34.9667),
        'baringo': (0.4833, 36.1333),
        'laikipia': (-0.2833, 36.8),
        'nakuru': (-0.3667, 36.15),
        'narok': (-1.4167, 35.4167),
        'kajiado': (-2.25, 36.7667),
        'kericho': (-0.3667, 35.2833),
        'bomet': (-0.7833, 34.75),
        'kakamega': (0.2833, 34.75),
        'vihiga': (0.1167, 34.6167),
        'bungoma': (0.5667, 34.5667),
        'trans-nzoia': (0.8333, 35.0333),
        'uasin-gishu': (0.5, 35.2833),
        'kericho': (-0.3667, 35.2833),
        'kisii': (-0.6833, 34.7667),
        'nyamira': (-0.5833, 34.4333),
        'kisumu': (0.1022, 34.7617),
        'homa-bay': (-0.5273, 34.4571),
        'migori': (-1.0634, 34.4731),
        'siaya': (0.0607, 34.2881),
        'nairobi': (-1.2833, 36.9167),
        'murang\'a': (-0.65, 37.1333),
        'nyeri': (-0.4167, 36.95),
        'kiambu': (-1.1833, 36.8333),
        'machakos': (-2.8167, 37.2667),
        'makueni': (-2.75, 37.75),
        'kitui': (-2.2667, 38.3333),
        'mbeere': (-0.5, 37.75),
        'embu': (-0.5333, 37.45),
        'tharaka-nithi': (0.3333, 37.8333),
        'mandera': (3.9369, 41.8623),
        'wajir': (1.7421, 40.0589),
        'garissa': (-0.4422, 39.6422),
        'isiolo': (0.3516, 37.5833),
    }
    
    # Soil type mapping with confidence
    COUNTY_SOIL_MAP = {
        # Coastal Region - Mostly Sandy
        'mombasa': ('sandy', 0.85),
        'kwale': ('sandy', 0.80),
        'kilifi': ('sandy', 0.80),
        'tanariver': ('sandy', 0.75),
        'lamu': ('sandy', 0.85),
        
        # Southern Region - Mixed
        'taita-taveta': ('loamy', 0.65),
        
        # Eastern Semi-Arid - Sandy
        'garissa': ('sandy', 0.80),
        'wajir': ('sandy', 0.85),
        'mandera': ('sandy', 0.85),
        'marsabit': ('sandy', 0.80),
        
        # Central Rift - Mixed
        'isiolo': ('loamy', 0.60),
        'samburu': ('sandy', 0.75),
        'turkana': ('sandy', 0.80),
        'westpokot': ('loamy', 0.65),
        'elgeyo-marakwet': ('loamy', 0.70),
        'nandi': ('loamy', 0.75),
        'baringo': ('loamy', 0.70),
        'laikipia': ('loamy', 0.70),
        
        # Rift Valley - Mixed
        'nakuru': ('loamy', 0.75),
        'narok': ('loamy', 0.70),
        'kajiado': ('sandy', 0.70),
        'kericho': ('loamy', 0.80),
        'bomet': ('loamy', 0.80),
        
        # Western Region - Clay
        'kakamega': ('clay', 0.75),
        'vihiga': ('clay', 0.75),
        'bungoma': ('clay', 0.80),
        'trans-nzoia': ('loamy', 0.75),
        'uasin-gishu': ('loamy', 0.80),
        
        # Nyanza Region - Clay
        'kisii': ('clay', 0.80),
        'nyamira': ('clay', 0.80),
        'kisumu': ('clay', 0.75),
        'homa-bay': ('clay', 0.75),
        'migori': ('clay', 0.75),
        'siaya': ('clay', 0.75),
        
        # Central Highlands - Loamy
        'nairobi': ('loamy', 0.85),
        'murang\'a': ('loamy', 0.85),
        'nyeri': ('loamy', 0.85),
        'kiambu': ('loamy', 0.80),
        'embu': ('loamy', 0.75),
        'mbeere': ('loamy', 0.70),
        'tharaka-nithi': ('loamy', 0.70),
        
        # Machacos Region - Mixed
        'machakos': ('sandy', 0.75),
        'makueni': ('sandy', 0.80),
        'kitui': ('sandy', 0.80),
    }
    
    def __init__(self):
        self.coordinates = self.COUNTY_COORDINATES
        self.soil_map = self.COUNTY_SOIL_MAP
    
    def detect_from_county_name(self, county: str) -> Dict[str, Any]:
        """
        Get soil type from county name instantly
        
        Args:
            county: County name (case-insensitive)
        
        Returns:
            {
                'county': 'nairobi',
                'soil_type': 'loamy',
                'confidence': 0.85,
                'method': 'county_automatic',
                'reasoning': 'Based on your county location'
            }
        """
        
        county_key = county.strip().lower()
        
        if county_key not in self.soil_map:
            logger.warning(f"County '{county}' not found in map")
            return {
                'county': county,
                'soil_type': 'loamy',  # Default global fallback
                'confidence': 0.50,
                'method': 'global_default',
                'reasoning': f"County '{county}' not recognized. Using global default (loamy). Please check spelling."
            }
        
        soil_type, confidence = self.soil_map[county_key]
        
        return {
            'county': county,
            'soil_type': soil_type,
            'confidence': confidence,
            'method': 'county_automatic',
            'reasoning': f'Automatically detected from {county.title()} location ({soil_type} soil, {confidence*100:.0f}% common in this area)'
        }
    
    def detect_from_gps(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Detect soil type from GPS coordinates (auto-detect county)
        
        Args:
            latitude: GPS latitude (-90 to 90)
            longitude: GPS longitude (-180 to 180)
        
        Returns:
            {
                'county': 'nairobi',
                'soil_type': 'loamy',
                'confidence': 0.85,
                'method': 'gps_automatic',
                'latitude': -1.2833,
                'longitude': 36.9167
            }
        """
        
        # Find closest county by GPS coordinates
        closest_county = self._find_closest_county(latitude, longitude)
        
        if closest_county is None:
            return {
                'latitude': latitude,
                'longitude': longitude,
                'soil_type': 'loamy',
                'confidence': 0.40,
                'method': 'global_default',
                'reasoning': 'Location outside Kenya. Using global default.'
            }
        
        # Get soil type for closest county
        result = self.detect_from_county_name(closest_county)
        result['method'] = 'gps_automatic'
        result['latitude'] = latitude
        result['longitude'] = longitude
        result['reasoning'] = f'GPS detected {closest_county.title()} with {result["soil_type"]} soil'
        
        return result
    
    def _find_closest_county(self, lat: float, lon: float) -> Optional[str]:
        """Find county closest to given GPS coordinates"""
        
        if not self.coordinates:
            return None
        
        min_distance = float('inf')
        closest = None
        
        for county, (c_lat, c_lon) in self.coordinates.items():
            # Simple Euclidean distance (good enough for Kenya)
            distance = math.sqrt((lat - c_lat)**2 + (lon - c_lon)**2)
            
            if distance < min_distance:
                min_distance = distance
                closest = county
        
        return closest
    
    def detect_automatic(self, location_input: str = None, 
                        latitude: float = None, 
                        longitude: float = None) -> Dict[str, Any]:
        """
        Automatic detection - choose best method based on available input
        
        Priority:
        1. GPS coordinates (most accurate)
        2. County name (instant)
        3. Global default (fallback)
        
        Args:
            location_input: County name or address
            latitude: GPS latitude (optional)
            longitude: GPS longitude (optional)
        
        Returns:
            Soil detection result with confidence and method
        """
        
        # Try GPS first (highest accuracy)
        if latitude is not None and longitude is not None:
            return self.detect_from_gps(latitude, longitude)
        
        # Try county name
        if location_input:
            return self.detect_from_county_name(location_input)
        
        # Fallback
        return {
            'soil_type': 'loamy',
            'confidence': 0.40,
            'method': 'global_default',
            'reasoning': 'No location data provided. Using global default (loamy).'
        }
    
    def get_all_counties(self) -> list:
        """Get list of all supported counties"""
        return list(self.soil_map.keys())


# Global instance
auto_detector = AutoLocationSoilDetector()


# ============================================================================
# INTEGRATION EXAMPLES FOR DIFFERENT INPUT METHODS
# ============================================================================

class LocationInputMethod:
    """Different ways farmers can enter location"""
    
    @staticmethod
    def voice_county_name(county_spoken: str) -> Dict[str, Any]:
        """
        IVR: Farmer says their county name
        
        IVR: "What county are you in?"
        Farmer: "Nairobi"
        Result: Instant soil type (no extra questions needed!)
        """
        
        return auto_detector.detect_from_county_name(county_spoken)
    
    @staticmethod
    def voice_gps(latitude: float, longitude: float) -> Dict[str, Any]:
        """
        IVR: Farmer's phone GPS location is captured
        
        Result: Instant soil type from coordinates
        """
        
        return auto_detector.detect_from_gps(latitude, longitude)
    
    @staticmethod
    def web_form_county(county_dropdown_value: str) -> Dict[str, Any]:
        """
        Web Chatbot: Farmer selects county from dropdown
        
        Farmer selects "Nairobi" from county dropdown
        Result: Soil type shows immediately (no form field needed!)
        """
        
        return auto_detector.detect_from_county_name(county_dropdown_value)
    
    @staticmethod
    def web_form_current_location() -> Dict[str, Any]:
        """
        Web Chatbot: Farmer clicks "Use my location"
        Browser requests GPS permission and auto-detects
        """
        
        # This would use browser's Geolocation API
        # For now, showing the backend method
        latitude = -1.2833
        longitude = 36.9167
        
        return auto_detector.detect_from_gps(latitude, longitude)
    
    @staticmethod
    def ussd_county_number(county_number: int) -> Dict[str, Any]:
        """
        USSD: Farmer selects county number (1-47)
        
        USSD: "Select your county (1-47)"
        Farmer: "1"
        System: Maps number to county name, gets soil type
        """
        
        counties_list = sorted(auto_detector.get_all_counties())
        
        if 0 <= county_number < len(counties_list):
            county_name = counties_list[county_number]
            return auto_detector.detect_from_county_name(county_name)
        else:
            return {
                'soil_type': 'loamy',
                'confidence': 0.40,
                'method': 'global_default',
                'reasoning': f'Invalid county number {county_number}'
            }


if __name__ == '__main__':
    print("=" * 70)
    print("AUTO LOCATION-BASED SOIL DETECTION - EXAMPLES")
    print("=" * 70)
    
    # Example 1: Voice - Farmer says county name
    print("\n📱 EXAMPLE 1: IVR Voice - Farmer says 'Nairobi'")
    result = LocationInputMethod.voice_county_name("nairobi")
    print(f"   Soil: {result['soil_type'].upper()}")
    print(f"   Confidence: {result['confidence']*100:.0f}%")
    print(f"   Method: {result['method']}")
    print(f"   ✓ No questions needed!")
    
    # Example 2: GPS
    print("\n📱 EXAMPLE 2: GPS Auto-Detection from coordinates")
    result = LocationInputMethod.voice_gps(-0.3667, 36.15)
    print(f"   Location: {result['county'].upper()}")
    print(f"   Soil: {result['soil_type'].upper()}")
    print(f"   Confidence: {result['confidence']*100:.0f}%")
    print(f"   ✓ Instant - no manual input!")
    
    # Example 3: Web dropdown
    print("\n🌐 EXAMPLE 3: Web Chatbot - Farmer selects Kitui")
    result = LocationInputMethod.web_form_county("kitui")
    print(f"   Soil: {result['soil_type'].upper()}")
    print(f"   Confidence: {result['confidence']*100:.0f}%")
    print(f"   ✓ Form field for soil type can be hidden/auto-filled!")
    
    # Example 4: USSD county number
    print("\n📱 EXAMPLE 4: USSD - Farmer presses '30' for county 30")
    result = LocationInputMethod.ussd_county_number(30)
    print(f"   County: {result['county'].upper()}")
    print(f"   Soil: {result['soil_type'].upper()}")
    print(f"   Confidence: {result['confidence']*100:.0f}%")
    print(f"   ✓ Quick numeric selection!")
    
    # Example 5: Not in list
    print("\n⚠️  EXAMPLE 5: Farmer enters unknown county")
    result = auto_detector.detect_from_county_name("atlantis")
    print(f"   Fallback: {result['soil_type'].upper()}")
    print(f"   Confidence: {result['confidence']*100:.0f}%")
    print(f"   ✓ Still provides default, no crash!")
    
    print("\n" + "=" * 70)
    print("All counties supported:")
    print("=" * 70)
    counties = sorted(auto_detector.get_all_counties())
    for i, county in enumerate(counties, 1):
        soil, conf = auto_detector.soil_map[county]
        print(f"{i:2d}. {county.upper():20s} → {soil:6s} ({conf*100:.0f}%)")
