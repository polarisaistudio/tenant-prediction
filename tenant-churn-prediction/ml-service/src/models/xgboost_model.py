"""
XGBoost Churn Prediction Model
Primary production model with hyperparameter tuning
"""

from typing import Any, Dict

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import cross_val_score

from .base_model import BaseChurnModel


class XGBoostChurnModel(BaseChurnModel):
    """XGBoost-based tenant churn prediction model"""

    DEFAULT_PARAMS = {
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 200,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 1,
        "gamma": 0,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "scale_pos_weight": 1,  # Adjust for class imbalance
        "random_state": 42,
        "n_jobs": -1,
        "tree_method": "hist",
    }

    def __init__(self, model_config: Dict[str, Any] = None):
        """
        Initialize XGBoost model

        Args:
            model_config: Model hyperparameters (uses defaults if not provided)
        """
        config = {**self.DEFAULT_PARAMS}
        if model_config:
            config.update(model_config)

        super().__init__(config)
        self.model = xgb.XGBClassifier(**self.model_config)

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        X_val: pd.DataFrame = None,
        y_val: pd.Series = None,
        early_stopping_rounds: int = 10,
    ) -> Dict[str, Any]:
        """
        Train XGBoost model with optional validation set

        Args:
            X: Training features
            y: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            early_stopping_rounds: Early stopping patience

        Returns:
            Training metrics
        """
        from datetime import datetime

        from sklearn.model_selection import cross_val_score

        print(f"Training XGBoost model on {len(X)} samples...")

        # Store feature names
        self.feature_names = list(X.columns)

        # Prepare evaluation set
        eval_set = [(X, y)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))

        # Train model
        start_time = datetime.utcnow()

        self.model.fit(X, y, eval_set=eval_set, verbose=False)

        training_time = (datetime.utcnow() - start_time).total_seconds()

        # Cross-validation score
        cv_scores = cross_val_score(
            self.model, X, y, cv=5, scoring="roc_auc", n_jobs=-1
        )

        # Store training metadata
        self.training_metadata = {
            "training_samples": len(X),
            "training_time_seconds": training_time,
            "cv_mean_auc": float(cv_scores.mean()),
            "cv_std_auc": float(cv_scores.std()),
            "n_features": len(self.feature_names),
            "best_iteration": self.model.best_iteration
            if hasattr(self.model, "best_iteration")
            else None,
            "trained_at": datetime.utcnow().isoformat(),
        }

        # Evaluate on training set
        train_metrics = self.evaluate(X, y)

        # Evaluate on validation set if provided
        val_metrics = {}
        if X_val is not None and y_val is not None:
            val_metrics = self.evaluate(X_val, y_val)

        print(f"Training complete in {training_time:.2f}s")
        print(f"Training AUC: {train_metrics['roc_auc']:.4f}")
        print(f"CV AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

        if val_metrics:
            print(f"Validation AUC: {val_metrics['roc_auc']:.4f}")

        return {
            "training_metrics": train_metrics,
            "validation_metrics": val_metrics,
            "metadata": self.training_metadata,
        }

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict churn class (0 or 1)

        Args:
            X: Feature matrix

        Returns:
            Binary predictions
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predict churn probabilities

        Args:
            X: Feature matrix

        Returns:
            Probability matrix [no_churn_prob, churn_prob]
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        return self.model.predict_proba(X)

    def predict_risk_score(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Predict churn with risk scoring (0-100 scale)

        Args:
            X: Feature matrix

        Returns:
            DataFrame with predictions and risk scores
        """
        probabilities = self.predict_proba(X)[:, 1]

        results = pd.DataFrame(
            {
                "churn_probability": probabilities,
                "risk_score": (probabilities * 100).astype(int),
                "risk_level": [self._get_risk_level(p) for p in probabilities],
                "predicted_churn": (probabilities >= 0.5).astype(int),
            }
        )

        return results

    def tune_hyperparameters(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        param_grid: Dict[str, list] = None,
        cv: int = 5,
    ) -> Dict[str, Any]:
        """
        Perform hyperparameter tuning using GridSearchCV

        Args:
            X: Feature matrix
            y: Target labels
            param_grid: Parameter grid for search
            cv: Number of cross-validation folds

        Returns:
            Best parameters and scores
        """
        from sklearn.model_selection import GridSearchCV

        if param_grid is None:
            param_grid = {
                "max_depth": [4, 6, 8],
                "learning_rate": [0.01, 0.1, 0.2],
                "n_estimators": [100, 200, 300],
                "subsample": [0.7, 0.8, 0.9],
                "colsample_bytree": [0.7, 0.8, 0.9],
            }

        print(f"Tuning hyperparameters with {cv}-fold CV...")

        grid_search = GridSearchCV(
            self.model, param_grid, cv=cv, scoring="roc_auc", n_jobs=-1, verbose=1
        )

        grid_search.fit(X, y)

        # Update model with best parameters
        self.model_config.update(grid_search.best_params_)
        self.model = grid_search.best_estimator_

        results = {
            "best_params": grid_search.best_params_,
            "best_score": grid_search.best_score_,
            "cv_results": pd.DataFrame(grid_search.cv_results_),
        }

        print(f"Best AUC: {grid_search.best_score_:.4f}")
        print(f"Best params: {grid_search.best_params_}")

        return results

    def get_shap_values(self, X: pd.DataFrame, sample_size: int = 100):
        """
        Calculate SHAP values for model interpretability

        Args:
            X: Feature matrix
            sample_size: Number of samples for SHAP calculation

        Returns:
            SHAP values
        """
        try:
            import shap

            # Sample data for performance
            X_sample = X.sample(min(sample_size, len(X)), random_state=42)

            explainer = shap.TreeExplainer(self.model)
            shap_values = explainer.shap_values(X_sample)

            return {
                "shap_values": shap_values,
                "base_value": explainer.expected_value,
                "feature_names": self.feature_names,
                "data": X_sample,
            }
        except ImportError:
            print("SHAP library not installed. Install with: pip install shap")
            return None
