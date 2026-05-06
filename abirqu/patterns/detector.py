"""
Quantum Pattern Detector for AbirQu
Copyright 2026 Abir Maheshwari

Detects known quantum patterns in circuits.
"""
from typing import List, Optional, Dict, Tuple
from ..core.circuit import Circuit
from ..core.gates import Gate

class PatternDetector:
    """Detects known quantum patterns in circuits."""
    
    def __init__(self):
        self.patterns = [
            ('bell_pair', self._is_bell_pair),
            ('ghz_state', self._is_ghz_state),
            ('qft_layer', self._is_qft_layer),
            ('vqe_ansatz', self._is_vqe_ansatz),
            ('grover_oracle', self._is_grover_oracle),
        ]
        
    def detect(self, circuit: Circuit) -> List[str]:
        """Detect patterns in circuit."""
        detected = []
        
        for name, check_func in self.patterns:
            if check_func(circuit):
                detected.append(name)
                
        return detected
        
    def suggest(self, circuit: Circuit) -> Optional[str]:
        """Suggest pattern to apply based on circuit structure."""
        gate_counts = circuit.count_gates()
        
        # Count two-qubit gates
        two_qubit_count = sum(gate_counts.get(g, 0) for g in ['CNOT', 'CZ', 'SWAP'])
        
        if two_qubit_count == 0 and len(circuit.gates) > 2:
            return "superposition"  # Suggest adding entanglement
        elif two_qubit_count > 0 and 'H' not in gate_counts:
            return "bell_pair"  # Suggest creating Bell pair
        elif circuit.depth() > 10:
            return "optimize"  # Suggest optimization
        else:
            return None
            
    def analyze_structure(self, circuit: Circuit) -> Dict[str, Any]:
        """Analyze circuit structure and return metrics."""
        gate_counts = circuit.count_gates()
        
        return {
            'num_qubits': circuit.num_qubits,
            'num_gates': len(circuit.gates),
            'depth': circuit.depth(),
            'gate_types': gate_counts,
            'two_qubit_ratio': self._two_qubit_ratio(gate_counts),
            'single_qubit_ratio': self._single_qubit_ratio(gate_counts),
            'detected_patterns': self.detect(circuit)
        }
        
    def _two_qubit_ratio(self, gate_counts: Dict) -> float:
        """Calculate ratio of two-qubit gates."""
        two_qubit = sum(gate_counts.get(g, 0) for g in ['CNOT', 'CZ', 'SWAP', 'CRX'])
        total = sum(gate_counts.values())
        return two_qubit / max(total, 1)
        
    def _single_qubit_ratio(self, gate_counts: Dict) -> float:
        """Calculate ratio of single-qubit gates."""
        single_qubit = sum(gate_counts.get(g, 0) for g in ['X', 'Y', 'Z', 'H', 'S', 'T', 'RX', 'RY', 'RZ'])
        total = sum(gate_counts.values())
        return single_qubit / max(total, 1)
        
    def _is_bell_pair(self, circuit: Circuit) -> bool:
        """Check if circuit creates a Bell pair."""
        if len(circuit.gates) != 2:
            return False
            
        # First gate should be H on qubit 0
        gate1, qubits1 = circuit.gates[0]
        if gate1.name != 'H' or qubits1[0] != 0:
            return False
            
        # Second gate should be CNOT(0, 1)
        gate2, qubits2 = circuit.gates[1]
        if gate2.name != 'CNOT' or qubits2 != [0, 1]:
            return False
            
        return True
        
    def _is_ghz_state(self, circuit: Circuit) -> bool:
        """Check if circuit creates GHZ state."""
        if len(circuit.gates) < 2:
            return False
            
        # First gate should be H on qubit 0
        gate1, qubits1 = circuit.gates[0]
        if gate1.name != 'H':
            return False
            
        # Subsequent gates should be CNOTs from qubit 0
        for i in range(1, len(circuit.gates)):
            gate, qubits = circuit.gates[i]
            if gate.name != 'CNOT' or qubits[0] != 0:
                return False
                
        return True
        
    def _is_qft_layer(self, circuit: Circuit) -> bool:
        """Check if circuit contains QFT layer."""
        # Look for Hadamard followed by controlled rotations
        has_h = False
        has_crot = False
        
        for gate, qubits in circuit.gates:
            if gate.name == 'H':
                has_h = True
            if 'RZ' in gate.name or 'C' in gate.name:
                has_crot = True
                
        return has_h and has_crot
        
    def _is_vqe_ansatz(self, circuit: Circuit) -> bool:
        """Check if circuit looks like VQE ansatz."""
        # VQE typically has alternating layers of single-qubit + CNOTs
        has_single = False
        has_cnot = False
        
        for gate, qubits in circuit.gates:
            name = gate.name.split('(')[0]
            if name in ['RX', 'RY', 'RZ', 'H']:
                has_single = True
            if name == 'CNOT':
                has_cnot = True
                
        return has_single and has_cnot
        
    def _is_grover_oracle(self, circuit: Circuit) -> bool:
        """Check if circuit is a Grover oracle."""
        # Oracle typically has X gates followed by multi-controlled Z
        has_x = any(gate.name == 'X' for gate, _ in circuit.gates)
        has_multiqubit = len(circuit.gates) > 0 and len(circuit.gates[-1][1]) > 1
        return has_x and has_multiqubit
