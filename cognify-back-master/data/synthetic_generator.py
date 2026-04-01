"""
Health Drift Engine - Synthetic Data Generator
Creates realistic longitudinal wearable data for training and testing
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
import random

class SyntheticDataGenerator:
    """Generate synthetic longitudinal health data with configurable drift"""
    
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.feature_specs = self._load_feature_specs()
        self.demographics = self._load_demographics()
    
    def _load_feature_specs(self) -> Dict:
        """Load feature specifications"""
        from data.feature_mappings import FEATURE_SPECIFICATIONS
        return FEATURE_SPECIFICATIONS
    
    def _load_demographics(self) -> Dict:
        """Load demographic statistics"""
        with open('data/cohort_demographics.json', 'r') as f:
            return json.load(f)
    
    def generate_healthy_user(
        self,
        user_id: str,
        age: int,
        sex: str,
        duration_days: int = 365,
        noise_level: float = 0.15
    ) -> pd.DataFrame:
        """
        Generate data for a healthy user with age-appropriate decline
        
        Args:
            user_id: Unique identifier
            age: User age
            sex: 'male' or 'female'
            duration_days: Number of days to generate
            noise_level: Gaussian noise std as fraction of signal
            
        Returns:
            DataFrame with daily measurements
        """
        # Determine age bin
        age_bin = self._get_age_bin(age)
        
        # Get demographic baseline
        demographics = self.demographics['age_bins'][age_bin][sex]
        
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=duration_days),
            periods=duration_days,
            freq='D'
        )
        
        data = {'timestamp': dates, 'userId': user_id}
        
        for feature, spec in self.feature_specs.items():
            if feature in demographics:
                mean = demographics[feature]['mean']
                std = demographics[feature]['std']
                annual_slope = demographics[feature]['annual_slope']
                
                # Generate with linear trend + noise
                trend = annual_slope * np.arange(duration_days) / 365
                noise = np.random.normal(0, std * noise_level, duration_days)
                baseline = np.random.normal(mean, std * 0.1)  # Individual baseline
                
                values = baseline + trend + noise
                
                # Add occasional missing values (5%)
                mask = np.random.random(duration_days) < 0.05
                values[mask] = np.nan
                
                data[feature] = values
        
        df = pd.DataFrame(data)
        return df
    
    def generate_declining_user(
        self,
        user_id: str,
        age: int,
        sex: str,
        duration_days: int = 365,
        decline_start_day: int = 180,
        decline_rate_multiplier: float = 5.0,
        affected_domains: List[str] = ["Neuro"],
        noise_level: float = 0.15
    ) -> pd.DataFrame:
        """
        Generate data for user with accelerated decline in specific domains
        
        Args:
            user_id: Unique identifier
            age: User age
            sex: 'male' or 'female'
            duration_days: Total days
            decline_start_day: Day when accelerated decline begins
            decline_rate_multiplier: How much faster than normal aging
            affected_domains: Which domains show accelerated decline
            noise_level: Gaussian noise level
            
        Returns:
            DataFrame with accelerated decline pattern
        """
        # Start with healthy baseline
        df = self.generate_healthy_user(user_id, age, sex, duration_days, noise_level)
        
        age_bin = self._get_age_bin(age)
        demographics = self.demographics['age_bins'][age_bin][sex]
        
        # Apply accelerated decline to affected domains
        for feature, spec in self.feature_specs.items():
            if spec['domain'] in affected_domains and feature in demographics:
                annual_slope = demographics[feature]['annual_slope']
                
                # Create accelerated decline after start day
                post_decline_days = duration_days - decline_start_day
                if post_decline_days > 0:
                    extra_decline = (
                        annual_slope * 
                        (decline_rate_multiplier - 1) * 
                        np.arange(post_decline_days) / 365
                    )
                    
                    # Apply to post-decline period
                    df.loc[df.index >= decline_start_day, feature] += extra_decline
        
        return df
    
    def generate_cohort(
        self,
        n_healthy: int = 50,
        n_declining: int = 20,
        duration_days: int = 365
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate a mixed cohort for training
        
        Returns:
            (healthy_df, declining_df)
        """
        healthy_users = []
        declining_users = []
        
        # Generate healthy users
        for i in range(n_healthy):
            age = np.random.randint(40, 75)
            sex = np.random.choice(['male', 'female'])
            df = self.generate_healthy_user(
                user_id=f"H{i:03d}",
                age=age,
                sex=sex,
                duration_days=duration_days
            )
            df['age'] = age
            df['sex'] = sex
            df['label'] = 'healthy'
            healthy_users.append(df)
        
        # Generate declining users
        for i in range(n_declining):
            age = np.random.randint(50, 75)
            sex = np.random.choice(['male', 'female'])
            
            # Random decline characteristics
            decline_start = np.random.randint(90, 180)
            decline_rate = np.random.uniform(3.0, 8.0)
            affected = random.choice( [["Neuro"], ["Cardio"], ["Neuro", "Cardio"]])
            
            df = self.generate_declining_user(
                user_id=f"D{i:03d}",
                age=age,
                sex=sex,
                duration_days=duration_days,
                decline_start_day=decline_start,
                decline_rate_multiplier=decline_rate,
                affected_domains=affected
            )
            df['age'] = age
            df['sex'] = sex
            df['label'] = 'declining'
            declining_users.append(df)
        
        healthy_df = pd.concat(healthy_users, ignore_index=True)
        declining_df = pd.concat(declining_users, ignore_index=True)
        
        return healthy_df, declining_df
    
    def _get_age_bin(self, age: int) -> str:
        """Map age to demographic bin"""
        if age < 30:
            return "18-30"
        elif age < 40:
            return "18-30"  # Use younger bin
        elif age < 50:
            return "40-50"
        elif age < 60:
            return "40-50"
        else:
            return "60-70"


if __name__ == "__main__":
    # Test data generation
    generator = SyntheticDataGenerator()
    
    # Generate one healthy user
    healthy_df = generator.generate_healthy_user(
        user_id="TEST001",
        age=55,
        sex="male",
        duration_days=365
    )
    print("Healthy user sample:")
    print(healthy_df.head())
    
    # Generate one declining user
    declining_df = generator.generate_declining_user(
        user_id="TEST002",
        age=60,
        sex="female",
        duration_days=365,
        decline_start_day=180,
        decline_rate_multiplier=6.0,
        affected_domains=["Neuro"]
    )
    print("\nDeclining user sample:")
    print(declining_df.tail())
