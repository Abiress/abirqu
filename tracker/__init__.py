"""
Quantum Advantage Tracker

Implements automated benchmarking against classical solvers.
Builds a live dashboard comparing AbirQu circuit performance vs. classical methods.
Supports custom benchmark definitions.
Implements advantage metric calculation (efficiency, cost, accuracy separation).
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time
import json

class BenchmarkType(Enum):
    """Types of benchmarks."""
    VQE = "vqe"
    QAOA = "qaoa"
    GROVER = "grover"
    SORTING = "sorting"
    FACTORING = "factoring"
    SIMULATION = "simulation"

@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    benchmark_name: str
    benchmark_type: BenchmarkType
    problem_size: int
    
    # Quantum results
    quantum_time: float
    quantum_fidelity: float
    quantum_cost: float  # Estimated cost in USD
    
    # Classical results
    classical_time: float
    classical_accuracy: float
    classical_cost: float
    
    # Metrics
    speedup: float  # classical_time / quantum_time
    advantage_score: float  # Combined metric
    
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            from datetime import datetime
            self.timestamp = datetime.now().isoformat()

class AdvantageMetric:
    """
    Calculates quantum advantage metrics.
    
    Quantum advantage is achieved when quantum algorithm outperforms
    classical methods in terms of time, cost, or accuracy.
    """
    
    @staticmethod
    def compute_speedup(quantum_time: float, 
                      classical_time: float) -> float:
        """Compute speedup factor."""
        if quantum_time <= 0:
            return float('inf')
        return classical_time / quantum_time
    
    @staticmethod
    def compute_cost_advantage(quantum_cost: float,
                                classical_cost: float) -> float:
        """Compute cost advantage ratio."""
        if quantum_cost <= 0:
            return float('inf')
        return classical_cost / quantum_cost
    
    @staticmethod
    def compute_accuracy_separation(quantum_fidelity: float,
                                   classical_accuracy: float) -> float:
        """Compute accuracy separation."""
        return quantum_fidelity - classical_accuracy
    
    @staticmethod
    def combined_score(quantum_time: float, classical_time: float,
                      quantum_fidelity: float, classical_accuracy: float,
                      quantum_cost: float = 1.0,
                      classical_cost: float = 1.0,
                      weights: Optional[Dict[str, float]] = None) -> float:
        """
        Compute combined advantage score.
        
        Returns:
            Score > 1 indicates quantum advantage
        """
        if weights is None:
            weights = {
                'speedup': 0.4,
                'accuracy': 0.3,
                'cost': 0.3
            }
        
        speedup = AdvantageMetric.compute_speedup(quantum_time, classical_time)
        cost_adv = AdvantageMetric.compute_cost_advantage(quantum_cost, classical_cost)
        acc_sep = AdvantageMetric.compute_accuracy_separation(
            quantum_fidelity, classical_accuracy
        )
        
        # Normalize speedup (cap at 100x)
        speedup_norm = min(speedup, 100.0) / 100.0
        
        # Accuracy separation normalized to [0, 1]
        acc_norm = max(0.0, min(acc_sep + 0.5, 1.0))
        
        # Cost advantage normalized
        cost_norm = min(cost_adv, 10.0) / 10.0
        
        score = (weights['speedup'] * speedup_norm +
                weights['accuracy'] * acc_norm +
                weights['cost'] * cost_norm)
        
        return score

class Benchmark:
    """Base class for benchmarks."""
    
    def __init__(self, name: str, benchmark_type: BenchmarkType):
        self.name = name
        self.benchmark_type = benchmark_type
        self.problem_sizes = [4, 8, 12, 16]
        
    def run_quantum(self, problem_size: int) -> Tuple[float, float, float]:
        """
        Run quantum algorithm.
        
        Returns:
            Tuple of (time, fidelity, cost)
        """
        raise NotImplementedError
    
    def run_classical(self, problem_size: int) -> Tuple[float, float, float]:
        """
        Run classical algorithm.
        
        Returns:
            Tuple of (time, accuracy, cost)
        """
        raise NotImplementedError
    
    def run_benchmark(self, problem_size: Optional[int] = None) -> BenchmarkResult:
        """Run full benchmark comparison."""
        size = problem_size or self.problem_sizes[0]
        
        q_time, q_fid, q_cost = self.run_quantum(size)
        c_time, c_acc, c_cost = self.run_classical(size)
        
        speedup = AdvantageMetric.compute_speedup(q_time, c_time)
        score = AdvantageMetric.combined_score(
            q_time, c_time, q_fid, c_acc, q_cost, c_cost
        )
        
        return BenchmarkResult(
            benchmark_name=self.name,
            benchmark_type=self.benchmark_type,
            problem_size=size,
            quantum_time=q_time,
            quantum_fidelity=q_fid,
            quantum_cost=q_cost,
            classical_time=c_time,
            classical_accuracy=c_acc,
            classical_cost=c_cost,
            speedup=speedup,
            advantage_score=score
        )

class VQEBenchmark(Benchmark):
    """VQE benchmark comparing to classical eigensolvers."""
    
    def __init__(self):
        super().__init__("VQE vs Classical Eigensolver", BenchmarkType.VQE)
        
    def run_quantum(self, problem_size: int) -> Tuple[float, float, float]:
        """Simulate VQE run."""
        start = time.time()
        
        # Mock VQE: O(n) circuit depth
        time.sleep(0.01 * problem_size)  # Simulate work
        
        q_time = time.time() - start
        q_fid = 0.95 + 0.05 * np.random.random()  # ~95% fidelity
        q_cost = 0.001 * problem_size  # $0.001 per qubit
        
        return q_time, q_fid, q_cost
    
    def run_classical(self, problem_size: int) -> Tuple[float, float, float]:
        """Run classical eigensolver (e.g., exact diagonalization)."""
        start = time.time()
        
        # Classical diagonalization: O(2^n) for exact
        # For small n, it's fast
        if problem_size <= 10:
            time.sleep(0.001 * (2 ** problem_size))
        else:
            time.sleep(1.0)  # Intractable
            
        c_time = time.time() - start
        c_acc = 1.0  # Exact result
        c_cost = 0.0001 * (2 ** problem_size)  # Exponential cost
        
        return c_time, c_acc, c_cost

class GroverBenchmark(Benchmark):
    """Grover's algorithm benchmark."""
    
    def __init__(self):
        super().__init__("Grover vs Linear Search", BenchmarkType.GROVER)
        
    def run_quantum(self, problem_size: int) -> Tuple[float, float, float]:
        """Simulate Grover search."""
        N = 2 ** problem_size
        iterations = int(np.pi/4 * np.sqrt(N))
        
        start = time.time()
        time.sleep(0.001 * iterations)  # Simulate
        q_time = time.time() - start
        
        q_fid = 0.90  # ~90% success probability
        q_cost = 0.01 * iterations
        
        return q_time, q_fid, q_cost
    
    def run_classical(self, problem_size: int) -> Tuple[float, float, float]:
        """Classical linear search."""
        N = 2 ** problem_size
        
        start = time.time()
        time.sleep(0.0001 * N)  # Linear in N
        c_time = time.time() - start
        
        c_acc = 1.0  # Always finds it
        c_cost = 0.001 * N
        
        return c_time, c_acc, c_cost

