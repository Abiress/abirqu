"""
AWS Braket Backend — Real hardware via amazon-braket-sdk.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...backend import QuantumBackend, JobStatus, JobHandle
from ...circuit import Circuit


@dataclass
class AWSBraketCredentials:
    aws_access_key_id: str
    aws_secret_access_key: str
    region: str = "us-east-1"

    @classmethod
    def from_env(cls) -> "AWSBraketCredentials":
        return cls(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
            region=os.getenv("AWS_REGION", "us-east-1"),
        )

    def validate(self) -> bool:
        return bool(self.aws_access_key_id and self.aws_secret_access_key)


class AWSBraketBackend(QuantumBackend):
    """AWS Braket backend using amazon-braket-sdk.

    Parameters
    ----------
    credentials : AWSBraketCredentials, optional
        Falls back to environment variables.
    device_arn : str
        ARN of the Braket device.
    s3_bucket : str
        S3 bucket for results.
    s3_prefix : str
        S3 key prefix.
    """

    name = "AWS-Braket"
    max_qubits = 34
    native_gates = ["C", "Rx", "Ry", "Rz", "H", "X", "Y", "Z", "CNOT", "CZ"]
    is_local = False

    def __init__(
        self,
        credentials: Optional[AWSBraketCredentials] = None,
        device_arn: str = "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        s3_bucket: str = "",
        s3_prefix: str = "abirqu-results",
    ):
        self.creds = credentials or AWSBraketCredentials.from_env()
        self.device_arn = device_arn
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            import boto3
            from botocore.config import Config
            config = Config(retries={"max_attempts": 3, "mode": "standard"})
            self._client = boto3.client(
                "braket",
                aws_access_key_id=self.creds.aws_access_key_id,
                aws_secret_access_key=self.creds.aws_secret_access_key,
                region_name=self.creds.region,
                config=config,
            )
            return self._client
        except ImportError as exc:
            raise RuntimeError(
                "Braket backend requires boto3. Install with: pip install boto3"
            ) from exc

    def _circuit_to_braket(self, circuit: Circuit):
        from ...converters import to_braket
        return to_braket(circuit)

    def run_circuit(
        self,
        circuit: Circuit,
        shots: int = 1024,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            from braket.aws import AwsDevice
        except ImportError as exc:
            raise RuntimeError(
                "Braket backend requires 'amazon-braket-sdk'. "
                "Install with: pip install amazon-braket-sdk"
            ) from exc

        bc = self._circuit_to_braket(circuit)
        device = AwsDevice(self.device_arn)
        s3_dest = (self.s3_bucket, self.s3_prefix) if self.s3_bucket else None
        task = device.run(bc, s3_destination_folder=s3_dest, shots=shots)
        result = task.result()
        counts = dict(result.measurement_counts)
        total = sum(counts.values())
        probs = {k: v / total for k, v in counts.items()}

        return {
            "success": True,
            "backend": f"Braket:{self.device_arn.split('/')[-1]}",
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
            from braket.aws import AwsDevice
        except ImportError as exc:
            raise RuntimeError("Braket SDK required.") from exc

        bc = self._circuit_to_braket(circuit)
        device = AwsDevice(self.device_arn)
        s3_dest = (self.s3_bucket, self.s3_prefix) if self.s3_bucket else None
        task = device.run(bc, s3_destination_folder=s3_dest, shots=shots)

        handle = JobHandle(
            job_id=task.id,
            backend=self,
            status=JobStatus.RUNNING,
        )
        handle._braket_task = task
        return handle

    def query_job(self, job_id: str) -> JobStatus:
        try:
            from braket.aws import AwsQuantumTask
            task = AwsQuantumTask(task_arn=job_id)
            state = task.state()
            state_map = {
                "QUEUED": JobStatus.QUEUED,
                "RUNNING": JobStatus.RUNNING,
                "COMPLETED": JobStatus.COMPLETED,
                "FAILED": JobStatus.FAILED,
                "CANCELLED": JobStatus.CANCELED,
            }
            return state_map.get(state, JobStatus.UNKNOWN)
        except Exception:
            return JobStatus.UNKNOWN

    def fetch_result(self, job_id: str) -> Dict[str, Any]:
        from braket.aws import AwsQuantumTask
        task = AwsQuantumTask(task_arn=job_id)
        result = task.result()
        counts = dict(result.measurement_counts)
        total = sum(counts.values())
        probs = {k: v / total for k, v in counts.items()}
        return {
            "success": True,
            "backend": f"Braket:{self.device_arn.split('/')[-1]}",
            "shots": total,
            "counts": counts,
            "probabilities": probs,
            "statevector": None,
        }

    def cancel_job(self, job_id: str) -> bool:
        try:
            from braket.aws import AwsQuantumTask
            task = AwsQuantumTask(task_arn=job_id)
            task.cancel()
            return True
        except Exception:
            return False

    def list_devices(self) -> List[Dict[str, Any]]:
        client = self._get_client()
        response = client.search_devices(
            filters=[{"name": "status", "values": ["ONLINE"]}]
        )
        return response.get("devices", [])


# Backward-compatible alias
BraketBackend = AWSBraketBackend
