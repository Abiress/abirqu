"""
IonQ Backend — Real hardware via REST API.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...backend import QuantumBackend, JobStatus, JobHandle
from ...circuit import Circuit


@dataclass
class IonQCredentials:
    api_key: str
    endpoint: str = "https://api.ionq.co"

    @classmethod
    def from_env(cls) -> "IonQCredentials":
        return cls(
            api_key=os.getenv("IONQ_API_KEY", ""),
            endpoint=os.getenv("IONQ_ENDPOINT", "https://api.ionq.co"),
        )

    def validate(self) -> bool:
        return bool(self.api_key)


class IonQBackend(QuantumBackend):
    """IonQ REST API backend.

    Parameters
    ----------
    credentials : IonQCredentials, optional
        Falls back to environment variables.
    target : str
        ``'simulator'`` (default) or a real device like ``'qpu.aria-1'``.
    """

    name = "IonQ"
    max_qubits = 32
    native_gates = ["GPI", "GPI2", "MS"]
    is_local = False

    _BASE_URL = "https://api.ionq.co/v0.3"

    def __init__(
        self,
        credentials: Optional[IonQCredentials] = None,
        target: str = "simulator",
    ):
        self.creds = credentials or IonQCredentials.from_env()
        self.target = target
        self._session = None

    def _get_session(self):
        if self._session is not None:
            return self._session
        if not self.creds.validate():
            raise ValueError("IonQ API key required. Set IONQ_API_KEY environment variable.")
        import requests
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"apiKey {self.creds.api_key}",
            "Content-Type": "application/json",
        })
        return self._session

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        session = self._get_session()
        url = f"{self.creds.endpoint}{endpoint}"
        resp = session.request(method, url, timeout=kwargs.pop("timeout", 30), **kwargs)
        resp.raise_for_status()
        return resp.json()

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        from ...converters import to_ionq_json
        ionq_circuit = to_ionq_json(circuit)

        payload = {
            "target": self.target,
            "shots": shots,
            "input": {
                "format": "ionq.circuit.v0",
                "gateset": "native",
                "qubits": circuit.num_qubits,
                "circuit": ionq_circuit["circuit"],
            },
        }

        resp = self._request("POST", f"{self._BASE_URL}/jobs", json=payload)
        job_id = resp["id"]

        # Poll for completion
        while True:
            data = self._request("GET", f"{self._BASE_URL}/jobs/{job_id}")
            status = data.get("status", "")
            if status == "completed":
                break
            if status in ("failed", "canceled"):
                raise RuntimeError(f"IonQ job {job_id} ended with status={status}")
            time.sleep(2)

        raw_probs = data.get("data", {}).get("histogram", {})
        probs = {
            format(int(k), f"0{circuit.num_qubits}b"): v
            for k, v in raw_probs.items()
        }
        counts = {state: int(round(prob * shots)) for state, prob in probs.items() if prob > 0}

        return {
            "success": True,
            "backend": f"IonQ:{self.target}",
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
        from ...converters import to_ionq_json
        ionq_circuit = to_ionq_json(circuit)

        payload = {
            "target": self.target,
            "shots": shots,
            "input": {
                "format": "ionq.circuit.v0",
                "gateset": "native",
                "qubits": circuit.num_qubits,
                "circuit": ionq_circuit["circuit"],
            },
        }

        resp = self._request("POST", f"{self._BASE_URL}/jobs", json=payload)
        return JobHandle(
            job_id=resp["id"],
            backend=self,
            status=JobStatus.QUEUED,
        )

    def query_job(self, job_id: str) -> JobStatus:
        try:
            data = self._request("GET", f"{self._BASE_URL}/jobs/{job_id}")
            status_map = {
                "ready": JobStatus.QUEUED,
                "running": JobStatus.RUNNING,
                "completed": JobStatus.COMPLETED,
                "failed": JobStatus.FAILED,
                "canceled": JobStatus.CANCELED,
            }
            return status_map.get(data.get("status", ""), JobStatus.UNKNOWN)
        except Exception:
            return JobStatus.UNKNOWN

    def fetch_result(self, job_id: str) -> Dict[str, Any]:
        data = self._request("GET", f"{self._BASE_URL}/jobs/{job_id}")
        raw_probs = data.get("data", {}).get("histogram", {})
        n = data.get("qubits", 2)
        probs = {format(int(k), f"0{n}b"): v for k, v in raw_probs.items()}
        counts = {s: int(round(p * 1024)) for s, p in probs.items() if p > 0}
        return {
            "success": True,
            "backend": f"IonQ:{self.target}",
            "shots": 1024,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }

    def cancel_job(self, job_id: str) -> bool:
        try:
            self._request("DELETE", f"{self._BASE_URL}/jobs/{job_id}")
            return True
        except Exception:
            return False

    def list_backends(self) -> List[Dict[str, Any]]:
        try:
            data = self._request("GET", "/v0.3/backends")
            return data.get("backends", [])
        except Exception:
            return [
                {"name": "simulator", "status": "online"},
                {"name": "qpu.aria-1", "status": "online"},
                {"name": "qpu.aria-2", "status": "online"},
            ]
