"""
Health Drift Engine - Anomaly Detector
Statistical anomaly detection based on z-scores and acceleration

FIXES APPLIED:
  Bug 1a — summarize_anomalies() scanned only the single most-recent row,
            so it always returned [] unless that exact timestamp had a flag.
            Fixed: scan the entire DataFrame (or a configurable tail window)
            and de-duplicate by feature, keeping the most severe occurrence.

  Bug 1b — _classify_severity() thresholds (>3, >4) were calibrated for the
            old ANOMALY_ZSCORE_THRESHOLD=2.5.  With the new threshold of 1.5,
            all newly-detected anomalies fell into 'Moderate' with no 'Low'
            tier.  Recalibrated to: Low ≥1.5, High ≥2.5, Critical ≥3.5.

  Bug 1c — detect_acceleration_anomalies() computed its threshold as
            abs(expected_slope) * multiplier.  When expected_slope ≈ 0
            (stable features) the threshold collapsed to ~0, causing either
            everything or nothing to fire.  Fixed: enforce a sensible minimum
            threshold floor so near-zero expected slopes don't corrupt the
            check.
"""

import uuid
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from utils.constants import (
    ANOMALY_ZSCORE_THRESHOLD,
    ANOMALY_ACCELERATION_MULTIPLIER,
    DOMAIN_FEATURES,
)

logger = get_logger()

# Minimum acceleration threshold — prevents collapse when expected_slope ≈ 0
_MIN_ACCEL_THRESHOLD = 0.05

# How many recent rows to scan in summarize_anomalies (None = all rows)
_SUMMARIZE_WINDOW = None


# ---------------------------------------------------------------------------
# Human-readable labels per feature
# ---------------------------------------------------------------------------

_FEATURE_LABELS: Dict[str, str] = {
    "gaitSpeedMs":        "Gait Speed",
    "walkingAsymmetry":   "Walking Asymmetry",
    "reactionTimeMs":     "Reaction Time",
    "memoryScore":        "Memory Score",
    "remSleepHours":      "REM Sleep",
    "awakenings":         "Sleep Awakenings",
    "heartRateAvg":       "Heart Rate",
    "hrvSdnnMs":          "Heart Rate Variability",
    "bloodOxygenAvg":     "Blood Oxygen",
    "stepCadence":        "Step Cadence",
    "steps":              "Daily Steps",
    "deepSleepHours":     "Deep Sleep",
}

def _feature_label(feature: str) -> str:
    return _FEATURE_LABELS.get(feature, feature)


def _feature_to_domain(feature: str) -> Optional[str]:
    """Return the first domain that contains this feature."""
    for domain, features in DOMAIN_FEATURES.items():
        if feature in features:
            return domain
    return None


# ---------------------------------------------------------------------------
# AnomalyDetector
# ---------------------------------------------------------------------------

