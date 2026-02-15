"""
Feature Engineering Pipeline for Tenant Churn Prediction
Transforms raw data into ML-ready features
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from category_encoders import TargetEncoder
from sklearn.preprocessing import LabelEncoder, StandardScaler


class TenantFeatureEngineer:
    """Feature engineering for tenant churn prediction"""

    def __init__(self):
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, LabelEncoder] = {}
        self.target_encoder: Optional[TargetEncoder] = None
        self.feature_names: List[str] = []

    def engineer_features(
        self,
        tenants: pd.DataFrame,
        leases: pd.DataFrame,
        payments: pd.DataFrame,
        properties: pd.DataFrame,
        maintenance: pd.DataFrame,
        market_data: pd.DataFrame = None,
        is_training: bool = True,
    ) -> pd.DataFrame:
        """
        Generate all features for churn prediction

        Args:
            tenants: Tenant demographic data
            leases: Lease contracts
            payments: Payment history
            properties: Property characteristics
            maintenance: Maintenance requests
            market_data: Market/neighborhood analytics
            is_training: Whether this is for training (fits encoders) or prediction

        Returns:
            Feature matrix
        """
        # Merge all data sources
        df = self._merge_data_sources(
            tenants, leases, payments, properties, maintenance, market_data
        )

        # Generate feature categories
        features = pd.DataFrame(index=df.index)

        # 1. Tenant Behavior Features (15 features)
        features = pd.concat(
            [features, self._tenant_behavior_features(df, payments, maintenance)],
            axis=1,
        )

        # 2. Property Characteristics (12 features)
        features = pd.concat(
            [features, self._property_features(df, properties)], axis=1
        )

        # 3. Financial Features (8 features)
        features = pd.concat([features, self._financial_features(df, payments)], axis=1)

        # 4. Market Condition Features (10 features)
        if market_data is not None:
            features = pd.concat(
                [features, self._market_features(df, market_data)], axis=1
            )

        # 5. Temporal Features (5 features)
        features = pd.concat([features, self._temporal_features(df, leases)], axis=1)

        # Handle missing values
        features = self._handle_missing_values(features)

        # Encode categorical variables
        features = self._encode_categoricals(features, is_training)

        # Scale numerical features
        features = self._scale_features(features, is_training)

        self.feature_names = list(features.columns)

        return features

    def _merge_data_sources(
        self,
        tenants: pd.DataFrame,
        leases: pd.DataFrame,
        payments: pd.DataFrame,
        properties: pd.DataFrame,
        maintenance: pd.DataFrame,
        market_data: pd.DataFrame = None,
    ) -> pd.DataFrame:
        """Merge all data sources on common keys"""

        # Start with leases as base
        df = leases.copy()

        # Join tenants
        df = df.merge(tenants, on="tenant_id", how="left", suffixes=("", "_tenant"))

        # Join properties
        df = df.merge(
            properties, on="property_id", how="left", suffixes=("", "_property")
        )

        # Aggregate payments per lease
        payment_agg = (
            payments.groupby("lease_id")
            .agg(
                {
                    "amount": ["sum", "mean", "std", "count"],
                    "days_late": ["mean", "max", "sum"],
                    "payment_date": "max",
                }
            )
            .reset_index()
        )
        payment_agg.columns = [
            "lease_id",
            "total_paid",
            "avg_payment",
            "payment_std",
            "payment_count",
            "avg_days_late",
            "max_days_late",
            "total_days_late",
            "last_payment_date",
        ]
        df = df.merge(payment_agg, on="lease_id", how="left")

        # Aggregate maintenance per lease
        maint_agg = (
            maintenance.groupby("property_id")
            .agg(
                {
                    "request_id": "count",
                    "priority": lambda x: (x == "HIGH").sum(),
                    "resolution_days": "mean",
                }
            )
            .reset_index()
        )
        maint_agg.columns = [
            "property_id",
            "maintenance_count",
            "high_priority_count",
            "avg_resolution_days",
        ]
        df = df.merge(maint_agg, on="property_id", how="left")

        # Join market data if available
        if market_data is not None:
            df = df.merge(
                market_data, on="zip_code", how="left", suffixes=("", "_market")
            )

        return df

    def _tenant_behavior_features(
        self, df: pd.DataFrame, payments: pd.DataFrame, maintenance: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate tenant behavior-based features"""

        features = pd.DataFrame(index=df.index)

        # Payment behavior
        features["avg_days_late"] = df["avg_days_late"].fillna(0)
        features["max_days_late"] = df["max_days_late"].fillna(0)
        features["late_payment_rate"] = (
            df["total_days_late"] / df["payment_count"]
        ).fillna(0)
        features["payment_consistency"] = 1 / (1 + df["payment_std"].fillna(0))

        # Payment recency
        if "last_payment_date" in df.columns:
            features["days_since_last_payment"] = (
                pd.to_datetime("today") - pd.to_datetime(df["last_payment_date"])
            ).dt.days
        else:
            features["days_since_last_payment"] = 0

        # Auto-pay indicator
        features["has_autopay"] = df.get("autopay_enabled", 0).astype(int)

        # Portal engagement
        features["portal_logins_per_month"] = df.get("portal_login_count", 0) / (
            df.get("tenure_months", 1).clip(lower=1)
        )

        # Maintenance request behavior
        features["maintenance_requests_per_year"] = df["maintenance_count"].fillna(
            0
        ) / (df.get("tenure_months", 12) / 12).clip(lower=1)
        features["high_priority_requests"] = df["high_priority_count"].fillna(0)

        # Communication responsiveness
        features["avg_response_time_hours"] = df.get("avg_response_time_hours", 24)
        features["missed_communication_count"] = df.get("missed_communication_count", 0)

        # Complaint/escalation history
        features["complaint_count"] = df.get("complaint_count", 0)
        features["escalation_count"] = df.get("escalation_count", 0)

        # Renewal history
        features["previous_renewals"] = df.get("renewal_count", 0)
        features["tenure_months"] = df.get("tenure_months", 0)

        return features

    def _property_features(
        self, df: pd.DataFrame, properties: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate property characteristic features"""

        features = pd.DataFrame(index=df.index)

        # Physical characteristics
        features["square_feet"] = df.get("square_feet", 1500)
        features["bedrooms"] = df.get("bedrooms", 3)
        features["bathrooms"] = df.get("bathrooms", 2)
        features["property_age"] = pd.to_datetime("today").year - df.get(
            "year_built", 2000
        )

        # Location quality score (1-10)
        features["location_score"] = df.get("location_score", 5)
        features["school_rating"] = df.get("school_rating", 5)

        # Amenities
        features["has_garage"] = df.get("garage", False).astype(int)
        features["has_yard"] = df.get("yard", False).astype(int)
        features["has_ac"] = df.get("air_conditioning", False).astype(int)

        # Property condition (1-5 scale)
        features["property_condition"] = df.get("condition_rating", 3)

        # Recent renovations
        features["years_since_renovation"] = df.get("years_since_renovation", 10)

        # Neighborhood type (encoded later)
        features["neighborhood_type"] = df.get("neighborhood_type", "suburban")

        return features

    def _financial_features(
        self, df: pd.DataFrame, payments: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate financial/economic features"""

        features = pd.DataFrame(index=df.index)

        # Rent economics
        features["monthly_rent"] = df.get("monthly_rent", 2000)
        features["rent_per_sqft"] = features["monthly_rent"] / df.get(
            "square_feet", 1500
        )

        # Rent-to-income ratio (if income data available)
        if "annual_income" in df.columns:
            features["rent_to_income_ratio"] = (
                features["monthly_rent"] * 12 / df["annual_income"]
            ).clip(upper=1.0)
        else:
            features["rent_to_income_ratio"] = 0.30  # Assume 30% default

        # Rent changes
        features["rent_increase_pct"] = df.get("last_rent_increase_pct", 0)
        features["total_rent_increases"] = df.get("rent_increase_count", 0)

        # Payment method (encoded later)
        features["payment_method"] = df.get("primary_payment_method", "ach")

        # Security deposit
        features["security_deposit_months"] = (
            df.get("security_deposit", 2000) / features["monthly_rent"]
        )

        # Late fees incurred
        features["total_late_fees"] = df.get("total_late_fees", 0)

        return features

    def _market_features(
        self, df: pd.DataFrame, market_data: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate market condition features"""

        features = pd.DataFrame(index=df.index)

        # Market rent comparison
        features["market_rent_median"] = df.get("market_rent_median", 2000)
        features["rent_vs_market"] = (
            df.get("monthly_rent", 2000) / features["market_rent_median"]
        )

        # Vacancy rates
        features["neighborhood_vacancy_rate"] = df.get("vacancy_rate", 0.05)

        # Rent trends
        features["market_rent_growth_1yr"] = df.get("rent_growth_1yr_pct", 0.03)
        features["market_rent_growth_3yr"] = df.get("rent_growth_3yr_pct", 0.10)

        # Supply/demand indicators
        features["new_listings_count"] = df.get("new_listings_30d", 10)
        features["avg_days_on_market"] = df.get("avg_days_on_market", 30)

        # Demographics
        features["median_household_income"] = df.get("median_hh_income", 75000)
        features["population_growth_rate"] = df.get("population_growth_rate", 0.01)

        # Competition
        features["competitor_properties_1mi"] = df.get("competitor_count_1mi", 50)

        return features

    def _temporal_features(
        self, df: pd.DataFrame, leases: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate time-based features"""

        features = pd.DataFrame(index=df.index)

        # Days until lease expiration
        if "lease_end_date" in df.columns:
            features["days_to_expiration"] = (
                pd.to_datetime(df["lease_end_date"]) - pd.to_datetime("today")
            ).dt.days
        else:
            features["days_to_expiration"] = 90

        # Lease duration
        features["lease_term_months"] = df.get("lease_term_months", 12)

        # Seasonality
        if "lease_end_date" in df.columns:
            lease_end = pd.to_datetime(df["lease_end_date"])
            features["lease_end_month"] = lease_end.dt.month
            features["is_summer_expiration"] = lease_end.dt.month.isin(
                [6, 7, 8]
            ).astype(int)
        else:
            features["lease_end_month"] = 1
            features["is_summer_expiration"] = 0

        # Tenure
        features["tenure_months"] = df.get("tenure_months", 12)

        return features

    def _handle_missing_values(self, features: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values with appropriate strategies"""

        # Numerical: fill with median
        numerical_cols = features.select_dtypes(include=[np.number]).columns
        for col in numerical_cols:
            if features[col].isna().any():
                features[col].fillna(features[col].median(), inplace=True)

        # Categorical: fill with mode
        categorical_cols = features.select_dtypes(include=["object"]).columns
        for col in categorical_cols:
            if features[col].isna().any():
                features[col].fillna(features[col].mode()[0], inplace=True)

        return features

    def _encode_categoricals(
        self, features: pd.DataFrame, is_training: bool
    ) -> pd.DataFrame:
        """Encode categorical variables"""

        categorical_cols = features.select_dtypes(include=["object"]).columns

        for col in categorical_cols:
            if is_training:
                encoder = LabelEncoder()
                features[col] = encoder.fit_transform(features[col].astype(str))
                self.encoders[col] = encoder
            else:
                if col in self.encoders:
                    # Handle unseen categories
                    encoder = self.encoders[col]
                    features[col] = (
                        features[col]
                        .astype(str)
                        .map(
                            lambda x: (
                                encoder.transform([x])[0]
                                if x in encoder.classes_
                                else -1
                            )
                        )
                    )
                else:
                    features[col] = -1

        return features

    def _scale_features(
        self, features: pd.DataFrame, is_training: bool
    ) -> pd.DataFrame:
        """Scale numerical features"""

        # Select features to scale (exclude binary/categorical)
        scale_cols = [
            col
            for col in features.columns
            if features[col].nunique() > 2
            and np.issubdtype(features[col].dtype, np.number)
        ]

        if is_training:
            scaler = StandardScaler()
            features[scale_cols] = scaler.fit_transform(features[scale_cols])
            self.scalers["standard"] = scaler
        else:
            if "standard" in self.scalers:
                features[scale_cols] = self.scalers["standard"].transform(
                    features[scale_cols]
                )

        return features

    def get_feature_names(self) -> List[str]:
        """Return list of feature names"""
        return self.feature_names
