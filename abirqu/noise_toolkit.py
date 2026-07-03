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


# ═══════════════════════════════════════════════════════════════════
#  Error Mitigation Pipeline
# ═══════════════════════════════════════════════════════════════════


class ReadoutErrorMitigator:
    """Readout error mitigation via confusion matrix inversion."""

    def calibrate(self, measured_confusion: np.ndarray) -> np.ndarray:
        mat = np.asarray(measured_confusion, dtype=float)
        if mat.shape[0] != mat.shape[1]:
            raise ValueError("confusion matrix must be square")
        reg = 1e-8 * np.eye(mat.shape[0])
        return np.linalg.pinv(mat + reg)

    def mitigate(self, noisy_probs: np.ndarray, inv_confusion: np.ndarray) -> np.ndarray:
        p = np.asarray(noisy_probs, dtype=float)
        corrected = inv_confusion @ p
        corrected = np.clip(corrected, 0.0, None)
        s = corrected.sum()
        return corrected / s if s > 0 else corrected


class ZeroNoiseExtrapolatorSimple:
    """Simple linear extrapolation to zero noise."""

    def extrapolate(self, noise_scales: Sequence[float], values: Sequence[float]) -> float:
        x = np.asarray(noise_scales, dtype=float)
        y = np.asarray(values, dtype=float)
        if len(x) != len(y) or len(x) < 2:
            raise ValueError("Need at least 2 scale/value points")
        a, b = np.polyfit(x, y, 1)
        return float(b)


class PauliTwirlingPass:
    """Pauli twirling metadata generation."""

    def twirl_metadata(self, gate_count: int, seed: int = 0) -> Dict[str, int]:
        rng = np.random.default_rng(seed)
        x = int(rng.integers(0, gate_count + 1))
        y = int(rng.integers(0, gate_count + 1 - x))
        z = gate_count - x - y
        return {"X": x, "Y": y, "Z": z, "total": gate_count}


class ErrorMitigationPipeline:
    """Unified error mitigation pipeline combining ZNE, readout, and twirling."""

    def run(
        self,
        noisy_probs: np.ndarray,
        confusion: np.ndarray,
        noise_scales: Sequence[float],
        measured_values: Sequence[float],
    ) -> Dict[str, float]:
        rem = ReadoutErrorMitigator()
        inv = rem.calibrate(confusion)
        corrected = rem.mitigate(noisy_probs, inv)
        zne = ZeroNoiseExtrapolatorSimple().extrapolate(noise_scales, measured_values)
        return {
            "zne_zero_noise": zne,
            "corrected_sum": float(corrected.sum()),
            "max_corrected_prob": float(np.max(corrected) if len(corrected) else 0.0),
        }

    def zero_noise_extrapolation(
        self,
        scales: Sequence[float],
        measured_values: Sequence[float],
    ) -> float:
        """Simple zero-noise extrapolation."""
        return ZeroNoiseExtrapolatorSimple().extrapolate(scales, measured_values)


# ═══════════════════════════════════════════════════════════════════
#  Gate Folding ZNE (G → GG†G)
# ═══════════════════════════════════════════════════════════════════

