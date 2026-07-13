"""
AbirQu Cloud-Native Job Orchestration
========================================
SQLite-backed job persistence, multi-policy scheduling, circuit batching,
LRU result caching, cost estimation, and automatic backend selection.

Pure Python + numpy — no external dependencies.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
import uuid
from collections import OrderedDict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ── Enums ───────────────────────────────────────────────────────────────────

class JobStatus(Enum):
    """Lifecycle status of a queued job."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SchedulingPolicy(Enum):
    """Supported scheduling policies."""
    FIFO = "fifo"
    PRIORITY = "priority"
    SJF = "sjf"
    FAIR_SHARE = "fair_share"


# ── Data classes ────────────────────────────────────────────────────────────

class Job:
    """Represents a single quantum job."""

    def __init__(
        self,
        circuit_json: str,
        backend: str = "auto",
        shots: int = 1024,
        priority: int = 0,
        owner: str = "default",
        job_id: Optional[str] = None,
        status: JobStatus = JobStatus.PENDING,
        created_at: Optional[float] = None,
        estimated_duration: Optional[float] = None,
        tags: Optional[Dict[str, str]] = None,
    ):
        self.job_id = job_id or uuid.uuid4().hex[:12]
        self.circuit_json = circuit_json
        self.backend = backend
        self.shots = shots
        self.priority = priority
        self.owner = owner
        self.status = status
        self.created_at = created_at or time.time()
        self.estimated_duration = estimated_duration
        self.tags = tags or {}
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "circuit_json": self.circuit_json,
            "backend": self.backend,
            "shots": self.shots,
            "priority": self.priority,
            "owner": self.owner,
            "status": self.status.value,
            "created_at": self.created_at,
            "estimated_duration": self.estimated_duration,
            "tags": json.dumps(self.tags),
            "result": json.dumps(self.result) if self.result else None,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Job":
        j = cls(
            job_id=d["job_id"],
            circuit_json=d["circuit_json"],
            backend=d["backend"],
            shots=d["shots"],
            priority=d["priority"],
            owner=d["owner"],
            status=JobStatus(d["status"]),
            created_at=d["created_at"],
            estimated_duration=d.get("estimated_duration"),
            tags=json.loads(d.get("tags") or "{}"),
        )
        j.result = json.loads(d["result"]) if d.get("result") else None
        j.error = d.get("error")
        return j


# ── JobQueue — SQLite-backed persistence ────────────────────────────────────

