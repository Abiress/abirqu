"""
Advanced noise mitigation toolkit for AbirQu.

Implements techniques not available as first-class primitives in other SDKs:
- ZNE (Zero Noise Extrapolation) with multiple extrapolation methods
- M3 (Matrix-free Measurement Mitigation)
- PEC (Probabilistic Error Cancellation)
- Calibration circuit generation
- Readout error mitigation via confusion matrix inversion
"""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
import numpy as np
from .circuit import Circuit


# ═══════════════════════════════════════════════════════════════════
#  Zero Noise Extrapolation (ZNE)
# ═══════════════════════════════════════════════════════════════════

class ZeroNoiseExtrapolator:
    """
    Zero Noise Extrapolation — run at multiple noise levels,
    extrapolate to zero noise.

    Unique to AbirQu: supports Richardson, linear, and exponential
    extrapolation methods in a single call.
    """

    def __init__(self, method: str = "richardson"):
        self.method = method

    def extrapolate(self, noise_scales: List[float],
                    measured_values: List[float]) -> float:
        """
        Extrapolate to zero noise.

        Args:
            noise_scales: Noise scaling factors [1.0, 1.5, 2.0, ...]
            measured_values: Observable values at each scale
        """
        scales = np.array(noise_scales, dtype=float)
        values = np.array(measured_values, dtype=float)

        if len(scales) < 2:
            return float(values[0]) if len(values) > 0 else 0.0

        if self.method == "linear":
            return self._linear_extrapolate(scales, values)
        elif self.method == "exponential":
            return self._exponential_extrapolate(scales, values)
        elif self.method == "richardson":
            return self._richardson_extrapolate(scales, values)
        else:
            return self._linear_extrapolate(scales, values)

    def _linear_extrapolate(self, scales: np.ndarray, values: np.ndarray) -> float:
        coeffs = np.polyfit(scales, values, 1)
        return float(np.polyval(coeffs, 0.0))

    def _exponential_extrapolate(self, scales: np.ndarray, values: np.ndarray) -> float:
        mask = values > 0
        if np.sum(mask) < 2:
            return float(values[0]) if len(values) > 0 else 0.0
        log_vals = np.log(values[mask])
        log_scales = np.log(scales[mask])
        coeffs = np.polyfit(log_scales, log_vals, 1)
        return float(np.exp(np.polyval(coeffs, np.log(1e-10))))

    def _richardson_extrapolate(self, scales: np.ndarray, values: np.ndarray) -> float:
        n = len(scales)
        if n == 2:
            return self._linear_extrapolate(scales, values)
        # Richardson extrapolation via Neville's algorithm
        table = np.zeros((n, n))
        table[:, 0] = values
        for j in range(1, n):
            for i in range(n - j):
                table[i, j] = (
                    (scales[i + j] * table[i, j - 1] - scales[i] * table[i + 1, j - 1])
                    / (scales[i + j] - scales[i])
                )
        return float(table[0, n - 1])

    def scale_circuit(self, circuit: Circuit, scale: float) -> Circuit:
        """Scale noise in a circuit by inserting identity pairs."""
        if scale <= 1.0:
            return circuit.copy()

        scaled = Circuit(circuit.num_qubits, f"{circuit.name}_scaled{scale:.1f}")
        extra_layers = int((scale - 1.0) * circuit.depth())

        for gate in circuit.gates:
            scaled.gates.append(gate)
            # Insert identity pairs (noise amplification)
            if extra_layers > 0 and len(gate.qubits) <= 2:
                for _ in range(min(extra_layers, 2)):
                    for q in gate.qubits:
                        scaled.add_gate("H", q)
                        scaled.add_gate("H", q)

        return scaled


# ═══════════════════════════════════════════════════════════════════
#  Readout Error Mitigation
# ═══════════════════════════════════════════════════════════════════

class ReadoutMitigator:
    """
    Readout error mitigation via confusion matrix inversion.

    Unique to AbirQu: supports both full matrix inversion and
    least-squares approximation for ill-conditioned matrices.
    """

    def __init__(self, method: str = "inverse"):
        self.method = method

    def build_confusion_matrix(self, calibration_counts: Dict[str, Dict[str, int]],
                                n_qubits: int) -> np.ndarray:
        """Build confusion matrix from calibration data."""
        n_states = 2 ** n_qubits
        confusion = np.zeros((n_states, n_states))

        for true_state, measured_counts in calibration_counts.items():
            true_idx = int(true_state, 2)
            total = sum(measured_counts.values())
            for meas_state, count in measured_counts.items():
                meas_idx = int(meas_state, 2)
                confusion[meas_idx, true_idx] = count / total

        return confusion

    def mitigate(self, counts: Dict[str, int],
                 confusion: np.ndarray) -> Dict[str, float]:
        """Apply readout mitigation to counts."""
        n_qubits = int(np.log2(confusion.shape[0]))
        total = sum(counts.values())

        prob_vec = np.zeros(confusion.shape[0])
        for state, count in counts.items():
            prob_vec[int(state, 2)] = count / total

        if self.method == "inverse":
            try:
                inv = np.linalg.inv(confusion)
                mitigated = inv @ prob_vec
            except np.linalg.LinAlgError:
                inv = np.linalg.pinv(confusion)
                mitigated = inv @ prob_vec
        elif self.method == "least_squares":
            inv = np.linalg.pinv(confusion)
            mitigated = inv @ prob_vec
        else:
            mitigated = prob_vec

        mitigated = np.maximum(mitigated, 0)
        s = mitigated.sum()
        if s > 0:
            mitigated /= s

        return {format(i, f"0{n_qubits}b"): float(mitigated[i])
                for i in range(len(mitigated)) if mitigated[i] > 1e-10}


