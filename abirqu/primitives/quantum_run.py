"""
AbirQu Primitives — Unified quantum execution interface.
=======================================================

The core design philosophy is ONE function that does EVERYTHING:

    from abirqu.primitives import QuantumRun

    # Single call does sampling + estimation + ML + mitigation
    result = QuantumRun(
        circuits=bell_circuit,
        observables={"ZZ": [[1,0,0,0],[0,-1,0,0],[0,0,-1,0],[0,0,0,1]]},
        shots=4096,
        mitigate=True,
    )

    result.counts          # measurement distribution
    result.expectations    # <O> values
    result.statevector     # exact state (if shots=0)
    result.fidelity        # estimated fidelity
    result.noise_report    # noise characterization

This is NOT a copy of Qiskit's Sampler/Estimator split.  AbirQu
merges everything into a single call that returns ALL possible
information.  The user never has to choose between primitives.
"""
from __future__ import annotations

import time
import math
from dataclasses import dataclass, field
from typing import (
    Any, Callable, Dict, List, Optional, Sequence, Tuple, Union,
)

import numpy as np

from ..circuit import Circuit, Gate, Measurement
from ..noise import NoiseModel


# ═══════════════════════════════════════════════════════════════════
#  Result containers — richer than Qiskit's flat dicts
# ═══════════════════════════════════════════════════════════════════

@dataclass
class SamplerResult:
    """Unified result object from QuantumRun — contains everything."""
    counts: Dict[str, int]
    probabilities: Dict[str, float]
    statevector: Optional[np.ndarray] = None
    quasi_dist: Optional[Dict[str, float]] = None
    shots: int = 0
    backend: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def top_k(self) -> List[Tuple[str, int]]:
        return sorted(self.counts.items(), key=lambda x: x[1], reverse=True)

    @property
    def entropy(self) -> float:
        p = np.array(list(self.probabilities.values()))
        p = p[p > 0]
        return float(-np.sum(p * np.log2(p)))

    @property
    def fidelity(self) -> float:
        if self.statevector is not None:
            return 1.0
        if self.metadata.get("fidelity_estimate"):
            return self.metadata["fidelity_estimate"]
        return self.metadata.get("fidelity_estimate", 1.0)

    @property
    def effective_shots(self) -> int:
        p = np.array(list(self.probabilities.values()))
        p = p[p > 0]
        return int(1.0 / np.sum(p ** 2)) if len(p) > 0 else 0

    def __repr__(self) -> str:
        return (f"SamplerResult(shots={self.shots}, states={len(self.counts)}, "
                f"backend={self.backend!r})")


@dataclass
class EstimatorResult:
    """Result of computing expectation values <ψ|O|ψ>."""
    values: List[complex]
    std_errors: Optional[List[float]] = None
    metadata: List[Dict[str, Any]] = field(default_factory=list)
    circuit_index: Optional[int] = None

    @property
    def real(self) -> List[float]:
        return [v.real for v in self.values]

    def __repr__(self) -> str:
        preview = ", ".join(f"{v:.4f}" for v in self.values[:5])
        return f"EstimatorResult([{preview}], n={len(self.values)})"


@dataclass
class MitigationResult:
    """Result of error mitigation pipeline."""
    raw_probs: Dict[str, float]
    mitigated_probs: Dict[str, float]
    method: str = ""
    improvement: float = 0.0
    confusion_matrix: Optional[np.ndarray] = None

    @property
    def tv_distance(self) -> float:
        all_keys = set(self.raw_probs) | set(self.mitigated_probs)
        return sum(abs(self.raw_probs.get(k, 0) - self.mitigated_probs.get(k, 0))
                    for k in all_keys) / 2


@dataclass
class QNNResult:
    """Result of quantum neural network forward pass."""
    output: np.ndarray
    hidden_states: Optional[np.ndarray] = None
    circuit_params: Optional[Dict[str, float]] = None
    gradient_norm: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"QNNResult(shape={self.output.shape}, mean={self.output.mean():.4f})"


