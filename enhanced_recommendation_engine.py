#!/usr/bin/env python3
"""
Enhanced Fahamu Shamba - AI Crop Recommendation Engine
Meets all objectives: Environmental, Agronomic, Market variables + Farmer feedback loop
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib
import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import requests
import json
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedCropRecommendationEngine:
    """Complete AI-powered crop recommendation system meeting all objectives"""

    # Kenya-specific crop requirements with environmental data
    CROP_REQUIREMENTS = {
        'maize': {
            'ph_range': (5.5, 7.0), 'rainfall_mm': (500, 800), 'temp_c': (15, 30),
            'growing_season_days': 120, 'market_demand': 'high', 'price_per_kg': 30
        },
        'beans': {
            'ph_range': (6.0, 7.5), 'rainfall_mm': (400, 600), 'temp_c': (15, 25),
            'growing_season_days': 90, 'market_demand': 'medium', 'price_per_kg': 85
        },
        'tomatoes': {
            'ph_range': (6.0, 7.0), 'rainfall_mm': (600, 900), 'temp_c': (18, 28),
            'growing_season_days': 150, 'market_demand': 'high', 'price_per_kg': 120
        },
        'potatoes': {
            'ph_range': (4.8, 6.5), 'rainfall_mm': (500, 700), 'temp_c': (15, 22),
            'growing_season_days': 110, 'market_demand': 'medium', 'price_per_kg': 45
        },
        'kale': {
            'ph_range': (6.0, 7.5), 'rainfall_mm': (400, 600), 'temp_c': (15, 22),
            'growing_season_days': 60, 'market_demand': 'high', 'price_per_kg': 60
        },
        'sorghum': {
            'ph_range': (6.0, 7.5), 'rainfall_mm': (300, 600), 'temp_c': (20, 35),
            'growing_season_days': 100, 'market_demand': 'medium', 'price_per_kg': 55
        },
        'millet': {
            'ph_range': (6.0, 7.5), 'rainfall_mm': (250, 500), 'temp_c': (20, 35),
            'growing_season_days': 80, 'market_demand': 'low', 'price_per_kg': 65
        }
    }

    # Kenyan counties with climate data
    KENYA_COUNTIES = {
        'nairobi': {'altitude': 1795, 'climate': 'highland', 'avg_rainfall': 850, 'avg_temp': 18},
        'mombasa': {'altitude': 0, 'climate': 'coastal', 'avg_rainfall': 1200, 'avg_temp': 27},
        'kisumu': {'altitude': 1131, 'climate': 'lakeside', 'avg_rainfall': 1350, 'avg_temp': 23},
        'nakuru': {'altitude': 1859, 'climate': 'highland', 'avg_rainfall': 700, 'avg_temp': 17},
        'eldoret': {'altitude': 2100, 'climate': 'highland', 'avg_rainfall': 900, 'avg_temp': 16},
        'kitui': {'altitude': 1100, 'climate': 'semi-arid', 'avg_rainfall': 500, 'avg_temp': 24},
        'garissa': {'altitude': 150, 'climate': 'arid', 'avg_rainfall': 250, 'avg_temp': 29},
        'kakamega': {'altitude': 1530, 'climate': 'highland', 'avg_rainfall': 1900, 'avg_temp': 19}
    }

    def __init__(self, model_type: str = "random_forest"):
        self.model_type = model_type
        self.scaler = StandardScaler()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_columns: List[str] = []
        self.is_trained = False
        self.feedback_data: List[Dict] = []
        
        # Support persistent storage for Render deployment
        import os
        default_data_dir = '/app/data'
        if os.name == 'nt':
            default_data_dir = '.'
        self.data_dir = os.environ.get('MODEL_DATA_DIR', default_data_dir)
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir, exist_ok=True)
            except Exception as e:
                logger.warning(f"Could not create data directory {self.data_dir}: {e}. Using current directory.")
                self.data_dir = '.'

        if model_type == "random_forest":
            self.model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        elif model_type == "gradient_boosting":
            self.model = GradientBoostingClassifier(n_estimators=100, random_state=42, learning_rate=0.1)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    def generate_enhanced_sample_data(self, n_samples: int = 2000) -> pd.DataFrame:
        """Generate realistic Kenyan agricultural data"""
        np.random.seed(42)
        data = []

        counties = list(self.KENYA_COUNTIES.keys())
        crops = list(self.CROP_REQUIREMENTS.keys())
        soil_types = ['loamy', 'clay', 'sandy', 'silty', 'peaty']
        irrigation_options = [0, 1]  # 0=no, 1=yes
        
        for i in range(n_samples):
            county = np.random.choice(counties)
            crop = np.random.choice(crops)
            soil_type = np.random.choice(soil_types)
            irrigation = np.random.choice(irrigation_options)
            
            county_data = self.KENYA_COUNTIES[county]
            crop_data = self.CROP_REQUIREMENTS[crop]
            
            # Environmental variables
            ph = np.random.uniform(4.5, 8.0)
            rainfall = county_data['avg_rainfall'] + np.random.normal(0, 100)
            temperature = county_data['avg_temp'] + np.random.normal(0, 2)
            humidity = np.random.uniform(40, 90)
            altitude = county_data['altitude']
            
            # Farmer variables
            land_size = np.random.uniform(0.5, 10)  # acres
            fertilizer_use = np.random.choice([0, 1])
            pest_disease_risk = np.random.uniform(0, 1)
            
            # Market variables
            market_price = crop_data['price_per_kg'] + np.random.normal(0, 10)
            demand_index = {'high': 0.9, 'medium': 0.6, 'low': 0.3}[crop_data['market_demand']]
            
            # Calculate yield based on conditions
            suitability_score = self._calculate_suitability_score(ph, rainfall, temperature, crop)
            base_yield = suitability_score * 3.0  # tons per acre
            actual_yield = base_yield * (1 + irrigation * 0.3) * (1 + fertilizer_use * 0.2)
            actual_yield *= (1 - pest_disease_risk * 0.3)
            actual_yield = max(0.1, actual_yield + np.random.normal(0, 0.3))
            
            # Success metric (yield > threshold)
            success = 1 if actual_yield > 1.5 else 0
            
            data.append({
                'county': county,
                'crop': crop,
                'soil_type': soil_type,
                'soil_ph': ph,
                'rainfall_mm': rainfall,
                'temperature_c': temperature,
                'humidity_percent': humidity,
                'altitude_m': altitude,
                'land_size_acres': land_size,
                'irrigation_available': irrigation,
                'fertilizer_use': fertilizer_use,
                'pest_disease_risk': pest_disease_risk,
                'market_price_kes': market_price,
                'demand_index': demand_index,
                'actual_yield_tons_per_acre': actual_yield,
                'success': success
            })
        
        return pd.DataFrame(data)

    def _calculate_suitability_score(self, ph: float, rainfall: float, temp: float, crop: str) -> float:
        """Calculate how suitable conditions are for a specific crop"""
        crop_req = self.CROP_REQUIREMENTS[crop]
        
        ph_score = 1.0 - abs(ph - np.mean(crop_req['ph_range'])) / 3.0
        ph_score = max(0, min(1, ph_score))
        
        rain_score = 1.0 - abs(rainfall - np.mean(crop_req['rainfall_mm'])) / 500
        rain_score = max(0, min(1, rain_score))
        
        temp_score = 1.0 - abs(temp - np.mean(crop_req['temp_c'])) / 10
        temp_score = max(0, min(1, temp_score))
        
        return (ph_score + rain_score + temp_score) / 3.0

    def preprocess_features(self, df: pd.DataFrame, fit_encoders: bool = False) -> pd.DataFrame:
        """Preprocess features for ML model"""
        df_processed = df.copy()
        
        categorical_columns = ['county', 'soil_type']
        
        for col in categorical_columns:
            if fit_encoders:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                df_processed[f'{col}_encoded'] = self.label_encoders[col].fit_transform(df_processed[col])
            else:
                if col in self.label_encoders:
                    df_processed[f'{col}_encoded'] = self.label_encoders[col].transform(df_processed[col])
                else:
                    df_processed[f'{col}_encoded'] = 0
        
        # Feature columns for model
        feature_cols = [
            'county_encoded', 'soil_type_encoded', 'soil_ph', 'rainfall_mm',
            'temperature_c', 'humidity_percent', 'altitude_m', 'land_size_acres',
            'irrigation_available', 'fertilizer_use', 'pest_disease_risk',
            'market_price_kes', 'demand_index'
        ]
        
        if fit_encoders:
            self.feature_columns = feature_cols
        
        return df_processed[feature_cols]

    def train(self, data: pd.DataFrame) -> Dict:
        """Train the AI model with feedback loop capability"""
        logger.info(f"Training enhanced model with {len(data)} samples")
        
        # Preprocess features
        X = self.preprocess_features(data, fit_encoders=True)
        y = data['crop']
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        test_score = self.model.score(X_test_scaled, y_test)
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        
        metrics = {
            'train_accuracy': train_score,
            'test_accuracy': test_score,
            'cv_mean': cv_scores.mean(),
            'cv_std': cv_scores.std(),
            'n_features': X_train.shape[1],
            'n_samples': len(data)
        }
        
        logger.info(f"Model trained - Test accuracy: {test_score:.3f}")
        return metrics

    def get_recommendations(self, farmer_data: Dict) -> Dict:
        """Get crop recommendations with confidence scores"""
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        # Create input dataframe with all required columns
        input_df = pd.DataFrame([farmer_data])
        
        # Add derived features
        county = farmer_data.get('county', 'nairobi')
        if county in self.KENYA_COUNTIES:
            county_data = self.KENYA_COUNTIES[county]
            input_df['altitude_m'] = county_data['altitude']
            input_df['rainfall_mm'] = county_data['avg_rainfall']
            input_df['temperature_c'] = county_data['avg_temp']
        
        # Add missing columns with defaults
        input_df['humidity_percent'] = farmer_data.get('humidity_percent', 65)
        input_df['pest_disease_risk'] = farmer_data.get('pest_disease_risk', 0.3)
        input_df['market_price_kes'] = farmer_data.get('market_price_kes', 50)
        input_df['demand_index'] = farmer_data.get('demand_index', 0.6)
        input_df['fertilizer_use'] = farmer_data.get('fertilizer_use', 0)
        
        # Preprocess
        X = self.preprocess_features(input_df, fit_encoders=False)
        X_scaled = self.scaler.transform(X)
        
        # Get predictions and probabilities
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        # Get top 3 recommendations
        crop_classes = self.model.classes_
        prob_scores = probabilities[0]
        
        market_prices = {
            str(name).lower(): value
            for name, value in (farmer_data.get('market_prices') or {}).items()
        }
        market_trends = {
            str(name).lower(): value
            for name, value in (farmer_data.get('market_trends') or {}).items()
        }

        # Create recommendation list with confidence scores
        recommendations = []
        for i, crop in enumerate(crop_classes):
            confidence = prob_scores[i]
            crop_data = self.CROP_REQUIREMENTS[crop]
            live_price = market_prices.get(crop.lower(), crop_data['price_per_kg'])
            trend_data = market_trends.get(crop.lower(), {})
            trend = trend_data.get('trend', crop_data['market_demand'])
            trend_bonus = 1.05 if trend == 'increasing' else 0.97 if trend == 'decreasing' else 1.0
             
            # Calculate expected yield and revenue
            suitability = self._calculate_suitability_score(
                farmer_data.get('soil_ph', 6.5),
                farmer_data.get('rainfall_mm', 700),
                farmer_data.get('temperature_c', 22),
                crop
            )
             
            expected_yield = suitability * 3.0  # tons per acre
            expected_revenue = expected_yield * farmer_data.get('land_size_acres', 2) * live_price * trend_bonus
             
            recommendations.append({
                'crop': crop,
                'confidence': round(confidence * 100, 1),
                'expected_yield_tons_per_acre': round(expected_yield, 2),
                'expected_revenue_kes': round(expected_revenue, 0),
                'growing_season_days': crop_data['growing_season_days'],
                'market_demand': crop_data['market_demand'],
                'live_market_price_kes': round(live_price, 2),
                'market_trend': trend,
                'reason': self._generate_recommendation_reason(suitability, crop_data, farmer_data, live_price, trend)
            })
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'top_recommendation': recommendations[0],
            'all_recommendations': recommendations[:3],
            'farmer_data': farmer_data,
            'model_confidence': recommendations[0]['confidence']
        }

    def _generate_recommendation_reason(
        self,
        suitability: float,
        crop_data: Dict,
        farmer_data: Dict,
        live_price: float,
        trend: str,
    ) -> str:
        """Generate human-readable recommendation reason"""
        reasons = []
        
        if suitability > 0.8:
            reasons.append("Excellent soil and climate conditions")
        elif suitability > 0.6:
            reasons.append("Good growing conditions")
        else:
            reasons.append("Suitable with proper management")
        
        if farmer_data.get('irrigation_available', 0):
            reasons.append("Irrigation available improves yield")
        
        if crop_data['market_demand'] == 'high':
            reasons.append("High market demand")

        if live_price >= crop_data['price_per_kg'] * 1.05:
            reasons.append("Current market price is favorable")
        elif live_price <= crop_data['price_per_kg'] * 0.9:
            reasons.append("Market price is below the usual range")

        if trend == 'increasing':
            reasons.append("Price trend is improving")
        elif trend == 'decreasing':
            reasons.append("Price trend is softening")
         
        return ". ".join(reasons)

    def add_feedback(self, feedback: Dict):
        """Add farmer feedback for model retraining"""
        self.feedback_data.append(feedback)
        logger.info(f"Added feedback: {feedback['crop']} - success: {feedback['success']}")

    def retrain_with_feedback(self, min_feedback: int = 50) -> Dict:
        """Retrain model with accumulated feedback data"""
        if len(self.feedback_data) < min_feedback:
            logger.info(f"Insufficient feedback: {len(self.feedback_data)}/{min_feedback}")
            return {'status': 'insufficient_feedback', 'count': len(self.feedback_data)}
        
        logger.info(f"Retraining with {len(self.feedback_data)} feedback samples")
        
        # Convert feedback to training data
        feedback_df = pd.DataFrame(self.feedback_data)
        
        # Combine with existing data (load from file if exists)
        try:
            existing_data = pd.read_csv('fahamu_shamba_training_data.csv')
            combined_data = pd.concat([existing_data, feedback_df], ignore_index=True)
        except FileNotFoundError:
            combined_data = feedback_df
        
        # Retrain model
        metrics = self.train(combined_data)
        
        # Save updated model and data
        self.save_model('enhanced_crop_recommendation_model.pkl')
        combined_data.to_csv('fahamu_shamba_training_data.csv', index=False)
        
        # Clear feedback after retraining
        self.feedback_data = []
        
        return {
            'status': 'retrained',
            'metrics': metrics,
            'feedback_used': len(feedback_df)
        }

    def save_model(self, filename: str):
        """Save the trained model and preprocessors"""
        import os
        
        # If filename is just a basename, save to data directory
        if not os.path.dirname(filename):
            filepath = os.path.join(self.data_dir, filename)
        else:
            filepath = filename
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filename: str):
        """Load a trained model from persistent storage or current directory"""
        import os
        
        # Try multiple paths for flexibility
        possible_paths = [
            filename,  # Current directory or absolute path
            os.path.join(self.data_dir, filename),  # Data directory
            os.path.join('/app/data', filename),  # Render persistent disk
        ]
        
        filepath = None
        for path in possible_paths:
            if os.path.exists(path):
                filepath = path
                break
        
        if filepath is None:
            raise FileNotFoundError(f"Model file {filename} not found. Checked: {possible_paths}")
        
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.label_encoders = model_data['label_encoders']
        self.feature_columns = model_data['feature_columns']
        self.model_type = model_data['model_type']
        self.is_trained = model_data['is_trained']
        logger.info(f"Model loaded from {filepath}")

def main():
    """Demonstrate the enhanced recommendation engine"""
    print("🌾 FAHAMU SHAMBA - Enhanced AI Recommendation Engine")
    print("=" * 60)
    
    # Initialize engine
    engine = EnhancedCropRecommendationEngine()
    
    # Generate training data
    print("📊 Generating Kenyan agricultural training data...")
    data = engine.generate_enhanced_sample_data(2000)
    
    # Train model
    print("🤖 Training AI model with environmental and market variables...")
    metrics = engine.train(data)
    print(f"✅ Model trained successfully!")
    print(f"   Test Accuracy: {metrics['test_accuracy']:.3f}")
    print(f"   Cross-validation Score: {metrics['cv_mean']:.3f} ± {metrics['cv_std']:.3f}")
    
    # Save model
    engine.save_model('enhanced_crop_recommendation_model.pkl')
    
    # Test recommendations
    print("\n🧪 Testing crop recommendations...")
    
    test_farmers = [
        {
            'county': 'nairobi',
            'soil_type': 'loamy',
            'soil_ph': 6.5,
            'land_size_acres': 2.5,
            'irrigation_available': 1,
            'fertilizer_use': 1
        },
        {
            'county': 'kitui',
            'soil_type': 'sandy',
            'soil_ph': 5.8,
            'land_size_acres': 5.0,
            'irrigation_available': 0,
            'fertilizer_use': 0
        },
        {
            'county': 'kakamega',
            'soil_type': 'clay',
            'soil_ph': 7.2,
            'land_size_acres': 1.0,
            'irrigation_available': 1,
            'fertilizer_use': 1
        }
    ]
    
    for i, farmer in enumerate(test_farmers, 1):
        print(f"\n👨‍🌾 Farmer {i} - {farmer['county'].title()}")
        recommendations = engine.get_recommendations(farmer)
        
        top = recommendations['top_recommendation']
        print(f"   🌱 Top Recommendation: {top['crop'].title()}")
        print(f"   📊 Confidence: {top['confidence']}%")
        print(f"   💰 Expected Revenue: KES {top['expected_revenue_kes']:,}")
        print(f"   📈 Expected Yield: {top['expected_yield_tons_per_acre']} tons/acre")
        print(f"   📝 Reason: {top['reason']}")
    
    print(f"\n✅ Enhanced AI recommendation system ready!")
    print(f"   All objectives met:")
    print(f"   ✅ Environmental variables (soil, weather, climate)")
    print(f"   ✅ Agronomic variables (crop cycles, pest risk)")
    print(f"   ✅ Market variables (prices, demand)")
    print(f"   ✅ Farmer data (location, land size, irrigation)")
    print(f"   ✅ AI Model (Random Forest with confidence scores)")
    print(f"   ✅ Feedback loop for continuous improvement")
    print(f"   ✅ Kenyan-specific data and counties")

if __name__ == "__main__":
    main()
