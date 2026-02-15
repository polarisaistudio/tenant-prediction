# ============================================================================
# Looker View: Churn Predictions
# Dimensional view for churn prediction analysis
# ============================================================================

view: churn_predictions {
  sql_table_name: TENANT_ANALYTICS.ANALYTICS.FACT_CHURN_PREDICTIONS ;;

  # ============================================================================
  # Dimensions
  # ============================================================================

  dimension: prediction_key {
    type: number
    primary_key: yes
    sql: ${TABLE}.prediction_key ;;
    hidden: yes
  }

  dimension: tenant_key {
    type: number
    sql: ${TABLE}.tenant_key ;;
    hidden: yes
  }

  dimension: property_key {
    type: number
    sql: ${TABLE}.property_key ;;
    hidden: yes
  }

  dimension: lease_id {
    type: string
    sql: ${TABLE}.lease_id ;;
    link: {
      label: "View Lease Details"
      url: "/dashboards/lease_detail?lease_id={{ value }}"
    }
  }

  # Date dimensions
  dimension_group: prediction {
    type: time
    timeframes: [date, week, month, quarter, year]
    sql: ${TABLE}.predicted_at ;;
  }

  dimension_group: lease_end {
    type: time
    timeframes: [date, week, month, quarter, year]
    sql: TO_DATE(${TABLE}.lease_end_date_key::STRING, 'YYYYMMDD') ;;
  }

  # Prediction metrics
  dimension: churn_probability {
    type: number
    sql: ${TABLE}.churn_probability ;;
    value_format_name: percentage_2
  }

  dimension: risk_score {
    type: number
    sql: ${TABLE}.risk_score ;;
    value_format: "0"
  }

  dimension: risk_level {
    type: string
    sql: ${TABLE}.risk_level ;;

    html:
      {% if value == 'HIGH' %}
        <span style="color: red; font-weight: bold;">{{ value }}</span>
      {% elsif value == 'MEDIUM' %}
        <span style="color: orange; font-weight: bold;">{{ value }}</span>
      {% else %}
        <span style="color: green;">{{ value }}</span>
      {% endif %}
    ;;
  }

  dimension: predicted_churn {
    type: yesno
    sql: ${TABLE}.predicted_churn ;;
  }

  dimension: confidence_score {
    type: number
    sql: ${TABLE}.confidence_score ;;
    value_format_name: percentage_2
  }

  dimension: model_version {
    type: string
    sql: ${TABLE}.model_version ;;
  }

  # Lease context
  dimension: monthly_rent {
    type: number
    sql: ${TABLE}.monthly_rent ;;
    value_format_name: usd_currency
  }

  dimension: lease_term_months {
    type: number
    sql: ${TABLE}.lease_term_months ;;
  }

  dimension: tenure_months {
    type: number
    sql: ${TABLE}.tenure_months ;;
  }

  dimension: days_to_expiration {
    type: number
    sql: ${TABLE}.days_to_expiration ;;
  }

  dimension: expiration_window {
    type: tier
    tiers: [30, 60, 90, 120]
    style: integer
    sql: ${days_to_expiration} ;;
  }

  dimension: renewal_count {
    type: number
    sql: ${TABLE}.renewal_count ;;
  }

  # Feature dimensions
  dimension: avg_days_late {
    type: number
    sql: ${TABLE}.avg_days_late ;;
    value_format: "0.0"
  }

  dimension: payment_consistency {
    type: number
    sql: ${TABLE}.payment_consistency ;;
    value_format_name: percentage_1
  }

  dimension: portal_engagement_score {
    type: number
    sql: ${TABLE}.portal_engagement_score ;;
    value_format: "0.0"
  }

  dimension: rent_to_market_ratio {
    type: number
    sql: ${TABLE}.rent_to_market_ratio ;;
    value_format: "0.00"
  }

  # Tiered dimensions for analysis
  dimension: risk_score_tier {
    type: tier
    tiers: [20, 40, 60, 80]
    style: integer
    sql: ${risk_score} ;;
  }

  dimension: tenure_tier {
    type: tier
    tiers: [6, 12, 24, 36, 60]
    style: integer
    sql: ${tenure_months} ;;
  }

  dimension: rent_tier {
    type: tier
    tiers: [1500, 2000, 2500, 3000, 4000]
    style: integer
    sql: ${monthly_rent} ;;
  }

  # ============================================================================
  # Measures
  # ============================================================================

  measure: count {
    type: count
    drill_fields: [detail*]
  }

  measure: count_high_risk {
    type: count
    filters: [risk_level: "HIGH"]
    drill_fields: [detail*]
  }

  measure: count_medium_risk {
    type: count
    filters: [risk_level: "MEDIUM"]
    drill_fields: [detail*]
  }

  measure: count_low_risk {
    type: count
    filters: [risk_level: "LOW"]
    drill_fields: [detail*]
  }

  measure: count_predicted_churn {
    type: count
    filters: [predicted_churn: "yes"]
  }

  measure: average_risk_score {
    type: average
    sql: ${risk_score} ;;
    value_format: "0.0"
  }

  measure: average_churn_probability {
    type: average
    sql: ${churn_probability} ;;
    value_format_name: percentage_1
  }

  measure: median_risk_score {
    type: median
    sql: ${risk_score} ;;
    value_format: "0"
  }

  measure: total_monthly_rent_at_risk {
    type: sum
    sql: ${monthly_rent} ;;
    filters: [risk_level: "HIGH"]
    value_format_name: usd_currency
  }

  measure: estimated_turnover_cost {
    type: number
    sql: ${count_high_risk} * 4000 ;;
    value_format_name: usd_currency
    description: "High-risk leases * $4,000 avg turnover cost"
  }

  measure: average_tenure_months {
    type: average
    sql: ${tenure_months} ;;
    value_format: "0.0"
  }

  measure: average_days_to_expiration {
    type: average
    sql: ${days_to_expiration} ;;
    value_format: "0"
  }

  measure: churn_rate {
    type: number
    sql: ${count_predicted_churn}::FLOAT / NULLIF(${count}, 0) ;;
    value_format_name: percentage_1
  }

  measure: high_risk_percentage {
    type: number
    sql: ${count_high_risk}::FLOAT / NULLIF(${count}, 0) ;;
    value_format_name: percentage_1
  }

  # ============================================================================
  # Drill Fields
  # ============================================================================

  set: detail {
    fields: [
      lease_id,
      tenants.full_name,
      properties.address,
      risk_level,
      risk_score,
      churn_probability,
      days_to_expiration,
      monthly_rent,
      tenure_months
    ]
  }
}
