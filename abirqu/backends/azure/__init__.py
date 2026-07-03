"""
Azure Quantum Backend — Real hardware via azure-quantum SDK.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...backend import QuantumBackend, JobStatus, JobHandle
from ...circuit import Circuit


@dataclass
class AzureQuantumCredentials:
    subscription_id: str
    resource_group: str
    workspace_name: str
    location: str = "eastus"

    @classmethod
    def from_env(cls) -> "AzureQuantumCredentials":
        return cls(
            subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID", ""),
            resource_group=os.getenv("AZURE_RESOURCE_GROUP", ""),
            workspace_name=os.getenv("AZURE_WORKSPACE_NAME", ""),
            location=os.getenv("AZURE_LOCATION", "eastus"),
        )

    def validate(self) -> bool:
        return bool(self.subscription_id and self.resource_group and self.workspace_name)


class AzureQuantumBackend(QuantumBackend):
    """Azure Quantum backend using azure-quantum SDK.

    Parameters
    ----------
    credentials : AzureQuantumCredentials, optional
        Falls back to environment variables.
    target : str
        Provider target, e.g. ``'ionq.simulator'`` or ``'quantinuum.sim.h1-1sc'``.
    """

    name = "Azure-Quantum"
    max_qubits = 12
    native_gates = ["Ry", "Rz", "MS", "ZZ"]
    is_local = False

    def __init__(
        self,
        credentials: Optional[AzureQuantumCredentials] = None,
        target: str = "ionq.simulator",
    ):
        self.creds = credentials or AzureQuantumCredentials.from_env()
        self.target = target
        self._workspace = None

    def _get_workspace(self):
        if self._workspace is not None:
            return self._workspace
        if not self.creds.validate():
            raise ValueError(
                "Azure credentials required. Set AZURE_SUBSCRIPTION_ID, "
                "AZURE_RESOURCE_GROUP, AZURE_WORKSPACE_NAME."
            )
        try:
            from azure.quantum import Workspace
            self._workspace = Workspace(
                subscription_id=self.creds.subscription_id,
                resource_group=self.creds.resource_group,
                name=self.creds.workspace_name,
                location=self.creds.location,
            )
            return self._workspace
        except ImportError as exc:
            raise RuntimeError(
                "Azure backend requires 'azure-quantum'. "
                "Install with: pip install azure-quantum"
            ) from exc

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        workspace = self._get_workspace()
        target = workspace.get_targets(provider_id=self.target)

        # Convert via Qiskit bridge
        try:
            from qiskit import QuantumCircuit as QkCircuit, transpile
            qc = QkCircuit(circuit.num_qubits)
            for gate in getattr(circuit, "gates", []):
                name = gate.name.upper()
                q = list(gate.qubits)
                p = gate.params
                if name == "H":
                    qc.h(q[0])
                elif name in ("CNOT", "CX"):
                    qc.cx(q[0], q[1])
                elif name == "X":
                    qc.x(q[0])
                elif name == "Y":
                    qc.y(q[0])
                elif name == "Z":
                    qc.z(q[0])
                elif name == "S":
                    qc.s(q[0])
                elif name == "T":
                    qc.t(q[0])
                elif name == "RX":
                    qc.rx(float(p[0]), q[0])
                elif name == "RY":
                    qc.ry(float(p[0]), q[0])
                elif name == "RZ":
                    qc.rz(float(p[0]), q[0])
                elif name == "CZ":
                    qc.cz(q[0], q[1])
                elif name == "SWAP":
                    qc.swap(q[0], q[1])
            tqc = transpile(qc, basis_gates=["rx", "ry", "rz", "cx"])
            job = target.submit(tqc, name="abirqu-job", shots=shots)
            result = job.get_results()
            counts = result.get("histogram", {})
            # Normalize counts
            counts = {k: int(v) for k, v in counts.items()}
            total = sum(counts.values()) or shots
            probs = {k: v / total for k, v in counts.items()}
            return {
                "success": True,
                "backend": f"Azure:{self.target}",
                "shots": shots,
                "counts": counts,
                "probabilities": probs,
                "statevector": None,
            }
        except ImportError:
            raise RuntimeError("Azure Qiskit bridge requires 'qiskit'.")

    def submit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> JobHandle:
        workspace = self._get_workspace()
        target = workspace.get_targets(provider_id=self.target)

        try:
            from qiskit import QuantumCircuit as QkCircuit
            qc = QkCircuit(circuit.num_qubits)
            for gate in getattr(circuit, "gates", []):
                name = gate.name.upper()
                q = list(gate.qubits)
                p = gate.params
                if name == "H":
                    qc.h(q[0])
                elif name in ("CNOT", "CX"):
                    qc.cx(q[0], q[1])
                elif name == "X":
                    qc.x(q[0])
                elif name == "Y":
                    qc.y(q[0])
                elif name == "Z":
                    qc.z(q[0])
                elif name == "RX":
                    qc.rx(float(p[0]), q[0])
                elif name == "RY":
                    qc.ry(float(p[0]), q[0])
                elif name == "RZ":
                    qc.rz(float(p[0]), q[0])
                elif name == "CZ":
                    qc.cz(q[0], q[1])
                elif name == "SWAP":
                    qc.swap(q[0], q[1])

            from qiskit import transpile
            tqc = transpile(qc, basis_gates=["rx", "ry", "rz", "cx"])
            job = target.submit(tqc, name="abirqu-job", shots=shots)
            return JobHandle(
                job_id=job.id,
                backend=self,
                status=JobStatus.RUNNING,
            )
        except ImportError:
            raise RuntimeError("Azure Qiskit bridge required.")

    def query_job(self, job_id: str) -> JobStatus:
        try:
            workspace = self._get_workspace()
            job = workspace.get_job(job_id)
            status_map = {
                "Succeeded": JobStatus.COMPLETED,
                "Failed": JobStatus.FAILED,
                "Cancelled": JobStatus.CANCELED,
            }
            return status_map.get(job.details.status, JobStatus.RUNNING)
        except Exception:
            return JobStatus.UNKNOWN

    def fetch_result(self, job_id: str) -> Dict[str, Any]:
        workspace = self._get_workspace()
        job = workspace.get_job(job_id)
        result = job.get_results()
        counts = {k: int(v) for k, v in result.get("histogram", {}).items()}
        total = sum(counts.values()) or 1
        probs = {k: v / total for k, v in counts.items()}
        return {
            "success": True,
            "backend": f"Azure:{self.target}",
            "shots": total,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }

    def cancel_job(self, job_id: str) -> bool:
        try:
            workspace = self._get_workspace()
            job = workspace.get_job(job_id)
            job.cancel()
            return True
        except Exception:
            return False

    def list_backends(self) -> List[Dict[str, Any]]:
        workspace = self._get_workspace()
        targets = workspace.get_targets()
        return [
            {"name": t.name, "provider": t.provider_id, "status": t.status}
            for t in targets
        ]
