"""
Health Drift Engine - Evaluation Metrics
Comprehensive evaluation on test set
"""

import pandas as pd
import numpy as np
from typing import Dict
from sklearn.metrics import (
    roc_auc_score, roc_curve, precision_recall_curve,
    confusion_matrix, classification_report
)
import matplotlib.pyplot as plt
from training.train_model import DriftEngineTrainer
from utils.logger import get_logger

logger = get_logger()


class ModelEvaluator:
    """Evaluate trained drift engine"""
    
    def __init__(self):
        self.trainer = DriftEngineTrainer()
        # Load trained model
        self.trainer.load_calibration_params()
    
    def evaluate_on_test_set(
        self,
        test_healthy_df: pd.DataFrame,
        test_declining_df: pd.DataFrame
    ) -> Dict:
        """
        Evaluate on held-out test set
        
        Returns:
            Dictionary with evaluation metrics
        """
        logger.info("Evaluating on test set")
        
        X_test = []
        y_test = []
        user_ids = []
        
        # Process test users
        for user_id in test_healthy_df['userId'].unique():
            user_data = test_healthy_df[test_healthy_df['userId'] == user_id]
            try:
                processed = self.trainer.process_user_data(user_data)
                risks = self.trainer.extract_domain_risks(processed)
                X_test.append([risks['Neuro'], risks['Cardio'], risks['Frailty']])
                y_test.append(0)
                user_ids.append(user_id)
            except Exception as e:
                logger.warning(f"Failed to process {user_id}: {e}")
        
        for user_id in test_declining_df['userId'].unique():
            user_data = test_declining_df[test_declining_df['userId'] == user_id]
            try:
                processed = self.trainer.process_user_data(user_data)
                risks = self.trainer.extract_domain_risks(processed)
                X_test.append([risks['Neuro'], risks['Cardio'], risks['Frailty']])
                y_test.append(1)
                user_ids.append(user_id)
            except Exception as e:
                logger.warning(f"Failed to process {user_id}: {e}")
        
        X_test = np.array(X_test)
        y_test = np.array(y_test)
        
        # Scale and predict
        X_scaled = self.trainer.scaler.transform(X_test)
        y_pred_proba = self.trainer.calibration_model.predict_proba(X_scaled)[:, 1]
        y_pred = self.trainer.calibration_model.predict(X_scaled)
        
        # Compute metrics
        auc = roc_auc_score(y_test, y_pred_proba)
        cm = confusion_matrix(y_test, y_pred)
        
        print("\n" + "="*60)
        print("TEST SET EVALUATION")
        print("="*60)
        print(f"AUC-ROC: {auc:.3f}")
        print(f"\nConfusion Matrix:")
        print(cm)
        print(f"\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Healthy', 'Declining']))
        
        return {
            'auc': auc,
            'confusion_matrix': cm.tolist(),
            'y_true': y_test.tolist(),
            'y_pred_proba': y_pred_proba.tolist(),
            'user_ids': user_ids
        }
