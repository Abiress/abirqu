"""
Quick Start — AbirQu quantum computing library
================================================
Demonstrates the core building blocks:
  • Creating a circuit
  • Applying gates
  • Running a simulation
  • Reading probabilities
"""

from abirqu import Circuit, NumPySimulator


# ──────────────────────────────────────────────────────────────
# 1. Bell State  (maximally entangled 2-qubit state)
# ──────────────────────────────────────────────────────────────
def bell_state() -> None:
    print("\n=== Bell State ===")
    c = Circuit(2, name="Bell")
    c.h(0)          # Put qubit-0 into superposition
    c.cnot(0, 1)    # Entangle qubit-1 with qubit-0
    c.measure_all()

    sim = NumPySimulator(2)
    sim.run_circuit(c)

    print(f"State vector: {sim.state}")
    probs = sim.get_probabilities()
    print("Measurement probabilities:")
    for state, p in sorted(probs.items()):
        bar = "█" * round(p * 40)
        print(f"  |{state}⟩  {p:.4f}  {bar}")


# ──────────────────────────────────────────────────────────────
# 2. GHZ State  (3-qubit entangled state)
# ──────────────────────────────────────────────────────────────
def ghz_state() -> None:
    print("\n=== GHZ State (3 qubits) ===")
    c = Circuit(3, name="GHZ")
    c.h(0)
    c.cnot(0, 1)
    c.cnot(0, 2)
    c.measure_all()

    sim = NumPySimulator(3)
    sim.run_circuit(c)

    probs = sim.get_probabilities()
    print("Measurement probabilities:")
    for state, p in sorted(probs.items()):
        if p > 1e-6:
            bar = "█" * round(p * 40)
            print(f"  |{state}⟩  {p:.4f}  {bar}")


# ──────────────────────────────────────────────────────────────
# 3. Superposition & Phase
# ──────────────────────────────────────────────────────────────
def superposition_demo() -> None:
    print("\n=== Superposition & Phase ===")
    c = Circuit(1, name="Phase")
    c.h(0)   # |0⟩ → (|0⟩ + |1⟩)/√2
    c.s(0)   # Apply S gate: phase |1⟩ by i
    c.h(0)   # Rotate back: constructive/destructive interference
    c.measure_all()

    sim = NumPySimulator(1)
    sim.run_circuit(c)
    probs = sim.get_probabilities()
    print(f"Probabilities after H-S-H: {probs}")


# ──────────────────────────────────────────────────────────────
# 4. Export to OpenQASM 2.0
# ──────────────────────────────────────────────────────────────
def export_qasm() -> None:
    print("\n=== Export to OpenQASM 2.0 ===")
    c = Circuit(2, name="BellQASM")
    c.h(0)
    c.cnot(0, 1)
    c.measure_all()
    qasm = c.to_qasm()
    print(qasm)


# ──────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("AbirQu Quick Start")
    print("==================")
    bell_state()
    ghz_state()
    superposition_demo()
    export_qasm()
    print("\nDone! Try examples/grover_search.py next.")