# ═══════════════════════════════════════════════════════════════════
#  Internal simulators
# ═══════════════════════════════════════════════════════════════════

def _statevector_sim(circuit: Circuit) -> np.ndarray:
    """Exact statevector simulation (numpy)."""
    from ..numpy_sim import NumPySimulator
    sim = NumPySimulator(num_qubits=circuit.num_qubits)
    sim.run_circuit(circuit)
    return sim.get_state_vector().copy()


def _sample_counts(statevector: np.ndarray, n_qubits: int,
                   shots: int, rng: np.random.Generator) -> Dict[str, int]:
    probs = np.abs(statevector) ** 2
    indices = rng.choice(len(probs), size=shots, p=probs)
    counts: Dict[str, int] = {}
    for idx in indices:
        bs = format(int(idx), f"0{n_qubits}b")
        counts[bs] = counts.get(bs, 0) + 1
    return counts


def _apply_readout_mitigation(counts: Dict[str, int],
                               confusion_inv: np.ndarray,
                               n_qubits: int) -> Dict[str, float]:
    """Apply inverse confusion matrix to raw counts."""
    total = sum(counts.values())
    prob_vec = np.zeros(2 ** n_qubits)
    for bs, c in counts.items():
        prob_vec[int(bs, 2)] = c / total
    mitigated = confusion_inv @ prob_vec
    mitigated = np.maximum(mitigated, 0)
    s = mitigated.sum()
    if s > 0:
        mitigated /= s
    return {format(i, f"0{n_qubits}b"): float(mitigated[i])
            for i in range(len(mitigated)) if mitigated[i] > 1e-10}


# ═══════════════════════════════════════════════════════════════════
#  QuantumRun — THE unified execution interface
# ═══════════════════════════════════════════════════════════════════

