"""
Resource Estimation for AbirQu
==============================

Estimate the physical resources required to run quantum circuits and
algorithms on fault-tolerant hardware.

Covers:

* **Circuit-level estimates** — physical qubits, T-count, depth, runtime.
* **Algorithm-level estimates** — Shor, Grover, VQE, HHL resource tables.
* **Overhead estimates** — surface-code overhead, magic-state factories.

Usage::

    from abirqu.resource_estimation import (
        ResourceEstimator, AlgorithmEstimator, LogicalQubitCost,
    )

    estimator = ResourceEstimator()
    estimate  = estimator.estimate_circuit(circuit)
    print(estimate)

    algo = AlgorithmEstimator()
    shor = algo.estimate_algorithm("shor", {"n_bits": 128})
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

from abirqu.circuit import Circuit


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ResourceEstimate:
    """Resource estimate for a single circuit or algorithm run.

    Attributes
    ----------
    physical_qubits : int
        Total number of physical qubits required.
    logical_qubits : int
        Number of logical (error-corrected) qubits.
    t_count : int
        Number of T-gates (dominant cost in fault-tolerant circuits).
    depth : int
        Circuit depth (longest path through the circuit).
    runtime_ms : float
        Estimated wall-clock runtime in milliseconds.
    memory_mb : float
        Estimated memory footprint in megabytes.
    circuit_volume : int
        ``depth × logical_qubits`` — a single-number complexity proxy.
    """

    physical_qubits: int = 0
    logical_qubits: int = 0
    t_count: int = 0
    depth: int = 0
    runtime_ms: float = 0.0
    memory_mb: float = 0.0
    circuit_volume: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __repr__(self) -> str:
        return (
            f"ResourceEstimate(logical_q={self.logical_qubits}, "
            f"physical_q={self.physical_qubits}, T={self.t_count}, "
            f"depth={self.depth}, vol={self.circuit_volume}, "
            f"runtime={self.runtime_ms:.2f}ms, mem={self.memory_mb:.2f}MB)"
        )


@dataclass
class OverheadEstimate:
    """Surface-code overhead for encoding logical qubits.

    Attributes
    ----------
    physical_per_logical : int
        Physical qubits per logical qubit at the given code distance.
    code_distance : int
        Minimum code distance ``d`` for the target logical error rate.
    rounds_per_logical : int
        Syndrome-extraction rounds per logical time step.
    magic_states : int
        Number of magic states required for T-gate distillation.
    """

    physical_per_logical: int = 0
    code_distance: int = 0
    rounds_per_logical: int = 0
    magic_states: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __repr__(self) -> str:
        return (
            f"OverheadEstimate(d={self.code_distance}, "
            f"phys/log={self.physical_per_logical}, "
            f"rounds={self.rounds_per_logical}, "
            f"magic={self.magic_states})"
        )


@dataclass
class LogicalQubitCost:
    """Per-logical-qubit cost model for a surface code at distance ``d``.

    Parameters
    ----------
    code_distance : int
        Surface code distance (must be odd and ≥ 3).
    physical_error_rate : float
        Assumed physical error rate per gate.
    t_factory_count : int
        Number of parallel T-state distillation factories.
    """

    code_distance: int = 3
    physical_error_rate: float = 1e-3
    t_factory_count: int = 1

    def cost(self, code_distance: int | None = None) -> Dict[str, Any]:
        """Return resource costs for a surface-code patch at distance *d*.

        Returns
        -------
        dict with keys:
            ``physical_qubits``, ``t_states``, ``time_overhead``,
            ``logical_error_rate``.
        """
        d = code_distance if code_distance is not None else self.code_distance
        if d < 3 or d % 2 == 0:
            raise ValueError(f"Code distance must be odd and >= 3, got {d}")

        # Surface code: 2d^2 - 1 data + ancilla qubits per patch
        physical_qubits = 2 * d * d - 1

        # Logical error rate approximation: p_L ≈ 0.1 × (p / p_th)^((d+1)/2)
        p_th = 0.01  # approximate threshold
        exponent = (d + 1) / 2
        logical_error_rate = 0.1 * (self.physical_error_rate / p_th) ** exponent

        # T-state production: ~d rounds per T-state in a standard factory
        t_time_overhead = d  # rounds per T-state
        t_states = self.t_factory_count  # T-states per round

        # Total time overhead: syndrome rounds + T distillation
        time_overhead = d  # base syndrome rounds per round

        return {
            "physical_qubits": physical_qubits,
            "t_states": t_states,
            "time_overhead": time_overhead,
            "t_time_overhead": t_time_overhead,
            "logical_error_rate": logical_error_rate,
            "code_distance": d,
        }


# ---------------------------------------------------------------------------
# Core estimator
# ---------------------------------------------------------------------------

# Approximate T-gate counts for common gate decompositions
_T_COUNTS: Dict[str, int] = {
    "T": 1,
    "T_dag": 1,
    "Tdg": 1,
    "S": 0,
    "S_dag": 0,
    "H": 0,
    "X": 0,
    "Y": 0,
    "Z": 0,
    "CNOT": 0,
    "CZ": 0,
    "SWAP": 0,
    "RX": 1,
    "RY": 1,
    "RZ": 1,
    "TOFFOLI": 7,
    "FREDKIN": 14,
}


class ResourceEstimator:
    """Estimate physical resources for AbirQu circuits.

    Parameters
    ----------
    code_distance : int
        Surface code distance for logical-to-physical qubit conversion.
    physical_error_rate : float
        Physical error rate per gate (for threshold estimates).
    clock_ghz : float
        Physical clock speed in GHz (for runtime estimates).
    """

    def __init__(
        self,
        code_distance: int = 5,
        physical_error_rate: float = 1e-3,
        clock_ghz: float = 1.0,
    ) -> None:
        self.code_distance = code_distance
        self.physical_error_rate = physical_error_rate
        self.clock_ghz = clock_ghz
        self._qubit_cost = LogicalQubitCost(
            code_distance=code_distance,
            physical_error_rate=physical_error_rate,
        )

    def estimate_circuit(self, circuit: Circuit) -> ResourceEstimate:
        """Produce a ``ResourceEstimate`` for a single AbirQu ``Circuit``.

        Parameters
        ----------
        circuit : Circuit
            The circuit to analyse.

        Returns
        -------
        ResourceEstimate
        """
        logical_qubits = circuit.num_qubits
        depth = circuit.depth()
        gate_counts = circuit.count_gates()

        # T-count estimation
        t_count = 0
        for gate_name, count in gate_counts.items():
            norm = gate_name.split("(")[0]
            t_count += _T_COUNTS.get(norm, 1) * count

        # Physical qubits via surface code overhead
        overhead = self._qubit_cost.cost(self.code_distance)
        physical_per_logical = overhead["physical_qubits"]
        physical_qubits = logical_qubits * physical_per_logical

        # Runtime estimation (ns per layer × depth + T-distillation overhead)
        ns_per_cycle = 1.0 / (self.clock_ghz * 1e3)  # GHz → ns per cycle
        base_time_ns = depth * ns_per_cycle
        t_overhead_ns = t_count * overhead["t_time_overhead"] * ns_per_cycle
        runtime_ms = (base_time_ns + t_overhead_ns) * 1e-6

        # Memory: statevector ≈ 2^n complex amplitudes × 16 bytes + circuit storage
        statevec_mb = (2 ** logical_qubits * 16) / (1024 * 1024)
        circuit_mb = len(circuit.gates) * 64 / (1024 * 1024)  # ~64 bytes per gate
        memory_mb = statevec_mb + circuit_mb

        circuit_volume = depth * logical_qubits

        return ResourceEstimate(
            physical_qubits=physical_qubits,
            logical_qubits=logical_qubits,
            t_count=t_count,
            depth=depth,
            runtime_ms=round(runtime_ms, 4),
            memory_mb=round(memory_mb, 4),
            circuit_volume=circuit_volume,
        )

    def estimate_algorithm(
        self,
        algorithm_type: str,
        params: Dict[str, Any],
    ) -> ResourceEstimate:
        """High-level resource estimate for a named algorithm.

        Parameters
        ----------
        algorithm_type : str
            One of ``"shor"``, ``"grover"``, ``"vqe"``, ``"hhl"``.
        params : dict
            Algorithm-specific parameters (see ``AlgorithmEstimator``).

        Returns
        -------
        ResourceEstimate
        """
        estimator = AlgorithmEstimator(
            code_distance=self.code_distance,
            physical_error_rate=self.physical_error_rate,
            clock_ghz=self.clock_ghz,
        )
        return estimator.estimate_algorithm(algorithm_type, params)

    def estimate_overhead(
        self,
        code_type: str = "surface",
        logical_qubits: int = 1,
    ) -> OverheadEstimate:
        """Estimate the encoding overhead for *logical_qubits* under *code_type*.

        Parameters
        ----------
        code_type : str
            Only ``"surface"`` is supported currently.
        logical_qubits : int
            Number of logical qubits to encode.

        Returns
        -------
        OverheadEstimate
        """
        if code_type != "surface":
            raise ValueError(f"Unsupported code type: {code_type!r} (only 'surface' supported)")

        cost = self._qubit_cost.cost(self.code_distance)
        return OverheadEstimate(
            physical_per_logical=cost["physical_qubits"],
            code_distance=self.code_distance,
            rounds_per_logical=cost["time_overhead"],
            magic_states=cost["t_states"] * logical_qubits,
        )


# ---------------------------------------------------------------------------
# Algorithm-level estimator
# ---------------------------------------------------------------------------

class AlgorithmEstimator:
    """Pre-built resource estimates for canonical quantum algorithms.

    Parameters
    ----------
    code_distance : int
        Surface code distance.
    physical_error_rate : float
        Physical error rate per gate.
    clock_ghz : float
        Clock speed in GHz.
    """

    def __init__(
        self,
        code_distance: int = 5,
        physical_error_rate: float = 1e-3,
        clock_ghz: float = 1.0,
    ) -> None:
        self.code_distance = code_distance
        self.physical_error_rate = physical_error_rate
        self.clock_ghz = clock_ghz
        self._qubit_cost = LogicalQubitCost(
            code_distance=code_distance,
            physical_error_rate=physical_error_rate,
        )

    def estimate_algorithm(
        self,
        algorithm_type: str,
        params: Dict[str, Any],
    ) -> ResourceEstimate:
        """Return a ``ResourceEstimate`` for a standard algorithm.

        Supported algorithms and parameters
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        ``"shor"``
            * ``n_bits`` (int, default 128) — bit-length of the number to factor.

        ``"grover"``
            * ``search_space`` (int, default 2**20) — size of the unstructured search space.
            * ``iterations`` (int, optional) — override Grover iteration count.

        ``"vqe"``
            * ``n_qubits`` (int, default 12) — number of qubits in the ansatz.
            * ``n_layers`` (int, default 4) — depth of the hardware-efficient ansatz.

        ``"hhl"``
            * ``matrix_size`` (int, default 8) — dimension of the linear system.

        Returns
        -------
        ResourceEstimate
        """
        dispatch = {
            "shor": self._estimate_shor,
            "grover": self._estimate_grover,
            "vqe": self._estimate_vqe,
            "hhl": self._estimate_hhl,
        }
        fn = dispatch.get(algorithm_type.lower())
        if fn is None:
            raise ValueError(
                f"Unknown algorithm: {algorithm_type!r}. "
                f"Supported: {', '.join(dispatch)}"
            )
        return fn(params)

    # ── Shor ──────────────────────────────────────────────────────────────

    def _estimate_shor(self, params: Dict[str, Any]) -> ResourceEstimate:
        """Shor's algorithm for factoring an *n*-bit integer.

        Resources based on:
        - Gidney & Ekerå (2021) "How to factor 2048 bit RSA integers in 8 hours
          using 20 million noisy qubits."
        """
        n = int(params.get("n_bits", 128))
        n = max(4, n)

        # Logical qubits: ~2n for the arithmetic registers + workspace
        logical_qubits = 2 * n + 4

        # T-count: ~O(n^3) for modular exponentiation
        t_count = int(10 * n ** 3)

        # Circuit depth: ~O(n^3) with pipelined modular exponentiation
        depth = int(5 * n ** 3)

        cost = self._qubit_cost.cost(self.code_distance)
        physical_per_logical = cost["physical_qubits"]
        physical_qubits = logical_qubits * physical_per_logical

        ns_per_cycle = 1.0 / (self.clock_ghz * 1e3)
        runtime_ms = (depth * ns_per_cycle + t_count * cost["t_time_overhead"] * ns_per_cycle) * 1e-6

        # Rough memory: statevector is infeasible; we report circuit store only
        memory_mb = (logical_qubits * 1024) / (1024 * 1024)  # ~1 KB per logical qubit (classical)

        return ResourceEstimate(
            physical_qubits=physical_qubits,
            logical_qubits=logical_qubits,
            t_count=t_count,
            depth=depth,
            runtime_ms=round(runtime_ms, 4),
            memory_mb=round(memory_mb, 4),
            circuit_volume=depth * logical_qubits,
        )

    # ── Grover ────────────────────────────────────────────────────────────

    def _estimate_grover(self, params: Dict[str, Any]) -> ResourceEstimate:
        """Grover search over an unstructured space of size *search_space*."""
        search_space = int(params.get("search_space", 2 ** 20))
        n_qubits = max(1, math.ceil(math.log2(search_space)))
        iterations = int(params.get(
            "iterations",
            max(1, int(math.pi / 4 * math.sqrt(search_space))),
        ))

        logical_qubits = n_qubits
        # Each Grover iteration: oracle + diffusion ≈ 2n gates
        gates_per_iter = 4 * n_qubits
        depth = iterations * gates_per_iter
        t_count = iterations * n_qubits  # each iteration needs ~n T-gates for oracle

        cost = self._qubit_cost.cost(self.code_distance)
        physical_qubits = logical_qubits * cost["physical_qubits"]

        ns_per_cycle = 1.0 / (self.clock_ghz * 1e3)
        runtime_ms = (depth * ns_per_cycle + t_count * cost["t_time_overhead"] * ns_per_cycle) * 1e-6
        memory_mb = (2 ** n_qubits * 16) / (1024 * 1024)

        return ResourceEstimate(
            physical_qubits=physical_qubits,
            logical_qubits=logical_qubits,
            t_count=t_count,
            depth=depth,
            runtime_ms=round(runtime_ms, 4),
            memory_mb=round(memory_mb, 4),
            circuit_volume=depth * logical_qubits,
        )

    # ── VQE ───────────────────────────────────────────────────────────────

    def _estimate_vqe(self, params: Dict[str, Any]) -> ResourceEstimate:
        """Variational Quantum Eigensolver with a hardware-efficient ansatz."""
        n_qubits = int(params.get("n_qubits", 12))
        n_layers = int(params.get("n_layers", 4))

        logical_qubits = n_qubits
        # Each layer: n single-qubit rotations + (n-1) entangling gates
        gates_per_layer = 2 * n_qubits + (n_qubits - 1)
        depth = n_layers * gates_per_layer
        t_count = n_layers * n_qubits  # each rotation ≈ 1 T-gate via decomposition

        cost = self._qubit_cost.cost(self.code_distance)
        physical_qubits = logical_qubits * cost["physical_qubits"]

        ns_per_cycle = 1.0 / (self.clock_ghz * 1e3)
        runtime_ms = (depth * ns_per_cycle + t_count * cost["t_time_overhead"] * ns_per_cycle) * 1e-6
        memory_mb = (2 ** n_qubits * 16) / (1024 * 1024)

        return ResourceEstimate(
            physical_qubits=physical_qubits,
            logical_qubits=logical_qubits,
            t_count=t_count,
            depth=depth,
            runtime_ms=round(runtime_ms, 4),
            memory_mb=round(memory_mb, 4),
            circuit_volume=depth * logical_qubits,
        )

    # ── HHL ───────────────────────────────────────────────────────────────

    def _estimate_hhl(self, params: Dict[str, Any]) -> ResourceEstimate:
        """HHL algorithm for solving A·x = b on a system of size *matrix_size*."""
        matrix_size = int(params.get("matrix_size", 8))
        n = max(2, math.ceil(math.log2(matrix_size)))

        # HHL requires: n data qubits + n precision qubits + 1 ancilla
        logical_qubits = 2 * n + 1

        # T-count: O(n^3) for controlled rotations + O(n^2) for QPE
        t_count = int(4 * n ** 3 + 2 * n ** 2)
        depth = int(3 * n ** 3)

        cost = self._qubit_cost.cost(self.code_distance)
        physical_qubits = logical_qubits * cost["physical_qubits"]

        ns_per_cycle = 1.0 / (self.clock_ghz * 1e3)
        runtime_ms = (depth * ns_per_cycle + t_count * cost["t_time_overhead"] * ns_per_cycle) * 1e-6
        memory_mb = (2 ** logical_qubits * 16) / (1024 * 1024)

        return ResourceEstimate(
            physical_qubits=physical_qubits,
            logical_qubits=logical_qubits,
            t_count=t_count,
            depth=depth,
            runtime_ms=round(runtime_ms, 4),
            memory_mb=round(memory_mb, 4),
            circuit_volume=depth * logical_qubits,
        )


__all__ = [
    "ResourceEstimate",
    "OverheadEstimate",
    "LogicalQubitCost",
    "ResourceEstimator",
    "AlgorithmEstimator",
]
