"""
Preemption Manager
==================
Preempt low-priority jobs when high-priority jobs arrive.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .job import QuantumJob, JobState


@dataclass
class PreemptionEvent:
    """Record of a preemption."""
    preempted_job_id: str
    preempting_job_id: str
    timestamp: float
    reason: str


class PreemptionManager:
    """Manage job preemption based on priority.

    When a high-priority job arrives and all slots are full,
    the lowest-priority running job is preempted (paused).

    Parameters
    ----------
    enabled : bool
        Whether preemption is active.
    min_priority_gap : int
        Minimum priority difference to trigger preemption.
    max_preemptions : int
        Maximum times a job can be preempted before being killed.
    """

    def __init__(
        self,
        enabled: bool = True,
        min_priority_gap: int = 1,
        max_preemptions: int = 3,
    ):
        self.enabled = enabled
        self.min_priority_gap = min_priority_gap
        self.max_preemptions = max_preemptions
        self._events: List[PreemptionEvent] = []
        self._preemption_counts: Dict[str, int] = {}
        self._paused_jobs: Dict[str, QuantumJob] = {}
        self._on_preempt: Optional[Callable[[QuantumJob], None]] = None
        self._on_resume: Optional[Callable[[QuantumJob], None]] = None

    def set_callbacks(
        self,
        on_preempt: Optional[Callable[[QuantumJob], None]] = None,
        on_resume: Optional[Callable[[QuantumJob], None]] = None,
    ):
        """Set callback functions for preemption events."""
        self._on_preempt = on_preempt
        self._on_resume = on_resume

    def should_preempt(
        self,
        running_jobs: List[QuantumJob],
        incoming_job: QuantumJob,
    ) -> Optional[QuantumJob]:
        """Determine if a running job should be preempted.

        Returns the job to preempt, or None if no preemption needed.
        """
        if not self.enabled or not running_jobs:
            return None

        min_running_priority = min(j.priority for j in running_jobs)
        priority_gap = incoming_job.priority - min_running_priority

        if priority_gap < self.min_priority_gap:
            return None

        # Find lowest priority job
        candidates = [
            j for j in running_jobs
            if j.priority == min_running_priority
            and self._preemption_counts.get(j.job_id, 0) < self.max_preemptions
        ]

        if not candidates:
            return None

        return min(candidates, key=lambda j: j.created_at)

    def preempt(self, job: QuantumJob, incoming_job: QuantumJob) -> PreemptionEvent:
        """Preempt a running job."""
        count = self._preemption_counts.get(job.job_id, 0) + 1
        self._preemption_counts[job.job_id] = count

        event = PreemptionEvent(
            preempted_job_id=job.job_id,
            preempting_job_id=incoming_job.job_id,
            timestamp=time.time(),
            reason=f"Priority {incoming_job.priority} > {job.priority}",
        )
        self._events.append(event)
        self._paused_jobs[job.job_id] = job

        if self._on_preempt:
            self._on_preempt(job)

        return event

    def resume(self, job_id: str) -> Optional[QuantumJob]:
        """Resume a preempted job."""
        job = self._paused_jobs.pop(job_id, None)
        if job and self._on_resume:
            self._on_resume(job)
        return job

    def get_events(self) -> List[Dict]:
        """Get all preemption events."""
        return [
            {
                "preempted_job": e.preempted_job_id,
                "preempting_job": e.preempting_job_id,
                "timestamp": e.timestamp,
                "reason": e.reason,
            }
            for e in self._events
        ]

    @property
    def paused_count(self) -> int:
        return len(self._paused_jobs)

    @property
    def total_preemptions(self) -> int:
        return len(self._events)
