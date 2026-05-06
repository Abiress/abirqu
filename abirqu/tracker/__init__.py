"""Quantum Advantage Tracker for AbirQu. Copyright 2026 Abir Maheshwari"""
import numpy as np
import time
from typing import Dict, List, Any, Optional, Tuple
from ..core.circuit import Circuit
from ..core.gates import H, CNOT

class QuantumAdvantageTracker:
    """Tracks and compares quantum vs classical performance."""
    
    def __init__(self):
        self.metrics: Dict[str, List[Dict]] = {
            'quantum': [],
            'classical': []
        }
        self.benchmarks = {}
        
    def compare(self, quantum_result: Any, classical_result: Any, 
               task_name: str = "unknown") -> Dict[str, Any]:
        """Compare quantum vs classical results."""
        comparison = {
            'task': task_name,
            'timestamp': time.time(),
            'quantum': self._extract_metrics(quantum_result, 'quantum'),
            'classical': self._extract_metrics(classical_result, 'classical')
        }
        
        # Calculate advantage
        if comparison['quantum'] and comparison['classical']:
            q_time = comparison['quantum'].get('execution_time', 0)
            c_time = comparison['classical'].get('execution_time', 0)
            
            if c_time > 0:
                advantage = c_time / max(q_time, 0.001)
                comparison['advantage'] = {
                    'speedup': advantage,
                    'quantum_faster': q_time < c_time,
                    'factor': f"{advantage:.2f}x"
                }
        
        # Store
        self.metrics['quantum'].append(comparison['quantum'])
        self.metrics['classical'].append(comparison['classical'])
        
        return comparison
        
    def _extract_metrics(self, result: Any, result_type: str) -> Dict:
        """Extract metrics from result."""
        if isinstance(result, dict):
            return result
        elif isinstance(result, Circuit):
            return {
                'type': result_type,
                'num_qubits': result.num_qubits,
                'gate_count': len(result.gates),
                'depth': result.depth()
            }
        else:
            return {'type': result_type, 'result': str(result)}
        
    def run_benchmark(self, benchmark_name: str, num_qubits_list: List[int]) -> Dict:
        """Run benchmark across different qubit counts."""
        results = {
            'benchmark': benchmark_name,
            'results': []
        }
        
        for num_qubits in num_qubits_list:
            # Quantum execution
            q_start = time.perf_counter()
            q_circuit = self._run_quantum_benchmark(benchmark_name, num_qubits)
            q_time = time.perf_counter() - q_start
            
            # Classical simulation
            c_start = time.perf_counter()
            c_result = self._run_classical_benchmark(benchmark_name, num_qubits)
            c_time = time.perf_counter() - c_start
            
            result = {
                'num_qubits': num_qubits,
                'quantum_time': q_time,
                'classical_time': c_time,
                'speedup': c_time / max(q_time, 0.001),
                'quantum_depth': q_circuit.depth(),
                'quantum_gates': len(q_circuit.gates)
            }
            results['results'].append(result)
        
        self.benchmarks[benchmark_name] = results
        return results
        
    def _run_quantum_benchmark(self, name: str, num_qubits: int) -> Circuit:
        """Run quantum benchmark circuit."""
        if name == 'bell_pairs':
            circuit = Circuit(num_qubits, 'bell_bench')
            for i in range(0, num_qubits - 1, 2):
                circuit.h(i).cnot(i, i + 1)
            return circuit
            
        elif name == 'ghz':
            circuit = Circuit(num_qubits, 'ghz_bench')
            circuit.h(0)
            for i in range(1, num_qubits):
                circuit.cnot(0, i)
            return circuit
            
        elif name == 'superposition':
            circuit = Circuit(num_qubits, 'super_bench')
            for q in range(num_qubits):
                circuit.h(q)
            return circuit
            
        else:
            # Default: random circuit
            circuit = Circuit(num_qubits, 'random_bench')
            import random
            for _ in range(num_qubits * 2):
                q = random.randint(0, num_qubits - 1)
                circuit.h(q)
            return circuit
        
    def _run_classical_benchmark(self, name: str, num_qubits: int):
        """Run classical simulation benchmark."""
        # Simplified: simulate quantum state classically
        state_size = 2 ** num_qubits
        
        if name == 'bell_pairs':
            # Simulate Bell pairs
            return {'state_vector_size': state_size, 'method': 'exact'}
            
        elif name == 'ghz':
            # Simulate GHZ
            return {'state_vector_size': state_size, 'method': 'exact'}
            
        else:
            # Generic simulation
            return {'state_vector_size': state_size, 'method': 'monte_carlo'}
        
    def get_advantage_threshold(self) -> Optional[int]:
        """Estimate quantum advantage threshold."""
        if not self.benchmarks:
            return None
            
        # Find where quantum becomes faster
        for bench_name, bench_data in self.benchmarks.items():
            for result in bench_data['results']:
                if result['speedup'] > 1.0:
                    return result['num_qubits']
        
        return None
        
    def export_results(self, filepath: str):
        """Export tracking results to JSON."""
        import json
        
        data = {
            'metrics': self.metrics,
            'benchmarks': self.benchmarks,
            'advantage_threshold': self.get_advantage_threshold()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
            
    def visualize_advantage(self) -> Dict:
        """Generate visualization data for advantage."""
        if not self.benchmarks:
            return {}
            
        # Use first benchmark
        bench_name = list(self.benchmarks.keys())[0]
        bench_data = self.benchmarks[bench_name]
        
        qubits = []
        q_times = []
        c_times = []
        speedups = []
        
        for result in bench_data['results']:
            qubits.append(result['num_qubits'])
            q_times.append(result['quantum_time'])
            c_times.append(result['classical_time'])
            speedups.append(result['speedup'])
        
        return {
            'type': 'advantage_plot',
            'x': qubits,
            'quantum_times': q_times,
            'classical_times': c_times,
            'speedups': speedups,
            'threshold': self.get_advantage_threshold()
        }
