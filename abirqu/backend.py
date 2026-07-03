"""
AbirQu Backend Framework
========================
Unified, hardware-agnostic backend API for running quantum circuits.

Core classes:
- QuantumBackend : Abstract base class for all backends
- FastBackend    : Local Rust/NumPy statevector simulator
- BackendRegistry: Auto-discovery and management of backends
- JobHandle      : Async job tracking for remote backends

Usage
-----
    from abirqu.backend import FastBackend, BackendRegistry
    from abirqu.circuit import Circuit

    circ = Circuit(2)
    circ.h(0)
    circ.cnot(0, 1)

    # Local simulation
    backend = FastBackend(n_qubits=2)
    result = backend.run_circuit(circ, shots=1024)

    # Remote hardware
    registry = BackendRegistry()
    backend = registry.get("ibm")
    handle = backend.submit(circ, shots=1024)
    result = handle.result()
"""

from __future__ import annotations

import abc
import importlib
import inspect
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Type

import numpy as np

from .circuit import Circuit
from .simulator import SimulatorBackend, RustSimulator, _serialize_circuit, HAS_RUST_CORE

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Job status and handle
# ──────────────────────────────────────────────────────────────────────────────

class JobStatus(str, Enum):
    """Status of a quantum job."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    UNKNOWN = "unknown"


class JobHandle:
    """Handle for tracking an asynchronous quantum job.

    Returned by ``QuantumBackend.submit()``.  Use :meth:`result` to block
    until the job completes and retrieve the result dict.
    """

    def __init__(
        self,
        job_id: str,
        backend: "QuantumBackend",
        status: JobStatus = JobStatus.QUEUED,
        poll_interval: float = 2.0,
        timeout: float = 600.0,
    ):
        self.job_id = job_id
        self.backend = backend
        self._status = status
        self._result: Optional[Dict[str, Any]] = None
        self._error: Optional[Exception] = None
        self.poll_interval = poll_interval
        self.timeout = timeout

    @property
    def status(self) -> JobStatus:
        return self._status

    def cancel(self) -> bool:
        """Cancel the job.  Returns True if cancellation was requested."""
        try:
            return self.backend.cancel_job(self.job_id)
        except Exception:
            return False

    def result(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Block until the job completes and return the result."""
        if self._result is not None:
            return self._result
        if self._error is not None:
            raise self._error

        t0 = time.monotonic()
        max_wait = timeout or self.timeout

        while time.monotonic() - t0 < max_wait:
            status = self.backend.query_job(self.job_id)
            self._status = status

            if status == JobStatus.COMPLETED:
                self._result = self.backend.fetch_result(self.job_id)
                return self._result
            elif status == JobStatus.FAILED:
                self._error = RuntimeError(f"Job {self.job_id} failed")
                raise self._error
            elif status == JobStatus.CANCELED:
                self._error = RuntimeError(f"Job {self.job_id} was canceled")
                raise self._error

            time.sleep(self.poll_interval)

        raise TimeoutError(
            f"Job {self.job_id} timed out after {max_wait}s (status={self._status})"
        )


# ──────────────────────────────────────────────────────────────────────────────
# Base class
# ──────────────────────────────────────────────────────────────────────────────

