import os
from typing import Any, Dict, Optional

from ..backend import AzureBackend, BraketBackend, CirqBackend, FastBackend, IBMQBackend, IonQBackend
from ..circuit import Circuit


class HardwareExecutionManager:
    """Run circuits on real hardware when credentials are available.

    Set `dry_run=True` to validate routing and run locally without cloud credentials.
    """

    SUPPORTED = {"local", "ibm", "aws", "azure", "ionq", "google"}

    def list_supported(self):
        return sorted(self.SUPPORTED)

    def run(
        self,
        circuit: Circuit,
        provider: str = "local",
        shots: int = 1024,
        dry_run: bool = False,
        credentials: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        p = provider.lower()
        if p not in self.SUPPORTED:
            raise ValueError(f"Unsupported provider: {provider}")

        if dry_run or p == "local":
            result = FastBackend(n_qubits=circuit.num_qubits).run_circuit(circuit, shots=shots)
            result["dry_run"] = True
            result["provider"] = p
            return result

        creds = credentials or {}
        if p == "ibm":
            token = creds.get("token") or os.getenv("IBM_QUANTUM_TOKEN", "")
            backend_name = creds.get("backend_name", "ibmq_qasm_simulator")
            instance = creds.get("instance", "ibm-q/open/main")
            return IBMQBackend(token=token, backend_name=backend_name, instance=instance).run_circuit(circuit, shots=shots)

        if p == "aws":
            device_arn = creds.get("device_arn", "arn:aws:braket:::device/quantum-simulator/amazon/sv1")
            s3_bucket = creds.get("s3_bucket", "")
            s3_prefix = creds.get("s3_prefix", "abirqu-results")
            return BraketBackend(device_arn=device_arn, s3_bucket=s3_bucket, s3_prefix=s3_prefix).run_circuit(circuit, shots=shots)

        if p == "azure":
            resource_id = creds.get("resource_id") or os.getenv("AZURE_QUANTUM_RESOURCE_ID", "")
            location = creds.get("location", "eastus")
            provider_id = creds.get("provider_id", "ionq")
            target = creds.get("target", "ionq.simulator")
            return AzureBackend(resource_id=resource_id, location=location, provider_id=provider_id, target=target).run_circuit(circuit, shots=shots)

        if p == "ionq":
            api_key = creds.get("api_key") or os.getenv("IONQ_API_KEY", "")
            target = creds.get("target", "simulator")
            return IonQBackend(api_key=api_key, target=target).run_circuit(circuit, shots=shots)

        if p == "google":
            processor_id = creds.get("processor_id")
            project_id = creds.get("project_id", "")
            return CirqBackend(use_gpu=False, processor_id=processor_id).run_circuit(circuit, shots=shots, project_id=project_id)

        raise ValueError(f"Unhandled provider: {provider}")


class HardwareCapabilityProbe:
    def detect(self) -> Dict[str, bool]:
        return {
            "ibm": bool(os.getenv("IBM_QUANTUM_TOKEN")),
            "aws": bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")),
            "azure": bool(os.getenv("AZURE_QUANTUM_RESOURCE_ID")),
            "ionq": bool(os.getenv("IONQ_API_KEY")),
            "google": bool(os.getenv("GOOGLE_CLOUD_PROJECT")),
        }
