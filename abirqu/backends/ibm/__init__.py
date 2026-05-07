"""
IBM Quantum (IBMQ) Backend - Real REST API Implementation
Connects to IBM Quantum services via qiskit-ibm-runtime with real API calls
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class IBMQuantumCredentials:
    """IBM Quantum credentials"""
    api_token: str
    instance: str = "ibm-q/open/main"
    url: str = "https://api.quantum-computing.ibm.com"
    
    @classmethod
    def from_env(cls) -> "IBMQuantumCredentials":
        """Load credentials from environment variables"""
        return cls(
            api_token=os.getenv("IBM_QUANTUM_TOKEN", ""),
            instance=os.getenv("IBM_QUANTUM_INSTANCE", "ibm-q/open/main"),
            url=os.getenv("IBM_QUANTUM_URL", "https://api.quantum-computing.ibm.com")
        )
    
    def validate(self) -> bool:
        """Validate credentials are present"""
        return len(self.api_token) > 0


class IBMQuantumBackend:
    """IBM Quantum backend with real API calls"""
    
    def __init__(self, credentials: Optional[IBMQuantumCredentials] = None):
        self.creds = credentials or IBMQuantumCredentials.from_env()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.creds.api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        self.base_url = self.creds.url
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to IBM API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"IBM API request failed: {e}")
    
    def list_backends(self) -> List[Dict[str, Any]]:
        """List available IBM quantum backends"""
        result = self._make_request("GET", f"v1/backends?instance={self.creds.instance}")
        return result.get("backends", [])
    
    def get_backend_info(self, backend_name: str) -> Dict[str, Any]:
        """Get information about a specific backend"""
        result = self._make_request("GET", f"v1/backends/{backend_name}")
        return result
    
    def compile_circuit(self, circuit_qasm: str, backend_name: str) -> Dict[str, Any]:
        """Compile a QASM circuit for a specific backend"""
        payload = {
            "qasm": circuit_qasm,
            "backend": backend_name,
            "optimization_level": 3
        }
        result = self._make_request("POST", "v1/compile", json=payload)
        return result
    
    def run_circuit(self, compiled_circuit: str, backend_name: str, shots: int = 1024) -> Dict[str, Any]:
        """Run a compiled circuit on IBM hardware"""
        payload = {
            "circuit": compiled_circuit,
            "backend": backend_name,
            "shots": shots,
            "instance": self.creds.instance
        }
        result = self._make_request("POST", "v1/jobs", json=payload)
        job_id = result.get("job_id")
        
        # Poll for completion
        return self._poll_job(job_id)
    
    def _poll_job(self, job_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Poll job status until completion"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self._make_request("GET", f"v1/jobs/{job_id}")
            status = result.get("status", "")
            
            if status in ["COMPLETED", "FAILED", "CANCELED"]:
                return result
            
            time.sleep(2)
        
        raise TimeoutError(f"Job {job_id} timed out after {timeout}s")
    
    def get_counts(self, job_result: Dict[str, Any]) -> Dict[str, int]:
        """Extract measurement counts from job result"""
        if "result" in job_result:
            for res in job_result["result"]:
                if "data" in res and "counts" in res["data"]:
                    return res["data"]["counts"]
        return {}
    
    def get_probabilities(self, counts: Dict[str, int]) -> Dict[str, float]:
        """Convert counts to probabilities"""
        total = sum(counts.values())
        if total == 0:
            return {}
        return {state: count / total for state, count in counts.items()}
    
    def test_connection(self) -> bool:
        """Test connection to IBM Quantum"""
        try:
            backends = self.list_backends()
            return len(backends) > 0
        except Exception:
            return False


# Convenience function
def create_ibm_backend(api_token: Optional[str] = None) -> IBMQuantumBackend:
    """Create IBM Quantum backend with optional token"""
    if api_token:
        creds = IBMQuantumCredentials(api_token=api_token)
    else:
        creds = IBMQuantumCredentials.from_env()
    
    if not creds.validate():
        raise ValueError(
            "IBM Quantum API token required. Set IBM_QUANTUM_TOKEN environment variable "
            "or pass api_token parameter."
        )
    
    return IBMQuantumBackend(creds)


if __name__ == "__main__":
    # Test the implementation
    backend = create_ibm_backend()
    
    print("Testing IBM Quantum Backend...")
    print(f"Credentials valid: {backend.creds.validate()}")
    print(f"Base URL: {backend.base_url}")
    
    # Test connection (requires real token)
    if backend.test_connection():
        print("✓ Connected to IBM Quantum")
        backends = backend.list_backends()
        print(f"Available backends: {len(backends)}")
    else:
        print("✗ Could not connect (check IBM_QUANTUM_TOKEN)")
