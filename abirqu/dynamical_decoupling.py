"""
AbirQu Dynamical Decoupling Pulse Sequences
=============================================
DD sequences suppress decoherence during idle periods of quantum circuits.

Implements: XY-4, XY-8, CPMG, Uhrig DD (UDD).
Includes a scheduler that inserts DD pulses into circuit idle gaps.

Pure numpy — no external dependencies.
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import numpy as np

from .circuit import Circuit, Gate, Measurement


# ── Gate matrices (reused) ──────────────────────────────────────────────────

_SQRT2_INV = 1.0 / math.sqrt(2)


def _x_matrix() -> np.ndarray:
    return np.array([[0, 1], [1, 0]], dtype=complex)


def _y_matrix() -> np.ndarray:
    return np.array([[0, -1j], [1j, 0]], dtype=complex)


def _z_matrix() -> np.ndarray:
    return np.array([[1, 0], [0, -1]], dtype=complex)


def _rx_matrix(theta: float) -> np.ndarray:
    return np.array([
        [np.cos(theta / 2), -1j * np.sin(theta / 2)],
        [-1j * np.sin(theta / 2), np.cos(theta / 2)],
    ], dtype=complex)


def _ry_matrix(theta: float) -> np.ndarray:
    return np.array([
        [np.cos(theta / 2), -np.sin(theta / 2)],
        [np.sin(theta / 2), np.cos(theta / 2)],
    ], dtype=complex)


def _rz_matrix(theta: float) -> np.ndarray:
    return np.array([
        [np.exp(-1j * theta / 2), 0],
        [0, np.exp(1j * theta / 2)],
    ], dtype=complex)


# ── DDSequence base class ───────────────────────────────────────────────────

class DDSequence(ABC):
    """Base class for dynamical decoupling sequences.

    A DD sequence is a series of pi-pulses (or rotations) applied to a
    qubit during an idle period to suppress decoherence.

    Subclasses must implement :meth:`pulse_times` and :meth:`pulse_axes`.
    """

    @property
    @abstractmethod
    def num_pulses(self) -> int:
        """Number of pi-pulses in the sequence."""

    @abstractmethod
    def pulse_times(self, total_time: float) -> List[float]:
        """Return the normalised times ``[0, 1]`` at which each pulse fires.

        Parameters
        ----------
        total_time : float
            Total idle duration (used only for non-equidistant sequences).
        """

    @abstractmethod
    def pulse_axes(self) -> List[str]:
        """Return the rotation axis for each pulse (e.g. ``["X", "Y"]``).``"""

    def generate_gates(
        self, qubit: int, total_time: float = 1.0
    ) -> List[Tuple[str, List[int], List[float]]]:
        """Return a list of ``(gate_name, qubits, params)`` tuples.

        Each pulse is a pi-rotation (rotation angle ``π``) about the
        axis given by :meth:`pulse_axes`.
        """
        axes = self.pulse_axes()
        times = self.pulse_times(total_time)
        gates: List[Tuple[str, List[int], List[float]]] = []
        for axis in axes:
            axis_upper = axis.upper()
            if axis_upper == "X":
                gates.append(("X", [qubit], []))
            elif axis_upper == "Y":
                gates.append(("Y", [qubit], []))
            elif axis_upper == "RX":
                gates.append(("RX", [qubit], [math.pi]))
            elif axis_upper == "RY":
                gates.append(("RY", [qubit], [math.pi]))
            elif axis_upper == "RZ":
                gates.append(("RZ", [qubit], [math.pi]))
            else:
                gates.append((axis_upper, [qubit], []))
        return gates

    def apply_to_circuit(
        self, circuit: Circuit, qubit: int, total_time: float = 1.0
    ) -> Circuit:
        """Append this DD sequence's gates to *circuit* on *qubit*."""
        for name, qubits, params in self.generate_gates(qubit, total_time):
            circuit.add_gate(name, qubits, params if params else None)
        return circuit

    def unitary(self, total_time: float = 1.0) -> np.ndarray:
        """Compute the net unitary of the entire DD sequence."""
        axes = self.pulse_axes()
        u = np.eye(2, dtype=complex)
        for axis in axes:
            axis_upper = axis.upper()
            if axis_upper == "X":
                p = _x_matrix()
            elif axis_upper == "Y":
                p = _y_matrix()
            elif axis_upper == "RX":
                p = _rx_matrix(math.pi)
            elif axis_upper == "RY":
                p = _ry_matrix(math.pi)
            elif axis_upper == "RZ":
                p = _rz_matrix(math.pi)
            else:
                p = np.eye(2, dtype=complex)
            u = p @ u
        return u

    @property
    def is_identity(self) -> bool:
        """Check whether the net unitary is the identity (up to global phase)."""
        u = self.unitary()
        # Check if U = e^{i phi} I
        phase = u[0, 0]
        if abs(phase) < 1e-12:
            return False
        return np.allclose(u / phase, np.eye(2), atol=1e-10)


# ── XY-4 Sequence ──────────────────────────────────────────────────────────

