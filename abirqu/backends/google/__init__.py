"""
Google Quantum Backend — Real hardware via cirq / cirq-google.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...backend import QuantumBackend, JobStatus, JobHandle
from ...circuit import Circuit


@dataclass
class GoogleQuantumCredentials:
    project_id: str
    access_token: str = ""

    @classmethod
    def from_env(cls) -> "GoogleQuantumCredentials":
        return cls(
            project_id=os.getenv("GOOGLE_PROJECT_ID", ""),
            access_token=os.getenv("GOOGLE_ACCESS_TOKEN", ""),
        )


class GoogleQuantumBackend(QuantumBackend):
    """Google Quantum backend using Cirq.

    Parameters
    ----------
    credentials : GoogleQuantumCredentials, optional
        Required for real hardware. Falls back to env vars.
    processor_id : str, optional
        Google QCS processor ID.  ``None`` uses the Cirq simulator.
    """

    name = "Google-Quantum"
    max_qubits = 72
    native_gates = ["PhasedXPow", "XPow", "YPow", "CZ", "FSim"]
    is_local = False

    def __init__(
        self,
        credentials: Optional[GoogleQuantumCredentials] = None,
        processor_id: Optional[str] = None,
        use_gpu: bool = False,
    ):
        self.creds = credentials or GoogleQuantumCredentials.from_env()
        self.processor_id = processor_id
        self.use_gpu = use_gpu

    def _circuit_to_cirq(self, circuit: Circuit):
        from ...converters import to_cirq
        return to_cirq(circuit, add_measurement=True)

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            import cirq
        except ImportError as exc:
            raise RuntimeError(
                "Google backend requires 'cirq'. Install with: pip install cirq"
            ) from exc

        cq, _ = self._circuit_to_cirq(circuit)

        if self.processor_id:
            try:
                import cirq_google
                engine = cirq_google.Engine(project_id=self.creds.project_id)
                sampler = engine.get_sampler(processor_id=self.processor_id)
            except ImportError as exc:
                raise RuntimeError("Real hardware requires 'cirq-google'.") from exc
        else:
            if self.use_gpu:
                try:
                    sampler = cirq.CuStateVecSimulator()
                except AttributeError:
                    sampler = cirq.Simulator()
            else:
                sampler = cirq.Simulator()

        result = sampler.run(cq, repetitions=shots)
        measurements = result.measurements["result"]

        counts: Dict[str, int] = {}
        for row in measurements:
            key = "".join(str(b) for b in row)
            counts[key] = counts.get(key, 0) + 1

        probs = self._counts_to_probs(counts, shots)
        return {
            "success": True,
            "backend": f"Cirq:{self.processor_id or 'simulator'}",
            "shots": shots,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }

    def list_backends(self) -> List[str]:
        if self.processor_id:
            try:
                import cirq_google
                engine = cirq_google.Engine(project_id=self.creds.project_id)
                processors = engine.get_processors()
                return [p.processor_id for p in processors]
            except Exception:
                return [self.processor_id]
        return ["simulator", "simulator_gpu"]

    def cancel_job(self, job_id: str) -> bool:
        return False
