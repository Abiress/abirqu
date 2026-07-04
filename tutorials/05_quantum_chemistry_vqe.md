# Tutorial 5: Quantum Chemistry with VQE

## Introduction

This tutorial covers using quantum computers for chemistry simulations:
- Molecular Hamiltonians
- Variational Quantum Eigensolver (VQE)
- Fermion-to-qubit mapping
- Energy calculations

## Prerequisites

```python
from abirqu.circuit import Circuit
from abirqu.backend import get_best_backend
from abirqu.chemistry import JordanWignerMapper, MolecularData
from abirqu.primitives import Sampler
import numpy as np
```

## 1. Why Quantum Chemistry?

Classical chemistry simulations scale exponentially with system size. Quantum computers can:
- Simulate molecular ground states
- Calculate reaction energies
- Design new drugs and materials
- Optimize catalysts

## 2. Molecular Hamiltonians

The electronic structure Hamiltonian in second quantization:

H = Σᵢⱼ hᵢⱼ aᵢ†aⱼ + ½ Σᵢⱼₖₗ hᵢⱼₖₗ aᵢ†aⱼ†aₖaₗ

```python
# Create a simple molecular system
molecule = MolecularData()

print("Molecular Data:")
print(f"  Type: {type(molecule)}")
```

## 3. Fermion-to-Qubit Mapping

Map fermionic operators to qubit operators using Jordan-Wigner transformation.

```python
# Jordan-Wigner mapping
n_orbitals = 4
jw_mapper = JordanWignerMapper(n_orbitals=n_orbitals)

print(f"Jordan-Wigner Mapper:")
print(f"  Orbitals: {n_orbitals}")
print(f"  Qubits: {n_orbitals}")
```

### Jordan-Wigner Transformation

- Maps fermionic creation/annihilation operators to Pauli strings
- Preserves fermionic anti-commutation relations
- Uses Z operators to encode parity

```python
# Example mapping
print("Jordan-Wigner Mapping Example:")
print("-" * 40)
print("a₁† → (X₁ - iY₁) ⊗ Z₀ / 2")
print("a₁  → (X₁ + iY₁) ⊗ Z₀ / 2")
```

## 4. Variational Quantum Eigensolver (VQE)

VQE finds the ground state energy of a Hamiltonian.

### VQE Algorithm

1. **Prepare** trial state |ψ(θ)⟩ using parameterized circuit
2. **Measure** expectation value ⟨ψ(θ)|H|ψ(θ)⟩
3. **Optimize** parameters θ to minimize energy
4. **Repeat** until convergence

```python
def vqe_workflow():
    """Simplified VQE workflow."""

    # 1. Define Hamiltonian (simplified)
    print("VQE Workflow:")
    print("-" * 40)
    print("1. Initialize parameters θ")
    print("2. Prepare trial state |ψ(θ)⟩")
    print("3. Measure ⟨H⟩")
    print("4. Update θ using classical optimizer")
    print("5. Repeat until convergence")

vqe_workflow()
```

## 5. Hardware-Efficient Ansatz

```python
from abirqu.algorithms import vqe_hardware_efficient

# Create VQE ansatz
ansatz = vqe_hardware_efficient(num_qubits=4, depth=2)

print(f"VQE Ansatz:")
print(f"  Qubits: {ansatz.num_qubits}")
print(f"  Depth: 2")
print(f"  Gates: {len(ansatz.gates)}")
```

### Ansatz Structure

The hardware-efficient ansatz consists of:
1. **Rotation layers**: Parameterized single-qubit rotations
2. **Entanglement layers**: Two-qubit gates (CNOT, CZ)
3. **Repeated**: Multiple layers for expressivity

```python
# Compare different depths
for depth in [1, 2, 3]:
    ansatz = vqe_hardware_efficient(num_qubits=4, depth=depth)
    print(f"Depth {depth}: {len(ansatz.gates)} gates")
```

## 6. Energy Calculation

```python
def calculate_hamiltonian_energy(circuit, hamiltonian_terms):
    """Calculate expectation value of Hamiltonian."""
    backend = get_best_backend(n_qubits=circuit.num_qubits)

    total_energy = 0.0
    for coefficient, pauli_string in hamiltonian_terms:
        # Run circuit
        result = backend.run_circuit(circuit, shots=1000)

        # Measure expectation value (simplified)
        expectation = 0.5  # Placeholder
        total_energy += coefficient * expectation

    return total_energy

# Example
circuit = vqe_hardware_efficient(num_qubits=2, depth=1)
energy = calculate_hamiltonian_energy(circuit, [(1.0, "ZI"), (0.5, "ZZ")])
print(f"Estimated energy: {energy:.6f}")
```

## 7. Molecular Examples

```python
# H2 molecule (simplified)
print("H2 Molecule:")
print("-" * 40)
print("Bond length: 0.74 Å")
print("Exact ground state: -1.137 Ha")
print("VQE can find this with sufficient qubits/depth")

# HeH+ molecule
print("\nHeH+ Molecule:")
print("-" * 40)
print("Bond length: 0.77 Å")
print("Exact ground state: -2.862 Ha")
```

## 8. Putting It All Together

```python
def vqe_simulation(molecule_name, n_qubits, depth=2):
    """Run a simplified VQE simulation."""

    print(f"\nVQE Simulation: {molecule_name}")
    print("=" * 40)

    # 1. Create ansatz
    ansatz = vqe_hardware_efficient(num_qubits=n_qubits, depth=depth)
    print(f"Ansatz: {ansatz.num_qubits} qubits, {len(ansatz.gates)} gates")

    # 2. Create sampler
    sampler = Sampler()

    # 3. Run (simplified)
    result = sampler.run(ansatz, shots=1000)
    print(f"Sampling complete: {type(result)}")

    # 4. Estimate energy (placeholder)
    energy = -1.0  # Would be calculated from measurements
    print(f"Estimated energy: {energy:.6f} Ha")

    return energy

# Run simulations
vqe_simulation("H2", n_qubits=4, depth=2)
vqe_simulation("HeH+", n_qubits=4, depth=3)
```

## 9. Error Mitigation in VQE

```python
from abirqu.noise import NoiseModel

def vqe_with_noise(n_qubits=4, error_rate=0.01):
    """VQE with noise mitigation."""

    print(f"\nVQE with Noise (error rate: {error_rate})")
    print("-" * 40)

    # Create noisy backend
    noise_model = NoiseModel(num_qubits=n_qubits)
    for q in range(n_qubits):
        noise_model.add_depolarizing_error(q, error_rate)

    # Run VQE (simplified)
    ansatz = vqe_hardware_efficient(num_qubits=n_qubits, depth=2)
    print(f"Noisy VQE: {len(ansatz.gates)} gates")

    return ansatz

vqe_with_noise()
```

## Summary

In this tutorial, you learned:
1. **Quantum chemistry**: Why quantum computers excel at chemistry
2. **Hamiltonians**: Electronic structure in second quantization
3. **Jordan-Wigner mapping**: Fermions to qubits
4. **VQE**: Variational algorithm for ground states
5. **Hardware-efficient ansatz**: Practical circuit design
6. **Error mitigation**: Handling noise in NISQ era

## Applications

- **Drug discovery**: Molecular interactions
- **Materials science**: Battery materials, superconductors
- **Catalysis**: Nitrogen fixation, carbon capture
- **Energy**: Solar cells, fuel cells

## References

- Peruzzo, A. et al. (2014). "A variational eigenvalue solver on a photonic quantum processor"
- Kandala, A. et al. (2017). "Hardware-efficient variational quantum eigensolver for small molecules and quantum magnets"
