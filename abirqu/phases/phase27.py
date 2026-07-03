import os
from typing import Any, Dict, Optional

from ..backend import FastBackend
from ..backends.aws import AWSBraketBackend as BraketBackend
from ..backends.azure import AzureQuantumBackend as AzureBackend
from ..backends.google import GoogleQuantumBackend as CirqBackend
from ..backends.ibm import IBMQuantumBackend as IBMQBackend
from ..backends.ionq import IonQBackend
from ..circuit import Circuit


class HardwareExecutionManager:
    """Run circuits on real hardware when credentials are available.

    Set `dry_run=True` to validate routing and run locally without cloud credentials.
    """

    SUPPORTED = {"local", "ibm", "aws", "azure", "ionq", "google"}

    @staticmethod
    def _pick_env(*names: str) -> str:
        for name in names:
            value = os.getenv(name)
            if value:
                return value
        return ""

    @staticmethod
    def _missing_credentials_response(provider: str, required_env: list[str], hint: str = "") -> Dict[str, Any]:
        return {
            "success": False,
            "provider": provider,
            "error": "missing_credentials",
            "required_env": required_env,
            "message": f"Missing credentials for provider '{provider}'. Set one of: {', '.join(required_env)}",
            "hint": hint,
        }

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
            token = creds.get("token") or self._pick_env("IBM_QUANTUM_TOKEN", "IBM_TOKEN")
            if not token:
                return self._missing_credentials_response(
                    "ibm",
                    ["IBM_QUANTUM_TOKEN", "IBM_TOKEN"],
                    "Use dry_run=True for local validation without cloud credentials.",
                )
            backend_name = creds.get("backend_name", "ibmq_qasm_simulator")
            instance = creds.get("instance", "ibm-q/open/main")
            return IBMQBackend(token=token, backend_name=backend_name, instance=instance).run_circuit(circuit, shots=shots)

        if p == "aws":
            access_key = creds.get("aws_access_key_id") or self._pick_env("AWS_ACCESS_KEY_ID")
            secret_key = creds.get("aws_secret_access_key") or self._pick_env("AWS_SECRET_ACCESS_KEY")
            if not (access_key and secret_key):
                return self._missing_credentials_response(
                    "aws",
                    ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
                    "Also configure region/profile as needed by AWS SDK.",
                )
            device_arn = creds.get("device_arn", "arn:aws:braket:::device/quantum-simulator/amazon/sv1")
            s3_bucket = creds.get("s3_bucket", "")
            s3_prefix = creds.get("s3_prefix", "abirqu-results")
            return BraketBackend(device_arn=device_arn, s3_bucket=s3_bucket, s3_prefix=s3_prefix).run_circuit(circuit, shots=shots)

        if p == "azure":
            resource_id = creds.get("resource_id") or self._pick_env("AZURE_QUANTUM_RESOURCE_ID", "AZURE_RESOURCE_ID")
            if not resource_id:
                return self._missing_credentials_response(
                    "azure",
                    ["AZURE_QUANTUM_RESOURCE_ID", "AZURE_RESOURCE_ID"],
                    "Azure SDK auth must also be configured (for example via az login).",
                )
            location = creds.get("location", "eastus")
            provider_id = creds.get("provider_id", "ionq")
            target = creds.get("target", "ionq.simulator")
            return AzureBackend(resource_id=resource_id, location=location, provider_id=provider_id, target=target).run_circuit(circuit, shots=shots)

        if p == "ionq":
            api_key = creds.get("api_key") or self._pick_env("IONQ_API_KEY")
            if not api_key:
                return self._missing_credentials_response(
                    "ionq",
                    ["IONQ_API_KEY"],
                    "Use dry_run=True to validate end-to-end flow without provider access.",
                )
            target = creds.get("target", "simulator")
            return IonQBackend(api_key=api_key, target=target).run_circuit(circuit, shots=shots)

        if p == "google":
            processor_id = creds.get("processor_id")
            project_id = creds.get("project_id") or self._pick_env("GOOGLE_CLOUD_PROJECT", "GOOGLE_PROJECT_ID")
            if not project_id:
                return self._missing_credentials_response(
                    "google",
                    ["GOOGLE_CLOUD_PROJECT", "GOOGLE_PROJECT_ID"],
                    "Google auth credentials must also be configured for live runs.",
                )
            return CirqBackend(use_gpu=False, processor_id=processor_id).run_circuit(circuit, shots=shots, project_id=project_id)

        raise ValueError(f"Unhandled provider: {provider}")


class HardwareCapabilityProbe:
    def detect(self) -> Dict[str, bool]:
        return {
            "ibm": bool(os.getenv("IBM_QUANTUM_TOKEN") or os.getenv("IBM_TOKEN")),
            "aws": bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")),
            "azure": bool(os.getenv("AZURE_QUANTUM_RESOURCE_ID") or os.getenv("AZURE_RESOURCE_ID")),
            "ionq": bool(os.getenv("IONQ_API_KEY")),
            "google": bool(os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_PROJECT_ID")),
        }