class QuantumBackend(abc.ABC):
    """Abstract base class for all AbirQu backends.

    Every backend must implement :meth:`run_circuit` (synchronous) and
    should implement :meth:`submit` (asynchronous) for remote backends.

    Return value of ``run_circuit`` is always a ``Result`` dict with at
    least the keys ``success``, ``counts``, and ``probabilities``.
    """

    name: str = "QuantumBackend"
    max_qubits: Optional[int] = None
    native_gates: List[str] = []
    supports_noise_model: bool = False
    is_local: bool = False

    # ── Synchronous execution ─────────────────────────────────────────────

    @abc.abstractmethod
    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute *circuit* synchronously and return a result dictionary.

        Returns
        -------
        dict with keys:
            success       – bool
            backend       – str (backend name)
            shots         – int
            counts        – dict[bitstring, count]
            probabilities – dict[bitstring, probability] | None
            statevector   – list[complex] | None  (if shots==0)
        """

    def run_batch(
        self,
        circuits: List[Circuit],
        shots: int = 1024,
    ) -> List[Dict[str, Any]]:
        """Execute multiple circuits sequentially."""
        return [self.run_circuit(c, shots=shots) for c in circuits]

    # ── Asynchronous execution (remote backends) ──────────────────────────

    def submit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> JobHandle:
        """Submit *circuit* asynchronously and return a :class:`JobHandle`.

        Default implementation runs synchronously and wraps the result.
        Override for real async remote backends.
        """
        job_id = f"local-{int(time.time() * 1000)}"
        result = self.run_circuit(circuit, shots=shots, **kwargs)
        handle = JobHandle(job_id=job_id, backend=self, status=JobStatus.COMPLETED)
        handle._result = result
        return handle

    def query_job(self, job_id: str) -> JobStatus:
        """Query the status of a submitted job.

        Override for remote backends with real job polling.
        """
        return JobStatus.COMPLETED

    def fetch_result(self, job_id: str) -> Dict[str, Any]:
        """Fetch the result of a completed job.

        Override for remote backends.
        """
        return {"success": True, "backend": self.name, "job_id": job_id}

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job.  Returns True if successful.

        Override for remote backends.
        """
        return False

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _counts_to_probs(counts: Dict[str, int], shots: int) -> Dict[str, float]:
        if shots == 0:
            return {}
        return {k: v / shots for k, v in counts.items()}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


# ──────────────────────────────────────────────────────────────────────────────
# FastBackend — local Rust/NumPy statevector simulator
# ──────────────────────────────────────────────────────────────────────────────

class FastBackend(QuantumBackend):
    """High-performance local Rust statevector simulator.

    Uses the compiled Rust core (AVX-512/SIMD optimised) when available,
    falling back to the NumPy QVM for portability.

    Parameters
    ----------
    n_qubits: int
        Number of qubits.  Inferred from the circuit when ``None``.
    use_gpu: bool
        Attempt to use GPU acceleration (requires CUDA build).
    """

    name = "AbirQu-FastBackend"
    is_local = True
    supports_noise_model = True

    def __init__(self, n_qubits: Optional[int] = None, use_gpu: bool = False):
        self._n_qubits = n_qubits
        self._use_gpu = use_gpu
        self._delegate = SimulatorBackend(use_gpu=use_gpu)

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        noise_model=None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        n = self._n_qubits or circuit.num_qubits

        # ── Rust path ─────────────────────────────────────────────────────
        if HAS_RUST_CORE:
            sim = RustSimulator(n)
            sim.run_circuit(_serialize_circuit(circuit))

            raw = sim.get_probabilities_bytes()
            if isinstance(raw, (bytes, bytearray)):
                probs_arr = np.frombuffer(raw, dtype=np.float64).copy()
            else:
                probs_arr = np.array(sim.get_probabilities(), dtype=np.float64)

            if noise_model is not None:
                try:
                    probs_arr = noise_model.apply_to_probs_array(probs_arr, n)
                except Exception:
                    pass

            total = probs_arr.sum()
            if total > 0:
                probs_arr /= total

            probs_dict = {
                format(i, f"0{n}b"): float(p)
                for i, p in enumerate(probs_arr)
                if p > 0
            }

            counts: Dict[str, int] = {}
            if shots > 0:
                indices = np.random.choice(len(probs_arr), size=shots, p=probs_arr)
                unique_idx, raw_counts = np.unique(indices, return_counts=True)
                counts = {
                    format(int(u), f"0{n}b"): int(c)
                    for u, c in zip(unique_idx, raw_counts)
                }

            statevector = None
            if shots == 0:
                try:
                    statevector = list(sim.get_statevector())
                except Exception:
                    statevector = None

            return {
                "success": True,
                "backend": self.name,
                "shots": shots,
                "counts": counts,
                "probabilities": probs_dict,
                "statevector": statevector,
            }

        # ── NumPy fallback ────────────────────────────────────────────────
        result = self._delegate.run(circuit, shots=shots, noise_model=noise_model)
        counts = result.get("counts", {})
        probs = self._counts_to_probs(counts, shots) if shots > 0 else {}
        return {
            "success": result.get("success", True),
            "backend": self.name + "(numpy-fallback)",
            "shots": shots,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }


