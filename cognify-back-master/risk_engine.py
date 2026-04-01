"""
Health Drift Engine - Risk Engine (Enhanced with Error Handling)
Clean inference pipeline: Drifts → Hazard → Risks → Probabilities
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import json
from preprocessing.parser import HealthDataParser
from preprocessing.demographic_normalizer import DemographicNormalizer
from preprocessing.rolling_features import RollingFeaturesComputer
from preprocessing.anomaly_detector import AnomalyDetector
from models.slope_estimator import SlopeEstimator, MultiScaleDriftAnalyzer
from models.domain_dispatcher import DomainDispatcher
from models.hazard_mapper import HazardMapper
from models.state_space import StateSpaceModel
from utils.logger import get_logger
from utils.config import get_config
from utils.constants import HAZARD_BETAS, DOMAIN_FUSION_WEIGHTS

logger = get_logger()


class RiskEngine:
    """
    Unified risk assessment engine
    
    Clean Architecture:
        1. Parse & preprocess data
        2. Normalize to z-scores
        3. Compute slopes & drifts
        4. Aggregate to domain drifts
        5. Hazard transform → domain risks (FIXED betas)
        6. Compute StabilityIndex (weighted fusion, NO training)
        7. Logistic regression → DeclineProbability (TRAINED)
        8. Detect anomalies (using accelerations)
    """
    
    def __init__(self, calibration_path: str = "models/calibration_params.json"):
        self.config = get_config()
        
        # Initialize components
        self.parser = HealthDataParser()
        self.normalizer = DemographicNormalizer()
        self.rolling_computer = RollingFeaturesComputer()
        self.slope_estimator = SlopeEstimator()
        self.dispatcher = DomainDispatcher()
        self.hazard_mapper = HazardMapper(beta_values=HAZARD_BETAS)  # Fixed
        self.state_space = StateSpaceModel(use_kalman=self.config.use_kalman_filter)
        self.anomaly_detector = AnomalyDetector()
        self.drift_analyzer = MultiScaleDriftAnalyzer()
        
        # Load calibration parameters
        self._load_calibration(calibration_path)
        
        logger.info("Risk engine initialized")
    
    def _load_calibration(self, path: str):
        """Load trained logistic regression parameters"""
        try:
            with open(path, 'r') as f:
                params = json.load(f)
            
            # Extract parameters
            self.logistic_intercept = params['calibration_model']['intercept']
            self.logistic_coefs = np.array([
                params['calibration_model']['coefficients']['neuro'],
                params['calibration_model']['coefficients']['cardio'],
                params['calibration_model']['coefficients']['frailty']
            ])
            self.scaler_mean = np.array(params['scaler']['mean'])
            self.scaler_scale = np.array(params['scaler']['scale'])
            
            logger.info("Calibration parameters loaded", path=path)
        except FileNotFoundError:
            logger.warning(f"Calibration file not found: {path}, using defaults")
            self.logistic_intercept = 0.0
            self.logistic_coefs = np.array([1.0, 1.0, 1.0])
            self.scaler_mean = np.array([0.0, 0.0, 0.0])
            self.scaler_scale = np.array([1.0, 1.0, 1.0])
        except KeyError as e:
            logger.error(f"Invalid calibration file format: {e}")
            raise ValueError(f"Calibration file missing required field: {e}")
    
    def _get_available_features(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of features actually available in the dataframe
        
        Args:
            df: DataFrame to check
            
        Returns:
            List of available feature names
        """
        expected_features = [
            'hrvSdnnMs', 'heartRateAvg', 'gaitSpeedMs', 'steps',
            'bloodOxygenAvg', 'deepSleepHours', 'remSleepHours',
            'reactionTimeMs', 'memoryScore', 'stepCadence',
            'walkingAsymmetry', 'awakenings', 'sleepLatencyMinutes',
            'totalSleepHours'
        ]
        
        available = [f for f in expected_features if f in df.columns]
        
        if len(available) == 0:
            logger.warning("No expected features found in dataframe")
            logger.debug(f"Available columns: {list(df.columns)}")
        else:
            logger.info(f"Found {len(available)}/{len(expected_features)} features")
        
        return available
    
    def process_user_timeseries(
        self,
        df: pd.DataFrame,
        age: int,
        sex: str
    ) -> pd.DataFrame:
        """
        Process user time series through full pipeline
        
        Args:
            df: Clean daily time series
            age: User age
            sex: User sex
            
        Returns:
            Fully processed DataFrame with all computed features
        """
        logger.info("Processing user time series", age=age, sex=sex, days=len(df))
        
        # Validate minimum data requirements
        if len(df) < self.config.min_data_points_for_slope:
            logger.warning(
                f"Time series has only {len(df)} days, " 
                f"minimum {self.config.min_data_points_for_slope} recommended"
            )
        
        # Get available features dynamically
        available_features = self._get_available_features(df)
        
        if not available_features:
            raise ValueError("No valid features found in input data")
        
        try:
            # Step 1: Optional Kalman smoothing
            if self.config.use_kalman_filter:
                logger.debug("Applying Kalman smoothing")
                df = self.state_space.smooth_dataframe(df, available_features)
            
            # Step 2: Normalize to z-scores
            logger.debug("Normalizing features to z-scores")
            df_normalized = self.normalizer.normalize_dataframe(
                df,
                age=age,
                sex=sex,
                features_to_normalize=available_features
            )
            
            # Step 3: Compute slopes
            logger.debug("Computing rolling slopes")
            df_slopes = self.rolling_computer.compute_all_slopes(
                df_normalized,
                features=available_features
            )
            
            # Step 4: Compute drifts
            logger.debug("Computing drift signals")
            df_drifts = self.slope_estimator.compute_all_drifts(
                df_slopes,
                features=available_features,
                age=age,
                sex=sex
            )
            
            # Step 5: Detect anomalies (uses accelerations)
            logger.debug("Detecting anomalies")
            expected_slopes = {}
            for feature in available_features:
                _, _, slope = self.normalizer.get_cohort_stats(feature, age, sex)
                expected_slopes[feature] = slope
            
            df_final = self.anomaly_detector.detect_all_anomalies(
                df_drifts,
                features=available_features,
                age=age,
                sex=sex,
                expected_slopes=expected_slopes
            )
            
            logger.info("Time series processing complete")
            
            return df_final
            
        except Exception as e:
            logger.error(f"Error during time series processing: {e}")
            raise RuntimeError(f"Time series processing failed: {e}") from e
    
    def compute_domain_risks(
        self,
        processed_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Compute domain risks from processed data
        
        Pipeline:
            Feature drifts → Domain drifts → Hazard transform → Domain risks
        
        Returns:
            {NeuroRisk, CardioRisk, FrailtyRisk}
        """
        try:
            # Extract latest feature drifts
            feature_drifts = self.dispatcher.extract_latest_feature_drifts(
                processed_df,
                drift_type='long'
            )
            
            if not feature_drifts:
                logger.warning("No feature drifts available, returning zero risks")
                return {'Neuro': 0.0, 'Cardio': 0.0, 'Frailty': 0.0}
            
            # Compute domain drifts (weighted aggregation)
            domain_drifts = self.dispatcher.compute_all_domain_drifts(feature_drifts)
            
            # Apply hazard transform (fixed betas)
            domain_risks = self.hazard_mapper.compute_all_domain_risks(domain_drifts)
            
            logger.debug("Domain risks computed", risks=domain_risks)
            
            return domain_risks
            
        except Exception as e:
            logger.error(f"Error computing domain risks: {e}")
            # Return safe defaults
            return {'Neuro': 0.0, 'Cardio': 0.0, 'Frailty': 0.0}
    
    def compute_stability_index(
        self,
        domain_risks: Dict[str, float]
    ) -> float:
        """
        Compute StabilityIndex via weighted fusion
        
        Formula:
            TotalRisk = 0.4×Neuro + 0.35×Cardio + 0.25×Frailty
            StabilityIndex = 1 - TotalRisk
        
        This is NOT trained - uses fixed weights
        
        Returns:
            Stability index [0, 1]
        """
        total_risk = self.dispatcher.fuse_domain_risks(
            domain_risks,
            weights=DOMAIN_FUSION_WEIGHTS
        )
        
        stability_index = self.dispatcher.compute_stability_index(total_risk)
        
        # Ensure bounds
        stability_index = np.clip(stability_index, 0.0, 1.0)
        
        return float(stability_index)
    
    def compute_decline_probability(
        self,
        domain_risks: Dict[str, float]
    ) -> float:
        """
        Compute decline probability via trained logistic regression
        
        Input: [NeuroRisk, CardioRisk, FrailtyRisk]
        Output: DeclineProbability [0, 1]
        
        This is the ONLY trained component
        
        Returns:
            Decline probability
        """
        # Create feature vector
        X = np.array([
            domain_risks.get('Neuro', 0.0),
            domain_risks.get('Cardio', 0.0),
            domain_risks.get('Frailty', 0.0)
        ])
        
        # Check for invalid values
        if np.any(np.isnan(X)):
            logger.warning("NaN values in domain risks, using zeros")
            X = np.nan_to_num(X, nan=0.0)
        
        # Standardize (avoid division by zero)
        safe_scale = np.where(self.scaler_scale > 0, self.scaler_scale, 1.0)
        X_scaled = (X - self.scaler_mean) / safe_scale
        
        # Logistic regression: p = sigmoid(w^T x + b)
        logit = np.dot(self.logistic_coefs, X_scaled) + self.logistic_intercept
        
        # Clip logit to avoid overflow in exp
        logit = np.clip(logit, -20, 20)
        
        probability = 1 / (1 + np.exp(-logit))
        
        # Ensure bounds
        probability = np.clip(probability, 0.0, 1.0)
        
        return float(probability)
    
    def assess_risk(
        self,
        json_records: List[Dict],
        age: int,
        sex: str,
        user_id: str
    ) -> Dict:
        """
        Complete risk assessment pipeline
        
        Args:
            json_records: Raw health data (list of dicts)
            age: User age (years)
            sex: User sex ('male' or 'female')
            user_id: User identifier
            
        Returns:
            Comprehensive risk assessment dictionary
            
        Raises:
            ValueError: If input data is invalid
            RuntimeError: If assessment pipeline fails
        """
        logger.info("Starting risk assessment", user_id=user_id)
        
        # Validate inputs
        if not json_records:
            raise ValueError("Empty json_records provided")
        
        if age < 18 or age > 120:
            raise ValueError(f"Invalid age: {age}. Must be 18-120")
        
        if sex not in ['male', 'female']:
            raise ValueError(f"Invalid sex: {sex}. Must be 'male' or 'female'")
        
        try:
            # Parse and clean data
            logger.debug("Parsing JSON records")
            df = self.parser.parse_and_clean(json_records)
            
            # Process time series
            logger.debug("Processing time series")
            processed_df = self.process_user_timeseries(df, age, sex)
            
            # Compute domain risks (hazard-transformed)
            logger.debug("Computing domain risks")
            domain_risks = self.compute_domain_risks(processed_df)
            
            # Compute StabilityIndex (weighted fusion, not trained)
            logger.debug("Computing stability index")
            stability_index = self.compute_stability_index(domain_risks)
            
            # Compute DeclineProbability (trained logistic regression)
            logger.debug("Computing decline probability")
            decline_probability = self.compute_decline_probability(domain_risks)
            
            # Extract anomalies (uses accelerations for detection)
            logger.debug("Extracting anomalies")
            anomalies = self.anomaly_detector.summarize_anomalies(processed_df)
            
            # Get latest drifts for explainability
            feature_drifts = self.dispatcher.extract_latest_feature_drifts(
                processed_df,
                drift_type='long'
            )
            
            # Get domain-level drift breakdown
            domain_drifts = self.dispatcher.compute_all_domain_drifts(feature_drifts)
            
            # Get feature contributions for each domain
            domain_contributions = {}
            for domain in ['Neuro', 'Cardio', 'Frailty']:
                contributions = self.dispatcher.get_feature_contributions(
                    feature_drifts,
                    domain
                )
                domain_contributions[domain] = contributions
            
            result = {
                'user_id': user_id,
                'stability_index': float(stability_index),
                'decline_probability': float(decline_probability),
                'domain_risks': {k: float(v) for k, v in domain_risks.items()},
                'domain_drifts': {k: float(v) for k, v in domain_drifts.items()},
                'anomalies': anomalies,
                'domain_contributions': domain_contributions,
                'last_assessment_date': str(processed_df['timestamp'].max()),
                'data_days': len(df),
                'features_used': len(self._get_available_features(df))
            }
            
            logger.info(
                "Risk assessment complete",
                user_id=user_id,
                stability=f"{stability_index:.3f}",
                decline_prob=f"{decline_probability:.3f}",
                data_days=len(df)
            )
            
            return result
            
        except ValueError as e:
            logger.error(f"Validation error: {e}", user_id=user_id)
            raise
        except Exception as e:
            logger.error(f"Unexpected error during risk assessment: {e}", user_id=user_id)
            raise RuntimeError(f"Risk assessment failed for {user_id}: {e}") from e


if __name__ == "__main__":
    # Test risk engine
    from data.synthetic_generator import SyntheticDataGenerator
    
    print("Testing Risk Engine...")
    
    generator = SyntheticDataGenerator()
    
    # Generate test user
    df = generator.generate_declining_user(
        user_id="TEST001",
        age=60,
        sex="male",
        duration_days=365,
        decline_start_day=180,
        affected_domains=["Neuro"]
    )
    
    print(f"Generated {len(df)} days of data")
    print(f"Columns: {list(df.columns)}")
    
    # Convert to JSON format
    json_records = df.to_dict('records')
    print(f"Converted to {len(json_records)} JSON records")
    
    # Run risk assessment
    try:
        engine = RiskEngine()
        result = engine.assess_risk(
            json_records=json_records,
            age=60,
            sex="male",
            user_id="TEST001"
        )
        
        print("\n" + "="*60)
        print("RISK ASSESSMENT RESULT")
        print("="*60)
        print(f"Stability Index: {result['stability_index']:.3f}")
        print(f"Decline Probability: {result['decline_probability']:.3f}")
        print(f"\nDomain Risks:")
        for domain, risk in result['domain_risks'].items():
            print(f"  {domain}: {risk:.3f}")
        print(f"\nData Quality:")
        print(f"  Days analyzed: {result['data_days']}")
        print(f"  Features used: {result['features_used']}")
        print(f"  Anomalies detected: {len(result['anomalies'])}")
        
        print("\n✓ Test passed!")
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
