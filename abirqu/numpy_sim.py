"""
NumPy-accelerated quantum simulator fallback for AbirQu.
Uses tensor-reshape gate application for O(2^n) performance
with NumPy's BLAS-backed array operations instead of Python loops.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple


# Gate matrices
_H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
_X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
_Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
_Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
_S = np.array([[1, 0], [0, 1j]], dtype=np.complex128)
_T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=np.complex128)
_CNOT = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=np.complex128).reshape(2,2,2,2)
_CZ = np.array([[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,-1]], dtype=np.complex128).reshape(2,2,2,2)
_SWAP = np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]], dtype=np.complex128).reshape(2,2,2,2)


class NumPySimulator:
    """
    Pure-NumPy state-vector simulator.
    Uses tensor reshaping for efficient gate application:
      - State stored as shape (2,)*n tensor
      - Single-qubit gates via np.tensordot on one axis
      - Two-qubit gates via np.tensordot on two axes
    """

    def __init__(self, num_qubits: int):
        self.n = num_qubits
        self.state = np.zeros(2**num_qubits, dtype=np.complex128)
        self.state[0] = 1.0

    def _axis(self, qubit: int) -> int:
        """Map qubit index to tensor axis. Rust uses LSB convention:
        qubit k = bit k, so qubit 0 is the LAST axis in the (2,)*n tensor."""
        return self.n - 1 - qubit

    def _apply_single(self, gate: np.ndarray, qubit: int):
        """Apply a 2x2 gate to a single qubit using tensor contraction."""
        ax = self._axis(qubit)
        state = self.state.reshape([2] * self.n)
        state = np.moveaxis(state, ax, 0)
        state = np.tensordot(gate, state, axes=([1], [0]))
        state = np.moveaxis(state, 0, ax)
        self.state = state.reshape(-1)

    def _apply_two(self, gate: np.ndarray, q0: int, q1: int):
        """Apply a 4x4 (reshaped to 2,2,2,2) gate to two qubits."""
        ax0, ax1 = self._axis(q0), self._axis(q1)
        state = self.state.reshape([2] * self.n)
        perm = [ax0, ax1] + [i for i in range(self.n) if i != ax0 and i != ax1]
        state = state.transpose(perm)
        state = np.tensordot(gate, state, axes=([2, 3], [0, 1]))
        inv_perm = [0] * self.n
        for i, p in enumerate(perm):
            inv_perm[p] = i
        state = state.transpose(inv_perm)
        self.state = state.reshape(-1)

    # ── Standard gates ───────────────────────────────────────────────
    def h(self, qubit: int): self._apply_single(_H, qubit)
    def x(self, qubit: int): self._apply_single(_X, qubit)
    def y(self, qubit: int): self._apply_single(_Y, qubit)
    def z(self, qubit: int): self._apply_single(_Z, qubit)
    def s(self, qubit: int): self._apply_single(_S, qubit)
    def t(self, qubit: int): self._apply_single(_T, qubit)

    def rx(self, qubit: int, theta: float):
        c, s = np.cos(theta/2), np.sin(theta/2)
        gate = np.array([[c, -1j*s], [-1j*s, c]], dtype=np.complex128)
        self._apply_single(gate, qubit)

    def ry(self, qubit: int, theta: float):
        c, s = np.cos(theta/2), np.sin(theta/2)
        gate = np.array([[c, -s], [s, c]], dtype=np.complex128)
        self._apply_single(gate, qubit)

    def rz(self, qubit: int, theta: float):
        gate = np.array([[np.exp(-1j*theta/2), 0],
                         [0, np.exp(1j*theta/2)]], dtype=np.complex128)
        self._apply_single(gate, qubit)

    def cnot(self, control: int, target: int):
        self._apply_two(_CNOT, control, target)

    def cz(self, control: int, target: int):
        self._apply_two(_CZ, control, target)

    def swap(self, q0: int, q1: int):
        self._apply_two(_SWAP, q0, q1)

    # ── Circuit execution ────────────────────────────────────────────

    _GATE_DISPATCH = {
        'H': lambda s, g: s.h(g.qubits[0]),
        'X': lambda s, g: s.x(g.qubits[0]),
        'Y': lambda s, g: s.y(g.qubits[0]),
        'Z': lambda s, g: s.z(g.qubits[0]),
        'S': lambda s, g: s.s(g.qubits[0]),
        'T': lambda s, g: s.t(g.qubits[0]),
        'RX': lambda s, g: s.rx(g.qubits[0], g.params[0]),
        'RY': lambda s, g: s.ry(g.qubits[0], g.params[0]),
        'RZ': lambda s, g: s.rz(g.qubits[0], g.params[0]),
        'CNOT': lambda s, g: s.cnot(g.qubits[0], g.qubits[1]),
        'CX': lambda s, g: s.cnot(g.qubits[0], g.qubits[1]),
        'CZ': lambda s, g: s.cz(g.qubits[0], g.qubits[1]),
        'SWAP': lambda s, g: s.swap(g.qubits[0], g.qubits[1]),
    }

    def run_circuit(self, circuit) -> Dict[str, float]:
        """Execute a full Circuit object. Returns probability dict."""
        for gate in getattr(circuit, 'gates', []):
            dispatch = self._GATE_DISPATCH.get(gate.name.upper())
            if dispatch:
                dispatch(self, gate)

        probs = np.abs(self.state) ** 2
        return {
            format(i, f'0{self.n}b'): float(p)
            for i, p in enumerate(probs) if p > 1e-15
        }

    # ── State access ─────────────────────────────────────────────────

    def get_probabilities(self) -> Dict[str, float]:
        probs = np.abs(self.state) ** 2
        return {
            format(i, f'0{self.n}b'): float(p)
            for i, p in enumerate(probs) if p > 1e-15
        }

    def get_state_vector(self) -> np.ndarray:
        return self.state.copy()
