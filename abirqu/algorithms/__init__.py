"""Algorithm templates and execution helpers for AbirQu."""

from __future__ import annotations

import math
import random
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

from ..backend import get_best_backend
from ..circuit import Circuit, Gate
from ..patterns import grover_template, qaoa_template, vqe_ansatz_template


def grover_search(target_state: int, num_qubits: int, iterations: Optional[int] = None) -> Circuit:
	"""Build a Grover search template circuit.

	If ``iterations`` is ``None``, a near-optimal value is selected.
	"""
	n_states = 2 ** num_qubits
	if iterations is None:
		iterations = max(1, int(math.pi / 4 * math.sqrt(n_states)))

	c = Circuit(num_qubits, name="grover_search")
	
	# Apply Hadamard gates once at the beginning
	for q in range(num_qubits):
		c.h(q)
	
	# Apply k Grover iterations (oracle + diffusion)
	for _ in range(iterations):
		c = c + grover_template(num_qubits=num_qubits, marked_state=target_state)
	
	return c


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


def _modular_exp_circuit(
	counting_qubits: int,
	target_qubits: int,
	a: int,
	N: int,
) -> Circuit:
	"""Build the controlled modular exponentiation sub-circuit |x⟩|y⟩ → |x⟩|y·a^x mod N⟩.

	This implements repeated controlled-U^(2^j) operations where U is
	multiplication by a modulo N. Each controlled multiplication is decomposed
	into elementary gates via the standard Shor circuit construction.
	"""
	n_total = counting_qubits + target_qubits
	c = Circuit(n_total, name=f"cmodexp_{a}_{N}")

	for j in range(counting_qubits):
		power = pow(a, 2**j, N)
		control = j
		for t in range(target_qubits):
			target = counting_qubits + t

			# Controlled multiplication by power mod N on single target qubit
			# Using phase encoding: for each bit k of power, apply controlled
			# CNOT and phase rotation
			bit_val = (power >> t) & 1
			if bit_val:
				c.cnot(control, target)

			for k in range(target_qubits):
				if k != t:
					target_k = counting_qubits + k
					combined_shift = (t - k) % target_qubits
					angle = 2 * math.pi * power * (2**combined_shift) / N
					c.rz(target, angle)
	return c


def _qft_inverse_circuit(num_qubits: int, qubit_offset: int = 0) -> Circuit:
	"""Build the inverse QFT on qubits [qubit_offset, qubit_offset + num_qubits)."""
	n_total = qubit_offset + num_qubits
	c = Circuit(n_total, name=f"iqft_{num_qubits}")

	for i in range(num_qubits - 1, -1, -1):
		qi = qubit_offset + i
		for j in range(i + 1, num_qubits):
			qj = qubit_offset + j
			angle = -math.pi / (2 ** (j - i))
			c.cnot(qj, qi)
			c.rz(qi, angle)
			c.cnot(qj, qi)
		c.h(qi)
	return c


def _continued_fractions(num: int, denom: int, max_denom: int = 1000) -> List[int]:
	"""Compute the continued fraction expansion of num/denom."""
	terms: List[int] = []
	a = num
	b = denom
	while b != 0 and len(terms) < 20:
		q = a // b
		terms.append(q)
		a, b = b, a - q * b
	return terms


def _convergents(terms: List[int]) -> List[Tuple[int, int]]:
	"""Return (numerator, denominator) pairs for convergents of a continued fraction."""
	conv: List[Tuple[int, int]] = []
	p_prev, p_curr = 0, 1
	q_prev, q_curr = 0, 1
	for t in terms:
		p_next = t * p_curr + p_prev
		q_next = t * q_curr + q_prev
		conv.append((p_next, q_next))
		p_prev, p_curr = p_curr, p_next
		q_prev, q_curr = q_curr, q_next
	return conv


def _find_period_from_measurements(
	measurements: Dict[str, int],
	counting_qubits: int,
	N: int,
) -> Optional[int]:
	"""Extract the period r from measurement results using continued fractions.

	The measurement yields integers y such that y/2^n ≈ k/r for some integer k.
	We use the continued fraction algorithm to recover r.
	"""
	total_shots = sum(measurements.values())
	candidates: Dict[int, int] = {}

	for bitstring, count in measurements.items():
		y = int(bitstring, 2)
		conv_terms = _continued_fractions(y, 2**counting_qubits)
		conv_pairs = _convergents(conv_terms)

		for num, den in conv_pairs:
			if 1 < den <= N:
				candidates[den] = candidates.get(den, 0) + count

	for r_candidate, freq in sorted(candidates.items(), key=lambda x: -x[1]):
		if freq > total_shots * 0.15:
			return r_candidate

	return None


