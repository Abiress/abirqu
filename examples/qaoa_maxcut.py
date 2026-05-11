"""
QAOA — Quantum Approximate Optimisation Algorithm
===================================================
QAOA solves combinatorial optimisation problems using a parameterised
quantum circuit. Here we solve the MaxCut problem on a small graph.

MaxCut: partition graph vertices into two sets (S and S̄) to maximise
the number of edges that cross between them.

Graph used (triangle + extra edge):
    0 ── 1
    │ ╲  │
    │   ╲│
    2 ── 3
"""
from typing import List, Tuple
from abirqu import Circuit, NumPySimulator
from abirqu.algorithms import qaoa_maxcut


def evaluate_cut(partition: str, edges: List[Tuple[int, int]]) -> int:
    """Count edges that cross between the two partitions."""
    return sum(1 for u, v in edges if partition[u] != partition[v])


def run_qaoa(edges: List[Tuple[int, int]], n_qubits: int, label: str) -> None:
    print(f"\n=== {label} ===")
    print(f"  Vertices : {n_qubits}")
    print(f"  Edges    : {edges}")
    max_cut = sum(1 for _ in edges)  # upper bound = all edges
    print(f"  Max possible cut : {max_cut}")

    # Run QAOA circuit
    c = qaoa_maxcut(num_qubits=n_qubits, edges=edges, beta=0.4, gamma=0.7)
    sim = NumPySimulator(n_qubits)
    sim.run_circuit(c)

    probs = sim.get_probabilities()

    # Evaluate cuts for all bitstrings
    cuts = {state: evaluate_cut(state, edges) for state in probs}

    # Show top results
    print("\n  Top 6 states by cut value:")
    sorted_states = sorted(probs.items(), key=lambda x: (cuts[x[0]], x[1]), reverse=True)
    for state, p in sorted_states[:6]:
        cut_val = cuts[state]
        bar = "█" * round(p * 40)
        print(f"  |{state}⟩  cut={cut_val}  p={p:.4f}  {bar}")

    # Best state found
    best_state = max(probs, key=lambda s: cuts[s])
    best_cut = cuts[best_state]
    print(f"\n  Best state found : |{best_state}⟩  (cut = {best_cut}/{max_cut})")
    approx_ratio = best_cut / max_cut if max_cut > 0 else 1.0
    print(f"  Approximation ratio : {approx_ratio:.3f}")


def maxcut_brute_force(edges: List[Tuple[int, int]], n_qubits: int) -> Tuple[int, str]:
    """Classical brute force MaxCut for comparison."""
    best_cut, best_part = 0, "0" * n_qubits
    for i in range(2 ** n_qubits):
        partition = format(i, f"0{n_qubits}b")
        cut = evaluate_cut(partition, edges)
        if cut > best_cut:
            best_cut, best_part = cut, partition
    return best_cut, best_part


if __name__ == "__main__":
    print("AbirQu — QAOA MaxCut")
    print("====================")

    # ── Example 1: Triangle graph (3 nodes, 3 edges) ──
    edges_triangle = [(0, 1), (1, 2), (0, 2)]
    run_qaoa(edges=edges_triangle, n_qubits=3, label="Triangle Graph MaxCut")

    opt_cut, opt_part = maxcut_brute_force(edges_triangle, 3)
    print(f"\n  Classical optimal: |{opt_part}⟩  (cut = {opt_cut})")

    # ── Example 2: 4-node path graph ──
    edges_path = [(0, 1), (1, 2), (2, 3)]
    run_qaoa(edges=edges_path, n_qubits=4, label="Path Graph MaxCut (4 nodes)")

    opt_cut4, opt_part4 = maxcut_brute_force(edges_path, 4)
    print(f"\n  Classical optimal: |{opt_part4}⟩  (cut = {opt_cut4})")

    print("\nDone! Try examples/quantum_ml.py next.")
