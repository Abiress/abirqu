"""
Variational Quantum Eigensolver (VQE) — H₂ Molecule
======================================================
VQE is a hybrid quantum-classical algorithm to find the ground-state energy
of a quantum Hamiltonian. Here we simulate a simplified H₂ (hydrogen molecule)
energy landscape using a hardware-efficient ansatz.

The true FCI ground state energy of H₂ at equilibrium is ≈ −1.137 Ha.
This demo uses a parameterised ansatz and gradient-free optimisation.
"""
import math
import random
from typing import List, Tuple
from abirqu import Circuit, NumPySimulator
from abirqu.algorithms import vqe_ansatz_template


# ─────────────────────────────────────────────────────────────
# Simplified H₂ Hamiltonian expectation value
# ─────────────────────────────────────────────────────────────

def h2_energy(probs: dict) -> float:
    """
    Approximate the H₂ ground state energy using a simplified 2-qubit mapping.

    Hamiltonian coefficients at equilibrium bond length (STO-3G basis):
        H = g₀ I + g₁ Z₀ + g₂ Z₁ + g₃ Z₀Z₁ + g₄ X₀X₁ + g₅ Y₀Y₁
    Using mapped coefficients (approximate):
    """
    g0 = -0.4804
    g1 = +0.3435
    g2 = -0.4347
    g3 = +0.5716
    g4 = +0.0910
    g5 = +0.0910

    # Extract diagonal terms from probabilities
    p00 = probs.get("00", 0.0)
    p01 = probs.get("01", 0.0)
    p10 = probs.get("10", 0.0)
    p11 = probs.get("11", 0.0)

    z0 = (p00 + p01) - (p10 + p11)   # ⟨Z₀⟩
    z1 = (p00 + p10) - (p01 + p11)   # ⟨Z₁⟩
    z0z1 = (p00 + p11) - (p01 + p10) # ⟨Z₀Z₁⟩

    # Off-diagonal terms: XX and YY measured with Hadamard / S basis change
    # For demo purposes we use a simplified model based on state overlap
    xx_yy = 2 * g4 * (p00 - p11)

    energy = g0 + g1 * z0 + g2 * z1 + g3 * z0z1 + xx_yy
    return energy


# ─────────────────────────────────────────────────────────────
# Variational optimisation (Nelder-Mead style, parameter sweep)
# ─────────────────────────────────────────────────────────────

def run_vqe(n_qubits: int = 2, depth: int = 2, iterations: int = 30) -> Tuple[float, List[float]]:
    """Run VQE with random parameter initialisation and gradient-free search."""

    # Count parameterised gates in the ansatz
    template = vqe_ansatz_template(n_qubits, depth)
    n_params = sum(1 for g in template.gates if g.name in ("RX", "RY", "RZ"))

    # Initialise parameters randomly
    params = [random.uniform(0, 2 * math.pi) for _ in range(n_params)]
    best_energy = float("inf")
    best_params = params[:]

    print(f"  Ansatz: {n_qubits} qubits, depth={depth}, {n_params} parameters")
    print(f"  Running {iterations} VQE iterations...\n")

    energy_history = []

    for it in range(iterations):
        # Evaluate energy at current params
        c = vqe_ansatz_template(n_qubits, depth)
        sim = NumPySimulator(n_qubits)
        sim.run_circuit(c)
        probs = sim.get_probabilities()

        energy = h2_energy(probs)
        energy_history.append(energy)

        if energy < best_energy:
            best_energy = energy
            best_params = params[:]

        # Simple random perturbation (parameter shift-style)
        idx = random.randint(0, n_params - 1)
        params[idx] += random.gauss(0, 0.3)

        if (it + 1) % 10 == 0:
            print(f"  Iter {it+1:3d}: energy = {energy:.6f} Ha  (best = {best_energy:.6f} Ha)")

    return best_energy, energy_history


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("AbirQu — VQE for H₂ Molecule")
    print("==============================")
    print("\nH₂ ground state FCI energy ≈ −1.137 Hartree (reference)\n")

    random.seed(42)
    best_e, history = run_vqe(n_qubits=2, depth=3, iterations=30)

    print(f"\n{'─'*45}")
    print(f"  Best VQE energy  : {best_e:.6f} Ha")
    print(f"  FCI reference    : -1.137270 Ha")
    print(f"  Energy error     : {abs(best_e - (-1.137270)):.6f} Ha")
    print(f"{'─'*45}")
    print("\nConvergence trace (every iteration):")
    for i, e in enumerate(history):
        bar = "█" * max(0, round((e + 1.2) * 30))
        print(f"  Iter {i+1:3d}  {e:+.5f} Ha  |{bar:<30}|")

    print("\nDone! Try examples/qaoa_maxcut.py next.")
