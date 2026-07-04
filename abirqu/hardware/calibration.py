"""
AbirQu Hardware Calibration
Copyright 2026 Abir Maheshwari

Comprehensive calibration system for quantum hardware:
T1/T2 coherence times, gate fidelities, readout errors, crosstalk.
"""
import math
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


@dataclass
class QubitProperties:
    """Properties of a single physical qubit."""
    qubit_id: int
    t1_us: float = 50.0
    t2_us: float = 70.0
    t2_echo_us: float = 100.0
    frequency_ghz: float = 5.0
    anharmonicity_mhz: float = -300.0
    readout_error_0: float = 0.01
    readout_error_1: float = 0.03
    readout_fidelity: float = 0.98
    sx_error_rate: float = 0.001
    x_error_rate: float = 0.001
    z_error_rate: float = 0.0001
    t1_date: float = 0.0
    t2_date: float = 0.0

    @property
    def coherence_time(self) -> float:
        return min(self.t1_us, self.t2_us / 2)

    @property
    def is_healthy(self) -> bool:
        return (self.t1_us > 10 and self.t2_us > 10 and
                self.readout_fidelity > 0.9 and self.x_error_rate < 0.05)

    def to_dict(self) -> Dict:
        return {
            'qubit_id': self.qubit_id,
            't1_us': self.t1_us, 't2_us': self.t2_us,
            't2_echo_us': self.t2_echo_us,
            'frequency_ghz': self.frequency_ghz,
            'anharmonicity_mhz': self.anharmonicity_mhz,
            'readout_error_0': self.readout_error_0,
            'readout_error_1': self.readout_error_1,
            'readout_fidelity': self.readout_fidelity,
            'sx_error_rate': self.sx_error_rate,
            'x_error_rate': self.x_error_rate,
            'z_error_rate': self.z_error_rate,
            'coherence_time': self.coherence_time,
            'is_healthy': self.is_healthy,
        }


@dataclass
class GateProperties:
    """Properties of a two-qubit gate."""
    qubit_pair: Tuple[int, int]
    gate_name: str = 'CNOT'
    fidelity: float = 0.99
    error_rate: float = 0.01
    duration_ns: float = 300.0
    angle_error_rad: float = 0.01
    crosstalk_error: float = 0.001
    calibration_date: float = 0.0

    @property
    def is_healthy(self) -> bool:
        return self.fidelity > 0.95 and self.error_rate < 0.05

    def to_dict(self) -> Dict:
        return {
            'qubit_pair': list(self.qubit_pair),
            'gate_name': self.gate_name,
            'fidelity': self.fidelity,
            'error_rate': self.error_rate,
            'duration_ns': self.duration_ns,
            'angle_error_rad': self.angle_error_rad,
            'crosstalk_error': self.crosstalk_error,
            'is_healthy': self.is_healthy,
        }


@dataclass
class ReadoutCalibration:
    """Readout calibration data for all qubits."""
    confusion_matrices: Dict[int, Any] = field(default_factory=dict)
    assignment_fidelity: float = 0.98
    discriminators: Dict[int, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'num_calibrated': len(self.confusion_matrices),
            'assignment_fidelity': self.assignment_fidelity,
        }


@dataclass
class T1Calibration:
    """T1 relaxation calibration."""
    t1_values: Dict[int, float] = field(default_factory=dict)
    exponential_fits: Dict[int, Dict] = field(default_factory=dict)

    def get_t1(self, qubit: int) -> float:
        return self.t1_values.get(qubit, 50.0)

    def average_t1(self) -> float:
        if not self.t1_values:
            return 50.0
        return sum(self.t1_values.values()) / len(self.t1_values)

    def to_dict(self) -> Dict:
        return {
            't1_values': self.t1_values,
            'average_t1': self.average_t1(),
            'num_qubits': len(self.t1_values),
        }


@dataclass
class T2Calibration:
    """T2 dephasing calibration."""
    t2_values: Dict[int, float] = field(default_factory=dict)
    t2_echo_values: Dict[int, float] = field(default_factory=dict)
    ramsey_fits: Dict[int, Dict] = field(default_factory=dict)

    def get_t2(self, qubit: int) -> float:
        return self.t2_values.get(qubit, 70.0)

    def average_t2(self) -> float:
        if not self.t2_values:
            return 70.0
        return sum(self.t2_values.values()) / len(self.t2_values)

    def to_dict(self) -> Dict:
        return {
            't2_values': self.t2_values,
            't2_echo_values': self.t2_echo_values,
            'average_t2': self.average_t2(),
            'num_qubits': len(self.t2_values),
        }


