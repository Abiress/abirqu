"""
Task 20.4 — Production Monitoring.

Monitor production quantum systems.
Collect metrics, alerts, and health checks.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import json


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """A metric for monitoring."""
    name: str
    type: MetricType
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    help_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type.value,
            'value': self.value,
            'labels': self.labels,
            'timestamp': self.timestamp,
            'help': self.help_text
        }


@dataclass
class Alert:
    """An alert in the monitoring system."""
    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    source: str  # Where the alert originated.
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'name': self.name,
            'severity': self.severity.value,
            'message': self.message,
            'source': self.source,
            'timestamp': self.timestamp,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at
        }
    
    def resolve(self):
        """Resolve the alert."""
        self.resolved = True
        self.resolved_at = time.time()


@dataclass
class MonitoringDashboard:
    """Dashboard for visualization."""
    dashboard_id: str
    name: str
    panels: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'dashboard_id': self.dashboard_id,
            'name': self.name,
            'panel_count': len(self.panels),
            'panels': self.panels,
            'created_at': self.created_at
        }
    
    def add_panel(self, title: str, metric_name: str,
                  chart_type: str = "line"):
        """Add a panel to the dashboard."""
        panel = {
            'title': title,
            'metric': metric_name,
            'chart_type': chart_type,
            'panel_id': len(self.panels)
        }
        self.panels.append(panel)


class MetricCollector:
    """Collect and store metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = {}
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
    
    def record_metric(self, metric: Metric):
        """Record a metric value."""
        if metric.name not in self.metrics:
            self.metrics[metric.name] = []
        
        self.metrics[metric.name].append(metric)
        
        # Update current values.
        if metric.type == MetricType.COUNTER:
            self.counters[metric.name] = self.counters.get(metric.name, 0) + metric.value
        elif metric.type == MetricType.GAUGE:
            self.gauges[metric.name] = metric.value
    
    def get_metric(self, name: str, 
                  start_time: Optional[float] = None,
                  end_time: Optional[float] = None) -> List[Metric]:
        """Get metric values within time range."""
        if name not in self.metrics:
            return []
        
        metrics = self.metrics[name]
        
        if start_time is None and end_time is None:
            return metrics
        
        filtered = []
        for m in metrics:
            if start_time and m.timestamp < start_time:
                continue
            if end_time and m.timestamp > end_time:
                continue
            filtered.append(m)
        
        return filtered
    
    def get_current_value(self, name: str) -> Optional[float]:
        """Get current value of a metric."""
        if name in self.gauges:
            return self.gauges[name]
        if name in self.counters:
            return self.counters[name]
        return None
    
    def get_summary(self, name: str) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        metrics = self.metrics.get(name, [])
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        return {
            'count': len(values),
            'sum': sum(values),
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values)
        }


class AlertManager:
    """Manage alerts."""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.handlers: List[Callable] = []
        self.alert_counter = 0
    
    def raise_alert(self, name: str, severity: AlertSeverity,
                    message: str, source: str) -> Alert:
        """Raise a new alert."""
        self.alert_counter += 1
        alert_id = f"alert_{self.alert_counter}"
        
        alert = Alert(
            alert_id=alert_id,
            name=name,
            severity=severity,
            message=message,
            source=source
        )
        
        self.alerts[alert_id] = alert
        
        # Call handlers.
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception:
                pass
        
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        if alert_id not in self.alerts:
            return False
        
        self.alerts[alert_id].resolve()
        return True
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all unresolved alerts."""
        return [a for a in self.alerts.values() if not a.resolved]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get alerts filtered by severity."""
        return [a for a in self.alerts.values() 
                if a.severity == severity and not a.resolved]
    
    def register_handler(self, handler: Callable):
        """Register an alert handler."""
        self.handlers.append(handler)


