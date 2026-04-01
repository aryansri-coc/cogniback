"""
Health Drift Engine - Response Builder (Refactored)
Format risk assessment into DBMS-compatible JSON response
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from utils.constants import STATUS_THRESHOLDS, STATUS_COLORS, FATIGUE_RISK_THRESHOLDS
from utils.logger import get_logger

logger = get_logger()


class ResponseBuilder:
    """
    Build structured JSON response for DBMS consumption
    
    Outputs:
        - cognitiveIndex (derived from NeuroRisk)
        - healthStatus (Stable/Warning/Critical based on StabilityIndex)
        - stabilityScore (StabilityIndex)
        - neuroDeclineProbability (from trained logistic regression)
        - fatigueRisk (derived from FrailtyRisk)
        - anomalies (list with explanations)
        - aiInsights (human-readable explanations)
    """
    
    def __init__(self):
        pass
    
    def classify_health_status(
        self,
        stability_index: float
    ) -> tuple:
        """
        Classify health status based on StabilityIndex
        
        Thresholds:
            - Stable: > 0.75
            - Warning: 0.50 - 0.75
            - Critical: < 0.50
        
        Returns:
            (status_label, status_color)
        """
        if stability_index > STATUS_THRESHOLDS['Stable']['min']:
            return 'Stable', STATUS_COLORS['Stable']
        elif stability_index > STATUS_THRESHOLDS['Warning']['min']:
            return 'Warning', STATUS_COLORS['Warning']
        else:
            return 'Critical', STATUS_COLORS['Critical']
    
    def classify_fatigue_risk(
        self,
        frailty_risk: float
    ) -> str:
        """
        Classify fatigue risk from FrailtyRisk
        
        Returns:
            'Low', 'Medium', or 'High'
        """
        if frailty_risk < FATIGUE_RISK_THRESHOLDS['Low']['max']:
            return 'Low'
        elif frailty_risk < FATIGUE_RISK_THRESHOLDS['Medium']['max']:
            return 'Medium'
        else:
            return 'High'
    
    def compute_cognitive_index(
        self,
        neuro_risk: float
    ) -> int:
        """
        Compute cognitive index (0-100 scale)
        
        Formula:
            CognitiveIndex = 100 × (1 - NeuroRisk)
        
        Returns:
            Integer [0, 100]
        """
        cognitive_index = int(100 * (1 - neuro_risk))
        return max(0, min(100, cognitive_index))
    
    def generate_ai_insights(
        self,
        domain_risks: Dict[str, float],
        domain_drifts: Dict[str, float],
        domain_contributions: Dict[str, Dict],
        anomalies: List[Dict],
        stability_index: float,
        decline_probability: float
    ) -> List[str]:
        """
        Generate human-readable AI insights
        
        Returns:
            List of insight strings
        """
        insights = []
        
        # Overall status insight
        if stability_index > 0.75:
            insights.append(
                f"Your health patterns are stable (stability: {stability_index:.0%}). "
                "Continue your current routines."
            )
        elif stability_index > 0.50:
            insights.append(
                f"Your health stability has decreased to {stability_index:.0%}. "
                "Some patterns show concerning changes worth monitoring."
            )
        else:
            insights.append(
                f"Your health stability is low ({stability_index:.0%}). "
                "Multiple health domains show significant changes. "
                "Consider consulting your healthcare provider."
            )
        
        # Domain-specific insights
        risk_threshold = 0.3
        
        if domain_risks['Neuro'] > risk_threshold:
            # Find top contributors
            neuro_contrib = domain_contributions.get('Neuro', {})
            if neuro_contrib:
                top_feature = list(neuro_contrib.keys())[0]
                feature_data = neuro_contrib[top_feature]
                insights.append(
                    f"Neurological patterns show elevated risk ({domain_risks['Neuro']:.0%}). "
                    f"Primary driver: changes in {top_feature.replace('Ms', '').replace('_', ' ')}."
                )
        
        if domain_risks['Cardio'] > risk_threshold:
            cardio_contrib = domain_contributions.get('Cardio', {})
            if cardio_contrib:
                top_feature = list(cardio_contrib.keys())[0]
                insights.append(
                    f"Cardiovascular health shows elevated risk ({domain_risks['Cardio']:.0%}). "
                    f"Key factor: {top_feature.replace('Ms', '').replace('_', ' ')} variability."
                )
        
        if domain_risks['Frailty'] > risk_threshold:
            frailty_contrib = domain_contributions.get('Frailty', {})
            if frailty_contrib:
                top_feature = list(frailty_contrib.keys())[0]
                insights.append(
                    f"Physical vitality shows decline risk ({domain_risks['Frailty']:.0%}). "
                    f"Monitor: {top_feature.replace('Ms', '').replace('_', ' ')}."
                )
        
        # Anomaly insights
        if len(anomalies) > 0:
            high_severity = [a for a in anomalies if a.get('severity') in ['High', 'Critical']]
            if high_severity:
                insights.append(
                    f"Detected {len(high_severity)} high-severity anomalies in recent data. "
                    "These represent unusual deviations from your baseline."
                )
        
        # Decline probability insight
        if decline_probability > 0.7:
            insights.append(
                f"Advanced analysis indicates {decline_probability:.0%} probability of health decline. "
                "We recommend discussing these trends with your healthcare provider."
            )
        elif decline_probability > 0.4:
            insights.append(
                f"Moderate probability ({decline_probability:.0%}) of health pattern changes. "
                "Continue monitoring closely over the coming weeks."
            )
        
        return insights
    
    def build_response(
        self,
        risk_assessment: Dict,
        include_debug: bool = False
    ) -> Dict[str, Any]:
        """
        Build complete DBMS-compatible JSON response
        
        Args:
            risk_assessment: Output from RiskEngine.assess_risk()
            include_debug: Include detailed debug information
            
        Returns:
            Formatted JSON response
        """
        logger.info("Building response", user_id=risk_assessment.get('user_id'))
        
        # Extract core values
        stability_index = risk_assessment['stability_index']
        decline_probability = risk_assessment['decline_probability']
        domain_risks = risk_assessment['domain_risks']
        domain_drifts = risk_assessment['domain_drifts']
        domain_contributions = risk_assessment['domain_contributions']
        anomalies = risk_assessment['anomalies']
        
        # Compute derived metrics
        cognitive_index = self.compute_cognitive_index(domain_risks['Neuro'])
        health_status, status_color = self.classify_health_status(stability_index)
        fatigue_risk = self.classify_fatigue_risk(domain_risks['Frailty'])
        
        # Generate insights
        ai_insights = self.generate_ai_insights(
            domain_risks,
            domain_drifts,
            domain_contributions,
            anomalies,
            stability_index,
            decline_probability
        )
        
        # Build response
        response = {
            "status": "success",
            "data": {
                "cognitiveIndex": cognitive_index,
                "healthStatus": health_status,
                "statusColor": status_color,
                "predictions": {
                    "stabilityScore": round(stability_index, 3),
                    "fatigueRisk": fatigue_risk,
                    "neuroDeclineProbability": round(decline_probability, 3)
                },
                "domainRisks": {
                    "neuro": round(domain_risks['Neuro'], 3),
                    "cardio": round(domain_risks['Cardio'], 3),
                    "frailty": round(domain_risks['Frailty'], 3)
                },
                "anomalies": anomalies,
                "aiInsights": ai_insights,
                "lastSync": risk_assessment['last_assessment_date']
            }
        }
        
        # Optional debug information
        if include_debug:
            response['debug'] = {
                'domain_drifts': domain_drifts,
                'domain_contributions': domain_contributions,
                'hazard_betas': {
                    'neuro': 7.0,
                    'cardio': 5.0,
                    'frailty': 6.0
                },
                'fusion_weights': {
                    'neuro': 0.40,
                    'cardio': 0.35,
                    'frailty': 0.25
                }
            }
        
        logger.info(
            "Response built",
            status=health_status,
            cognitive_index=cognitive_index
        )
        
        return response


if __name__ == "__main__":
    # Test response builder
    mock_assessment = {
        'user_id': 'TEST001',
        'stability_index': 0.65,
        'decline_probability': 0.42,
        'domain_risks': {
            'Neuro': 0.35,
            'Cardio': 0.20,
            'Frailty': 0.25
        },
        'domain_drifts': {
            'Neuro': 0.45,
            'Cardio': 0.30,
            'Frailty': 0.35
        },
        'anomalies': [
            {
                'feature': 'gaitSpeedMs',
                'type': 'Z-score',
                'value': -2.8,
                'severity': 'High',
                'timestamp': '2024-03-01'
            }
        ],
        'domain_contributions': {
            'Neuro': {
                'gaitSpeedMs': {'drift': 0.6, 'weight': 0.35, 'contribution': 0.21},
                'reactionTimeMs': {'drift': 0.4, 'weight': 0.30, 'contribution': 0.12}
            },
            'Cardio': {},
            'Frailty': {}
        },
        'last_assessment_date': '2024-03-01'
    }
    
    builder = ResponseBuilder()
    response = builder.build_response(mock_assessment, include_debug=True)
    
    import json
    print(json.dumps(response, indent=2))