class HardwareCalibration:
    """Complete hardware calibration data for a quantum device."""

    def __init__(self, num_qubits: int, backend_name: str = 'unknown'):
        self.num_qubits = num_qubits
        self.backend_name = backend_name
        self.calibration_timestamp = time.time()
        self.qubits: Dict[int, QubitProperties] = {}
        self.gates: Dict[Tuple[int, int], GateProperties] = {}
        self.readout = ReadoutCalibration()
        self.t1_cal = T1Calibration()
        self.t2_cal = T2Calibration()
        self._crosstalk_matrix = None

        for i in range(num_qubits):
            self.qubits[i] = QubitProperties(qubit_id=i)

    def set_t1(self, qubit: int, t1_us: float):
        if qubit in self.qubits:
            self.qubits[qubit].t1_us = t1_us
            self.qubits[qubit].t1_date = time.time()
            self.t1_cal.t1_values[qubit] = t1_us

    def set_t2(self, qubit: int, t2_us: float):
        if qubit in self.qubits:
            self.qubits[qubit].t2_us = t2_us
            self.qubits[qubit].t2_date = time.time()
            self.t2_cal.t2_values[qubit] = t2_us

    def set_gate_error(self, q1: int, q2: int, error_rate: float,
                       gate_name: str = 'CNOT'):
        pair = (min(q1, q2), max(q1, q2))
        fidelity = 1.0 - error_rate
        self.gates[pair] = GateProperties(
            qubit_pair=pair, gate_name=gate_name,
            fidelity=fidelity, error_rate=error_rate,
            calibration_date=time.time(),
        )

    def set_readout_error(self, qubit: int, error_0: float, error_1: float):
        if qubit in self.qubits:
            self.qubits[qubit].readout_error_0 = error_0
            self.qubits[qubit].readout_error_1 = error_1
            self.qubits[qubit].readout_fidelity = 1 - (error_0 + error_1) / 2
            self.readout.confusion_matrices[qubit] = {
                'P(0|0)': 1 - error_0, 'P(1|0)': error_0,
                'P(0|1)': error_1, 'P(1|1)': 1 - error_1,
            }

    def set_frequency(self, qubit: int, freq_ghz: float):
        if qubit in self.qubits:
            self.qubits[qubit].frequency_ghz = freq_ghz

    def get_qubit(self, qubit: int) -> Optional[QubitProperties]:
        return self.qubits.get(qubit)

    def get_gate(self, q1: int, q2: int) -> Optional[GateProperties]:
        return self.gates.get((min(q1, q2), max(q1, q2)))

    def get_healthy_qubits(self) -> List[int]:
        return [q for q, props in self.qubits.items() if props.is_healthy]

    def get_best_qubit_pairs(self, n: int = 1) -> List[Tuple[int, int]]:
        pairs = [(q1, q2) for (q1, q2), g in self.gates.items() if g.is_healthy]
        pairs.sort(key=lambda p: -self.gates[p].fidelity)
        return pairs[:n]

    def average_gate_fidelity(self) -> float:
        if not self.gates:
            return 0.99
        return sum(g.fidelity for g in self.gates.values()) / len(self.gates)

    def average_readout_fidelity(self) -> float:
        fidelities = [q.readout_fidelity for q in self.qubits.values()]
        return sum(fidelities) / len(fidelities) if fidelities else 0.98

    def compute_crosstalk_matrix(self) -> List[List[float]]:
        n = self.num_qubits
        matrix = [[0.0] * n for _ in range(n)]
        for (q1, q2), gate in self.gates.items():
            if q1 < n and q2 < n:
                matrix[q1][q2] = gate.crosstalk_error
                matrix[q2][q1] = gate.crosstalk_error
        self._crosstalk_matrix = matrix
        return matrix

    def generate_noise_model(self):
        from ..noise import NoiseModel
        nm = NoiseModel(self.num_qubits)
        for qubit, props in self.qubits.items():
            nm.add_depolarizing_error(qubit, props.x_error_rate)
            nm.add_amplitude_damping(qubit, 1 - math.exp(-1 / props.t1_us))
            nm.add_phase_damping(qubit, 1 - math.exp(-1 / props.t2_us))
        return nm

    def get_render_data(self) -> Dict:
        qubits = [q.to_dict() for q in self.qubits.values()]
        gates = [g.to_dict() for g in self.gates.values()]
        return {
            'backend_name': self.backend_name,
            'num_qubits': self.num_qubits,
            'calibration_timestamp': self.calibration_timestamp,
            'qubits': qubits,
            'gates': gates,
            'readout': self.readout.to_dict(),
            't1': self.t1_cal.to_dict(),
            't2': self.t2_cal.to_dict(),
            'average_gate_fidelity': self.average_gate_fidelity(),
            'average_readout_fidelity': self.average_readout_fidelity(),
            'healthy_qubits': len(self.get_healthy_qubits()),
        }

    def __repr__(self):
        return (f"HardwareCalibration({self.backend_name}, "
                f"qubits={self.num_qubits}, "
                f"gates={len(self.gates)})")
