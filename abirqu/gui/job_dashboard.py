"""
AbirQu Job Dashboard
Copyright 2026 Abir Maheshwari

Real-time job monitoring dashboard.
"""
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class JobEntry:
    """A job entry for the dashboard."""
    job_id: str
    circuit_name: str
    backend: str
    shots: int
    status: str = 'pending'
    progress: float = 0.0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    result_summary: Optional[Dict] = None

    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

    @property
    def elapsed(self) -> float:
        if self.started_at:
            end = self.completed_at or time.time()
            return end - self.started_at
        return 0.0

    def to_dict(self) -> Dict:
        return {
            'job_id': self.job_id,
            'circuit_name': self.circuit_name,
            'backend': self.backend,
            'shots': self.shots,
            'status': self.status,
            'progress': self.progress,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'error': self.error,
            'duration': self.duration,
            'elapsed': self.elapsed,
            'result_summary': self.result_summary,
        }


class JobDashboard:
    """Job monitoring dashboard with real-time updates."""

    def __init__(self, max_jobs: int = 100):
        self.max_jobs = max_jobs
        self.jobs: Dict[str, JobEntry] = {}
        self._callbacks = []

    def on(self, event: str, callback):
        self._callbacks.append((event, callback))

    def _emit(self, event: str, data: Any):
        for ev, cb in self._callbacks:
            if ev == event:
                try:
                    cb(data)
                except Exception:
                    pass

    def add_job(self, job_id: str, circuit_name: str, backend: str,
                shots: int) -> JobEntry:
        job = JobEntry(
            job_id=job_id,
            circuit_name=circuit_name,
            backend=backend,
            shots=shots,
        )
        self.jobs[job_id] = job
        self._cleanup_old_jobs()
        self._emit('job_added', job.to_dict())
        return job

    def update_job(self, job_id: str, **kwargs) -> bool:
        if job_id not in self.jobs:
            return False
        job = self.jobs[job_id]
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        self._emit('job_updated', job.to_dict())
        return True

    def remove_job(self, job_id: str) -> bool:
        if job_id in self.jobs:
            del self.jobs[job_id]
            self._emit('job_removed', job_id)
            return True
        return False

    def get_job(self, job_id: str) -> Optional[JobEntry]:
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> List[JobEntry]:
        return sorted(self.jobs.values(), key=lambda j: -j.created_at)

    def get_jobs_by_status(self, status: str) -> List[JobEntry]:
        return [j for j in self.jobs.values() if j.status == status]

    def get_jobs_by_backend(self, backend: str) -> List[JobEntry]:
        return [j for j in self.jobs.values() if j.backend == backend]

    def get_stats(self) -> Dict:
        statuses = {}
        backends = {}
        total_shots = 0
        for job in self.jobs.values():
            statuses[job.status] = statuses.get(job.status, 0) + 1
            backends[job.backend] = backends.get(job.backend, 0) + 1
            total_shots += job.shots

        return {
            'total_jobs': len(self.jobs),
            'by_status': statuses,
            'by_backend': backends,
            'total_shots': total_shots,
            'running': statuses.get('running', 0),
            'completed': statuses.get('completed', 0),
            'failed': statuses.get('failed', 0),
        }

    def get_recent_jobs(self, limit: int = 10) -> List[JobEntry]:
        return self.get_all_jobs()[:limit]

    def get_performance_data(self) -> Dict:
        completed = self.get_jobs_by_status('completed')
        durations = [j.duration for j in completed if j.duration is not None]
        return {
            'total_completed': len(completed),
            'avg_duration': sum(durations) / len(durations) if durations else 0,
            'min_duration': min(durations) if durations else 0,
            'max_duration': max(durations) if durations else 0,
            'total_shots': sum(j.shots for j in self.jobs.values()),
        }

    def _cleanup_old_jobs(self):
        if len(self.jobs) > self.max_jobs:
            sorted_jobs = sorted(self.jobs.items(), key=lambda x: x[1].created_at)
            for job_id, _ in sorted_jobs[:len(self.jobs) - self.max_jobs]:
                del self.jobs[job_id]

    def get_render_data(self) -> Dict:
        jobs = [j.to_dict() for j in self.get_all_jobs()]
        stats = self.get_stats()
        return {
            'jobs': jobs,
            'stats': stats,
            'performance': self.get_performance_data(),
        }

    def clear(self):
        self.jobs.clear()
        self._emit('dashboard_cleared', None)

    def __len__(self):
        return len(self.jobs)

    def __repr__(self):
        return f"JobDashboard(jobs={len(self.jobs)})"
