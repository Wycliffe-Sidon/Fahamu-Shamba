#!/usr/bin/env python3
"""
Fahamu Shamba - AI Model Training Pipeline
Enhanced Random Forest model for crop recommendations
"""

import pandas as pd
import numpy as np
import json
import pickle
import logging
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
import sqlite3
import requests
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CropRecommendationModel:
    """Enhanced AI model for crop recommendations"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        self.crop_labels = []
        self.model_version = "2.0"
        self.last_trained = None
        
        # Kenyan counties with their agricultural zones
        self.county_zones = {
            'nairobi': 'highland', 'mombasa': 'coastal', 'kwale': 'coastal',
            'kilifi': 'coastal', 'tana_river': 'coastal', 'lamu': 'coastal',
            'taita_taveta': 'coastal', 'garissa': 'arid', 'wajir': 'arid',
            'mandera': 'arid', 'marsabit': 'arid', 'isiolo': 'arid',
            'meru': 'highland', 'tharaka': 'highland', 'embu': 'highland',
            'kitui': 'semi-arid', 'machakos': 'semi-arid', 'makueni': 'semi-arid',
            'nyeri': 'highland', 'kirinyaga': 'highland', 'muranga': 'highland',
            'kiambu': 'highland', 'turkana': 'arid', 'west_pokot': 'highland',
            'samburu': 'arid', 'trans_nzoia': 'highland', 'uasin_gishu': 'highland',
            'elgeyo_maji': 'highland', 'nandi': 'highland', 'baringo': 'highland',
            'laikipia': 'semi-arid', 'nakuru': 'highland', 'narok': 'highland',
            'kajiado': 'semi-arid', 'kericho': 'highland', 'bomet': 'highland',
            'kakamega': 'highland', 'vihiga': 'highland', 'bungoma': 'highland',
            'busia': 'highland', 'siaya': 'highland', 'kisumu': 'highland',
            'homabay': 'highland', 'migori': 'highland', 'nyamira': 'highland',
            'kisii': 'highland', 'homa_bay': 'highland'
        }
        
        # Crop suitability by zone
        self.zone_crops = {
            'highland': ['maize', 'beans', 'potatoes', 'kale', 'cabbage', 'carrots', 'tea', 'coffee'],
            'coastal': ['maize', 'cashew_nuts', 'coconuts', 'mangoes', 'rice', 'sesame'],
            'arid': ['sorghum', 'millet', 'cowpeas', 'drought_resistant_maize', 'pigeon_peas'],
            'semi-arid': ['maize', 'beans', 'sorghum', 'millet', 'green_grams', 'drought_resistant_crops']
        }
    
    def load_historical_data(self) -> pd.DataFrame:
        """Load and prepare historical agricultural data.

        Priority order:
        1. Real CSV from TRAINING_DATA_PATH env var (KALRO / FAO / KNBS export)
        2. Existing fahamu_shamba_training_data.csv in current directory
        3. Synthetic fallback (development only)
        """
        import os

        real_data_paths = [
            os.getenv("TRAINING_DATA_PATH", ""),
            "fahamu_shamba_training_data.csv",
            "/app/data/fahamu_shamba_training_data.csv",
        ]

        for path in real_data_paths:
            if path and os.path.exists(path):
                try:
                    df = pd.read_csv(path)
                    required = {"county", "crop_planted", "rainfall_mm", "temperature_c", "soil_ph"}
                    if required.issubset(set(df.columns)):
                        logger.info("Loaded real training data from %s (%d rows)", path, len(df))
                        return df
                    logger.warning("CSV at %s missing required columns, skipping.", path)
                except Exception as exc:
                    logger.warning("Could not read %s: %s", path, exc)

        logger.warning(
            "No real training data found. Using synthetic data. "
            "For production, export KALRO/FAO/KNBS data to fahamu_shamba_training_data.csv "
            "with columns: county, crop_planted, rainfall_mm, temperature_c, soil_ph, "
            "humidity_percent, soil_moisture_percent, nitrogen_mg_kg, phosphorus_mg_kg, "
            "potassium_mg_kg, organic_matter_percent, land_size_acres, irrigation_available, "
            "fertilizer_use, market_price_ksh, demand_trend, month, actual_yield_tons_per_acre"
        )
        np.random.seed(42)
        
        data = []
        
        # Generate 10,000 historical records
        for i in range(10000):
            # Random county
            county = np.random.choice(list(self.county_zones.keys()))
            zone = self.county_zones[county]
            
            # Environmental variables
            rainfall = np.random.normal(800, 300) if zone == 'highland' else \
                      np.random.normal(400, 200) if zone == 'semi-arid' else \
                      np.random.normal(200, 150) if zone == 'coastal' else \
                      np.random.normal(150, 100)
            
            temperature = np.random.normal(18, 3) if zone == 'highland' else \
                         np.random.normal(25, 4) if zone == 'coastal' else \
                         np.random.normal(28, 5) if zone == 'arid' else \
                         np.random.normal(22, 4)
            
            humidity = np.random.normal(65, 15) if zone == 'highland' else \
                      np.random.normal(75, 10) if zone == 'coastal' else \
                      np.random.normal(45, 20) if zone == 'arid' else \
                      np.random.normal(55, 15)
            
            # Soil properties
            soil_ph = np.random.normal(6.5, 0.8)
            soil_moisture = np.random.normal(45, 20)
            nitrogen = np.random.normal(40, 15)
            phosphorus = np.random.normal(25, 10)
            potassium = np.random.normal(35, 12)
            organic_matter = np.random.normal(2.5, 1.0)
            
            # Farm characteristics
            land_size = np.random.exponential(2.0)  # Exponential distribution for small farms
            irrigation = np.random.choice([0, 1], p=[0.7, 0.3])  # 30% have irrigation
            fertilizer_use = np.random.choice([0, 1], p=[0.4, 0.6])  # 60% use fertilizer
            
            # Market factors
            market_price = np.random.normal(50, 20)
            demand_trend = np.random.choice(['increasing', 'stable', 'decreasing'], p=[0.4, 0.4, 0.2])
            
            # Time variables
            month = np.random.randint(1, 13)
            season = self._get_season(month)
            
            # Select suitable crop based on conditions
            suitable_crops = self.zone_crops[zone]
            
            # Add some logic for crop selection based on conditions
            if rainfall > 600 and temperature < 22:
                preferred_crops = ['maize', 'beans', 'potatoes']
            elif rainfall < 300:
                preferred_crops = ['sorghum', 'millet', 'drought_resistant_maize']
            elif temperature > 25:
                preferred_crops = ['cashew_nuts', 'coconuts', 'mangoes'] if zone == 'coastal' else suitable_crops
            else:
                preferred_crops = suitable_crops
            
            # Choose crop with some probability
            if np.random.random() < 0.7:  # 70% choose from preferred
                crop = np.random.choice(preferred_crops)
            else:  # 30% choose any suitable crop
                crop = np.random.choice(suitable_crops)
            
            # Calculate yield (simplified model)
            base_yield = {
                'maize': 2.5, 'beans': 1.2, 'potatoes': 8.0, 'kale': 15.0,
                'cabbage': 20.0, 'carrots': 12.0, 'tea': 3.0, 'coffee': 2.0,
                'cashew_nuts': 1.5, 'coconuts': 4.0, 'mangoes': 6.0, 'rice': 3.5,
                'sesame': 1.0, 'sorghum': 1.8, 'millet': 1.5, 'cowpeas': 0.8,
                'drought_resistant_maize': 2.0, 'pigeon_peas': 1.0, 'green_grams': 0.9,
                'drought_resistant_crops': 1.5
            }
            
            # Yield modifiers based on conditions
            rainfall_modifier = min(rainfall / 500, 1.5) if rainfall < 1000 else 1.0
            temp_modifier = 1.0 - abs(temperature - 22) / 20
            soil_modifier = 1.0 - abs(soil_ph - 6.5) / 3
            irrigation_modifier = 1.3 if irrigation else 1.0
            fertilizer_modifier = 1.4 if fertilizer_use else 1.0
            
            actual_yield = (base_yield.get(crop, 2.0) * 
                          rainfall_modifier * temp_modifier * soil_modifier * 
                          irrigation_modifier * fertilizer_modifier * 
                          np.random.normal(1.0, 0.2))
            
            # Success indicator (yield above threshold)
            success = 1 if actual_yield > base_yield.get(crop, 2.0) * 0.8 else 0
            
            data.append({
                'county': county,
                'zone': zone,
                'rainfall_mm': max(0, rainfall),
                'temperature_c': temperature,
                'humidity_percent': max(0, min(100, humidity)),
                'soil_ph': soil_ph,
                'soil_moisture_percent': max(0, min(100, soil_moisture)),
                'nitrogen_mg_kg': max(0, nitrogen),
                'phosphorus_mg_kg': max(0, phosphorus),
                'potassium_mg_kg': max(0, potassium),
                'organic_matter_percent': max(0, organic_matter),
                'land_size_acres': max(0.1, land_size),
                'irrigation_available': irrigation,
                'fertilizer_use': fertilizer_use,
                'market_price_ksh': max(0, market_price),
                'demand_trend': demand_trend,
                'month': month,
                'season': season,
                'crop_planted': crop,
                'actual_yield_tons_per_acre': max(0, actual_yield),
                'success': success
            })
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} historical records")
        
        return df
    
    def _get_season(self, month: int) -> str:
        """Get season based on month"""
        if month in [3, 4, 5]:
            return 'long_rains'
        elif month in [6, 7, 8, 9]:
            return 'dry_season'
        elif month in [10, 11, 12]:
            return 'short_rains'
        else:
            return 'hot_season'
    
    def preprocess_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Preprocess data for model training"""
        logger.info("Preprocessing data...")
        
        # Create success indicator based on yield performance
        # We'll predict which crops are likely to be successful
        
        # Filter for successful crops (above average yield)
        successful_crops = df[df['success'] == 1].copy()
        
        # Create features for each crop-county-season combination
        features = []
        labels = []
        
        # Group by county and season to create crop recommendations
        for (county, season), group in df.groupby(['county', 'season']):
            zone = self.county_zones[county]
            
            # Get average conditions for this county-season
            avg_conditions = group.agg({
                'rainfall_mm': 'mean',
                'temperature_c': 'mean',
                'humidity_percent': 'mean',
                'soil_ph': 'mean',
                'soil_moisture_percent': 'mean',
                'nitrogen_mg_kg': 'mean',
                'phosphorus_mg_kg': 'mean',
                'potassium_mg_kg': 'mean',
                'organic_matter_percent': 'mean',
                'market_price_ksh': 'mean'
            }).to_dict()
            
            # For each crop, calculate success rate
            crop_performance = group.groupby('crop_planted').agg({
                'success': ['mean', 'count'],
                'actual_yield_tons_per_acre': 'mean'
            }).round(3)
            
            # Create training examples for successful crops
            for crop in crop_performance.index:
                success_rate = crop_performance.loc[crop, ('success', 'mean')]
                sample_count = crop_performance.loc[crop, ('success', 'count')]
                
                if sample_count >= 5:  # Minimum samples for reliability
                    feature_row = avg_conditions.copy()
                    feature_row.update({
                        'crop': crop,
                        'zone': zone,
                        'season': season,
                        'success_rate': success_rate,
                        'sample_count': sample_count
                    })
                    
                    # Add crop-specific features
                    suitable_crops = self.zone_crops.get(zone, [])
                    feature_row['crop_suitable_for_zone'] = 1 if crop in suitable_crops else 0
                    
                    features.append(feature_row)
                    labels.append(crop)
        
        feature_df = pd.DataFrame(features)
        
        logger.info(f"Created {len(feature_df)} training examples")
        return feature_df, pd.Series(labels)
    
    def encode_features(self, df: pd.DataFrame, fit_encoders: bool = True) -> pd.DataFrame:
        """Encode categorical features"""
        df_encoded = df.copy()
        
        # Encode categorical variables
        categorical_columns = ['zone', 'season', 'demand_trend']
        
        for col in categorical_columns:
            if col in df_encoded.columns:
                if fit_encoders:
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                    df_encoded[col + '_encoded'] = self.label_encoders[col].fit_transform(df_encoded[col])
                else:
                    if col in self.label_encoders:
                        df_encoded[col + '_encoded'] = self.label_encoders[col].transform(df_encoded[col])
        
        # Select numerical features for modeling
        numerical_features = [
            'rainfall_mm', 'temperature_c', 'humidity_percent',
            'soil_ph', 'soil_moisture_percent', 'nitrogen_mg_kg',
            'phosphorus_mg_kg', 'potassium_mg_kg', 'organic_matter_percent',
            'market_price_ksh', 'success_rate', 'sample_count',
            'crop_suitable_for_zone'
        ]
        
        # Add encoded categorical features
        for col in categorical_columns:
            if col + '_encoded' in df_encoded.columns:
                numerical_features.append(col + '_encoded')
        
        # Keep only available features
        available_features = [f for f in numerical_features if f in df_encoded.columns]
        
        return df_encoded[available_features]
    
    def train_model(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """Train the crop recommendation model"""
        logger.info("Training crop recommendation model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Try both Random Forest and Gradient Boosting
        models = {
            'RandomForest': RandomForestClassifier(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            ),
            'GradientBoosting': GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=6,
                random_state=42
            )
        }
        
        best_model = None
        best_score = 0
        best_name = None
        
        for name, model in models.items():
            # Cross-validation
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='accuracy')
            avg_score = cv_scores.mean()
            
            logger.info(f"{name} CV Score: {avg_score:.3f} (+/- {cv_scores.std() * 2:.3f})")
            
            if avg_score > best_score:
                # Train final model
                model.fit(X_train_scaled, y_train)
                
                # Test performance
                y_pred = model.predict(X_test_scaled)
                test_score = accuracy_score(y_test, y_pred)
                
                logger.info(f"{name} Test Score: {test_score:.3f}")
                
                best_model = model
                best_score = avg_score
                best_name = name
        
        self.model = best_model
        self.feature_names = X.columns.tolist()
        self.crop_labels = y.unique().tolist()
        
        # Feature importance
        if hasattr(best_model, 'feature_importances_'):
            feature_importance = dict(zip(self.feature_names, best_model.feature_importances_))
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            
            logger.info("Top 10 Important Features:")
            for feature, importance in sorted_features[:10]:
                logger.info(f"  {feature}: {importance:.3f}")
        
        training_info = {
            'model_type': best_name,
            'cv_score': best_score,
            'features_count': len(self.feature_names),
            'crops_count': len(self.crop_labels),
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        self.last_trained = datetime.now().isoformat()
        
        return training_info
    
    def save_model(self, filepath: str = 'enhanced_crop_recommendation_model.pkl'):
        """Save the trained model"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'crop_labels': self.crop_labels,
            'model_version': self.model_version,
            'last_trained': self.last_trained,
            'county_zones': self.county_zones,
            'zone_crops': self.zone_crops
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str = 'enhanced_crop_recommendation_model.pkl'):
        """Load a trained model"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.label_encoders = model_data['label_encoders']
            self.feature_names = model_data['feature_names']
            self.crop_labels = model_data['crop_labels']
            self.model_version = model_data['model_version']
            self.last_trained = model_data['last_trained']
            self.county_zones = model_data['county_zones']
            self.zone_crops = model_data['zone_crops']
            
            logger.info(f"Model loaded from {filepath}")
            logger.info(f"Model version: {self.model_version}")
            logger.info(f"Last trained: {self.last_trained}")
            
            return True
            
        except FileNotFoundError:
            logger.warning(f"Model file {filepath} not found")
            return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict_crops(self, input_data: Dict, top_k: int = 5) -> Dict:
        """Predict top K suitable crops for given conditions"""
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Prepare input data
        input_df = pd.DataFrame([input_data])
        
        # Add derived features
        county = input_data.get('county', 'nairobi')
        zone = self.county_zones.get(county, 'highland')
        input_df['zone'] = zone
        input_df['season'] = self._get_season(input_data.get('month', 3))
        
        # Add market and success rate estimates (simplified)
        input_df['market_price_ksh'] = 50  # Default market price
        input_df['success_rate'] = 0.7  # Default success rate
        input_df['sample_count'] = 100  # Default sample count
        input_df['crop_suitable_for_zone'] = 1  # Assume suitable
        
        # Encode features
        input_encoded = self.encode_features(input_df, fit_encoders=False)
        
        # Ensure all required features are present
        missing_features = set(self.feature_names) - set(input_encoded.columns)
        for feature in missing_features:
            input_encoded[feature] = 0  # Default value
        
        # Reorder columns to match training
        input_encoded = input_encoded[self.feature_names]
        
        # Scale features
        input_scaled = self.scaler.transform(input_encoded)
        
        # Get prediction probabilities
        probabilities = self.model.predict_proba(input_scaled)[0]
        
        # Get all crop predictions with probabilities
        crop_predictions = []
        for i, crop in enumerate(self.model.classes_):
            crop_predictions.append((crop, probabilities[i]))
        
        # Sort by probability and get top K
        crop_predictions.sort(key=lambda x: x[1], reverse=True)
        top_crops = crop_predictions[:top_k]
        
        # Format response
        recommendations = []
        for crop, confidence in top_crops:
            recommendations.append({
                'crop': crop,
                'confidence': round(confidence * 100, 1),
                'reasoning': self._generate_reasoning(crop, input_data),
                'expected_yield': self._estimate_yield(crop, input_data),
                'market_outlook': self._get_market_outlook(crop)
            })
        
        return {
            'top_recommendation': recommendations[0],
            'all_recommendations': recommendations,
            'input_conditions': input_data,
            'model_version': self.model_version,
            'prediction_time': datetime.now().isoformat()
        }
    
    def _generate_reasoning(self, crop: str, input_data: Dict) -> str:
        """Generate reasoning for crop recommendation"""
        county = input_data.get('county', 'nairobi')
        zone = self.county_zones.get(county, 'highland')
        rainfall = input_data.get('rainfall_mm', 500)
        temperature = input_data.get('temperature_c', 20)
        
        reasoning_parts = []
        
        # Zone suitability
        if crop in self.zone_crops.get(zone, []):
            reasoning_parts.append(f"Well-suited for {zone} zone")
        
        # Rainfall suitability
        if rainfall > 600 and crop in ['maize', 'beans', 'potatoes']:
            reasoning_parts.append("Adequate rainfall for water-intensive crops")
        elif rainfall < 300 and crop in ['sorghum', 'millet']:
            reasoning_parts.append("Drought-resistant variety suitable for low rainfall")
        
        # Temperature suitability
        if 15 <= temperature <= 25 and crop in ['maize', 'beans', 'potatoes']:
            reasoning_parts.append("Optimal temperature range")
        elif temperature > 25 and crop in ['cashew_nuts', 'mangoes']:
            reasoning_parts.append("Warm climate suitable")
        
        # Default reasoning
        if not reasoning_parts:
            reasoning_parts.append("Suitable for current conditions")
        
        return "; ".join(reasoning_parts)
    
    def _estimate_yield(self, crop: str, input_data: Dict) -> float:
        """Estimate expected yield for crop"""
        base_yields = {
            'maize': 2.5, 'beans': 1.2, 'potatoes': 8.0, 'kale': 15.0,
            'cabbage': 20.0, 'carrots': 12.0, 'tea': 3.0, 'coffee': 2.0,
            'cashew_nuts': 1.5, 'coconuts': 4.0, 'mangoes': 6.0, 'rice': 3.5,
            'sesame': 1.0, 'sorghum': 1.8, 'millet': 1.5, 'cowpeas': 0.8
        }
        
        base_yield = base_yields.get(crop, 2.0)
        
        # Adjust based on conditions
        rainfall_factor = min(input_data.get('rainfall_mm', 500) / 500, 1.2)
        fertilizer_factor = 1.3 if input_data.get('fertilizer_use', 0) else 1.0
        irrigation_factor = 1.2 if input_data.get('irrigation_available', 0) else 1.0
        
        estimated_yield = base_yield * rainfall_factor * fertilizer_factor * irrigation_factor
        
        return round(estimated_yield, 2)
    
    def _get_market_outlook(self, crop: str) -> str:
        """Get market outlook for crop"""
        market_outlooks = {
            'maize': 'Stable demand, good prices expected',
            'beans': 'Increasing demand, favorable prices',
            'potatoes': 'High demand, prices rising',
            'kale': 'Consistent demand, stable prices',
            'sorghum': 'Growing demand for drought-resistant crops',
            'millet': 'Increasing health-conscious demand',
            'rice': 'Strong demand, import-dependent',
            'coffee': 'International market, price volatility',
            'tea': 'Stable export market, good prices'
        }
        
        return market_outlooks.get(crop, 'Market conditions favorable')

def main():
    """Main training pipeline"""
    logger.info("🌾 FAHAMU SHAMBA - AI MODEL TRAINING PIPELINE")
    logger.info("=" * 60)
    
    # Initialize model
    model = CropRecommendationModel()
    
    # Try to load existing model
    if model.load_model():
        logger.info("✅ Existing model loaded successfully")
    else:
        logger.info("🔄 Training new model...")
        
        # Load historical data
        df = model.load_historical_data()
        
        # Preprocess data
        X, y = model.preprocess_data(df)
        
        # Train model
        training_info = model.train_model(X, y)
        
        logger.info(f"✅ Model trained successfully!")
        logger.info(f"   Model Type: {training_info['model_type']}")
        logger.info(f"   CV Score: {training_info['cv_score']:.3f}")
        logger.info(f"   Features: {training_info['features_count']}")
        logger.info(f"   Crops: {training_info['crops_count']}")
        
        # Save model
        model.save_model()
    
    # Test prediction
    logger.info("\n🧪 Testing model predictions...")
    
    test_input = {
        'county': 'nairobi',
        'rainfall_mm': 800,
        'temperature_c': 18,
        'humidity_percent': 65,
        'soil_ph': 6.5,
        'soil_moisture_percent': 45,
        'nitrogen_mg_kg': 40,
        'phosphorus_mg_kg': 25,
        'potassium_mg_kg': 35,
        'organic_matter_percent': 2.5,
        'land_size_acres': 2.0,
        'irrigation_available': 1,
        'fertilizer_use': 1,
        'month': 3
    }
    
    prediction = model.predict_crops(test_input)
    
    logger.info(f"🎯 Top Recommendation: {prediction['top_recommendation']['crop']}")
    logger.info(f"   Confidence: {prediction['top_recommendation']['confidence']}%")
    logger.info(f"   Reasoning: {prediction['top_recommendation']['reasoning']}")
    logger.info(f"   Expected Yield: {prediction['top_recommendation']['expected_yield']} tons/acre")
    
    logger.info("\n🏁 Training pipeline complete!")

if __name__ == '__main__':
    main()
