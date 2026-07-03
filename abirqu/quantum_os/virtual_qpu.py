"""
Virtual QPU
===========
Virtual quantum processing unit with time-sharing on real hardware.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from ..circuit import Circuit
from ..backend import QuantumBackend, FastBackend


class VirtualQPU:
    """Virtual QPU that wraps a real backend with time-sharing.

    Provides isolation, resource quotas, and usage tracking.

    Parameters
    ----------
    name : str
        Virtual QPU name.
    backend : QuantumBackend
        The real backend to wrap.
    max_shots_per_job : int
        Maximum shots per job.
    max_jobs_per_hour : int
        Rate limit.
    """

    def __init__(
        self,
        name: str,
        backend: Optional[QuantumBackend] = None,
        max_shots_per_job: int = 10000,
        max_jobs_per_hour: int = 100,
    ):
        self.name = name
        self._backend = backend or FastBackend()
        self.max_shots_per_job = max_shots_per_job
        self.max_jobs_per_hour = max_jobs_per_hour
        self._job_count = 0
        self._total_shots = 0
        self._job_history: List[Dict[str, Any]] = []

    def run(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Run a circuit on the virtual QPU.

        Applies resource limits and usage tracking.
        """
        # Apply limits
        shots = min(shots, self.max_shots_per_job)

        # Execute
        start_time = time.time()
        result = self._backend.run_circuit(circuit, shots=shots, **kwargs)
        exec_time = time.time() - start_time

        # Track usage
        self._job_count += 1
        self._total_shots += shots
        self._job_history.append({
            "shots": shots,
            "execution_time": exec_time,
            "timestamp": start_time,
            "success": result.get("success", False),
        })

        result["virtual_qpu"] = self.name
        result["actual_backend"] = self._backend.name
        return result

    @property
    def stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "name": self.name,
            "backend": self._backend.name,
            "total_jobs": self._job_count,
            "total_shots": self._total_shots,
            "avg_shots_per_job": self._total_shots / max(1, self._job_count),
        }

    def get_backend(self) -> QuantumBackend:
        """Get the underlying real backend."""
        return self._backend
