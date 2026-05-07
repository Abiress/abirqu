"""
Azure Quantum Backend - Real Implementation
Uses azure-quantum Python SDK with real API calls
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class AzureQuantumCredentials:
    """Azure Quantum credentials"""
    subscription_id: str
    resource_group: str
    workspace_name: str
    location: str = "westus"
    
    @classmethod
    def from_env(cls) -> "AzureQuantumCredentials":
        return cls(
            subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID", ""),
            resource_group=os.getenv("AZURE_RESOURCE_GROUP", ""),
            workspace_name=os.getenv("AZURE_WORKSPACE_NAME", ""),
            location=os.getenv("AZURE_LOCATION", "westus")
        )
    
    def validate(self) -> bool:
        return all([
            len(self.subscription_id) > 0,
            len(self.resource_group) > 0,
            len(self.workspace_name) > 0
        ])


class AzureQuantumBackend:
    """Azure Quantum backend with real SDK integration"""
    
    def __init__(self, credentials: Optional[AzureQuantumCredentials] = None):
        self.creds = credentials or AzureQuantumCredentials.from_env()
        self.workspace = None
        
        # Try to import azure-quantum
        try:
            from azure.quantum import Workspace
            self.azure_available = True
        except ImportError:
            self.azure_available = False
    
    def _get_workspace(self):
        """Get or create Azure Quantum workspace"""
        if self.workspace:
            return self.workspace
        
        if not self.azure_available:
            raise RuntimeError("azure-quantum not installed. Install: pip install azure-quantum")
        
        if not self.creds.validate():
            raise ValueError(
                "Azure credentials required. Set AZURE_SUBSCRIPTION_ID, "
                "AZURE_RESOURCE_GROUP, AZURE_WORKSPACE_NAME"
            )
        
        from azure.quantum import Workspace
        
        self.workspace = Workspace(
            subscription_id=self.creds.subscription_id,
            resource_group=self.creds.resource_group,
            name=self.creds.workspace_name,
            location=self.creds.location
        )
        return self.workspace
    
    def list_backends(self) -> List[Dict[str, Any]]:
        """List available Azure Quantum backends"""
        if not self.azure_available:
            raise RuntimeError("azure-quantum not available")
        
        workspace = self._get_workspace()
        providers = workspace.get_targets()
        return [{"name": p.name, "id": p.id, "status": p.status} for p in providers]
    
    def get_backend_info(self, backend_id: str) -> Dict[str, Any]:
        """Get information about a specific backend"""
        workspace = self._get_workspace()
        target = workspace.get_targets(provider_id=backend_id)
        if target:
            return {"name": target.name, "id": target.id, "status": target.status}
        return {}
    
    def create_bell_circuit(self) -> Any:
        """Create Bell state circuit for Azure"""
        if not self.azure_available:
            raise RuntimeError("azure-quantum not available")
        
        from azure.quantum.circuits import Circuit
        
        circuit = Circuit()
        circuit.h(0)
        circuit.cx(0, 1)  # CNOT
        return circuit
    
    def submit_circuit(self, circuit: Any, backend_id: str, shots: int = 1024) -> Dict[str, Any]:
        """Submit circuit to Azure Quantum"""
        workspace = self._get_workspace()
        
        job = workspace.submit(circuit, backend_id=backend_id, shots=shots)
        job.wait_until_completed()
        
        return {
            "job_id": job.id,
            "status": job.details.status,
            "results": job.details.results if hasattr(job.details, 'results') else {}
        }
    
    def get_counts(self, job_result: Dict[str, Any]) -> Dict[str, int]:
        """Extract measurement counts from job result"""
        counts = {}
        if "results" in job_result:
            for res in job_result["results"]:
                if "data" in res and "counts" in res["data"]:
                    counts.update(res["data"]["counts"])
        return counts
    
    def get_azure_backends(self) -> List[str]:
        """List available Azure Quantum backends"""
        return [
            "ionq.simulator",
            "ionq.qpu",
            "quantinuum.qpu",
            "microsoft.simulator",
            "microsoft.estimator",
        ]
    
    def test_connection(self) -> bool:
        """Test connection to Azure Quantum"""
        if not self.azure_available:
            return False
        
        try:
            backends = self.list_backends()
            return isinstance(backends, list)
        except Exception:
            return False


if __name__ == "__main__":
    backend = AzureQuantumBackend()
    
    print("Testing Azure Quantum Backend...")
    print(f"azure-quantum available: {backend.azure_available}")
    
    if backend.azure_available:
        if backend.test_connection():
            print("✓ Connected to Azure Quantum")
            backends = backend.list_backends()
            print(f"Available backends: {len(backends)}")
        else:
            print("✗ Could not connect (check Azure credentials)")
    else:
        print("Install azure-quantum: pip install azure-quantum")
        print("Azure backends:", backend.get_azure_backends())
