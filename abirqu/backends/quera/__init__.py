"""
QuEra Aquila Backend — Real hardware via AWS Braket (analog Hamiltonian).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ...backend import QuantumBackend, JobStatus, JobHandle
from ...circuit import Circuit


@dataclass
class QuEraCredentials:
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    region: str = "us-east-1"

    @classmethod
    def from_env(cls) -> "QuEraCredentials":
        return cls(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            region=os.getenv("AWS_REGION", "us-east-1"),
        )


class QuEraBackend(QuantumBackend):
    """QuEra Aquila analog Hamiltonian QPU via AWS Braket.

    QuEra operates on the analog Hamiltonian model — circuits must be
    decomposed to amplitude/phase/detuning pulses.

    Parameters
    ----------
    credentials : QuEraCredentials, optional
        Falls back to environment variables.
    """

    name = "QuEra"
    max_qubits = 256
    native_gates = []  # Analog — no discrete gates
    is_local = False

    def __init__(self, credentials: Optional[QuEraCredentials] = None):
        self.creds = credentials or QuEraCredentials.from_env()
        self.aquila_arn = "arn:aws:braket:us-east-1::device/qpu/aquila"

    def _circuit_to_analog(self, circuit: Circuit) -> dict:
        """Convert AbirQu circuit to analog Hamiltonian program.

        This is a simplified converter that maps qubit positions to atom
        locations and creates basic driving fields.
        """
        n = circuit.num_qubits
        sites = [{"x": float(i * 8), "y": 0.0} for i in range(n)]
        filling = [1] * n

        # Build driving fields from circuit structure
        driving_fields = []
        for gate in getattr(circuit, "gates", []):
            name = gate.name.upper()
            qubits = list(gate.qubits)
            params = list(gate.params)
            if name == "H":
                driving_fields.append({
                    "amplitude": 1.0,
                    "phase": 0.0,
                    "detuning": 0.0,
                })
            elif name in ("CNOT", "CX"):
                driving_fields.append({
                    "amplitude": 0.5,
                    "phase": 0.0,
                    "detuning": 100.0,
                })

        if not driving_fields:
            driving_fields = [{"amplitude": 1.0, "phase": 0.0, "detuning": 0.0}]

        return {
            "setup": {
                "atomArray": {
                    "sites": sites,
                    "filling": filling,
                }
            },
            "hamiltonian": {
                "drivingFields": driving_fields,
            },
        }

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            import boto3
            from botocore.config import Config
        except ImportError as exc:
            raise RuntimeError(
                "QuEra backend requires boto3. Install with: pip install boto3"
            ) from exc

        program = self._circuit_to_analog(circuit)
        config = Config(retries={"max_attempts": 3})
        client = boto3.client(
            "braket",
            aws_access_key_id=self.creds.aws_access_key_id,
            aws_secret_access_key=self.creds.aws_secret_access_key,
            region_name=self.creds.region,
            config=config,
        )

        response = client.create_task(
            taskName=f"abirqu-quera-{int(time.time())}",
            taskSpecification={
                "source": json.dumps(program),
                "shots": shots,
            },
            deviceArn=self.aquila_arn,
        )
        task_arn = response.get("taskArn", "")

        # Poll for completion
        while True:
            result = client.get_task(taskArn=task_arn)
            status = result.get("status", "")
            if status == "COMPLETED":
                break
            if status in ("FAILED", "CANCELLED"):
                raise RuntimeError(f"QuEra task {task_arn} ended with status={status}")
            time.sleep(5)

        counts_str = result.get("measurementResults", {}).get("measurementCounts", {})
        counts = {k: int(v) for k, v in counts_str.items()}
        total = sum(counts.values()) or shots
        probs = {k: v / total for k, v in counts.items()}

        return {
            "success": True,
            "backend": "QuEra:Aquila",
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
            import boto3
            from botocore.config import Config
        except ImportError as exc:
            raise RuntimeError("boto3 required.") from exc

        program = self._circuit_to_analog(circuit)
        config = Config(retries={"max_attempts": 3})
        client = boto3.client(
            "braket",
            aws_access_key_id=self.creds.aws_access_key_id,
            aws_secret_access_key=self.creds.aws_secret_access_key,
            region_name=self.creds.region,
            config=config,
        )

        response = client.create_task(
            taskName=f"abirqu-quera-{int(time.time())}",
            taskSpecification={
                "source": json.dumps(program),
                "shots": shots,
            },
            deviceArn=self.aquila_arn,
        )

        return JobHandle(
            job_id=response.get("taskArn", ""),
            backend=self,
            status=JobStatus.RUNNING,
        )

    def query_job(self, job_id: str) -> JobStatus:
        try:
            import boto3
            from botocore.config import Config
            config = Config(retries={"max_attempts": 3})
            client = boto3.client(
                "braket",
                aws_access_key_id=self.creds.aws_access_key_id,
                aws_secret_access_key=self.creds.aws_secret_access_key,
                region_name=self.creds.region,
                config=config,
            )
            result = client.get_task(taskArn=job_id)
            status_map = {
                "QUEUED": JobStatus.QUEUED,
                "RUNNING": JobStatus.RUNNING,
                "COMPLETED": JobStatus.COMPLETED,
                "FAILED": JobStatus.FAILED,
                "CANCELLED": JobStatus.CANCELED,
            }
            return status_map.get(result.get("status", ""), JobStatus.UNKNOWN)
        except Exception:
            return JobStatus.UNKNOWN

    def cancel_job(self, job_id: str) -> bool:
        try:
            import boto3
            from botocore.config import Config
            config = Config(retries={"max_attempts": 3})
            client = boto3.client(
                "braket",
                aws_access_key_id=self.creds.aws_access_key_id,
                aws_secret_access_key=self.creds.aws_secret_access_key,
                region_name=self.creds.region,
                config=config,
            )
            client.cancel_task(taskArn=job_id)
            return True
        except Exception:
            return False

    def list_backends(self) -> List[str]:
        return ["aquila", "simulator"]
