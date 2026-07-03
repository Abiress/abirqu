"""
Quantum Job
===========
Job lifecycle management for quantum circuits.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class JobState(str, Enum):
    """Quantum job states."""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class QuantumJob:
    """A quantum job representing a circuit to be executed.

    Attributes
    ----------
    job_id : str
        Unique job identifier.
    circuit : Circuit
        The quantum circuit to execute.
    backend_name : str
        Target backend name.
    shots : int
        Number of measurement shots.
    priority : int
        Job priority (higher = more important).
    state : JobState
        Current job state.
    created_at : float
        Creation timestamp.
    metadata : dict
        Additional job metadata.
    """
    circuit: Any  # Circuit
    backend_name: str = "fast"
    shots: int = 1024
    priority: int = 0
    job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    state: JobState = JobState.CREATED
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def start(self):
        """Mark job as started."""
        self.state = JobState.RUNNING
        self.started_at = time.time()

    def complete(self, result: Dict[str, Any]):
        """Mark job as completed."""
        self.state = JobState.COMPLETED
        self.completed_at = time.time()
        self.result = result

    def fail(self, error: str):
        """Mark job as failed."""
        self.state = JobState.FAILED
        self.completed_at = time.time()
        self.error = error

    def cancel(self):
        """Cancel the job."""
        self.state = JobState.CANCELED
        self.completed_at = time.time()

    @property
    def execution_time(self) -> Optional[float]:
        """Execution time in seconds, or None if not completed."""
        if self.started_at is None:
            return None
        end = self.completed_at or time.time()
        return end - self.started_at

    @property
    def queue_time(self) -> Optional[float]:
        """Time spent in queue before execution."""
        if self.started_at is None:
            return None
        return self.started_at - self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Export job as dictionary."""
        return {
            "job_id": self.job_id,
            "backend_name": self.backend_name,
            "shots": self.shots,
            "priority": self.priority,
            "state": self.state.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "execution_time": self.execution_time,
            "queue_time": self.queue_time,
            "metadata": self.metadata,
        }