class XY4Sequence(DDSequence):
    """XY-4 dynamical decoupling sequence.

    4-pulse sequence: X – Y – X – Y

    Equivalent to two repetitions of the basic XY pair.  Cancels
    dephasing (Z noise) and relaxation (X/Y noise) up to first order.

    Net unitary: I (identity).
    """

    @property
    def num_pulses(self) -> int:
        return 4

    def pulse_times(self, total_time: float = 1.0) -> List[float]:
        n = 4
        return [i / (n + 1) for i in range(1, n + 1)]

    def pulse_axes(self) -> List[str]:
        return ["X", "Y", "X", "Y"]

    def __repr__(self) -> str:
        return "XY4Sequence(4-pulse: X-Y-X-Y)"


# ── XY-8 Sequence ──────────────────────────────────────────────────────────

class XY8Sequence(DDSequence):
    """XY-8 dynamical decoupling sequence.

    8-pulse sequence: X – Y – X – Y – X – Y – X – Y

    An extension of XY-4 that doubles the number of pulses to achieve
    higher-order suppression of coherent and stochastic noise.

    Net unitary: I (identity).
    """

    @property
    def num_pulses(self) -> int:
        return 8

    def pulse_times(self, total_time: float = 1.0) -> List[float]:
        n = 8
        return [i / (n + 1) for i in range(1, n + 1)]

    def pulse_axes(self) -> List[str]:
        return ["X", "Y", "X", "Y", "X", "Y", "X", "Y"]

    def __repr__(self) -> str:
        return "XY8Sequence(8-pulse: X-Y-X-Y-X-Y-X-Y)"


# ── CPMG Sequence ──────────────────────────────────────────────────────────

class CPMGSequence(DDSequence):
    """CPMG (Carr-Purcell-Meiboom-Gill) dynamical decoupling sequence.

    Uses N equidistant Y-pulses (Meiboom modification of the original
    Carr-Purcell sequence which used X-pulses).  The Y-axis choice
    avoids accumulation of pulse-length errors.

    Parameters
    ----------
    n_pulses : int
        Number of Y-pulses (default 4).
    """

    def __init__(self, n_pulses: int = 4):
        if n_pulses < 1:
            raise ValueError("n_pulses must be >= 1")
        self._n = n_pulses

    @property
    def num_pulses(self) -> int:
        return self._n

    def pulse_times(self, total_time: float = 1.0) -> List[float]:
        n = self._n
        return [i / (n + 1) for i in range(1, n + 1)]

    def pulse_axes(self) -> List[str]:
        return ["Y"] * self._n

    def __repr__(self) -> str:
        return f"CPMGSequence({self._n}-pulse Y-axis)"


# ── UDD Sequence ────────────────────────────────────────────────────────────

class UDDSequence(DDSequence):
    """Uhrig Dynamical Decoupling (UDD) sequence.

    Uses N equidistant X-pulses placed at *non-equidistant* times:

        t_j = T * sin²(π j / (2N + 2))

    where T is the total idle time and j = 1, …, N.  Uhrig showed this
    timing suppresses pure dephasing noise to N-th order.

    Parameters
    ----------
    n_pulses : int
        Number of X-pulses (default 4).
    """

    def __init__(self, n_pulses: int = 4):
        if n_pulses < 1:
            raise ValueError("n_pulses must be >= 1")
        self._n = n_pulses

    @property
    def num_pulses(self) -> int:
        return self._n

    def pulse_times(self, total_time: float = 1.0) -> List[float]:
        """Return non-equidistant times scaled to [0, total_time]."""
        N = self._n
        times = []
        for j in range(1, N + 1):
            t = total_time * (math.sin(math.pi * j / (2 * N + 2))) ** 2
            times.append(t)
        return times

    def pulse_axes(self) -> List[str]:
        return ["X"] * self._n

    def __repr__(self) -> str:
        return f"UDDSequence({self._n}-pulse, Uhrig non-equidistant)"


# ── DDScheduler ─────────────────────────────────────────────────────────────

