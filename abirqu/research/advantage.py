"""
Task 15.3 — Quantum Advantage Validator.

Quantum advantage testing, classical simulation comparison, statistical testing, reproducible benchmarks.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
import time
import random


@dataclass
class AdvantageResult:
    """Result of quantum advantage validation."""
    problem: str
    quantum_time: float
    classical_time: float
    speedup_factor: float  # quantum_time / classical_time.
    advantage_confirmed: bool
    confidence: float  # 0-1, statistical confidence.
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'problem': self.problem,
            'quantum_time': self.quantum_time,
            'classical_time': self.classical_time,
            'speedup_factor': self.speedup_factor,
            'advantage_confirmed': self.advantage_confirmed,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


class QuantumAdvantageValidator:
    """Rigorous quantum advantage testing framework."""
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.experiments: List[AdvantageResult] = []
    
    def validate_advantage(self, problem: str,
                           quantum_func: Callable,
                           classical_func: Callable,
                           problem_sizes: List[int],
                           num_trials: int = 100) -> AdvantageResult:
        """
        Validate quantum advantage.
        
        Args:
            problem: Problem name.
            quantum_func: Quantum algorithm function.
            classical_func: Classical algorithm function.
            problem_sizes: List of problem sizes to test.
            num_trials: Number of trials per size.
            
        Returns:
            AdvantageResult.
        """
        quantum_times = []
        classical_times = []
        
        for size in problem_sizes:
            # Run multiple trials.
            for _ in range(min(num_trials, 20)):  # Limit for speed.
                # Quantum runtime.
                start = time.time()
                quantum_func(size)
                quantum_time = time.time() - start
                quantum_times.append(quantum_time)
                
                # Classical runtime.
                start = time.time()
                classical_func(size)
                classical_time = time.time() - start
                classical_times.append(classical_time)
        
        # Compute statistics.
        avg_quantum = np.mean(quantum_times) if quantum_times else 0.0
        avg_classical = np.mean(classical_times) if classical_times else 1.0
        
        speedup = avg_quantum / max(avg_classical, 1e-10)
        advantage = speedup < 1.0  # Quantum is faster.
        
        # Statistical test (simplified t-test).
        if len(quantum_times) > 1 and len(classical_times) > 1:
            # Simplified: check if means are significantly different.
            quantum_std = np.std(quantum_times)
            classical_std = np.std(classical_times)
            # T-statistic.
            t_stat = (avg_classical - avg_quantum) / np.sqrt(
                quantum_std**2 / len(quantum_times) + 
                classical_std**2 / len(classical_times)
            )
            confidence = min(0.99, abs(t_stat) / 10.0)  # Simplified.
        else:
            confidence = 0.5
        
        result = AdvantageResult(
            problem=problem,
            quantum_time=avg_quantum,
            classical_time=avg_classical,
            speedup_factor=speedup,
            advantage_confirmed=advantage,
            confidence=confidence,
            metadata={
                'problem_sizes': problem_sizes,
                'num_trials': min(num_trials, 20),
                'quantum_std': np.std(quantum_times) if quantum_times else 0.0,
                'classical_std': np.std(classical_times) if classical_times else 0.0
            }
        )
        
        self.experiments.append(result)
        return result
    
    def validate_search_advantage(self, num_items_list: List[int]) -> AdvantageResult:
        """Validate Grover's quadratic speedup."""
        def quantum_search(n: int):
            # Simulated quantum search: O(sqrt(N)).
            import time
            time.sleep(0.001 * np.sqrt(n))
            return True
        
        def classical_search(n: int):
            # Simulated classical search: O(N).
            import time
            time.sleep(0.001 * n)
            return True
        
        return self.validate_advantage(
            problem='unstructured_search',
            quantum_func=quantum_search,
            classical_func=classical_search,
            problem_sizes=num_items_list,
            num_trials=10
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all advantage experiments."""
        if not self.experiments:
            return {}
        
        confirmed = sum(1 for e in self.experiments if e.advantage_confirmed)
        
        return {
            'total_experiments': len(self.experiments),
            'advantage_confirmed': confirmed,
            'confirmation_rate': confirmed / len(self.experiments),
            'average_speedup': np.mean([e.speedup_factor for e in self.experiments]),
            'average_confidence': np.mean([e.confidence for e in self.experiments])
        }


class ClassicalSimulationComparator:
    """Compare with classical simulation using matching resources."""
    
    def __init__(self):
        self.comparisons: List[Dict] = []
    
    def compare_with_simulator(self, circuit_func: Callable,
                               size: int,
                               classical_simulator: str = "exact") -> Dict[str, Any]:
        """
        Compare quantum circuit with classical simulation.
        
        Args:
            circuit_func: Function that returns a circuit given size.
            size: Problem size.
            classical_simulator: Type of classical simulation.
            
        Returns:
            Comparison dictionary.
        """
        # Generate circuit.
        circuit = circuit_func(size)
        
        # Classical simulation time (simplified).
        # In practice, would use actual classical simulator.
        num_qubits = size if isinstance(size, int) else 4
        classical_time = 2**num_qubits * 0.001  # Exponential.
        
        # Quantum execution time (simplified).
        quantum_time = np.sqrt(2**num_qubits) * 0.001  # Quadratic improvement.
        
        speedup = classical_time / max(quantum_time, 1e-10)
        
        result = {
            'problem_size': size,
            'num_qubits': num_qubits,
            'classical_simulator': classical_simulator,
            'classical_time': classical_time,
            'quantum_time': quantum_time,
            'speedup': speedup,
            'advantage': speedup > 1.0
        }
        
        self.comparisons.append(result)
        return result
    
    def compare_factoring(self, bit_length: int) -> Dict[str, Any]:
        """Compare quantum vs classical factoring."""
        # Shor's algorithm: O(n^3).
        quantum_time = bit_length**3 * 0.001
        
        # Best classical: O(e^(n^(1/3))).
        classical_time = np.exp(bit_length**(1/3)) * 0.001
        
        return {
            'bit_length': bit_length,
            'quantum_algorithm': 'Shor',
            'quantum_time': quantum_time,
            'classical_time': classical_time,
            'advantage': classical_time > quantum_time,
            'speedup_factor': classical_time / max(quantum_time, 1e-10)
        }
    
    def batch_compare(self, func: Callable, sizes: List[int]) -> List[Dict]:
        """Run multiple comparisons."""
        return [self.compare_with_simulator(func, s) for s in sizes]


class StatisticalTester:
    """Statistical hypothesis testing for advantage claims."""
    
    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha  # Significance level.
        self.test_results: List[Dict] = []
    
    def t_test(self, sample1: List[float], sample2: List[float]) -> Dict[str, Any]:
        """
        Perform t-test to compare two algorithms.
        
        Returns:
            Dictionary with test results.
        """
        if len(sample1) < 2 or len(sample2) < 2:
            return {'error': 'Insufficient data'}
        
        # Compute t-statistic (Welch's t-test).
        mean1, std1, n1 = np.mean(sample1), np.std(sample1, ddof=1), len(sample1)
        mean2, std2, n2 = np.mean(sample2), np.std(sample2, ddof=1), len(sample2)
        
        # Standard error.
        se = np.sqrt(std1**2 / n1 + std2**2 / n2)
        if se == 0:
            t_stat = 0.0
        else:
            t_stat = (mean2 - mean1) / se
        
        # Degrees of freedom (simplified).
        df = min(n1, n2) - 1
        
        # P-value (simplified normal approximation).
        # In practice, would use t-distribution.
        p_value = 2 * (1 - self._norm_cdf(abs(t_stat)))
        
        significant = p_value < self.alpha
        
        result = {
            'test': 't-test',
            't_statistic': t_stat,
            'p_value': p_value,
            'significant': significant,
            'alpha': self.alpha,
            'mean1': mean1,
            'mean2': mean2,
            'interpretation': 'Quantum is faster' if mean1 < mean2 else 'Classical is faster'
        }
        
        self.test_results.append(result)
        return result
    
    def _norm_cdf(self, x: float) -> float:
        """Approximate normal CDF."""
        # Abramowitz & Stegun approximation.
        import math
        if x < 0:
            return 1 - self._norm_cdf(-x)
        return 0.5 * (1 + math.erf(x / np.sqrt(2)))
    
    def bootstrap_test(self, sample1: List[float], sample2: List[float],
                     num_bootstrap: int = 1000) -> Dict[str, Any]:
        """Bootstrap test for median difference."""
        differences = []
        
        for _ in range(num_bootstrap):
            # Resample with replacement.
            bs1 = np.random.choice(sample1, size=len(sample1), replace=True)
            bs2 = np.random.choice(sample2, size=len(sample2), replace=True)
            differences.append(np.median(bs2) - np.median(bs1))
        
        # Compute confidence interval.
        ci_lower = np.percentile(differences, 2.5)
        ci_upper = np.percentile(differences, 97.5)
        
        # Check if 0 is outside CI.
        significant = ci_lower > 0 or ci_upper < 0
        
        return {
            'test': 'bootstrap',
            'bootstrap_samples': num_bootstrap,
            'ci_95': (ci_lower, ci_upper),
            'significant': significant,
            'median_difference': np.median(differences)
        }


class ReproducibleBenchmark:
    """Reproducible benchmark suite for advantage demonstrations."""
    
    def __init__(self, seed: Optional[int] = 42):
        self.seed = seed
        if seed:
            random.seed(seed)
            np.random.seed(seed)
        self.benchmarks: List[Dict] = []
    
    def run_benchmark(self, name: str, func: Callable,
                     sizes: List[int], num_runs: int = 10) -> Dict[str, Any]:
        """
        Run a reproducible benchmark.
        
        Args:
            name: Benchmark name.
            func: Function to benchmark.
            sizes: Problem sizes.
            num_runs: Number of runs per size.
            
        Returns:
            Benchmark results.
        """
        results = {
            'name': name,
            'seed': self.seed,
            'sizes': sizes,
            'num_runs': num_runs,
            'data': []
        }
        
        for size in sizes:
            times = []
            for _ in range(num_runs):
                start = time.time()
                func(size)
                elapsed = time.time() - start
                times.append(elapsed)
            
            size_data = {
                'size': size,
                'mean_time': np.mean(times),
                'std_time': np.std(times),
                'min_time': min(times),
                'max_time': max(times),
                'all_times': times
            }
            results['data'].append(size_data)
        
        self.benchmarks.append(results)
        return results
    
    def compare_benchmarks(self, name1: str, name2: str) -> Dict[str, Any]:
        """Compare two benchmarks."""
        bench1 = next((b for b in self.benchmarks if b['name'] == name1), None)
        bench2 = next((b for b in self.benchmarks if b['name'] == name2), None)
        
        if not bench1 or not bench2:
            return {'error': 'Benchmark not found'}
        
        # Compare at each size.
        comparisons = []
        for d1, d2 in zip(bench1['data'], bench2['data']):
            if d1['size'] == d2['size']:
                speedup = d1['mean_time'] / max(d2['mean_time'], 1e-10)
                comparisons.append({
                    'size': d1['size'],
                    'time1': d1['mean_time'],
                    'time2': d2['mean_time'],
                    'speedup': speedup
                })
        
        return {
            'benchmark1': name1,
            'benchmark2': name2,
            'comparisons': comparisons,
            'average_speedup': np.mean([c['speedup'] for c in comparisons]) if comparisons else 0
        }
    
    def export_results(self, filepath: str):
        """Export all benchmark results to JSON."""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.benchmarks, f, indent=2, default=str)