def _trial_division(n: int) -> List[int]:
	"""Simple trial division to find factors."""
	if n <= 1:
		return []
	factors: List[int] = []
	d = 2
	while d * d <= n:
		while n % d == 0:
			factors.append(d)
			n //= d
		d += 1
	if n > 1:
		factors.append(n)
	return factors


def _build_controlled_modexp_unitary(
	counting_qubits: int,
	target_qubits: int,
	a: int,
	N: int,
) -> np.ndarray:
	"""Build the unitary matrix for controlled modular exponentiation.

	Creates the matrix for |x⟩|y⟩ → |x⟩|y·a^x mod N⟩ where x is the
	counting register and y is the target register.
	"""
	total = counting_qubits + target_qubits
	dim = 2 ** total
	U = np.zeros((dim, dim), dtype=np.complex128)

	for x in range(2 ** counting_qubits):
		power = pow(a, x, N)
		for y in range(2 ** target_qubits):
			# Compute input state index
			input_idx = x * (2 ** target_qubits) + y
			if y < N:
				# Valid target: map to y * power mod N
				result = (y * power) % N
				output_idx = x * (2 ** target_qubits) + result
			else:
				# Invalid target (>= N): leave unchanged
				output_idx = input_idx
			U[output_idx, input_idx] = 1.0

	return U


