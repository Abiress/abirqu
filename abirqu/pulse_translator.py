"""
Automated Pulse-Level Translation.

Translates high-level quantum circuits into optimized analog pulse sequences
without requiring the user to understand hardware physics.

Features:
- Automatic pulse scheduling
- Cross-platform pulse translation (superconducting, trapped-ion, neutral-atom)
- DRAG pulse optimization
- Crosstalk-aware pulse allocation
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .circuit import Circuit, Gate


@dataclass
class Pulse:
    """A single analog pulse."""
    channel: str
    qubit: int
    duration_ns: float
    amplitude: float
    frequency_ghz: float
    phase_rad: float = 0.0
    shape: str = "gaussian"
    drag_coefficient: float = 0.0
    t_start_ns: float = 0.0


@dataclass
class PulseSchedule:
    """Complete pulse schedule for a circuit."""
    pulses: List[Pulse] = field(default_factory=list)
    measurement_time_ns: float = 1000.0
    total_time_ns: float = 0.0
    num_qubits: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class HardwareProfile:
    """Hardware-specific pulse parameters."""

    def __init__(self, platform: str = "superconducting"):
        self.platform = platform
        self._profiles = {
            "superconducting": {
                "t1_us": 100.0,
                "t2_us": 80.0,
                "gate_time_1q_ns": 20.0,
                "gate_time_2q_ns": 300.0,
                "readout_time_ns": 1000.0,
                "max_amplitude": 0.9,
                "frequency_ghz": 5.0,
                "anharmonicity_ghz": -0.3,
                "drag_coefficient": 0.2,
                "crosstalk_matrix": None,
            },
            "trapped_ion": {
                "t1_us": 10000.0,
                "t2_us": 3000.0,
                "gate_time_1q_ns": 100.0,
                "gate_time_2q_ns": 10000.0,
                "readout_time_ns": 100000.0,
                "max_amplitude": 0.8,
                "frequency_ghz": 0.1,
                "anharmonicity_ghz": 0.0,
                "drag_coefficient": 0.0,
                "crosstalk_matrix": None,
            },
            "neutral_atom": {
                "t1_us": 1000.0,
                "t2_us": 500.0,
                "gate_time_1q_ns": 50.0,
                "gate_time_2q_ns": 500.0,
                "readout_time_ns": 5000.0,
                "max_amplitude": 1.0,
                "frequency_ghz": 0.3,
                "anharmonicity_ghz": 0.0,
                "drag_coefficient": 0.0,
                "crosstalk_matrix": None,
            },
        }
        self.params = self._profiles.get(platform, self._profiles["superconducting"])

    def get(self, key: str, default=None):
        return self.params.get(key, default)


class PulseTranslator:
    """Translate quantum gates to analog pulses."""

    def __init__(self, hardware_profile: Optional[HardwareProfile] = None):
        self.hw = hardware_profile or HardwareProfile()

    def translate_gate(self, gate: Gate, t_start: float = 0.0) -> List[Pulse]:
        """Translate a single gate to pulses."""
        name = gate.name.upper()
        qubits = gate.qubits if isinstance(gate.qubits, list) else [gate.qubits]
        params = gate.params or []

        if name in ("RX", "RY", "RZ"):
            return self._rotation_pulse(name, qubits[0], params[0] if params else 0, t_start)
        elif name == "H":
            return self._hadamard_pulse(qubits[0], t_start)
        elif name == "CNOT":
            return self._cnot_pulse(qubits[0], qubits[1], t_start)
        elif name in ("X", "Y", "Z"):
            return self._pauli_pulse(name, qubits[0], t_start)
        elif name == "S":
            return self._s_pulse(qubits[0], t_start)
        elif name == "T":
            return self._t_pulse(qubits[0], t_start)
        else:
            return self._generic_pulse(name, qubits, params, t_start)

    def _rotation_pulse(self, axis: str, qubit: int, angle: float, t_start: float) -> List[Pulse]:
        """Generate rotation pulse."""
        freq = self.hw.get("frequency_ghz", 5.0)
        duration = self.hw.get("gate_time_1q_ns", 20.0)
        max_amp = self.hw.get("max_amplitude", 0.9)
        drag = self.hw.get("drag_coefficient", 0.0)

        # Map axis to phase
        phase_map = {"RX": 0, "RY": np.pi / 2, "RZ": np.pi}
        phase = phase_map.get(axis, 0)

        amplitude = max_amp * abs(angle) / np.pi

        return [Pulse(
            channel=f"drive_{qubit}",
            qubit=qubit,
            duration_ns=duration * abs(angle) / np.pi,
            amplitude=min(amplitude, max_amp),
            frequency_ghz=freq,
            phase_rad=phase,
            shape="gaussian",
            drag_coefficient=drag,
            t_start_ns=t_start,
        )]

    def _hadamard_pulse(self, qubit: int, t_start: float) -> List[Pulse]:
        """Hadamard = RY(π/2) followed by RZ(π)."""
        pulses = []
        pulses.extend(self._rotation_pulse("RY", qubit, np.pi / 2, t_start))
        dur1 = self.hw.get("gate_time_1q_ns", 20.0) * 0.5
        pulses.extend(self._rotation_pulse("RZ", qubit, np.pi, t_start + dur1))
        return pulses

    def _cnot_pulse(self, control: int, target: int, t_start: float) -> List[Pulse]:
        """CNOT = cross-resonance gate for superconducting, or Mølmer-Sørensen for ions."""
        freq = self.hw.get("frequency_ghz", 5.0)
        duration = self.hw.get("gate_time_2q_ns", 300.0)
        max_amp = self.hw.get("max_amplitude", 0.9)

        if self.hw.platform == "trapped_ion":
            # Mølmer-Sørensen gate
            return [
                Pulse(channel=f"MS_{control}_{target}", qubit=control,
                      duration_ns=duration, amplitude=max_amp * 0.8,
                      frequency_ghz=0.1, phase_rad=0,
                      shape="rectangular", t_start_ns=t_start),
                Pulse(channel=f"MS_{control}_{target}", qubit=target,
                      duration_ns=duration, amplitude=max_amp * 0.8,
                      frequency_ghz=0.1, phase_rad=0,
                      shape="rectangular", t_start_ns=t_start),
            ]
        else:
            # Cross-resonance gate for superconducting
            return [
                Pulse(channel=f"cr_{control}_{target}", qubit=control,
                      duration_ns=duration, amplitude=max_amp * 0.7,
                      frequency_ghz=freq, phase_rad=0,
                      shape="gaussian", t_start_ns=t_start),
                Pulse(channel=f"zx_{control}_{target}", qubit=target,
                      duration_ns=duration, amplitude=max_amp * 0.5,
                      frequency_ghz=freq, phase_rad=np.pi / 2,
                      shape="gaussian", t_start_ns=t_start),
            ]

    def _pauli_pulse(self, gate: str, qubit: int, t_start: float) -> List[Pulse]:
        """Pauli gate as virtual Z (frame change) + physical rotation if needed."""
        if gate == "Z":
            # Virtual Z gate - no actual pulse, just frame change
            return [Pulse(
                channel=f"frame_{qubit}", qubit=qubit,
                duration_ns=0, amplitude=0,
                frequency_ghz=0, phase_rad=np.pi,
                shape="virtual", t_start_ns=t_start,
            )]
        elif gate == "X":
            return self._rotation_pulse("RX", qubit, np.pi, t_start)
        elif gate == "Y":
            return self._rotation_pulse("RY", qubit, np.pi, t_start)
        return []

    def _s_pulse(self, qubit: int, t_start: float) -> List[Pulse]:
        """S gate = virtual Z(π/2)."""
        return [Pulse(
            channel=f"frame_{qubit}", qubit=qubit,
            duration_ns=0, amplitude=0,
            frequency_ghz=0, phase_rad=np.pi / 2,
            shape="virtual", t_start_ns=t_start,
        )]

    def _t_pulse(self, qubit: int, t_start: float) -> List[Pulse]:
        """T gate = virtual Z(π/4)."""
        return [Pulse(
            channel=f"frame_{qubit}", qubit=qubit,
            duration_ns=0, amplitude=0,
            frequency_ghz=0, phase_rad=np.pi / 4,
            shape="virtual", t_start_ns=t_start,
        )]

    def _generic_pulse(self, name: str, qubits: List[int], params: List[float],
                        t_start: float) -> List[Pulse]:
        """Generic fallback for unknown gates."""
        return [Pulse(
            channel=f"generic_{name}_{qubits[0]}", qubit=qubits[0],
            duration_ns=self.hw.get("gate_time_1q_ns", 20.0),
            amplitude=0.5,
            frequency_ghz=self.hw.get("frequency_ghz", 5.0),
            shape="gaussian", t_start_ns=t_start,
        )]


class PulseScheduler:
    """Schedule pulses with crosstalk awareness and parallelism."""

    def __init__(self, hardware_profile: Optional[HardwareProfile] = None):
        self.hw = hardware_profile or HardwareProfile()
        self.crosstalk = self.hw.get("crosstalk_matrix")

    def schedule(self, circuit: Circuit) -> PulseSchedule:
        """Schedule all gates in a circuit into a pulse schedule."""
        translator = PulseTranslator(self.hw)
        schedule = PulseSchedule(num_qubits=circuit.num_qubits)

        current_time = 0.0
        qubit_end_times = [0.0] * circuit.num_qubits

        for gate in circuit.gates:
            qubits = gate.qubits if isinstance(gate.qubits, list) else [gate.qubits]

            # Find earliest time all qubits are free
            earliest = max(qubit_end_times[q] for q in qubits if q < len(qubit_end_times))

            # Generate pulses
            pulses = translator.translate_gate(gate, t_start=earliest)

            # Update qubit end times
            gate_duration = max(p.duration_ns for p in pulses) if pulses else 0
            for q in qubits:
                if q < len(qubit_end_times):
                    qubit_end_times[q] = earliest + gate_duration

            schedule.pulses.extend(pulses)

        schedule.total_time_ns = max(qubit_end_times) if qubit_end_times else 0
        schedule.measurement_time_ns = self.hw.get("readout_time_ns", 1000.0)

        return schedule

    def optimize_parallelism(self, schedule: PulseSchedule) -> PulseSchedule:
        """Optimize pulse scheduling for maximum parallelism."""
        if not schedule.pulses:
            return schedule

        # Sort pulses by qubit and time
        sorted_pulses = sorted(schedule.pulses, key=lambda p: (p.qubit, p.t_start_ns))

        # Merge overlapping pulses on same channel
        merged = []
        current = None
        for p in sorted_pulses:
            if current and current.channel == p.channel and current.t_start_ns + current.duration_ns >= p.t_start_ns:
                # Merge overlapping pulses
                end = max(current.t_start_ns + current.duration_ns, p.t_start_ns + p.duration_ns)
                current = Pulse(
                    channel=current.channel, qubit=current.qubit,
                    duration_ns=end - current.t_start_ns,
                    amplitude=max(current.amplitude, p.amplitude),
                    frequency_ghz=current.frequency_ghz,
                    phase_rad=current.phase_rad,
                    shape=current.shape,
                    t_start_ns=current.t_start_ns,
                )
            else:
                if current:
                    merged.append(current)
                current = p
        if current:
            merged.append(current)

        schedule.pulses = merged
        return schedule


class PulseOptimizer:
    """Optimize pulse shapes for reduced error and crosstalk."""

    def __init__(self, hardware_profile: Optional[HardwareProfile] = None):
        self.hw = hardware_profile or HardwareProfile()
        self.crosstalk = self.hw.get("crosstalk_matrix")

    def optimize_drag(self, pulses: List[Pulse]) -> List[Pulse]:
        """Optimize DRAG pulses to reduce leakage."""
        optimized = []
        anharmonicity = self.hw.get("anharmonicity_ghz", -0.3)

        for p in pulses:
            if p.shape == "gaussian" and anharmonicity != 0:
                # DRAG coefficient from Motzoi et al.
                drag_coeff = p.amplitude / (2 * anharmonicity * p.duration_ns * 1e-9)
                p.drag_coefficient = drag_coeff
            optimized.append(p)
        return optimized

    def minimize_crosstalk(self, pulses: List[Pulse]) -> List[Pulse]:
        """Minimize crosstalk by staggering concurrent pulses."""
        if not self.crosstalk:
            return pulses

        # Simple staggering: offset concurrent pulses on adjacent qubits
        qubit_times: Dict[int, float] = {}
        optimized = []

        for p in sorted(pulses, key=lambda x: x.t_start_ns):
            if p.shape == "virtual":
                optimized.append(p)
                continue

            # Check for crosstalk with active pulses
            offset = 0.0
            for active_q, active_time in qubit_times.items():
                if active_q != p.qubit and abs(active_q - p.qubit) == 1:
                    if p.t_start_ns < active_time:
                        offset = max(offset, active_time - p.t_start_ns + 5.0)

            p.t_start_ns += offset
            qubit_times[p.qubit] = p.t_start_ns + p.duration_ns
            optimized.append(p)

        return optimized


class AutomatedPulseEngine:
    """
    Automated pulse-level translation engine.

    Translates high-level circuits to optimized pulse schedules
    with no manual hardware configuration.
    """

    def __init__(self, platform: str = "superconducting"):
        self.hw = HardwareProfile(platform)
        self.translator = PulseTranslator(self.hw)
        self.scheduler = PulseScheduler(self.hw)
        self.optimizer = PulseOptimizer(self.hw)

    def translate(self, circuit: Circuit, optimize: bool = True) -> PulseSchedule:
        """
        Translate a circuit to an optimized pulse schedule.

        Parameters
        ----------
        circuit : Circuit
            High-level quantum circuit.
        optimize : bool
            Apply pulse optimization (DRAG, crosstalk minimization).

        Returns
        -------
        PulseSchedule with optimized pulses.
        """
        schedule = self.scheduler.schedule(circuit)

        if optimize:
            schedule.pulses = self.optimizer.optimize_drag(schedule.pulses)
            schedule.pulses = self.optimizer.minimize_crosstalk(schedule.pulses)
            schedule = self.scheduler.optimize_parallelism(schedule)

        schedule.metadata = {
            "platform": self.hw.platform,
            "num_pulses": len(schedule.pulses),
            "total_time_ns": schedule.total_time_ns,
            "optimization_applied": optimize,
        }

        return schedule

    def translate_to_waveforms(self, schedule: PulseSchedule) -> Dict[str, np.ndarray]:
        """Convert pulse schedule to hardware-specific waveforms."""
        waveforms = {}
        sample_rate_ghz = 1.0  # 1 GS/s

        for i, p in enumerate(schedule.pulses):
            if p.shape == "virtual":
                continue

            num_samples = int(p.duration_ns * sample_rate_ghz)
            if num_samples < 1:
                continue

            t = np.linspace(0, p.duration_ns, num_samples)

            if p.shape == "gaussian":
                sigma = p.duration_ns / 6
                envelope = p.amplitude * np.exp(-0.5 * ((t - p.duration_ns / 2) / sigma) ** 2)
                if p.drag_coefficient != 0:
                    drag = -p.drag_coefficient * (t - p.duration_ns / 2) / sigma ** 2 * envelope
                    waveforms[f"iq_{p.channel}_{i}"] = envelope + 1j * drag
                else:
                    waveforms[f"iq_{p.channel}_{i}"] = envelope * np.exp(1j * p.phase_rad)
            elif p.shape == "rectangular":
                waveforms[f"iq_{p.channel}_{i}"] = p.amplitude * np.ones(num_samples) * np.exp(1j * p.phase_rad)

        return waveforms

    def get_info(self) -> Dict[str, Any]:
        """Get hardware profile information."""
        return {
            "platform": self.hw.platform,
            "gate_time_1q_ns": self.hw.get("gate_time_1q_ns"),
            "gate_time_2q_ns": self.hw.get("gate_time_2q_ns"),
            "t1_us": self.hw.get("t1_us"),
            "t2_us": self.hw.get("t2_us"),
            "max_amplitude": self.hw.get("max_amplitude"),
        }


__all__ = [
    "AutomatedPulseEngine",
    "PulseTranslator",
    "PulseScheduler",
    "PulseOptimizer",
    "HardwareProfile",
    "Pulse",
    "PulseSchedule",
]
