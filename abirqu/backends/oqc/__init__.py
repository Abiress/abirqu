"""
OQC (Oxford Quantum Circuits) Backend — Real hardware via REST API.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...backend import QuantumBackend, JobStatus, JobHandle
from ...circuit import Circuit


@dataclass
class OQCCredentials:
    api_key: str = ""
    endpoint: str = "https://job-server.cloud.oqc.co"

    @classmethod
    def from_env(cls) -> "OQCCredentials":
        return cls(
            api_key=os.getenv("OQC_API_KEY", ""),
            endpoint=os.getenv("OQC_ENDPOINT", "https://job-server.cloud.oqc.co"),
        )


class OQCBackend(QuantumBackend):
    """OQC superconducting backend via REST API.

    Parameters
    ----------
    credentials : OQCCredentials, optional
        Falls back to environment variables.
    device_name : str
        ``'Lucy'`` (8-qubit), ``'Penny'`` (4-qubit), or ``'Simulator'``.
    """

    name = "OQC"
    max_qubits = 8
    native_gates = ["Rz", "SX", "CNOT"]
    is_local = False

    def __init__(
        self,
        credentials: Optional[OQCCredentials] = None,
        device_name: str = "Lucy",
    ):
        self.creds = credentials or OQCCredentials.from_env()
        self.device_name = device_name
        self._session = None

    def _get_session(self):
        if self._session is not None:
            return self._session
        import requests
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.creds.api_key}",
            "Content-Type": "application/json",
        })
        return self._session

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        session = self._get_session()
        url = f"{self.creds.endpoint}{endpoint}"
        resp = session.request(method, url, timeout=kwargs.pop("timeout", 30), **kwargs)
        resp.raise_for_status()
        return resp.json()

    def _circuit_to_qasm(self, circuit: Circuit) -> str:
        from ...converters import to_openqasm
        return to_openqasm(circuit)

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        qasm = self._circuit_to_qasm(circuit)

        payload = {
            "name": "abirqu-job",
            "shots": shots,
            "backend": self.device_name,
            "program": {"qasm": qasm},
        }
        resp = self._request("POST", "/jobs", json=payload)
        job_id = resp.get("job_id", resp.get("id"))

        # Poll for completion
        while True:
            result = self._request("GET", f"/jobs/{job_id}")
            status = result.get("status", "")
            if status == "COMPLETED":
                break
            if status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"OQC job {job_id} ended with status={status}")
            time.sleep(2)

        counts = result.get("result", {}).get("counts", {})
        total = sum(counts.values()) or shots
        probs = {k: v / total for k, v in counts.items()}

        return {
            "success": True,
            "backend": f"OQC:{self.device_name}",
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
        qasm = self._circuit_to_qasm(circuit)
        payload = {
            "name": "abirqu-job",
            "shots": shots,
            "backend": self.device_name,
            "program": {"qasm": qasm},
        }
        resp = self._request("POST", "/jobs", json=payload)
        return JobHandle(
            job_id=resp.get("job_id", resp.get("id", "")),
            backend=self,
            status=JobStatus.QUEUED,
        )

    def query_job(self, job_id: str) -> JobStatus:
        try:
            data = self._request("GET", f"/jobs/{job_id}")
            status_map = {
                "QUEUED": JobStatus.QUEUED,
                "RUNNING": JobStatus.RUNNING,
                "COMPLETED": JobStatus.COMPLETED,
                "FAILED": JobStatus.FAILED,
                "CANCELLED": JobStatus.CANCELED,
            }
            return status_map.get(data.get("status", ""), JobStatus.UNKNOWN)
        except Exception:
            return JobStatus.UNKNOWN

    def cancel_job(self, job_id: str) -> bool:
        try:
            self._request("DELETE", f"/jobs/{job_id}")
            return True
        except Exception:
            return False

    def list_backends(self) -> List[str]:
        return ["Lucy", "Penny", "Simulator"]
