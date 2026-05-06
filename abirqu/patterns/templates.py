"""
Quantum Pattern Templates for AbirQu
Copyright 2026 Abir Maheshwari

Templates for common quantum algorithms (VQE, QAOA, Grover's).
"""
import numpy as np
from typing import List, Dict, Any, Callable
from ..core.circuit import Circuit
from ..core.gates import rx, ry, rz, CNOT, H

class VQETemplate:
    """Variational Quantum Eigensolver template."""
    
    def __init__(self, num_qubits: int = 2):
        self.num_qubits = num_qubits
        self.ansatz_type = "hardware-efficient"  # or "UCC"
        
    def build_ansatz(self, params: np.ndarray) -> Circuit:
        """Build VQE ansatz circuit."""
        circuit = Circuit(self.num_qubits, "vqe_ansatz")
        
        if self.ansatz_type == "hardware-efficient":
            # Layer of single-qubit rotations
            param_idx = 0
            for q in range(self.num_qubits):
                if param_idx < len(params):
                    circuit.ry(q, params[param_idx])
                    param_idx += 1
                    
            # Layer of entangling gates
            for q in range(self.num_qubits - 1):
                circuit.cnot(q, q + 1)
                
            # Second layer of rotations
            for q in range(self.num_qubits):
                if param_idx < len(params):
                    circuit.rz(q, params[param_idx])
                    param_idx += 1
                    
        elif self.ansatz_type == "UCC":
            # Unitary Coupled Cluster ansatz (simplified)
            # exp(-i * theta * (a†b - ab†))
            for q in range(self.num_qubits - 1):
                if param_idx < len(params):
                    # CNOT + Ry + CNOT decomposition
                    circuit.cnot(q, q + 1)
                    circuit.ry(q + 1, params[param_idx])
                    circuit.cnot(q, q + 1)
                    param_idx += 1
                    
        return circuit
        
    def build_hamiltonian(self) -> List[Dict]:
        """Build Hamiltonian terms (simplified)."""
        # For H2 molecule: H = g0 * I + g1 * Z0 + g2 * Z1 + g3 * Z0Z1
        terms = [
            {'paulis': '', 'coeff': -1.0524},  # Identity
            {'paulis': 'Z', 'qubits': [0], 'coeff': 0.3979},
            {'paulis': 'Z', 'qubits': [1], 'coeff': -0.3979},
            {'paulis': 'Z', 'qubits': [0, 1], 'coeff': 0.0113},
        ]
        return terms
        
    def measure_expectation(self, circuit: Circuit, hamiltonian: List[Dict]) -> Circuit:
        """Add measurements for expectation value estimation."""
        # Add measurements in appropriate bases
        for term in hamiltonian:
            if 'X' in term.get('paulis', ''):
                # Measure in X basis: H before measurement
                for q in term.get('qubits', []):
                    circuit.h(q)
            elif 'Y' in term.get('paulis', ''):
                # Measure in Y basis: Rz(-pi/2) * H before measurement
                for q in term.get('qubits', []):
                    circuit.rz(q, -np.pi/2)
                    circuit.h(q)
                    
        return circuit
        
    def __repr__(self):
        return f"VQETemplate(qubits={self.num_qubits}, type={self.ansatz_type})"

