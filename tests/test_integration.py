import sys
import numpy as np
from abirqu.algorithms.advanced import create_algorithm, AlgorithmType

print("Testing QAOA with Rust Core Integration...")
qaoa = create_algorithm(AlgorithmType.QAOA, p=2)
# Simple 2-qubit diagonal Hamiltonian
cost_h = np.array([1.0, -1.0, -1.0, 1.0])
res_qaoa = qaoa.optimize(cost_h)
print(f"QAOA Success: {res_qaoa.success}, Optimal Energy: {res_qaoa.output['optimal_energy']:.4f}")

print("\nTesting VQE with Rust Core Integration...")
vqe = create_algorithm(AlgorithmType.VQE, ansatz_depth=2)
# 2-qubit Hamiltonian matrix (diagonal for simplicity)
H = np.diag([1.0, -1.0, -1.0, 1.0])
res_vqe = vqe.compute_ground_state(H)
print(f"VQE Success: {res_vqe.success}, Ground Energy: {res_vqe.output['ground_energy']:.4f}")

print("\nAlgorithms successfully dispatched to Rust C++ Core!")