# ──────────────────────────────────────────────────────────────────────────────
# BackendRegistry — auto-discovery and management
# ──────────────────────────────────────────────────────────────────────────────

class BackendRegistry:
    """Registry of all available backends.

    Provides auto-discovery via ``importlib.metadata`` entry points and
    manual registration.  Call :meth:`get` to retrieve a backend by name.
    """

    _registry: Dict[str, Type[QuantumBackend]] = {}
    _instances: Dict[str, QuantumBackend] = {}

    def __init__(self):
        if not BackendRegistry._registry:
            self._discover_builtin()
            self._discover_entry_points()

    # ── Built-in discovery ────────────────────────────────────────────────

    def _discover_builtin(self):
        """Register built-in backends from this package."""
        from . import backends as _pkg

        _mapping = {
            "fast": FastBackend,
            "local": FastBackend,
        }

        # Scan backends subpackage for ABC-integrated backends
        for name in dir(_pkg):
            obj = getattr(_pkg, name, None)
            if (
                inspect.isclass(obj)
                and issubclass(obj, QuantumBackend)
                and obj is not QuantumBackend
                and obj is not FastBackend
            ):
                key = getattr(obj, "name", name).lower().replace("-", "").replace("_", "")
                _mapping[key] = obj

        # Also scan this module for classes defined here
        for name in dir():
            obj = globals().get(name)
            if (
                inspect.isclass(obj)
                and issubclass(obj, QuantumBackend)
                and obj is not QuantumBackend
                and obj is not FastBackend
            ):
                key = getattr(obj, "name", name).lower().replace("-", "").replace("_", "")
                _mapping[key] = obj

        BackendRegistry._registry.update(_mapping)

    def _discover_entry_points(self):
        """Discover backends registered via importlib.metadata entry points."""
        try:
            eps = importlib.metadata.entry_points()
            group = getattr(eps, "select", None)
            if group:
                entries = group(group="abirqu.backends")
            else:
                entries = eps.get("abirqu.backends", [])
            for ep in entries:
                try:
                    cls = ep.load()
                    if inspect.isclass(cls) and issubclass(cls, QuantumBackend):
                        key = getattr(cls, "name", ep.name).lower().replace("-", "").replace("_", "")
                        BackendRegistry._registry[key] = cls
                except Exception as exc:
                    logger.warning("Failed to load backend plugin %s: %s", ep.name, exc)
        except Exception:
            pass

    # ── Public API ────────────────────────────────────────────────────────

    def register(self, name: str, backend_cls: Type[QuantumBackend]):
        """Register a backend class under *name*."""
        BackendRegistry._registry[name.lower()] = backend_cls

    def get(self, name: str, **kwargs) -> QuantumBackend:
        """Get a backend instance by name.

        Returns a cached instance if one exists, otherwise creates one.
        """
        key = name.lower().replace("-", "").replace("_", "")
        if key in BackendRegistry._instances:
            return BackendRegistry._instances[key]

        cls = BackendRegistry._registry.get(key)
        if cls is None:
            raise KeyError(
                f"Unknown backend '{name}'. Available: {list(BackendRegistry._registry.keys())}"
            )

        instance = cls(**kwargs)
        BackendRegistry._instances[key] = instance
        return instance

    def list_available(self) -> List[str]:
        """List all registered backend names."""
        return sorted(BackendRegistry._registry.keys())

    def is_available(self, name: str) -> bool:
        """Check if a backend is registered."""
        key = name.lower().replace("-", "").replace("_", "")
        return key in BackendRegistry._registry

    def clear(self):
        """Clear cached instances (useful for testing)."""
        BackendRegistry._instances.clear()


# ──────────────────────────────────────────────────────────────────────────────
# Auto-selector
# ──────────────────────────────────────────────────────────────────────────────

def get_best_backend(n_qubits: int = 30, **kwargs: Any) -> QuantumBackend:
    """Return the fastest available local backend for the given qubit count."""
    return FastBackend(n_qubits=n_qubits, **kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Public exports
# ──────────────────────────────────────────────────────────────────────────────

__all__ = [
    "JobStatus",
    "JobHandle",
    "QuantumBackend",
    "FastBackend",
    "BackendRegistry",
    "get_best_backend",
]