class QAOATemplate:
    """Quantum Approximate Optimization Algorithm template."""
    
    def __init__(self, num_qubits: int = 2):
        self.num_qubits = num_qubits
        self.depth: int = 1  # Number of QAOA layers
        
    def build_circuit(self, params: np.ndarray) -> Circuit:
        """Build QAOA circuit with p layers."""
        circuit = Circuit(self.num_qubits, "qaoa")
        
        # Initial superposition
        for q in range(self.num_qubits):
            circuit.h(q)
            
        # QAOA layers
        params_per_layer = 2  # gamma (cost) + beta (mixer)
        p = len(params) // params_per_layer
        
        for layer in range(p):
            # Cost Hamiltonian evolution (exp(-i * gamma * C))
            gamma = params[layer * params_per_layer]
            circuit = self._apply_cost_hamiltonian(circuit, gamma)
            
            # Mixer Hamiltonian evolution (exp(-i * beta * B))
            beta = params[layer * params_per_layer + 1]
            circuit = self._apply_mixer_hamiltonian(circuit, beta)
            
        return circuit
        
    def _apply_cost_hamiltonian(self, circuit: Circuit, gamma: float) -> Circuit:
        """Apply cost Hamiltonian: exp(-i * gamma * sum(Z_i Z_j))."""
        # Simplified: use RZ for single-qubit terms, CNOT-RZ-CNOT for two-qubit
        for q in range(self.num_qubits):
            circuit.rz(q, 2 * gamma)  # Single-qubit Z term
            
        # Two-qubit ZZ terms (for MaxCut problem)
        for q in range(self.num_qubits - 1):
            # ZZ = CNOT - RZ(2*gamma) - CNOT
            circuit.cnot(q, q + 1)
            circuit.rz(q + 1, -2 * gamma)
            circuit.cnot(q, q + 1)
            
        return circuit
        
    def _apply_mixer_hamiltonian(self, circuit: Circuit, beta: float) -> Circuit:
        """Apply mixer Hamiltonian: exp(-i * beta * sum(X_i))."""
        for q in range(self.num_qubits):
            circuit.rx(q, 2 * beta)
        return circuit
        
    def get_default_problem(self) -> Dict:
        """Return default MaxCut problem graph."""
        return {
            'nodes': list(range(self.num_qubits)),
            'edges': [(i, i+1) for i in range(self.num_qubits - 1)]
        }
        
    def __repr__(self):
        return f"QAOATemplate(qubits={self.num_qubits}, depth={self.depth})"

class GroversTemplate:
    """Grover's algorithm template."""
    
    def __init__(self, num_items: int = 4):
        self.num_items = num_items
        self.num_qubits = int(np.ceil(np.log2(num_items)))
        
    def build_oracle(self, target: int) -> Circuit:
        """Build oracle that marks target state."""
        circuit = Circuit(self.num_qubits, "grover_oracle")
        
        # Convert target to binary
        binary = format(target, f'0{self.num_qubits}b')
        
        # Apply X to qubits that should be 0
        for i, bit in enumerate(binary):
            if bit == '0':
                circuit.x(i)
                
        # Multi-controlled Z gate (simplified: use CNOT chain)
        if self.num_qubits == 1:
            circuit.z(0)
        elif self.num_qubits == 2:
            circuit.cz(0, 1)
        else:
            # Use Toffoli decomposition for 3+ qubits
            # Simplified: apply CNOT chain + Z on last qubit
            for i in range(self.num_qubits - 1):
                circuit.cnot(i, self.num_qubits - 1)
            circuit.z(self.num_qubits - 1)
            for i in range(self.num_qubits - 2, -1, -1):
                circuit.cnot(i, self.num_qubits - 1)
                
        # Uncompute X gates
        for i, bit in enumerate(binary):
            if bit == '0':
                circuit.x(i)
                    
        return circuit
        
    def build_diffuser(self) -> Circuit:
        """Build diffuser: 2|s><s| - I."""
        circuit = Circuit(self.num_qubits, "grover_diffuser")
        
        # Apply H to all qubits
        for q in range(self.num_qubits):
            circuit.h(q)
            
        # Apply X to all qubits
        for q in range(self.num_qubits):
            circuit.x(q)
                
        # Multi-controlled Z (same as oracle)
        if self.num_qubits == 1:
            circuit.z(0)
        elif self.num_qubits == 2:
            circuit.cz(0, 1)
        else:
            for i in range(self.num_qubits - 1):
                circuit.cnot(i, self.num_qubits - 1)
            circuit.z(self.num_qubits - 1)
            for i in range(self.num_qubits - 2, -1, -1):
                circuit.cnot(i, self.num_qubits - 1)
                
        # Uncompute X and H
        for q in range(self.num_qubits):
            circuit.x(q)
            circuit.h(q)
                
        return circuit
        
    def run(self, target: int, iterations: Optional[int] = None) -> Circuit:
        """Build complete Grover's algorithm circuit."""
        if iterations is None:
            # Optimal number of iterations
            N = 2**self.num_qubits
            iterations = int(np.round(np.pi / 4 * np.sqrt(N)))
            
        circuit = Circuit(self.num_qubits, "grover")
        
        # Initialize superposition
        for q in range(self.num_qubits):
            circuit.h(q)
            
        # Grover iterations
        for _ in range(iterations):
            circuit = self.build_oracle(target)
            circuit = self.build_diffuser()
            
        return circuit
        
    def __repr__(self):
        return f"GroversTemplate(items={self.num_items}, qubits={self.num_qubits})"
