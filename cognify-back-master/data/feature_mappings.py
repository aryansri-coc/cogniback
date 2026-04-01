"""
Health Drift Engine - Feature Mappings
Defines expected slopes, directionality, and weights for all features
"""

from typing import Dict, Any


FEATURE_SPECIFICATIONS: Dict[str, Dict[str, Any]] = {
    # ==================== VITALS ====================
    "steps": {
        "domain": "Frailty",
        "annual_slope": -200,  # Steps decline with age
        "direction": "decline_is_worse",
        "weight": 0.25,
        "unit": "steps/day"
    },
    "heartRateAvg": {
        "domain": "Cardio",
        "annual_slope": 0.2,  # Resting HR slightly increases
        "direction": "increase_is_worse",
        "weight": 0.20,
        "unit": "bpm"
    },
    "hrvSdnnMs": {
        "domain": "Cardio",
        "annual_slope": -0.5,  # HRV declines with age
        "direction": "decline_is_worse",
        "weight": 0.30,
        "unit": "ms"
    },
    "bloodOxygenAvg": {
        "domain": "Cardio",
        "annual_slope": -0.05,  # Slight decline
        "direction": "decline_is_worse",
        "weight": 0.15,
        "unit": "%"
    },
    
    # ==================== MOVEMENT ====================
    "gaitSpeedMs": {
        "domain": "Neuro",  # Primary for neuro
        "annual_slope": -0.02,  # m/s decline
        "direction": "decline_is_worse",
        "weight": 0.35,
        "unit": "m/s"
    },
    "stepCadence": {
        "domain": "Cardio",
        "annual_slope": -1.0,  # Steps per minute
        "direction": "decline_is_worse",
        "weight": 0.15,
        "unit": "steps/min"
    },
    "walkingAsymmetry": {
        "domain": "Neuro",
        "annual_slope": 0.01,  # Asymmetry increases with age
        "direction": "increase_is_worse",
        "weight": 0.25,
        "unit": "ratio"
    },
    
    # ==================== SLEEP ====================
    "totalSleepHours": {
        "domain": "Frailty",
        "annual_slope": -0.05,  # Total sleep slightly declines
        "direction": "decline_is_worse",
        "weight": 0.15,
        "unit": "hours"
    },
    "deepSleepHours": {
        "domain": "Frailty",
        "annual_slope": -0.03,  # Deep sleep declines
        "direction": "decline_is_worse",
        "weight": 0.30,
        "unit": "hours"
    },
    "remSleepHours": {
        "domain": "Neuro",
        "annual_slope": -0.02,  # REM sleep declines
        "direction": "decline_is_worse",
        "weight": 0.20,
        "unit": "hours"
    },
    "sleepLatencyMinutes": {
        "domain": "Frailty",
        "annual_slope": 0.5,  # Takes longer to fall asleep
        "direction": "increase_is_worse",
        "weight": 0.10,
        "unit": "minutes"
    },
    "awakenings": {
        "domain": "Neuro",  # Sleep fragmentation
        "annual_slope": 0.3,  # More awakenings with age
        "direction": "increase_is_worse",
        "weight": 0.15,
        "unit": "count"
    },
    
    # ==================== COGNITIVE ====================
    "reactionTimeMs": {
        "domain": "Neuro",
        "annual_slope": 5.0,  # Reaction time increases (slower)
        "direction": "increase_is_worse",
        "weight": 0.30,
        "unit": "ms"
    },
    "memoryScore": {
        "domain": "Neuro",
        "annual_slope": -0.5,  # Memory score declines
        "direction": "decline_is_worse",
        "weight": 0.30,
        "unit": "score"
    }
}


def get_feature_spec(feature_name: str) -> Dict[str, Any]:
    """Get specification for a feature"""
    if feature_name not in FEATURE_SPECIFICATIONS:
        raise ValueError(f"Feature {feature_name} not found in specifications")
    return FEATURE_SPECIFICATIONS[feature_name]


def get_features_by_domain(domain: str) -> Dict[str, Dict[str, Any]]:
    """Get all features for a specific domain"""
    return {
        name: spec 
        for name, spec in FEATURE_SPECIFICATIONS.items()
        if spec["domain"] == domain
    }


def normalize_drift_direction(
    drift: float,
    feature_name: str
) -> float:
    """
    Normalize drift so that positive = worse
    
    Args:
        drift: Observed drift value
        feature_name: Name of the feature
        
    Returns:
        Normalized drift (positive = worse)
    """
    spec = get_feature_spec(feature_name)
    
    if spec["direction"] == "decline_is_worse":
        # If decline is worse, negative drift is bad → flip sign
        return -drift
    else:
        # If increase is worse, positive drift is bad → keep as is
        return drift
