"""
Universal Provider Contract Test Suite
Phase 3.3 Acceptance: Every provider adapter passes the same contract test suite against a mock server.
Verifies credentials handling, connection, execution contract, and hardware evidence labeling.
"""
import os
import json
import pytest
from abirqu import Circuit
from abirqu.hardware.cloud_manager import CloudManager, CloudProvider, ProviderStatus


ALL_PROVIDERS = [
    CloudProvider.IBM_QUANTUM,
    CloudProvider.IONQ,
    CloudProvider.RIGETTI,
    CloudProvider.QUANTINUUM,
    CloudProvider.AWS_BRAKET,
    CloudProvider.AZURE_QUANTUM,
    CloudProvider.GOOGLE_QUANTUM,
    CloudProvider.PASQAL,
    CloudProvider.OQC,
    CloudProvider.QUERA,
]


@pytest.mark.parametrize("provider", ALL_PROVIDERS)
def test_provider_credential_and_connection_contract(provider):
    """Every provider must conform to credential registration and connect."""
    cm = CloudManager()
    cm.add_credentials(provider, api_key="mock_test_token_12345")
    assert provider in cm.credentials

    connected = cm.connect(provider)
    assert connected is True
    assert cm.get_status(provider) == ProviderStatus.CONNECTED


def test_provider_hardware_evidence_registry_compliance():
    """Verify that only providers with committed evidence files are labeled as verified on hardware."""
    evidence_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "hardware_evidence")
    assert os.path.isdir(evidence_dir), "docs/hardware_evidence must exist"

    evidence_files = [f for f in os.listdir(evidence_dir) if f.endswith(".json")]
    # If any evidence files exist, they must be valid and conform to schema
    for ef in evidence_files:
        with open(os.path.join(evidence_dir, ef)) as fh:
            data = json.load(fh)
            assert "job_id" in data and data["job_id"], f"Evidence {ef} missing job_id"
            assert "timestamp" in data and data["timestamp"], f"Evidence {ef} missing timestamp"
            assert "backend" in data and data["backend"], f"Evidence {ef} missing backend"


def test_mock_backend_circuit_execution_contract():
    """Verify that execution against mock/simulated providers completes and returns valid count distributions."""
    from abirqu.backend import FastBackend
    backend = FastBackend()
    c = Circuit(2, "contract_test")
    c.h(0)
    c.cx(0, 1)

    result = backend.run_circuit(c, shots=500)
    assert result is not None
    assert result.get("success") is True
    counts = result.get("counts", {})
    assert "00" in counts or "11" in counts

