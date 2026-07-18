"""Security Dashboard analytics package."""

from kdbxstudio.application.security_dashboard.analyzer import (
    SecurityDashboardAnalyzer,
)
from kdbxstudio.application.security_dashboard.models import DashboardSnapshot

__all__ = ["DashboardSnapshot", "SecurityDashboardAnalyzer"]
