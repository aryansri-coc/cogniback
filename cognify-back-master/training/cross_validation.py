"""
Health Drift Engine - Cross Validation
K-fold validation for calibration model
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from training.train_model import DriftEngineTrainer
from utils.logger import get_logger

logger = get_logger()


class CrossValidator:
    """K-fold cross validation for drift engine"""
    
    def __init__(self, n_folds: int = 5):
        self.n_folds = n_folds
        self.trainer = DriftEngineTrainer()
    
    def run_cross_validation(
        self,
        healthy_df: pd.DataFrame,
        declining_df: pd.DataFrame
    ) -> Dict[str, List[float]]:
        """
        Run k-fold cross validation
        
        Returns:
            Dictionary with metric lists across folds
        """
        logger.info(f"Starting {self.n_folds}-fold cross validation")
        
        # Combine and create labels
        all_data = []
        all_labels = []
        
        # Process all users
        for user_id in healthy_df['userId'].unique():
            user_data = healthy_df[healthy_df['userId'] == user_id]
            try:
                processed = self.trainer.process_user_data(user_data)
                risks = self.trainer.extract_domain_risks(processed)
                all_data.append([risks['Neuro'], risks['Cardio'], risks['Frailty']])
                all_labels.append(0)
            except:
                pass
        
        for user_id in declining_df['userId'].unique():
            user_data = declining_df[declining_df['userId'] == user_id]
            try:
                processed = self.trainer.process_user_data(user_data)
                risks = self.trainer.extract_domain_risks(processed)
                all_data.append([risks['Neuro'], risks['Cardio'], risks['Frailty']])
                all_labels.append(1)
            except:
                pass
        
        X = np.array(all_data)
        y = np.array(all_labels)
        
        # Stratified k-fold
        skf = StratifiedKFold(n_splits=self.n_folds, shuffle=True, random_state=42)
        
        metrics = {
            'auc': [],
            'precision': [],
            'recall': [],
            'f1': []
        }
        
        for fold, (train_idx, test_idx) in enumerate(skf.split(X, y)):
            logger.info(f"Fold {fold + 1}/{self.n_folds}")
            
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            # Train on this fold
            from sklearn.preprocessing import StandardScaler
            from sklearn.linear_model import LogisticRegression
            
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            model = LogisticRegression(random_state=42, class_weight='balanced')
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            y_pred = model.predict(X_test_scaled)
            
            auc = roc_auc_score(y_test, y_pred_proba)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            metrics['auc'].append(auc)
            metrics['precision'].append(precision)
            metrics['recall'].append(recall)
            metrics['f1'].append(f1)
            
            logger.info(
                f"Fold {fold + 1} results",
                auc=f"{auc:.3f}",
                precision=f"{precision:.3f}",
                recall=f"{recall:.3f}"
            )
        
        # Summarize
        print("\n" + "="*60)
        print("CROSS VALIDATION RESULTS")
        print("="*60)
        for metric_name, values in metrics.items():
            mean = np.mean(values)
            std = np.std(values)
            print(f"{metric_name.upper():12s}: {mean:.3f} ± {std:.3f}")
        
        return metrics


if __name__ == "__main__":
    from training.train_model import DriftEngineTrainer
    
    # Generate data
    trainer = DriftEngineTrainer()
    healthy, declining = trainer.generate_training_data(n_healthy=50, n_declining=20)
    
    # Cross validate
    validator = CrossValidator(n_folds=5)
    metrics = validator.run_cross_validation(healthy, declining)
