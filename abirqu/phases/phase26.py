import json
import time
from pathlib import Path
from typing import Any, Dict, List


class AuditLog:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]")

    def append(self, event: Dict[str, Any]) -> None:
        rows = json.loads(self.path.read_text())
        rows.append({"ts": time.time(), **event})
        self.path.write_text(json.dumps(rows, indent=2))

    def read(self) -> List[Dict[str, Any]]:
        return json.loads(self.path.read_text())


class PolicyEngine:
    def evaluate(self, request: Dict[str, Any], policy: Dict[str, Any]) -> Dict[str, Any]:
        allowed_ops = set(policy.get("allowed_operations", []))
        max_shots = int(policy.get("max_shots", 4096))
        op_ok = request.get("operation") in allowed_ops
        shots_ok = int(request.get("shots", 0)) <= max_shots
        return {"allowed": op_ok and shots_ok, "op_ok": op_ok, "shots_ok": shots_ok}


class ComplianceReporter:
    def report(self, audit_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(audit_events)
        denied = sum(1 for e in audit_events if e.get("allowed") is False)
        return {
            "total_events": total,
            "denied_events": denied,
            "allow_rate": (total - denied) / total if total else 1.0,
        }
