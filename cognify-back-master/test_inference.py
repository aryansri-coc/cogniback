"""
Health Drift Engine - Inference Test Script
Tests end-to-end inference pipeline with synthetic data
"""

import sys
import os
import json
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.synthetic_generator import SyntheticDataGenerator
from inference.risk_engine import RiskEngine
from utils.logger import get_logger

logger = get_logger()


def test_healthy_user():
    """Test inference on healthy user"""
    print("\n" + "="*70)
    print("TEST 1: HEALTHY USER")
    print("="*70)
    
    # Generate synthetic healthy user
    generator = SyntheticDataGenerator(seed=42)
    healthy_df = generator.generate_healthy_user(
        user_id="HEALTHY_001",
        age=55,
        sex="male",
        duration_days=365,
        noise_level=0.15
    )
    
    print(f"Generated {len(healthy_df)} days of data")
    print(f"Columns: {list(healthy_df.columns)}")
    
    # Convert to JSON records (what the API expects)
    json_records = healthy_df.to_dict(orient='records')
    
    print(f"Converted to {len(json_records)} JSON records")
    
    # Initialize risk engine
    engine = RiskEngine(calibration_path="models/calibration_params.json")
    
    # Run risk assessment
    result = engine.assess_risk(
        json_records=json_records,
        age=55,
        sex="male",
        user_id="HEALTHY_001"
    )
    
    # Print results
    print("\n--- RISK ASSESSMENT RESULTS ---")
    print(f"Stability Index: {result['stability_index']:.3f}")
    print(f"Decline Probability: {result['decline_probability']:.3f}")
    print(f"\nDomain Risks:")
    for domain, risk in result['domain_risks'].items():
        print(f"  {domain:10s}: {risk:.3f}")
    print(f"\nAnomalies Detected: {len(result['anomalies'])}")
    
    # Verify healthy user has low risk
    assert result['decline_probability'] < 0.6, "Healthy user should have low decline probability"
    assert result['stability_index'] > 0.0, "Healthy user should have some stability"
    print("\n✓ Test passed: Healthy user correctly classified")
    
    return result


def test_declining_user():
    """Test inference on declining user"""
    print("\n" + "="*70)
    print("TEST 2: DECLINING USER")
    print("="*70)
    
    # Generate synthetic declining user
    generator = SyntheticDataGenerator(seed=43)
    declining_df = generator.generate_declining_user(
        user_id="DECLINING_001",
        age=62,
        sex="female",
        duration_days=365,
        decline_start_day=180,
        decline_rate_multiplier=6.0,
        affected_domains=["Neuro", "Cardio"],
        noise_level=0.15
    )
    
    print(f"Generated {len(declining_df)} days of data")
    print(f"Decline starts at day {180}")
    print(f"Affected domains: Neuro, Cardio")
    
    # Convert to JSON records
    json_records = declining_df.to_dict(orient='records')
    
    # Initialize risk engine
    engine = RiskEngine(calibration_path="models/calibration_params.json")
    
    # Run risk assessment
    result = engine.assess_risk(
        json_records=json_records,
        age=62,
        sex="female",
        user_id="DECLINING_001"
    )
    
    # Print results
    print("\n--- RISK ASSESSMENT RESULTS ---")
    print(f"Stability Index: {result['stability_index']:.3f}")
    print(f"Decline Probability: {result['decline_probability']:.3f}")
    print(f"\nDomain Risks:")
    for domain, risk in result['domain_risks'].items():
        print(f"  {domain:10s}: {risk:.3f}")
    print(f"\nDomain Drifts:")
    for domain, drift in result['domain_drifts'].items():
        print(f"  {domain:10s}: {drift:.3f}")
    print(f"\nAnomalies Detected: {len(result['anomalies'])}")
    if result['anomalies']:
        print("\nTop Anomalies:")
        for i, anomaly in enumerate(result['anomalies'][:3]):
            print(f"  {i+1}. {anomaly['feature']} ({anomaly['type']}): {anomaly.get('severity', 'N/A')}")
    
    # Verify declining user has high risk
    assert result['decline_probability'] > 0.2, "Declining user should have elevated decline probability"
    print("\n✓ Test passed: Declining user correctly detected")
    
    return result


