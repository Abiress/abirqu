import statistics
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence


@dataclass
class MetricPoint:
    ts: float
    name: str
    value: float


class QuantumTelemetry:
    def __init__(self) -> None:
        self.points: List[MetricPoint] = []

    def emit(self, name: str, value: float) -> None:
        self.points.append(MetricPoint(ts=time.time(), name=name, value=float(value)))

    def series(self, name: str) -> List[float]:
        return [p.value for p in self.points if p.name == name]

    def summary(self, name: str) -> Dict[str, float]:
        vals = self.series(name)
        if not vals:
            return {"count": 0, "mean": 0.0, "p95": 0.0}
        vals_sorted = sorted(vals)
        p95 = vals_sorted[int(0.95 * (len(vals_sorted) - 1))]
        return {"count": len(vals), "mean": float(statistics.mean(vals)), "p95": float(p95)}


class DriftMonitor:
    def detect(self, values: Sequence[float], threshold_sigma: float = 2.5) -> Dict[str, Any]:
        vals = list(map(float, values))
        if len(vals) < 3:
            return {"drift": False, "z_score": 0.0}
        mu = statistics.mean(vals[:-1])
        sigma = statistics.pstdev(vals[:-1]) or 1e-9
        z = (vals[-1] - mu) / sigma
        return {"drift": abs(z) >= threshold_sigma, "z_score": z}


class AlertManager:
    def __init__(self) -> None:
        self.alerts: List[Dict[str, Any]] = []

    def raise_alert(self, severity: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        alert = {"severity": severity, "message": message, "context": dict(context), "ts": time.time()}
        self.alerts.append(alert)
        return alert

    def active(self) -> List[Dict[str, Any]]:
        return list(self.alerts)


class QuantumOpsDashboard:
    def snapshot(self, metrics: QuantumTelemetry) -> Dict[str, Any]:
        names = sorted({p.name for p in metrics.points})
        return {"metrics": {n: metrics.summary(n) for n in names}, "total_points": len(metrics.points)}