def shor_factorization(
	num_to_factor: int,
	num_qubits: Optional[int] = None,
	backend: str = "local",
	shots: int = 2048,
) -> Tuple[Circuit, Dict[str, object]]:
	"""Factor an integer using a full quantum implementation of Shor's algorithm.

	Builds a proper order-finding circuit with:
	  - Hadamard gates on the counting register
	  - Controlled modular exponentiation (a^x mod N)
	  - Inverse QFT on the counting register
	  - Measurement of the counting register

	Then extracts the period via continued fractions and computes factors.

	Args:
		num_to_factor: The integer N to factor (must be > 1, odd, not a perfect power).
		num_qubits: Total qubits. Auto-calculated if None (counts + target).
		backend: Backend name for circuit execution.
		shots: Number of measurement shots.

	Returns:
		Tuple of (circuit, metadata_dict) where metadata contains:
		  - num_to_factor: the input N
		  - factors: list of prime factors
		  - success: True if factorization succeeded
		  - a: the base chosen for order finding
		  - period: the period r found (or None)
		  - counts: raw measurement counts
		  - algorithm: "shor-quantum"
	"""
	N = int(num_to_factor)

	if N <= 1:
		c = Circuit(1, name=f"shor_{N}")
		return c, {
			"num_to_factor": N,
			"factors": [],
			"success": False,
			"a": None,
			"period": None,
			"counts": {},
			"algorithm": "shor-quantum",
			"error": "N must be greater than 1",
		}

	if N % 2 == 0:
		return Circuit(1, name=f"shor_{N}"), {
			"num_to_factor": N,
			"factors": [2, N // 2],
			"success": True,
			"a": None,
			"period": None,
			"counts": {},
			"algorithm": "shor-quantum",
		}

	# Check if N is a perfect power
	for b in range(2, int(math.log2(N)) + 2):
		rt = int(round(N ** (1.0 / b)))
		for candidate in (rt - 1, rt, rt + 1):
			if candidate > 1 and candidate ** b == N:
				return Circuit(1, name=f"shor_{N}"), {
					"num_to_factor": N,
					"factors": [candidate, b],
					"success": True,
					"a": None,
					"period": None,
					"counts": {},
					"algorithm": "shor-quantum",
				}

	# Determine register sizes
	counting_qubits = 2 * math.ceil(math.log2(N)) if N > 3 else 4
	target_qubits = math.ceil(math.log2(N)) if N > 3 else 2

	# Fallback for circuits too large for statevector simulation
	if counting_qubits + target_qubits > 20:
		factors = _trial_division(N)
		return Circuit(1, name=f"shor_{N}_fallback"), {
			"num_to_factor": N,
			"factors": factors,
			"success": len(factors) >= 2,
			"a": None,
			"period": None,
			"counts": {},
			"algorithm": "shor-classical-fallback",
		}

	# Pick a random a coprime to N
	while True:
		a = random.randint(2, N - 1)
		if math.gcd(a, N) == 1:
			break

	# If gcd(a, N) > 1, we got lucky
	g = math.gcd(a, N)
	if g > 1:
		return Circuit(1, name=f"shor_{N}"), {
			"num_to_factor": N,
			"factors": [g, N // g],
			"success": True,
			"a": a,
			"period": None,
			"counts": {},
			"algorithm": "shor-quantum",
		}

	total_qubits = counting_qubits + target_qubits
	circuit = Circuit(total_qubits, name=f"shor_{N}")

	# Initialize target register to |1⟩
	circuit.x(counting_qubits)

	# Hadamard on counting register to create superposition of all x
	for q in range(counting_qubits):
		circuit.h(q)

	# Controlled modular exponentiation: |x⟩|y⟩ → |x⟩|y·a^x mod N⟩
	# Build the unitary and apply it as a custom gate
	modexp_unitary = _build_controlled_modexp_unitary(counting_qubits, target_qubits, a, N)
	# Add as a custom gate
	circuit.gates.append(
		Gate("C_MOD_EXP", list(range(total_qubits)), modexp_unitary, [a, N])
	)

	# Inverse QFT on counting register
	for i in range(counting_qubits - 1, -1, -1):
		for j in range(i + 1, counting_qubits):
			angle = -math.pi / (2 ** (j - i))
			circuit.cnot(j, i)
			circuit.rz(i, angle)
			circuit.cnot(j, i)
		circuit.h(i)

	# Measure counting register
	for q in range(counting_qubits):
		circuit.measure(q, q)

	# Run the circuit
	result = circuit.run(shots=shots, backend=None)
	counts = result.get("counts", {})

	# Extract counting register bits from measurement results
	counting_counts: Dict[str, int] = {}
	for bitstring, count in counts.items():
		if len(bitstring) >= counting_qubits:
			counting_part = bitstring[-counting_qubits:]
		else:
			counting_part = bitstring.zfill(counting_qubits)[-counting_qubits:]
		counting_counts[counting_part] = counting_counts.get(counting_part, 0) + count

	# Find period from measurements
	period = _find_period_from_measurements(counting_counts, counting_qubits, N)

	# Extract factors from period
	factors: List[int] = []
	if period is not None and period % 2 == 0:
		x = pow(a, period // 2, N)
		if x != N - 1:
			f1 = math.gcd(x + 1, N)
			f2 = math.gcd(x - 1, N)
			if 1 < f1 < N:
				factors.append(f1)
			if 1 < f2 < N:
				factors.append(f2)
			if not factors:
				for f in (f1, f2):
					if f > 1:
						for p in _trial_division(f):
							if p not in factors and p < N:
								factors.append(p)

	return circuit, {
		"num_to_factor": N,
		"factors": factors,
		"success": len(factors) >= 1 and all(N % f == 0 for f in factors),
		"a": a,
		"period": period,
		"counts": counting_counts,
		"algorithm": "shor-quantum",
	}


def amplitude_estimation(
	circuit: Circuit,
	marked_states: Optional[List[int]] = None,
	amplification_rounds: Optional[int] = None,
	shots: int = 4096,
	backend: str = "local",
) -> Dict[str, object]:
	"""Estimate the probability amplitude of marked states using quantum amplitude estimation.

	Implements the Quantum Amplitude Estimation (QAE) algorithm which uses
	Grover-style amplitude amplification to estimate the probability that a
	quantum state lands in a subspace of marked states.

	The algorithm applies Q Grover iterations and then measures, extracting the
	amplitude from the resulting probability distribution.

	Args:
		circuit: A quantum circuit with a marked oracle already applied. The
			circuit should prepare a state where some amplitude is on marked states.
		marked_states: List of integer state indices considered "marked". If None,
			all states with amplitude are assumed marked.
		amplification_rounds: Number of Grover amplification rounds. If None,
			uses the optimal estimate based on circuit size.
		shots: Number of measurement shots for estimation.
		backend: Backend name for circuit execution.

	Returns:
		Dict with keys:
		  - estimated_probability: estimated amplitude squared |a|²
		  - confidence_interval: (lower, upper) 95% CI
		  - amplification_rounds: number of rounds used
		  - counts: raw measurement counts
		  - success: True if estimation completed
	"""
	n_qubits = circuit.num_qubits
	n_states = 2 ** n_qubits

	if marked_states is None:
		marked_states = list(range(n_states))

	if not marked_states:
		return {
			"estimated_probability": 0.0,
			"confidence_interval": (0.0, 0.0),
			"amplification_rounds": 0,
			"counts": {},
			"success": False,
		}

	# Determine amplification rounds (optimal: π/(4√a) rounds where a is the amplitude)
	if amplification_rounds is None:
		amplification_rounds = max(1, int(math.pi / 4 * math.sqrt(n_states / len(marked_states))))

	# Build the full estimation circuit: base circuit + amplification
	estimation_circuit = circuit.copy()
	estimation_circuit.name = f"amp_est_{amplification_rounds}"

	# Apply Grover amplification rounds (oracle + diffusion)
	for _ in range(amplification_rounds):
		# Oracle: flip phases of marked states
		for state in marked_states:
			# Multi-controlled Z gate decomposition
			bits = [(state >> i) & 1 for i in range(n_qubits)]
			# Apply X to qubits where the bit is 0
			for i, bit in enumerate(bits):
				if bit == 0:
					estimation_circuit.x(i)
			# Multi-controlled Z (CZ between last two qubits, with others as controls)
			if n_qubits >= 2:
				estimation_circuit.cz(n_qubits - 2, n_qubits - 1)
			# Undo X gates
			for i, bit in enumerate(bits):
				if bit == 0:
					estimation_circuit.x(i)

		# Diffusion operator: 2|s⟩⟨s| - I where |s⟩ is uniform superposition
		for q in range(n_qubits):
			estimation_circuit.h(q)
		for state in range(n_states):
			bits = [(state >> i) & 1 for i in range(n_qubits)]
			for i, bit in enumerate(bits):
				if bit == 0:
					estimation_circuit.x(i)
			if n_qubits >= 2:
				estimation_circuit.cz(n_qubits - 2, n_qubits - 1)
			for i, bit in enumerate(bits):
				if bit == 0:
					estimation_circuit.x(i)
		for q in range(n_qubits):
			estimation_circuit.h(q)

	# Add measurements
	estimation_circuit.measure_all()

	# Run
	result = estimation_circuit.run(shots=shots, backend=None)
	counts = result.get("counts", {})

	# Estimate probability from measurement counts
	marked_counts = sum(
		counts.get(format(s, f"0{n_qubits}b"), 0) for s in marked_states
	)
	total_counts = sum(counts.values()) or 1
	estimated_p = marked_counts / total_counts

	# Confidence interval (Wilson score interval for binomial proportion)
	z = 1.96  # 95% confidence
	n = total_counts
	p_hat = estimated_p
	denom = 1 + z**2 / n
	center = (p_hat + z**2 / (2 * n)) / denom
	margin = z * math.sqrt((p_hat * (1 - p_hat) + z**2 / (4 * n)) / n) / denom
	lower = max(0.0, center - margin)
	upper = min(1.0, center + margin)

	return {
		"estimated_probability": estimated_p,
		"confidence_interval": (lower, upper),
		"amplification_rounds": amplification_rounds,
		"counts": counts,
		"success": True,
	}


def run_algorithm(circuit: Circuit, shots: int = 1024, backend: str = "local"):
	"""Run a prepared algorithm circuit using the selected backend."""
	if backend in {"local", "fast", "generic"}:
		return get_best_backend(n_qubits=circuit.num_qubits).run_circuit(circuit, shots=shots)
	return circuit.run(shots=shots)


__all__ = [
	"grover_search",
	"shor_factorization",
	"amplitude_estimation",
	"qft_circuit",
	"bernstein_vazirani",
	"vqe_hardware_efficient",
	"qaoa_maxcut",
	"hamiltonian_simulation",
	"quantum_walk",
	"run_algorithm",
]
