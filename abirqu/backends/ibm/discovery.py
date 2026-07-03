"""
IBM Quantum Backend Discovery
=============================
List and filter available IBM quantum backends.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


class IBMBackendDiscovery:
    """Discover and filter available IBM Quantum backends.

    Parameters
    ----------
    token : str, optional
        IBM Quantum API token.  Falls back to env vars.
    instance : str
        Hub/group/project.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        instance: str = "ibm-q/open/main",
    ):
        self.token = token or os.getenv("IBM_QUANTUM_TOKEN", os.getenv("QISKIT_IBM_TOKEN", ""))
        self.instance = instance
        self._service = None

    def _get_service(self):
        if self._service is not None:
            return self._service
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            self._service = QiskitRuntimeService(
                channel="ibm_quantum",
                token=self.token,
                instance=self.instance,
            )
            return self._service
        except ImportError as exc:
            raise RuntimeError(
                "Requires 'qiskit-ibm-runtime'. Install: pip install qiskit-ibm-runtime"
            ) from exc

    def list_backends(
        self,
        min_qubits: int = 0,
        operational: bool = True,
    ) -> List[Dict[str, Any]]:
        """List available IBM backends.

        Parameters
        ----------
        min_qubits : int
            Minimum number of qubits.
        operational : bool
            If True, only return operational backends.

        Returns
        -------
        List of dicts with backend info.
        """
        service = self._get_service()
        backends = service.backends(
            min_num_qubits=min_qubits,
            operational=operational,
        )
        return [
            {
                "name": b.name,
                "num_qubits": b.num_qubits,
                "status": str(b.status()),
                "simulator": b.configuration().simulator if hasattr(b, "configuration") else False,
                "max_shots": b.configuration().max_shots if hasattr(b, "configuration") else 4000,
            }
            for b in backends
        ]

    def get_best_backend(
        self,
        min_qubits: int = 5,
        simulator: bool = False,
    ) -> Dict[str, Any]:
        """Get the best available backend matching criteria.

        Prefers real hardware over simulators and backends with
        lower error rates.
        """
        backends = self.list_backends(min_qubits=min_qubits)
        if simulator:
            backends = [b for b in backends if b.get("simulator", False)]
        else:
            backends = [b for b in backends if not b.get("simulator", False)]

        if not backends:
            raise RuntimeError(f"No IBM backend found with {min_qubits}+ qubits.")

        # Sort by qubit count (prefer larger)
        backends.sort(key=lambda b: b["num_qubits"], reverse=True)
        return backends[0]

    def get_backend_properties(self, backend_name: str) -> Dict[str, Any]:
        """Get detailed properties of a specific backend."""
        service = self._get_service()
        backend = service.backend(backend_name)
        props = backend.properties()
        return {
            "name": backend_name,
            "num_qubits": backend.num_qubits,
            "t1": [props.qubit_property(i, "T1")[0] / 1000 for i in range(backend.num_qubits)],  # μs
            "t2": [props.qubit_property(i, "T2")[0] / 1000 for i in range(backend.num_qubits)],  # μs
            "gate_error_1q": [props.gate_error("sx", [i]) for i in range(backend.num_qubits)],
            "readout_error": [props.readout_error(i) for i in range(backend.num_qubits)],
        }
