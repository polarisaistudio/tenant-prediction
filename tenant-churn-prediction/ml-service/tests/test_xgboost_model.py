"""
Unit Tests for XGBoost Churn Model
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.append(str(Path(__file__).parent.parent))

from src.models.xgboost_model import XGBoostChurnModel


@pytest.fixture
def sample_data():
    """Generate sample training data"""
    np.random.seed(42)
    n_samples = 1000

    X = pd.DataFrame(
        {
            "avg_days_late": np.random.uniform(0, 15, n_samples),
            "payment_count": np.random.randint(6, 36, n_samples),
            "tenure_months": np.random.randint(1, 60, n_samples),
            "monthly_rent": np.random.uniform(1500, 3500, n_samples),
            "property_age": np.random.randint(5, 50, n_samples),
            "condition_rating": np.random.randint(1, 6, n_samples),
            "complaint_count": np.random.randint(0, 5, n_samples),
        }
    )

    # Generate labels with some correlation to features
    y = (
        (X["avg_days_late"] > 5) & (X["complaint_count"] > 1)
        | (X["condition_rating"] < 3)
    ).astype(int)

    return X, y


@pytest.fixture
def trained_model(sample_data):
    """Train a model for testing"""
    X, y = sample_data
    X_train = X.iloc[:800]
    y_train = y.iloc[:800]

    model = XGBoostChurnModel()
    model.train(X_train, y_train)

    return model


def test_model_initialization():
    """Test model initialization"""
    model = XGBoostChurnModel()

    assert model is not None
    assert model.model is not None
    assert model.model_config is not None
    assert "max_depth" in model.model_config


def test_model_training(sample_data):
    """Test model training"""
    X, y = sample_data

    model = XGBoostChurnModel()
    results = model.train(X, y)

    assert "training_metrics" in results
    assert "metadata" in results
    assert model.feature_names is not None
    assert len(model.feature_names) == X.shape[1]


def test_predictions(trained_model, sample_data):
    """Test model predictions"""
    X, y = sample_data
    X_test = X.iloc[800:]

    predictions = trained_model.predict(X_test)

    assert len(predictions) == len(X_test)
    assert all(p in [0, 1] for p in predictions)


def test_predict_proba(trained_model, sample_data):
    """Test probability predictions"""
    X, y = sample_data
    X_test = X.iloc[800:]

    probas = trained_model.predict_proba(X_test)

    assert probas.shape == (len(X_test), 2)
    assert np.all((probas >= 0) & (probas <= 1))
    assert np.allclose(probas.sum(axis=1), 1.0)


def test_evaluate(trained_model, sample_data):
    """Test model evaluation"""
    X, y = sample_data
    X_test = X.iloc[800:]
    y_test = y.iloc[800:]

    metrics = trained_model.evaluate(X_test, y_test)

    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "roc_auc" in metrics

    assert 0 <= metrics["accuracy"] <= 1
    assert 0 <= metrics["roc_auc"] <= 1


def test_feature_importance(trained_model):
    """Test feature importance extraction"""
    importance_df = trained_model.get_feature_importance()

    assert isinstance(importance_df, pd.DataFrame)
    assert "feature" in importance_df.columns
    assert "importance" in importance_df.columns
    assert len(importance_df) > 0


def test_risk_scoring(trained_model, sample_data):
    """Test risk score generation"""
    X, _ = sample_data
    X_test = X.iloc[800:810]

    risk_scores = trained_model.predict_risk_score(X_test)

    assert "risk_score" in risk_scores.columns
    assert "risk_level" in risk_scores.columns
    assert "churn_probability" in risk_scores.columns

    assert all(0 <= score <= 100 for score in risk_scores["risk_score"])
    assert all(
        level in ["LOW", "MEDIUM", "HIGH"] for level in risk_scores["risk_level"]
    )


def test_model_save_load(trained_model, tmp_path):
    """Test model save and load"""
    model_path = tmp_path / "test_model.pkl"

    # Save model
    trained_model.save(model_path)
    assert model_path.exists()

    # Load model
    loaded_model = XGBoostChurnModel.load(model_path)

    assert loaded_model is not None
    assert loaded_model.feature_names == trained_model.feature_names
    assert loaded_model.model_version == trained_model.model_version


def test_prediction_explanation(trained_model, sample_data):
    """Test prediction explanation"""
    X, _ = sample_data
    X_single = X.iloc[[800]]

    explanation = trained_model.get_prediction_explanation(X_single)

    assert "churn_probability" in explanation
    assert "predicted_class" in explanation
    assert "risk_level" in explanation
    assert "top_contributing_features" in explanation
    assert len(explanation["top_contributing_features"]) == 5


def test_metadata(trained_model):
    """Test model metadata"""
    metadata = trained_model.get_metadata()

    assert "model_version" in metadata
    assert "model_type" in metadata
    assert "feature_count" in metadata
    assert metadata["model_type"] == "XGBoostChurnModel"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
