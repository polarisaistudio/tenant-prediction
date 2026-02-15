"""
FastAPI ML Service for Tenant Churn Prediction
Provides REST API for model predictions and batch scoring
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.features.feature_engineer import TenantFeatureEngineer
from src.models.xgboost_model import XGBoostChurnModel

# Initialize FastAPI app
app = FastAPI(
    title="Tenant Churn Prediction API",
    description="ML service for predicting tenant churn and calculating risk scores",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
MODEL_PATH = Path(os.getenv("MODEL_PATH", "data/models/xgboost_churn_model.pkl"))
model: Optional[XGBoostChurnModel] = None
feature_engineer: Optional[TenantFeatureEngineer] = None


# Pydantic models for request/response
class TenantData(BaseModel):
    """Single tenant data for prediction"""

    tenant_id: str
    property_id: str
    lease_id: str

    # Tenant behavior
    avg_days_late: float = 0
    max_days_late: float = 0
    payment_count: int = 12
    autopay_enabled: bool = False
    portal_login_count: int = 10
    maintenance_count: int = 2
    complaint_count: int = 0
    tenure_months: int = 12

    # Property characteristics
    square_feet: int = 1500
    bedrooms: int = 3
    bathrooms: float = 2.0
    year_built: int = 2010
    location_score: int = Field(ge=1, le=10, default=7)
    has_garage: bool = True
    property_condition: int = Field(ge=1, le=5, default=4)

    # Financial
    monthly_rent: float = 2000
    annual_income: Optional[float] = None
    last_rent_increase_pct: float = 0.03
    payment_method: str = "ach"

    # Market data
    market_rent_median: float = 2100
    vacancy_rate: float = 0.05
    rent_growth_1yr_pct: float = 0.03

    # Temporal
    lease_end_date: str
    lease_term_months: int = 12


class PredictionRequest(BaseModel):
    """Request for single or batch predictions"""

    tenants: List[TenantData]
    include_explanation: bool = False
    risk_threshold_high: int = 80
    risk_threshold_medium: int = 50


class PredictionResponse(BaseModel):
    """Prediction response"""

    tenant_id: str
    property_id: str
    churn_probability: float
    risk_score: int
    risk_level: str
    predicted_churn: bool
    confidence: float
    explanation: Optional[Dict[str, Any]] = None
    predicted_at: str


class ModelMetrics(BaseModel):
    """Model performance metrics"""

    model_version: str
    model_type: str
    training_auc: float
    cv_auc: float
    feature_count: int
    trained_at: str


@app.on_event("startup")
async def load_model():
    """Load model on startup"""
    global model, feature_engineer

    try:
        if MODEL_PATH.exists():
            print(f"Loading model from {MODEL_PATH}")
            model = XGBoostChurnModel.load(MODEL_PATH)
            feature_engineer = TenantFeatureEngineer()
            print("Model loaded successfully")
        else:
            print(f"Model not found at {MODEL_PATH}. Train a model first.")
            model = None
            feature_engineer = TenantFeatureEngineer()
    except Exception as e:
        print(f"Error loading model: {e}")
        model = None
        feature_engineer = TenantFeatureEngineer()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "status": "ready",
        "model_version": model.model_version,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/predict", response_model=List[PredictionResponse])
async def predict_churn(request: PredictionRequest):
    """
    Predict churn probability for one or more tenants

    Returns risk scores, churn probabilities, and optional explanations
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Convert request to DataFrame
        tenant_data = pd.DataFrame([t.dict() for t in request.tenants])

        # Engineer features (simplified - in production would fetch full data)
        # For now, use the raw features directly
        feature_df = tenant_data.copy()

        # Get predictions
        probabilities = model.predict_proba(feature_df[model.feature_names])[:, 1]
        predictions = (probabilities >= 0.5).astype(int)

        # Calculate risk scores
        risk_scores = (probabilities * 100).astype(int)

        # Determine risk levels
        def get_risk_level(score: int) -> str:
            if score >= request.risk_threshold_high:
                return "HIGH"
            elif score >= request.risk_threshold_medium:
                return "MEDIUM"
            else:
                return "LOW"

        risk_levels = [get_risk_level(score) for score in risk_scores]

        # Calculate confidence (distance from decision boundary)
        confidence = np.abs(probabilities - 0.5) * 2

        # Build responses
        responses = []
        for i, tenant in enumerate(request.tenants):
            response = PredictionResponse(
                tenant_id=tenant.tenant_id,
                property_id=tenant.property_id,
                churn_probability=float(probabilities[i]),
                risk_score=int(risk_scores[i]),
                risk_level=risk_levels[i],
                predicted_churn=bool(predictions[i]),
                confidence=float(confidence[i]),
                predicted_at=datetime.utcnow().isoformat(),
            )

            # Add explanation if requested
            if request.include_explanation:
                try:
                    explanation = model.get_prediction_explanation(
                        feature_df.iloc[[i]][model.feature_names]
                    )
                    response.explanation = explanation
                except Exception as e:
                    print(f"Error generating explanation: {e}")

            responses.append(response)

        return responses

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.post("/predict/batch")
async def predict_batch(background_tasks: BackgroundTasks, lease_ids: List[str]):
    """
    Batch prediction endpoint for processing large datasets
    Returns job ID for async processing
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # In production, this would queue a background job
    job_id = f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    return {
        "job_id": job_id,
        "status": "queued",
        "lease_count": len(lease_ids),
        "estimated_completion": "2 minutes",
    }


@app.get("/model/info")
async def get_model_info() -> Dict[str, Any]:
    """Get model metadata and performance metrics"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    metadata = model.get_metadata()

    return {
        "model_version": metadata["model_version"],
        "model_type": metadata["model_type"],
        "feature_count": metadata["feature_count"],
        "training_metadata": metadata["training_metadata"],
        "model_config": metadata["config"],
    }


@app.get("/model/features")
async def get_feature_importance():
    """Get feature importance rankings"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        importance_df = model.get_feature_importance()

        return {
            "features": importance_df.to_dict(orient="records"),
            "top_10": importance_df.head(10).to_dict(orient="records"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/model/reload")
async def reload_model():
    """Reload model from disk (useful after retraining)"""
    global model

    try:
        if MODEL_PATH.exists():
            model = XGBoostChurnModel.load(MODEL_PATH)
            return {
                "status": "success",
                "message": "Model reloaded",
                "model_version": model.model_version,
            }
        else:
            raise HTTPException(status_code=404, detail="Model file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload error: {str(e)}")


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    # In production, implement proper Prometheus metrics
    return {
        "predictions_total": 0,
        "prediction_latency_ms": 0,
        "model_version": model.model_version if model else "none",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("ML_SERVICE_PORT", 8000))

    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True, log_level="info")
