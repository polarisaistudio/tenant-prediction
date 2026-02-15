/**
 * Dashboard Home Page
 * Main tenant churn prediction dashboard
 */
'use client';

import { useState } from 'react';
import { useDashboardData } from '@/hooks/useDashboardData';
import RiskSummaryCards from '@/components/dashboard/RiskSummaryCards';
import ChurnRiskMap from '@/components/dashboard/ChurnRiskMap';
import RiskTrendChart from '@/components/dashboard/RiskTrendChart';
import HighRiskTenantsList from '@/components/dashboard/HighRiskTenantsList';
import CampaignMetrics from '@/components/dashboard/CampaignMetrics';
import Filters from '@/components/dashboard/Filters';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import ErrorMessage from '@/components/common/ErrorMessage';

export default function DashboardPage() {
  const [filters, setFilters] = useState({
    riskLevel: 'all',
    daysToExpiration: 90,
    neighborhood: 'all'
  });

  const { data, isLoading, error, mutate } = useDashboardData(filters);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <ErrorMessage
          title="Failed to load dashboard data"
          message={error.message}
          onRetry={() => mutate()}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Tenant Churn Prediction
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                AI-powered retention insights for 80,000+ properties
              </p>
            </div>
            <button
              onClick={() => mutate()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Refresh Data
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Filters */}
        <div className="mb-6">
          <Filters
            filters={filters}
            onChange={setFilters}
            neighborhoods={data?.neighborhoods || []}
          />
        </div>

        {/* Risk Summary Cards */}
        <div className="mb-8">
          <RiskSummaryCards
            summary={data?.riskSummary}
            turnoverCost={4000}
          />
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Churn Risk Map */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Denver Metro Risk Heatmap
            </h2>
            <ChurnRiskMap
              properties={data?.properties}
              center={[39.7392, -104.9903]} // Denver coordinates
              zoom={11}
            />
          </div>

          {/* Risk Trend Chart */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Churn Risk Trends
            </h2>
            <RiskTrendChart
              data={data?.trendData}
              timeRange="30d"
            />
          </div>
        </div>

        {/* High Risk Tenants Table */}
        <div className="mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                High-Risk Tenants ({data?.highRiskTenants?.length || 0})
              </h2>
              <span className="text-sm text-gray-500">
                Requires immediate attention
              </span>
            </div>
            <HighRiskTenantsList
              tenants={data?.highRiskTenants}
              onActionTrigger={(leaseId, action) => {
                // Handle retention action trigger
                console.log('Trigger action:', action, 'for lease:', leaseId);
              }}
            />
          </div>
        </div>

        {/* Campaign Metrics */}
        <div className="mb-8">
          <CampaignMetrics
            metrics={data?.campaignMetrics}
            roi={data?.campaignROI}
          />
        </div>

        {/* Quick Stats Footer */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
            <div className="text-sm text-gray-600">Predicted This Month</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {data?.monthlyStats?.predictedCount || 0}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
            <div className="text-sm text-gray-600">Campaigns Sent</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {data?.monthlyStats?.campaignsSent || 0}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
            <div className="text-sm text-gray-600">Avg Response Rate</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">
              {data?.monthlyStats?.responseRate || 0}%
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
            <div className="text-sm text-gray-600">Model Accuracy</div>
            <div className="text-2xl font-bold text-green-600 mt-1">
              {data?.modelInfo?.accuracy || 85}%
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
