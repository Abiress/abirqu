"""
OQC (Superconducting) Backend - Real Implementation
Uses REST API for Oxford Quantum Computing systems
"""

import json
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class OQCCredentials:
    """OQC credentials"""
    api_key: str
    endpoint: str = "https://api.oqc.se"
    
    @classmethod
    def from_env(cls) -> "OQCCredentials":
        import os
        return cls(
            api_key=os.getenv("OQC_API_KEY", ""),
            endpoint=os.getenv("OQC_ENDPOINT", "https://api.oqc.se")
        )


class OQCBackend:
    """OQC superconductung backend with REST API"""
    
    def __init__(self, credentials: Optional[OQCCredentials] = None):
        self.creds = credentials or OQCCredentials.from_env()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.creds.api_key}",
            "Content-Type": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request to OQC API"""
        url = f"{self.creds.endpoint}/{endpoint.lstrip('/')}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OQC API request failed: {e}")
    
    def list_backends(self) -> List[Dict[str, Any]]:
        """List available OQC backends"""
        result = self._request("GET", "/v1/devices")
        return result.get("devices", [])
    
    def get_backend_info(self, device_id: str) -> Dict[str, Any]:
        """Get device information"""
        return self._request("GET", f"/v1/devices/{device_id}")
    
    def create_qasm_circuit(self) -> Dict[str, Any]:
        """Create Bell state QASM program"""
        qasm = """
        OPENQASM 2.0;
        include "qelib1.inc";
        qreg q[2];
        creg c[2];
        h q[0];
        cx q[0],q[1];
        measure q -> c;
        """
        return {
            "qasm": qasm,
            "shots": 1024
        }
    
    def submit_circuit(self, circuit_qasm: str, device_id: str, shots: int = 1024) -> Dict[str, Any]:
        """Submit circuit to OQC"""
        payload = {
            "qasm": circuit_qasm,
            "device": device_id,
            "shots": shots
        }
        result = self._request("POST", "/v1/jobs", json=payload)
        job_id = result.get("job_id")
        
        return self._poll_job(job_id)
    
    def _poll_job(self, job_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Poll job status"""
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self._request("GET", f"/v1/jobs/{job_id}")
            status = result.get("status", "")
            
            if status in ["COMPLETED", "FAILED"]:
                return result
            
            time.sleep(2)
        
        raise TimeoutError(f"Job {job_id} timed out")
    
    def get_counts(self, job_result: Dict[str, Any]) -> Dict[str, int]:
        """Extract counts from result"""
        if "result" in job_result and "counts" in job_result["result"]:
            return job_result["result"]["counts"]
        return {}
    
    def get_oqc_backends(self) -> List[str]:
        """List available OQC backends"""
        return [
            "Lucy",       # 8-qubit superconductung processor
            "Penny",      # 4-qubit processor
            "Simulator",  # Cloud simulator
        ]
    
    def test_connection(self) -> bool:
        """Test connection to OQC"""
        if not self.creds.api_key:
            return False
        
        try:
            backends = self.list_backends()
            return isinstance(backends, list)
        except Exception:
            return False


if __name__ == "__main__":
    backend = OQCBackend()
    
    print("Testing OQC (Superconducting) Backend...")
    print(f"Credentials valid: {bool(backend.creds.api_key)}")
    
    if backend.test_connection():
        print("✓ Connected to OQC")
        backends = backend.list_backends()
        print(f"Available backends: {len(backends)}")
    else:
        print("✗ Could not connect (check OQC_API_KEY)")
        print("OQC backends:", backend.get_oqc_backends())
