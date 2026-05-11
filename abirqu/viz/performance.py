"""Performance Analysis for AbirQu. Copyright 2026 Abir Maheshwari"""
import numpy as np
import time
from typing import List, Dict, Any, Optional
from ..circuit import Circuit
from ..backend import FastBackend as SimulatorBackend

class PerformanceAnalyzer:
    """Analyzes quantum circuit performance."""
    
    def __init__(self):
        self.results = []
        self.baseline_time = None
        
    def benchmark_circuit(self, circuit: Circuit, shots_list: List[int] = [100, 1000, 10000]) -> Dict[str, Any]:
        """Benchmark circuit execution time across shot counts."""
        backend = SimulatorBackend()
        benchmark_results = {
            'circuit': circuit.name,
            'num_qubits': circuit.num_qubits,
            'gate_count': len(circuit.gates),
            'depth': circuit.depth(),
            'shots': {},
            'total_time': 0.0
        }
        
        for shots in shots_list:
            start = time.perf_counter()
            result = backend.run(circuit, shots=shots)
            end = time.perf_counter()
            
            exec_time = end - start
            benchmark_results['shots'][shots] = {
                'time': exec_time,
                'time_per_shot_ms': (exec_time / shots) * 1000,
                'success': result['success']
            }
            benchmark_results['total_time'] += exec_time
            
        self.results.append(benchmark_results)
        return benchmark_results
        
    def benchmark_scaling(self, circuit_factory, qubit_range: List[int]) -> Dict[str, Any]:
        """Benchmark how performance scales with qubit count."""
        scaling_results = {
            'qubits': [],
            'gate_counts': [],
            'depths': [],
            'times': [],
            'times_per_qubit': []
        }
        
        for num_qubits in qubit_range:
            circuit = circuit_factory(num_qubits)
            
            backend = SimulatorBackend()
            start = time.perf_counter()
            result = backend.run(circuit, shots=100)
            end = time.perf_counter()
            
            exec_time = end - start
            
            scaling_results['qubits'].append(num_qubits)
            scaling_results['gate_counts'].append(len(circuit.gates))
            scaling_results['depths'].append(circuit.depth())
            scaling_results['times'].append(exec_time)
            scaling_results['times_per_qubit'].append(exec_time / num_qubits if num_qubits > 0 else 0)
            
        return scaling_results
        
    def compare_circuits(self, circuits: List[Circuit], labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Compare performance of multiple circuits."""
        comparison = {
            'circuits': [],
            'metrics': []
        }
        
        for i, circuit in enumerate(circuits):
            label = labels[i] if labels and i < len(labels) else f"Circuit {i+1}"
            
            benchmark = self.benchmark_circuit(circuit, shots_list=[1000])
            
            comparison['circuits'].append(label)
            comparison['metrics'].append({
                'qubits': circuit.num_qubits,
                'gates': len(circuit.gates),
                'depth': circuit.depth(),
                'time_1000_shots': benchmark['shots'][1000]['time']
            })
            
        return comparison
        
    def analyze_gate_overhead(self, circuit: Circuit) -> Dict[str, Any]:
        """Analyze gate type distribution and overhead."""
        gate_counts: Dict[str, int] = {}
        for gate in circuit.gates:
            name = gate.name.split('(')[0].upper()
            gate_counts[name] = gate_counts.get(name, 0) + 1
        
        analysis = {
            'total_gates': sum(gate_counts.values()),
            'unique_gate_types': len(gate_counts),
            'gate_distribution': gate_counts,
            'single_qubit_ratio': 0.0,
            'two_qubit_ratio': 0.0
        }
        
        single_qubit = sum(count for gate, count in gate_counts.items() 
                            if gate in ['X', 'Y', 'Z', 'H', 'S', 'T', 'RX', 'RY', 'RZ'])
        two_qubit = sum(count for gate, count in gate_counts.items() 
                          if gate in ['CNOT', 'CZ', 'SWAP'])
        
        total = analysis['total_gates']
        if total > 0:
            analysis['single_qubit_ratio'] = single_qubit / total
            analysis['two_qubit_ratio'] = two_qubit / total
            
        return analysis
        
    def export_report(self, filepath: str):
        """Export performance report to JSON."""
        import json
        
        report = {
            'timestamp': time.time(),
            'results': self.results
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
            
    def plot_scaling(self, scaling_results: Dict[str, Any]):
        """Plot scaling results using matplotlib."""
        try:
            import matplotlib.pyplot as plt
            
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))
            
            # Time vs Qubits
            axes[0].plot(scaling_results['qubits'], scaling_results['times'], 'bo-')
            axes[0].set_xlabel('Number of Qubits')
            axes[0].set_ylabel('Execution Time (s)')
            axes[0].set_title('Scaling: Time vs Qubits')
            axes[0].grid(True)
            
            # Time per qubit
            axes[1].plot(scaling_results['qubits'], scaling_results['times_per_qubit'], 'ro-')
            axes[1].set_xlabel('Number of Qubits')
            axes[1].set_ylabel('Time per Qubit (s)')
            axes[1].set_title('Scaling: Time per Qubit')
            axes[1].grid(True)
            
            plt.tight_layout()
            return plt
        except ImportError:
            return "matplotlib not installed"