class AnomalyDetector:
    """Detect statistical anomalies in time series health data."""

    def __init__(
        self,
        zscore_threshold: float = ANOMALY_ZSCORE_THRESHOLD,
        acceleration_multiplier: float = ANOMALY_ACCELERATION_MULTIPLIER,
    ):
        self.zscore_threshold = zscore_threshold
        self.acceleration_multiplier = acceleration_multiplier

    # ------------------------------------------------------------------
    # Detection helpers
    # ------------------------------------------------------------------

    def detect_zscore_anomalies(
        self,
        df: pd.DataFrame,
        feature: str,
        age: int,
        sex: str,
    ) -> pd.DataFrame:
        """
        Flag rows where |z-scored feature| > zscore_threshold.

        The incoming DataFrame is expected to have already-normalized
        (z-scored) values in the feature column.
        """
        result_df = df.copy()

        if feature not in result_df.columns:
            logger.warning(f"Feature {feature} not found in DataFrame")
            return result_df

        anomaly_col = f"{feature}_zscore_anomaly"
        result_df[anomaly_col] = (
            np.abs(result_df[feature]) > self.zscore_threshold
        )

        return result_df

    def detect_acceleration_anomalies(
        self,
        df: pd.DataFrame,
        feature: str,
        expected_slope: float,
    ) -> pd.DataFrame:
        """
        Flag rows where acceleration exceeds multiplier × expected_slope.

        FIX: enforce _MIN_ACCEL_THRESHOLD so that near-zero expected_slope
        values don't collapse the threshold to ~0.
        """
        result_df = df.copy()

        accel_col = f"{feature}_acceleration"
        if accel_col not in result_df.columns:
            logger.warning(f"Acceleration column {accel_col} not found")
            return result_df

        # FIX: was `abs(expected_slope) * multiplier` which → 0 when slope ≈ 0
        raw_threshold = abs(expected_slope) * self.acceleration_multiplier
        threshold = max(raw_threshold, _MIN_ACCEL_THRESHOLD)

        anomaly_col = f"{feature}_accel_anomaly"
        result_df[anomaly_col] = np.abs(result_df[accel_col]) > threshold

        return result_df

    def detect_all_anomalies(
        self,
        df: pd.DataFrame,
        features: List[str],
        age: int,
        sex: str,
        expected_slopes: Dict[str, float],
    ) -> pd.DataFrame:
        """Detect all anomaly types for all features."""
        logger.info("Detecting anomalies", features=len(features))

        result_df = df.copy()

        for feature in features:
            if feature in df.columns:
                result_df = self.detect_zscore_anomalies(
                    result_df, feature, age, sex
                )
                if feature in expected_slopes:
                    result_df = self.detect_acceleration_anomalies(
                        result_df, feature, expected_slopes[feature]
                    )

        logger.info("Anomaly detection complete")
        return result_df

    # ------------------------------------------------------------------
    # Summarization  (FIX: scan full history, not just one row)
    # ------------------------------------------------------------------

    def summarize_anomalies(
        self,
        df: pd.DataFrame,
        date: pd.Timestamp = None,
        scan_window: Optional[int] = _SUMMARIZE_WINDOW,
    ) -> List[Dict[str, Any]]:
        """
        Return a de-duplicated list of anomaly dicts across the history.

        FIX: Previously only inspected the single row matching `date`, so
        it returned [] whenever that exact timestamp was clean — even if
        hundreds of earlier rows were flagged.

        New behaviour:
          - If `date` is given, scan from the start up to (and including)
            that date.
          - If `scan_window` is set, only the most recent N rows are scanned.
          - Anomalies are de-duplicated by feature: only the most severe
            occurrence per feature is kept, so the response list stays concise.

        Returns:
            List of anomaly dicts compatible with the AiPrediction.anomalies
            JSON schema expected by the backend.
        """
        if df.empty:
            return []

        # ---- narrow to date range ----------------------------------------
        working = df.copy()

        if date is not None:
            if "timestamp" in working.columns:
                working = working[working["timestamp"] <= date]
            else:
                working = working[working.index <= date]

        if scan_window is not None and len(working) > scan_window:
            working = working.tail(scan_window)

        if working.empty:
            return []

        # ---- collect all flagged rows ------------------------------------
        anomaly_cols = [c for c in working.columns if c.endswith("_anomaly")]

        if not anomaly_cols:
            logger.warning("No anomaly flag columns found — run detect_all_anomalies first")
            return []

        # best_per_feature: feature -> best anomaly dict seen so far
        best_per_feature: Dict[str, Dict[str, Any]] = {}

        _severity_rank = {"Low": 1, "High": 2, "Critical": 3, "Unknown": 0}

        for col in anomaly_cols:
            flagged_rows = working[working[col] == True]  # noqa: E712
            if flagged_rows.empty:
                continue

            # Parse feature and anomaly_type from column name
            if col.endswith("_zscore_anomaly"):
                feature = col[: -len("_zscore_anomaly")]
                anomaly_type = "Z-score"
                value_col = feature
            elif col.endswith("_accel_anomaly"):
                feature = col[: -len("_accel_anomaly")]
                anomaly_type = "Acceleration"
                value_col = f"{feature}_acceleration"
            else:
                continue

            for _, row in flagged_rows.iterrows():
                raw_value = row.get(value_col, np.nan)
                value = float(raw_value) if not _is_nan(raw_value) else np.nan
                severity = self._classify_severity(value, anomaly_type)

                # Keep only the most severe occurrence per feature
                existing = best_per_feature.get(feature)
                if existing is None or (
                    _severity_rank.get(severity, 0)
                    > _severity_rank.get(existing["severity"], 0)
                ):
                    ts = row.get("timestamp", None)
                    domain = _feature_to_domain(feature)
                    label = _feature_label(feature)

                    best_per_feature[feature] = {
                        "id": str(uuid.uuid4()),
                        "type": _anomaly_type_label(feature, anomaly_type),
                        "severity": severity,
                        "message": _build_message(feature, label, anomaly_type, severity, domain),
                        # extra fields available to backend if needed
                        "feature": feature,
                        "domain": domain,
                        "value": value if not _is_nan(value) else None,
                        "timestamp": str(ts) if ts is not None else None,
                    }

        result = list(best_per_feature.values())
        logger.info(f"summarize_anomalies: {len(result)} anomalies found")
        return result

    # ------------------------------------------------------------------
    # Severity classification  (FIX: recalibrated for threshold=1.5)
    # ------------------------------------------------------------------

    def _classify_severity(self, value: float, anomaly_type: str) -> str:
        """
        Classify anomaly severity.

        FIX: old cutoffs (>3, >4) were above the new ANOMALY_ZSCORE_THRESHOLD
        of 1.5, so every newly-detected anomaly landed in the lowest bucket
        with no 'Low' tier at all.

        New tiers (Z-score):
            Low      ≥ 1.5   (just crossed threshold)
            High     ≥ 2.5   (clearly abnormal)
            Critical ≥ 3.5   (severe)

        Acceleration tiers use absolute acceleration magnitude.
        """
        if _is_nan(value):
            return "Unknown"

        abs_val = abs(value)

        if anomaly_type == "Z-score":
            if abs_val >= 3.5:
                return "Critical"
            elif abs_val >= 2.5:
                return "High"
            else:
                return "Low"   # ≥ 1.5 (threshold gate already applied)
        else:  # Acceleration
            if abs_val > 10.0:
                return "Critical"
            elif abs_val > 5.0:
                return "High"
            else:
                return "Low"


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _is_nan(v) -> bool:
    try:
        return np.isnan(v)
    except (TypeError, ValueError):
        return v is None


