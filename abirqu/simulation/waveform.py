"""
Waveform Enveloping Module.

Generates time-domain pulse waveforms for quantum control. These waveforms
map directly to analog instructions sent to physical control electronics
(arbitrary waveform generators, DACs).

Supports:
    - Gaussian pulses (with optional DRAG correction)
    - Square/rectangular pulses
    - Cosine/Sine shaped pulses
    - Kaiser window pulses
    - Arbitrary user-defined shapes via callable
    - Pulse stacking and concatenation
    - Modulation (carrier frequency + IQ mixing)

Each waveform is a discrete array of samples that can be directly
output to an AWG (Arbitrary Waveform Generator) or DAC.

References:
    - Motzoi et al. (2009): "Simple Pulses for Elimination of Leakage in
      Weakly Nonlinear Qubits"
    - Reed (2013): "Entangling Microwaves and Photons..."
"""

import math
from typing import Callable, Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class WaveformType(Enum):
    """Supported waveform types."""
    GAUSSIAN = "gaussian"
    SQUARE = "square"
    COSINE = "cosine"
    SINE = "sine"
    KAISER = "kaiser"
    DERIVATIVE_GAUSSIAN = "derivative_gaussian"
    ARBITRARY = "arbitrary"


@dataclass
class WaveformSample:
    """
    A discrete sample of a waveform.

    Attributes
    ----------
    time : float
        Sample time in nanoseconds
    i_value : float
        In-phase component (amplitude)
    q_value : float
        Quadrature component (for DRAG/cross-talk)
    """
    time: float
    i_value: float
    q_value: float = 0.0


@dataclass
class WaveformEnvelope:
    """
    Complete waveform envelope for a single pulse.

    Attributes
    ----------
    name : str
        Pulse identifier
    channel : str
        Hardware channel (e.g., 'drive', 'flux', 'cr')
    qubit : int
        Target qubit index
    duration_ns : float
        Pulse duration in nanoseconds
    samples_i : np.ndarray
        In-phase samples (I component)
    samples_q : np.ndarray
        Quadrature samples (Q component)
    sample_rate_ghz : float
        Sample rate in GHz (default 1 GS/s = 1 GHz)
    center_freq_ghz : float
        Center/carrier frequency in GHz
    phase_rad : float
        Phase offset in radians
    """
    name: str
    channel: str
    qubit: int
    duration_ns: float
    samples_i: np.ndarray
    samples_q: np.ndarray
    sample_rate_ghz: float = 1.0
    center_freq_ghz: float = 5.0
    phase_rad: float = 0.0

    @property
    def num_samples(self) -> int:
        return len(self.samples_i)

    @property
    def time_array(self) -> np.ndarray:
        """Time axis in nanoseconds."""
        return np.linspace(0, self.duration_ns, self.num_samples)

    def to_iq_pairs(self) -> List[Tuple[float, float]]:
        """Return list of (I, Q) sample pairs."""
        return list(zip(self.samples_i.tolist(), self.samples_q.tolist()))

    def to_voltage(self, v_scale: float = 1.0) -> np.ndarray:
        """Convert to voltage samples: V = sqrt(I^2 + Q^2) * scale."""
        return np.sqrt(self.samples_i ** 2 + self.samples_q ** 2) * v_scale

    def energy(self) -> float:
        """Compute pulse energy: ∫ (I² + Q²) dt."""
        dt = self.duration_ns / self.num_samples / 1e3  # convert ns to μs for energy units
        return float(np.sum(self.samples_i ** 2 + self.samples_q ** 2) * dt)


