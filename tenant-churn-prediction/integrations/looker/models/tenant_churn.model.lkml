# ============================================================================
# Looker Model: Tenant Churn Analytics
# Business intelligence model for churn prediction insights
# ============================================================================

connection: "snowflake_tenant_analytics"

include: "/views/*.view.lkml"
include: "/dashboards/*.dashboard.lookml"

# ============================================================================
# Explores (Data Models)
# ============================================================================

explore: churn_predictions {
  label: "Churn Predictions"
  description: "Analyze tenant churn predictions and risk scores"

  join: tenants {
    type: left_outer
    sql_on: ${churn_predictions.tenant_key} = ${tenants.tenant_key} ;;
    relationship: many_to_one
  }

  join: properties {
    type: left_outer
    sql_on: ${churn_predictions.property_key} = ${properties.property_key} ;;
    relationship: many_to_one
  }

  join: market_conditions {
    type: left_outer
    sql_on: ${properties.zip_code} = ${market_conditions.zip_code}
        AND ${churn_predictions.prediction_date} = ${market_conditions.data_date} ;;
    relationship: many_to_one
  }

  join: retention_actions {
    type: left_outer
    sql_on: ${churn_predictions.lease_id} = ${retention_actions.lease_id} ;;
    relationship: one_to_many
  }
}

explore: lease_events {
  label: "Lease Events"
  description: "Analyze lease renewals, terminations, and lifecycle events"

  join: tenants {
    type: left_outer
    sql_on: ${lease_events.tenant_key} = ${tenants.tenant_key} ;;
    relationship: many_to_one
  }

  join: properties {
    type: left_outer
    sql_on: ${lease_events.property_key} = ${properties.property_key} ;;
    relationship: many_to_one
  }

  join: churn_predictions {
    type: left_outer
    sql_on: ${lease_events.lease_id} = ${churn_predictions.lease_id} ;;
    relationship: one_to_many
  }
}

explore: retention_campaigns {
  from: retention_actions
  label: "Retention Campaigns"
  description: "Track retention campaign performance and ROI"

  join: tenants {
    type: left_outer
    sql_on: ${retention_campaigns.tenant_key} = ${tenants.tenant_key} ;;
    relationship: many_to_one
  }

  join: properties {
    type: left_outer
    sql_on: ${retention_campaigns.property_key} = ${properties.property_key} ;;
    relationship: many_to_one
  }

  join: churn_predictions {
    type: left_outer
    sql_on: ${retention_campaigns.lease_id} = ${churn_predictions.lease_id} ;;
    relationship: many_to_one
  }
}

# ============================================================================
# Access Grants
# ============================================================================

access_grant: tenant_data_access {
  user_attribute: department
  allowed_values: ["property_management", "analytics", "executive"]
}

access_grant: pii_access {
  user_attribute: role
  allowed_values: ["admin", "property_manager"]
  required_access_grants: [tenant_data_access]
}

# ============================================================================
# Datagroups (Caching)
# ============================================================================

datagroup: daily_refresh {
  sql_trigger: SELECT CURRENT_DATE ;;
  max_cache_age: "24 hours"
}

datagroup: hourly_refresh {
  sql_trigger: SELECT FLOOR(EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)/3600) ;;
  max_cache_age: "1 hour"
}

# ============================================================================
# Named Value Formats
# ============================================================================

named_value_format: usd_currency {
  value_format: "$#,##0.00"
}

named_value_format: percentage_1 {
  value_format: "0.0%"
}

named_value_format: percentage_2 {
  value_format: "0.00%"
}