def _anomaly_type_label(feature: str, anomaly_type: str) -> str:
    """Map feature + anomaly_type to a human-readable type string."""
    domain = _feature_to_domain(feature)
    label = _feature_label(feature)
    if anomaly_type == "Acceleration":
        return f"{label} Acceleration"
    domain_prefix = f"{domain} " if domain else ""
    return f"{domain_prefix}Change"


def _build_message(
    feature: str,
    label: str,
    anomaly_type: str,
    severity: str,
    domain: Optional[str],
) -> str:
    """Build a human-readable anomaly message."""
    severity_lower = severity.lower()
    domain_str = f" ({domain})" if domain else ""

    if anomaly_type == "Z-score":
        return (
            f"{label}{domain_str} shows a {severity_lower}-severity deviation "
            f"from your demographic baseline."
        )
    else:
        return (
            f"{label}{domain_str} is declining at an accelerating rate — "
            f"recent trend is significantly worse than your long-term average."
        )


# ---------------------------------------------------------------------------
# Quick smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    dates = pd.date_range("2024-01-01", periods=100)

    # Simulate declining gait speed — z-scores creep past threshold over time
    z_scores = np.linspace(0.0, -2.8, 100)   # crosses 1.5 around day 45
    accel     = np.linspace(0.0,  0.3, 100)   # mild acceleration

    df = pd.DataFrame({
        "timestamp":                 dates,
        "gaitSpeedMs":               z_scores,
        "gaitSpeedMs_acceleration":  accel,
    })

    detector = AnomalyDetector()

    # Detect
    df = detector.detect_zscore_anomalies(df, "gaitSpeedMs", age=65, sex="male")
    df = detector.detect_acceleration_anomalies(df, "gaitSpeedMs", expected_slope=-0.001)

    # Summarize across full history
    anomalies = detector.summarize_anomalies(df)

    print(f"Anomalies found: {len(anomalies)}")
    for a in anomalies:
        print(a)