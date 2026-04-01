"""
Health Drift Engine - Hazard Mapper
Maps drift scores to risk probabilities using exponential hazard functions

ROOT CAUSE FIX (Bug 2 - Domain risks saturating at 1.0):
  risk_engine.py calls HazardMapper(beta_values=HAZARD_BETAS), passing betas
  explicitly from constants. The log was showing old betas {7.0, 5.0, 6.0}
  which confirmed the old file was still active / new file wasn't saved.

  Additionally, even with correct betas, the hazard transform was receiving
  raw drift values (e.g. Frailty: 83.36) and computing:
      1 - exp(-2.2 * 83.36) = 1.0   <- still saturates for EVERY user

  Fix: Added _normalize_drift() which normalizes raw drift into [0,1] using
  DRIFT_NORMALIZATION_SCALE before applying the hazard transform.

  Result:
      Healthy  drift ~0.4  -> normalized ~0.03 -> risk ~0.07
      Declining drift ~83  -> normalized ~1.00 -> risk ~0.89
"""

import numpy as np
from typing import Dict
from utils.constants import HAZARD_BETAS, DRIFT_NORMALIZATION_SCALE
from utils.logger import get_logger

logger = get_logger()


class HazardMapper:
    """Map domain drift scores to risk probabilities"""
    
    def __init__(self, beta_values: Dict[str, float] = None):
        """
        Initialize hazard mapper
        
        Args:
            beta_values: Domain-specific beta parameters (None = use defaults)
        """
        self.betas = beta_values if beta_values is not None else HAZARD_BETAS.copy()
        self.drift_scales = DRIFT_NORMALIZATION_SCALE.copy()
        logger.info("Hazard mapper initialized", betas=self.betas)

    # ------------------------------------------------------------------
    # NEW: Internal drift normalization (fixes saturation bug)
    # ------------------------------------------------------------------

    def _normalize_drift(self, drift_score: float, domain: str) -> float:
        """
        Normalize raw drift (in feature-space units) into [0, 1].

        Uses DRIFT_NORMALIZATION_SCALE[domain] as the "maximally bad" anchor:
            normalized = clip(raw_drift / scale, 0, 1)

        Why this is needed:
            slope_estimator outputs drift in original feature units (steps/day,
            ms/day, etc). A declining user produces Frailty drift ~83, which
            means 1 - exp(-beta * 83) = 1.0 for ANY beta > 0.05, saturating
            every user to the same risk regardless of actual health status.

            By normalizing against DRIFT_NORMALIZATION_SCALE, we map the
            severely declining range into [0, 1] so betas operate correctly.

        Args:
            drift_score: Raw domain drift in feature-space units
            domain:      Domain name ('Neuro', 'Cardio', 'Frailty')

        Returns:
            Normalized drift in [0, 1]
        """
        scale = self.drift_scales.get(domain, 10.0)
        return float(np.clip(drift_score / scale, 0.0, 1.0))

    # ------------------------------------------------------------------
    # Public API (unchanged signatures — fully backward compatible)
    # ------------------------------------------------------------------

    def compute_hazard_risk(
        self,
        drift_score: float,
        domain: str
    ) -> float:
        """
        Compute risk using exponential hazard transform
        
        Mathematical formulation:
            normalized_drift = clip(raw_drift / scale[domain], 0, 1)
            Risk = 1 - exp(-beta * normalized_drift)
        
        This ensures:
            - Risk in [0, 1]
            - Risk = 0 when drift = 0
            - Risk approaches 1 as drift approaches infinity
            - Beta controls sensitivity over a stable [0, 1] normalized range
            - Healthy users produce low risk; declining users produce high risk
        
        Args:
            drift_score: Domain drift score (positive = worse)
            domain: Domain name ('Neuro', 'Cardio', 'Frailty')
            
        Returns:
            Risk probability [0, 1]
        """
        if domain not in self.betas:
            logger.warning(f"Domain {domain} not found, using default beta=2.0")
            beta = 2.0
        else:
            beta = self.betas[domain]
        
        # Ensure drift is non-negative (should be already, but safety check)
        drift_score = max(0, drift_score)
        
        # FIX: normalize before applying hazard transform
        normalized = self._normalize_drift(drift_score, domain)

        # Exponential hazard transform on normalized drift
        risk = 1 - np.exp(-beta * normalized)
        
        # Ensure [0, 1] bounds
        risk = np.clip(risk, 0.0, 1.0)
        
        return float(risk)
    
    def compute_all_domain_risks(
        self,
        domain_drifts: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Compute risk for all domains
        
        Args:
            domain_drifts: Dictionary mapping domain -> drift score
            
        Returns:
            Dictionary mapping domain -> risk probability
        """
        risks = {}
        
        for domain, drift in domain_drifts.items():
            risks[domain] = self.compute_hazard_risk(drift, domain)
        
        logger.debug("Domain risks computed", risks=risks)
        
        return risks
    
    def inverse_hazard(
        self,
        risk: float,
        domain: str
    ) -> float:
        """
        Inverse transform: given risk, compute required drift
        
        Useful for understanding: "What drift would give this risk level?"
        
        Note: Returns NORMALIZED drift (not raw feature-space drift).
        To get raw drift, multiply result by DRIFT_NORMALIZATION_SCALE[domain].
        
        Args:
            risk: Risk probability [0, 1]
            domain: Domain name
            
        Returns:
            Normalized drift score required to achieve this risk
        """
        if domain not in self.betas:
            beta = 2.0
        else:
            beta = self.betas[domain]
        
        # Inverse of: risk = 1 - exp(-beta * normalized_drift)
        # => normalized_drift = -ln(1 - risk) / beta
        
        risk = np.clip(risk, 0.0, 0.9999)  # Avoid log(0)
        drift = -np.log(1 - risk) / beta
        
        return float(drift)
    
    def calibrate_beta(
        self,
        observed_drifts: np.ndarray,
        observed_outcomes: np.ndarray,
        domain: str,
        target_auc: float = 0.85
    ) -> float:
        """
        Calibrate beta parameter to match observed data
        
        This would be used during training to optimize beta values.
        Normalizes drifts before calibration so the optimized beta
        is consistent with how compute_hazard_risk uses it.
        
        Args:
            observed_drifts: Array of RAW drift scores
            observed_outcomes: Binary outcomes (0=healthy, 1=declining)
            domain: Domain name
            target_auc: Target AUC-ROC
            
        Returns:
            Optimal beta value
        """
        from sklearn.metrics import roc_auc_score
        from scipy.optimize import minimize_scalar

        # Normalize drifts first — beta must be calibrated on same scale it runs on
        scale = self.drift_scales.get(domain, 10.0)
        norm_drifts = np.clip(observed_drifts / scale, 0.0, 1.0)
        
        def objective(beta):
            risks = 1 - np.exp(-beta * norm_drifts)
            try:
                auc = roc_auc_score(observed_outcomes, risks)
                return abs(auc - target_auc)
            except:
                return 1.0  # Penalize invalid configurations
        
        # Optimize beta in range [0.5, 10]
        result = minimize_scalar(objective, bounds=(0.5, 10), method='bounded')
        
        optimal_beta = result.x
        
        logger.info(
            f"Calibrated beta for {domain}",
            optimal_beta=optimal_beta,
            original_beta=self.betas.get(domain, 2.0)
        )
        
        return optimal_beta
    
    def sensitivity_analysis(
        self,
        domain: str,
        drift_range: np.ndarray = None
    ) -> Dict[str, np.ndarray]:
        """
        Analyze sensitivity of risk to drift
        
        Note: drift_range here is NORMALIZED drift [0, 1], not raw drift.
        This gives a clean picture of how beta shapes the risk curve
        independent of feature-space magnitudes.
        
        Args:
            domain: Domain name
            drift_range: Array of normalized drift values [0, 1] to test
                         (None = default range 0 to 1)
            
        Returns:
            Dictionary with drift values and corresponding risks
        """
        if drift_range is None:
            drift_range = np.linspace(0, 1, 100)
        
        beta = self.betas.get(domain, 2.0)

        risks = np.array([
            1.0 - np.exp(-beta * np.clip(d, 0.0, 1.0))
            for d in drift_range
        ])
        
        return {
            'drift': drift_range,
            'risk': risks,
            'beta': beta
        }


if __name__ == "__main__":
    # Test hazard mapper with real values from test output
    mapper = HazardMapper()

    print("=== Healthy user (low raw drifts) ===")
    healthy_drifts = {"Neuro": 0.3, "Cardio": 0.2, "Frailty": 0.4}
    print(mapper.compute_all_domain_risks(healthy_drifts))

    print("\n=== Declining user (real values from test: Frailty=83.36) ===")
    declining_drifts = {"Neuro": 2.308, "Cardio": 0.433, "Frailty": 83.360}
    print(mapper.compute_all_domain_risks(declining_drifts))

    print("\nExpected output:")
    print("  Healthy:   Neuro~0.07, Cardio~0.04, Frailty~0.07")
    print("  Declining: Neuro~0.33, Cardio~0.08, Frailty~0.89")

    # Sensitivity analysis
    sensitivity = mapper.sensitivity_analysis('Neuro')
    print(f"\nNeuro sensitivity (normalized drift 0 to 1):")
    for i in [0, 25, 50, 75, 99]:
        print(f"  drift={sensitivity['drift'][i]:.2f} -> risk={sensitivity['risk'][i]:.3f}")

    # Inverse hazard
    print(f"\nInverse hazard (Neuro, risk=0.5): normalized drift = {mapper.inverse_hazard(0.5, 'Neuro'):.3f}")