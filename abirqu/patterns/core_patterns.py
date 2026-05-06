"""
Quantum Design Patterns for AbirQu
Copyright 2026 Abir Maheshwari

Implements reusable quantum circuit patterns.
"""
import numpy as np
from typing import Dict, Any, List, Optional, Set
from ..core.circuit import Circuit
from ..core.gates import H, CNOT, X, Z, ry

class QuantumPattern:
    """Base class for quantum design patterns."""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.applied_count = 0
        
    def apply(self, circuit: Circuit, qubits: List[int]) -> Circuit:
        """Apply pattern to circuit on specified qubits."""
        raise NotImplementedError("Subclasses must implement apply()")
        
    def validate(self, circuit: Circuit, qubits: List[int]) -> bool:
        """Validate that pattern can be applied."""
        return all(0 <= q < circuit.num_qubits for q in qubits)
        
    def get_gate_count(self) -> int:
        """Return number of gates this pattern adds."""
        return 0
        
    def __repr__(self):
        return f"QuantumPattern({self.name})"

class InitializationPattern(QuantumPattern):
    """Initialize qubits to a specific state."""
    
    def __init__(self):
        super().__init__("Initialization", "Initialize qubits to |0> or |1>")
        
    def apply(self, circuit: Circuit, qubits: List[int], state: int = 0) -> Circuit:
        """Initialize qubits to |0> or |1>."""
        if not self.validate(circuit, qubits):
            raise ValueError("Invalid qubits")
            
        for q in qubits:
            if state == 1:
                circuit.x(q)
        self.applied_count += 1
        return circuit
        
    def get_gate_count(self) -> int:
        return 1  # X gate if state=1

class SuperpositionPattern(QuantumPattern):
    """Create superposition using Hadamard gates."""
    
    def __init__(self):
        super().__init__("Superposition", "Create uniform superposition")
        
    def apply(self, circuit: Circuit, qubits: List[int]) -> Circuit:
        """Apply Hadamard to create superposition."""
        if not self.validate(circuit, qubits):
            raise ValueError("Invalid qubits")
            
        for q in qubits:
            circuit.h(q)
        self.applied_count += 1
        return circuit
        
    def get_gate_count(self) -> int:
        return len(qubits)
        
    def create_uniform_superposition(self, circuit: Circuit, qubits: List[int]) -> Circuit:
        """Create uniform superposition over all basis states."""
        return self.apply(circuit, qubits)

class EntanglementPattern(QuantumPattern):
    """Create entanglement between qubits."""
    
    def __init__(self):
        super().__init__("Entanglement", "Create entangled states (Bell pairs, GHZ)")
        
    def apply_bell_pair(self, circuit: Circuit, q1: int, q2: int) -> Circuit:
        """Create Bell pair: (|00> + |11>)/sqrt(2)."""
        if not self.validate(circuit, [q1, q2]):
            raise ValueError("Invalid qubits")
            
        circuit.h(q1)
        circuit.cnot(q1, q2)
        self.applied_count += 1
        return circuit
        
    def apply_ghz(self, circuit: Circuit, qubits: List[int]) -> Circuit:
        """Create GHZ state: (|00...0> + |11...1>)/sqrt(2)."""
        if not self.validate(circuit, qubits) or len(qubits) < 2:
            raise ValueError("Invalid qubits or need at least 2")
            
        circuit.h(qubits[0])
        for i in range(1, len(qubits)):
            circuit.cnot(qubits[0], qubits[i])
        self.applied_count += 1
        return circuit
        
    def apply_cluster_state(self, circuit: Circuit, qubits: List[int]) -> Circuit:
        """Create cluster state for measurement-based QC."""
        # Apply Hadamard to all
        for q in qubits:
            circuit.h(q)
        # Apply CZ between adjacent qubits
        for i in range(len(qubits) - 1):
            # Use CNOT + S + CNOT + S + CNOT for CZ
            q1, q2 = qubits[i], qubits[i+1]
            circuit.cnot(q1, q2)
            circuit.s(q2)
            circuit.cnot(q1, q2)
        self.applied_count += 1
        return circuit
        
    def get_gate_count(self) -> int:
        return 2  # H + CNOT for Bell pair

class OraclePattern(QuantumPattern):
    """Oracle patterns for quantum algorithms (Grover, etc.)."""
    
    def __init__(self):
        super().__init__("Oracle", "Oracle for marking solution states")
        
    def apply_grover_oracle(self, circuit: Circuit, target_state: List[int], 
                           qubits: List[int]) -> Circuit:
        """Mark target state by flipping its phase."""
        if not self.validate(circuit, qubits):
            raise ValueError("Invalid qubits")
            
        # Apply X gates to qubits that should be |0>
        for q, bit in zip(qubits, target_state):
            if bit == 0:
                circuit.x(q)
                
        # Multi-controlled Z (simplified: use Toffoli decomposition)
        if len(qubits) == 1:
            circuit.z(qubits[0])
        elif len(qubits) == 2:
            circuit.cz(qubits[0], qubits[1])
        else:
            # Use multi-controlled Z decomposition
            # Simplified: apply CNOT chain
            for i in range(len(qubits) - 1):
                circuit.cnot(qubits[i], qubits[i+1])
            circuit.z(qubits[-1])
            for i in range(len(qubits) - 2, -1, -1):
                circuit.cnot(qubits[i], qubits[i+1])
                
        # Uncompute X gates
        for q, bit in zip(qubits, target_state):
            if bit == 0:
                circuit.x(q)
                
        self.applied_count += 1
        return circuit
        
    def apply_phase_oracle(self, circuit: Circuit, qubits: List[int], 
                          phase: float = np.pi) -> Circuit:
        """Apply phase oracle: flip phase of |11...1> state."""
        # Apply X to all qubits to flip to |00...0>
        for q in qubits:
            circuit.x(q)
            
        # Multi-controlled Z
        if len(qubits) >= 2:
            circuit.cz(qubits[-2], qubits[-1])
            for i in range(len(qubits) - 2):
                circuit.cnot(qubits[i], qubits[-1])
                
        # Uncompute X
        for q in qubits:
            circuit.x(q)
            
        self.applied_count += 1
        return circuit
        
    def get_gate_count(self) -> int:
        return len(qubits) * 2 + 1  # X + multi-Z + X