class HealthChecker:
    """System health checks."""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, Tuple[bool, str]] = {}
    
    def register_check(self, name: str, check_fn: Callable) -> bool:
        """Register a health check."""
        self.checks[name] = check_fn
        return True
    
    def run_check(self, name: str) -> Tuple[bool, str]:
        """Run a single health check."""
        if name not in self.checks:
            return False, f"Check '{name}' not found"
        
        try:
            result = self.checks[name]()
            success = bool(result)
            message = "OK" if success else str(result)
        except Exception as e:
            success = False
            message = str(e)
        
        self.last_results[name] = (success, message)
        return success, message
    
    def run_all_checks(self) -> Dict[str, Tuple[bool, str]]:
        """Run all health checks."""
        results = {}
        for name in self.checks:
            results[name] = self.run_check(name)
        return results
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        if not self.last_results:
            self.run_all_checks()
        
        total = len(self.last_results)
        healthy = sum(1 for r in self.last_results.values() if r[0])
        
        return {
            'total_checks': total,
            'healthy': healthy,
            'unhealthy': total - healthy,
            'health_percentage': (healthy / max(total, 1)) * 100,
            'status': 'healthy' if healthy == total else 
                     'degraded' if healthy > 0 else 'unhealthy'
        }


class ProductionMonitor:
    """Main production monitoring system."""
    
    def __init__(self):
        self.collector = MetricCollector()
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
        self.dashboards: Dict[str, MonitoringDashboard] = {}
        self.monitoring_active = False
        self.start_time: Optional[float] = None
    
    def start_monitoring(self):
        """Start production monitoring."""
        self.monitoring_active = True
        self.start_time = time.time()
        
        # Register default health checks.
        self.health_checker.register_check(
            "system_uptime",
            lambda: (time.time() - self.start_time) > 0
        )
        
        return True
    
    def stop_monitoring(self):
        """Stop monitoring."""
        self.monitoring_active = False
        return True
    
    def record_metric(self, name: str, value: float,
                      type: MetricType = MetricType.GAUGE,
                      labels: Optional[Dict[str, str]] = None,
                      help_text: str = "") -> Metric:
        """Record a metric."""
        metric = Metric(
            name=name,
            type=type,
            value=value,
            labels=labels or {},
            help_text=help_text
        )
        
        self.collector.record_metric(metric)
        return metric
    
    def increment_counter(self, name: str,
                         value: float = 1.0,
                         labels: Optional[Dict[str, str]] = None) -> Metric:
        """Increment a counter metric."""
        return self.record_metric(
            name=name,
            value=value,
            type=MetricType.COUNTER,
            labels=labels
        )
    
    def set_gauge(self, name: str, value: float,
                  labels: Optional[Dict[str, str]] = None) -> Metric:
        """Set a gauge metric."""
        return self.record_metric(
            name=name,
            value=value,
            type=MetricType.GAUGE,
            labels=labels
        )
    
    def raise_alert(self, name: str, 
                    severity: AlertSeverity,
                    message: str,
                    source: str = "system") -> Alert:
        """Raise an alert."""
        return self.alert_manager.raise_alert(
            name=name,
            severity=severity,
            message=message,
            source=source
        )
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        return self.alert_manager.resolve_alert(alert_id)
    
    def create_dashboard(self, name: str) -> MonitoringDashboard:
        """Create a monitoring dashboard."""
        dashboard_id = f"dashboard_{len(self.dashboards) + 1}"
        
        dashboard = MonitoringDashboard(
            dashboard_id=dashboard_id,
            name=name
        )
        
        self.dashboards[dashboard_id] = dashboard
        return dashboard
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        summary = {}
        for name in self.collector.metrics:
            summary[name] = self.collector.get_summary(name)
        return summary
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts."""
        return [a.to_dict() for a in self.alert_manager.get_active_alerts()]
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run health checks."""
        return self.health_checker.get_health_status()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return {
            'monitoring_active': self.monitoring_active,
            'uptime': (time.time() - self.start_time) if self.start_time else 0,
            'total_metrics': sum(len(m) for m in self.collector.metrics.values()),
            'total_alerts': len(self.alert_manager.alerts),
            'active_alerts': len(self.alert_manager.get_active_alerts()),
            'dashboards': len(self.dashboards),
            'health_checks': len(self.health_checker.checks)
        }
