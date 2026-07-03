"""
IBM Quantum Backend — Real hardware via qiskit-ibm-runtime.

Connects to IBM Quantum services, transpiles AbirQu circuits to IBM native
gates, and submits jobs via the SamplerV2 primitive.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...backend import QuantumBackend, JobStatus, JobHandle
from ...circuit import Circuit


# ──────────────────────────────────────────────────────────────────────────────
# Credentials
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class IBMQuantumCredentials:
    """IBM Quantum credentials."""
    api_token: str
    instance: str = "ibm-q/open/main"

    @classmethod
    def from_env(cls) -> "IBMQuantumCredentials":
        return cls(
            api_token=os.getenv("IBM_QUANTUM_TOKEN", os.getenv("QISKIT_IBM_TOKEN", "")),
            instance=os.getenv("IBM_QUANTUM_INSTANCE", "ibm-q/open/main"),
        )

    def validate(self) -> bool:
        return len(self.api_token) > 0


# ──────────────────────────────────────────────────────────────────────────────
# Backend
# ──────────────────────────────────────────────────────────────────────────────

class IBMQuantumBackend(QuantumBackend):
    """IBM Quantum backend using qiskit-ibm-runtime SamplerV2.

    Parameters
    ----------
    credentials : IBMQuantumCredentials, optional
        Credentials object.  Falls back to environment variables.
    backend_name : str
        IBM device name, e.g. ``'ibm_brisbane'`` or ``'ibmq_qasm_simulator'``.
    """

    name = "IBM-Quantum"
    max_qubits = 127
    native_gates = ["ECR", "ID", "RZ", "X", "SX"]
    supports_noise_model = True
    is_local = False

    def __init__(
        self,
        credentials: Optional[IBMQuantumCredentials] = None,
        backend_name: str = "ibmq_qasm_simulator",
    ):
        self.creds = credentials or IBMQuantumCredentials.from_env()
        self.backend_name = backend_name
        self._service = None
        self._backend = None

    # ── Connection ────────────────────────────────────────────────────────

    def _connect(self):
        if self._service is not None:
            return
        if not self.creds.validate():
            raise ValueError(
                "IBM Quantum API token required. Set IBM_QUANTUM_TOKEN or "
                "QISKIT_IBM_TOKEN environment variable."
            )
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            QiskitRuntimeService.save_account(
                channel="ibm_quantum",
                token=self.creds.api_token,
                instance=self.creds.instance,
                overwrite=True,
            )
            self._service = QiskitRuntimeService(
                channel="ibm_quantum",
                instance=self.creds.instance,
            )
            self._backend = self._service.backend(self.backend_name)
        except ImportError as exc:
            raise RuntimeError(
                "IBM backend requires 'qiskit-ibm-runtime'. "
                "Install with: pip install qiskit qiskit-ibm-runtime"
            ) from exc

    # ── Conversion ────────────────────────────────────────────────────────

    def _circuit_to_qiskit(self, circuit: Circuit):
        """Convert AbirQu Circuit to a Qiskit QuantumCircuit."""
        from ...converters import to_qiskit
        qc = to_qiskit(circuit)
        return qc

    # ── Synchronous execution ─────────────────────────────────────────────

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        self._connect()
        from qiskit import transpile
        from qiskit_ibm_runtime import SamplerV2 as Sampler

        qc = self._circuit_to_qiskit(circuit)
        tqc = transpile(qc, self._backend)
        sampler = Sampler(mode=self._backend)
        job = sampler.run([tqc], shots=shots)
        pub_result = job.result()[0]
        raw_counts = pub_result.data.meas.get_counts()
        total = sum(raw_counts.values())
        probs = {k: v / total for k, v in raw_counts.items()}

        return {
            "success": True,
            "backend": f"IBM:{self.backend_name}",
            "shots": shots,
            "counts": dict(raw_counts),
            "probabilities": probs,
            "statevector": None,
        }

    # ── Asynchronous execution ────────────────────────────────────────────

    def submit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> JobHandle:
        self._connect()
        from qiskit import transpile
        from qiskit_ibm_runtime import SamplerV2 as Sampler

        qc = self._circuit_to_qiskit(circuit)
        tqc = transpile(qc, self._backend)
        sampler = Sampler(mode=self._backend)
        job = sampler.run([tqc], shots=shots)

        handle = JobHandle(
            job_id=job.job_id(),
            backend=self,
            status=JobStatus.RUNNING,
        )
        handle._ibm_job = job  # store reference
        return handle

    def query_job(self, job_id: str) -> JobStatus:
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            if self._service is None:
                self._connect()
            job = self._service.job(job_id)
            status = job.status()
            status_map = {
                "QUEUED": JobStatus.QUEUED,
                "RUNNING": JobStatus.RUNNING,
                "DONE": JobStatus.COMPLETED,
                "ERROR": JobStatus.FAILED,
                "CANCELLED": JobStatus.CANCELED,
                "CANCELED": JobStatus.CANCELED,
            }
            return status_map.get(str(status), JobStatus.UNKNOWN)
        except Exception:
            return JobStatus.UNKNOWN

    def fetch_result(self, job_id: str) -> Dict[str, Any]:
        if self._service is None:
            self._connect()
        job = self._service.job(job_id)
        pub_result = job.result()[0]
        raw_counts = pub_result.data.meas.get_counts()
        total = sum(raw_counts.values())
        probs = {k: v / total for k, v in raw_counts.items()}
        return {
            "success": True,
            "backend": f"IBM:{self.backend_name}",
            "shots": total,
            "counts": dict(raw_counts),
            "probabilities": probs,
            "statevector": None,
        }

    def cancel_job(self, job_id: str) -> bool:
        try:
            if self._service is None:
                self._connect()
            job = self._service.job(job_id)
            job.cancel()
            return True
        except Exception:
            return False

    # ── Discovery ─────────────────────────────────────────────────────────

    def list_backends(self) -> List[Dict[str, Any]]:
        """List available IBM quantum backends."""
        self._connect()
        backends = self._service.backends()
        return [
            {
                "name": b.name,
                "num_qubits": b.num_qubits,
                "status": str(b.status()),
            }
            for b in backends
        ]


def create_ibm_backend(
    token: Optional[str] = None,
    backend_name: str = "ibmq_qasm_simulator",
) -> IBMQuantumBackend:
    """Create an IBM Quantum backend with optional token override."""
    creds = IBMQuantumCredentials(api_token=token or "") if token else IBMQuantumCredentials.from_env()
    return IBMQuantumBackend(credentials=creds, backend_name=backend_name)
