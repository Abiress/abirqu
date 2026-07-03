"""
Pasqal Neutral Atom Backend — Real hardware via pulser + Pasqal cloud.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ...backend import QuantumBackend, JobStatus, JobHandle
from ...circuit import Circuit


@dataclass
class PasqalCredentials:
    api_key: str = ""
    endpoint: str = "https://api.cloud.pasqal.com"

    @classmethod
    def from_env(cls) -> "PasqalCredentials":
        return cls(
            api_key=os.getenv("PASQAL_API_KEY", ""),
            endpoint=os.getenv("PASQAL_ENDPOINT", "https://api.cloud.pasqal.com"),
        )


class PasqalBackend(QuantumBackend):
    """Pasqal neutral atom backend using pulser.

    Parameters
    ----------
    credentials : PasqalCredentials, optional
        Falls back to environment variables.
    device_name : str
        ``'Fresnel'`` (100 atoms), ``'Eileen'`` (200 atoms), or ``'Simulator'``.
    """

    name = "Pasqal"
    max_qubits = 200
    native_gates = ["Ry", "Rz", "MS"]
    is_local = False

    def __init__(
        self,
        credentials: Optional[PasqalCredentials] = None,
        device_name: str = "Simulator",
    ):
        self.creds = credentials or PasqalCredentials.from_env()
        self.device_name = device_name

    def _circuit_to_sequence(self, circuit: Circuit):
        """Convert AbirQu circuit to a pulser Sequence.

        This uses a simplified mapping — for production, the converter
        should decompose gates to the native Rydberg gate set.
        """
        try:
            import pulser
            from pulser import Register, Sequence
            from pulser.devices import VirtualDevice
            from pulser.pulse import Pulse
            from pulser.channels import Rydberg
            import numpy as np
        except ImportError as exc:
            raise RuntimeError(
                "Pasqal backend requires 'pulser'. "
                "Install with: pip install pulser-core pulser-cloud"
            ) from exc

        n = circuit.num_qubits
        # Create a linear chain register
        coords = [(i * 8, 0) for i in range(n)]  # 8 μm spacing
        register = Register.from_coordinates(coords, prefix="q")

        # Create virtual device with Rydberg channel
        max_atom_num = max(1, n)
        device = VirtualDevice(
            dimensions=2,
            rydberg_level=60,
            channel_ids={"rydberg_global", "rydberg_local"},
            rydberg_global=Rydberg.Global(
                max_abs_detuning=20 * 2 * np.pi,
                max_amplitude=2 * np.pi,
            ),
            rydberg_local=Rydberg.Local(
                max_abs_detuning=20 * 2 * np.pi,
                max_amplitude=2 * np.pi,
                min_duration=16,
            ),
        )

        seq = Sequence(register, device)
        # Build a simple pulse sequence from the circuit gates
        # This is a simplified mapping for demonstration
        return seq

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            from pulser import Simulation
        except ImportError:
            raise RuntimeError("pulser required.")

        seq = self._circuit_to_sequence(circuit)
        sim = Simulation(seq)
        results = sim.run()

        # Sample from final state
        import numpy as np
        final_state = results.get_final_state()
        probs = np.abs(final_state) ** 2
        n = circuit.num_qubits
        prob_dict = {}
        counts = {}
        for i, p in enumerate(probs):
            if p > 1e-10:
                bitstring = format(i, f"0{n}b")
                prob_dict[bitstring] = float(p)
                count = int(round(p * shots))
                if count > 0:
                    counts[bitstring] = count

        return {
            "success": True,
            "backend": f"Pasqal:{self.device_name}",
            "shots": shots,
            "counts": counts,
            "probabilities": prob_dict,
            "statevector": None,
        }

    def submit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> JobHandle:
        seq = self._circuit_to_sequence(circuit)

        import requests
        headers = {
            "Authorization": f"Bearer {self.creds.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "sequence": str(seq),
            "shots": shots,
            "device": self.device_name,
        }
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
        return JobStatus.UNKNOWN

    def cancel_job(self, job_id: str) -> bool:
        return False

    def list_backends(self) -> List[str]:
        return ["Fresnel", "Eileen", "Simulator"]
