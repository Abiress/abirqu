"""
Job Monitor
===========
Real-time monitoring of quantum jobs.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .job import QuantumJob, JobState


@dataclass
class JobSnapshot:
    """Snapshot of a job's state."""
    job_id: str
    state: str
    backend: str
    priority: int
    created_at: float
    queue_time: Optional[float]
    execution_time: Optional[float]
    progress: float  # 0.0 to 1.0
    result_summary: Optional[str] = None


class JobMonitor:
    """Monitor quantum job execution in real-time.

    Parameters
    ----------
    poll_interval : float
        Seconds between status checks.
    history_size : int
        Maximum number of historical snapshots to keep.
    """

    def __init__(
        self,
        poll_interval: float = 1.0,
        history_size: int = 1000,
    ):
        self.poll_interval = poll_interval
        self.history_size = history_size
        self._jobs: Dict[str, QuantumJob] = {}
        self._snapshots: Dict[str, List[JobSnapshot]] = {}
        self._callbacks: Dict[str, Callable] = {}
        self._alerts: List[Dict] = []

    def track(self, job: QuantumJob):
        """Start tracking a job."""
        self._jobs[job.job_id] = job
        self._snapshots[job.job_id] = []

    def untrack(self, job_id: str):
        """Stop tracking a job."""
        self._jobs.pop(job_id, None)
        self._snapshots.pop(job_id, None)

    def set_callback(self, job_id: str, callback: Callable[[JobSnapshot], None]):
        """Set a callback for job state changes."""
        self._callbacks[job_id] = callback

    def snapshot(self, job_id: str) -> Optional[JobSnapshot]:
        """Take a snapshot of a job's current state."""
        job = self._jobs.get(job_id)
        if not job:
            return None

        now = time.time()
        progress = 0.0
        if job.state == JobState.COMPLETED:
            progress = 1.0
        elif job.state == JobState.RUNNING and job.started_at:
            # Estimate progress from circuit depth
            num_gates = len(getattr(job.circuit, "gates", []))
            estimated_duration = max(1.0, num_gates * 0.001)
            elapsed = now - job.started_at
            progress = min(0.99, elapsed / estimated_duration)

        snap = JobSnapshot(
            job_id=job.job_id,
            state=job.state.value,
            backend=job.backend_name,
            priority=job.priority,
            created_at=job.created_at,
            queue_time=job.queue_time,
            execution_time=job.execution_time,
            progress=progress,
        )

        self._snapshots.setdefault(job_id, []).append(snap)
        if len(self._snapshots[job_id]) > self.history_size:
            self._snapshots[job_id] = self._snapshots[job_id][-self.history_size:]

        # Fire callback
        cb = self._callbacks.get(job_id)
        if cb:
            cb(snap)

        return snap

    def snapshot_all(self) -> List[JobSnapshot]:
        """Snapshot all tracked jobs."""
        return [self.snapshot(jid) for jid in self._jobs if self.snapshot(jid) is not None]

    def get_history(self, job_id: str) -> List[JobSnapshot]:
        """Get snapshot history for a job."""
        return list(self._snapshots.get(job_id, []))

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked jobs."""
        states = {}
        for job in self._jobs.values():
            states[job.state.value] = states.get(job.state.value, 0) + 1

        return {
            "total_tracked": len(self._jobs),
            "states": states,
            "total_snapshots": sum(len(s) for s in self._snapshots.values()),
        }

    def check_alerts(self, max_queue_time: float = 300.0) -> List[Dict]:
        """Check for jobs exceeding queue time threshold."""
        alerts = []
        for job in self._jobs.values():
            if job.state == JobState.QUEUED and job.queue_time and job.queue_time > max_queue_time:
                alerts.append({
                    "job_id": job.job_id,
                    "type": "long_queue_time",
                    "queue_time": job.queue_time,
                    "threshold": max_queue_time,
                })
        return alerts
