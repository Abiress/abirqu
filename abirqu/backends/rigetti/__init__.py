"""
Rigetti / QCS Backend — Real hardware via pyquil + QCS REST API.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...backend import QuantumBackend, JobStatus, JobHandle
from ...circuit import Circuit


@dataclass
class RigettiCredentials:
    api_key: str = ""
    endpoint: str = "https://qcs.rigetti.com"

    @classmethod
    def from_env(cls) -> "RigettiCredentials":
        return cls(
            api_key=os.getenv("RIGETTI_API_KEY", os.getenv("QCS_API_KEY", "")),
            endpoint=os.getenv("RIGETTI_ENDPOINT", "https://qcs.rigetti.com"),
        )


class RigettiBackend(QuantumBackend):
    """Rigetti / QCS backend using pyquil.

    Parameters
    ----------
    credentials : RigettiCredentials, optional
        Falls back to environment variables.
    device_name : str
        QPU or QVM name, e.g. ``'Aspen-M-3'`` or ``'QVM'``.
    """

    name = "Rigetti-QCS"
    max_qubits = 80
    native_gates = ["RZ", "RX", "ISWAP", "CZ"]
    is_local = False

    def __init__(
        self,
        credentials: Optional[RigettiCredentials] = None,
        device_name: str = "QVM",
    ):
        self.creds = credentials or RigettiCredentials.from_env()
        self.device_name = device_name

    def _circuit_to_quil(self, circuit: Circuit) -> str:
        from ...converters import to_quil
        return to_quil(circuit)

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        quil = self._circuit_to_quil(circuit)

        # Try pyquil first
        try:
            import pyquil
            from pyquil import Program, get_qc
            from pyquil.gates import MEASURE
            from pyquil.quilbase import Declare

            prog = Program()
            ro = prog.declare("ro", "BIT", circuit.num_qubits)
            for line in quil.split("\n"):
                line = line.strip()
                if not line or line.startswith("DECLARE") or line.startswith("MEASURE"):
                    continue
                # Parse and add gates
                if line.startswith("H "):
                    q = int(line.split()[1])
                    prog += pyquil.gates.H(q)
                elif line.startswith("CNOT "):
                    parts = line.split()
                    prog += pyquil.gates.CNOT(int(parts[1]), int(parts[2]))
                elif line.startswith("X "):
                    q = int(line.split()[1])
                    prog += pyquil.gates.X(q)
                elif line.startswith("Y "):
                    q = int(line.split()[1])
                    prog += pyquil.gates.Y(q)
                elif line.startswith("Z "):
                    q = int(line.split()[1])
                    prog += pyquil.gates.Z(q)
                elif line.startswith("CZ "):
                    parts = line.split()
                    prog += pyquil.gates.CZ(int(parts[1]), int(parts[2]))
                elif line.startswith("SWAP "):
                    parts = line.split()
                    prog += pyquil.gates.SWAP(int(parts[1]), int(parts[2]))

            for i in range(circuit.num_qubits):
                prog += MEASURE(i, ro[i])

            qc = get_qc(self.device_name)
            executable = qc.compile(prog)
            results = qc.run(executable)
            bitstrings = results.readout_data.get("ro")
            counts: Dict[str, int] = {}
            for row in bitstrings:
                key = "".join(str(b) for b in row)
                counts[key] = counts.get(key, 0) + 1
            total = sum(counts.values())
            probs = {k: v / total for k, v in counts.items()}
            return {
                "success": True,
                "backend": f"Rigetti:{self.device_name}",
                "shots": shots,
                "counts": counts,
                "probabilities": probs,
                "statevector": None,
            }
        except ImportError:
            pass

        # Fallback: REST API submission to QCS
        import requests
        headers = {"X-API-Key": self.creds.api_key, "Content-Type": "application/json"}
        payload = {"quil": quil, "shots": shots, "target": self.device_name}
        resp = requests.post(
            f"{self.creds.endpoint}/v1/jobs",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        counts = data.get("result", {}).get("counts", {})
        total = sum(counts.values()) or shots
        probs = {k: v / total for k, v in counts.items()}
        return {
            "success": True,
            "backend": f"Rigetti:{self.device_name}",
            "shots": shots,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }

    def submit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> JobHandle:
        quil = self._circuit_to_quil(circuit)
        import requests
        headers = {"X-API-Key": self.creds.api_key, "Content-Type": "application/json"}
        payload = {"quil": quil, "shots": shots, "target": self.device_name}
        resp = requests.post(
            f"{self.creds.endpoint}/v1/jobs",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return JobHandle(
            job_id=data.get("job_id", data.get("id", "")),
            backend=self,
            status=JobStatus.QUEUED,
        )

    def query_job(self, job_id: str) -> JobStatus:
        import requests
        headers = {"X-API-Key": self.creds.api_key}
        try:
            resp = requests.get(
                f"{self.creds.endpoint}/v1/jobs/{job_id}",
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            status_map = {
                "queued": JobStatus.QUEUED,
                "running": JobStatus.RUNNING,
                "completed": JobStatus.COMPLETED,
                "failed": JobStatus.FAILED,
            }
            return status_map.get(data.get("status", ""), JobStatus.UNKNOWN)
        except Exception:
            return JobStatus.UNKNOWN

    def cancel_job(self, job_id: str) -> bool:
        return False

    def list_backends(self) -> List[str]:
        return ["Aspen-M-3", "Ankaa-3", "QVM"]
