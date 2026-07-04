"""
AbirQu Noise Profiler
Copyright 2026 Abir Maheshwari

Profiles noise from real hardware data, tracks drift, and generates
noise models for simulation.
"""
import math
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class NoiseProfile:
    """Complete noise profile for a quantum device."""
    backend_name: str
    num_qubits: int
    single_qubit_errors: Dict[int, float] = field(default_factory=dict)
    two_qubit_errors: Dict[Tuple[int, int], float] = field(default_factory=dict)
    readout_errors: Dict[int, float] = field(default_factory=dict)
    t1_values: Dict[int, float] = field(default_factory=dict)
    t2_values: Dict[int, float] = field(default_factory=dict)
    gate_times: Dict[str, float] = field(default_factory=dict)
    crosstalk_rates: Dict[Tuple[int, int], float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    @property
    def average_1q_error(self) -> float:
        if not self.single_qubit_errors:
            return 0.001
        return sum(self.single_qubit_errors.values()) / len(self.single_qubit_errors)

    @property
    def average_2q_error(self) -> float:
        if not self.two_qubit_errors:
            return 0.01
        return sum(self.two_qubit_errors.values()) / len(self.two_qubit_errors)

    @property
    def average_readout_error(self) -> float:
        if not self.readout_errors:
            return 0.01
        return sum(self.readout_errors.values()) / len(self.readout_errors)

    @property
    def average_t1(self) -> float:
        if not self.t1_values:
            return 50.0
        return sum(self.t1_values.values()) / len(self.t1_values)

    @property
    def average_t2(self) -> float:
        if not self.t2_values:
            return 70.0
        return sum(self.t2_values.values()) / len(self.t2_values)

    def worst_qubit(self) -> int:
        if not self.single_qubit_errors:
            return 0
        return max(self.single_qubit_errors, key=self.single_qubit_errors.get)

    def best_qubit(self) -> int:
        if not self.single_qubit_errors:
            return 0
        return min(self.single_qubit_errors, key=self.single_qubit_errors.get)

    def worst_pair(self) -> Optional[Tuple[int, int]]:
        if not self.two_qubit_errors:
            return None
        return max(self.two_qubit_errors, key=self.two_qubit_errors.get)

    def best_pair(self) -> Optional[Tuple[int, int]]:
        if not self.two_qubit_errors:
            return None
        return min(self.two_qubit_errors, key=self.two_qubit_errors.get)

    def to_dict(self) -> Dict:
        return {
            'backend_name': self.backend_name,
            'num_qubits': self.num_qubits,
            'average_1q_error': self.average_1q_error,
            'average_2q_error': self.average_2q_error,
            'average_readout_error': self.average_readout_error,
            'average_t1': self.average_t1,
            'average_t2': self.average_t2,
            'num_crosstalk_pairs': len(self.crosstalk_rates),
            'timestamp': self.timestamp,
        }

    def generate_noise_model(self):
        from ..noise import NoiseModel
        nm = NoiseModel(self.num_qubits)
        for q, err in self.single_qubit_errors.items():
            nm.add_depolarizing_error(q, err)
        for (q1, q2), err in self.two_qubit_errors.items():
            nm.add_depolarizing_error([q1, q2], err)
        return nm


class NoiseProfiler:
    """Profiles and tracks noise characteristics of quantum hardware."""

    def __init__(self, num_qubits: int, backend_name: str = 'unknown'):
        self.num_qubits = num_qubits
        self.backend_name = backend_name
        self.current_profile = NoiseProfile(
            backend_name=backend_name, num_qubits=num_qubits,
        )
        self.profile_history: List[NoiseProfile] = []
        self._measurement_data: Dict[str, List] = {}

    def set_single_qubit_error(self, qubit: int, error_rate: float):
        self.current_profile.single_qubit_errors[qubit] = error_rate

    def set_two_qubit_error(self, q1: int, q2: int, error_rate: float):
        pair = (min(q1, q2), max(q1, q2))
        self.current_profile.two_qubit_errors[pair] = error_rate

    def set_readout_error(self, qubit: int, error_rate: float):
        self.current_profile.readout_errors[qubit] = error_rate

    def set_t1(self, qubit: int, t1_us: float):
        self.current_profile.t1_values[qubit] = t1_us

    def set_t2(self, qubit: int, t2_us: float):
        self.current_profile.t2_values[qubit] = t2_us

    def set_crosstalk(self, q1: int, q2: int, rate: float):
        pair = (min(q1, q2), max(q1, q2))
        self.current_profile.crosstalk_rates[pair] = rate

    def snapshot(self) -> NoiseProfile:
        import copy
        snapshot = copy.deepcopy(self.current_profile)
        snapshot.timestamp = time.time()
        self.profile_history.append(snapshot)
        return snapshot

    def detect_drift(self, window: int = 5) -> Dict:
        if len(self.profile_history) < 2:
            return {'drift_detected': False, 'num_snapshots': len(self.profile_history)}

        recent = self.profile_history[-window:]
        if len(recent) < 2:
            return {'drift_detected': False, 'num_snapshots': len(recent)}

        errors = [p.average_1q_error for p in recent]
        mean_err = sum(errors) / len(errors)
        variance = sum((e - mean_err) ** 2 for e in errors) / len(errors)
        drift_magnitude = math.sqrt(variance) if variance > 0 else 0

        return {
            'drift_detected': drift_magnitude > 0.001,
            'drift_magnitude': drift_magnitude,
            'mean_error': mean_err,
            'error_trend': errors[-1] - errors[0] if len(errors) >= 2 else 0,
            'num_snapshots': len(recent),
        }

    def generate_calibration_circuits(self) -> List[Dict]:
        circuits = []
        for q in range(self.num_qubits):
            circuits.append({
                'name': f't1_q{q}',
                'type': 't1',
                'qubit': q,
                'delays': [0, 10, 20, 50, 100, 200, 500],
            })
            circuits.append({
                'name': f't2_q{q}',
                'type': 'ramsey',
                'qubit': q,
                'delays': [0, 5, 10, 20, 50, 100],
            })
            circuits.append({
                'name': f'readout_q{q}',
                'type': 'readout',
                'qubit': q,
                'shots': 1000,
            })
        for q1 in range(self.num_qubits):
            for q2 in range(q1 + 1, self.num_qubits):
                circuits.append({
                    'name': f'rb_{q1}_{q2}',
                    'type': 'rb_2q',
                    'qubits': [q1, q2],
                    'num_cliffords': [1, 2, 4, 8, 16, 32],
                })
        return circuits

    def get_render_data(self) -> Dict:
        return {
            'current_profile': self.current_profile.to_dict(),
            'history_length': len(self.profile_history),
            'drift': self.detect_drift(),
        }

    def __repr__(self):
        return (f"NoiseProfiler({self.backend_name}, "
                f"qubits={self.num_qubits}, "
                f"snapshots={len(self.profile_history)})")


class DriftTracker:
    """Tracks parameter drift over time."""

    def __init__(self):
        self._data: Dict[str, List[Tuple[float, float]]] = {}

    def record(self, parameter: str, value: float, timestamp: Optional[float] = None):
        ts = timestamp or time.time()
        if parameter not in self._data:
            self._data[parameter] = []
        self._data[parameter].append((ts, value))

    def get_drift(self, parameter: str) -> Dict:
        if parameter not in self._data or len(self._data[parameter]) < 2:
            return {'drift': 0.0, 'stable': True}
        values = [v for _, v in self._data[parameter]]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        drift = abs(values[-1] - values[0])
        return {
            'drift': drift,
            'stable': drift < 0.01,
            'mean': mean,
            'variance': variance,
            'num_points': len(values),
        }

    def get_all_drifts(self) -> Dict[str, Dict]:
        return {param: self.get_drift(param) for param in self._data}