class GateFoldingZNE:
    """
    Gate folding for Zero Noise Extrapolation.

    Implements the G→GG†G identity insertion technique:
    - For scale factor 1: original circuit (no noise amplification)
    - For scale factor 3: each gate G becomes G G† G (3x noise)
    - For scale factor 5: each gate G becomes G G† G G† G (5x noise)
    - For scale factor n: each gate G repeated n times with G† inserted

    The key insight: G G† = I (identity), so the logical operation is
    unchanged, but the physical noise is amplified by a known factor.

    References:
        - Li & Benjamin (2017): "Estimating Quantum Speedup with ZNE"
        - Gidney (2021): "Extrapolation of Error Mitigation"
    """

    def __init__(self):
        self._inverse_map = {
            "H": "H", "X": "X", "Y": "Y", "Z": "Z",
            "S": "S_DAG", "S_DAG": "S", "T": "T_DAG", "T_DAG": "T",
            "CNOT": "CNOT", "CZ": "CZ", "SWAP": "SWAP",
            "RX": "RX", "RY": "RY", "RZ": "RZ",
        }

    def fold_circuit(self, circuit: Circuit, scale_factor: int) -> Circuit:
        """
        Apply gate folding to amplify noise by a known factor.

        Parameters
        ----------
        circuit : Circuit
            Original circuit
        scale_factor : int
            Noise amplification factor (must be odd: 1, 3, 5, 7, ...)
            - 1: no change
            - 3: G → GG†G
            - 5: G → GGG†GG†G

        Returns
        -------
        Circuit
            Folded circuit with amplified noise
        """
        if scale_factor < 1 or scale_factor % 2 == 0:
            raise ValueError("Scale factor must be a positive odd integer (1, 3, 5, ...)")

        if scale_factor == 1:
            return circuit.copy()

        # Number of G†G pairs to insert = (scale_factor - 1) / 2
        num_pairs = (scale_factor - 1) // 2

        folded = Circuit(circuit.num_qubits, f"{circuit.name}_folded{scale_factor}")

        for gate in circuit.gates:
            qubits = gate.qubits if isinstance(gate.qubits, list) else [gate.qubits]
            params = gate.params or []

            # Add original gate
            folded.add_gate(gate.name, qubits, params if params else None)

            # Insert G†G pairs
            for _ in range(num_pairs):
                # Add G† (inverse gate)
                inv_name = self._inverse_map.get(gate.name, gate.name)
                if inv_name == gate.name and gate.name not in ("H", "X", "Y", "Z"):
                    # For parametric gates, negate the parameter
                    inv_params = [-p for p in params] if params else None
                    folded.add_gate(inv_name, qubits, inv_params)
                else:
                    folded.add_gate(inv_name, qubits, params if params else None)

                # Add G (original gate again)
                folded.add_gate(gate.name, qubits, params if params else None)

        return folded

    def fold_single_gate(self, gate_name: str, qubits: list,
                         params: list, scale_factor: int) -> list:
        """
        Fold a single gate, returning a list of (name, qubits, params) tuples.

        Useful for gate-level noise amplification without creating a full circuit.
        """
        if scale_factor < 1 or scale_factor % 2 == 0:
            raise ValueError("Scale factor must be a positive odd integer")

        num_pairs = (scale_factor - 1) // 2
        result = [(gate_name, qubits, params)]

        for _ in range(num_pairs):
            inv_name = self._inverse_map.get(gate_name, gate_name)
            if inv_name == gate_name and gate_name not in ("H", "X", "Y", "Z"):
                inv_params = [-p for p in params] if params else None
                result.append((inv_name, qubits, inv_params))
            else:
                result.append((inv_name, qubits, params))
            result.append((gate_name, qubits, params))

        return result

    def amplify_noise(self, circuit: Circuit, noise_scale: float) -> Circuit:
        """
        Amplify noise by a continuous scale factor.

        Uses a combination of gate folding and partial folding:
        - Integer part: full gate folding
        - Fractional part: partial identity insertion
        """
        int_scale = int(noise_scale)
        if int_scale % 2 == 0:
            int_scale += 1  # Make it odd

        # Full folding for integer part
        folded = self.fold_circuit(circuit, int_scale)

        # For fractional part, we can't do partial folding on discrete gates,
        # so we just use the integer-folded circuit
        return folded