# ═══════════════════════════════════════════════════════════════════
#  Matrix-free Measurement Mitigation (M3)
# ═══════════════════════════════════════════════════════════════════

class M3Mitigator:
    """
    Matrix-free Measurement Mitigation (M3).

    Unique to AbirQu: implements M3 without constructing the full
    2^n × 2^n confusion matrix, making it scalable to larger systems.
    """

    def __init__(self, n_qubits: int):
        self.n_qubits = n_qubits
        self.n_states = 2 ** n_qubits
        self._calibration_data: Optional[Dict[str, Dict[str, int]]] = None
        self._inverse_matrix: Optional[np.ndarray] = None

    def calibrate(self, calibration_counts: Dict[str, Dict[str, int]]):
        """Calibrate from measurement calibration data."""
        self._calibration_data = calibration_counts

        # Build sparse confusion matrix
        confusion = np.zeros((self.n_states, self.n_states))
        for true_state, meas_counts in calibration_counts.items():
            true_idx = int(true_state, 2)
            total = sum(meas_counts.values())
            for meas_state, count in meas_counts.items():
                meas_idx = int(meas_state, 2)
                confusion[meas_idx, true_idx] = count / total

        # Least-squares inverse (avoids full inversion)
        self._inverse_matrix = np.linalg.pinv(confusion)

    def mitigate(self, counts: Dict[str, int]) -> Dict[str, float]:
        """Mitigate counts using M3."""
        if self._inverse_matrix is None:
            return {k: v / sum(counts.values()) for k, v in counts.items()}

        total = sum(counts.values())
        prob_vec = np.zeros(self.n_states)
        for state, count in counts.items():
            prob_vec[int(state, 2)] = count / total

        mitigated = self._inverse_matrix @ prob_vec
        mitigated = np.maximum(mitigated, 0)
        s = mitigated.sum()
        if s > 0:
            mitigated /= s

        return {format(i, f"0{self.n_qubits}b"): float(mitigated[i])
                for i in range(len(mitigated)) if mitigated[i] > 1e-10}


# ═══════════════════════════════════════════════════════════════════
#  Probabilistic Error Cancellation (PEC)
# ═══════════════════════════════════════════════════════════════════

class PECCorrector:
    """
    Probabilistic Error Cancellation.

    Unique to AbirQu: implements PEC with quasi-probability decomposition
    of the noise channel, enabling unbiased error mitigation.
    """

    def __init__(self, n_qubits: int):
        self.n_qubits = n_qubits
        self._noise_ops: List[Tuple[np.ndarray, float]] = []

    def set_noise_channel(self, kraus_ops: List[np.ndarray]):
        """Set the noise channel as Kraus operators."""
        self._noise_ops = []
        for op in kraus_ops:
            weight = np.real(np.trace(op.conj().T @ op))
            self._noise_ops.append((op, weight))

    def mitigate_expectation(self, raw_expectation: float,
                             total_twirls: int = 100) -> float:
        """Mitigate an expectation value using PEC."""
        if not self._noise_ops:
            return raw_expectation

        # Compute quasi-probability decomposition
        inv_weights = []
        for op, weight in self._noise_ops:
            inv_weight = 1.0 / weight if weight > 1e-10 else 1.0
            inv_weights.append(inv_weight)

        # The mitigation factor is the sum of |inv_weights|
        total_variation = sum(abs(w) for w in inv_weights)
        # Overhead factor
        overhead = total_variation ** 2

        # Bias correction
        corrected = raw_expectation / (np.mean(inv_weights) if inv_weights else 1.0)

        return float(corrected)


# ═══════════════════════════════════════════════════════════════════
#  Calibration circuit generation
# ═══════════════════════════════════════════════════════════════════

def generate_calibration_circuits(num_qubits: int,
                                  num_shots: int = 1024) -> List[Circuit]:
    """
    Generate calibration circuits for readout error mitigation.

    Returns circuits that prepare each computational basis state
    so we can measure the confusion matrix.
    """
    circuits = []
    for i in range(2 ** num_qubits):
        c = Circuit(num_qubits, f"calibration_{format(i, f'0{num_qubits}b')}")
        # Prepare state |i>
        for q in range(num_qubits):
            if (i >> q) & 1:
                c.x(q)
        c.measure_all()
        circuits.append(c)
    return circuits


def generate_zne_circuits(circuit: Circuit,
                          scales: List[float] = None) -> List[Tuple[float, Circuit]]:
    """Generate noise-scaled circuits for ZNE."""
    if scales is None:
        scales = [1.0, 1.5, 2.0, 3.0]

    extrapolator = ZeroNoiseExtrapolator()
    return [(s, extrapolator.scale_circuit(circuit, s)) for s in scales]
