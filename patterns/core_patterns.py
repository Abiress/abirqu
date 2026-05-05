"""
Quantum Design Patterns Library

Implements the four core patterns as reusable components:
- Initialization pattern
- Superposition pattern  
- Entanglement pattern
- Oracle pattern

Also implements pattern detection engine and pattern-specific optimization rules.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Callable
from enum import Enum

class PatternType(Enum):
    """Types of quantum design patterns."""
    INITIALIZATION = "initialization"
    SUPERPOSITION = "superposition"
    ENTANGLEMENT = "entanglement"
    ORACLE = "oracle"
    MODULARIZATION = "modularization"
    INTEGRATION = "integration"
    TRANSLATION = "translation"

class QuantumPattern:
    """Base class for quantum design patterns."""
    
    def __init__(self, pattern_type: PatternType, name: str, description: str):
        self.pattern_type = pattern_type
        self.name = name
        self.description = description
        self.qubits_needed = 0
        
    def generate_circuit(self, qubits: List[int], **kwargs) -> List[Tuple[str, List[int]]]:
        """
        Generate circuit implementing this pattern.
        
        Args:
            qubits: List of qubit indices to use
            **kwargs: Pattern-specific parameters
            
        Returns:
            List of (gate_name, qubits) tuples
        """
        raise NotImplementedError
        
    def validate(self, circuit: List[Tuple[str, List[int]]], 
                 qubits: List[int]) -> bool:
        """
        Check if a circuit implements this pattern.
        
        Args:
            circuit: Circuit to check
            qubits: Qubits the pattern should use
            
        Returns:
            True if pattern is detected
        """
        raise NotImplementedError

class InitializationPattern(QuantumPattern):
    """
    Initialization Pattern.
    
    Properly initializes qubits to a desired state.
    Common initializations: |0>, |1>, |+>, |->, |+i>, |-i>
    """
    
    def __init__(self):
        super().__init__(
            PatternType.INITIALIZATION,
            "Initialization",
            "Initialize qubits to a specific basis state"
        )
        
    def generate_circuit(self, qubits: List[int], 
                        state: str = '0') -> List[Tuple[str, List[int]]]:
        """
        Generate initialization circuit.
        
        Args:
            qubits: Qubits to initialize
            state: Target state ('0', '1', '+', '-', '+i', '-i')
            
        Returns:
            Circuit gates
        """
        gates = []
        
        for q in qubits:
            if state == '0':
                # Already in |0>, no gates needed
                pass
            elif state == '1':
                gates.append(('X', [q]))
            elif state == '+':
                gates.append(('H', [q]))
            elif state == '-':
                gates.append(('H', [q]))
                gates.append(('Z', [q]))
            elif state == '+i':
                gates.append(('H', [q]))
                gates.append(('S', [q]))
            elif state == '-i':
                gates.append(('H', [q]))
                gates.append(('S_dag', [q]))
            else:
                raise ValueError(f"Unknown state: {state}")
                
        return gates
    
    def validate(self, circuit: List[Tuple[str, List[int]]], 
                qubits: List[int]) -> bool:
        """Check if circuit initializes qubits."""
        # Simple heuristic: check if circuit starts with initialization gates
        if not circuit:
            return False
            
        # Check first gates on each qubit
        first_gates = {}
        for gate, gate_qubits in circuit:
            for q in gate_qubits:
                if q in qubits and q not in first_gates:
                    first_gates[q] = gate
                    
        # If we have initialization gates (X, H, etc.) on all qubits
        init_gates = {'X', 'H', 'S', 'S_dag', 'I'}
        return all(q in first_gates and first_gates[q] in init_gates 
                   for q in qubits)

class SuperpositionPattern(QuantumPattern):
    """
    Superposition Pattern.
    
    Creates superposition states using Hadamard gates.
    Can create uniform superposition over computational basis.
    """
    
    def __init__(self):
        super().__init__(
            PatternType.SUPERPOSITION,
            "Superposition",
            "Create superposition states using Hadamard gates"
        )
        
    def generate_circuit(self, qubits: List[int], 
                        weighted: bool = False,
                        angles: Optional[List[float]] = None) -> List[Tuple[str, List[int]]]:
        """
        Generate superposition circuit.
        
        Args:
            qubits: Qubits to put in superposition
            weighted: If True, use arbitrary rotation angles
            angles: Rotation angles for weighted superposition
            
        Returns:
            Circuit gates
        """
        gates = []
        
        if weighted and angles:
            # Use Ry gates for weighted superposition
            for q, angle in zip(qubits, angles):
                gates.append(('RY', [q, angle]))
        else:
            # Standard uniform superposition with Hadamard
            for q in qubits:
                gates.append(('H', [q]))
                
        return gates
    
    def validate(self, circuit: List[Tuple[str, List[int]]], 
                qubits: List[int]) -> bool:
        """Check if circuit creates superposition."""
        # Look for H gates on the specified qubits
        h_count = 0
        for gate, gate_qubits in circuit:
            if gate == 'H' and any(q in gate_qubits for q in qubits):
                h_count += 1
        return h_count >= len(qubits) * 0.5  # At least half have H

class EntanglementPattern(QuantumPattern):
    """
    Entanglement Pattern.
    
    Creates entangled states (Bell pairs, GHZ states, cluster states).
    """
    
    def __init__(self):
        super().__init__(
            PatternType.ENTANGLEMENT,
            "Entanglement",
            "Create entangled states between qubits"
        )
        
    def generate_circuit(self, qubits: List[int], 
                        entangle_type: str = 'bell') -> List[Tuple[str, List[int]]]:
        """
        Generate entanglement circuit.
        
        Args:
            qubits: Qubits to entangle
            entangle_type: Type of entanglement ('bell', 'ghz', 'cluster', 'graph')
            
        Returns:
            Circuit gates
        """
        gates = []
        
        if entangle_type == 'bell' and len(qubits) >= 2:
            # Create Bell pair: |00> + |11>
            gates.append(('H', [qubits[0]]))
            gates.append(('CNOT', [qubits[0], qubits[1]]))
            
        elif entangle_type == 'ghz' and len(qubits) >= 3:
            # Create GHZ state: |000> + |111>
            gates.append(('H', [qubits[0]]))
            for i in range(1, len(qubits)):
                gates.append(('CNOT', [qubits[0], qubits[i]]))
                
        elif entangle_type == 'cluster':
            # Create cluster state
            for q in qubits:
                gates.append(('H', [q]))
            # Add controlled-Z gates between neighbors
            for i in range(len(qubits) - 1):
                gates.append(('CZ', [qubits[i], qubits[i+1]]))
                
        return gates
    
    def validate(self, circuit: List[Tuple[str, List[int]]], 
                qubits: List[int]) -> bool:
        """Check if circuit creates entanglement."""
        # Look for CNOT or CZ gates involving the qubits
        entangle_gates = {'CNOT', 'CZ', 'TOFFOLI'}
        found = False
        for gate, gate_qubits in circuit:
            if gate in entangle_gates:
                if any(q in gate_qubits for q in qubits):
                    found = True
                    break
        return found

class OraclePattern(QuantumPattern):
    """
    Oracle Pattern.
    
    Implements oracle functions for quantum algorithms (Grover, Deutsch-Jozsa, etc.)
    """
    
    def __init__(self):
        super().__init__(
            PatternType.ORACLE,
            "Oracle",
            "Implement oracle functions for quantum algorithms"
        )
        
    def generate_circuit(self, qubits: List[int], 
                        target: int,
                        oracle_func: Optional[Callable] = None,
                        marked_states: Optional[List[int]] = None) -> List[Tuple[str, List[int]]]:
        """
        Generate oracle circuit.
        
        Args:
            qubits: Input qubits (control qubits)
            target: Target qubit for phase flip
            oracle_func: Function that returns True for marked states
            marked_states: List of marked state indices
            
        Returns:
            Circuit gates
        """
        gates = []
        
        if marked_states:
            # Flip phase for marked states
            for state in marked_states:
                # Convert state to binary
                binary = format(state, f'0{len(qubits)}b')
                
                # Apply X gates to qubits that should be |0>
                x_qubits = []
                for i, bit in enumerate(binary):
                    if bit == '0':
                        x_qubits.append(qubits[i])
                        
                # Apply X gates
                for q in x_qubits:
                    gates.append(('X', [q]))
                    
                # Multi-controlled Z on target
                if len(qubits) == 1:
                    gates.append(('Z', [target]))
                elif len(qubits) == 2:
                    gates.append(('CZ', [qubits[0], target]))
                else:
                    # Use Toffoli-like structure
                    gates.append(('TOFFOLI', qubits + [target]))
                    
                # Uncompute X gates
                for q in x_qubits:
                    gates.append(('X', [q]))
                    
        return gates
    
    def validate(self, circuit: List[Tuple[str, List[int]]], 
                qubits: List[int]) -> bool:
        """Check if circuit contains an oracle (multi-controlled gates)."""
        # Look for multi-qubit gates
        multi_qubit_gates = {'CNOT', 'CZ', 'TOFFOLI', 'MCZ'}
        for gate, gate_qubits in circuit:
            if gate in multi_qubit_gates and len(gate_qubits) > 1:
                if any(q in gate_qubits for q in qubits):
                    return True
        return False

class PatternDetector:
    """
    Engine that detects design patterns in existing circuits.
    """
    
    def __init__(self):
        self.patterns: Dict[PatternType, QuantumPattern] = {
            PatternType.INITIALIZATION: InitializationPattern(),
            PatternType.SUPERPOSITION: SuperpositionPattern(),
            PatternType.ENTANGLEMENT: EntanglementPattern(),
            PatternType.ORACLE: OraclePattern()
        }
        
    def detect_patterns(self, circuit: List[Tuple[str, List[int]]]) -> List[Dict]:
        """
        Detect all patterns in a circuit.
        
        Args:
            circuit: Circuit to analyze
            
        Returns:
            List of detected patterns with metadata
        """
        detected = []
        
        # Get all qubits used
        all_qubits = set()
        for _, qubits in circuit:
            all_qubits.update(qubits)
        all_qubits = sorted(all_qubits)
        
        # Try to detect each pattern type
        for pattern_type, pattern in self.patterns.items():
            # Try different qubit combinations (simplified)
            for num_qubits in [1, 2, 3]:
                if len(all_qubits) >= num_qubits:
                    qubits = all_qubits[:num_qubits]
                    if pattern.validate(circuit, qubits):
                        detected.append({
                            'type': pattern_type.value,
                            'name': pattern.name,
                            'qubits': qubits,
                            'description': pattern.description
                        })
                        
        return detected
    
    def get_pattern_instance(self, pattern_type: PatternType) -> Optional[QuantumPattern]:
        """Get pattern instance by type."""
        return self.patterns.get(pattern_type)

# Example usage and tests
if __name__ == "__main__":
    print("Testing Quantum Design Patterns...")
    
    # Test Initialization Pattern
    print("\n1. Initialization Pattern:")
    init = InitializationPattern()
    circuit = init.generate_circuit([0, 1], state='+')
    print(f"Initialization to |+>: {circuit}")
    
    # Test Superposition Pattern
    print("\n2. Superposition Pattern:")
    superpos = SuperpositionPattern()
    circuit = superpos.generate_circuit([0, 1, 2])
    print(f"Uniform superposition: {circuit}")
    
    # Test Entanglement Pattern
    print("\n3. Entanglement Pattern:")
    entangle = EntanglementPattern()
    circuit = entangle.generate_circuit([0, 1, 2], entangle_type='ghz')
    print(f"GHZ state: {circuit}")
    
    # Test Oracle Pattern
    print("\n4. Oracle Pattern:")
    oracle = OraclePattern()
    circuit = oracle.generate_circuit([0, 1], target=2, marked_states=[3])  # |11>
    print(f"Oracle for |11>: {circuit[:5]}...")  # Show first 5 gates
    
    # Test Pattern Detector
    print("\n5. Pattern Detection:")
    detector = PatternDetector()
    
    # Create test circuit with patterns
    test_circuit = [
        ('H', [0]),
        ('H', [1]),  # Superposition
        ('CNOT', [0, 1]),  # Entanglement
        ('TOFFOLI', [0, 1, 2])  # Oracle-like
    ]
    
    detected = detector.detect_patterns(test_circuit)
    print(f"Detected patterns: {detected}")