"""
Grover's Search Algorithm — AbirQu
=====================================
Grover's algorithm finds a marked item in an unsorted database of N items
in O(√N) queries, quadratically faster than classical exhaustive search.

Example: search for |11⟩ (state 3) among 4 computational basis states.
"""
import math
from abirqu import Circuit, NumPySimulator
from abirqu.algorithms import grover_search, grover_template


def run_grover(target_state: int, num_qubits: int) -> None:
    n_states = 2 ** num_qubits
    # Optimal: floor(π/4 · √N) — let the library decide (pass None)
    iterations = max(1, int(math.pi / 4 * math.sqrt(n_states)))

    print(f"\n=== Grover Search ===")
    print(f"  Database size : {n_states} states")
    print(f"  Target state  : |{target_state:0{num_qubits}b}⟩  (decimal {target_state})")
    print(f"  Iterations    : {iterations}")

    # Build and simulate (pass None to let grover_search choose optimal)
    circuit = grover_search(
        target_state=target_state,
        num_qubits=num_qubits,
        iterations=None,
    )

    sim = NumPySimulator(num_qubits)
    sim.run_circuit(circuit)

    probs = sim.get_probabilities()
    print("\nMeasurement probabilities:")
    for state_bits, p in sorted(probs.items(), key=lambda x: -x[1]):
        bar = "█" * round(p * 40)
        marker = " ← TARGET" if int(state_bits, 2) == target_state else ""
        print(f"  |{state_bits}⟩  {p:.4f}  {bar}{marker}")

    # Sanity check
    target_bits = format(target_state, f"0{num_qubits}b")
    found_prob = probs.get(target_bits, 0.0)
    print(f"\nSuccess probability: {found_prob:.4f} (classical = {1/n_states:.4f})")
    speedup = found_prob / (1 / n_states)
    print(f"Quantum speedup factor: {speedup:.1f}×")


def compare_iterations() -> None:
    """Show how probability grows with Grover iterations."""
    print("\n=== Grover Iteration Sweep ===")
    print(f"  Target: |11⟩ in 2-qubit space\n")

    target, n_qubits = 3, 2
    target_bits = format(target, f"0{n_qubits}b")

    for iters in [None, 1, 2]:
        circuit = grover_search(target_state=target, num_qubits=n_qubits, iterations=iters)
        sim = NumPySimulator(n_qubits)
        sim.run_circuit(circuit)
        p = sim.get_probabilities().get(target_bits, 0.0)
        bar = "█" * round(p * 30)
        iters_label = "optimal" if iters is None else f"{iters} iter"
        print(f"  {iters_label:>10}: p={p:.4f}  {bar}")


if __name__ == "__main__":
    print("AbirQu — Grover's Search Algorithm")
    print("===================================")

    # 2-qubit search (4 states, target = |11⟩)
    run_grover(target_state=3, num_qubits=2)

    # Show iteration effect
    compare_iterations()

    print("\nDone! Try examples/vqe_h2.py next.")
