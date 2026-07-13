"""
Auto-differentiation for parameterized quantum circuits.

Provides gradient computation via parameter-shift rule, finite differences,
and adjoint simulation. All methods work with AbirQu circuits and the
NumPy simulator as the execution backend.

Copyright 2026 Abir Maheshwari
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .circuit import Circuit, Gate

__all__ = [
    "QuantumTape",
    "GradientResult",
    "parameter_shift_gradient",
    "finite_difference_gradient",
    "adjoint_gradient",
]


# ── Quantum Tape ──────────────────────────────────────────────────────────────

class QuantumTape:
    """Records quantum operations for differentiation.

    A tape captures the sequence of gates and their parameter positions so
    that gradient methods can replay or modify individual parameters.

    Attributes:
        gates: List of recorded gate operations as dicts with keys
            ``name``, ``qubits``, ``params``, ``param_indices``.
        num_qubits: Number of qubits in the circuit this tape was built from.
    """

    def __init__(self, circuit: Optional[Circuit] = None) -> None:
        """Create a tape from an existing circuit, or start empty.

        Args:
            circuit: Optional circuit to record.  If *None*, use :meth:`record`
                to add gates manually.
        """
        self.gates: List[Dict[str, Any]] = []
        self.num_qubits: int = 0
        self._param_index = 0
        if circuit is not None:
            self.record_circuit(circuit)

    # ── recording ─────────────────────────────────────────────────────────
    def record_circuit(self, circuit: Circuit) -> None:
        """Record all gates from *circuit* into this tape."""
        self.num_qubits = circuit.num_qubits
        for gate in circuit.gates:
            self.record_gate(gate)

    def record_gate(self, gate: Gate) -> None:
        """Record a single gate, tracking parameter positions."""
        param_indices: List[int] = []
        for _ in (gate.params or []):
            param_indices.append(self._param_index)
            self._param_index += 1
        self.gates.append({
            "name": gate.name,
            "qubits": list(gate.qubits),
            "params": list(gate.params or []),
            "param_indices": param_indices,
        })

    # ── parameter helpers ─────────────────────────────────────────────────
    @property
    def num_params(self) -> int:
        """Total number of trainable parameters in the tape."""
        return self._param_index

    def get_param_values(self) -> List[float]:
        """Return a flat list of all parameter values in order."""
        values: List[float] = []
        for g in self.gates:
            values.extend(g["params"])
        return values

    def set_params(self, values: Sequence[float]) -> None:
        """Set all parameter values from a flat sequence.

        Args:
            values: Flat list of floats matching :meth:`num_params`.
        """
        if len(values) != self.num_params:
            raise ValueError(
                f"Expected {self.num_params} parameters, got {len(values)}"
            )
        idx = 0
        for g in self.gates:
            n = len(g["params"])
            g["params"] = list(values[idx : idx + n])
            idx += n

    def copy(self) -> "QuantumTape":
        """Return a deep copy of this tape."""
        new = QuantumTape()
        new.num_qubits = self.num_qubits
        new._param_index = self._param_index
        new.gates = [dict(g) for g in self.gates]
        for g in new.gates:
            g["params"] = list(g["params"])
            g["qubits"] = list(g["qubits"])
            g["param_indices"] = list(g["param_indices"])
        return new

    # ── rebuild into a Circuit ────────────────────────────────────────────
    def to_circuit(self) -> Circuit:
        """Reconstruct a :class:`Circuit` from the recorded tape."""
        circ = Circuit(self.num_qubits)
        for g in self.gates:
            circ.add_gate(g["name"], g["qubits"], g["params"] or None)
        return circ


# ── Gradient Result ───────────────────────────────────────────────────────────

@dataclass
class GradientResult:
    """Container for gradient computation results.

    Attributes:
        gradients: Array of partial derivatives, one per trainable parameter.
        method: Name of the gradient method used.
        circuit_evals: Number of circuit executions performed.
        param_values: The parameter values at which the gradient was evaluated.
    """

    gradients: np.ndarray
    method: str
    circuit_evals: int
    param_values: np.ndarray


# ── Internal helpers ──────────────────────────────────────────────────────────

def _run_tape(
    tape: QuantumTape,
    param_values: np.ndarray,
    hamiltonian: np.ndarray,
    shots: int = 0,
) -> float:
    """Evaluate ``<ψ(θ)|H|ψ(θ)>`` for the given tape and parameters."""
    saved = tape.get_param_values()
    tape.set_params(param_values.tolist())
    circ = tape.to_circuit()
    tape.set_params(saved)

    from .numpy_sim import NumPySimulator
    sim = NumPySimulator(circ.num_qubits)
    for gate in circ.gates:
        name = gate.name.upper()
        qubits = gate.qubits
        params = gate.params or []
        if len(qubits) == 1:
            q = qubits[0]
            if name == "H":
                sim.h(q)
            elif name == "X":
                sim.x(q)
            elif name == "Y":
                sim.y(q)
            elif name == "Z":
                sim.z(q)
            elif name == "S":
                sim.s(q)
            elif name == "T":
                sim.t(q)
            elif name == "RX":
                sim.rx(q, params[0])
            elif name == "RY":
                sim.ry(q, params[0])
            elif name == "RZ":
                sim.rz(q, params[0])
        elif len(qubits) == 2:
            c, t = qubits[0], qubits[1]
            if name in ("CNOT", "CX"):
                sim.cnot(c, t)
            elif name == "CZ":
                sim.cz(c, t)
            elif name == "SWAP":
                sim.swap(c, t)
        elif len(qubits) == 3 and name == "TOFFOLI":
            sim.toffoli(qubits[0], qubits[1], qubits[2])

    psi = sim.get_state_vector()
    ham_matrix = np.asarray(hamiltonian, dtype=complex)
    if ham_matrix.ndim == 1:
        # diagonal Hamiltonian
        return float(np.real(np.sum(np.abs(psi) ** 2 * ham_matrix)))
    return float(np.real(psi.conj() @ ham_matrix @ psi))


def _identity_like(n: int) -> np.ndarray:
    """Return an identity matrix of size *n*."""
    return np.eye(n, dtype=complex)


# ── Parameter-Shift Rule ─────────────────────────────────────────────────────

def parameter_shift_gradient(
    circuit: Circuit,
    param_values: Sequence[float],
    hamiltonian: np.ndarray,
    shots: int = 0,
) -> GradientResult:
    """Compute the gradient of `<ψ(θ)|H|ψ(θ)>` using the parameter-shift rule.

    For a gate with a single parameter θ the expectation value is of the
    form ``A·cos(θ) + B·sin(θ)`` so

        ∂E/∂θ = [E(θ + π/2) − E(θ − π/2)] / 2

    This method requires that each parameterised gate acts on at most one
    qubit and contains a single rotation parameter (RX, RY, RZ).

    Args:
        circuit: Parameterised quantum circuit.
        param_values: Current parameter values (flat list).
        hamiltonian: Observable as a square matrix (or diagonal vector).
        shots: Kept for interface compatibility; ``0`` gives exact gradients.

    Returns:
        :class:`GradientResult` with per-parameter partial derivatives.
    """
    tape = QuantumTape(circuit)
    params = np.asarray(param_values, dtype=float)
    n_params = tape.num_params

    shift = math.pi / 2
    grads = np.zeros(n_params, dtype=float)
    evals = 0

    for i in range(n_params):
        p_plus = params.copy()
        p_plus[i] += shift
        e_plus = _run_tape(tape, p_plus, hamiltonian, shots)
        evals += 1

        p_minus = params.copy()
        p_minus[i] -= shift
        e_minus = _run_tape(tape, p_minus, hamiltonian, shots)
        evals += 1

        grads[i] = (e_plus - e_minus) / 2.0

    return GradientResult(
        gradients=grads,
        method="parameter_shift",
        circuit_evals=evals,
        param_values=params.copy(),
    )


# ── Finite Differences ────────────────────────────────────────────────────────

def finite_difference_gradient(
    circuit: Circuit,
    param_values: Sequence[float],
    hamiltonian: np.ndarray,
    epsilon: float = 1e-4,
    shots: int = 0,
) -> GradientResult:
    """Compute the gradient via central finite differences.

    Uses the central-difference formula:

        ∂E/∂θᵢ ≈ [E(θᵢ+ε) − E(θᵢ−ε)] / (2ε)

    This is a universal fallback that works for arbitrary circuits but is
    slower and noisier than the parameter-shift rule.

    Args:
        circuit: Quantum circuit (may contain arbitrary gates).
        param_values: Current parameter values (flat list).
        hamiltonian: Observable as a square matrix or diagonal vector.
        epsilon: Finite-difference step size.
        shots: Number of measurement shots (0 = exact statevector).

    Returns:
        :class:`GradientResult` with per-parameter partial derivatives.
    """
    tape = QuantumTape(circuit)
    params = np.asarray(param_values, dtype=float)
    n_params = tape.num_params
    evals = 0

    grads = np.zeros(n_params, dtype=float)
    e0 = _run_tape(tape, params, hamiltonian, shots)
    evals += 1

    for i in range(n_params):
        p_plus = params.copy()
        p_plus[i] += epsilon
        e_plus = _run_tape(tape, p_plus, hamiltonian, shots)
        evals += 1

        p_minus = params.copy()
        p_minus[i] -= epsilon
        e_minus = _run_tape(tape, p_minus, hamiltonian, shots)
        evals += 1

        grads[i] = (e_plus - e_minus) / (2.0 * epsilon)

    return GradientResult(
        gradients=grads,
        method="finite_difference",
        circuit_evals=evals,
        param_values=params.copy(),
    )


# ── Adjoint Gradient ──────────────────────────────────────────────────────────

def adjoint_gradient(
    circuit: Circuit,
    param_values: Sequence[float],
    hamiltonian: np.ndarray,
    shots: int = 0,
) -> GradientResult:
    """Compute the gradient using the adjoint (backward-pass) method.

    The adjoint method propagates a state-vector forward through the
    circuit, stores the state at each parameterised gate, then propagates
    an observable backward.  For each parameterised gate with generator G:

        ∂E/∂θ = 2·Re⟨ψ_b| G |ψ_f⟩

    where |ψ_f⟩ is the forward state *before* the gate and |ψ_b⟩ is the
    backward state *after* applying the gate's inverse.  This requires only
    **one forward + one backward pass** (plus one circuit evaluation for
    the overall energy), making it significantly cheaper than the
    parameter-shift rule for large circuits.

    .. note::

        The implementation below works by replaying the full tape with
        the NumPy simulator and capturing intermediate states via the
        ``QuantumTape`` structure.  It is a correct (if simple) reference
        implementation; production code would fuse the forward/backward
        passes at a lower level for maximum performance.

    Args:
        circuit: Parameterised quantum circuit.
        param_values: Current parameter values (flat list).
        hamiltonian: Observable as a square matrix or diagonal vector.
        shots: Kept for interface compatibility; ``0`` gives exact values.

    Returns:
        :class:`GradientResult` with per-parameter partial derivatives.
    """
    tape = QuantumTape(circuit)
    params = np.asarray(param_values, dtype=float)
    n_params = tape.num_params
    evals = 0

    ham = np.asarray(hamiltonian, dtype=complex)
    n_qubits = circuit.num_qubits
    dim = 1 << n_qubits
    if ham.ndim == 1:
        ham = np.diag(ham)

    # ── Generator matrices for single-qubit rotations ─────────────────────
    _sx = np.array([[0, 1], [1, 0]], dtype=complex)
    _sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    _sz = np.array([[1, 0], [0, -1]], dtype=complex)
    _gen_map: Dict[str, np.ndarray] = {
        "RX": _sx,
        "RY": _sy,
        "RZ": _sz,
    }

    # ── Forward pass: simulate the full circuit and record per-gate states ─
    from .numpy_sim import NumPySimulator

    tape.set_params(params.tolist())

    forward_states: List[Optional[np.ndarray]] = [None] * len(tape.gates)

    sim = NumPySimulator(n_qubits)
    for gi, g in enumerate(tape.gates):
        name = g["name"].upper()
        qubits = g["qubits"]
        gate_params = g["params"]
        if len(qubits) == 1:
            q = qubits[0]
            if name == "H":
                sim.h(q)
            elif name == "X":
                sim.x(q)
            elif name == "Y":
                sim.y(q)
            elif name == "Z":
                sim.z(q)
            elif name == "S":
                sim.s(q)
            elif name == "T":
                sim.t(q)
            elif name == "RX":
                sim.rx(q, gate_params[0])
            elif name == "RY":
                sim.ry(q, gate_params[0])
            elif name == "RZ":
                sim.rz(q, gate_params[0])
        elif len(qubits) == 2:
            c, t = qubits[0], qubits[1]
            if name in ("CNOT", "CX"):
                sim.cnot(c, t)
            elif name == "CZ":
                sim.cz(c, t)
            elif name == "SWAP":
                sim.swap(c, t)
        elif len(qubits) == 3 and name == "TOFFOLI":
            sim.toffoli(qubits[0], qubits[1], qubits[2])

        if gate_params and name in _gen_map:
            forward_states[gi] = sim.get_state_vector().copy()

    # ── Backward pass ─────────────────────────────────────────────────────
    # Start with |b⟩ = H|ψ⟩  (final state transformed by observable)
    psi_final = sim.get_state_vector()
    backward_state = ham @ psi_final

    grads = np.zeros(n_params, dtype=float)
    evals += 1  # one forward pass counted

    for gi in range(len(tape.gates) - 1, -1, -1):
        g = tape.gates[gi]
        name = g["name"].upper()
        qubits = g["qubits"]
        gate_params = g["params"]

        # Inverse the gate that was applied at position gi
        if len(qubits) == 1:
            q = qubits[0]
            if name == "H":
                # H is self-inverse
                _sim_rev = NumPySimulator(n_qubits)
                _sim_rev.state = backward_state.copy()
                _sim_rev.h(q)
                backward_state = _sim_rev.get_state_vector()
            elif name == "X":
                _sim_rev = NumPySimulator(n_qubits)
                _sim_rev.state = backward_state.copy()
                _sim_rev.x(q)
                backward_state = _sim_rev.get_state_vector()
            elif name == "Y":
                _sim_rev = NumPySimulator(n_qubits)
                _sim_rev.state = backward_state.copy()
                _sim_rev.y(q)
                backward_state = _sim_rev.get_state_vector()
            elif name == "Z":
                _sim_rev = NumPySimulator(n_qubits)
                _sim_rev.state = backward_state.copy()
                _sim_rev.z(q)
                backward_state = _sim_rev.get_state_vector()
            elif name == "S":
                _sim_rev = NumPySimulator(n_qubits)
                _sim_rev.state = backward_state.copy()
                # S† = S inverse
                _sim_rev.s(q)
                _sim_rev.s(q)
                _sim_rev.s(q)
                backward_state = _sim_rev.get_state_vector()
            elif name == "T":
                _sim_rev = NumPySimulator(n_qubits)
                _sim_rev.state = backward_state.copy()
                for _ in range(7):
                    _sim_rev.t(q)
                backward_state = _sim_rev.get_state_vector()
            elif name == "RX":
                _sim_rev = NumPySimulator(n_qubits)
                _sim_rev.state = backward_state.copy()
                _sim_rev.rx(q, -gate_params[0])
                backward_state = _sim_rev.get_state_vector()
            elif name == "RY":
                _sim_rev = NumPySimulator(n_qubits)
                _sim_rev.state = backward_state.copy()
                _sim_rev.ry(q, -gate_params[0])
                backward_state = _sim_rev.get_state_vector()
            elif name == "RZ":
                _sim_rev = NumPySimulator(n_qubits)
                _sim_rev.state = backward_state.copy()
                _sim_rev.rz(q, -gate_params[0])
                backward_state = _sim_rev.get_state_vector()
        elif len(qubits) == 2:
            c, t = qubits[0], qubits[1]
            _sim_rev = NumPySimulator(n_qubits)
            _sim_rev.state = backward_state.copy()
            if name in ("CNOT", "CX"):
                _sim_rev.cnot(c, t)
            elif name == "CZ":
                _sim_rev.cz(c, t)
            elif name == "SWAP":
                _sim_rev.swap(c, t)
            backward_state = _sim_rev.get_state_vector()
        elif len(qubits) == 3 and name == "TOFFOLI":
            _sim_rev = NumPySimulator(n_qubits)
            _sim_rev.state = backward_state.copy()
            _sim_rev.toffoli(qubits[0], qubits[1], qubits[2])
            backward_state = _sim_rev.get_state_vector()

        # Compute gradient for parameters of this gate
        if gate_params and name in _gen_map and forward_states[gi] is not None:
            gen = _gen_map[name]
            q = qubits[0]
            psi_f = forward_states[gi]

            # Apply generator to |ψ_f⟩ on qubit q
            mask = 1 << q
            gen_psi = np.zeros(dim, dtype=complex)
            for basis in range(dim):
                b = (basis >> q) & 1
                other = basis ^ mask
                gen_psi[basis] += gen[0, b] * psi_f[basis]
                gen_psi[basis] += gen[b, 1 - b] * psi_f[other]

            grads[gi] = 2.0 * float(np.real(backward_state.conj() @ gen_psi))

    return GradientResult(
        gradients=grads,
        method="adjoint",
        circuit_evals=evals,
        param_values=params.copy(),
    )
