"""
Task 15.2 — Quantum Complexity Analyzer.

Complexity classification, resource scaling, classical comparison, lower bound estimation.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class ComplexityClass(Enum):
    """Quantum complexity classes."""
    BQP = "BQP"  # Bounded-error Quantum Polynomial time.
    QMA = "QMA"  # Quantum Merlin-Arthur.
    QIP = "QIP"  # Quantum Interactive Proofs.
    P = "P"  # Classical Polynomial time.
    NP = "NP"  # Classical Non-deterministic Polynomial.
    EXP = "EXP"  # Exponential time.


@dataclass
class ComplexityResult:
    """Result of complexity analysis."""
    problem: str
    quantum_class: ComplexityClass
    classical_class: ComplexityClass
    quantum_resources: Dict[str, Any]
    classical_resources: Dict[str, Any]
    quantum_advantage: bool  # True if quantum is asymptotically better.
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'problem': self.problem,
            'quantum_class': self.quantum_class.value,
            'classical_class': self.classical_class.value,
            'quantum_resources': self.quantum_resources,
            'classical_resources': self.classical_resources,
            'quantum_advantage': self.quantum_advantage,
            'metadata': self.metadata
        }


class ComplexityAnalyzer:
    """Automatic complexity classification (BQP, QMA, QIP)."""
    
    def __init__(self):
        self.known_problems: Dict[str, ComplexityResult] = {}
        self._load_known_problems()
    
    def _load_known_problems(self):
        """Load known quantum algorithms and their complexity."""
        self.known_problems['factoring'] = ComplexityResult(
            problem='integer_factoring',
            quantum_class=ComplexityClass.BQP,
            classical_class=ComplexityClass.EXP,
            quantum_resources={'time': 'O(n^3)', 'qubits': 'O(n)'},
            classical_resources={'time': 'O(e^(n^(1/3)))', 'space': 'polynomial'},
            quantum_advantage=True
        )
        self.known_problems['grover'] = ComplexityResult(
            problem='unstructured_search',
            quantum_class=ComplexityClass.BQP,
            classical_class=ComplexityClass.P,
            quantum_resources={'time': 'O(sqrt(N))', 'qubits': 'O(log N)'},
            classical_resources={'time': 'O(N)', 'space': 'O(1)'},
            quantum_advantage=True
        )
        self.known_problems['simon'] = ComplexityResult(
            problem='simon_period_finding',
            quantum_class=ComplexityClass.BQP,
            classical_class=ComplexityClass.EXP,
            quantum_resources={'time': 'O(n)', 'qubits': 'O(n)'},
            classical_resources={'time': 'O(2^(n/2))', 'space': 'polynomial'},
            quantum_advantage=True
        )
    
    def classify(self, problem_description: str) -> Optional[ComplexityResult]:
        """
        Classify a problem's complexity.
        
        Args:
            problem_description: Text description of the problem.
            
        Returns:
            ComplexityResult or None if unknown.
        """
        problem_lower = problem_description.lower()
        
        # Check known problems.
        for key, result in self.known_problems.items():
            if key in problem_lower or result.problem in problem_lower:
                return result
        
        # Heuristic classification.
        if 'search' in problem_lower:
            return self.known_problems['grover']
        elif 'factor' in problem_lower:
            return self.known_problems['factoring']
        elif 'period' in problem_lower or 'hidden' in problem_lower:
            return self.known_problems['simon']
        
        return None
    
    def estimate_class(self, circuit: Any, input_size: int) -> ComplexityClass:
        """
        Estimate complexity class from circuit structure.
        
        Args:
            circuit: Quantum circuit.
            input_size: Size of input (e.g., number of bits).
            
        Returns:
            Estimated complexity class.
        """
        # Simplified: analyze gate count scaling.
        if hasattr(circuit, 'gates'):
            num_gates = len(circuit.gates)
            # Heuristic: if gate count is polynomial in input size.
            if num_gates <= input_size ** 3:
                return ComplexityClass.BQP
            else:
                return ComplexityClass.EXP
        
        return ComplexityClass.BQP  # Default assumption.


class ResourceScalingAnalyzer:
    """Analyze how resource cost grows with problem size."""
    
    def __init__(self):
        self.scaling_data: List[Dict] = []
    
    def analyze_scaling(self, resource_func: Callable[[int], Dict],
                       sizes: List[int]) -> Dict[str, Any]:
        """
        Analyze resource scaling.
        
        Args:
            resource_func: Function that takes problem size and returns resource dict.
            sizes: List of problem sizes to test.
            
        Returns:
            Dictionary with scaling analysis.
        """
        results = []
        for size in sizes:
            resources = resource_func(size)
            results.append({
                'size': size,
                'resources': resources
            })
        
        self.scaling_data.extend(results)
        
        # Fit scaling laws (simplified).
        qubit_counts = [r['resources'].get('qubits', 0) for r in results]
        gate_counts = [r['resources'].get('gates', 0) for r in results]
        
        return {
            'sizes': sizes,
            'qubit_scaling': self._fit_scaling(sizes, qubit_counts),
            'gate_scaling': self._fit_scaling(sizes, gate_counts),
            'raw_data': results
        }
    
    def _fit_scaling(self, x: List[int], y: List[float]) -> str:
        """Fit a scaling law (simplified)."""
        if len(x) < 2:
            return "insufficient_data"
        
        # Check if polynomial or exponential.
        log_y = [np.log(max(v, 1e-10)) for v in y]
        
        # Linear regression on log-log plot.
        coeffs = np.polyfit(np.log(x), log_y, 1)
        exponent = coeffs[0]
        
        if exponent < 1.5:
            return f"O(n^{exponent:.1f})"
        elif exponent < 2.5:
            return f"O(n^{exponent:.1f})"
        else:
            return "O(2^n) or worse"
    
    def compare_scaling(self, quantum_func: Callable, classical_func: Callable,
                       sizes: List[int]) -> Dict[str, Any]:
        """Compare quantum vs classical scaling."""
        quantum_scaling = self.analyze_scaling(quantum_func, sizes)
        classical_scaling = self.analyze_scaling(classical_func, sizes)
        
        # Determine if quantum has better scaling.
        quantum_better = (
            'O(2^n)' not in quantum_scaling['gate_scaling'] and
            'worse' not in quantum_scaling['gate_scaling']
        )
        
        return {
            'quantum_scaling': quantum_scaling,
            'classical_scaling': classical_scaling,
            'quantum_advantage': quantum_better,
            'description': 'Quantum scaling comparison complete'
        }


class ClassicalComparator:
    """Compare classical vs quantum complexity for same problem."""
    
    def __init__(self):
        self.comparisons: List[Dict] = []
    
    def compare(self, problem: str, input_size: int) -> Dict[str, Any]:
        """
        Compare classical and quantum approaches.
        
        Args:
            problem: Problem name.
            input_size: Size of input.
            
        Returns:
            Comparison dictionary.
        """
        # Known comparisons.
        comparisons = {
            'factoring': {
                'problem': 'integer_factoring',
                'input_bits': input_size,
                'quantum_time': f"O(n^3)",
                'classical_time': f"O(e^(n^(1/3) * log^(2/3)(n)))",
                'quantum_qubits': f"O({input_size})",
                'classical_space': f"O({input_size})",
                'advantage': True,
                'advantage_factor': 'exponential'
            },
            'search': {
                'problem': 'unstructured_search',
                'input_size': input_size,
                'quantum_time': f"O(sqrt({input_size}))",
                'classical_time': f"O({input_size})",
                'quantum_qubits': f"O(log({input_size}))",
                'classical_space': "O(1)",
                'advantage': True,
                'advantage_factor': 'quadratic'
            },
            'simulation': {
                'problem': 'quantum_simulation',
                'input_size': input_size,
                'quantum_time': f"O(poly({input_size}))",
                'classical_time': f"O(2^{input_size})",
                'quantum_qubits': f"O({input_size})",
                'classical_space': f"O(2^{input_size})",
                'advantage': True,
                'advantage_factor': 'exponential'
            }
        }
        
        result = comparisons.get(problem.lower(), {
            'problem': problem,
            'input_size': input_size,
            'quantum_time': 'unknown',
            'classical_time': 'unknown',
            'advantage': False,
            'note': 'No known comparison available'
        })
        
        self.comparisons.append(result)
        return result
    
    def batch_compare(self, problems: List[str], 
                       size: int) -> List[Dict[str, Any]]:
        """Compare multiple problems."""
        return [self.compare(p, size) for p in problems]
    
    def summary(self) -> Dict[str, Any]:
        """Get summary of comparisons."""
        advantages = sum(1 for c in self.comparisons if c.get('advantage'))
        return {
            'total_comparisons': len(self.comparisons),
            'problems_with_advantage': advantages,
            'advantage_rate': advantages / max(len(self.comparisons), 1)
        }


class ComplexityEstimator:
    """Estimate complexity lower bounds."""
    
    def __init__(self):
        self.lower_bounds: Dict[str, str] = {}
        self._set_default_bounds()
    
    def _set_default_bounds(self):
        """Set known lower bounds."""
        self.lower_bounds['search'] = 'Omega(sqrt(N))'
        self.lower_bounds['factoring'] = 'Omega(e^(n^(1/3)))'
        self.lower_bounds['sorting'] = 'Omega(n log n)'
    
    def estimate_lower_bound(self, problem: str, 
                            technique: str = "information_theoretic") -> str:
        """
        Estimate lower bound for a problem.
        
        Args:
            problem: Problem name.
            technique: Estimation technique.
            
        Returns:
            Lower bound string (e.g., "Omega(n log n)").
        """
        problem_lower = problem.lower()
        
        # Check known bounds.
        for key, bound in self.lower_bounds.items():
            if key in problem_lower:
                return bound
        
        # Heuristic: based on problem characteristics.
        if 'search' in problem_lower:
            return 'Omega(sqrt(N))'
        elif 'sort' in problem_lower:
            return 'Omega(n log n)'
        elif 'optimization' in problem_lower:
            return 'Omega(2^(n/2))'
        
        return 'Omega(1)'  # Trivial lower bound.
    
    def estimate_quantum_lower_bound(self, algorithm: Any, 
                                    input_size: int) -> str:
        """
        Estimate quantum-specific lower bound.
        
        Based on query complexity, communication complexity, etc.
        """
        # Simplified: use known quantum lower bounds.
        if hasattr(algorithm, 'name'):
            return self.estimate_lower_bound(algorithm.name)
        return 'Omega(sqrt(N))'  # Default for search-type problems.
    
    def compare_bounds(self, algorithm_complexity: str,
                      lower_bound: str) -> Dict[str, Any]:
        """
        Compare algorithm complexity to lower bound.
        
        Returns:
            Dictionary with tightness analysis.
        """
        # Simplified: check if complexity matches lower bound.
        # Parse to extract exponent (very simplified).
        is_tight = 'sqrt' in algorithm_complexity and 'sqrt' in lower_bound
        
        return {
            'algorithm_complexity': algorithm_complexity,
            'lower_bound': lower_bound,
            'is_tight': is_tight,
            'gap': 'unknown' if not is_tight else 'optimal'
        }
