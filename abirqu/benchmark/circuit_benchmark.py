"""
Task 18.1 — Quantum Circuit Benchmarking Suite.

Standardized benchmarking for quantum circuits: gate depth, width, fidelity tracking.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class BenchmarkMetric(Enum):
    """Metrics for benchmarking."""
    GATE_DEPTH = "gate_depth"
    GATE_COUNT = "gate_count"
    CIRCUIT_WIDTH = "circuit_width"
    FIDELITY = "fidelity"
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"


@dataclass
class BenchmarkResult:
    """Result of a benchmark run."""
    name: str
    metric: BenchmarkMetric
    value: float
    baseline: Optional[float] = None
    improvement: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'metric': self.metric.value,
            'value': self.value,
            'baseline': self.baseline,
            'improvement': self.improvement,
            'metadata': self.metadata
        }


class CircuitBenchmark:
    """Benchmark quantum circuits."""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.circuits: List[Dict[str, Any]] = []
        self.results: List[BenchmarkResult] = []
    
    def add_circuit(self, gates: List[Tuple], name: Optional[str] = None):
        """Add a circuit to benchmark."""
        self.circuits.append({
            'name': name or f"circuit_{len(self.circuits)}",
            'gates': gates
        })
    
    def run_benchmark(self) -> List[BenchmarkResult]:
        """Run all benchmarks."""
        self.results = []
        
        for circuit in self.circuits:
            gates = circuit['gates']
            
            # Gate count
            self.results.append(BenchmarkResult(
                name=circuit['name'],
                metric=BenchmarkMetric.GATE_COUNT,
                value=len(gates),
                metadata={'circuit': circuit['name']}
            ))
            
            # Gate depth (simplified: assume each gate adds 1 to depth)
            depth = self._compute_depth(gates)
            self.results.append(BenchmarkResult(
                name=circuit['name'],
                metric=BenchmarkMetric.GATE_DEPTH,
                value=depth,
                metadata={'circuit': circuit['name']}
            ))
            
            # Circuit width
            qubits_used = set()
            for gate_info in gates:
                if len(gate_info) >= 2:
                    qubits = gate_info[1]
                    if isinstance(qubits, (list, tuple)):
                        qubits_used.update(qubits)
                    else:
                        qubits_used.add(qubits)
            
            self.results.append(BenchmarkResult(
                name=circuit['name'],
                metric=BenchmarkMetric.CIRCUIT_WIDTH,
                value=len(qubits_used),
                metadata={'circuit': circuit['name']}
            ))
        
        return self.results
    
    def _compute_depth(self, gates: List[Tuple]) -> int:
        """Compute circuit depth (simplified)."""
        # For now, assume all gates are in sequence (depth = gate count)
        return len(gates)
    
    def compare_to_baseline(self, baseline_name: str = "baseline") -> List[BenchmarkResult]:
        """Compare results to baseline."""
        baseline_results = {r.metric: r.value for r in self.results 
                          if r.name == baseline_name}
        
        comparison = []
        for result in self.results:
            if result.name != baseline_name and result.metric in baseline_results:
                baseline_val = baseline_results[result.metric]
                if baseline_val > 0:
                    improvement = (baseline_val - result.value) / baseline_val
                else:
                    improvement = 0.0
                
                result.baseline = baseline_val
                result.improvement = improvement
                comparison.append(result)
        
        return comparison
