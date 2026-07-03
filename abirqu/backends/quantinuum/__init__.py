"""
Quantinuum H-Series Backend — Real hardware via pytket + pytket-quantinuum.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...backend import QuantumBackend, JobStatus, JobHandle
from ...circuit import Circuit


@dataclass
class QuantinuumCredentials:
    api_key: str = ""
    issuer: str = "quantinuum"
    client_id: str = ""

    @classmethod
    def from_env(cls) -> "QuantinuumCredentials":
        return cls(
            api_key=os.getenv("QUANTINUUM_API_KEY", ""),
            issuer=os.getenv("QUANTINUUM_ISSUER", "quantinuum"),
            client_id=os.getenv("QUANTINUUM_CLIENT_ID", ""),
        )

    def validate(self) -> bool:
        return bool(self.api_key)


class QuantinuumBackend(QuantumBackend):
    """Quantinuum H-Series backend using pytket.

    Parameters
    ----------
    credentials : QuantinuumCredentials, optional
        Falls back to environment variables.
    device_name : str
        H-Series device, e.g. ``'H1-1'`` or ``'H2-1'``.
    """

    name = "Quantinuum"
    max_qubits = 56
    native_gates = ["Rz", "Ry", "MS", "ZZ"]
    is_local = False

    def __init__(
        self,
        credentials: Optional[QuantinuumCredentials] = None,
        device_name: str = "H1-1SC",
    ):
        self.creds = credentials or QuantinuumCredentials.from_env()
        self.device_name = device_name

    def _circuit_to_pytket(self, circuit: Circuit):
        from ...converters import to_pytket
        return to_pytket(circuit)

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            from pytket.extensions.quantinuum import QuantinuumAPI
        except ImportError as exc:
            raise RuntimeError(
                "Quantinuum backend requires 'pytket' and 'pytket-quantinuum'. "
                "Install with: pip install pytket pytket-quantinuum"
            ) from exc

        api = QuantinuumAPI(token=self.creds.api_key)
        tk_circuit = self._circuit_to_pytket(circuit)

        result_handler = api.process_circuit(
            tk_circuit,
            shots=shots,
            name="abirqu-job",
            target=self.device_name,
        )
        status = result_handler.status()

        # Poll until done
        while status not in ("completed", "failed", "error"):
            import time
            time.sleep(2)
            status = result_handler.status()

        if status != "completed":
            raise RuntimeError(f"Quantinuum job ended with status: {status}")

        counts = result_handler.get_counts()
        total = sum(counts.values())
        probs = {k: v / total for k, v in counts.items()}

        return {
            "success": True,
            "backend": f"Quantinuum:{self.device_name}",
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
        try:
            from pytket.extensions.quantinuum import QuantinuumAPI
        except ImportError as exc:
            raise RuntimeError("pytket-quantinuum required.") from exc

        api = QuantinuumAPI(token=self.creds.api_key)
        tk_circuit = self._circuit_to_pytket(circuit)

        result_handler = api.process_circuit(
            tk_circuit,
            shots=shots,
            name="abirqu-job",
            target=self.device_name,
        )

        return JobHandle(
            job_id=str(id(result_handler)),
            backend=self,
            status=JobStatus.RUNNING,
        )

    def query_job(self, job_id: str) -> JobStatus:
        return JobStatus.UNKNOWN

    def cancel_job(self, job_id: str) -> bool:
        return False

    def list_backends(self) -> List[str]:
        return ["H1-1", "H1-1SC", "H1-2", "H2-1", "H2-1SC"]
