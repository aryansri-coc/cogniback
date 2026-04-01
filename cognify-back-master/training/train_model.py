"""
Health Drift Engine - Training Pipeline
Train calibration parameters on synthetic cohort
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import json
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from data.synthetic_generator import SyntheticDataGenerator
from preprocessing.parser import HealthDataParser
from preprocessing.demographic_normalizer import DemographicNormalizer
from preprocessing.rolling_features import RollingFeaturesComputer
from models.slope_estimator import SlopeEstimator
from models.domain_dispatcher import DomainDispatcher
from models.hazard_mapper import HazardMapper
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger()


class DriftEngineTrainer:
    """Train calibration parameters for the drift detection engine"""
    
    def __init__(self):
        self.config = get_config()
        self.generator = SyntheticDataGenerator()
        self.normalizer = DemographicNormalizer()
        self.rolling_computer = RollingFeaturesComputer()
        self.slope_estimator = SlopeEstimator()
        self.dispatcher = DomainDispatcher()
        self.hazard_mapper = HazardMapper()
        
        # To be trained
        self.calibration_model = None
        self.scaler = None
        self.optimal_betas = {}
        self.classification_thresholds = {}
    
    def generate_training_data(
        self,
        n_healthy: int = 50,
        n_declining: int = 20,
        duration_days: int = 365
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate synthetic training cohort
        
        Returns:
            (healthy_df, declining_df)
        """
        logger.info(
            "Generating training data",
            n_healthy=n_healthy,
            n_declining=n_declining
        )
        
        healthy_df, declining_df = self.generator.generate_cohort(
            n_healthy=n_healthy,
            n_declining=n_declining,
            duration_days=duration_days
        )
        
        return healthy_df, declining_df
    
    def process_user_data(
        self,
        user_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Process single user's data through full pipeline
        
        Args:
            user_df: Raw user data with age, sex columns
            
        Returns:
            Processed DataFrame with drifts computed
        """
        age = user_df['age'].iloc[0]
        sex = user_df['sex'].iloc[0]
        
        # Get numeric features
        numeric_features = [
            'hrvSdnnMs', 'heartRateAvg', 'gaitSpeedMs', 'steps',
            'bloodOxygenAvg', 'deepSleepHours', 'remSleepHours',
            'reactionTimeMs', 'memoryScore'
        ]
        
        available_features = [f for f in numeric_features if f in user_df.columns]
        
        # Normalize
        normalized_df = self.normalizer.normalize_dataframe(
            user_df,
            age=age,
            sex=sex,
            features_to_normalize=available_features
        )
        
        # Compute slopes
        slopes_df = self.rolling_computer.compute_all_slopes(
            normalized_df,
            features=available_features
        )
        
        # Compute drifts
        drifts_df = self.slope_estimator.compute_all_drifts(
            slopes_df,
            features=available_features,
            age=age,
            sex=sex
        )
        
        return drifts_df
    
    def extract_training_features(
        self,
        processed_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Extract features for training from processed user data
        
        Returns:
            Dictionary of training features
        """
        # Get latest drift values
        feature_drifts = self.dispatcher.extract_latest_feature_drifts(
            processed_df,
            drift_type='long'
        )
        
        # Compute domain drifts
        domain_drifts = self.dispatcher.compute_all_domain_drifts(feature_drifts)
        
        # Get accelerations (short - long drift)
        feature_drifts_short = self.dispatcher.extract_latest_feature_drifts(
            processed_df,
            drift_type='short'
        )
        
        accelerations = {}
        for feature in feature_drifts:
            if feature in feature_drifts_short:
                accel = feature_drifts_short[feature] - feature_drifts[feature]
                accelerations[f'{feature}_accel'] = accel
        
        # Combine into feature vector
        training_features = {
            **domain_drifts,
            **accelerations
        }
        
        return training_features
    
    def train_calibration_model(
        self,
        healthy_df: pd.DataFrame,
        declining_df: pd.DataFrame
    ) -> Dict[str, any]:
        """
        Train logistic regression calibration layer
        
        Args:
            healthy_df: Healthy users
            declining_df: Declining users
            
        Returns:
            Trained model parameters
        """
        logger.info("Training calibration model")
        
        X_train = []
        y_train = []
        
        # Process healthy users
        for user_id in healthy_df['userId'].unique():
            user_data = healthy_df[healthy_df['userId'] == user_id]
            
            try:
                processed = self.process_user_data(user_data)
                features = self.extract_training_features(processed)
                
                # Convert to feature vector
                feature_vec = [
                    features.get('Neuro', 0),
                    features.get('Cardio', 0),
                    features.get('Frailty', 0),
                    features.get('gaitSpeedMs_accel', 0),
                    features.get('hrvSdnnMs_accel', 0)
                ]
                
                X_train.append(feature_vec)
                y_train.append(0)  # Healthy
            except Exception as e:
                logger.warning(f"Failed to process user {user_id}: {e}")
        
        # Process declining users
        for user_id in declining_df['userId'].unique():
            user_data = declining_df[declining_df['userId'] == user_id]
            
            try:
                processed = self.process_user_data(user_data)
                features = self.extract_training_features(processed)
                
                feature_vec = [
                    features.get('Neuro', 0),
                    features.get('Cardio', 0),
                    features.get('Frailty', 0),
                    features.get('gaitSpeedMs_accel', 0),
                    features.get('hrvSdnnMs_accel', 0)
                ]
                
                X_train.append(feature_vec)
                y_train.append(1)  # Declining
            except Exception as e:
                logger.warning(f"Failed to process user {user_id}: {e}")
        
        # Train model
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        
        logger.info(f"Training on {len(X_train)} samples")
        
        # Standardize features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_train)
        
        # Train logistic regression
        self.calibration_model = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced'
        )
        self.calibration_model.fit(X_scaled, y_train)
        
        # Get coefficients
        coefficients = {
            'intercept': float(self.calibration_model.intercept_[0]),
            'coef_neuro': float(self.calibration_model.coef_[0][0]),
            'coef_cardio': float(self.calibration_model.coef_[0][1]),
            'coef_frailty': float(self.calibration_model.coef_[0][2]),
            'coef_gait_accel': float(self.calibration_model.coef_[0][3]),
            'coef_hrv_accel': float(self.calibration_model.coef_[0][4])
        }
        
        logger.info("Calibration model trained", coefficients=coefficients)
        
        return coefficients
    
    def optimize_hazard_betas(
        self,
        healthy_df: pd.DataFrame,
        declining_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Optimize beta parameters for hazard mapping
        
        Returns:
            Optimized beta values
        """
        logger.info("Optimizing hazard beta parameters")
        
        # Extract domain drifts and outcomes for each domain
        domain_data = {'Neuro': [], 'Cardio': [], 'Frailty': []}
        outcomes = []
        
        # Process all users
        all_users = pd.concat([healthy_df, declining_df])
        
        for user_id in all_users['userId'].unique():
            user_data = all_users[all_users['userId'] == user_id]
            label = user_data['label'].iloc[0]
            
            try:
                processed = self.process_user_data(user_data)
                features = self.extract_training_features(processed)
                
                domain_data['Neuro'].append(features.get('Neuro', 0))
                domain_data['Cardio'].append(features.get('Cardio', 0))
                domain_data['Frailty'].append(features.get('Frailty', 0))
                
                outcomes.append(1 if label == 'declining' else 0)
            except:
                pass
        
        outcomes = np.array(outcomes)
        
        # Optimize beta for each domain
        optimal_betas = {}
        for domain in ['Neuro', 'Cardio', 'Frailty']:
            drifts = np.array(domain_data[domain])
            
            beta = self.hazard_mapper.calibrate_beta(
                drifts,
                outcomes,
                domain,
                target_auc=0.85
            )
            
            optimal_betas[domain] = beta
        
        self.optimal_betas = optimal_betas
        logger.info("Beta optimization complete", betas=optimal_betas)
        
        return optimal_betas
    
    def save_calibration_params(self, output_path: str = "models/calibration_params.json"):
        """Save trained parameters to file"""
        params = {
            'calibration_model': {
                'intercept': float(self.calibration_model.intercept_[0]),
                'coefficients': self.calibration_model.coef_[0].tolist()
            },
            'scaler': {
                'mean': self.scaler.mean_.tolist(),
                'scale': self.scaler.scale_.tolist()
            },
            'optimal_betas': self.optimal_betas,
            'classification_thresholds': self.classification_thresholds
        }
        
        with open(output_path, 'w') as f:
            json.dump(params, f, indent=2)
        
        logger.info(f"Calibration parameters saved to {output_path}")


if __name__ == "__main__":
    # Train model
    trainer = DriftEngineTrainer()
    
    # Generate data
    healthy, declining = trainer.generate_training_data(
        n_healthy=15,
        n_declining=10
    )
    
    # Train
    coefficients = trainer.train_calibration_model(healthy, declining)
    betas = trainer.optimize_hazard_betas(healthy, declining)
    
    # Save
    trainer.save_calibration_params()
    
    print("Training complete!")
    print(f"Coefficients: {coefficients}")
    print(f"Optimal betas: {betas}")
