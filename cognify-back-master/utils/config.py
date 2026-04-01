"""
Health Drift Engine - Configuration Manager (ENHANCED)
Handles loading and validation of configuration parameters
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class EngineConfig:
    """Configuration for the drift detection engine"""
    
    # File paths
    cohort_demographics_path: str = "data/cohort_demographics.json"
    feature_mappings_path: str = "data/feature_mappings.py"
    calibration_params_path: str = "models/calibration_params.json"
    
    # Processing options
    use_kalman_filter: bool = False  # CHANGED: Default to False for stability
    enable_state_space: bool = False  # CHANGED: Default to False
    
    # Slope estimation
    long_term_window_days: int = 180
    short_term_window_days: int = 30
    min_data_points_for_slope: int = 30
    
    # Anomaly detection
    anomaly_zscore_threshold: float = 2.5
    anomaly_acceleration_multiplier: float = 3.0
    
    # Missing data handling
    max_forward_fill_days: int = 3
    min_completeness_ratio: float = 0.5  # CHANGED: Lowered for synthetic data
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None  # CHANGED: No file logging by default
    
    # Output options
    include_debug_info: bool = False
    verbose_anomalies: bool = True
    
    # Model parameters (loaded from calibration)
    calibration_params: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_json(cls, config_path: str) -> "EngineConfig":
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        return cls(**config_dict)
    
    def load_calibration_params(self) -> None:
        """Load trained calibration parameters"""
        try:
            with open(self.calibration_params_path, 'r') as f:
                self.calibration_params = json.load(f)
        except FileNotFoundError:
            print(f"Warning: Calibration params not found at {self.calibration_params_path}")
            self.calibration_params = {}
    
    def validate(self) -> bool:
        """Validate configuration parameters"""
        assert 0 <= self.min_completeness_ratio <= 1, "Completeness ratio must be 0-1"
        assert self.short_term_window_days < self.long_term_window_days, \
            "Short-term window must be < long-term window"
        assert self.max_forward_fill_days >= 0, "Forward fill days must be >= 0"
        return True


# Global config instance
_config_instance: Optional[EngineConfig] = None


def get_config() -> EngineConfig:
    """Get global configuration instance (singleton pattern)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = EngineConfig()
        _config_instance.validate()
    return _config_instance


def set_config(config: EngineConfig) -> None:
    """Set global configuration instance"""
    global _config_instance
    config.validate()
    _config_instance = config
