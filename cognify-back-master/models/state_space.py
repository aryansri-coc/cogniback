"""
Health Drift Engine - State Space Model
Kalman Filter for smoothing noisy wearable data and estimating hidden health state
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from utils.logger import get_logger
from utils.constants import KALMAN_PROCESS_NOISE, KALMAN_MEASUREMENT_NOISE

logger = get_logger()


class KalmanSmoother:
    """1D Kalman Filter for time series smoothing"""
    
    def __init__(
        self,
        process_noise: float = KALMAN_PROCESS_NOISE,
        measurement_noise: float = KALMAN_MEASUREMENT_NOISE,
        initial_estimate: Optional[float] = None,
        initial_error: float = 1.0
    ):
        """
        Initialize Kalman Filter
        
        Args:
            process_noise: Process noise variance (Q)
            measurement_noise: Measurement noise variance (R)
            initial_estimate: Initial state estimate (None = use first measurement)
            initial_error: Initial error covariance (P)
        """
        self.Q = process_noise  # Process noise
        self.R = measurement_noise  # Measurement noise
        self.initial_estimate = initial_estimate
        self.initial_error = initial_error
        
        # State variables
        self.x = None  # State estimate
        self.P = None  # Error covariance
    
    def reset(self):
        """Reset filter state"""
        self.x = None
        self.P = None
    
    def predict(self) -> Tuple[float, float]:
        """
        Prediction step: predict next state
        
        Returns:
            (predicted_state, predicted_covariance)
        """
        # State transition (assume constant state)
        x_pred = self.x
        
        # Covariance prediction
        P_pred = self.P + self.Q
        
        return x_pred, P_pred
    
    def update(self, measurement: float) -> Tuple[float, float]:
        """
        Update step: incorporate new measurement
        
        Args:
            measurement: Observed value
            
        Returns:
            (updated_state, updated_covariance)
        """
        # Kalman gain
        K = self.P / (self.P + self.R)
        
        # Update estimate with measurement
        self.x = self.x + K * (measurement - self.x)
        
        # Update covariance
        self.P = (1 - K) * self.P
        
        return self.x, self.P
    
    def filter_series(self, measurements: pd.Series) -> pd.Series:
        """
        Apply Kalman filter to entire time series
        
        Args:
            measurements: Time series of measurements
            
        Returns:
            Smoothed time series
        """
        self.reset()
        
        filtered_values = []
        
        for i, value in enumerate(measurements):
            if np.isnan(value):
                # For missing values, use prediction only
                if self.x is not None:
                    x_pred, P_pred = self.predict()
                    filtered_values.append(x_pred)
                    self.x = x_pred
                    self.P = P_pred
                else:
                    filtered_values.append(np.nan)
            else:
                # Initialize on first valid measurement
                if self.x is None:
                    self.x = value if self.initial_estimate is None else self.initial_estimate
                    self.P = self.initial_error
                    filtered_values.append(self.x)
                else:
                    # Predict
                    x_pred, P_pred = self.predict()
                    self.x = x_pred
                    self.P = P_pred
                    
                    # Update
                    x_updated, P_updated = self.update(value)
                    filtered_values.append(x_updated)
        
        return pd.Series(filtered_values, index=measurements.index)


class StateSpaceModel:
    """Multi-variate state space modeling for health metrics"""
    
    def __init__(
        self,
        use_kalman: bool = True,
        process_noise: float = KALMAN_PROCESS_NOISE,
        measurement_noise: float = KALMAN_MEASUREMENT_NOISE
    ):
        self.use_kalman = use_kalman
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.filters = {}  # One filter per feature
    
    def smooth_dataframe(
        self,
        df: pd.DataFrame,
        features: list
    ) -> pd.DataFrame:
        """
        Apply Kalman smoothing to multiple features
        
        Args:
            df: DataFrame with time series
            features: List of features to smooth
            
        Returns:
            DataFrame with smoothed features (original preserved as _unsmoothed)
        """
        if not self.use_kalman:
            logger.info("Kalman filtering disabled")
            return df
        
        logger.info("Applying Kalman smoothing", features=len(features))
        
        result_df = df.copy()
        
        for feature in features:
            if feature not in df.columns:
                continue
            
            # Create filter for this feature
            kalman = KalmanSmoother(
                process_noise=self.process_noise,
                measurement_noise=self.measurement_noise
            )
            
            # Store original
            result_df[f'{feature}_unsmoothed'] = df[feature]
            
            # Apply smoothing
            result_df[feature] = kalman.filter_series(df[feature])
            
            self.filters[feature] = kalman
        
        logger.info("Kalman smoothing complete")
        
        return result_df
    
    def estimate_hidden_state(
        self,
        df: pd.DataFrame,
        features: list
    ) -> pd.Series:
        """
        Estimate overall health state from multiple features
        
        Args:
            df: DataFrame with multiple health metrics
            features: Features to combine
            
        Returns:
            Time series of estimated health state
        """
        # Simple averaging of normalized features
        # More sophisticated: could use multivariate Kalman
        
        valid_features = [f for f in features if f in df.columns]
        
        if not valid_features:
            return pd.Series(np.nan, index=df.index)
        
        # Average across features (assuming they're normalized)
        health_state = df[valid_features].mean(axis=1)
        
        return health_state


if __name__ == "__main__":
    # Test Kalman filter
    np.random.seed(42)
    
    # Generate noisy sine wave
    t = np.linspace(0, 10, 200)
    true_signal = np.sin(t)
    noisy_signal = true_signal + np.random.normal(0, 0.5, 200)
    
    # Add some missing values
    noisy_signal[50:55] = np.nan
    
    df = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=200),
        'test_feature': noisy_signal
    })
    
    model = StateSpaceModel(use_kalman=True)
    smoothed_df = model.smooth_dataframe(df, ['test_feature'])
    
    print("Smoothing comparison:")
    print(smoothed_df[['test_feature_unsmoothed', 'test_feature']].head(20))