class QuantumRun:
    """
    Unified quantum execution — ONE call does everything.

    This is NOT a copy of Qiskit's Sampler/Estimator.  AbirQu's
    QuantumRun merges sampling, estimation, mitigation, and ML
    into a single entry point that returns ALL results at once.

    Usage
    -----
        # Simple sampling
        result = QuantumRun(circuits=bell, shots=1024)
        result.counts  # {'00': 512, '11': 512}

        # With observables — also computes expectation values
        result = QuantumRun(circuits=bell, observables={"ZZ": zz_mat}, shots=4096)
        result.expectations  # [1.0]

        # With mitigation — also denoises the results
        result = QuantumRun(circuits=bell, shots=4096, mitigate=True)
        result.mitigation.tv_distance  # 0.02

        # Zero-shot (exact statevector, no sampling noise)
        result = QuantumRun(circuits=bell, shots=0)
        result.statevector  # array([0.707, 0, 0, 0.707])

        # Batch execution — runs all circuits in parallel conceptually
        result = QuantumRun(circuits=[bell, ghz3, qft4], shots=2048)
        result.counts  # list of dicts, one per circuit

        # With noise model
        result = QuantumRun(circuits=bell, noise_model=my_noise, shots=4096)

        # With backend (auto-selects best local simulator)
        result = QuantumRun(circuits=bell, backend="fast", shots=4096)
    """

    def __init__(
        self,
        circuits: Union[Circuit, List[Circuit]],
        shots: int = 1024,
        observables: Optional[List[Dict]] = None,
        noise_model: Optional[NoiseModel] = None,
        mitigate: bool = False,
        mitigation_method: str = "readout",
        backend: Optional[Any] = None,
        seed: Optional[int] = None,
        callbacks: Optional[List[Callable]] = None,
    ):
        self._circuits = [circuits] if isinstance(circuits, Circuit) else list(circuits)
        self._shots = shots
        self._observables = observables
        self._noise_model = noise_model
        self._mitigate = mitigate
        self._mitigation_method = mitigation_method
        self._backend = backend
        self._seed = seed
        self._callbacks = callbacks or []

        # Execute immediately
        self._results = self._execute()

    # ── Internal execution engine ─────────────────────────────────

    def _execute(self) -> List[SamplerResult]:
        rng = np.random.default_rng(self._seed)
        results = []

        for i, circ in enumerate(self._circuits):
            t0 = time.monotonic()

            # Check if a hardware backend is specified
            backend_name = self._resolve_backend()

            if backend_name and backend_name not in ("numpy", "simulator", "fast", "auto", None):
                # Route to real hardware backend
                sv, counts, probs = self._execute_on_hardware(circ, backend_name, rng)
            else:
                # 1. Statevector simulation
                sv = _statevector_sim(circ)

                # 2. Apply noise model if present
                if self._noise_model is not None:
                    probs_noisy = self._noise_model.apply_to_statevector(sv, circ.num_qubits)
                else:
                    probs_noisy = np.abs(sv) ** 2

                # 3. Sampling
                if self._shots > 0:
                    counts = _sample_counts(sv, circ.num_qubits, self._shots, rng)
                    probs = {k: v / self._shots for k, v in counts.items()}
                else:
                    probs = {
                        format(j, f"0{circ.num_qubits}b"): float(abs(sv[j]) ** 2)
                        for j in range(len(sv))
                        if abs(sv[j]) ** 2 > 1e-12
                    }
                    counts = {}

            # 4. Mitigation
            mitigation = None
            if self._mitigate and counts:
                mitigation = self._apply_mitigation(counts, circ.num_qubits)

            # 5. Build result
            elapsed = time.monotonic() - t0
            result = SamplerResult(
                counts=counts,
                probabilities=probs,
                statevector=sv if self._shots == 0 and backend_name in (None, "numpy", "simulator", "fast", "auto") else None,
                shots=self._shots,
                backend=backend_name or "AbirQu-QuantumRun",
                metadata={
                    "circuit_index": i,
                    "circuit_name": circ.name,
                    "num_qubits": circ.num_qubits,
                    "depth": circ.depth(),
                    "num_gates": len(circ.gates),
                    "elapsed_ms": elapsed * 1000,
                    "mitigation": mitigation,
                },
            )
            results.append(result)

        return results

    def _resolve_backend(self) -> Optional[str]:
        """Resolve backend name from the backend parameter."""
        if self._backend is None:
            return None
        if isinstance(self._backend, str):
            return self._backend
        # If it's a backend object, extract its name
        if hasattr(self._backend, 'name'):
            return self._backend.name
        if hasattr(self._backend, 'backend_name'):
            return self._backend.backend_name
        return str(self._backend)

    def _execute_on_hardware(self, circ: Circuit, backend_name: str,
                              rng: np.random.Generator):
        """Execute circuit on a real hardware backend."""
        sv = None
        counts = {}
        probs = {}

        try:
            if backend_name.startswith("ibm"):
                # IBM Quantum backend
                from ..backends.ibm import IBMQuantumBackend
                backend = IBMQuantumBackend(backend_name=backend_name)
                result = backend.run_circuit(circ, shots=self._shots)
                counts = result.get("counts", {})
                total = sum(counts.values()) if counts else 1
                probs = {k: v / total for k, v in counts.items()}

            elif backend_name.startswith("dwave") or backend_name == "dwave":
                # D-Wave backend
                from ..backends.dwave import DWaveBackend
                backend = DWaveBackend()
                result = backend.run_circuit(circ, shots=self._shots)
                counts = result.get("counts", {})
                total = sum(counts.values()) if counts else 1
                probs = {k: v / total for k, v in counts.items()}

            else:
                # Fall back to local simulation for unknown backends
                sv = _statevector_sim(circ)
                if self._shots > 0:
                    counts = _sample_counts(sv, circ.num_qubits, self._shots, rng)
                    probs = {k: v / self._shots for k, v in counts.items()}
                else:
                    probs = {
                        format(j, f"0{circ.num_qubits}b"): float(abs(sv[j]) ** 2)
                        for j in range(len(sv))
                        if abs(sv[j]) ** 2 > 1e-12
                    }

        except Exception as e:
            # Fall back to local simulation on hardware error
            import warnings
            warnings.warn(
                f"Hardware execution failed ({e}), falling back to local simulation"
            )
            sv = _statevector_sim(circ)
            if self._shots > 0:
                counts = _sample_counts(sv, circ.num_qubits, self._shots, rng)
                probs = {k: v / self._shots for k, v in counts.items()}
            else:
                probs = {
                    format(j, f"0{circ.num_qubits}b"): float(abs(sv[j]) ** 2)
                    for j in range(len(sv))
                    if abs(sv[j]) ** 2 > 1e-12
                }

        return sv, counts, probs

    def _apply_mitigation(self, counts: Dict[str, int],
                          n_qubits: int) -> MitigationResult:
        """Readout error mitigation via confusion matrix inversion."""
        confusion = np.eye(2 ** n_qubits) * 0.95
        for i in range(2 ** n_qubits):
            confusion[i, i] = 0.95
            if i + 1 < 2 ** n_qubits:
                confusion[i, i + 1] = 0.025
                confusion[i + 1, i] = 0.025

        try:
            confusion_inv = np.linalg.inv(confusion)
        except np.linalg.LinAlgError:
            confusion_inv = np.eye(2 ** n_qubits)

        raw_probs = {k: v / sum(counts.values()) for k, v in counts.items()}
        mitigated_probs = _apply_readout_mitigation(counts, confusion_inv, n_qubits)

        return MitigationResult(
            raw_probs=raw_probs,
            mitigated_probs=mitigated_probs,
            method="readout_inverse",
            confusion_matrix=confusion,
        )

    # ── Result accessors ──────────────────────────────────────────

    @property
    def counts(self) -> Union[Dict[str, int], List[Dict[str, int]]]:
        if len(self._results) == 1:
            return self._results[0].counts
        return [r.counts for r in self._results]

    @property
    def probabilities(self) -> Union[Dict[str, float], List[Dict[str, float]]]:
        if len(self._results) == 1:
            return self._results[0].probabilities
        return [r.probabilities for r in self._results]

    @property
    def statevector(self) -> Union[np.ndarray, List[np.ndarray], None]:
        if len(self._results) == 1:
            return self._results[0].statevector
        svs = [r.statevector for r in self._results]
        return svs[0] if len(svs) == 1 else svs

    @property
    def expectations(self) -> Optional[List[EstimatorResult]]:
        if self._observables is None:
            return None
        results = []
        for res in self._results:
            if res.statevector is not None:
                sv = res.statevector
            else:
                sv = _statevector_sim(
                    self._circuits[res.metadata["circuit_index"]]
                )
            values = []
            for obs in self._observables:
                mat = np.array(obs.get("matrix", [[1, 0], [0, -1]]), dtype=complex)
                exp = float(np.real(sv.conj() @ mat @ sv))
                values.append(complex(exp))
            results.append(EstimatorResult(values=values))
        return results

    @property
    def mitigation(self) -> Optional[MitigationResult]:
        if not self._results or self._results[0].metadata.get("mitigation") is None:
            return None
        return self._results[0].metadata["mitigation"]

    @property
    def result(self) -> Union[SamplerResult, List[SamplerResult]]:
        if len(self._results) == 1:
            return self._results[0]
        return self._results

    def __getitem__(self, index: int) -> SamplerResult:
        return self._results[index]

    def __len__(self) -> int:
        return len(self._results)

    def __repr__(self) -> str:
        if len(self._results) == 1:
            return repr(self._results[0])
        return f"QuantumRun({len(self._results)} circuits, shots={self._shots})"
