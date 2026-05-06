"""
Hardware-Aware Transpiler for AbirQu
Copyright 2026 Abir Maheshwari

Transpiles circuits for specific quantum hardware.
"""
import numpy as np
from typing import List, Dict, Optional, Set, Tuple
from ..core.circuit import Circuit
from ..core.gates import Gate, X, Y, Z, H, S, T, rx, ry, rz, CNOT, CZ, SWAP

class HardwareAwareTranspiler:
    """Transpiles circuits for specific quantum hardware."""
    
    # Native gate sets for different backends
    GATE_SETS = {
        'IBM': {
            'single': ['ID', 'X', 'SX', 'RZ', 'S', 'T', 'H'],
            'two': ['CNOT', 'CZ'],
            'basis': ['SX', 'RZ', 'CNOT']  # Native basis
        },
        'Google': {
            'single': ['X', 'Y', 'Z', 'H', 'S', 'T', 'RX', 'RY', 'RZ'],
            'two': ['CZ', 'iSWAP'],
            'basis': ['X', 'RZ', 'CZ']  # Native basis (Sycamore)
        },
        'IonQ': {
            'single': ['X', 'Y', 'Z', 'H', 'S', 'T', 'RX', 'RY', 'RZ'],
            'two': ['XX', 'YY', 'ZZ'],
            'basis': ['GPi', 'GPi2', 'MS']  # Native basis
        },
        'generic': {
            'single': ['X', 'Y', 'Z', 'H', 'S', 'T', 'RX', 'RY', 'RZ'],
            'two': ['CNOT', 'CZ', 'SWAP'],
            'basis': ['X', 'RZ', 'CNOT']
        }
    }
    
    def __init__(self, backend: str = "generic"):
        self.backend = backend
        self.gate_set = self.GATE_SETS.get(backend, self.GATE_SETS['generic'])
        self.coupling_map: Optional[List[Tuple[int, int]]] = None
        
    def set_coupling_map(self, coupling: List[Tuple[int, int]]):
        """Set hardware connectivity constraints."""
        self.coupling_map = coupling
        
    def _get_gate_set(self) -> List[str]:
        """Get native gate set for target backend."""
        return self.gate_set['basis']
        
    def transpile(self, circuit: Circuit) -> 'TranspiledCircuit':
        """Transpile circuit to native gates."""
        transpiled = Circuit(circuit.num_qubits, f"{circuit.name}_transpiled")
        
        for gate, qubits in circuit.gates:
            name = gate.name.split('(')[0]
            
            if name in self.gate_set['basis']:
                # Already native
                transpiled.add_gate(gate, qubits)
            else:
                # Decompose to basis gates
                decomposed = self._decompose_to_basis(gate, qubits)
                for g, q in decomposed:
                    transpiled.add_gate(g, q)
                    
        # Handle connectivity constraints
        if self.coupling_map:
            transpiled = self._apply_routing(transpiled)
            
        return TranspiledCircuit(circuit, transpiled, self.backend)
        
    def _decompose_to_basis(self, gate: Gate, qubits: List[int]) -> List[Tuple[Gate, List[int]]]:
        """Decompose non-native gate to basis gates."""
        name = gate.name.split('(')[0]
        
        if name == 'H':
            # H = RZ(pi/2) * SX * RZ(pi/2) (IBM decomposition)
            if self.backend == 'IBM':
                rz_gate1 = rz(np.pi/2)
                rz_gate1.qubits = [qubits[0]]
                sx_matrix = np.array([[1,1],[1,-1]], dtype=complex)/np.sqrt(2)
                sx_gate = Gate('SX', sx_matrix, [qubits[0]])
                rz_gate2 = rz(np.pi/2)
                rz_gate2.qubits = [qubits[0]]
                return [(rz_gate1, [qubits[0]]), (sx_gate, [qubits[0]]), (rz_gate2, [qubits[0]])]
            else:
                return [(gate, qubits)]
                
        elif name == 'T':
            # T = RZ(pi/4)
            return [(rz(np.pi/4)._replace(qubits=qubits), qubits)]
            
        elif name == 'S':
            # S = RZ(pi/2)
            return [(rz(np.pi/2)._replace(qubits=qubits), qubits)]
            
        elif name == 'SWAP':
            # SWAP = CNOT(a,b) * CNOT(b,a) * CNOT(a,b)
            q0, q1 = qubits
            return [
                (CNOT()._replace(qubits=[q0, q1]), [q0, q1]),
                (CNOT()._replace(qubits=[q1, q0]), [q1, q0]),
                (CNOT()._replace(qubits=[q0, q1]), [q0, q1])
            ]
            
        elif name in ['RX', 'RY']:
            # Convert to RZ basis
            # RX(theta) = H * RZ(theta) * H
            return [
                (H._replace(qubits=qubits), qubits),
                (rz(float(gate.name.split('(')[1].split(')')[0]))._replace(qubits=qubits), qubits),
                (H._replace(qubits=qubits), qubits)
            ]
            
        return [(gate, qubits)]
        
    def _apply_routing(self, circuit: Circuit) -> Circuit:
        """Apply routing to satisfy connectivity constraints."""
        # Simplified: add SWAP gates when needed
        if not self.coupling_map:
            return circuit
            
        # Build adjacency set
        connected = set()
        for q1, q2 in self.coupling_map:
            connected.add((q1, q2))
            connected.add((q2, q1))
            
        routed = Circuit(circuit.num_qubits, circuit.name)
        
        for gate, qubits in circuit.gates:
            if len(qubits) == 2:
                q1, q2 = qubits
                if (q1, q2) not in connected:
                    # Need to route - simplified: assume linear topology
                    # Add SWAPs to bring qubits together
                    pass  # Full implementation would add SWAP chain
            routed.add_gate(gate, qubits)
            
        return routed
        
    def set_backend(self, backend: str):
        self.backend = backend
        self.gate_set = self.GATE_SETS.get(backend, self.GATE_SETS['generic'])
        
    def get_native_gates(self) -> List[str]:
        return self.gate_set['basis']

class TranspiledCircuit:
    def __init__(self, original: Circuit, transpiled: Circuit, backend: str):
        self.original = original
        self.transpiled = transpiled
        self.backend = backend
        
    def __repr__(self):
        return f"TranspiledCircuit(backend={self.backend}, gates={len(self.transpiled.gates)})"
