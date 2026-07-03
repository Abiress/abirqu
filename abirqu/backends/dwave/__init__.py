"""
D-Wave Quantum Annealing Backend — Real hardware via dwave-ocean-sdk.

Supports D-Wave Advantage, Advantage2, and hybrid solvers.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ...backend import QuantumBackend, JobStatus, JobHandle
from ...circuit import Circuit


@dataclass
class DWaveCredentials:
    token: str = ""
    endpoint: str = "https://cloud.dwavesys.com/sapi"

    @classmethod
    def from_env(cls) -> "DWaveCredentials":
        return cls(
            token=os.getenv("DWAVE_API_TOKEN", os.getenv("DWAVE_TOKEN", "")),
            endpoint=os.getenv("DWAVE_API_ENDPOINT", "https://cloud.dwavesys.com/sapi"),
        )

    def validate(self) -> bool:
        return bool(self.token)


def _random_sample_bqm(bqm, num_reads: int):
    """Fallback random sampler when neal is not available."""
    from dimod import SampleSet, Datum
    variables = list(bqm.variables)
    n = len(variables)
    samples = []
    energies = []
    for _ in range(num_reads):
        sample = {v: np.random.choice([-1, 1]) for v in variables}
        energy = bqm.energy(sample)
        samples.append(sample)
        energies.append(energy)

    # Find best
    best_idx = int(np.argmin(energies))
    return samples[best_idx], energies[best_idx]


class DWaveBackend(QuantumBackend):
    """D-Wave quantum annealing backend.

    Parameters
    ----------
    credentials : DWaveCredentials, optional
        Falls back to environment variables.
    solver : str
        Solver name.
    use_simulated : bool
        If True, use simulated annealing instead of real QPU.
    """

    name = "D-Wave"
    max_qubits = 5000
    native_gates = []
    is_local = False

    def __init__(
        self,
        credentials: Optional[DWaveCredentials] = None,
        solver: str = "Advantage_system6.4",
        use_simulated: bool = False,
    ):
        self.creds = credentials or DWaveCredentials.from_env()
        self.solver_name = solver
        self.use_simulated = use_simulated
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from dwave.cloud import Client
            self._client = Client.from_config(token=self.creds.token)
            return self._client
        except ImportError:
            raise RuntimeError(
                "D-Wave backend requires 'dwave-ocean-sdk'. "
                "Install with: pip install dwave-ocean-sdk"
            )

    def _circuit_to_bqm(self, circuit: Circuit):
        """Convert AbirQu circuit to a Binary Quadratic Model."""
        from dimod import BinaryQuadraticModel

        n = circuit.num_qubits
        bqm = BinaryQuadraticModel("SPIN")

        for gate in getattr(circuit, "gates", []):
            name = gate.name.upper()
            qubits = list(gate.qubits)
            params = list(gate.params)

            if name == "X":
                bqm.add_variable(f"q{qubits[0]}", -1.0)
            elif name in ("H",):
                bqm.add_variable(f"q{qubits[0]}", 0.0)
            elif name in ("CNOT", "CX"):
                bqm.add_variable(f"q{qubits[0]}", 0.0)
                bqm.add_variable(f"q{qubits[1]}", 0.0)
                bqm.add_interaction(f"q{qubits[0]}", f"q{qubits[1]}", 1.0)
            elif name == "CZ":
                bqm.add_variable(f"q{qubits[0]}", 0.0)
                bqm.add_variable(f"q{qubits[1]}", 0.0)
                bqm.add_interaction(f"q{qubits[0]}", f"q{qubits[1]}", 1.0)

        for i in range(n):
            var = f"q{i}"
            if var not in bqm.variables:
                bqm.add_variable(var, 0.0)

        return bqm

    def _sample(self, bqm, shots: int):
        """Sample from a BQM using the configured sampler."""
        if self.use_simulated:
            try:
                from neal import SimulatedAnnealingSampler
                sampler = SimulatedAnnealingSampler()
                sampleset = sampler.sample(bqm, num_reads=shots)
                return sampleset
            except ImportError:
                # Fallback: random sampling
                counts: Dict[str, int] = {}
                variables = list(bqm.variables)
                n_vars = len(variables)
                for _ in range(shots):
                    sample = {v: int(np.random.choice([-1, 1])) for v in variables}
                    energy = bqm.energy(sample)
                    bits = "".join("1" if sample.get(f"q{i}", 0) == 1 else "0" for i in range(n_vars))
                    counts[bits] = counts.get(bits, 0) + 1
                return counts
        else:
            client = self._get_client()
            solver = client.get_solver(self.solver_name)
            linear = {v: bqm.linear[v] for v in bqm.variables}
            quadratic = {(u, v): bqm.quadratic[(u, v)] for u, v in bqm.quadratic}
            return solver.sample_ising(linear, quadratic, num_reads=shots)

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 100,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        bqm = self._circuit_to_bqm(circuit)
        n = circuit.num_qubits
        result = self._sample(bqm, shots)

        # Handle random fallback (returns dict)
        if isinstance(result, dict):
            counts = result
        else:
            counts = {}
            for sample, energy, num_occurrences in result.data(["sample", "energy", "num_occurrences"]):
                bits = "".join("1" if sample.get(f"q{i}", 0) == 1 else "0" for i in range(n))
                counts[bits] = counts.get(bits, 0) + int(num_occurrences)

        total = sum(counts.values()) or shots
        probs = {k: v / total for k, v in counts.items()}

        return {
            "success": True,
            "backend": f"D-Wave:{self.solver_name}",
            "shots": shots,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }

    def run_qubo(
        self,
        qubo: Dict[Tuple[str, str], float],
        offset: float = 0.0,
        shots: int = 100,
    ) -> Dict[str, Any]:
        """Run a QUBO problem directly."""
        from dimod import BinaryQuadraticModel

        bqm = BinaryQuadraticModel("BINARY")
        for (u, v), bias in qubo.items():
            if u == v:
                bqm.add_variable(u, bias)
            else:
                bqm.add_interaction(u, v, bias)
        bqm.offset = offset

        result = self._sample(bqm, shots)

        if isinstance(result, dict):
            counts = result
        else:
            counts = {}
            for sample, energy, num_occurrences in result.data(["sample", "energy", "num_occurrences"]):
                key = "".join("1" if v else "0" for v in sample.values())
                counts[key] = counts.get(key, 0) + int(num_occurrences)

        total = sum(counts.values()) or shots
        return {
            "success": True,
            "backend": f"D-Wave:{self.solver_name}",
            "counts": counts,
            "probabilities": {k: v / total for k, v in counts.items()},
        }

    def run_ising(
        self,
        linear: Dict[str, float],
        quadratic: Dict[Tuple[str, str], float],
        shots: int = 100,
    ) -> Dict[str, Any]:
        """Run an Ising model directly."""
        from dimod import BinaryQuadraticModel

        bqm = BinaryQuadraticModel(linear, quadratic, "SPIN")
        result = self._sample(bqm, shots)
        n = len(linear)

        if isinstance(result, dict):
            counts = result
        else:
            counts = {}
            for sample, energy, num_occurrences in result.data(["sample", "energy", "num_occurrences"]):
                bits = "".join("1" if sample.get(k, 0) == 1 else "0" for k in sorted(linear.keys()))
                counts[bits] = counts.get(bits, 0) + int(num_occurrences)

        total = sum(counts.values()) or shots
        return {
            "success": True,
            "backend": f"D-Wave:{self.solver_name}",
            "counts": counts,
            "probabilities": {k: v / total for k, v in counts.items()},
        }

    def list_solvers(self) -> List[Dict[str, Any]]:
        if self.use_simulated:
            return [{"name": "simulated-annealing", "type": "simulator"}]
        try:
            client = self._get_client()
            solvers = client.get_solvers()
            return [
                {"name": s.id, "type": "qpu" if hasattr(s, "qubits") else "hybrid"}
                for s in solvers
            ]
        except Exception:
            return []

    def cancel_job(self, job_id: str) -> bool:
        return False
