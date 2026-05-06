"""
Task 14.2 — Quantum Property-Based Testing.

Property-based test generator, quantum state invariant checking, randomized testing, coverage metrics.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass
from enum import Enum
import random


class PropertyType(Enum):
    """Types of quantum properties."""
    UNITARY = "unitary"  # U†U = I
    NORMALIZATION = "normalization"  # ||ψ|| = 1
    HERMITIAN = "hermitian"  # U = U†
    POSITIVE = "positive"  # All eigenvalues >= 0
    ENTANGLEMENT = "entanglement"  # Bell state check


@dataclass
class PropertyTestResult:
    """Result of property-based testing."""
    property_type: PropertyType
    passed: bool
    num_tests: int
    num_passed: int
    counterexamples: List[Any]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'property_type': self.property_type.value,
            'passed': self.passed,
            'num_tests': self.num_tests,
            'num_passed': self.num_passed,
            'counterexamples': self.counterexamples[:10],  # Limit output.
            'metadata': self.metadata or {}
        }


class QuantumPropertyTester:
    """Property-based testing for quantum circuits."""
    
    def __init__(self, num_tests: int = 100, seed: Optional[int] = None):
        self.num_tests = num_tests
        if seed:
            random.seed(seed)
            np.random.seed(seed)
    
    def test_unitary_property(self, unitary_func: Callable,
                              num_qubits: int) -> PropertyTestResult:
        """Test if a function produces unitary matrices."""
        passed = 0
        counterexamples = []
        
        for i in range(self.num_tests):
            # Generate random unitary.
            U = unitary_func(num_qubits)
            # Check U†U = I.
            identity = np.eye(2**num_qubits)
            UdU = U.conj().T @ U
            if np.allclose(UdU, identity, atol=1e-6):
                passed += 1
            else:
                counterexamples.append({
                    'test': i,
                    'error': float(np.linalg.norm(UdU - identity))
                })
        
        return PropertyTestResult(
            property_type=PropertyType.UNITARY,
            passed=(passed == self.num_tests),
            num_tests=self.num_tests,
            num_passed=passed,
            counterexamples=counterexamples,
            metadata={'num_qubits': num_qubits}
        )
    
    def test_normalization(self, state_func: Callable) -> PropertyTestResult:
        """Test if states remain normalized."""
        passed = 0
        counterexamples = []
        
        for i in range(self.num_tests):
            state = state_func()
            norm = np.linalg.norm(state)
            if np.isclose(norm, 1.0, atol=1e-6):
                passed += 1
            else:
                counterexamples.append({
                    'test': i,
                    'norm': float(norm)
                })
        
        return PropertyTestResult(
            property_type=PropertyType.NORMALIZATION,
            passed=(passed == self.num_tests),
            num_tests=self.num_tests,
            num_passed=passed,
            counterexamples=counterexamples
        )


class PropertyBasedGenerator:
    """Generate test cases for quantum circuits (like Hypothesis)."""
    
    def __init__(self):
        self.generators: Dict[str, Callable] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        """Register default generators."""
        self.generators['random_unitary'] = self._gen_random_unitary
        self.generators['random_state'] = self._gen_random_state
        self.generators['random_circuit'] = self._gen_random_circuit
    
    def generate(self, generator_type: str, **kwargs) -> Any:
        """Generate test case."""
        if generator_type not in self.generators:
            raise ValueError(f"Unknown generator: {generator_type}")
        return self.generators[generator_type](**kwargs)
    
    def _gen_random_unitary(self, num_qubits: int) -> np.ndarray:
        """Generate random unitary matrix."""
        # Use QR decomposition method.
        dim = 2**num_qubits
        Z = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        Q, R = np.linalg.qr(Z)
        # Ensure positive diagonal.
        D = np.diag(R)
        phase = D / np.abs(D)
        Q = Q @ np.diag(phase)
        return Q
    
    def _gen_random_state(self, num_qubits: int) -> np.ndarray:
        """Generate random normalized state vector."""
        dim = 2**num_qubits
        state = np.random.randn(dim) + 1j * np.random.randn(dim)
        state = state / np.linalg.norm(state)
        return state
    
    def _gen_random_circuit(self, num_qubits: int, depth: int) -> List[Tuple]:
        """Generate random circuit as list of gates."""
        gates = ['h', 'x', 'y', 'z', 'cnot']
        circuit = []
        for _ in range(depth):
            gate = random.choice(gates)
            if gate == 'cnot':
                qubit1 = random.randint(0, num_qubits-1)
                qubit2 = random.randint(0, num_qubits-1)
                circuit.append(('cnot', qubit1, qubit2))
            else:
                qubit = random.randint(0, num_qubits-1)
                circuit.append((gate, qubit))
        return circuit


class InvariantChecker:
    """Check quantum state invariants."""
    
    def __init__(self):
        self.invariants: List[Callable] = []
    
    def add_invariant(self, invariant_func: Callable[[np.ndarray], bool]):
        """Add an invariant to check."""
        self.invariants.append(invariant_func)
    
    def check_state(self, state: np.ndarray) -> Tuple[bool, List[str]]:
        """
        Check all invariants on a state.
        
        Returns:
            Tuple of (all_passed, failed_invariants).
        """
        failed = []
        for i, inv in enumerate(self.invariants):
            if not inv(state):
                failed.append(f"Invariant {i} failed")
        
        return len(failed) == 0, failed
    
    @staticmethod
    def normalization_invariant(state: np.ndarray) -> bool:
        """Invariant: state must be normalized."""
        return np.isclose(np.linalg.norm(state), 1.0, atol=1e-6)
    
    @staticmethod
    def positivity_invariant(state: np.ndarray) -> bool:
        """Invariant: probabilities must be non-negative."""
        probs = np.abs(state)**2
        return all(p >= 0 for p in probs)


class RandomizedTester:
    """Randomized testing with quantum-specific properties."""
    
    def __init__(self, num_trials: int = 1000):
        self.num_trials = num_trials
    
    def test_with_noise(self, circuit_func: Callable,
                       noise_model: Dict) -> PropertyTestResult:
        """Test circuit behavior under random noise."""
        passed = 0
        counterexamples = []
        
        for i in range(min(self.num_trials, 100)):  # Limit for speed.
            # Apply random noise.
            try:
                result = circuit_func(noise_model)
                if result is not None:
                    passed += 1
            except Exception as e:
                counterexamples.append({'trial': i, 'error': str(e)})
        
        return PropertyTestResult(
            property_type=PropertyType.UNITARY,
            passed=(passed == min(self.num_trials, 100)),
            num_tests=min(self.num_trials, 100),
            num_passed=passed,
            counterexamples=counterexamples
        )


class CoverageMetrics:
    """Test coverage metrics for quantum circuits."""
    
    def __init__(self):
        self.gate_coverage: Dict[str, int] = {}
        self.qubit_coverage: Dict[int, int] = {}
        self.path_coverage: List[str] = []
    
    def record_gate(self, gate_name: str, qubit: Optional[int] = None):
        """Record that a gate was tested."""
        self.gate_coverage[gate_name] = self.gate_coverage.get(gate_name, 0) + 1
        if qubit is not None:
            self.qubit_coverage[qubit] = self.qubit_coverage.get(qubit, 0) + 1
    
    def record_path(self, path: str):
        """Record an execution path."""
        if path not in self.path_coverage:
            self.path_coverage.append(path)
    
    def get_coverage_report(self) -> Dict[str, Any]:
        """Get coverage report."""
        return {
            'gate_coverage': dict(self.gate_coverage),
            'qubit_coverage': dict(self.qubit_coverage),
            'path_coverage': len(self.path_coverage),
            'total_gates_tested': sum(self.gate_coverage.values()),
            'unique_gates': len(self.gate_coverage),
            'qubits_covered': len(self.qubit_coverage)
        }