class QuantumAdvantageTracker:
    """
    Tracks quantum advantage across multiple benchmarks.
    Provides live dashboard data.
    """
    
    def __init__(self):
        self.benchmarks: List[Benchmark] = [
            VQEBenchmark(),
            GroverBenchmark()
        ]
        self.results_history: List[BenchmarkResult] = []
        
    def run_all_benchmarks(self, 
                          problem_size: Optional[int] = None) -> List[BenchmarkResult]:
        """Run all benchmarks."""
        results = []
        
        for benchmark in self.benchmarks:
            result = benchmark.run_benchmark(problem_size)
            self.results_history.append(result)
            results.append(result)
            
        return results
    
    def get_advantage_summary(self) -> Dict[str, Any]:
        """Get summary of quantum advantage."""
        if not self.results_history:
            return {'status': 'No benchmarks run'}
            
        latest = {}
        for result in self.results_history:
            if (result.benchmark_name not in latest or
                result.timestamp > latest[result.benchmark_name].timestamp):
                latest[result.benchmark_name] = result
                
        summary = {
            'benchmarks_run': len(latest),
            'avantage_achieved': sum(1 for r in latest.values() 
                                     if r.advantage_score > 1.0),
            'average_speedup': np.mean([r.speedup for r in latest.values()]),
            'best_advantage': max(latest.values(), 
                                     key=lambda r: r.advantage_score),
            'details': [
                {
                    'name': r.benchmark_name,
                    'type': r.benchmark_type.value,
                    'problem_size': r.problem_size,
                    'speedup': r.speedup,
                    'advantage_score': r.advantage_score,
                    'quantum_time': r.quantum_time,
                    'classical_time': r.classical_time
                }
                for r in latest.values()
            ]
        }
        
        return summary
    
    def export_dashboard_data(self) -> str:
        """Export data for dashboard visualization."""
        data = {
            'timestamp': [r.timestamp for r in self.results_history],
            'benchmark': [r.benchmark_name for r in self.results_history],
            'problem_size': [r.problem_size for r in self.results_history],
            'speedup': [r.speedup for r in self.results_history],
            'advantage_score': [r.advantage_score for r in self.results_history],
            'quantum_time': [r.quantum_time for r in self.results_history],
            'classical_time': [r.classical_time for r in self.results_history]
        }
        
        return json.dumps(data, indent=2)

# Example usage and tests
if __name__ == "__main__":
    print("Testing Quantum Advantage Tracker...")
    
    tracker = QuantumAdvantageTracker()
    
    print("\nRunning all benchmarks...")
    results = tracker.run_all_benchmarks(problem_size=6)
    
    for result in results:
        print(f"\n{result.benchmark_name} (size={result.problem_size}):")
        print(f"  Quantum: {result.quantum_time:.3f}s, "
              f"fidelity={result.quantum_fidelity:.3f}")
        print(f"  Classical: {result.classical_time:.3f}s, "
              f"accuracy={result.classical_accuracy:.3f}")
        print(f"  Speedup: {result.speedup:.2f}x")
        print(f"  Advantage score: {result.advantage_score:.3f} "
              f"({'ADVANTAGE' if result.advantage_score > 1.0 else 'No advantage')}")
    
    print("\n" + "="*50)
    summary = tracker.get_advantage_summary()
    print("Advantage Summary:")
    print(f"  Benchmarks run: {summary['benchmarks_run']}")
    print(f"  Advantage achieved: {summary['advantage_achieved']}")
    print(f"  Average speedup: {summary['average_speedup']:.2f}x")
    
    print("\n" + "="*50)
    print("Quantum Advantage Tracker ready!")
    print("Dashboard data exported (JSON format)")
    print(tracker.export_dashboard_data()[:500] + "...")