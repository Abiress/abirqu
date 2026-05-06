"""
Task 18.1 — Quantum Process Scheduler.

Build a scheduler that manages multiple quantum jobs on shared hardware.
Implements priority-based scheduling with preemption, fair-share scheduling,
queue management with estimated wait times.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import heapq


class JobPriority(Enum):
    """Job priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PREEMPTED = "preempted"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QuantumJob:
    """Representation of a quantum job."""
    job_id: str
    circuit: List[Tuple]
    user: str
    project: str
    priority: JobPriority = JobPriority.NORMAL
    estimated_qubits: int = 1
    estimated_time: float = 1.0  # seconds
    status: JobStatus = JobStatus.PENDING
    submitted_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def elapsed_time(self) -> float:
        """Get elapsed time for running job."""
        if self.started_at is None:
            return 0.0
        end = self.completed_at or time.time()
        return end - self.started_at
    
    def wait_time(self) -> float:
        """Get wait time in queue."""
        if self.started_at is None:
            return time.time() - self.submitted_at
        return self.started_at - self.submitted_at


@dataclass
class SchedulingResult:
    """Result of a scheduling decision."""
    job_id: str
    action: str  # 'started', 'preempted', 'queued', 'completed'
    queue_position: Optional[int] = None
    estimated_wait: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_id': self.job_id,
            'action': self.action,
            'queue_position': self.queue_position,
            'estimated_wait': self.estimated_wait,
            'metadata': self.metadata
        }


