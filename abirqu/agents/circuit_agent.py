"""Circuit Agent for AbirQu. Copyright 2026 Abir Maheshwari"""
from typing import Optional, Dict, List, Any
from ..core.circuit import Circuit
from ..core.gates import H, CNOT, X, Z, ry, rz

class CircuitGenerationAgent:
    """Generates quantum circuits from natural language descriptions."""
    
    def __init__(self):
        self.name = "CircuitAgent"
        self.templates = {
            'bell': self._create_bell_pair,
            'ghz': self._create_ghz,
            'qft': self._create_qft,
            'vqe': self._create_vqe,
            'grover': self._create_grover,
            'superposition': self._create_superposition,
            'entanglement': self._create_entanglement,
        }
        
    def generate(self, description: str, num_qubits: Optional[int] = None) -> Circuit:
        """Generate a circuit from natural language description."""
        desc_lower = description.lower()
        
        # Pattern matching for known circuits
        for key, func in self.templates.items():
            if key in desc_lower:
                if num_qubits:
                    return func(num_qubits)
                return func()
                
        # Default: create superposition on all qubits
        if num_qubits:
            return self._create_superposition(num_qubits)
        return self._create_bell_pair()
        
    def _create_bell_pair(self, num_qubits: int = 2) -> Circuit:
        """Create Bell pair: (|00> + |11>)/sqrt(2)."""
        circuit = Circuit(2, "bell_pair")
        circuit.h(0)
        circuit.cnot(0, 1)
        return circuit
        
    def _create_ghz(self, num_qubits: int = 3) -> Circuit:
        """Create GHZ state: (|00...0> + |11...1>)/sqrt(2)."""
        if num_qubits < 2:
            num_qubits = 3
        circuit = Circuit(num_qubits, "ghz")
        circuit.h(0)
        for i in range(1, num_qubits):
            circuit.cnot(0, i)
        return circuit
        
    def _create_qft(self, num_qubits: int = 3) -> Circuit:
        """Create Quantum Fourier Transform circuit."""
        if num_qubits < 2:
            num_qubits = 3
        circuit = Circuit(num_qubits, "qft")
        
        for i in range(num_qubits):
            circuit.h(i)
            for j in range(i+1, num_qubits):
                # CRZ with angle pi/2^(j-i)
                angle = 3.14159 / (2**(j-i))
                circuit.rz(j, angle)
                
        return circuit
        
    def _create_vqe(self, num_qubits: int = 2) -> Circuit:
        """Create VQE ansatz circuit."""
        if num_qubits < 2:
            num_qubits = 2
        circuit = Circuit(num_qubits, "vqe")
        
        # Layer of rotations
        for q in range(num_qubits):
            circuit.ry(q, 0.5)  # Default parameter
            
        # Layer of entanglers
        for q in range(num_qubits - 1):
            circuit.cnot(q, q + 1)
            
        return circuit
        
    def _create_grover(self, num_qubits: int = 2) -> Circuit:
        """Create Grover's algorithm circuit."""
        if num_qubits < 2:
            num_qubits = 2
        circuit = Circuit(num_qubits, "grover")
        
        # Initialize superposition
        for q in range(num_qubits):
            circuit.h(q)
            
        # Oracle (mark |11...1>)
        if num_qubits == 1:
            circuit.z(0)
        elif num_qubits == 2:
            circuit.cz(0, 1)
        else:
            for q in range(num_qubits - 1):
                circuit.cnot(q, num_qubits - 1)
            circuit.z(num_qubits - 1)
            for q in range(num_qubits - 2, -1, -1):
                circuit.cnot(q, num_qubits - 1)
                
        # Diffuser
        for q in range(num_qubits):
            circuit.h(q)
            circuit.x(q)
        # Multi-Z (simplified)
        if num_qubits >= 2:
            circuit.cz(0, 1)
        for q in range(num_qubits):
            circuit.x(q)
            circuit.h(q)
            
        return circuit
        
    def _create_superposition(self, num_qubits: int = 2) -> Circuit:
        """Create uniform superposition."""
        circuit = Circuit(num_qubits, "superposition")
        for q in range(num_qubits):
            circuit.h(q)
        return circuit
        
    def _create_entanglement(self, num_qubits: int = 2) -> Circuit:
        """Create entangled pairs."""
        if num_qubits < 2:
            num_qubits = 2
        circuit = Circuit(num_qubits, "entanglement")
        for q in range(0, num_qubits - 1, 2):
            circuit.h(q)
            circuit.cnot(q, q + 1)
        return circuit
        
    def analyze_requirements(self, description: str) -> Dict[str, Any]:
        """Analyze description and extract requirements."""
        return {
            'num_qubits': self._extract_num_qubits(description),
            'circuit_type': self._extract_type(description),
            'parameters': self._extract_params(description)
        }
        
    def _extract_num_qubits(self, desc: str) -> int:
        """Extract number of qubits from description."""
        words = desc.lower().split()
        for i, word in enumerate(words):
            if 'qubit' in word and i > 0:
                try:
                    return int(words[i-1])
                except:
                    pass
        return 2  # Default
        
    def _extract_type(self, desc: str) -> str:
        """Extract circuit type from description."""
        desc_lower = desc.lower()
        for key in self.templates.keys():
            if key in desc_lower:
                return key
        return 'superposition'
        
    def _extract_params(self, desc: str) -> Dict:
        """Extract parameters from description."""
        return {}  # Simplified