class DDScheduler:
    """Inserts dynamical decoupling sequences into idle periods of a circuit.

    Parameters
    ----------
    default_sequence : DDSequence, optional
        Sequence to use when none is specified per qubit.
    min_idle_gates : int
        Minimum number of consecutive identity-equivalent time slots
        before inserting DD.  A single-qubit idle of *k* "gate slots"
        means there are at least *k* consecutive layers where the qubit
        is not acted upon.
    """

    def __init__(
        self,
        default_sequence: Optional[DDSequence] = None,
        min_idle_gates: int = 3,
    ):
        self.default_sequence = default_sequence or XY4Sequence()
        self.min_idle_gates = min_idle_gates

    def _find_idle_intervals(
        self, circuit: Circuit
    ) -> Dict[int, List[Tuple[int, int]]]:
        """Find idle intervals for each qubit.

        Returns a dict mapping qubit → list of (start_layer, end_layer) gaps.
        """
        # Build layer occupation map
        num_layers = len(circuit.gates)
        if num_layers == 0:
            return {q: [] for q in range(circuit.num_qubits)}

        qubit_occupied: Dict[int, List[bool]] = {
            q: [False] * num_layers for q in range(circuit.num_qubits)
        }

        for layer_idx, gate in enumerate(circuit.gates):
            for q in gate.qubits:
                if 0 <= q < circuit.num_qubits:
                    qubit_occupied[q][layer_idx] = True

        # Find gaps
        idle_intervals: Dict[int, List[Tuple[int, int]]] = {}
        for q in range(circuit.num_qubits):
            gaps: List[Tuple[int, int]] = []
            gap_start = None
            for layer in range(num_layers):
                if not qubit_occupied[q][layer]:
                    if gap_start is None:
                        gap_start = layer
                else:
                    if gap_start is not None:
                        gap_len = layer - gap_start
                        if gap_len >= self.min_idle_gates:
                            gaps.append((gap_start, layer))
                        gap_start = None
            # Close trailing gap
            if gap_start is not None:
                gap_len = num_layers - gap_start
                if gap_len >= self.min_idle_gates:
                    gaps.append((gap_start, num_layers))
            idle_intervals[q] = gaps

        return idle_intervals

    def schedule(
        self,
        circuit: Circuit,
        sequences: Optional[Dict[int, DDSequence]] = None,
    ) -> Circuit:
        """Insert DD pulses into idle periods of *circuit*.

        Parameters
        ----------
        circuit : Circuit
            The input circuit (not modified).
        sequences : dict, optional
            Per-qubit DD sequences.  Qubits not in the dict use
            :attr:`default_sequence`.

        Returns
        -------
        Circuit
            A new circuit with DD pulses inserted.
        """
        sequences = sequences or {}
        idle_intervals = self._find_idle_intervals(circuit)

        # Build a new circuit with DD pulses interleaved
        new_circuit = Circuit(circuit.num_qubits, name=f"{circuit.name}_dd")

        # We work with a flat gate list and insert DD gates at the
        # appropriate positions.
        # Strategy: rebuild gate list, inserting DD pulses after each gap.
        num_layers = len(circuit.gates)
        layer_idx = 0
        inserted: Dict[int, int] = {q: 0 for q in range(circuit.num_qubits)}

        for original_layer in range(num_layers):
            # Insert DD pulses for qubits that had idle gaps ending here
            for q in range(circuit.num_qubits):
                for gap_start, gap_end in idle_intervals.get(q, []):
                    if gap_end == original_layer and inserted[q] == 0:
                        # This gap ends at this layer — insert DD before
                        seq = sequences.get(q, self.default_sequence)
                        seq.apply_to_circuit(new_circuit, q)
                        inserted[q] = 1

            # Add the original gate
            if original_layer < len(circuit.gates):
                gate = circuit.gates[original_layer]
                new_circuit.gates.append(
                    Gate(gate.name, list(gate.qubits), gate.matrix,
                         list(gate.params))
                )

        # Handle trailing idle gaps
        for q in range(circuit.num_qubits):
            for gap_start, gap_end in idle_intervals.get(q, []):
                if gap_end == num_layers and inserted[q] == 0:
                    seq = sequences.get(q, self.default_sequence)
                    seq.apply_to_circuit(new_circuit, q)

        # Copy measurements
        new_circuit.measurements = [
            Measurement(m.qubit, m.cbit) for m in circuit.measurements
        ]
        new_circuit.classical_bits = circuit.classical_bits

        return new_circuit

    def insert_single(
        self,
        circuit: Circuit,
        qubit: int,
        position: int,
        sequence: Optional[DDSequence] = None,
    ) -> Circuit:
        """Insert a DD sequence at a specific gate position for one qubit.

        Parameters
        ----------
        circuit : Circuit
            Input circuit.
        qubit : int
            Target qubit.
        position : int
            Gate index at which to insert the DD sequence (before that gate).
        sequence : DDSequence, optional
            Sequence to insert (defaults to :attr:`default_sequence`).

        Returns
        -------
        Circuit
            New circuit with DD gates inserted.
        """
        seq = sequence or self.default_sequence
        new_circuit = Circuit(circuit.num_qubits, name=f"{circuit.name}_dd")

        for i, gate in enumerate(circuit.gates):
            if i == position:
                seq.apply_to_circuit(new_circuit, qubit)
            new_circuit.gates.append(
                Gate(gate.name, list(gate.qubits), gate.matrix,
                     list(gate.params))
            )

        if position >= len(circuit.gates):
            seq.apply_to_circuit(new_circuit, qubit)

        new_circuit.measurements = [
            Measurement(m.qubit, m.cbit) for m in circuit.measurements
        ]
        new_circuit.classical_bits = circuit.classical_bits

        return new_circuit


# ── Public API ──────────────────────────────────────────────────────────────

__all__ = [
    "DDSequence",
    "XY4Sequence",
    "XY8Sequence",
    "CPMGSequence",
    "UDDSequence",
    "DDScheduler",
]
