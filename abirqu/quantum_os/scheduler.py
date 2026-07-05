"""
Quantum Scheduler
=================
Job scheduling with FIFO, priority, and fair-share policies.
"""

from __future__ import annotations

import heapq
import logging
from enum import Enum
from typing import Callable, Dict, List, Optional

from .job import QuantumJob, JobState

logger = logging.getLogger(__name__)


class SchedulingPolicy(str, Enum):
    """Scheduling policies."""
    FIFO = "fifo"  # First In, First Out
    PRIORITY = "priority"  # Highest priority first
    FAIR_SHARE = "fair_share"  # Equal resource distribution
    SHORTEST_JOB_FIRST = "sjf"  # Shortest circuit first


class QuantumScheduler:
    """Quantum job scheduler with configurable policies.

    Parameters
    ----------
    policy : SchedulingPolicy
        Scheduling policy to use.
    max_concurrent : int
        Maximum number of concurrent jobs per backend.
    """

    def __init__(
        self,
        policy: SchedulingPolicy = SchedulingPolicy.PRIORITY,
        max_concurrent: int = 1,
    ):
        self.policy = policy
        self.max_concurrent = max_concurrent
        self._queue: List[QuantumJob] = []
        self._running: Dict[str, QuantumJob] = {}
        self._completed: List[QuantumJob] = []
        self._backends: Dict[str, int] = {}  # backend -> running count

    def submit(self, job: QuantumJob) -> str:
        """Submit a job to the scheduler.

        Returns the job ID.
        """
        logger.debug("Submitting job %s (policy=%s)", job.job_id, self.policy.value)
        job.state = JobState.QUEUED
        if self.policy == SchedulingPolicy.PRIORITY:
            heapq.heappush(self._queue, (-job.priority, job.created_at, job))
        elif self.policy == SchedulingPolicy.SHORTEST_JOB_FIRST:
            circuit_depth = len(getattr(job.circuit, "gates", []))
            heapq.heappush(self._queue, (circuit_depth, job.created_at, job))
        else:
            self._queue.append(job)
        return job.job_id

    def schedule_next(self) -> Optional[QuantumJob]:
        """Schedule the next job for execution.

        Returns the job to execute, or None if no jobs are ready.
        """
        if not self._queue:
            logger.debug("No jobs in queue")
            return None

        # Check backend capacity
        for entry in list(self._queue):
            if isinstance(entry, tuple):
                _, _, job = entry
            else:
                job = entry

            backend = job.backend_name
            running = self._backends.get(backend, 0)
            if running < self.max_concurrent:
                # Remove from queue
                if isinstance(entry, tuple):
                    self._queue.remove(entry)
                    heapq.heapify(self._queue)
                else:
                    self._queue.remove(entry)

                job.start()
                self._running[job.job_id] = job
                self._backends[backend] = running + 1
                logger.info("Scheduled job %s on backend %s", job.job_id, backend)
                return job

        return None

    def complete_job(self, job_id: str, result: Dict = None):
        """Mark a job as completed."""
        if job_id in self._running:
            job = self._running.pop(job_id)
            job.complete(result or {})
            backend = job.backend_name
            self._backends[backend] = max(0, self._backends.get(backend, 1) - 1)
            self._completed.append(job)
            logger.info("Completed job %s on backend %s", job_id, backend)

    def fail_job(self, job_id: str, error: str):
        """Mark a job as failed."""
        if job_id in self._running:
            job = self._running.pop(job_id)
            job.fail(error)
            backend = job.backend_name
            self._backends[backend] = max(0, self._backends.get(backend, 1) - 1)
            self._completed.append(job)
            logger.warning("Failed job %s on backend %s: %s", job_id, backend, error)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        logger.debug("Attempting to cancel job %s", job_id)
        # Check queue
        for i, entry in enumerate(self._queue):
            if isinstance(entry, tuple):
                _, _, job = entry
            else:
                job = entry
            if job.job_id == job_id:
                job.cancel()
                self._queue.pop(i)
                if isinstance(self._queue, list):
                    pass
                else:
                    heapq.heapify(self._queue)
                self._completed.append(job)
                return True

        # Check running
        if job_id in self._running:
            job = self._running.pop(job_id)
            job.cancel()
            backend = job.backend_name
            self._backends[backend] = max(0, self._backends.get(backend, 1) - 1)
            self._completed.append(job)
            return True

        return False

    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status."""
        return {
            "queued": len(self._queue),
            "running": len(self._running),
            "completed": len(self._completed),
            "backends": dict(self._backends),
        }

    def get_job(self, job_id: str) -> Optional[QuantumJob]:
        """Get a job by ID."""
        if job_id in self._running:
            return self._running[job_id]
        for entry in self._queue:
            if isinstance(entry, tuple):
                _, _, job = entry
            else:
                job = entry
            if job.job_id == job_id:
                return job
        for job in self._completed:
            if job.job_id == job_id:
                return job
        return None

    @property
    def queue_depth(self) -> int:
        return len(self._queue)

    @property
    def running_count(self) -> int:
        return len(self._running)
