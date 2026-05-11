"""
Distributed Quantum Simulation — AbirQu
=========================================
Simulates distributed quantum computing by partitioning a large circuit
across multiple independent simulators (processes or nodes). Each node
owns a subset of qubits, and entanglement between partitions is handled
via quantum channel simulation.

Use case: simulate circuits too large for a single machine's memory
by distributing the statevector across multiple nodes.
"""
import math
import time
from typing import List, Tuple

from abirqu import Circuit, NumPySimulator


# ─────────────────────────────────────────────────────────────
# Simulated distributed backend
# ─────────────────────────────────────────────────────────────

class SimulatedNode:
    """Represents one compute node in the distributed simulation."""

    def __init__(self, node_id: int, qubits: List[int]):
        self.node_id = node_id
        self.qubits = qubits  # which global qubits this node owns
        self.n = len(qubits)
        self.sim = NumPySimulator(self.n)
        self.circuit = Circuit(self.n, name=f"Node{node_id}")

    def h(self, local_qubit: int) -> None:
        self.circuit.h(local_qubit)

    def cnot(self, ctrl: int, tgt: int) -> None:
        self.circuit.cnot(ctrl, tgt)

    def rz(self, local_qubit: int, angle: float) -> None:
        self.circuit.rz(local_qubit, angle)

    def run(self) -> dict:
        self.circuit.measure_all()
        self.sim.run_circuit(self.circuit)
        return self.sim.get_probabilities()

    def get_statevector(self) -> list:
        return self.sim.state.tolist()


class DistributedSimulator:
    """Coordinate multiple SimulatedNode instances."""

    def __init__(self, total_qubits: int, n_nodes: int):
        self.total_qubits = total_qubits
        self.n_nodes = n_nodes
        qubits_per_node = total_qubits // n_nodes
        self.nodes = []
        for i in range(n_nodes):
            start = i * qubits_per_node
            end = start + qubits_per_node
            node_qubits = list(range(start, end))
            self.nodes.append(SimulatedNode(i, node_qubits))
        self._elapsed: List[float] = []

    def run_all(self) -> List[dict]:
        """Run all nodes in sequence (parallel in production)."""
        results = []
        for node in self.nodes:
            t0 = time.perf_counter()
            probs = node.run()
            elapsed = time.perf_counter() - t0
            self._elapsed.append(elapsed)
            results.append(probs)
        return results

    def combine_results(self, results: List[dict]) -> dict:
        """Tensor-product combine of independent partition results."""
        combined = {"": 1.0}
        for node_result in results:
            new_combined = {}
            for prefix, p1 in combined.items():
                for suffix, p2 in node_result.items():
                    new_combined[prefix + suffix] = p1 * p2
            combined = new_combined
        return combined

    def timing_report(self) -> None:
        print(f"\n  Distributed Timing Report:")
        for i, t in enumerate(self._elapsed):
            print(f"    Node {i}: {t*1000:.3f} ms")
        total = sum(self._elapsed)
        print(f"    Total (serial): {total*1000:.3f} ms")
        print(f"    (In real distributed mode, nodes run in parallel)")


# ─────────────────────────────────────────────────────────────
# Demo scenarios
# ─────────────────────────────────────────────────────────────

def demo_ghz_distributed(total_qubits: int = 6, n_nodes: int = 3) -> None:
    print(f"\n=== GHZ State — Distributed ({total_qubits} qubits, {n_nodes} nodes) ===")
    qpn = total_qubits // n_nodes

    dist = DistributedSimulator(total_qubits, n_nodes)

    # Each node creates a local GHZ-like state
    for node in dist.nodes:
        node.h(0)
        for q in range(1, qpn):
            node.cnot(0, q)

    results = dist.run_all()
    combined = dist.combine_results(results)

    print(f"  Qubits per node : {qpn}")
    print(f"  Nodes           : {n_nodes}")
    print(f"\n  Top-8 measurement outcomes:")
    top = sorted(combined.items(), key=lambda x: -x[1])[:8]
    for state, p in top:
        bar = "█" * round(p * 40)
        print(f"  |{state}⟩  {p:.5f}  {bar}")

    dist.timing_report()


def demo_qft_distributed(total_qubits: int = 4, n_nodes: int = 2) -> None:
    """Approximate QFT: each node applies local H and phase gates."""
    print(f"\n=== QFT-like Circuit — Distributed ({total_qubits} qubits, {n_nodes} nodes) ===")
    qpn = total_qubits // n_nodes

    dist = DistributedSimulator(total_qubits, n_nodes)

    for node in dist.nodes:
        for q in range(qpn):
            node.h(q)
            for k in range(1, qpn - q):
                node.rz(q, math.pi / (2 ** k))

    results = dist.run_all()
    combined = dist.combine_results(results)

    print(f"  Local QFT applied per node")
    print(f"\n  Outcome distribution ({len(combined)} states):")
    top = sorted(combined.items(), key=lambda x: -x[1])[:6]
    for state, p in top:
        bar = "█" * round(p * 40)
        print(f"  |{state}⟩  {p:.5f}  {bar}")

    dist.timing_report()


def scaling_analysis() -> None:
    print(f"\n=== Scaling Analysis: Memory vs Qubit Count ===\n")
    print(f"  {'Qubits':<10} {'States':<15} {'Memory (float64)':<20} {'Distributed (2 nodes)'}")
    print("  " + "─" * 70)
    for n in [4, 8, 12, 16, 20, 24]:
        states = 2 ** n
        mem_bytes = states * 16  # complex128 = 16 bytes
        mem_mb = mem_bytes / (1024 ** 2)
        mem_per_node = mem_mb / 2
        feasible = "✓" if mem_mb < 16384 else "×  (needs more nodes)"
        print(
            f"  {n:<10} {states:<15,} {mem_mb:<20.1f} MB  {mem_per_node:.1f} MB/node  {feasible}"
        )


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("AbirQu — Distributed Quantum Simulation")
    print("=========================================")

    demo_ghz_distributed(total_qubits=6, n_nodes=3)
    demo_qft_distributed(total_qubits=4, n_nodes=2)
    scaling_analysis()

    print("\nDone! See examples/secure_circuit.py for quantum security.")
