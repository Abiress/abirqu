"""
Rigetti / QCS Backend - Real Implementation
Uses pyquil and Quil IR for Rigetti systems
"""

import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class RigettiCredentials:
    """Rigetti credentials"""
    api_key: str
    endpoint: str = "https://api.rigetti.com"
    
    @classmethod
    def from_env(cls) -> "RigettiCredentials":
        import os
        return cls(
            api_key=os.getenv("RIGETTI_API_KEY", ""),
            endpoint=os.getenv("RIGETTI_ENDPOINT", "https://api.rigetti.com")
        )


class RigettiBackend:
    """Rigetti backend using pyquil + Quil IR"""
    
    def __init__(self, credentials: Optional[RigettiCredentials] = None):
        self.creds = credentials or RigettiCredentials.from_env()
        
        # Try to import pyquil
        try:
            import pyquil
            self.pyquil_available = True
        except ImportError:
            self.pyquil_available = False
    
    def create_program(self, num_qubits: int = 2) -> Any:
        """Create a pyquil program"""
        if not self.pyquil_available:
            raise RuntimeError("pyquil not installed. Install: pip install pyquil")
        
        import pyquil as pq
        return pq.Program()
    
    def add_h_gate(self, program: Any, qubit: int) -> None:
        """Add H gate"""
        if not self.pyquil_available:
            raise RuntimeError("pyquil not available")
        import pyquil as pq
        program += pq.H(qubit)
    
    def add_cnot(self, program: Any, control: int, target: int) -> None:
        """Add CNOT gate"""
        if not self.pyquil_available:
            raise RuntimeError("pyquil not available")
        import pyquil as pq
        program += pq.CNOT(control, target)
    
    def create_bell_state(self) -> Any:
        """Create Bell state program"""
        program = self.create_program(2)
        self.add_h_gate(program, 0)
        self.add_cnot(program, 0, 1)
        return program
    
    def to_quil(self, program: Any) -> str:
        """Convert program to Quil IR"""
        if not self.pyquil_available:
            raise RuntimeError("pyquil not available")
        return str(program)
    
    def submit_to_qcs(self, quil_code: str, shots: int = 1024) -> Dict[str, Any]:
        """Submit Quil program to QCS"""
        import requests
        
        headers = {
            "X-API-Key": self.creds.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "quil": quil_code,
            "shots": shots
        }
        
        try:
            response = requests.post(
                f"{self.creds.endpoint}/v1/jobs",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"QCS submission failed: {e}")
    
    def get_rigetti_backends(self) -> List[str]:
        """List available Rigetti backends"""
        return [
            "Aspen-M-3",      # 80-qubit processor
            "Ankaa-3",      # Next-gen processor
            "QVM",           # Rigetti simulator
        ]
    
    def test_pyquil(self) -> bool:
        """Test pyquil integration"""
        if not self.pyquil_available:
            return False
        
        try:
            bell = self.create_bell_state()
            quil_code = self.to_quil(bell)
            return len(quil_code) > 0
        except Exception:
            return False


if __name__ == "__main__":
    backend = RigettiBackend()
    
    print("Testing Rigetti/QCS Backend...")
    print(f"pyquil available: {backend.pyquil_available}")
    
    if backend.pyquil_available:
        if backend.test_pyquil():
            print("✓ pyquil integration working")
            bell = backend.create_bell_state()
            print(f"Bell state Quil: {backend.to_quil(bell)[:50]}...")
        else:
            print("✗ pyquil test failed")
    else:
        print("Install pyquil: pip install pyquil")
        print("Rigetti backends:", backend.get_rigetti_backends())
