"""
Base Model Abstract Class
Defines interface for all churn prediction models
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
import json
from pathlib import Path


class BaseChurnModel(ABC):
    """Abstract base class for tenant churn prediction models"""

    def __init__(self, model_config: Dict[str, Any]):
        self.model_config = model_config
        self.model = None
        self.feature_names: Optional[list] = None
        self.training_metadata: Dict[str, Any] = {}
        self.model_version = model_config.get('version', '1.0.0')

    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """
        Train the model on provided data

        Args:
            X: Feature matrix
            y: Target labels (0=renewed, 1=churned)

        Returns:
            Training metrics and metadata
        """
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict churn probability

        Args:
            X: Feature matrix

        Returns:
            Array of churn probabilities
        """
        pass

    @abstractmethod
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict class probabilities

        Args:
            X: Feature matrix

        Returns:
            Array of [no_churn_prob, churn_prob] for each sample
        """
        pass

    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        Evaluate model performance

        Args:
            X: Feature matrix
            y: True labels

        Returns:
            Dictionary of evaluation metrics
        """
        from sklearn.metrics import (
            roc_auc_score,
            accuracy_score,
            precision_score,
            recall_score,
            f1_score,
            confusion_matrix,
            classification_report
        )

        y_pred = self.predict(X)
        y_proba = self.predict_proba(X)[:, 1]

        metrics = {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred, zero_division=0),
            'recall': recall_score(y, y_pred, zero_division=0),
            'f1_score': f1_score(y, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y, y_proba),
        }

        # Confusion matrix
        tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()
        metrics.update({
            'true_negatives': int(tn),
            'false_positives': int(fp),
            'false_negatives': int(fn),
            'true_positives': int(tp),
            'specificity': tn / (tn + fp) if (tn + fp) > 0 else 0,
        })

        return metrics

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance scores

        Returns:
            DataFrame with features and their importance scores
        """
        if not hasattr(self.model, 'feature_importances_'):
            raise NotImplementedError("Model does not support feature importance")

        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)

        return importance_df

    def save(self, filepath: Path) -> None:
        """
        Save model to disk

        Args:
            filepath: Path to save model
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'model_config': self.model_config,
            'training_metadata': self.training_metadata,
            'model_version': self.model_version,
            'saved_at': datetime.utcnow().isoformat()
        }

        joblib.dump(model_data, filepath)
        print(f"Model saved to {filepath}")

    @classmethod
    def load(cls, filepath: Path) -> 'BaseChurnModel':
        """
        Load model from disk

        Args:
            filepath: Path to saved model

        Returns:
            Loaded model instance
        """
        model_data = joblib.load(filepath)

        instance = cls(model_data['model_config'])
        instance.model = model_data['model']
        instance.feature_names = model_data['feature_names']
        instance.training_metadata = model_data['training_metadata']
        instance.model_version = model_data['model_version']

        return instance

    def get_prediction_explanation(
        self,
        X: pd.DataFrame,
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Get explanation for predictions

        Args:
            X: Feature matrix (single row)
            top_n: Number of top features to return

        Returns:
            Dictionary with prediction and top contributing features
        """
        if len(X) != 1:
            raise ValueError("Explanation requires single sample")

        proba = self.predict_proba(X)[0, 1]
        prediction = int(proba >= 0.5)

        # Get feature contributions (simplified)
        feature_values = X.iloc[0].to_dict()
        importance = self.get_feature_importance()
        top_features = importance.head(top_n)

        explanation = {
            'churn_probability': float(proba),
            'predicted_class': prediction,
            'risk_level': self._get_risk_level(proba),
            'top_contributing_features': [
                {
                    'feature': row['feature'],
                    'importance': float(row['importance']),
                    'value': feature_values.get(row['feature'])
                }
                for _, row in top_features.iterrows()
            ]
        }

        return explanation

    @staticmethod
    def _get_risk_level(probability: float) -> str:
        """Map probability to risk level"""
        if probability >= 0.8:
            return 'HIGH'
        elif probability >= 0.5:
            return 'MEDIUM'
        else:
            return 'LOW'

    def get_metadata(self) -> Dict[str, Any]:
        """Get model metadata"""
        return {
            'model_version': self.model_version,
            'model_type': self.__class__.__name__,
            'training_metadata': self.training_metadata,
            'feature_count': len(self.feature_names) if self.feature_names else 0,
            'config': self.model_config
        }