class WaveformGenerator:
    """
    Generate pulse waveforms for quantum control.

    Parameters
    ----------
    sample_rate_ghz : float
        Sample rate in GHz (1.0 = 1 GS/s)
    """

    def __init__(self, sample_rate_ghz: float = 1.0):
        self.sample_rate_ghz = sample_rate_ghz

    def _num_samples(self, duration_ns: float) -> int:
        """Compute number of samples for given duration."""
        return max(int(duration_ns * self.sample_rate_ghz), 1)

    def gaussian(self, duration_ns: float, amplitude: float = 1.0,
                 sigma_ratio: float = 0.25, drag: float = 0.0,
                 channel: str = "drive", qubit: int = 0,
                 center_freq_ghz: float = 5.0, phase_rad: float = 0.0,
                 name: str = "gaussian") -> WaveformEnvelope:
        """
        Generate a Gaussian pulse envelope.

        Parameters
        ----------
        duration_ns : float
            Pulse duration in nanoseconds
        amplitude : float
            Peak amplitude (0 to 1)
        sigma_ratio : float
            Standard deviation as fraction of duration (e.g., 0.25 = quarter-width)
        drag : float
            DRAG coefficient. 0 = no DRAG. Typical: 0.2-0.5.
            DRAG adds a derivative component to suppress leakage to |2> state.
        channel : str
            Hardware channel name
        qubit : int
            Target qubit
        center_freq_ghz : float
            Carrier frequency in GHz
        phase_rad : float
            Phase offset
        name : str
            Pulse name

        Returns
        -------
        WaveformEnvelope
        """
        n = self._num_samples(duration_ns)
        t = np.linspace(-duration_ns / 2, duration_ns / 2, n)
        sigma = sigma_ratio * duration_ns

        # Gaussian envelope
        env = amplitude * np.exp(-0.5 * (t / sigma) ** 2)

        # DRAG correction: Q = -drag * dI/dt
        if drag != 0.0:
            deriv = -t / (sigma ** 2) * env
            samples_q = drag * deriv
        else:
            samples_q = np.zeros(n)

        return WaveformEnvelope(
            name=name, channel=channel, qubit=qubit,
            duration_ns=duration_ns,
            samples_i=env, samples_q=samples_q,
            sample_rate_ghz=self.sample_rate_ghz,
            center_freq_ghz=center_freq_ghz, phase_rad=phase_rad,
        )

    def square(self, duration_ns: float, amplitude: float = 1.0,
               rise_time_ns: float = 0.0,
               channel: str = "drive", qubit: int = 0,
               center_freq_ghz: float = 5.0, phase_rad: float = 0.0,
               name: str = "square") -> WaveformEnvelope:
        """
        Generate a square (rectangular) pulse envelope.

        Parameters
        ----------
        duration_ns : float
            Pulse duration
        amplitude : float
            Pulse amplitude
        rise_time_ns : float
            Rise/fall time for smooth edges (0 = hard edges)
        """
        n = self._num_samples(duration_ns)
        env = amplitude * np.ones(n)

        # Apply raised-cosine edges if rise_time > 0
        if rise_time_ns > 0:
            n_rise = int(rise_time_ns * self.sample_rate_ghz)
            n_rise = min(n_rise, n // 4)
            for i in range(n_rise):
                edge = 0.5 * (1 - math.cos(math.pi * i / n_rise))
                env[i] *= edge
                env[n - 1 - i] *= edge

        return WaveformEnvelope(
            name=name, channel=channel, qubit=qubit,
            duration_ns=duration_ns,
            samples_i=env, samples_q=np.zeros(n),
            sample_rate_ghz=self.sample_rate_ghz,
            center_freq_ghz=center_freq_ghz, phase_rad=phase_rad,
        )

    def cosine(self, duration_ns: float, amplitude: float = 1.0,
               num_cycles: float = 1.0,
               channel: str = "drive", qubit: int = 0,
               center_freq_ghz: float = 5.0, phase_rad: float = 0.0,
               name: str = "cosine") -> WaveformEnvelope:
        """
        Generate a cosine-shaped envelope (for DRAG-like pulses).

        Parameters
        ----------
        num_cycles : float
            Number of cosine half-cycles within the pulse
        """
        n = self._num_samples(duration_ns)
        t = np.linspace(0, duration_ns, n)
        env = amplitude * 0.5 * (1 + np.cos(2 * math.pi * num_cycles * t / duration_ns))

        return WaveformEnvelope(
            name=name, channel=channel, qubit=qubit,
            duration_ns=duration_ns,
            samples_i=env, samples_q=np.zeros(n),
            sample_rate_ghz=self.sample_rate_ghz,
            center_freq_ghz=center_freq_ghz, phase_rad=phase_rad,
        )

    def kaiser(self, duration_ns: float, amplitude: float = 1.0,
               beta: float = 5.0,
               channel: str = "drive", qubit: int = 0,
               center_freq_ghz: float = 5.0, phase_rad: float = 0.0,
               name: str = "kaiser") -> WaveformEnvelope:
        """
        Generate a Kaiser window pulse.

        Parameters
        ----------
        beta : float
            Kaiser beta parameter (higher = narrower main lobe)
        """
        n = self._num_samples(duration_ns)
        env = amplitude * np.kaiser(n, beta)

        return WaveformEnvelope(
            name=name, channel=channel, qubit=qubit,
            duration_ns=duration_ns,
            samples_i=env, samples_q=np.zeros(n),
            sample_rate_ghz=self.sample_rate_ghz,
            center_freq_ghz=center_freq_ghz, phase_rad=phase_rad,
        )

    def derivative_gaussian(self, duration_ns: float, amplitude: float = 1.0,
                            sigma_ratio: float = 0.25,
                            channel: str = "drive", qubit: int = 0,
                            center_freq_ghz: float = 5.0, phase_rad: float = 0.0,
                            name: str = "dg") -> WaveformEnvelope:
        """
        Generate a derivative-of-Gaussian pulse.

        This is the natural DRAG pulse shape without the Gaussian carrier.
        """
        n = self._num_samples(duration_ns)
        t = np.linspace(-duration_ns / 2, duration_ns / 2, n)
        sigma = sigma_ratio * duration_ns
        env = amplitude * (-t / (sigma ** 2)) * np.exp(-0.5 * (t / sigma) ** 2)

        return WaveformEnvelope(
            name=name, channel=channel, qubit=qubit,
            duration_ns=duration_ns,
            samples_i=env, samples_q=np.zeros(n),
            sample_rate_ghz=self.sample_rate_ghz,
            center_freq_ghz=center_freq_ghz, phase_rad=phase_rad,
        )

    def arbitrary(self, duration_ns: float, func: Callable[[float], float],
                  amplitude: float = 1.0,
                  channel: str = "drive", qubit: int = 0,
                  center_freq_ghz: float = 5.0, phase_rad: float = 0.0,
                  name: str = "arbitrary") -> WaveformEnvelope:
        """
        Generate a pulse from an arbitrary user-defined function.

        Parameters
        ----------
        func : callable
            Function f(t) -> amplitude, where t is in [0, duration_ns]
        """
        n = self._num_samples(duration_ns)
        t = np.linspace(0, duration_ns, n)
        env = amplitude * np.array([func(ti) for ti in t])

        return WaveformEnvelope(
            name=name, channel=channel, qubit=qubit,
            duration_ns=duration_ns,
            samples_i=env, samples_q=np.zeros(n),
            sample_rate_ghz=self.sample_rate_ghz,
            center_freq_ghz=center_freq_ghz, phase_rad=phase_rad,
        )


class WaveformModulator:
    """
    Modulate waveforms onto carrier frequencies for IQ mixing.

    Converts baseband I/Q envelopes to modulated signals:
        V(t) = I(t) * cos(2π f_c t) - Q(t) * sin(2π f_c t)
    """

    @staticmethod
    def modulate(envelope: WaveformEnvelope,
                 carrier_freq_ghz: Optional[float] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Modulate envelope onto carrier frequency.

        Returns
        -------
        modulated_i, modulated_q : np.ndarray
            Modulated I and Q signals
        """
        f_c = carrier_freq_ghz or envelope.center_freq_ghz
        n = envelope.num_samples
        t = envelope.time_array * 1e-3  # convert ns to μs for GHz frequency

        carrier_i = np.cos(2 * np.pi * f_c * t + envelope.phase_rad)
        carrier_q = np.sin(2 * np.pi * f_c * t + envelope.phase_rad)

        mod_i = envelope.samples_i * carrier_i - envelope.samples_q * carrier_q
        mod_q = envelope.samples_i * carrier_q + envelope.samples_q * carrier_i

        return mod_i, mod_q

    @staticmethod
    def demodulate(signal_i: np.ndarray, signal_q: np.ndarray,
                   carrier_freq_ghz: float, duration_ns: float,
                   sample_rate_ghz: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Demodulate a modulated signal back to baseband I/Q.
        """
        n = len(signal_i)
        t = np.linspace(0, duration_ns, n) * 1e-3

        carrier_i = np.cos(2 * np.pi * carrier_freq_ghz * t)
        carrier_q = np.sin(2 * np.pi * carrier_freq_ghz * t)

        baseband_i = signal_i * carrier_i + signal_q * carrier_q
        baseband_q = -signal_i * carrier_q + signal_q * carrier_i

        return baseband_i, baseband_q


class WaveformComposer:
    """
    Compose multiple waveform envelopes into a single pulse sequence.

    Handles:
    - Concatenation (sequential)
    - Parallel execution (same time, different channels)
    - Pulse stacking (overlap and sum)
    """

    @staticmethod
    def concatenate(envelopes: List[WaveformEnvelope]) -> WaveformEnvelope:
        """
        Concatenate waveforms sequentially in time.

        Parameters
        ----------
        envelopes : list of WaveformEnvelope
            Waveforms to join end-to-end

        Returns
        -------
        WaveformEnvelope
            Single concatenated waveform
        """
        if not envelopes:
            raise ValueError("No envelopes to concatenate")

        total_duration = sum(e.duration_ns for e in envelopes)
        all_i = np.concatenate([e.samples_i for e in envelopes])
        all_q = np.concatenate([e.samples_q for e in envelopes])

        return WaveformEnvelope(
            name="concatenated",
            channel=envelopes[0].channel,
            qubit=envelopes[0].qubit,
            duration_ns=total_duration,
            samples_i=all_i, samples_q=all_q,
            sample_rate_ghz=envelopes[0].sample_rate_ghz,
            center_freq_ghz=envelopes[0].center_freq_ghz,
        )

    @staticmethod
    def parallel(envelopes: List[WaveformEnvelope]) -> Dict[str, WaveformEnvelope]:
        """
        Return waveforms for parallel execution on different channels.

        All waveforms start at the same time.
        """
        return {e.channel: e for e in envelopes}

    @staticmethod
    def stack(envelopes: List[WaveformEnvelope],
              overlap_ns: float = 0.0) -> WaveformEnvelope:
        """
        Stack (overlap and sum) waveforms on the same channel.

        Parameters
        ----------
        overlap_ns : float
            How much to overlap consecutive waveforms (negative = gap)
        """
        if not envelopes:
            raise ValueError("No envelopes to stack")

        sample_rate = envelopes[0].sample_rate_ghz
        total_duration = sum(e.duration_ns for e in envelopes) - overlap_ns * (len(envelopes) - 1)
        n_total = int(total_duration * sample_rate)

        all_i = np.zeros(n_total)
        all_q = np.zeros(n_total)

        offset = 0
        for env in envelopes:
            n_env = len(env.samples_i)
            end = min(offset + n_env, n_total)
            length = end - offset
            all_i[offset:end] += env.samples_i[:length]
            all_q[offset:end] += env.samples_q[:length]
            offset += n_env - int(overlap_ns * sample_rate)

        return WaveformEnvelope(
            name="stacked",
            channel=envelopes[0].channel,
            qubit=envelopes[0].qubit,
            duration_ns=total_duration,
            samples_i=all_i, samples_q=all_q,
            sample_rate_ghz=sample_rate,
            center_freq_ghz=envelopes[0].center_freq_ghz,
        )


class PulseShapeLibrary:
    """
    Pre-built pulse shapes for common quantum gates.

    Usage:
        lib = PulseShapeLibrary(sample_rate_ghz=1.0)
        pi_pulse = lib.pi_pulse(qubit=0)
        sqrt_x = lib.sqrt_x(qubit=1)
    """

    def __init__(self, sample_rate_ghz: float = 1.0,
                 pi_pulse_duration_ns: float = 20.0,
                 drag_coefficient: float = 0.2):
        self.gen = WaveformGenerator(sample_rate_ghz)
        self.pi_duration = pi_pulse_duration_ns
        self.drag = drag_coefficient

    def pi_pulse(self, qubit: int, channel: str = "drive",
                 shape: str = "gaussian") -> WaveformEnvelope:
        """π pulse (X gate) — rotates by π around X axis."""
        if shape == "gaussian":
            return self.gen.gaussian(
                self.pi_duration, amplitude=1.0, drag=self.drag,
                channel=channel, qubit=qubit, name="pi_x"
            )
        elif shape == "square":
            return self.gen.square(
                self.pi_duration, amplitude=1.0,
                channel=channel, qubit=qubit, name="pi_x"
            )
        else:
            return self.gen.gaussian(
                self.pi_duration, amplitude=1.0,
                channel=channel, qubit=qubit, name="pi_x"
            )

    def half_pi_pulse(self, qubit: int, channel: str = "drive") -> WaveformEnvelope:
        """π/2 pulse — rotates by π/2 around X axis."""
        return self.gen.gaussian(
            self.pi_duration, amplitude=0.5, drag=self.drag,
            channel=channel, qubit=qubit, name="half_pi_x"
        )

    def sqrt_x(self, qubit: int) -> WaveformEnvelope:
        """√X pulse — S-X-S† decomposition as amplitude-scaled π pulse."""
        return self.gen.gaussian(
            self.pi_duration, amplitude=0.5, drag=self.drag,
            channel="drive", qubit=qubit, name="sqrt_x"
        )

    def sqrt_y(self, qubit: int) -> WaveformEnvelope:
        """√Y pulse."""
        return self.gen.gaussian(
            self.pi_duration, amplitude=0.5, drag=self.drag,
            channel="drive", qubit=qubit, name="sqrt_y",
            phase_rad=math.pi / 2,
        )

    def cz_pulse(self, qubit_i: int, qubit_j: int,
                 duration_ns: float = 40.0) -> Dict[str, WaveformEnvelope]:
        """CZ pulse — flux-mediated conditional phase."""
        return {
            "flux": self.gen.square(
                duration_ns, amplitude=0.8,
                channel="flux", qubit=qubit_i, name="cz_flux"
            ),
            "drive_i": self.gen.gaussian(
                duration_ns, amplitude=0.0, channel="drive",
                qubit=qubit_i, name="cz_drive_i"
            ),
            "drive_j": self.gen.gaussian(
                duration_ns, amplitude=0.0, channel="drive",
                qubit=qubit_j, name="cz_drive_j"
            ),
        }

    def cnot_cross_resonance(self, control: int, target: int,
                              duration_ns: float = 30.0) -> Dict[str, WaveformEnvelope]:
        """CNOT via cross-resonance (CR) interaction."""
        return {
            "cr": self.gen.gaussian(
                duration_ns, amplitude=0.3,
                channel="cr", qubit=control, name="cnot_cr"
            ),
            "zx": self.gen.gaussian(
                duration_ns, amplitude=0.1,
                channel="drive", qubit=target, name="cnot_zx_correction"
            ),
        }

    def idle(self, qubit: int, duration_ns: float) -> WaveformEnvelope:
        """Zero-amplitude idle pulse (for timing alignment)."""
        return self.gen.square(
            duration_ns, amplitude=0.0,
            channel="drive", qubit=qubit, name="idle"
        )