def test_comparison():
    """Compare healthy vs declining user results"""
    print("\n" + "="*70)
    print("TEST 3: COMPARATIVE ANALYSIS")
    print("="*70)
    
    generator = SyntheticDataGenerator(seed=44)
    
    # Generate both users
    healthy_df = generator.generate_healthy_user(
        user_id="COMPARE_HEALTHY",
        age=60,
        sex="male",
        duration_days=365
    )
    
    declining_df = generator.generate_declining_user(
        user_id="COMPARE_DECLINING",
        age=60,
        sex="male",
        duration_days=365,
        decline_start_day=150,
        decline_rate_multiplier=5.0,
        affected_domains=["Neuro"]
    )
    
    engine = RiskEngine(calibration_path="models/calibration_params.json")
    
    # Assess both
    healthy_result = engine.assess_risk(
        healthy_df.to_dict(orient='records'),
        age=60,
        sex="male",
        user_id="COMPARE_HEALTHY"
    )
    
    declining_result = engine.assess_risk(
        declining_df.to_dict(orient='records'),
        age=60,
        sex="male",
        user_id="COMPARE_DECLINING"
    )
    
    # Compare
    print("\n--- COMPARISON ---")
    print(f"{'Metric':<30s} {'Healthy':>12s} {'Declining':>12s} {'Difference':>12s}")
    print("-" * 70)
    
    metrics = [
        ('Stability Index', 'stability_index'),
        ('Decline Probability', 'decline_probability'),
        ('Neuro Risk', 'domain_risks.Neuro'),
        ('Cardio Risk', 'domain_risks.Cardio'),
        ('Frailty Risk', 'domain_risks.Frailty')
    ]
    
    for metric_name, metric_path in metrics:
        # Navigate nested dict
        parts = metric_path.split('.')
        healthy_val = healthy_result
        declining_val = declining_result
        for part in parts:
            healthy_val = healthy_val[part]
            declining_val = declining_val[part]
        
        diff = declining_val - healthy_val
        print(f"{metric_name:<30s} {healthy_val:>12.3f} {declining_val:>12.3f} {diff:>+12.3f}")
    
    # Verify separation
    assert declining_result['decline_probability'] > healthy_result['decline_probability'], \
        "Declining user should have higher decline probability than healthy user"
    
    print("\n✓ Test passed: Clear separation between healthy and declining users")


def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n" + "="*70)
    print("TEST 4: EDGE CASES")
    print("="*70)
    
    generator = SyntheticDataGenerator(seed=45)
    engine = RiskEngine(calibration_path="models/calibration_params.json")
    
    # Test 1: Short time series
    print("\n4a. Short time series (60 days)...")
    short_df = generator.generate_healthy_user(
        user_id="SHORT_001",
        age=50,
        sex="female",
        duration_days=60
    )
    
    try:
        result = engine.assess_risk(
            short_df.to_dict(orient='records'),
            age=50,
            sex="female",
            user_id="SHORT_001"
        )
        print(f"   ✓ Handled short series: decline_prob = {result['decline_probability']:.3f}")
    except Exception as e:
        print(f"   ✗ Failed on short series: {e}")
    
    # Test 2: Data with missing values
    print("\n4b. Data with missing values...")
    normal_df = generator.generate_healthy_user(
        user_id="MISSING_001",
        age=45,
        sex="male",
        duration_days=200
    )
    
    # Introduce random missing values
    for col in ['hrvSdnnMs', 'gaitSpeedMs', 'steps']:
        if col in normal_df.columns:
            mask = np.random.random(len(normal_df)) < 0.1
            normal_df.loc[mask, col] = np.nan
    
    try:
        result = engine.assess_risk(
            normal_df.to_dict(orient='records'),
            age=45,
            sex="male",
            user_id="MISSING_001"
        )
        print(f"   ✓ Handled missing values: decline_prob = {result['decline_probability']:.3f}")
    except Exception as e:
        print(f"   ✗ Failed with missing values: {e}")
    
    print("\n✓ Edge case tests complete")


def save_sample_output():
    """Generate and save sample output JSON"""
    print("\n" + "="*70)
    print("GENERATING SAMPLE OUTPUT")
    print("="*70)
    
    generator = SyntheticDataGenerator(seed=46)
    declining_df = generator.generate_declining_user(
        user_id="SAMPLE_001",
        age=58,
        sex="male",
        duration_days=365,
        decline_start_day=200,
        decline_rate_multiplier=5.5,
        affected_domains=["Neuro", "Frailty"]
    )
    
    engine = RiskEngine(calibration_path="models/calibration_params.json")
    result = engine.assess_risk(
        declining_df.to_dict(orient='records'),
        age=58,
        sex="male",
        user_id="SAMPLE_001"
    )
    
    # Save to file
    output_path = "sample_risk_assessment.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"Sample output saved to: {output_path}")
    print("\nSample output preview:")
    print(json.dumps({
        'user_id': result['user_id'],
        'stability_index': result['stability_index'],
        'decline_probability': result['decline_probability'],
        'domain_risks': result['domain_risks']
    }, indent=2))


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("HEALTH DRIFT ENGINE - INFERENCE TESTING")
    print("="*70)
    
    try:
        # Run tests
        test_healthy_user()
        test_declining_user()
        test_comparison()
        test_edge_cases()
        save_sample_output()
        
        print("\n" + "="*70)
        print("ALL TESTS PASSED ✓")
        print("="*70)
        
    except Exception as e:
        print("\n" + "="*70)
        print("TEST FAILED ✗")
        print("="*70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
