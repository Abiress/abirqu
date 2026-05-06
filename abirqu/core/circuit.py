"""
Quantum Circuit DSL for AbirQu
Copyright 2026 Abir Maheshwari
"""
from typing import List, Optional, Dict, Any, Tuple
from .gates import Gate, X, Y, Z, H, S, T, I, rx, ry, rz, phase, CNOT, CZ, SWAP, CRX, TOFFOLI, FREDKIN

class Circuit:
    """Quantum circuit representation with DSL."""
    
    def __init__(self, num_qubits: int, name: str = ""):
        self.num_qubits = num_qubits
        self.name = name
        self.gates: List[Tuple[Gate, List[int]]] = []
        self.measurements: List[Dict] = []
        self.classical_bits = 0
        
    def add_gate(self, gate: Gate, qubits: Optional[List[int]] = None) -> 'Circuit':
        """Add a gate to the circuit."""
        if qubits is None:
            qubits = gate.qubits
        self.gates.append((gate, qubits))
        return self
        
    def x(self, qubit: int) -> 'Circuit':
        """Apply X gate."""
        return self.add_gate(X._replace(qubits=[qubit]))
        
    def y(self, qubit: int) -> 'Circuit':
        """Apply Y gate."""
        return self.add_gate(Y._replace(qubits=[qubit]))
        
    def z(self, qubit: int) -> 'Circuit':
        """Apply Z gate."""
        return self.add_gate(Z._replace(qubits=[qubit]))
        
    def h(self, qubit: int) -> 'Circuit':
        """Apply H gate."""
        return self.add_gate(H._replace(qubits=[qubit]))
        
    def s(self, qubit: int) -> 'Circuit':
        """Apply S gate."""
        return self.add_gate(S._replace(qubits=[qubit]))
        
    def t(self, qubit: int) -> 'Circuit':
        """Apply T gate."""
        return self.add_gate(T._replace(qubits=[qubit]))
        
    def rx(self, qubit: int, theta: float) -> 'Circuit':
        """Apply RX rotation."""
        return self.add_gate(rx(theta)._replace(qubits=[qubit]))
        
    def ry(self, qubit: int, theta: float) -> 'Circuit':
        """Apply RY rotation."""
        return self.add_gate(ry(theta)._replace(qubits=[qubit]))
        
    def rz(self, qubit: int, theta: float) -> 'Circuit':
        """Apply RZ rotation."""
        return self.add_gate(rz(theta)._replace(qubits=[qubit]))
        
    def phase(self, qubit: int, phi: float) -> 'Circuit':
        """Apply phase gate."""
        return self.add_gate(phase(phi)._replace(qubits=[qubit]))
        
    def cnot(self, control: int, target: int) -> 'Circuit':
        """Apply CNOT gate."""
        return self.add_gate(CNOT(control, target))
        
    def cz(self, control: int, target: int) -> 'Circuit':
        """Apply CZ gate."""
        return self.add_gate(CZ(control, target))
        
    def swap(self, q1: int, q2: int) -> 'Circuit':
        """Apply SWAP gate."""
        return self.add_gate(SWAP(q1, q2))
        
    def crx(self, control: int, target: int, theta: float) -> 'Circuit':
        """Apply CRX gate."""
        return self.add_gate(CRX(control, target, theta))
        
    def toffoli(self, c1: int, c2: int, target: int) -> 'Circuit':
        """Apply Toffoli gate."""
        return self.add_gate(TOFFOLI(c1, c2, target))
        
    def fredkin(self, c1: int, t1: int, t2: int) -> 'Circuit':
        """Apply Fredkin gate."""
        return self.add_gate(FREDKIN(c1, t1, t2))
        
    def measure(self, qubit: int, cbit: Optional[int] = None) -> 'Circuit':
        """Measure qubit into classical bit."""
        if cbit is None:
            cbit = qubit
        self.measurements.append({'qubit': qubit, 'cbit': cbit})
        if cbit >= self.classical_bits:
            self.classical_bits = cbit + 1
        return self
        
    def depth(self) -> int:
        """Calculate circuit depth using topological ordering."""
        if not self.gates:
            return 0
            
        # Track when each qubit becomes free
        qubit_free_time = [0] * self.num_qubits
        max_depth = 0
        
        for gate, qubits in self.gates:
            # Gate can start when all its qubits are free
            start_time = max((qubit_free_time[q] for q in qubits), default=0)
            # Single-qubit gates take 1 unit, multi-qubit take 2
            duration = 1 if len(qubits) == 1 else 2
            end_time = start_time + duration
            
            # Update qubit free times
            for q in qubits:
                qubit_free_time[q] = end_time
                
            max_depth = max(max_depth, end_time)
            
        return max_depth
        
    def count_gates(self) -> Dict[str, int]:
        """Count gates by type."""
        counts = {}
        for gate, _ in self.gates:
            name = gate.name.split('(')[0]  # Remove parameters
            counts[name] = counts.get(name, 0) + 1
        return counts
        
    def to_qasm(self) -> str:
        """Export to OpenQASM 2.0 format."""
        lines = [
            'OPENQASM 2.0;',
            'include "qelib1.inc";',
            f'qreg q[{self.num_qubits}];',
            f'creg c[{max(self.classical_bits, 1)}];'
        ]
        
        for gate, qubits in self.gates:
            if len(qubits) == 1:
                lines.append(f"{gate.name} q[{qubits[0]}];")
            elif len(qubits) == 2:
                lines.append(f"{gate.name} q[{qubits[0]}],q[{qubits[1]}];")
            elif len(qubits) == 3:
                lines.append(f"{gate.name} q[{qubits[0]}],q[{qubits[1]}],q[{qubits[2]}];")
                
        for m in self.measurements:
            lines.append(f"measure q[{m['qubit']}] -> c[{m['cbit']}];")
            
        return '\n'.join(lines)
        
    def __repr__(self):
        return f"Circuit({self.name}, qubits={self.num_qubits}, gates={len(self.gates)}, depth={self.depth()})"