class QueueManager:
    """Manages job queues with priority ordering."""
    
    def __init__(self):
        self.queues: Dict[JobPriority, List[QuantumJob]] = {
            priority: [] for priority in JobPriority
        }
        self._counter = 0  # For tie-breaking in heap
    
    def enqueue(self, job: QuantumJob):
        """Add job to appropriate queue."""
        self.queues[job.priority].append(job)
    
    def dequeue(self) -> Optional[QuantumJob]:
        """Get highest priority job."""
        for priority in sorted(JobPriority, key=lambda p: p.value):
            if self.queues[priority]:
                return self.queues[priority].pop(0)
        return None
    
    def get_queue_length(self) -> int:
        """Total jobs in queue."""
        return sum(len(q) for q in self.queues.values())
    
    def get_estimated_wait(self, priority: JobPriority) -> float:
        """Estimate wait time for a given priority level."""
        total_time = 0.0
        found = False
        
        for p in sorted(JobPriority, key=lambda x: x.value):
            if found:
                # Add time for all jobs in lower priority queues.
                for job in self.queues[p]:
                    total_time += job.estimated_time
            elif p == priority:
                found = True
                # Add time for jobs ahead in same priority queue.
                for job in self.queues[p]:
                    total_time += job.estimated_time
        
        return total_time
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a specific job from queues."""
        for priority in self.queues:
            self.queues[priority] = [
                j for j in self.queues[priority] if j.job_id != job_id
            ]
        return True


class FairShareManager:
    """Fair-share scheduling across users and projects."""
    
    def __init__(self):
        self.user_usage: Dict[str, float] = {}  # user -> CPU time used
        self.project_usage: Dict[str, float] = {}  # project -> CPU time
        self.user_quota: Dict[str, float] = {}  # user -> quota
        self.project_quota: Dict[str, float] = {}  # project -> quota
    
    def record_usage(self, job: QuantumJob):
        """Record resource usage after job completion."""
        self.user_usage[job.user] = self.user_usage.get(job.user, 0.0) + job.elapsed_time()
        self.project_usage[job.project] = self.project_usage.get(job.project, 0.0) + job.elapsed_time()
    
    def get_user_priority_boost(self, user: str) -> float:
        """Calculate priority boost based on fair-share (lower usage = higher boost)."""
        usage = self.user_usage.get(user, 0.0)
        quota = self.user_quota.get(user, 100.0)  # Default quota
        
        if quota <= 0:
            return 0.0
        
        usage_ratio = usage / quota
        # More usage = lower boost (can be negative).
        return max(-1.0, 1.0 - usage_ratio)
    
    def get_project_priority_boost(self, project: str) -> float:
        """Calculate priority boost for project."""
        usage = self.project_usage.get(project, 0.0)
        quota = self.project_quota.get(project, 100.0)
        
        if quota <= 0:
            return 0.0
        
        usage_ratio = usage / quota
        return max(-1.0, 1.0 - usage_ratio)
    
    def set_user_quota(self, user: str, quota: float):
        """Set resource quota for user."""
        self.user_quota[user] = quota
    
    def set_project_quota(self, project: str, quota: float):
        """Set resource quota for project."""
        self.project_quota[project] = quota


class QuantumScheduler:
    """Main quantum process scheduler."""
    
    def __init__(self, num_qubits: int = 20, max_concurrent: int = 5):
        self.num_qubits = num_qubits
        self.max_concurrent = max_concurrent
        self.queue_manager = QueueManager()
        self.fair_share = FairShareManager()
        self.running_jobs: Dict[str, QuantumJob] = {}
        self.completed_jobs: List[QuantumJob] = []
        self.job_counter = 0
        
    def submit_job(self, circuit: List[Tuple], user: str, project: str,
                  priority: JobPriority = JobPriority.NORMAL,
                  estimated_qubits: int = 1,
                  estimated_time: float = 1.0) -> str:
        """Submit a new job."""
        self.job_counter += 1
        job_id = f"job_{self.job_counter}"
        
        job = QuantumJob(
            job_id=job_id,
            circuit=circuit,
            user=user,
            project=project,
            priority=priority,
            estimated_qubits=estimated_qubits,
            estimated_time=estimated_time
        )
        
        self.queue_manager.enqueue(job)
        return job_id
    
    def schedule(self) -> SchedulingResult:
        """Run one scheduling iteration."""
        if len(self.running_jobs) >= self.max_concurrent:
            # Check for preemption opportunities.
            return self._try_preemption()
        
        # Get next job from queue.
        job = self.queue_manager.dequeue()
        if job is None:
            return SchedulingResult(
                job_id="",
                action="no_jobs",
                metadata={'running': len(self.running_jobs)}
            )
        
        # Check if we have enough qubits.
        if job.estimated_qubits > self.num_qubits:
            job.status = JobStatus.FAILED
            self.completed_jobs.append(job)
            return SchedulingResult(
                job_id=job.job_id,
                action="failed_qubits",
                metadata={'required': job.estimated_qubits, 'available': self.num_qubits}
            )
        
        # Start the job.
        return self._start_job(job)
    
    def _start_job(self, job: QuantumJob) -> SchedulingResult:
        """Start a job."""
        job.status = JobStatus.RUNNING
        job.started_at = time.time()
        self.running_jobs[job.job_id] = job
        
        # Simulate job execution (simplified).
        # In practice, this would dispatch to quantum hardware.
        return SchedulingResult(
            job_id=job.job_id,
            action="started",
            metadata={
                'user': job.user,
                'project': job.project,
                'estimated_time': job.estimated_time
            }
        )
    
    def _try_preemption(self) -> SchedulingResult:
        """Try to preempt a low-priority job for a higher-priority one."""
        # Find lowest priority running job.
        lowest_job = None
        lowest_priority = None
        
        for job in self.running_jobs.values():
            if lowest_priority is None or job.priority.value > lowest_priority.value:
                lowest_job = job
                lowest_priority = job.priority
        
        if lowest_job is None:
            return SchedulingResult(
                job_id="",
                action="no_preemption",
                metadata={'reason': 'no running jobs'}
            )
        
        # Preempt the job.
        return self.preempt_job(lowest_job.job_id)
    
    def preempt_job(self, job_id: str) -> SchedulingResult:
        """Preempt a running job."""
        if job_id not in self.running_jobs:
            return SchedulingResult(
                job_id=job_id,
                action="preempt_failed",
                metadata={'reason': 'job not running'}
            )
        
        job = self.running_jobs.pop(job_id)
        job.status = JobStatus.PREEMPTED
        job.completed_at = time.time()
        
        # Re-queue with higher priority.
        job.priority = JobPriority(max(0, job.priority.value - 1))
        self.queue_manager.enqueue(job)
        
        return SchedulingResult(
            job_id=job_id,
            action="preempted",
            metadata={'new_priority': job.priority.name}
        )
    
    def complete_job(self, job_id: str, result: Optional[Any] = None):
        """Mark a job as completed."""
        if job_id in self.running_jobs:
            job = self.running_jobs.pop(job_id)
            job.status = JobStatus.COMPLETED
            job.completed_at = time.time()
            job.result = result
            self.completed_jobs.append(job)
            self.fair_share.record_usage(job)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job (pending or running)."""
        # Check running jobs.
        if job_id in self.running_jobs:
            job = self.running_jobs.pop(job_id)
            job.status = JobStatus.CANCELLED
            job.completed_at = time.time()
            self.completed_jobs.append(job)
            return True
        
        # Check pending queues.
        return self.queue_manager.remove_job(job_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        pending = self.queue_manager.get_queue_length()
        running = len(self.running_jobs)
        
        return {
            'pending_jobs': pending,
            'running_jobs': running,
            'completed_jobs': len(self.completed_jobs),
            'available_qubits': self.num_qubits,  # Simplified.
            'max_concurrent': self.max_concurrent
        }
    
    def get_job(self, job_id: str) -> Optional[QuantumJob]:
        """Get job by ID."""
        if job_id in self.running_jobs:
            return self.running_jobs[job_id]
        
        for priority in JobPriority:
            for job in self.queue_manager.queues[priority]:
                if job.job_id == job_id:
                    return job
        
        for job in self.completed_jobs:
            if job.job_id == job_id:
                return job
        
        return None
