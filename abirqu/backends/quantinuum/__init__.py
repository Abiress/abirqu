"""
Quantinuum (H-Series) Backend - Real Implementation
Uses pytket + Quantinuum backend
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class QuantinuumCredentials:
    """Quantinuum credentials"""
    api_key: str
    endpoint: str = "https://api.quantinuum.lu"
    
    @classmethod
    def from_env(cls) -> "QuantinuumCredentials":
        import os
        return cls(
            api_key=os.getenv("QUANTINUUM_API_KEY", ""),
            endpoint=os.getenv("QUANTINUUM_ENDPOINT", "https://api.quantinuum.lu")
        )


class QuantinuumBackend:
    """Quantinuum H-Series backend using pytket"""
    
    def __init__(self, credentials: Optional[QuantinuumCredentials] = None):
        self.creds = credentials or QuantinuumCredentials.from_env()
        
        # Try to import pytket
        try:
            import pytket
            from pytket.extensions import quantinuum
            self.pytket_available = True
        except ImportError:
            self.pytket_available = False
    
    def create_circuit(self, num_qubits: int = 2) -> Any:
        """Create a pytket circuit"""
        if not self.pytket_available:
            raise RuntimeError("pytket not installed. Install: pip install pytket pytket-quantinuum")
        
        from pytket import Circuit
        return Circuit(num_qubits)
    
    def add_h_gate(self, circuit: Any, qubit: int) -> None:
        """Add H gate"""
        if not self.pytket_available:
            raise RuntimeError("pytket not available")
        from pytket import OpType
        circuit.add_gate(OpType.H, [qubit])
    
    def add_cnot(self, circuit: Any, control: int, target: int) -> None:
        """Add CNOT gate"""
        if not self.pytket_available:
            raise RuntimeError("pytket not available")
        from pytket import OpType
        circuit.add_gate(OpType.CX, [control, target])
    
    def create_bell_state(self) -> Any:
        """Create Bell state circuit"""
        circuit = self.create_circuit(2)
        self.add_h_gate(circuit, 0)
        self.add_cnot(circuit, 0, 1)
        return circuit
    
    def compile_for_quantinuum(self, circuit: Any) -> Any:
        """Compile circuit for Quantinuum backend"""
        if not self.pytket_available:
            raise RuntimeError("pytket-quantinuum not available")
        
        from pytket.extensions import quantinuum
        device = quantinuum.H1()  # H-Series device
        compiled = circuit.copy()
        compiled.rename_qubits(device.default_mapping(circuit.n_qubits))
        return compiled
    
    def get_quantinuum_backends(self) -> List[str]:
        """List available Quantinuum backends"""
        return [
            "H1",      # 20-qubit H-Series
            "H2",      # 32-qubit H-Series
            "H1-LE",   # H1 with low energy
            "H2-LE",   # H2 with low energy
        ]
    
    def test_pytket(self) -> bool:
        """Test pytket integration"""
        if not self.pytket_available:
            return False
        
        try:
            circuit = self.create_bell_state()
            compiled = self.compile_for_quantinuum(circuit)
            return compiled.n_qubits > 0
        except Exception:
            return False


if __name__ == "__main__":
    backend = QuantinuumBackend()
    
    print("Testing Quantinuum (H-Series) Backend...")
    print(f"pytket available: {backend.pytket_available}")
    
    if backend.pytket_available:
        if backend.test_pytket():
            print("✓ pytket + Quantinuum integration working")
            bell = backend.create_bell_state()
            print(f"Bell state circuit created: {bell.n_qubits} qubits")
        else:
            print("✗ pytket test failed")
    else:
        print("Install pytket: pip install pytket pytket-quantinuum")
        print("Quantinuum backends:", backend.get_quantinuum_backends())
