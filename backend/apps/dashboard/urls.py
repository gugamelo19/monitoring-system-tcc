from django.urls import path

from .views import (
    DashboardSummaryView,
    DashboardProtocolsView,
    DashboardSeverityView,
    DashboardRecentEventsView,
    DashboardRecentAlertsView,
    DashboardAssetStatusView,
    DashboardAnomalyTypesView,
)

urlpatterns = [
    path("summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("protocols/", DashboardProtocolsView.as_view(),
         name="dashboard-protocols"),
    path("severity/", DashboardSeverityView.as_view(), name="dashboard-severity"),
    path("recent-events/", DashboardRecentEventsView.as_view(),
         name="dashboard-recent-events"),
    path("recent-alerts/", DashboardRecentAlertsView.as_view(),
         name="dashboard-recent-alerts"),
    path("assets-status/", DashboardAssetStatusView.as_view(),
         name="dashboard-assets-status"),
    path("anomaly-types/", DashboardAnomalyTypesView.as_view(),
         name="dashboard-anomaly-types"),
]