class JobQueue:
    """SQLite-backed persistent job queue.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file.
    """

    _CREATE_SQL = """
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        circuit_json TEXT NOT NULL,
        backend TEXT DEFAULT 'auto',
        shots INTEGER DEFAULT 1024,
        priority INTEGER DEFAULT 0,
        owner TEXT DEFAULT 'default',
        status TEXT DEFAULT 'pending',
        created_at REAL,
        estimated_duration REAL,
        tags TEXT DEFAULT '{}',
        result TEXT,
        error TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_status ON jobs(status);
    CREATE INDEX IF NOT EXISTS idx_owner ON jobs(owner);
    CREATE INDEX IF NOT EXISTS idx_priority ON jobs(priority DESC);
    """

    def __init__(self, db_path: str = ":memory:"):
        self._db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript(self._CREATE_SQL)
        conn.commit()

    def submit(self, job: Job) -> str:
        """Insert a job into the queue. Returns the job_id."""
        conn = self._get_conn()
        d = job.to_dict()
        conn.execute(
            """INSERT OR REPLACE INTO jobs
               (job_id, circuit_json, backend, shots, priority, owner,
                status, created_at, estimated_duration, tags, result, error)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                d["job_id"], d["circuit_json"], d["backend"], d["shots"],
                d["priority"], d["owner"], d["status"], d["created_at"],
                d["estimated_duration"], d["tags"], d["result"], d["error"],
            ),
        )
        conn.commit()
        return job.job_id

    def get(self, job_id: str) -> Optional[Job]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM jobs WHERE job_id=?", (job_id,)
        ).fetchone()
        return Job.from_dict(dict(row)) if row else None

    def update_status(self, job_id: str, status: JobStatus,
                      result: Optional[Dict] = None,
                      error: Optional[str] = None) -> None:
        conn = self._get_conn()
        result_json = json.dumps(result) if result else None
        conn.execute(
            "UPDATE jobs SET status=?, result=?, error=? WHERE job_id=?",
            (status.value, result_json, error, job_id),
        )
        conn.commit()

    def list_jobs(self, status: Optional[JobStatus] = None,
                  owner: Optional[str] = None,
                  limit: int = 100) -> List[Job]:
        conn = self._get_conn()
        query = "SELECT * FROM jobs WHERE 1=1"
        params: list = []
        if status:
            query += " AND status=?"
            params.append(status.value)
        if owner:
            query += " AND owner=?"
            params.append(owner)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
        return [Job.from_dict(dict(r)) for r in rows]

    def pending_count(self) -> int:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM jobs WHERE status='pending'"
        ).fetchone()
        return row["cnt"]

    def cancel(self, job_id: str) -> bool:
        return self.update_status(job_id, JobStatus.CANCELLED) is not None or True

    def delete(self, job_id: str) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM jobs WHERE job_id=?", (job_id,))
        conn.commit()


# ── JobScheduler ────────────────────────────────────────────────────────────

class JobScheduler:
    """Dispatches jobs from the queue using configurable policies.

    Parameters
    ----------
    queue : JobQueue
        The backing job queue.
    policy : SchedulingPolicy
        Scheduling strategy.
    quantum_shares : dict
        Owner → share weight for fair-share scheduling.
    """

    def __init__(
        self,
        queue: JobQueue,
        policy: SchedulingPolicy = SchedulingPolicy.FIFO,
        quantum_shares: Optional[Dict[str, float]] = None,
    ):
        self.queue = queue
        self.policy = policy
        self.quantum_shares = quantum_shares or {}
        self._rr_index: Dict[str, int] = {}  # for fair-share round-robin

    def schedule_next(self) -> Optional[Job]:
        """Select and mark the next job as scheduled. Returns None if idle."""
        candidates = self.queue.list_jobs(status=JobStatus.PENDING, limit=1000)
        if not candidates:
            return None

        selected = self._select(candidates)
        self.queue.update_status(selected.job_id, JobStatus.SCHEDULED)
        return selected

    def _select(self, jobs: List[Job]) -> Job:
        if self.policy == SchedulingPolicy.FIFO:
            return self._fifo(jobs)
        elif self.policy == SchedulingPolicy.PRIORITY:
            return self._priority(jobs)
        elif self.policy == SchedulingPolicy.SJF:
            return self._sjf(jobs)
        elif self.policy == SchedulingPolicy.FAIR_SHARE:
            return self._fair_share(jobs)
        return jobs[0]

    @staticmethod
    def _fifo(jobs: List[Job]) -> Job:
        return min(jobs, key=lambda j: j.created_at)

    @staticmethod
    def _priority(jobs: List[Job]) -> Job:
        return max(jobs, key=lambda j: (j.priority, -j.created_at))

    @staticmethod
    def _sjf(jobs: List[Job]) -> Job:
        return min(jobs, key=lambda j: j.estimated_duration or float("inf"))

    def _fair_share(self, jobs: List[Job]) -> Job:
        """Weighted round-robin fair-share scheduling."""
        if not self.quantum_shares:
            return jobs[0]

        # Group by owner
        by_owner: Dict[str, List[Job]] = {}
        for j in jobs:
            by_owner.setdefault(j.owner, []).append(j)

        owners = sorted(by_owner.keys())
        if not owners:
            return jobs[0]

        # Find owner with smallest accumulated share * round
        best_owner = min(
            owners,
            key=lambda o: self._rr_index.get(o, 0) / max(
                self.quantum_shares.get(o, 1.0), 0.01
            ),
        )
        self._rr_index[best_owner] = self._rr_index.get(best_owner, 0) + 1

        # Pick oldest job from that owner
        return min(by_owner[best_owner], key=lambda j: j.created_at)

    def set_policy(self, policy: SchedulingPolicy) -> None:
        self.policy = policy


# ── JobBatcher ──────────────────────────────────────────────────────────────

class JobBatcher:
    """Batches pending jobs destined for the same backend to reduce overhead.

    Parameters
    ----------
    queue : JobQueue
        The backing job queue.
    max_batch_size : int
        Maximum jobs per batch.
    """

    def __init__(self, queue: JobQueue, max_batch_size: int = 32):
        self.queue = queue
        self.max_batch_size = max_batch_size

    def create_batches(self) -> Dict[str, List[Job]]:
        """Group pending jobs by backend and return batches."""
        pending = self.queue.list_jobs(status=JobStatus.PENDING, limit=10000)
        by_backend: Dict[str, List[Job]] = {}
        for job in pending:
            by_backend.setdefault(job.backend, []).append(job)

        batches: Dict[str, List[Job]] = {}
        for backend, jobs in by_backend.items():
            jobs.sort(key=lambda j: j.created_at)
            for i in range(0, len(jobs), self.max_batch_size):
                batch_key = f"{backend}_{i // self.max_batch_size}"
                batches[batch_key] = jobs[i: i + self.max_batch_size]
        return batches

    def execute_batches(self, executor: Callable[[List[Job]], Dict[str, Any]]) -> Dict[str, Any]:
        """Execute all batches using the provided *executor* function.

        Parameters
        ----------
        executor : callable
            ``executor(jobs) -> {job_id: result}``
        """
        batches = self.create_batches()
        all_results: Dict[str, Any] = {}
        for batch_key, jobs in batches.items():
            try:
                results = executor(jobs)
                all_results[batch_key] = results
                for job in jobs:
                    job_result = results.get(job.job_id)
                    if job_result is not None:
                        self.queue.update_status(
                            job.job_id, JobStatus.COMPLETED, result=job_result
                        )
                    else:
                        self.queue.update_status(
                            job.job_id, JobStatus.FAILED, error="No result returned"
                        )
            except Exception as exc:
                logger.error("Batch %s failed: %s", batch_key, exc)
                for job in jobs:
                    self.queue.update_status(
                        job.job_id, JobStatus.FAILED, error=str(exc)
                    )
        return all_results


# ── ResultCache — LRU eviction ──────────────────────────────────────────────

class ResultCache:
    """Thread-safe LRU cache for quantum job results.

    Parameters
    ----------
    max_size : int
        Maximum number of cached results.
    ttl_seconds : float
        Time-to-live for cache entries (0 = no expiry).
    """

    def __init__(self, max_size: int = 1024, ttl_seconds: float = 0.0):
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._cache: OrderedDict[str, Tuple[Dict[str, Any], float]] = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def _make_key(circuit_json: str, backend: str, shots: int) -> str:
        raw = f"{circuit_json}|{backend}|{shots}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def get(self, circuit_json: str, backend: str, shots: int) -> Optional[Dict]:
        """Retrieve a cached result, or ``None`` on miss / expiry."""
        key = self._make_key(circuit_json, backend, shots)
        with self._lock:
            if key not in self._cache:
                return None
            result, ts = self._cache[key]
            if self._ttl > 0 and (time.time() - ts) > self._ttl:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return result

    def put(self, circuit_json: str, backend: str, shots: int,
            result: Dict[str, Any]) -> None:
        """Insert a result into the cache, evicting LRU if at capacity."""
        key = self._make_key(circuit_json, backend, shots)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (result, time.time())
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def invalidate(self, circuit_json: str, backend: str, shots: int) -> bool:
        key = self._make_key(circuit_json, backend, shots)
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


# ── CostEstimator ───────────────────────────────────────────────────────────

# Default pricing tables (USD per shot)
_DEFAULT_PRICING: Dict[str, Dict[str, float]] = {
    "ibm_osaka": {"cost_per_shot": 0.0001, "cost_per_shot_priority": 0.00015},
    "ibm_brisbane": {"cost_per_shot": 0.0001, "cost_per_shot_priority": 0.00015},
    "aws_braket_sv_sim": {"cost_per_shot": 0.000024, "cost_per_shot_priority": 0.000024},
    "aws_braket_ionq_harmony": {"cost_per_shot": 0.0003, "cost_per_shot_priority": 0.0003},
    "google_cirq_sim": {"cost_per_shot": 0.0, "cost_per_shot_priority": 0.0},
    "ionq_qpu": {"cost_per_shot": 0.0003, "cost_per_shot_priority": 0.0003},
    "quantinuum_h1": {"cost_per_shot": 0.00027, "cost_per_shot_priority": 0.00027},
}


class CostEstimator:
    """Estimates execution cost across different backends.

    Parameters
    ----------
    pricing : dict, optional
        Override default pricing table.
    budget_limit : float
        Maximum allowed budget in USD.
    """

    def __init__(
        self,
        pricing: Optional[Dict[str, Dict[str, float]]] = None,
        budget_limit: float = 100.0,
    ):
        self.pricing = pricing or dict(_DEFAULT_PRICING)
        self.budget_limit = budget_limit
        self.spent: float = 0.0

    def estimate(self, backend: str, shots: int, priority: bool = False) -> Dict[str, Any]:
        """Return cost estimate for running *shots* on *backend*.

        Returns
        -------
        dict
            ``{backend, shots, cost_usd, within_budget, budget_remaining}``
        """
        rate_key = "cost_per_shot_priority" if priority else "cost_per_shot"
        profile = self.pricing.get(backend, {"cost_per_shot": 0.0001})
        cost_per_shot = profile.get(rate_key, profile.get("cost_per_shot", 0.0001))
        cost = shots * cost_per_shot
        within = (self.spent + cost) <= self.budget_limit

        return {
            "backend": backend,
            "shots": shots,
            "cost_usd": round(cost, 8),
            "within_budget": within,
            "budget_remaining": round(self.budget_limit - self.spent, 8),
        }

    def estimate_batch(self, jobs: List[Job]) -> Dict[str, Any]:
        """Estimate total cost for a batch of jobs."""
        total = 0.0
        details = []
        for job in jobs:
            est = self.estimate(job.backend, job.shots)
            total += est["cost_usd"]
            details.append(est)
        return {
            "total_cost_usd": round(total, 8),
            "num_jobs": len(jobs),
            "within_budget": (self.spent + total) <= self.budget_limit,
            "details": details,
        }

    def record_spend(self, amount: float) -> None:
        self.spent += amount

    def compare_backends(self, shot_count: int,
                         backends: Optional[List[str]] = None) -> List[Dict]:
        """Compare cost across all (or selected) backends."""
        if backends is None:
            backends = list(self.pricing.keys())
        results = []
        for b in backends:
            est = self.estimate(b, shot_count)
            results.append(est)
        results.sort(key=lambda x: x["cost_usd"])
        return results


# ── AutoBackendSelector ─────────────────────────────────────────────────────

# Backend capability profiles
_DEFAULT_PROFILES: Dict[str, Dict[str, Any]] = {
    "ibm_osaka": {
        "num_qubits": 127,
        "max_shots": 8192,
        "avg_fidelity_1q": 0.9995,
        "avg_fidelity_2q": 0.995,
        "avg_t1_us": 100.0,
        "avg_t2_us": 80.0,
        "avg_gate_time_ns": 35.0,
        "max_circuit_depth": 200,
        "native_gates": {"CX", "ID", "RZ", "SX", "X"},
        "connectivity": "heavy-hex",
        "cost_per_shot": 0.0001,
        "provider": "IBM",
    },
    "ibm_brisbane": {
        "num_qubits": 127,
        "max_shots": 8192,
        "avg_fidelity_1q": 0.999,
        "avg_fidelity_2q": 0.994,
        "avg_t1_us": 95.0,
        "avg_t2_us": 75.0,
        "avg_gate_time_ns": 38.0,
        "max_circuit_depth": 180,
        "native_gates": {"CX", "ID", "RZ", "SX", "X"},
        "connectivity": "heavy-hex",
        "cost_per_shot": 0.0001,
        "provider": "IBM",
    },
    "ionq_qpu": {
        "num_qubits": 11,
        "max_shots": 4096,
        "avg_fidelity_1q": 0.9998,
        "avg_fidelity_2q": 0.997,
        "avg_t1_us": 10000.0,
        "avg_t2_us": 5000.0,
        "avg_gate_time_ns": 500.0,
        "max_circuit_depth": 1000,
        "native_gates": {"Rxx", "Ryy", "Rzz", "Rz", "Ry", "Rx"},
        "connectivity": "all-to-all",
        "cost_per_shot": 0.0003,
        "provider": "IonQ",
    },
    "aws_braket_sv_sim": {
        "num_qubits": 30,
        "max_shots": 8192,
        "avg_fidelity_1q": 1.0,
        "avg_fidelity_2q": 1.0,
        "avg_t1_us": float("inf"),
        "avg_t2_us": float("inf"),
        "avg_gate_time_ns": 0.0,
        "max_circuit_depth": float("inf"),
        "native_gates": {"H", "CNOT", "Rz", "Ry", "Rx"},
        "connectivity": "all-to-all",
        "cost_per_shot": 0.000024,
        "provider": "Amazon Braket",
    },
    "quantinuum_h1": {
        "num_qubits": 20,
        "max_shots": 4096,
        "avg_fidelity_1q": 0.9999,
        "avg_fidelity_2q": 0.998,
        "avg_t1_us": 10000.0,
        "avg_t2_us": 2000.0,
        "avg_gate_time_ns": 300.0,
        "max_circuit_depth": 500,
        "native_gates": {"ZZ", "Rz", "Ry", "Rx", "H", "X"},
        "connectivity": "all-to-all",
        "cost_per_shot": 0.00027,
        "provider": "Quantinuum",
    },
}


class AutoBackendSelector:
    """Automatically selects the best backend for a given circuit.

    Scoring considers: qubit count, native gate support, fidelity,
    connectivity, depth, and cost.

    Parameters
    ----------
    profiles : dict, optional
        Override default backend profiles.
    """

    def __init__(self, profiles: Optional[Dict[str, Dict[str, Any]]] = None):
        self.profiles = profiles or dict(_DEFAULT_PROFILES)

    def select(
        self,
        num_qubits: int,
        num_2q_gates: int = 0,
        depth: int = 0,
        gate_names: Optional[set] = None,
        preferred_gates: Optional[set] = None,
        max_cost: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Pick the best backend given circuit characteristics.

        Parameters
        ----------
        num_qubits : int
            Number of qubits in the circuit.
        num_2q_gates : int
            Number of two-qubit gates (affects fidelity estimate).
        depth : int
            Circuit depth.
        gate_names : set, optional
            Gate names used in the circuit.
        preferred_gates : set, optional
            Gates that should be natively supported by the backend.
        max_cost : float, optional
            Maximum acceptable cost per shot.

        Returns
        -------
        dict
            ``{backend, score, reasons, profile}``
        """
        gate_names = gate_names or set()
        preferred_gates = preferred_gates or set()

        scored: List[Tuple[str, float, List[str]]] = []

        for name, profile in self.profiles.items():
            score = 0.0
            reasons: List[str] = []

            # Qubit capacity (must fit)
            if num_qubits > profile["num_qubits"]:
                continue

            # Qubit count: prefer close fit (less waste)
            q_ratio = num_qubits / max(profile["num_qubits"], 1)
            score += (1.0 - q_ratio) * 10

            # Fidelity: weighted contribution
            fid_2q = profile["avg_fidelity_2q"]
            fid_1q = profile["avg_fidelity_1q"]
            fidelity_score = (fid_1q ** 5) * (fid_2q ** max(num_2q_gates, 0))
            score += fidelity_score * 30

            # Native gate support
            native = profile.get("native_gates", set())
            if gate_names and gate_names.issubset(native):
                score += 15
                reasons.append("all gates native")
            elif preferred_gates and preferred_gates.issubset(native):
                score += 8
                reasons.append("preferred gates native")

            # Connectivity
            conn = profile.get("connectivity", "")
            if conn == "all-to-all":
                score += 10
                reasons.append("all-to-all connectivity")

            # Depth headroom
            max_depth = profile.get("max_circuit_depth", float("inf"))
            if depth <= max_depth:
                score += 5
                reasons.append("depth OK")
            else:
                score -= 20
                reasons.append("exceeds max depth")

            # Cost penalty
            cost_per_shot = profile.get("cost_per_shot", 0.001)
            if max_cost is not None and cost_per_shot > max_cost:
                score -= 50
            score -= cost_per_shot * 1000  # small cost penalty

            # T1/T2 — prefer long coherence
            t2 = profile.get("avg_t2_us", 0)
            if t2 < 100:
                score -= 5
                reasons.append("short T2")
            elif t2 > 1000:
                score += 5
                reasons.append("long T2")

            scored.append((name, score, reasons))

        if not scored:
            return {
                "backend": None,
                "score": 0,
                "reasons": ["no suitable backend found"],
                "profile": None,
            }

        scored.sort(key=lambda x: x[1], reverse=True)
        best_name, best_score, best_reasons = scored[0]

        return {
            "backend": best_name,
            "score": round(best_score, 4),
            "reasons": best_reasons,
            "profile": self.profiles[best_name],
            "alternatives": [
                {"backend": n, "score": round(s, 4)}
                for n, s, _ in scored[1:4]
            ],
        }

    def register_backend(self, name: str, profile: Dict[str, Any]) -> None:
        """Register or update a backend profile."""
        self.profiles[name] = profile

    def list_backends(self) -> List[str]:
        return list(self.profiles.keys())


# ── Public API ──────────────────────────────────────────────────────────────

__all__ = [
    "JobStatus",
    "SchedulingPolicy",
    "Job",
    "JobQueue",
    "JobScheduler",
    "JobBatcher",
    "ResultCache",
    "CostEstimator",
    "AutoBackendSelector",
]
