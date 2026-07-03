"""
Virtual Environment
===================
Isolated quantum computing environments with resource quotas.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .job import QuantumJob, JobState


@dataclass
class ResourceQuota:
    """Resource quota for an environment."""
    max_jobs_per_hour: int = 100
    max_shots_per_day: int = 1_000_000
    max_concurrent_jobs: int = 10
    allowed_backends: List[str] = field(default_factory=lambda: ["fast", "local"])
    max_circuit_qubits: int = 100
    max_circuit_gates: int = 10000


@dataclass
class UsageRecord:
    """Resource usage record."""
    timestamp: float
    jobs_submitted: int
    shots_used: int
    backend: str
    execution_time: float


class VirtualEnvironment:
    """Isolated quantum computing environment with quotas.

    Parameters
    ----------
    name : str
        Environment name.
    tenant_id : str
        Tenant identifier.
    quotas : ResourceQuota
        Resource limits.
    """

    def __init__(
        self,
        name: str,
        tenant_id: str = "default",
        quotas: Optional[ResourceQuota] = None,
    ):
        self.name = name
        self.tenant_id = tenant_id
        self.quotas = quotas or ResourceQuota()
        self._env_id = str(uuid.uuid4())[:8]
        self._created_at = time.time()
        self._jobs: Dict[str, QuantumJob] = {}
        self._usage_history: List[UsageRecord] = []
        self._hourly_jobs: List[float] = []
        self._daily_shots: List[tuple] = []  # (timestamp, shots)

    def can_submit(self, circuit_num_qubits: int = 0, circuit_num_gates: int = 0) -> tuple:
        """Check if a job can be submitted. Returns (allowed, reason)."""
        now = time.time()

        # Check circuit limits
        if circuit_num_qubits > self.quotas.max_circuit_qubits:
            return False, f"Circuit has {circuit_num_qubits} qubits, limit is {self.quotas.max_circuit_qubits}"

        if circuit_num_gates > self.quotas.max_circuit_gates:
            return False, f"Circuit has {circuit_num_gates} gates, limit is {self.quotas.max_circuit_gates}"

        # Check hourly rate
        self._hourly_jobs = [t for t in self._hourly_jobs if now - t < 3600]
        if len(self._hourly_jobs) >= self.quotas.max_jobs_per_hour:
            return False, f"Hourly job limit reached ({self.quotas.max_jobs_per_hour})"

        # Check concurrent jobs
        running = sum(1 for j in self._jobs.values() if j.state == JobState.RUNNING)
        if running >= self.quotas.max_concurrent_jobs:
            return False, f"Concurrent job limit reached ({self.quotas.max_concurrent_jobs})"

        # Check daily shots
        day_start = now - 86400
        daily_shots = sum(s for t, s in self._daily_shots if t > day_start)
        if daily_shots >= self.quotas.max_shots_per_day:
            return False, f"Daily shot limit reached ({self.quotas.max_shots_per_day})"

        return True, "ok"

    def submit_job(self, job: QuantumJob) -> bool:
        """Submit a job to this environment."""
        allowed, reason = self.can_submit(
            circuit_num_qubits=getattr(job.circuit, 'num_qubits', 0),
            circuit_num_gates=len(getattr(job.circuit, 'gates', [])),
        )
        if not allowed:
            return False

        if job.backend_name not in self.quotas.allowed_backends:
            return False

        self._jobs[job.job_id] = job
        self._hourly_jobs.append(time.time())
        self._daily_shots.append((time.time(), job.shots))
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get environment statistics."""
        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400

        jobs_last_hour = sum(1 for t in self._hourly_jobs if t > hour_ago)
        shots_last_day = sum(s for t, s in self._daily_shots if t > day_ago)

        return {
            "env_id": self._env_id,
            "name": self.name,
            "tenant": self.tenant_id,
            "total_jobs": len(self._jobs),
            "jobs_last_hour": jobs_last_hour,
            "shots_last_day": shots_last_day,
            "quotas": {
                "max_jobs_per_hour": self.quotas.max_jobs_per_hour,
                "max_shots_per_day": self.quotas.max_shots_per_day,
                "max_concurrent_jobs": self.quotas.max_concurrent_jobs,
                "allowed_backends": self.quotas.allowed_backends,
            },
            "remaining": {
                "jobs_per_hour": max(0, self.quotas.max_jobs_per_hour - jobs_last_hour),
                "shots_per_day": max(0, self.quotas.max_shots_per_day - shots_last_day),
            },
        }

    def reset_daily_counters(self):
        """Reset daily counters (call at midnight)."""
        self._daily_shots = []
