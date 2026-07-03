"""
Job Queue
=========
Persistent job queue with SQLite backend.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

from .job import QuantumJob, JobState


class JobQueue:
    """Persistent job queue backed by SQLite.

    Parameters
    ----------
    db_path : str
        Path to the SQLite database file.
    """

    def __init__(self, db_path: str = "~/.abirqu/jobs.db"):
        self.db_path = os.path.expanduser(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    circuit_data TEXT,
                    backend_name TEXT,
                    shots INTEGER,
                    priority INTEGER,
                    state TEXT,
                    created_at REAL,
                    started_at REAL,
                    completed_at REAL,
                    result_data TEXT,
                    error TEXT,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_state ON jobs(state)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_priority ON jobs(priority DESC)
            """)

    def enqueue(self, job: QuantumJob):
        """Add a job to the queue."""
        circuit_data = json.dumps({
            "num_qubits": job.circuit.num_qubits,
            "gates": [
                {"name": g.name, "qubits": list(g.qubits), "params": list(g.params)}
                for g in getattr(job.circuit, "gates", [])
            ],
        })
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO jobs
                   (job_id, circuit_data, backend_name, shots, priority,
                    state, created_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (job.job_id, circuit_data, job.backend_name, job.shots,
                 job.priority, job.state.value, job.created_at,
                 json.dumps(job.metadata)),
            )

    def dequeue(self) -> Optional[QuantumJob]:
        """Get the next job from the queue."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """SELECT job_id, circuit_data, backend_name, shots, priority,
                          state, created_at, metadata
                   FROM jobs WHERE state = 'queued'
                   ORDER BY priority DESC, created_at ASC LIMIT 1"""
            ).fetchone()
            if row is None:
                return None
            return self._row_to_job(row)

    def update_state(self, job_id: str, state: JobState, result: Dict = None, error: str = None):
        """Update job state."""
        with sqlite3.connect(self.db_path) as conn:
            updates = {"state": state.value}
            if state == JobState.RUNNING:
                updates["started_at"] = time.time()
            elif state in (JobState.COMPLETED, JobState.FAILED, JobState.CANCELED):
                updates["completed_at"] = time.time()
            if result:
                updates["result_data"] = json.dumps(result)
            if error:
                updates["error"] = error

            set_clause = ", ".join(f"{k} = ?" for k in updates)
            values = list(updates.values()) + [job_id]
            conn.execute(f"UPDATE jobs SET {set_clause} WHERE job_id = ?", values)

    def get_job(self, job_id: str) -> Optional[QuantumJob]:
        """Get a job by ID."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if row is None:
                return None
            return self._row_to_job(row)

    def list_jobs(self, state: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """List jobs."""
        with sqlite3.connect(self.db_path) as conn:
            if state:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE state = ? ORDER BY created_at DESC LIMIT ?",
                    (state, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def clear_completed(self):
        """Remove completed jobs."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM jobs WHERE state IN ('completed', 'failed', 'canceled')"
            )

    def queue_depth(self) -> int:
        """Get number of queued jobs."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE state = 'queued'"
            ).fetchone()
            return row[0] if row else 0

    def _row_to_job(self, row) -> QuantumJob:
        """Convert a database row to a QuantumJob."""
        from ..circuit import Circuit
        circuit_data = json.loads(row[1]) if row[1] else {"num_qubits": 2, "gates": []}
        circuit = Circuit(circuit_data.get("num_qubits", 2))
        for g in circuit_data.get("gates", []):
            circuit.add_gate(g["name"], g["qubits"], g.get("params"))

        return QuantumJob(
            job_id=row[0],
            circuit=circuit,
            backend_name=row[2],
            shots=row[3],
            priority=row[4],
            state=JobState(row[5]),
            created_at=row[6],
            started_at=row[7],
            completed_at=row[8],
            result=json.loads(row[9]) if row[9] else None,
            error=row[10],
            metadata=json.loads(row[11]) if row[11] else {},
        )

    def _row_to_dict(self, row) -> Dict:
        """Convert a database row to a dictionary."""
        return {
            "job_id": row[0],
            "backend_name": row[2],
            "shots": row[3],
            "priority": row[4],
            "state": row[5],
            "created_at": row[6],
        }
