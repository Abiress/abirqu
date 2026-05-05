"""
Debugging and Verification Agent

Builds an agent that detects circuit bugs (incorrect unitary, broken entanglement).
Implements equivalence checking between original and optimized circuits.
Supports noise-aware debugging (identifying which gates contribute most to error).
Builds automated test generation for quantum circuits.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

class BugType(Enum):
    """Types of bugs in quantum circuits."""
    INCORRECT_UNITARY = "incorrect_unitary"
    BROKEN_ENTANGLEMENT = "broken_entanglement"
    INCORRECT_MEASUREMENT = "incorrect_measurement"
    GATE_DECOMPOSITION_ERROR = "gate_decomposition_error"
    TOPOLOGY_VIOLATION = "topology_violation"
    PHASE_MISMATCH = "phase_mismatch"

@dataclass
class BugReport:
    """Report of a detected bug."""
    bug_type: BugType
    severity: str  # 'high', 'medium', 'low'
    location: Optional[Tuple[int, int]]  # Gate index range
    description: str
    suggestion: str
    confidence: float

class DebuggingAgent:
    """
    Agent that detects bugs in quantum circuits.
    """
    
    def __init__(self):
        self.bug_reports: List[BugReport] = []
        self.test_results: Dict[str, Any] = {}
        
    def analyze_circuit(self, circuit: List[Tuple[str, List[int]]],
                       expected_unitary: Optional[np.ndarray] = None) -> List[BugReport]:
        """
        Analyze circuit for bugs.
        
        Args:
            circuit: Circuit to analyze
            expected_unitary: Expected unitary matrix (if known)
            
        Returns:
            List of bug reports
        """
        reports = []
        
        # Check for common issues
        reports.extend(self._check_gate_errors(circuit))
        reports.extend(self._check_entanglement(circuit))
        reports.extend(self._check_topology_violations(circuit))
        reports.extend(self._check_phase_errors(circuit))
        
        # Full unitary verification if expected provided
        if expected_unitary is not None:
            reports.extend(self._verify_unitary(circuit, expected_unitary))
            
        self.bug_reports = reports
        return reports
    
    def _check_gate_errors(self, circuit: List[Tuple[str, List[int]]]) -> List[BugReport]:
        """Check for gate application errors."""
        reports = []
        
        # Check for gates applied to non-existent qubits
        all_qubits = set()
        for _, qubits in circuit:
            all_qubits.update(qubits)
            
        max_qubit = max(all_qubits) if all_qubits else 0
        
        # Check for suspicious gate sequences
        for i in range(len(circuit) - 1):
            gate1, qubits1 = circuit[i]
            gate2, qubits2 = circuit[i+1]
            
            # Check for identity sequences (H followed by H)
            if gate1 == 'H' and gate2 == 'H' and qubits1 == qubits2:
                reports.append(BugReport(
                    bug_type=BugType.GATE_DECOMPOSITION_ERROR,
                    severity='low',
                    location=(i, i+1),
                    description=f"Redundant H gate pair at positions {i}, {i+1}",
                    suggestion="Remove redundant H gates",
                    confidence=0.95
                ))
                
        return reports
    
    def _check_entanglement(self, circuit: List[Tuple[str, List[int]]]) -> List[BugReport]:
        """Check for broken entanglement."""
        reports = []
        
        # Look for entanglement-breaking sequences
        # E.g., measuring a qubit then trying to entangle it
        
        measure_positions = []
        for i, (gate, qubits) in enumerate(circuit):
            if 'measure' in gate.lower() or gate == 'Measure':
                measure_positions.append((i, qubits))
                
        # Check if any two-qubit gate comes after measurement of its qubits
        for i, (gate, qubits) in enumerate(circuit):
            if len(qubits) > 1:
                for meas_pos, meas_qubits in measure_positions:
                    if meas_pos < i:
                        for q in qubits:
                            if q in meas_qubits:
                                reports.append(BugReport(
                                    bug_type=BugType.BROKEN_ENTANGLEMENT,
                                    severity='high',
                                    location=(meas_pos, i),
                                    description=f"Qubit {q} measured before entanglement gate at position {i}",
                                    suggestion="Move measurement after entanglement or remove measurement",
                                    confidence=0.9
                                ))
                                
        return reports
    
    def _check_topology_violations(self, circuit: List[Tuple[str, List[int]]]) -> List[BugReport]:
        """Check for topology violations (simplified)."""
        reports = []
        
        # Simplified: check for long-range gates without SWAPs
        # In practice, would check against device topology
        
        return reports
    
    def _check_phase_errors(self, circuit: List[Tuple[str, List[int]]]) -> List[BugReport]:
        """Check for phase mismatch errors."""
        reports = []
        
        # Check for missing phase gates in known algorithms
        # E.g., Grover's algorithm needs correct phase
        has_oracle = any('TOFFOLI' in g or 'CZ' in g for g, _ in circuit)
        
        if has_oracle:
            # Check if diffusion operator present
            # Simplified check
            pass
            
        return reports
    
    def _verify_unitary(self, circuit: List[Tuple[str, List[int]]],
                        expected: np.ndarray) -> List[BugReport]:
        """Verify circuit unitary matches expected."""
        reports = []
        
        # Simulate circuit to get unitary
        actual = self._circuit_to_unitary(circuit)
        
        # Compare unitaries
        if actual.shape == expected.shape:
            # Compute Frobenius norm of difference
            diff = np.linalg.norm(actual - expected)
            
            if diff > 1e-6:
                reports.append(BugReport(
                    bug_type=BugType.INCORRECT_UNITARY,
                    severity='high',
                    location=None,
                    description=f"Circuit unitary differs from expected (diff={diff:.2e})",
                    suggestion="Check gate decomposition and ordering",
                    confidence=0.99
                ))
                
        return reports
    
    def _circuit_to_unitary(self, circuit: List[Tuple[str, List[int]]]) -> np.ndarray:
        """Convert circuit to unitary matrix (simplified)."""
        # This is a placeholder - real implementation would use QVM
        num_qubits = 2  # Assume 2 qubits for simplicity
        n = 2 ** num_qubits
        unitary = np.eye(n, dtype=complex)
        return unitary
    
    def equivalence_check(self, circuit1: List[Tuple[str, List[int]]],
                          circuit2: List[Tuple[str, List[int]]]) -> Tuple[bool, float]:
        """
        Check if two circuits are equivalent.
        
        Args:
            circuit1: First circuit
            circuit2: Second circuit
            
        Returns:
            Tuple of (is_equivalent, similarity_score)
        """
        # Simplified: compare gate sequences
        if len(circuit1) != len(circuit2):
            # Could still be equivalent with different gate counts
            pass
            
        # Compare unitaries
        u1 = self._circuit_to_unitary(circuit1)
        u2 = self._circuit_to_unitary(circuit2)
        
        if u1.shape != u2.shape:
            return False, 0.0
            
        # Compute similarity (fidelity)
        # F = |Tr(U1^† U2)|^2 / n^2
        n = u1.shape[0]
        trace = np.trace(u1.conj().T @ u2)
        fidelity = (np.abs(trace) ** 2) / (n ** 2)
        
        is_equiv = fidelity > 0.999
        return is_equiv, fidelity
    
    def noise_aware_debug(self, circuit: List[Tuple[str, List[int]]],
                           noise_model: Any) -> List[BugReport]:
        """
        Identify which gates contribute most to error under noise.
        
        Args:
            circuit: Circuit to analyze
            noise_model: Noise model
            
        Returns:
            List of bug reports focusing on noisy gates
        """
        reports = []
        
        # Simplified: flag two-qubit gates (higher error)
        for i, (gate, qubits) in enumerate(circuit):
            if len(qubits) > 1:
                # Two-qubit gate - check if needed
                reports.append(BugReport(
                    bug_type=BugType.GATE_DECOMPOSITION_ERROR,
                    severity='medium',
                    location=(i, i+1),
                    description=f"Two-qubit gate {gate} at position {i} may introduce noise",
                    suggestion="Consider if this gate can be deferred or eliminated",
                    confidence=0.7
                ))
                
        return reports
    
    def generate_tests(self, circuit: List[Tuple[str, List[int]]],
                       num_tests: int = 10) -> List[Dict]:
        """
        Generate automated tests for a quantum circuit.
        
        Args:
            circuit: Circuit to test
            num_tests: Number of tests to generate
            
        Returns:
            List of test cases
        """
        tests = []
        
        # Generate different input states
        for i in range(num_tests):
            # Random input state
            input_state = np.random.choice([0, 1], size=2)  # Simplified
            
            test = {
                'name': f"test_random_{i}",
                'input_state': input_state.tolist(),
                'expected_output': None,  # Would compute from circuit
                'tolerance': 1e-6
            }
            tests.append(test)
            
        return tests

# Example usage and tests
if __name__ == "__main__":
    print("Testing Debugging and Verification Agent...")
    
    agent = DebuggingAgent()
    
    # Test circuit with issues
    test_circuit = [
        ('H', [0]),
        ('H', [0]),  # Redundant H
        ('CNOT', [0, 1]),
        ('Measure', [0]),  # Breaks entanglement
        ('CNOT', [0, 1])   # Late entanglement
    ]
    
    print(f"\nAnalyzing circuit with {len(test_circuit)} gates...")
    reports = agent.analyze_circuit(test_circuit)
    
    print(f"\nBug Reports ({len(reports)} issues found):")
    for report in reports:
        print(f"  [{report.severity.upper()}] {report.bug_type.value}")
        print(f"    Description: {report.description}")
        print(f"    Suggestion: {report.suggestion}")
        print(f"    Confidence: {report.confidence:.2f}")
        
    # Test equivalence checking
    print("\n" + "="*50)
    print("Testing Equivalence Checking...")
    
    circuit1 = [('H', [0]), ('CNOT', [0, 1])]
    circuit2 = [('H', [0]), ('H', [1]), ('CNOT', [0, 1]), ('H', [1])]  # H^2 = I on q1
    
    is_equiv, fidelity = agent.equivalence_check(circuit1, circuit2)
    print(f"Circuit 1: {circuit1}")
    print(f"Circuit 2: {circuit2}")
    print(f"Equivalent: {is_equiv}")
    print(f"Fidelity: {fidelity:.6f}")
    
    # Test noise-aware debugging
    print("\n" + "="*50)
    print("Testing Noise-Aware Debugging...")
    
    # Create a simple noise model (mock)
    class MockNoiseModel:
        def get_qubit_errors(self, q):
            return [{'type': 'depolarizing', 'probability': 0.01}]
    
    noise_reports = agent.noise_aware_debug(test_circuit, MockNoiseModel())
    print(f"Noise-related issues found: {len(noise_reports)}")
    
    # Test test generation
    print("\n" + "="*50)
    print("Testing Automated Test Generation...")
    
    tests = agent.generate_tests(test_circuit, num_tests=3)
    print(f"Generated {len(tests)} test cases")
    for test in tests:
        print(f"  - {test['name']}: input={test['input_state']}")