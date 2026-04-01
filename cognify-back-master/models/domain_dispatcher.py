"""
Health Drift Engine - Domain Dispatcher (Enhanced)
Aggregates feature-level drifts into domain-level scores with robust error handling
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from data.feature_mappings import get_features_by_domain, get_feature_spec
from utils.constants import DOMAIN_FEATURES, DOMAIN_FUSION_WEIGHTS
from utils.logger import get_logger

logger = get_logger()


class DomainDispatcher:
    """Dispatch features to domains and compute domain-level drift scores"""
    
    def __init__(self):
        self.domain_features = DOMAIN_FEATURES
        self.feature_specs = self._load_feature_specs()
        self._validate_configuration()
    
    def _load_feature_specs(self) -> Dict:
        """Load feature specifications"""
        try:
            from data.feature_mappings import FEATURE_SPECIFICATIONS
            return FEATURE_SPECIFICATIONS
        except ImportError as e:
            logger.error(f"Failed to load feature specifications: {e}")
            return {}
    
    def _validate_configuration(self):
        """Validate domain and feature configuration"""
        if not self.domain_features:
            logger.warning("No domain features configured")
        
        if not self.feature_specs:
            logger.warning("No feature specifications loaded")
        
        # Check that all domain features have specs
        for domain, features in self.domain_features.items():
            missing = [f for f in features if f not in self.feature_specs]
            if missing:
                logger.warning(
                    f"Domain {domain} references features without specs",
                    missing_features=missing
                )
    
    def compute_domain_drift(
        self,
        feature_drifts: Dict[str, float],
        domain: str
    ) -> float:
        """
        Compute weighted domain drift from feature drifts
        
        Formula:
            D_domain = Σ (weight_f × |drift_f|) / Σ weight_f
            
        Where sum is over all features in domain that have valid drift values.
        
        Args:
            feature_drifts: Dictionary mapping feature -> drift value
            domain: Domain name
            
        Returns:
            Domain drift score (positive value, 0 if no features available)
        """
        if domain not in self.domain_features:
            logger.warning(f"Domain {domain} not recognized")
            return 0.0
        
        domain_feature_names = self.domain_features[domain]
        
        weighted_drift = 0.0
        total_weight = 0.0
        features_used = []
        
        for feature in domain_feature_names:
            if feature in feature_drifts:
                drift = feature_drifts[feature]
                
                # Get feature weight
                if feature in self.feature_specs:
                    weight = self.feature_specs[feature].get('weight', 1.0)
                else:
                    weight = 1.0
                    logger.debug(f"No weight found for {feature}, using 1.0")
                
                # Accumulate weighted absolute drift (only if valid)
                if not np.isnan(drift):
                    weighted_drift += weight * abs(drift)
                    total_weight += weight
                    features_used.append(feature)
        
        # Compute normalized drift
        if total_weight > 0:
            domain_drift = weighted_drift / total_weight
            logger.debug(
                f"Domain {domain} drift computed",
                drift=f"{domain_drift:.3f}",
                features_used=len(features_used),
                total_features=len(domain_feature_names)
            )
        else:
            domain_drift = 0.0
            logger.warning(
                f"No valid features for domain {domain}",
                expected_features=domain_feature_names,
                available_features=list(feature_drifts.keys())
            )
        
        return domain_drift
    
    def compute_all_domain_drifts(
        self,
        feature_drifts: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Compute drift for all domains
        
        Args:
            feature_drifts: Dictionary mapping feature -> drift
            
        Returns:
            Dictionary mapping domain -> drift
        """
        if not feature_drifts:
            logger.warning("No feature drifts provided")
            return {domain: 0.0 for domain in self.domain_features.keys()}
        
        domain_drifts = {}
        
        for domain in self.domain_features.keys():
            drift = self.compute_domain_drift(feature_drifts, domain)
            domain_drifts[domain] = drift
        
        logger.debug("Domain drifts computed", drifts=domain_drifts)
        
        return domain_drifts
    
    def extract_latest_feature_drifts(
        self,
        df: pd.DataFrame,
        drift_type: str = 'long'
    ) -> Dict[str, float]:
        """
        Extract latest drift values for all features
        
        Args:
            df: DataFrame with drift columns
            drift_type: 'long' or 'short'
            
        Returns:
            Dictionary mapping feature -> drift (only non-NaN values)
        """
        if df.empty:
            logger.warning("Empty DataFrame provided for drift extraction")
            return {}
        
        feature_drifts = {}
        
        # Find all drift columns
        drift_suffix = f'_drift_{drift_type}'
        drift_cols = [col for col in df.columns if col.endswith(drift_suffix)]
        
        if not drift_cols:
            logger.warning(
                f"No drift columns found with suffix '{drift_suffix}'",
                available_columns=list(df.columns[:10])  # Show first 10 for debugging
            )
            return {}
        
        logger.debug(f"Found {len(drift_cols)} drift columns")
        
        for col in drift_cols:
            feature = col.replace(drift_suffix, '')
            
            # Get last non-NaN value
            valid_values = df[col].dropna()
            if len(valid_values) > 0:
                feature_drifts[feature] = float(valid_values.iloc[-1])
            else:
                logger.debug(f"No valid drift values for feature {feature}")
        
        logger.debug(f"Extracted {len(feature_drifts)} feature drifts")
        
        return feature_drifts
    
    def fuse_domain_risks(
        self,
        domain_risks: Dict[str, float],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Fuse domain-level risks into total risk score
        
        Formula:
            TotalRisk = Σ (weight_d × risk_d) / Σ weight_d
        
        Default weights:
            - Neuro: 0.40
            - Cardio: 0.35
            - Frailty: 0.25
        
        Args:
            domain_risks: Dictionary mapping domain -> risk
            weights: Custom weights (None = use defaults)
            
        Returns:
            Total fused risk [0, 1]
        """
        if weights is None:
            weights = DOMAIN_FUSION_WEIGHTS
        
        if not domain_risks:
            logger.warning("No domain risks provided for fusion")
            return 0.0
        
        total_risk = 0.0
        total_weight = 0.0
        
        for domain, risk in domain_risks.items():
            if domain in weights:
                weight = weights[domain]
                
                # Validate risk value
                if np.isnan(risk):
                    logger.warning(f"NaN risk for domain {domain}, using 0.0")
                    risk = 0.0
                
                total_risk += weight * risk
                total_weight += weight
            else:
                logger.debug(f"Domain {domain} not in fusion weights, skipping")
        
        # Normalize by total weight
        if total_weight > 0:
            total_risk = total_risk / total_weight
        else:
            logger.warning("No valid domain weights, returning 0.0")
            total_risk = 0.0
        
        # Ensure [0, 1] bounds
        total_risk = np.clip(total_risk, 0.0, 1.0)
        
        logger.debug(f"Fused total risk: {total_risk:.3f}")
        
        return float(total_risk)
    
    def compute_stability_index(
        self,
        total_risk: float
    ) -> float:
        """
        Compute stability index from total risk
        
        StabilityIndex = 1 - TotalRisk
        
        Higher stability = better health
        
        Args:
            total_risk: Total risk score [0, 1]
            
        Returns:
            Stability index [0, 1]
        """
        if np.isnan(total_risk):
            logger.warning("NaN total_risk provided, using 0.0")
            total_risk = 0.0
        
        stability = 1.0 - total_risk
        stability = np.clip(stability, 0.0, 1.0)
        
        return float(stability)
    
    def get_feature_contributions(
        self,
        feature_drifts: Dict[str, float],
        domain: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Get individual feature contributions to domain drift
        
        Useful for explainability - shows which features drive domain risk
        
        Args:
            feature_drifts: Feature drift values
            domain: Domain name
            
        Returns:
            Dictionary with feature contributions, sorted by contribution size
            Format: {feature_name: {'drift': float, 'weight': float, 'contribution': float}}
        """
        if domain not in self.domain_features:
            logger.warning(f"Domain {domain} not recognized")
            return {}
        
        if not feature_drifts:
            logger.warning("No feature drifts provided")
            return {}
        
        domain_feature_names = self.domain_features[domain]
        contributions = {}
        
        for feature in domain_feature_names:
            if feature in feature_drifts:
                drift = feature_drifts[feature]
                
                # Skip NaN values
                if np.isnan(drift):
                    continue
                
                # Get feature weight
                if feature in self.feature_specs:
                    weight = self.feature_specs[feature].get('weight', 1.0)
                else:
                    weight = 1.0
                
                contribution = weight * abs(drift)
                contributions[feature] = {
                    'drift': float(drift),
                    'weight': float(weight),
                    'contribution': float(contribution)
                }
        
        if not contributions:
            logger.debug(f"No valid contributions for domain {domain}")
            return {}
        
        # Sort by contribution (descending)
        contributions = dict(
            sorted(contributions.items(), key=lambda x: x[1]['contribution'], reverse=True)
        )
        
        logger.debug(f"Computed {len(contributions)} contributions for domain {domain}")
        
        return contributions
    
    def get_domain_summary(
        self,
        feature_drifts: Dict[str, float]
    ) -> Dict[str, Dict]:
        """
        Get comprehensive summary for all domains
        
        Returns:
            Dictionary with domain summaries including drifts, risks, and contributions
        """
        summary = {}
        
        # Compute domain drifts
        domain_drifts = self.compute_all_domain_drifts(feature_drifts)
        
        for domain in self.domain_features.keys():
            contributions = self.get_feature_contributions(feature_drifts, domain)
            
            summary[domain] = {
                'drift': domain_drifts[domain],
                'num_features': len(self.domain_features[domain]),
                'num_contributing_features': len(contributions),
                'top_contributors': list(contributions.keys())[:3],
                'contributions': contributions
            }
        
        return summary


if __name__ == "__main__":
    # Test domain dispatcher
    print("Testing Domain Dispatcher...")
    
    dispatcher = DomainDispatcher()
    
    # Mock feature drifts
    feature_drifts = {
        'gaitSpeedMs': 0.5,
        'walkingAsymmetry': 0.3,
        'reactionTimeMs': 0.4,
        'hrvSdnnMs': 0.2,
        'heartRateAvg': 0.1
    }
    
    print(f"\nInput feature drifts: {len(feature_drifts)} features")
    
    # Compute domain drifts
    domain_drifts = dispatcher.compute_all_domain_drifts(feature_drifts)
    print("\nDomain drifts:")
    for domain, drift in domain_drifts.items():
        print(f"  {domain}: {drift:.3f}")
    
    # Get feature contributions
    print("\nNeuro domain feature contributions:")
    contributions = dispatcher.get_feature_contributions(feature_drifts, 'Neuro')
    for feature, contrib in contributions.items():
        print(f"  {feature}:")
        print(f"    Drift: {contrib['drift']:.3f}")
        print(f"    Weight: {contrib['weight']:.3f}")
        print(f"    Contribution: {contrib['contribution']:.3f}")
    
    # Test domain summary
    print("\nDomain summary:")
    summary = dispatcher.get_domain_summary(feature_drifts)
    for domain, info in summary.items():
        print(f"\n{domain}:")
        print(f"  Drift: {info['drift']:.3f}")
        print(f"  Features: {info['num_contributing_features']}/{info['num_features']} contributing")
        print(f"  Top contributors: {', '.join(info['top_contributors'])}")
    
    # Test edge case: empty feature drifts
    print("\n\nTesting edge case: empty feature drifts")
    empty_drifts = dispatcher.compute_all_domain_drifts({})
    print(f"Result: {empty_drifts}")
    
    # Test edge case: NaN values
    print("\nTesting edge case: NaN values")
    nan_drifts = {
        'gaitSpeedMs': np.nan,
        'hrvSdnnMs': 0.3
    }
    nan_result = dispatcher.compute_all_domain_drifts(nan_drifts)
    print(f"Result: {nan_result}")
    
    print("\n✓ All tests complete!")