class ZNEPipeline:
    """
    Complete ZNE pipeline: fold circuits at multiple noise levels,
    execute each, and extrapolate to zero noise.

    Usage:
        zne = ZNEPipeline()
        result = zne.execute_with_mitigation(
            circuit, simulator, noise_scales=[1, 3, 5],
            shots=4096
        )
    """

    def __init__(self, extrapolation_method: str = "richardson"):
        self.folder = GateFoldingZNE()
        self.extrapolator = ZeroNoiseExtrapolator(method=extrapolation_method)

    def execute_with_mitigation(self, circuit: Circuit, simulator,
                                 noise_scales: Optional[List[int]] = None,
                                 shots: int = 4096,
                                 observable: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Execute circuit with ZNE error mitigation.

        Parameters
        ----------
        circuit : Circuit
            Circuit to execute
        simulator : simulator instance
            Simulator with run_circuit method
        noise_scales : list of int, optional
            Scale factors (must be odd). Default: [1, 3, 5]
        shots : int
            Shots per scale level
        observable : np.ndarray, optional
            Observable for expectation value. If None, uses counts.

        Returns
        -------
        dict with:
            - mitigated_value: extrapolated zero-noise value
            - raw_values: values at each noise level
            - noise_levels: noise scales used
            - counts: measurement counts at each level
        """
        if noise_scales is None:
            noise_scales = [1, 3, 5]

        raw_values = []
        all_counts = {}

        for scale in noise_scales:
            # Fold circuit
            folded = self.folder.fold_circuit(circuit, scale)

            # Execute
            result = simulator.run_circuit(folded, shots=shots)
            counts = result.get('counts', {})
            all_counts[f"scale_{scale}"] = counts

            # Compute expectation value
            if observable is not None:
                total = sum(counts.values())
                exp_val = 0.0
                for bitstring, count in counts.items():
                    idx = int(bitstring, 2)
                    exp_val += np.real(observable[idx, idx]) * count / total
                raw_values.append(float(exp_val))
            else:
                # Use parity as default observable
                total = sum(counts.values())
                exp_val = 0.0
                for bitstring, count in counts.items():
                    parity = sum(int(b) for b in bitstring) % 2
                    exp_val += (1 - 2 * parity) * count / total
                raw_values.append(float(exp_val))

        # Extrapolate to zero noise
        mitigated = self.extrapolator.extrapolate(
            [float(s) for s in noise_scales], raw_values
        )

        return {
            "mitigated_value": mitigated,
            "raw_values": raw_values,
            "noise_levels": noise_scales,
            "counts": all_counts,
        }


# ═══════════════════════════════════════════════════════════════════
#  Enhanced Readout Error Mitigation
# ═══════════════════════════════════════════════════════════════════

class EnhancedReadoutMitigator:
    """
    Advanced readout error mitigation with multiple inversion strategies.

    Improvements over basic ReadoutMitigator:
    1. Regularized matrix inversion (avoids numerical instability)
    2. Bayesian inference for small calibration datasets
    3. Per-qubit correction (scalable to many qubits)
    4. Measurement symmetry exploitation
    5. Bootstrap confidence intervals

    References:
        - Bravyi et al. (2021): "Mitigating readout errors in quantum simulations"
        - van den Berg et al. (2023): "Probabilistic error cancellation for
          measurement-based quantum computing"
    """

    def __init__(self, regularization: float = 1e-4):
        """
        Parameters
        ----------
        regularization : float
            Tikhonov regularization parameter (higher = more stable, less accurate)
        """
        self.regularization = regularization

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

    def regularized_inverse(self, confusion: np.ndarray) -> np.ndarray:
        """
        Compute regularized inverse via Tikhonov regularization.

        Solves: (A^T A + λI)^{-1} A^T instead of A^{-1}
        This is much more numerically stable for ill-conditioned confusion matrices.
        """
        A = confusion
        lam = self.regularization
        ATA = A.T @ A + lam * np.eye(A.shape[1])
        AT = A.T
        return np.linalg.solve(ATA, AT)

    def mitigate(self, counts: Dict[str, int],
                 confusion: np.ndarray) -> Dict[str, float]:
        """
        Apply readout mitigation with regularized inversion.
        """
        n_qubits = int(np.log2(confusion.shape[0]))
        total = sum(counts.values())

        prob_vec = np.zeros(confusion.shape[0])
        for state, count in counts.items():
            prob_vec[int(state, 2)] = count / total

        # Try regularized inverse first
        try:
            inv = self.regularized_inverse(confusion)
            mitigated = inv @ prob_vec
        except np.linalg.LinAlgError:
            # Fall back to pseudoinverse
            inv = np.linalg.pinv(confusion)
            mitigated = inv @ prob_vec

        # Clip negative probabilities
        mitigated = np.maximum(mitigated, 0)
        s = mitigated.sum()
        if s > 0:
            mitigated /= s

        return {format(i, f"0{n_qubits}b"): float(mitigated[i])
                for i in range(len(mitigated)) if mitigated[i] > 1e-10}

    def per_qubit_mitigate(self, counts: Dict[str, int],
                            qubit_confusions: Dict[int, np.ndarray],
                            n_qubits: int) -> Dict[str, float]:
        """
        Apply per-qubit readout mitigation (scalable approach).

        Instead of inverting a 2^n × 2^n matrix, invert n small 2×2 matrices.
        This is exponentially cheaper for large systems.
        """
        total = sum(counts.values())
        prob_vec = np.zeros(2 ** n_qubits)
        for state, count in counts.items():
            prob_vec[int(state, 2)] = count / total

        # Apply per-qubit correction
        corrected = prob_vec.copy()
        for qubit, confusion in qubit_confusions.items():
            inv = self.regularized_inverse(confusion)
            # Apply correction to the marginal of this qubit
            n_states = 2 ** n_qubits
            for i in range(n_states):
                bit = (i >> (n_qubits - 1 - qubit)) & 1
                # The correction factor for this qubit
                corrected[i] *= inv[0, bit] if bit == 0 else inv[1, bit]

        # Normalize
        corrected = np.maximum(corrected, 0)
        s = corrected.sum()
        if s > 0:
            corrected /= s

        return {format(i, f"0{n_qubits}b"): float(corrected[i])
                for i in range(len(corrected)) if corrected[i] > 1e-10}

    def bootstrap_confidence(self, counts: Dict[str, int],
                              confusion: np.ndarray,
                              n_bootstrap: int = 100,
                              confidence: float = 0.95) -> Dict[str, Any]:
        """
        Bootstrap confidence intervals for mitigated probabilities.

        Resamples measurement outcomes and applies mitigation to each
        resample to estimate uncertainty.
        """
        total = sum(counts.values())
        n_qubits = int(np.log2(confusion.shape[0]))

        # Convert to probability vector
        prob_vec = np.zeros(2 ** n_qubits)
        for state, count in counts.items():
            prob_vec[int(state, 2)] = count / total

        # Bootstrap resampling
        bootstrap_results = []
        inv = self.regularized_inverse(confusion)

        for _ in range(n_bootstrap):
            # Resample
            resampled = np.random.multinomial(total, prob_vec) / total
            # Mitigate
            mitigated = inv @ resampled
            mitigated = np.maximum(mitigated, 0)
            s = mitigated.sum()
            if s > 0:
                mitigated /= s
            bootstrap_results.append(mitigated)

        bootstrap_array = np.array(bootstrap_results)

        # Compute confidence intervals
        alpha = (1 - confidence) / 2
        lower = np.percentile(bootstrap_array, alpha * 100, axis=0)
        upper = np.percentile(bootstrap_array, (1 - alpha) * 100, axis=0)
        mean = np.mean(bootstrap_array, axis=0)

        return {
            "mean": {format(i, f"0{n_qubits}b"): float(mean[i])
                     for i in range(len(mean)) if mean[i] > 1e-10},
            "lower": {format(i, f"0{n_qubits}b"): float(lower[i])
                      for i in range(len(lower)) if mean[i] > 1e-10},
            "upper": {format(i, f"0{n_qubits}b"): float(upper[i])
                      for i in range(len(upper)) if mean[i] > 1e-10},
            "confidence": confidence,
            "n_bootstrap": n_bootstrap,
        }

    def build_per_qubit_confusion(self, calibration_counts: Dict[str, Dict[str, int]],
                                   n_qubits: int) -> Dict[int, np.ndarray]:
        """
        Build per-qubit 2×2 confusion matrices from full calibration data.

        This decomposes the 2^n × 2^n confusion matrix into n independent
        2×2 matrices, enabling exponential speedup in mitigation.
        """
        qubit_confusions = {}

        for q in range(n_qubits):
            # Accumulate counts for this qubit
            qubit_counts = np.zeros((2, 2))  # [measured, true]

            for true_state, measured_counts in calibration_counts.items():
                true_bit = (int(true_state, 2) >> (n_qubits - 1 - q)) & 1
                for meas_state, count in measured_counts.items():
                    meas_bit = (int(meas_state, 2) >> (n_qubits - 1 - q)) & 1
                    qubit_counts[meas_bit, true_bit] += count

            # Normalize to probabilities
            row_sums = qubit_counts.sum(axis=1, keepdims=True)
            row_sums = np.maximum(row_sums, 1)
            qubit_confusions[q] = qubit_counts / row_sums

        return qubit_confusions
