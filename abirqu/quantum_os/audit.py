"""
Audit Trail
===========
Comprehensive logging and tracking for quantum OS operations.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class AuditEvent:
    """A single audit event record."""
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)
    user_id: str = ""
    action: str = ""
    resource: str = ""
    details: Dict = field(default_factory=dict)
    status: str = "success"
    ip_address: str = ""

    @property
    def iso_timestamp(self) -> str:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat()


class AuditLogger:
    """In-memory audit logger with optional JSON file persistence.

    Parameters
    ----------
    persist_path : str, optional
        If set, events are flushed to this JSON file on each write.
    """

    def __init__(self, persist_path: Optional[str] = None):
        self._events: List[AuditEvent] = []
        self.persist_path = persist_path

    # ------------------------------------------------------------------
    # High-level logging helpers
    # ------------------------------------------------------------------

    def log_job_submit(
        self, job_id: str, user_id: str, backend: str, circuit_name: str
    ) -> AuditEvent:
        return self._record(
            user_id=user_id,
            action="job.submit",
            resource=f"job:{job_id}",
            details={"backend": backend, "circuit": circuit_name},
        )

    def log_job_complete(
        self, job_id: str, user_id: str, duration_ms: float, status: str = "success"
    ) -> AuditEvent:
        return self._record(
            user_id=user_id,
            action="job.complete",
            resource=f"job:{job_id}",
            details={"duration_ms": duration_ms},
            status=status,
        )

    def log_job_fail(self, job_id: str, user_id: str, error_message: str) -> AuditEvent:
        return self._record(
            user_id=user_id,
            action="job.fail",
            resource=f"job:{job_id}",
            details={"error": error_message},
            status="failure",
        )

    def log_authentication(
        self, user_id: str, method: str, success: bool, ip_address: str = ""
    ) -> AuditEvent:
        return self._record(
            user_id=user_id,
            action="auth.login",
            resource="auth",
            details={"method": method},
            status="success" if success else "failure",
            ip_address=ip_address,
        )

    def log_role_change(
        self,
        admin_id: str,
        target_user_id: str,
        old_role: str,
        new_role: str,
    ) -> AuditEvent:
        return self._record(
            user_id=admin_id,
            action="rbac.role_change",
            resource=f"user:{target_user_id}",
            details={"old_role": old_role, "new_role": new_role, "target_user": target_user_id},
        )

    # ------------------------------------------------------------------
    # Query & export
    # ------------------------------------------------------------------

    def get_events(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        since: Optional[float] = None,
    ) -> List[AuditEvent]:
        """Return events matching the given filters."""
        results = self._events
        if user_id is not None:
            results = [e for e in results if e.user_id == user_id]
        if action is not None:
            results = [e for e in results if e.action == action]
        if since is not None:
            results = [e for e in results if e.timestamp >= since]
        return list(results)

    def export_events(self, format: str = "json") -> str:
        """Export all events as a string.

        Supported formats: ``json``.
        """
        if format != "json":
            raise ValueError(f"Unsupported export format: {format!r}")
        return json.dumps([asdict(e) for e in self._events], indent=2)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _record(
        self,
        *,
        user_id: str,
        action: str,
        resource: str,
        details: Optional[Dict] = None,
        status: str = "success",
        ip_address: str = "",
    ) -> AuditEvent:
        event = AuditEvent(
            user_id=user_id,
            action=action,
            resource=resource,
            details=details or {},
            status=status,
            ip_address=ip_address,
        )
        self._events.append(event)
        if self.persist_path:
            self._flush()
        return event

    def _flush(self):
        with open(self.persist_path, "w") as f:
            json.dump([asdict(e) for e in self._events], f, indent=2)
