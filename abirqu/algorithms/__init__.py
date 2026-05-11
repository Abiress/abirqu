"""Algorithm templates and execution helpers for AbirQu."""

from __future__ import annotations

import math
from typing import Dict, Iterable, Optional, Tuple

from ..backend import get_best_backend
from ..circuit import Circuit
from ..patterns import grover_template, qaoa_template, vqe_ansatz_template


def grover_search(target_state: int, num_qubits: int, iterations: Optional[int] = None) -> Circuit:
	"""Build a Grover search template circuit.

	If ``iterations`` is ``None``, a near-optimal value is selected.
	"""
	n_states = 2 ** num_qubits
	if iterations is None:
		iterations = max(1, int(math.pi / 4 * math.sqrt(n_states)))

	base = grover_template(num_qubits=num_qubits, marked_state=target_state)
	if iterations <= 1:
		return base

	out = Circuit(num_qubits, name="grover_search")
	for _ in range(iterations):
		out = out + base
	return out


def qft_circuit(num_qubits: int) -> Circuit:
	"""Build a simple QFT-style circuit using native AbirQu primitives."""
	c = Circuit(num_qubits, name=f"qft_{num_qubits}")
	for i in range(num_qubits):
		c.h(i)
		for j in range(i + 1, num_qubits):
			angle = math.pi / (2 ** (j - i))
			c.cnot(j, i)
			c.rz(i, angle)
			c.cnot(j, i)
	return c


def bernstein_vazirani(secret: str) -> Circuit:
	"""Build a Bernstein-Vazirani circuit for the provided binary secret."""
	n = len(secret)
	anc = n
	c = Circuit(n + 1, name="bernstein_vazirani")
	c.x(anc).h(anc)
	for i in range(n):
		c.h(i)
	for i, bit in enumerate(secret):
		if bit == "1":
			c.cnot(i, anc)
	for i in range(n):
		c.h(i)
	return c


def hamiltonian_simulation(num_qubits: int, dt: float = 0.2) -> Circuit:
	"""Build a Trotter-style Hamiltonian simulation template."""
	c = Circuit(num_qubits, name="hamiltonian_simulation")
	for i in range(num_qubits):
		c.rx(i, dt)
	for i in range(num_qubits - 1):
		c.cnot(i, i + 1)
		c.rz(i + 1, dt / 2)
		c.cnot(i, i + 1)
	return c


def quantum_walk(num_qubits: int = 2, steps: int = 6) -> Circuit:
	"""Build a discrete-time quantum-walk style circuit."""
	c = Circuit(max(2, num_qubits), name="quantum_walk")
	for _ in range(max(1, steps)):
		c.h(0)
		c.cnot(0, 1)
	return c


def qaoa_maxcut(num_qubits: int, edges: Iterable[tuple[int, int]], beta: float = 0.4, gamma: float = 0.7) -> Circuit:
	return qaoa_template(num_qubits=num_qubits, edges=edges, beta=beta, gamma=gamma)


def vqe_hardware_efficient(num_qubits: int, depth: int = 2) -> Circuit:
	return vqe_ansatz_template(num_qubits=num_qubits, depth=depth)


def shor_factorization(num_to_factor: int, num_qubits: int = 8) -> Tuple[Circuit, Dict[str, object]]:
	"""Return a Shor-style template circuit and practical factorization metadata.

	The circuit is a pedagogical order-finding template suitable for simulation,
	while factors are computed classically for a deterministic SDK experience.
	"""
	c = Circuit(num_qubits, name=f"shor_{num_to_factor}")
	half = max(1, num_qubits // 2)
	for q in range(half):
		c.h(q)
	for q in range(half):
		tgt = half + (q % max(1, num_qubits - half))
		c.cnot(q, tgt)
		c.rz(tgt, math.pi / (q + 2))
		c.cnot(q, tgt)
	for q in range(half):
		c.h(q)

	factors = []
	n = int(num_to_factor)
	if n > 1:
		d = 2
		while d * d <= n:
			if n % d == 0:
				factors = [d, n // d]
				break
			d += 1

	metadata: Dict[str, object] = {
		"num_to_factor": n,
		"factorization": factors,
		"success": len(factors) == 2,
		"algorithm": "shor-template-with-classical-postprocess",
	}
	return c, metadata


def run_algorithm(circuit: Circuit, shots: int = 1024, backend: str = "local"):
	"""Run a prepared algorithm circuit using the selected backend."""
	if backend in {"local", "fast", "generic"}:
		return get_best_backend(n_qubits=circuit.num_qubits).run_circuit(circuit, shots=shots)
	return circuit.run(shots=shots)


__all__ = [
	"grover_search",
	"shor_factorization",
	"qft_circuit",
	"bernstein_vazirani",
	"vqe_hardware_efficient",
	"qaoa_maxcut",
	"hamiltonian_simulation",
	"quantum_walk",
	"run_algorithm",
]
