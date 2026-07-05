"""
Variational Quantum Eigensolver (VQE) — H₂ Molecule
=====================================================
VQE is a hybrid quantum-classical algorithm to find the ground-state energy
of a quantum Hamiltonian. Here we simulate a simplified H₂ (hydrogen molecule)
energy landscape using a parameterised ansatz.

The true FCI ground state energy of H₂ at equilibrium is ≈ −1.137 Ha.
This demo uses a parameterised ansatz and gradient-free optimisation.
"""
import math
import random
from typing import List, Tuple
from abirqu import Circuit
from abirqu.primitives import QuantumRun


# ─────────────────────────────────────────────────────────────
# Simplified H₂ Hamiltonian expectation value
# ─────────────────────────────────────────────────────────────

def h2_energy(circuit: Circuit) -> float:
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

    # Run the circuit to get probabilities
    result = QuantumRun(circuit, shots=4096)
    probs = result.probabilities

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
# Parameterised ansatz
# ─────────────────────────────────────────────────────────────

def make_vqe_circuit(params: List[float], n_qubits: int = 2) -> Circuit:
    """Build a parameterised VQE circuit with RY rotations and CNOT entanglement."""
    c = Circuit(n_qubits, name="vqe_ansatz")
    idx = 0
    for layer in range(2):
        for q in range(n_qubits):
            if idx < len(params):
                c.ry(q, params[idx])
                idx += 1
        for q in range(n_qubits - 1):
            c.cnot(q, q + 1)
    c.measure_all()
    return c


# ─────────────────────────────────────────────────────────────
# Variational optimisation (Nelder-Mead style, parameter sweep)
# ─────────────────────────────────────────────────────────────

def run_vqe(n_qubits: int = 2, iterations: int = 30) -> Tuple[float, List[float]]:
    """Run VQE with random parameter initialisation and gradient-free search."""

    n_params = 4  # 2 layers × 2 qubits
    params = [random.uniform(0, 2 * math.pi) for _ in range(n_params)]
    best_energy = float("inf")
    best_params = params[:]

    print(f"  Ansatz: {n_qubits} qubits, 2 layers, {n_params} parameters")
    print(f"  Running {iterations} VQE iterations...\n")

    energy_history = []

    for it in range(iterations):
        # Build circuit with current parameters
        c = make_vqe_circuit(params, n_qubits)
        energy = h2_energy(c)
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
    best_e, history = run_vqe(n_qubits=2, iterations=30)

    print(f"\n{'─'*45}")
    print(f"  Best VQE energy  : {best_e:.6f} Ha")
    print(f"  FCI reference    : -1.137270 Ha")
    print(f"  Energy error     : {abs(best_e - (-1.137270)):.6f} Ha")
    print(f"{'─'*45}")
    print("\nNote: This is a simplified 2-qubit VQE demo. A production VQE")
    print("would use a larger basis set, more qubits, and a better optimizer.")
    print("\nDone! Try examples/qaoa_maxcut.py next.")
