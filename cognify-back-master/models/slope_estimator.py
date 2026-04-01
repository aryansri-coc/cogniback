"""
Health Drift Engine - Slope Estimator
Estimates observed slopes and computes drift from expected slopes
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from data.feature_mappings import get_feature_spec, normalize_drift_direction
from preprocessing.demographic_normalizer import DemographicNormalizer
from utils.logger import get_logger

logger = get_logger()


class SlopeEstimator:
    """Estimate temporal slopes and compute drift from demographic baselines"""
    
    def __init__(self):
        self.normalizer = DemographicNormalizer()
    
    def compute_drift(
        self,
        observed_slope: float,
        expected_slope: float,
        feature_name: str
    ) -> float:
        """
        Compute drift: deviation from expected slope, normalized by direction
        
        Args:
            observed_slope: Observed slope from data
            expected_slope: Expected slope from demographics
            feature_name: Name of feature
            
        Returns:
            Drift value (positive = worse than expected)
        """
        # Raw drift
        raw_drift = observed_slope - expected_slope
        
        # Normalize so positive = worse
        normalized_drift = normalize_drift_direction(raw_drift, feature_name)
        
        return normalized_drift
    
    def compute_feature_drift(
        self,
        df: pd.DataFrame,
        feature: str,
        age: int,
        sex: str,
        slope_type: str = 'long'
    ) -> pd.Series:
        """
        Compute drift for a single feature across time
        
        Args:
            df: DataFrame with slope columns
            feature: Feature name
            age: User age
            sex: User sex
            slope_type: 'long' or 'short' term slope
            
        Returns:
            Time series of drift values
        """
        slope_col = f'{feature}_slope_{slope_type}'
        
        if slope_col not in df.columns:
            logger.warning(f"Slope column {slope_col} not found")
            return pd.Series(np.nan, index=df.index)
        
        # Get expected slope from demographics
        _, _, expected_slope = self.normalizer.get_cohort_stats(feature, age, sex)
        
        # Compute drift for each time point
        drift = df[slope_col].apply(
            lambda obs_slope: self.compute_drift(obs_slope, expected_slope, feature)
            if not np.isnan(obs_slope) else np.nan
        )
        
        return drift
    
    def compute_all_drifts(
        self,
        df: pd.DataFrame,
        features: list,
        age: int,
        sex: str
    ) -> pd.DataFrame:
        """
        Compute drift for all features
        
        Args:
            df: DataFrame with slope columns
            features: List of features
            age: User age
            sex: User sex
            
        Returns:
            DataFrame with drift columns added
        """
        logger.info("Computing drift values", features=len(features))
        
        result_df = df.copy()
        
        for feature in features:
            if feature in df.columns:
                # Long-term drift
                drift_long = self.compute_feature_drift(
                    df, feature, age, sex, slope_type='long'
                )
                result_df[f'{feature}_drift_long'] = drift_long
                
                # Short-term drift
                drift_short = self.compute_feature_drift(
                    df, feature, age, sex, slope_type='short'
                )
                result_df[f'{feature}_drift_short'] = drift_short
        
        logger.info("Drift computation complete")
        
        return result_df
    
    def get_latest_drift(
        self,
        df: pd.DataFrame,
        feature: str,
        slope_type: str = 'long'
    ) -> float:
        """
        Get most recent drift value for a feature
        
        Args:
            df: DataFrame with drift columns
            feature: Feature name
            slope_type: 'long' or 'short'
            
        Returns:
            Latest drift value
        """
        drift_col = f'{feature}_drift_{slope_type}'
        
        if drift_col not in df.columns:
            return np.nan
        
        # Get last non-NaN value
        valid_values = df[drift_col].dropna()
        
        if len(valid_values) == 0:
            return np.nan
        
        return valid_values.iloc[-1]


class MultiScaleDriftAnalyzer:
    """Analyze drift across multiple time scales"""
    
    def __init__(self):
        self.estimator = SlopeEstimator()
    
    def analyze_drift_consistency(
        self,
        df: pd.DataFrame,
        feature: str
    ) -> Dict[str, float]:
        """
        Analyze consistency between short and long-term drift
        
        Args:
            df: DataFrame with drift columns
            feature: Feature name
            
        Returns:
            Dictionary with drift metrics
        """
        drift_long_col = f'{feature}_drift_long'
        drift_short_col = f'{feature}_drift_short'
        
        if drift_long_col not in df.columns or drift_short_col not in df.columns:
            return {
                'drift_long': np.nan,
                'drift_short': np.nan,
                'drift_acceleration': np.nan,
                'drift_consistency': np.nan
            }
        
        # Get latest values
        drift_long = df[drift_long_col].dropna().iloc[-1] if len(df[drift_long_col].dropna()) > 0 else np.nan
        drift_short = df[drift_short_col].dropna().iloc[-1] if len(df[drift_short_col].dropna()) > 0 else np.nan
        
        # Drift acceleration: difference between short and long term
        drift_accel = drift_short - drift_long if not (np.isnan(drift_short) or np.isnan(drift_long)) else np.nan
        
        # Consistency: correlation between short and long term over time
        if len(df) > 30:
            recent = df.tail(30)
            valid = recent[[drift_long_col, drift_short_col]].dropna()
            if len(valid) > 10:
                consistency = valid[drift_long_col].corr(valid[drift_short_col])
            else:
                consistency = np.nan
        else:
            consistency = np.nan
        
        return {
            'drift_long': drift_long,
            'drift_short': drift_short,
            'drift_acceleration': drift_accel,
            'drift_consistency': consistency
        }
    
    def compute_drift_volatility(
        self,
        df: pd.DataFrame,
        feature: str,
        window: int = 30
    ) -> float:
        """
        Compute volatility (std) of drift over recent window
        
        Args:
            df: DataFrame with drift columns
            feature: Feature name
            window: Window size in days
            
        Returns:
            Drift volatility
        """
        drift_col = f'{feature}_drift_long'
        
        if drift_col not in df.columns:
            return np.nan
        
        recent = df[drift_col].tail(window).dropna()
        
        if len(recent) < 10:
            return np.nan
        
        return recent.std()


if __name__ == "__main__":
    # Test slope estimator
    dates = pd.date_range('2024-01-01', periods=200)
    
    # Simulate accelerating decline
    baseline = 0
    expected_slope = -0.1
    actual_slope = -0.3  # Worse than expected
    values = baseline + actual_slope * np.arange(200) / 365
    
    df = pd.DataFrame({
        'timestamp': dates,
        'test_feature': values,
        'test_feature_slope_long': [-0.3] * 200,
        'test_feature_slope_short': [-0.35] * 200  # Accelerating
    })
    
    estimator = SlopeEstimator()
    result = estimator.compute_all_drifts(df, ['test_feature'], age=55, sex='male')
    
    print("Drift analysis:")
    print(result[['test_feature_drift_long', 'test_feature_drift_short']].tail())
    
    analyzer = MultiScaleDriftAnalyzer()
    metrics = analyzer.analyze_drift_consistency(result, 'test_feature')
    print("\nDrift metrics:")
    print(metrics)
