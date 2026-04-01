"""
Health Drift Engine - Constants
Mathematical constants, domain definitions, and system parameters
"""

from typing import Dict, List

# ==================== DOMAIN DEFINITIONS ====================

DOMAIN_FEATURES: Dict[str, List[str]] = {
    "Neuro": [
        "gaitSpeedMs",
        "walkingAsymmetry", 
        "reactionTimeMs",
        "memoryScore",
        "remSleepHours",
        "awakenings"
    ],
    "Cardio": [
        "heartRateAvg",
        "hrvSdnnMs",
        "bloodOxygenAvg",
        "stepCadence"
    ],
    "Frailty": [
        "gaitSpeedMs",
        "walkingAsymmetry",
        "steps",
        "deepSleepHours"
    ]
}

# ==================== HAZARD MAPPING PARAMETERS ====================
#
# Betas operate on NORMALIZED drift [0, 1] after DRIFT_NORMALIZATION_SCALE
# is applied. Do not change these without also recalibrating the scales.
#   beta=2.5, normalized drift=0.64 -> risk ~0.80  (declining user target)
#   beta=2.5, normalized drift=0.08 -> risk ~0.18  (healthy user target)

HAZARD_BETAS: Dict[str, float] = {
    "Neuro": 2.5,
    "Cardio": 2.0,
    "Frailty": 2.2
}

# ==================== DRIFT NORMALIZATION SCALE ====================
#
# Calibrated from cohort_demographics.json actual slope magnitudes.
#
# How these were derived:
#   domain_drift = weighted sum of feature drifts over the long-term window
#   feature_drift = (observed_slope - expected_slope) in raw units/day
#
#   A decline_rate_multiplier=5 user produces:
#     steps extra drift:      2.19 steps/day  -> Frailty domain drift = 83.36
#     reactionTimeMs drift:   0.055 ms/day    -> Neuro domain drift   = 2.308
#     heartRateAvg drift:     0.002 bpm/day   -> Cardio domain drift  = 0.433
#
#   Scale = domain drift value that maps to risk ~0.80 for declining user
#           (normalized = drift/scale = 0.64)
#
#   Neuro:   2.308 / 0.64 = 3.6   -> declining risk ~0.80, healthy risk ~0.19
#   Cardio:  0.433 / 0.64 = 0.68  -> declining risk ~0.80, healthy risk ~0.06
#   Frailty: 83.36 / 1.00 = 83.4  -> declining risk ~0.89, healthy risk ~0.003
#
# Expected results after fix:
#   Healthy:   Neuro~0.19, Cardio~0.06, Frailty~0.003 -> stability > 0.85
#   Declining: Neuro~0.80, Cardio~0.80, Frailty~0.37  -> stability < 0.45

DRIFT_NORMALIZATION_SCALE: Dict[str, float] = {
    "Neuro": 3.6,    # was 15.0 — too large, no separation between users
    "Cardio": 0.68,  # was 10.0 — too large
    "Frailty": 83.4  # was 12.0 — too small, healthy user saturated at 1.0
}

# ==================== DOMAIN FUSION WEIGHTS ====================

DOMAIN_FUSION_WEIGHTS: Dict[str, float] = {
    "Neuro": 0.40,
    "Cardio": 0.35,
    "Frailty": 0.25
}

# ==================== STATUS THRESHOLDS ====================

STATUS_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "Stable": {"min": 0.75, "max": 1.0},
    "Warning": {"min": 0.50, "max": 0.75},
    "Critical": {"min": 0.0, "max": 0.50}
}

STATUS_COLORS: Dict[str, str] = {
    "Stable": "#4CAF50",
    "Warning": "#FF9800", 
    "Critical": "#F44336"
}

# ==================== TIME WINDOWS ====================

SLOPE_WINDOWS: Dict[str, int] = {
    "long_term": 180,
    "short_term": 30
}

# ==================== ANOMALY DETECTION PARAMETERS ====================

ANOMALY_ZSCORE_THRESHOLD: float = 1.5
ANOMALY_ACCELERATION_MULTIPLIER: float = 1.5

# ==================== MISSING VALUE HANDLING ====================

MAX_FORWARD_FILL_DAYS: int = 3

# ==================== DEMOGRAPHIC BINS ====================

AGE_BINS: List[tuple] = [
    (18, 30),
    (30, 40),
    (40, 50),
    (50, 60),
    (60, 70),
    (70, 150)
]

BMI_BINS: List[tuple] = [
    (0, 18.5),
    (18.5, 25),
    (25, 30),
    (30, 100)
]

# ==================== KALMAN FILTER PARAMETERS ====================

KALMAN_PROCESS_NOISE: float = 0.01
KALMAN_MEASUREMENT_NOISE: float = 0.1

# ==================== FATIGUE RISK CLASSIFICATION ====================

FATIGUE_RISK_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "Low": {"min": 0.0, "max": 0.3},
    "Medium": {"min": 0.3, "max": 0.6},
    "High": {"min": 0.6, "max": 1.0}
}