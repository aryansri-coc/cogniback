"""
Health Drift Engine - Rolling Features Computer
Computes rolling statistics, slopes, and accelerations
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from scipy import stats
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger()


class RollingFeaturesComputer:
    """Compute rolling window statistics and temporal derivatives"""
    
    def __init__(self):
        self.config = get_config()
        self.long_window = self.config.long_term_window_days
        self.short_window = self.config.short_term_window_days
        self.min_points = self.config.min_data_points_for_slope
    
    def compute_slope(
        self,
        values: pd.Series,
        timestamps: pd.Series
    ) -> float:
        """
        Compute linear slope via regression
        
        Args:
            values: Y values (feature values)
            timestamps: X values (time points)
            
        Returns:
            Slope (units per day)
        """
        # Remove NaN values
        mask = ~(values.isna() | timestamps.isna())
        clean_values = values[mask]
        clean_times = timestamps[mask]
        
        if len(clean_values) < self.min_points:
            return np.nan
        
        # Convert timestamps to numeric (days since first observation)
        time_numeric = (clean_times - clean_times.iloc[0]).dt.days
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            time_numeric,
            clean_values
        )
        
        return slope
    
    def compute_rolling_slopes(
        self,
        df: pd.DataFrame,
        feature: str
    ) -> pd.DataFrame:
        """
        Compute long-term and short-term slopes
        
        Args:
            df: DataFrame with timestamp index
            feature: Feature to compute slopes for
            
        Returns:
            DataFrame with added slope columns
        """
        result_df = df.copy()
        
        # Ensure timestamp is datetime
        if 'timestamp' in result_df.columns:
            result_df = result_df.set_index('timestamp')
        
        # Initialize slope columns
        result_df[f'{feature}_slope_long'] = np.nan
        result_df[f'{feature}_slope_short'] = np.nan
        result_df[f'{feature}_acceleration'] = np.nan
        
        # Compute slopes for each time point
        for idx in range(len(result_df)):
            # Long-term slope (180 days)
            if idx >= self.long_window:
                window_data = result_df.iloc[idx - self.long_window:idx + 1]
                slope_long = self.compute_slope(
                    window_data[feature],
                    pd.Series(window_data.index, index=window_data.index)
                )
                result_df.iloc[idx, result_df.columns.get_loc(f'{feature}_slope_long')] = slope_long
            
            # Short-term slope (30 days)
            if idx >= self.short_window:
                window_data = result_df.iloc[idx - self.short_window:idx + 1]
                slope_short = self.compute_slope(
                    window_data[feature],
                    pd.Series(window_data.index, index=window_data.index)
                )
                result_df.iloc[idx, result_df.columns.get_loc(f'{feature}_slope_short')] = slope_short
        
        # Compute acceleration (difference between short and long slopes)
        result_df[f'{feature}_acceleration'] = (
            result_df[f'{feature}_slope_short'] - result_df[f'{feature}_slope_long']
        )
        
        result_df = result_df.reset_index()
        
        return result_df
    
    def compute_all_slopes(
        self,
        df: pd.DataFrame,
        features: list
    ) -> pd.DataFrame:
        """
        Compute slopes and accelerations for all features
        
        Args:
            df: DataFrame with time series
            features: List of features to process
            
        Returns:
            DataFrame with slope and acceleration columns added
        """
        logger.info("Computing rolling slopes", features=len(features))
        
        result_df = df.copy()
        
        for feature in features:
            if feature in df.columns:
                result_df = self.compute_rolling_slopes(result_df, feature)
        
        logger.info("Slope computation complete")
        
        return result_df
    
    def compute_rolling_statistics(
        self,
        df: pd.DataFrame,
        feature: str,
        windows: list = [7, 14, 30]
    ) -> pd.DataFrame:
        """
        Compute rolling mean, std, min, max for multiple windows
        
        Args:
            df: DataFrame with time series
            feature: Feature name
            windows: List of window sizes in days
            
        Returns:
            DataFrame with rolling statistics
        """
        result_df = df.copy()
        
        if 'timestamp' in result_df.columns:
            result_df = result_df.set_index('timestamp')
        
        for window in windows:
            # Rolling mean
            result_df[f'{feature}_rolling_mean_{window}d'] = (
                result_df[feature].rolling(window=window, min_periods=1).mean()
            )
            
            # Rolling std
            result_df[f'{feature}_rolling_std_{window}d'] = (
                result_df[feature].rolling(window=window, min_periods=1).std()
            )
            
            # Rolling min
            result_df[f'{feature}_rolling_min_{window}d'] = (
                result_df[feature].rolling(window=window, min_periods=1).min()
            )
            
            # Rolling max
            result_df[f'{feature}_rolling_max_{window}d'] = (
                result_df[feature].rolling(window=window, min_periods=1).max()
            )
        
        result_df = result_df.reset_index()
        
        return result_df


if __name__ == "__main__":
    # Test rolling features
    dates = pd.date_range('2024-01-01', periods=200)
    
    # Simulate declining trend
    baseline = 50
    trend = -0.1 * np.arange(200)
    noise = np.random.normal(0, 2, 200)
    values = baseline + trend + noise
    
    df = pd.DataFrame({
        'timestamp': dates,
        'test_feature': values
    })
    
    computer = RollingFeaturesComputer()
    result = computer.compute_rolling_slopes(df, 'test_feature')
    
    print("Slopes computed:")
    print(result[['timestamp', 'test_feature', 'test_feature_slope_long', 
                  'test_feature_slope_short', 'test_feature_acceleration']].tail(10))
