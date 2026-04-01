"""
Health Drift Engine - Training Pipeline (Refactored)
Train logistic regression calibration on hazard-transformed domain risks
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import json
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, classification_report
from data.synthetic_generator import SyntheticDataGenerator
from preprocessing.parser import HealthDataParser
from preprocessing.demographic_normalizer import DemographicNormalizer
from preprocessing.rolling_features import RollingFeaturesComputer
from models.slope_estimator import SlopeEstimator
from models.domain_dispatcher import DomainDispatcher
from models.hazard_mapper import HazardMapper
from utils.logger import get_logger
from utils.config import get_config
from utils.constants import HAZARD_BETAS

logger = get_logger()


class DriftEngineTrainer:
    """
    Train calibration layer for drift detection engine
    
    Architecture:
        1. Compute domain drifts from feature drifts
        2. Apply hazard transform with FIXED betas → domain risks
        3. Train logistic regression: [NeuroRisk, CardioRisk, FrailtyRisk] → decline_prob
        4. StabilityIndex computed separately via weighted fusion (no training)
    """
    
    def __init__(self):
        self.config = get_config()
        self.generator = SyntheticDataGenerator()
        self.normalizer = DemographicNormalizer()
        self.rolling_computer = RollingFeaturesComputer()
        self.slope_estimator = SlopeEstimator()
        self.dispatcher = DomainDispatcher()
        self.hazard_mapper = HazardMapper(beta_values=HAZARD_BETAS)  # Fixed betas
        
        # To be trained
        self.calibration_model = None
        self.scaler = None
    
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
            'reactionTimeMs', 'memoryScore', 'stepCadence',
            'walkingAsymmetry', 'awakenings', 'sleepLatencyMinutes',
            'totalSleepHours'
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
    
    def extract_domain_risks(
        self,
        processed_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Extract domain risks (hazard-transformed) from processed data
        
        Pipeline:
            1. Get feature drifts (latest values)
            2. Compute domain drifts (weighted aggregation)
            3. Apply hazard transform → domain risks
        
        Returns:
            Dictionary with NeuroRisk, CardioRisk, FrailtyRisk
        """
        # Get latest feature drifts (long-term)
        feature_drifts = self.dispatcher.extract_latest_feature_drifts(
            processed_df,
            drift_type='long'
        )
        
        # Compute domain drifts (weighted sum)
        domain_drifts = self.dispatcher.compute_all_domain_drifts(feature_drifts)
        
        # Apply hazard transform (fixed betas)
        domain_risks = self.hazard_mapper.compute_all_domain_risks(domain_drifts)
        
        return domain_risks
    
    def train_calibration_model(
        self,
        healthy_df: pd.DataFrame,
        declining_df: pd.DataFrame
    ) -> Dict[str, any]:
        """
        Train logistic regression on domain risks
        
        Input features: [NeuroRisk, CardioRisk, FrailtyRisk]
        Output: Decline probability [0, 1]
        
        Args:
            healthy_df: Healthy users
            declining_df: Declining users
            
        Returns:
            Training metrics and model parameters
        """
        logger.info("Training calibration model on domain risks")
        
        X_train = []
        y_train = []
        
        # Process healthy users
        logger.info("Processing healthy users")
        for user_id in healthy_df['userId'].unique():
            user_data = healthy_df[healthy_df['userId'] == user_id]
            
            try:
                processed = self.process_user_data(user_data)
                domain_risks = self.extract_domain_risks(processed)
                
                # Feature vector: [NeuroRisk, CardioRisk, FrailtyRisk]
                feature_vec = [
                    domain_risks.get('Neuro', 0.0),
                    domain_risks.get('Cardio', 0.0),
                    domain_risks.get('Frailty', 0.0)
                ]
                
                X_train.append(feature_vec)
                y_train.append(0)  # Healthy
            except Exception as e:
                logger.warning(f"Failed to process user {user_id}: {e}")
        
        # Process declining users
        logger.info("Processing declining users")
        for user_id in declining_df['userId'].unique():
            user_data = declining_df[declining_df['userId'] == user_id]
            
            try:
                processed = self.process_user_data(user_data)
                domain_risks = self.extract_domain_risks(processed)
                
                feature_vec = [
                    domain_risks.get('Neuro', 0.0),
                    domain_risks.get('Cardio', 0.0),
                    domain_risks.get('Frailty', 0.0)
                ]
                
                X_train.append(feature_vec)
                y_train.append(1)  # Declining
            except Exception as e:
                logger.warning(f"Failed to process user {user_id}: {e}")
        
        # Convert to arrays
        X_train = np.array(X_train)
        y_train = np.array(y_train)
        
        logger.info(
            "Training data prepared",
            n_samples=len(X_train),
            n_healthy=int(np.sum(y_train == 0)),
            n_declining=int(np.sum(y_train == 1))
        )
        
        # Standardize features (important for logistic regression)
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_train)
        
        # Train logistic regression
        self.calibration_model = LogisticRegression(
            random_state=42,
            max_iter=1000,
            class_weight='balanced'  # Handle class imbalance
        )
        self.calibration_model.fit(X_scaled, y_train)
        
        # Evaluate on training set
        y_pred_proba = self.calibration_model.predict_proba(X_scaled)[:, 1]
        y_pred = self.calibration_model.predict(X_scaled)
        
        train_auc = roc_auc_score(y_train, y_pred_proba)
        
        logger.info(
            "Calibration model trained",
            train_auc=f"{train_auc:.3f}"
        )
        
        # Print classification report
        print("\nClassification Report:")
        print(classification_report(y_train, y_pred, target_names=['Healthy', 'Declining']))
        
        # Get model parameters
        coefficients = {
            'intercept': float(self.calibration_model.intercept_[0]),
            'coef_neuro': float(self.calibration_model.coef_[0][0]),
            'coef_cardio': float(self.calibration_model.coef_[0][1]),
            'coef_frailty': float(self.calibration_model.coef_[0][2])
        }
        
        logger.info("Model coefficients", **coefficients)
        
        return {
            'train_auc': train_auc,
            'coefficients': coefficients,
            'n_samples': len(X_train)
        }
    
    def save_calibration_params(
        self,
        output_path: str = "models/calibration_params.json"
    ):
        """
        Save trained parameters to file
        
        Saves:
            - Logistic regression coefficients
            - Scaler parameters
            - Fixed hazard betas (for reference)
        """
        params = {
            'model_version': '1.0',
            'model_type': 'logistic_regression',
            'calibration_model': {
                'intercept': float(self.calibration_model.intercept_[0]),
                'coefficients': {
                    'neuro': float(self.calibration_model.coef_[0][0]),
                    'cardio': float(self.calibration_model.coef_[0][1]),
                    'frailty': float(self.calibration_model.coef_[0][2])
                }
            },
            'scaler': {
                'mean': self.scaler.mean_.tolist(),
                'scale': self.scaler.scale_.tolist()
            },
            'hazard_betas': HAZARD_BETAS,  # Fixed, not trained
            'feature_order': ['NeuroRisk', 'CardioRisk', 'FrailtyRisk']
        }
        
        with open(output_path, 'w') as f:
            json.dump(params, f, indent=2)
        
        logger.info(f"Calibration parameters saved to {output_path}")
    
    def load_calibration_params(
        self,
        input_path: str = "models/calibration_params.json"
    ):
        """Load pre-trained calibration parameters"""
        with open(input_path, 'r') as f:
            params = json.load(f)
        
        # Reconstruct scaler
        self.scaler = StandardScaler()
        self.scaler.mean_ = np.array(params['scaler']['mean'])
        self.scaler.scale_ = np.array(params['scaler']['scale'])
        
        # Reconstruct logistic regression model
        self.calibration_model = LogisticRegression()
        self.calibration_model.intercept_ = np.array([params['calibration_model']['intercept']])
        self.calibration_model.coef_ = np.array([[
            params['calibration_model']['coefficients']['neuro'],
            params['calibration_model']['coefficients']['cardio'],
            params['calibration_model']['coefficients']['frailty']
        ]])
        self.calibration_model.classes_ = np.array([0, 1])
        
        logger.info(f"Calibration parameters loaded from {input_path}")


if __name__ == "__main__":
    # Train model
    trainer = DriftEngineTrainer()
    
    # Generate data
    print("Generating synthetic cohort...")
    healthy, declining = trainer.generate_training_data(
        n_healthy=50,
        n_declining=20,
        duration_days=365
    )
    
    print(f"Generated {len(healthy['userId'].unique())} healthy users")
    print(f"Generated {len(declining['userId'].unique())} declining users")
    
    # Train
    print("\nTraining calibration model...")
    metrics = trainer.train_calibration_model(healthy, declining)
    
    # Save
    print("\nSaving parameters...")
    trainer.save_calibration_params()
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"Training AUC: {metrics['train_auc']:.3f}")
    print(f"Samples: {metrics['n_samples']}")
    print(f"\nCoefficients:")
    for name, value in metrics['coefficients'].items():
        print(f"  {name}: {value:.4f}")
    print("\nCalibration parameters saved to: models/calibration_params.json")
