"""
Resource Manager
================
Track QPU availability and manage resource allocation.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ResourcePool:
    """A pool of quantum computing resources.

    Attributes
    ----------
    name : str
        Pool name (e.g. 'ibm', 'dwave').
    backends : list
        Available backend names.
    max_concurrent : int
        Maximum concurrent jobs.
    credits_per_shot : float
        Cost per shot in credits.
    """
    name: str
    backends: List[str] = field(default_factory=list)
    max_concurrent: int = 1
    credits_per_shot: float = 0.0
    current_usage: int = 0
    total_jobs: int = 0
    total_shots: int = 0


class ResourceManager:
    """Manage quantum computing resources across providers.

    Tracks availability, usage, and allocation of quantum backends.
    """

    def __init__(self):
        self._pools: Dict[str, ResourcePool] = {}
        self._allocations: Dict[str, str] = {}  # job_id -> pool_name
        self._init_default_pools()

    def _init_default_pools(self):
        """Initialize default resource pools."""
        self._pools["local"] = ResourcePool(
            name="local",
            backends=["fast", "local"],
            max_concurrent=10,
            credits_per_shot=0.0,
        )
        self._pools["ibm"] = ResourcePool(
            name="ibm",
            backends=["ibmq_qasm_simulator", "ibm_brisbane", "ibm_osaka"],
            max_concurrent=3,
            credits_per_shot=0.001,
        )
        self._pools["dwave"] = ResourcePool(
            name="dwave",
            backends=["simulated-annealing", "Advantage_system6.4"],
            max_concurrent=2,
            credits_per_shot=0.0005,
        )
        self._pools["spinq"] = ResourcePool(
            name="spinq",
            backends=["SpinQ-3", "SpinQ-6"],
            max_concurrent=1,
            credits_per_shot=0.002,
        )

    def register_pool(self, pool: ResourcePool):
        """Register a resource pool."""
        self._pools[pool.name] = pool

    def allocate(self, job_id: str, backend_name: str) -> Optional[str]:
        """Allocate a backend for a job.

        Returns the pool name if allocation succeeded, None otherwise.
        """
        for pool_name, pool in self._pools.items():
            if backend_name in pool.backends:
                if pool.current_usage < pool.max_concurrent:
                    pool.current_usage += 1
                    self._allocations[job_id] = pool_name
                    logger.debug("Allocated pool %s for job %s", pool_name, job_id)
                    return pool_name
        logger.warning("No available pool for backend %s (job %s)", backend_name, job_id)
        return None

    def release(self, job_id: str):
        """Release an allocation."""
        pool_name = self._allocations.pop(job_id, None)
        if pool_name and pool_name in self._pools:
            pool = self._pools[pool_name]
            pool.current_usage = max(0, pool.current_usage - 1)
            pool.total_jobs += 1
            logger.debug("Released pool %s for job %s", pool_name, job_id)

    def get_pool_status(self) -> Dict[str, Any]:
        """Get status of all resource pools."""
        return {
            name: {
                "backends": pool.backends,
                "max_concurrent": pool.max_concurrent,
                "current_usage": pool.current_usage,
                "available": pool.max_concurrent - pool.current_usage,
                "credits_per_shot": pool.credits_per_shot,
            }
            for name, pool in self._pools.items()
        }

    def estimate_cost(self, backend_name: str, shots: int) -> float:
        """Estimate the cost of a job."""
        for pool in self._pools.values():
            if backend_name in pool.backends:
                return pool.credits_per_shot * shots
        return 0.0

    def list_backends(self) -> List[Dict[str, Any]]:
        """List all available backends with their status."""
        result = []
        for pool_name, pool in self._pools.items():
            for backend in pool.backends:
                result.append({
                    "backend": backend,
                    "pool": pool_name,
                    "available": pool.current_usage < pool.max_concurrent,
                    "credits_per_shot": pool.credits_per_shot,
                })
        return result
