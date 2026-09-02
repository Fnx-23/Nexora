"""URL routing for Business Reports."""

from apps.reports.api.views import (
    CustomerOverviewExportView,
    CustomerOverviewReportView,
    ExecutiveSummaryReportView,
    ProjectPerformanceExportView,
    ProjectPerformanceReportView,
    TeamWorkloadExportView,
    TeamWorkloadReportView,
    TimeReportExportView,
    TimeReportView,
)
from django.urls import path

urlpatterns = [
    path(
        "project-performance/",
        ProjectPerformanceReportView.as_view(),
        name="report-project-performance",
    ),
    path(
        "project-performance/export/",
        ProjectPerformanceExportView.as_view(),
        name="report-project-performance-export",
    ),
    path(
        "team-workload/",
        TeamWorkloadReportView.as_view(),
        name="report-team-workload",
    ),
    path(
        "team-workload/export/",
        TeamWorkloadExportView.as_view(),
        name="report-team-workload-export",
    ),
    path(
        "time/",
        TimeReportView.as_view(),
        name="report-time",
    ),
    path(
        "time/export/",
        TimeReportExportView.as_view(),
        name="report-time-export",
    ),
    path(
        "customer-overview/",
        CustomerOverviewReportView.as_view(),
        name="report-customer-overview",
    ),
    path(
        "customer-overview/export/",
        CustomerOverviewExportView.as_view(),
        name="report-customer-overview-export",
    ),
    path(
        "summary/",
        ExecutiveSummaryReportView.as_view(),
        name="report-summary",
    ),
]
