"""
Model Training Script
Train and evaluate tenant churn prediction models
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.features.feature_engineer import TenantFeatureEngineer
from src.models.xgboost_model import XGBoostChurnModel
from src.utils.data_loader import DataLoader
from src.utils.snowflake_connector import SnowflakeConnector


def load_training_data(source: str = "local") -> tuple:
    """
    Load training data from specified source

    Args:
        source: 'local', 'snowflake', or 'mongodb'

    Returns:
        Tuple of (features, labels, metadata)
    """
    print(f"Loading training data from {source}...")

    if source == "snowflake":
        connector = SnowflakeConnector()
        query = """
        SELECT *
        FROM TENANT_ANALYTICS.ANALYTICS.CHURN_TRAINING_DATA
        WHERE training_set = TRUE
        """
        df = connector.execute_query(query)
    elif source == "mongodb":
        loader = DataLoader()
        df = loader.load_from_mongodb()
    else:
        # Load from local CSV (for development)
        data_path = Path(__file__).parent.parent.parent / "data" / "processed"
        df = pd.read_csv(data_path / "training_data.csv")

    # Separate features and target
    target_col = "churned"

    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in data")

    y = df[target_col]
    X = df.drop(
        columns=[target_col, "tenant_id", "lease_id", "property_id"], errors="ignore"
    )

    metadata = {
        "total_samples": len(df),
        "churn_rate": y.mean(),
        "feature_count": len(X.columns),
        "data_source": source,
        "loaded_at": datetime.utcnow().isoformat(),
    }

    print(f"Loaded {len(df)} samples with {len(X.columns)} features")
    print(f"Churn rate: {y.mean():.2%}")

    return X, y, metadata


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    config: dict = None,
    tune_hyperparameters: bool = False,
) -> XGBoostChurnModel:
    """
    Train churn prediction model

    Args:
        X: Feature matrix
        y: Target labels
        config: Model configuration
        tune_hyperparameters: Whether to perform hyperparameter tuning

    Returns:
        Trained model
    """
    print("\n" + "=" * 60)
    print("TRAINING TENANT CHURN PREDICTION MODEL")
    print("=" * 60)

    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"\nTrain set: {len(X_train)} samples")
    print(f"Validation set: {len(X_val)} samples")

    # Handle class imbalance
    churn_rate = y_train.mean()
    scale_pos_weight = (1 - churn_rate) / churn_rate

    if config is None:
        config = {}
    config["scale_pos_weight"] = scale_pos_weight

    # Initialize model
    model = XGBoostChurnModel(config)

    # Hyperparameter tuning (optional)
    if tune_hyperparameters:
        print("\nPerforming hyperparameter tuning...")
        model.tune_hyperparameters(X_train, y_train)

    # Train model
    print("\nTraining model...")
    training_results = model.train(
        X_train, y_train, X_val, y_val, early_stopping_rounds=10
    )

    # Print results
    print("\n" + "-" * 60)
    print("TRAINING RESULTS")
    print("-" * 60)

    train_metrics = training_results["training_metrics"]
    val_metrics = training_results["validation_metrics"]

    print(f"\nTraining Set:")
    print(f"  AUC:       {train_metrics['roc_auc']:.4f}")
    print(f"  Accuracy:  {train_metrics['accuracy']:.4f}")
    print(f"  Precision: {train_metrics['precision']:.4f}")
    print(f"  Recall:    {train_metrics['recall']:.4f}")
    print(f"  F1 Score:  {train_metrics['f1_score']:.4f}")

    print(f"\nValidation Set:")
    print(f"  AUC:       {val_metrics['roc_auc']:.4f}")
    print(f"  Accuracy:  {val_metrics['accuracy']:.4f}")
    print(f"  Precision: {val_metrics['precision']:.4f}")
    print(f"  Recall:    {val_metrics['recall']:.4f}")
    print(f"  F1 Score:  {val_metrics['f1_score']:.4f}")

    print("\n" + "-" * 60)

    # Feature importance
    print("\nTop 10 Most Important Features:")
    print("-" * 60)
    importance_df = model.get_feature_importance()
    for idx, row in importance_df.head(10).iterrows():
        print(f"  {row['feature']:30s} {row['importance']:.4f}")

    return model


def save_model_and_metadata(model: XGBoostChurnModel, metadata: dict, output_dir: Path):
    """Save trained model and metadata"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save model
    model_path = output_dir / "xgboost_churn_model.pkl"
    model.save(model_path)

    # Save metadata
    metadata_path = output_dir / "model_metadata.json"
    full_metadata = {**metadata, **model.get_metadata()}

    with open(metadata_path, "w") as f:
        json.dump(full_metadata, f, indent=2)

    # Save feature importance
    importance_df = model.get_feature_importance()
    importance_path = output_dir / "feature_importance.csv"
    importance_df.to_csv(importance_path, index=False)

    print(f"\nModel artifacts saved to {output_dir}")
    print(f"  - Model: {model_path.name}")
    print(f"  - Metadata: {metadata_path.name}")
    print(f"  - Feature Importance: {importance_path.name}")


def main():
    """Main training pipeline"""
    parser = argparse.ArgumentParser(description="Train tenant churn prediction model")
    parser.add_argument(
        "--data-source",
        type=str,
        default="local",
        choices=["local", "snowflake", "mongodb"],
        help="Data source for training",
    )
    parser.add_argument(
        "--tune", action="store_true", help="Perform hyperparameter tuning"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/models",
        help="Output directory for model artifacts",
    )

    args = parser.parse_args()

    try:
        # Load data
        X, y, metadata = load_training_data(args.data_source)

        # Train model
        model = train_model(X, y, tune_hyperparameters=args.tune)

        # Save model
        output_dir = Path(args.output_dir)
        save_model_and_metadata(model, metadata, output_dir)

        print("\n" + "=" * 60)
        print("TRAINING COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during training: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
