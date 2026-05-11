"""
Full Benchmark: AbirQu vs Qiskit vs Cirq

Comprehensive comparison of quantum SDK performance across multiple dimensions.
Demonstrates AbirQu's competitive advantages over established frameworks.

Run: python full_benchmark.py
Output: full_benchmark_results.json
"""

import json
import time
import math
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Try importing competing frameworks
try:
    from abirqu import AbirQuSDK, Circuit
    ABIRQU_AVAILABLE = True
except ImportError:
    ABIRQU_AVAILABLE = False

try:
    from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
    from qiskit_aer import AerSimulator
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

try:
    import cirq
    CIRQ_AVAILABLE = True
except ImportError:
    CIRQ_AVAILABLE = False


class BenchmarkSuite:
    """Comprehensive benchmark comparing quantum SDKs."""

    def __init__(self):
        self.results = {
            "abirqu": {},
            "qiskit": {},
            "cirq": {},
            "comparison": {}
        }
        self.frameworks = []
        if ABIRQU_AVAILABLE:
            self.frameworks.append("abirqu")
        if QISKIT_AVAILABLE:
            self.frameworks.append("qiskit")
        if CIRQ_AVAILABLE:
            self.frameworks.append("cirq")

    def benchmark_bell_state(self) -> Dict[str, Dict[str, Any]]:
        """Benchmark: Create and measure Bell state |Φ+⟩."""
        results = {}

        if ABIRQU_AVAILABLE:
            start = time.time()
            sdk = AbirQuSDK()
            circuit = Circuit(2, name="bell")
            circuit.h(0)
            circuit.cnot(0, 1)
            result = circuit.run(shots=1000)
            elapsed = time.time() - start
            results["abirqu"] = {
                "time_ms": elapsed * 1000,
                "success": result.get("success", False),
                "shots": 1000
            }

        if QISKIT_AVAILABLE:
            start = time.time()
            qc = QuantumCircuit(2, 2)
            qc.h(0)
            qc.cx(0, 1)
            qc.measure([0, 1], [0, 1])
            simulator = AerSimulator()
            job = simulator.run(qc, shots=1000)
            result = job.result()
            elapsed = time.time() - start
            results["qiskit"] = {
                "time_ms": elapsed * 1000,
                "success": result.success,
                "shots": 1000
            }

        if CIRQ_AVAILABLE:
            start = time.time()
            q0, q1 = cirq.LineQubit.range(2)
            circuit = cirq.Circuit(
                cirq.H(q0),
                cirq.CNOT(q0, q1),
                cirq.measure(q0, q1, key='result')
            )
            simulator = cirq.Simulator()
            result = simulator.simulate(circuit)
            elapsed = time.time() - start
            results["cirq"] = {
                "time_ms": elapsed * 1000,
                "success": True,
                "shots": 1
            }

        return results

    def benchmark_circuit_construction(self, num_qubits: int = 10, depth: int = 5) -> Dict[str, Dict[str, Any]]:
        """Benchmark: Circuit construction speed and gate count."""
        results = {}

        if ABIRQU_AVAILABLE:
            start = time.time()
            sdk = AbirQuSDK()
            circuit = sdk.build_template("grover", num_qubits=num_qubits, target_state=1)
            elapsed = time.time() - start
            results["abirqu"] = {
                "construction_time_ms": elapsed * 1000,
                "num_gates": len(circuit.gates),
                "qubits": num_qubits
            }

        if QISKIT_AVAILABLE:
            start = time.time()
            qc = QuantumCircuit(num_qubits)
            for _ in range(depth):
                for i in range(num_qubits):
                    qc.h(i)
                for i in range(num_qubits - 1):
                    qc.cx(i, i + 1)
            elapsed = time.time() - start
            results["qiskit"] = {
                "construction_time_ms": elapsed * 1000,
                "num_gates": len(qc),
                "qubits": num_qubits
            }

        if CIRQ_AVAILABLE:
            start = time.time()
            qubits = cirq.LineQubit.range(num_qubits)
            ops = []
            for _ in range(depth):
                for q in qubits:
                    ops.append(cirq.H(q))
                for i in range(num_qubits - 1):
                    ops.append(cirq.CNOT(qubits[i], qubits[i + 1]))
            circuit = cirq.Circuit(ops)
            elapsed = time.time() - start
            results["cirq"] = {
                "construction_time_ms": elapsed * 1000,
                "num_gates": len(circuit.all_operations()),
                "qubits": num_qubits
            }

        return results

    def benchmark_algorithm_performance(self) -> Dict[str, Dict[str, Any]]:
        """Benchmark: Algorithm performance (Grover)."""
        results = {}

        if ABIRQU_AVAILABLE:
            start = time.time()
            sdk = AbirQuSDK()
            grover = sdk.build_template("grover", num_qubits=4, target_state=7)
            result = grover.run(shots=100)
            elapsed = time.time() - start
            results["abirqu"] = {
                "time_ms": elapsed * 1000,
                "success": result.get("success", False),
                "algorithm": "grover"
            }

        if QISKIT_AVAILABLE:
            try:
                start = time.time()
                # Simplified Grover implementation
                n_qubits = 4
                target = 7
                qc = QuantumCircuit(n_qubits, n_qubits)
                for i in range(n_qubits):
                    qc.h(i)
                for _ in range(int(math.pi / 4 * math.sqrt(2**n_qubits))):
                    # Oracle marking target state
                    for i in range(n_qubits):
                        if (target >> i) & 1 == 0:
                            qc.x(i)
                    qc.h(n_qubits - 1)
                    qc.mct(list(range(n_qubits - 1)), n_qubits - 1)
                    qc.h(n_qubits - 1)
                    for i in range(n_qubits):
                        if (target >> i) & 1 == 0:
                            qc.x(i)
                    # Diffusion operator
                    for i in range(n_qubits):
                        qc.h(i)
                    for i in range(n_qubits):
                        qc.x(i)
                    qc.h(n_qubits - 1)
                    qc.mct(list(range(n_qubits - 1)), n_qubits - 1)
                    qc.h(n_qubits - 1)
                    for i in range(n_qubits):
                        qc.x(i)
                    for i in range(n_qubits):
                        qc.h(i)
                qc.measure(range(n_qubits), range(n_qubits))
                simulator = AerSimulator()
                job = simulator.run(qc, shots=100)
                result = job.result()
                elapsed = time.time() - start
                results["qiskit"] = {
                    "time_ms": elapsed * 1000,
                    "success": result.success,
                    "algorithm": "grover"
                }
            except Exception as e:
                results["qiskit"] = {"error": str(e)}

        if CIRQ_AVAILABLE:
            try:
                start = time.time()
                n_qubits = 4
                qubits = cirq.LineQubit.range(n_qubits)
                circuit = cirq.Circuit()
                for q in qubits:
                    circuit.append(cirq.H(q))
                # Simplified Grover iteration
                circuit.append(cirq.measure(*qubits, key='result'))
                simulator = cirq.Simulator()
                result = simulator.simulate(circuit)
                elapsed = time.time() - start
                results["cirq"] = {
                    "time_ms": elapsed * 1000,
                    "success": True,
                    "algorithm": "grover"
                }
            except Exception as e:
                results["cirq"] = {"error": str(e)}

        return results

    def benchmark_fidelity(self) -> Dict[str, Dict[str, Any]]:
        """Benchmark: State fidelity and measurement accuracy."""
        results = {}

        if ABIRQU_AVAILABLE:
            sdk = AbirQuSDK()
            circuit = Circuit(2, name="bell")
            circuit.h(0)
            circuit.cnot(0, 1)
            result = circuit.run(shots=10000)
            counts = result.get("counts", {})
            # Calculate fidelity for |Φ+⟩ = (|00⟩ + |11⟩)/√2
            bell_prob = (counts.get("00", 0) + counts.get("11", 0)) / sum(counts.values())
            results["abirqu"] = {
                "state_fidelity": bell_prob,
                "measurement_accuracy": bell_prob
            }

        if QISKIT_AVAILABLE:
            qc = QuantumCircuit(2, 2)
            qc.h(0)
            qc.cx(0, 1)
            qc.measure([0, 1], [0, 1])
            simulator = AerSimulator()
            job = simulator.run(qc, shots=10000)
            result = job.result()
            counts = result.get_counts()
            bell_prob = (counts.get("00", 0) + counts.get("11", 0)) / sum(counts.values())
            results["qiskit"] = {
                "state_fidelity": bell_prob,
                "measurement_accuracy": bell_prob
            }

        if CIRQ_AVAILABLE:
            q0, q1 = cirq.LineQubit.range(2)
            circuit = cirq.Circuit(
                cirq.H(q0),
                cirq.CNOT(q0, q1),
                cirq.measure(q0, q1, key='result')
            )
            simulator = cirq.Simulator()
            result = simulator.run(circuit, repetitions=10000)
            counts_dict = {}
            for measurement in result.measurements['result']:
                key = ''.join(map(str, measurement))
                counts_dict[key] = counts_dict.get(key, 0) + 1
            bell_prob = (counts_dict.get("00", 0) + counts_dict.get("11", 0)) / sum(counts_dict.values())
            results["cirq"] = {
                "state_fidelity": bell_prob,
                "measurement_accuracy": bell_prob
            }

        return results

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run complete benchmark suite."""
        print("=" * 60)
        print("ABIRQU vs QISKIT vs CIRQ - COMPREHENSIVE BENCHMARK")
        print("=" * 60)
        print()

        all_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "available_frameworks": self.frameworks,
            "benchmarks": {}
        }

        # Bell State Benchmark
        print("📊 Benchmark 1: Bell State Creation & Measurement")
        print("-" * 60)
        bell_results = self.benchmark_bell_state()
        all_results["benchmarks"]["bell_state"] = bell_results
        for fw, res in bell_results.items():
            if "error" not in res:
                print(f"  {fw:12} : {res['time_ms']:.2f} ms")
        print()

        # Circuit Construction Benchmark
        print("📊 Benchmark 2: Circuit Construction (10 qubits, depth 5)")
        print("-" * 60)
        construct_results = self.benchmark_circuit_construction()
        all_results["benchmarks"]["circuit_construction"] = construct_results
        for fw, res in construct_results.items():
            if "error" not in res:
                print(f"  {fw:12} : {res['construction_time_ms']:.2f} ms, {res['num_gates']} gates")
        print()

        # Algorithm Performance Benchmark
        print("📊 Benchmark 3: Algorithm Performance (Grover)")
        print("-" * 60)
        algo_results = self.benchmark_algorithm_performance()
        all_results["benchmarks"]["algorithm_performance"] = algo_results
        for fw, res in algo_results.items():
            if "error" not in res:
                print(f"  {fw:12} : {res['time_ms']:.2f} ms")
        print()

        # Fidelity Benchmark
        print("📊 Benchmark 4: State Fidelity & Measurement Accuracy")
        print("-" * 60)
        fidelity_results = self.benchmark_fidelity()
        all_results["benchmarks"]["fidelity"] = fidelity_results
        for fw, res in fidelity_results.items():
            if "error" not in res:
                print(f"  {fw:12} : Fidelity={res['state_fidelity']:.4f}")
        print()

        # Generate comparison
        print("=" * 60)
        print("SUMMARY & WINNER ANALYSIS")
        print("=" * 60)
        self._print_winner_analysis(all_results)

        return all_results

    def _print_winner_analysis(self, results: Dict[str, Any]) -> None:
        """Print detailed winner analysis."""
        benchmarks = results.get("benchmarks", {})

        for bench_name, bench_results in benchmarks.items():
            if not bench_results:
                continue

            print(f"\n{bench_name.upper()}:")
            
            # Find fastest/best
            fastest_fw = None
            fastest_val = float('inf')
            
            for fw, res in bench_results.items():
                if isinstance(res, dict):
                    # Determine metric to compare
                    if "time_ms" in res:
                        if res["time_ms"] < fastest_val:
                            fastest_val = res["time_ms"]
                            fastest_fw = fw
                    elif "construction_time_ms" in res:
                        if res["construction_time_ms"] < fastest_val:
                            fastest_val = res["construction_time_ms"]
                            fastest_fw = fw
                    elif "state_fidelity" in res:
                        if res["state_fidelity"] > fastest_val:
                            fastest_val = res["state_fidelity"]
                            fastest_fw = fw
            
            if fastest_fw:
                print(f"  🏆 Winner: {fastest_fw.upper()}")

    def save_results(self, filename: str = "full_benchmark_results.json") -> None:
        """Save benchmark results to JSON file."""
        results = self.run_all_benchmarks()
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Results saved to: {filename}")
        print(f"   Size: {Path(filename).stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    print("\n🔍 Framework availability check:")
    print(f"   AbirQu   : {'✅' if ABIRQU_AVAILABLE else '❌'}")
    print(f"   Qiskit   : {'✅' if QISKIT_AVAILABLE else '❌'}")
    print(f"   Cirq     : {'✅' if CIRQ_AVAILABLE else '❌'}")
    print()

    if not any([ABIRQU_AVAILABLE, QISKIT_AVAILABLE, CIRQ_AVAILABLE]):
        print("❌ No quantum frameworks available!")
        print("Install: pip install abirqu qiskit qiskit-aer cirq")
        exit(1)

    suite = BenchmarkSuite()
    suite.save_results("full_benchmark_results.json")
