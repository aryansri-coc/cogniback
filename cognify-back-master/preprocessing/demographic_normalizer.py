"""
Health Drift Engine - Demographic Normalizer
Z-score normalization based on age/sex/BMI cohorts
"""

import pandas as pd
import numpy as np
import json
from typing import Dict, Tuple, Optional
from utils.logger import get_logger

logger = get_logger()


class DemographicNormalizer:
    """Normalize features based on demographic-specific baselines"""
    
    def __init__(self, demographics_path: str = "data/cohort_demographics.json"):
        self.demographics = self._load_demographics(demographics_path)
        
    def _load_demographics(self, path: str) -> Dict:
        """Load demographic statistics"""
        with open(path, 'r') as f:
            demographics = json.load(f)
        logger.info("Loaded demographic statistics", path=path)
        return demographics
    
    def _get_age_bin(self, age: int) -> str:
        """Map age to demographic bin"""
        if age < 30:
            return "18-30"
        elif age < 50:
            return "40-50"
        else:
            return "60-70"
    
    def get_cohort_stats(
        self,
        feature: str,
        age: int,
        sex: str
    ) -> Tuple[float, float, float]:
        """
        Get cohort statistics for a feature
        
        Args:
            feature: Feature name
            age: User age
            sex: User sex ('male' or 'female')
            
        Returns:
            (mean, std, annual_slope) tuple
        """
        age_bin = self._get_age_bin(age)
        
        try:
            stats = self.demographics['age_bins'][age_bin][sex][feature]
            return stats['mean'], stats['std'], stats['annual_slope']
        except KeyError:
            logger.warning(
                "Feature not found in demographics, using defaults",
                feature=feature,
                age_bin=age_bin,
                sex=sex
            )
            # Return reasonable defaults
            return 0.0, 1.0, 0.0
    
    def normalize_feature(
        self,
        values: pd.Series,
        feature: str,
        age: int,
        sex: str
    ) -> pd.Series:
        """
        Compute Z-scores for a feature
        
        Args:
            values: Raw feature values
            feature: Feature name
            age: User age
            sex: User sex
            
        Returns:
            Z-scored values
        """
        mean, std, _ = self.get_cohort_stats(feature, age, sex)
        
        # Z-score transformation
        z_scores = (values - mean) / std
        
        return z_scores
    
    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        age: int,
        sex: str,
        features_to_normalize: Optional[list] = None
    ) -> pd.DataFrame:
        """
        Normalize all numeric features in DataFrame
        
        Args:
            df: DataFrame with raw values
            age: User age
            sex: User sex
            features_to_normalize: List of features to normalize (None = all numeric)
            
        Returns:
            DataFrame with z-scored features and '_raw' columns preserved
        """
        logger.info(
            "Normalizing features",
            age=age,
            sex=sex,
            rows=len(df)
        )
        
        normalized_df = df.copy()
        
        # Determine which features to normalize
        if features_to_normalize is None:
            features_to_normalize = df.select_dtypes(include=[np.number]).columns
            features_to_normalize = [
                f for f in features_to_normalize 
                if f not in ['userId', 'age', 'sex']
            ]
        
        # Normalize each feature
        for feature in features_to_normalize:
            if feature in df.columns:
                # Store raw values
                normalized_df[f'{feature}_raw'] = df[feature]
                
                # Compute z-scores
                normalized_df[feature] = self.normalize_feature(
                    df[feature],
                    feature,
                    age,
                    sex
                )
        
        logger.info("Normalization complete", features_normalized=len(features_to_normalize))
        
        return normalized_df
    
    def denormalize_feature(
        self,
        z_scores: pd.Series,
        feature: str,
        age: int,
        sex: str
    ) -> pd.Series:
        """
        Convert Z-scores back to raw values
        
        Args:
            z_scores: Z-scored values
            feature: Feature name
            age: User age
            sex: User sex
            
        Returns:
            Raw values
        """
        mean, std, _ = self.get_cohort_stats(feature, age, sex)
        raw_values = (z_scores * std) + mean
        return raw_values


if __name__ == "__main__":
    # Test normalizer
    import pandas as pd
    
    # Sample data
    data = {
        'timestamp': pd.date_range('2024-01-01', periods=10),
        'hrvSdnnMs': [45, 47, 46, 48, 44, 46, 47, 45, 46, 48],
        'gaitSpeedMs': [1.25, 1.27, 1.26, 1.24, 1.25, 1.26, 1.25, 1.27, 1.26, 1.25]
    }
    df = pd.DataFrame(data)
    
    normalizer = DemographicNormalizer()
    normalized_df = normalizer.normalize_dataframe(df, age=55, sex='male')
    
    print("Original:")
    print(df[['hrvSdnnMs', 'gaitSpeedMs']].head())
    print("\nNormalized:")
    print(normalized_df[['hrvSdnnMs', 'gaitSpeedMs']].head())
