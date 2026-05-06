"""
Task 16.1 — Quantum Sensor Simulator.

Simulation of quantum sensors, noise models, sensitivity estimation, sensor networks.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class SensorType(Enum):
    """Types of quantum sensors."""
    MAGNETOMETER = "magnetometer"
    GRAVIMETER = "gravimeter"
    ATOMIC_CLOCK = "atomic_clock"
    INTERFEROMETER = "interferometer"
    GYROSCOPE = "gyroscope"


@dataclass
class SensorReading:
    """Result of a quantum sensor measurement."""
    sensor_type: SensorType
    value: float
    uncertainty: float  # Standard deviation.
    snr: float  # Signal-to-noise ratio.
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sensor_type': self.sensor_type.value,
            'value': self.value,
            'uncertainty': self.uncertainty,
            'snr': self.snr,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class QuantumSensorSimulator:
    """Simulate quantum sensors (magnetometers, gravimeters, clocks, interferometers)."""
    
    def __init__(self, sensor_type: SensorType = SensorType.MAGNETOMETER):
        self.sensor_type = sensor_type
        self.noise_model: Optional[SensorNoiseModel] = None
        self.sensitivity: float = 1.0  # Base sensitivity.
    
    def set_noise_model(self, noise_model: 'SensorNoiseModel'):
        """Set the noise model for this sensor."""
        self.noise_model = noise_model
    
    def measure(self, signal: float, integration_time: float = 1.0) -> SensorReading:
        """
        Perform a measurement.
        
        Args:
            signal: True signal value to measure.
            integration_time: Measurement integration time (seconds).
            
        Returns:
            SensorReading with measured value and uncertainty.
        """
        # Base quantum projection noise.
        # SQL = 1/sqrt(N) for N measurements.
        N = integration_time * 1000  # Simplified: 1000 shots per second.
        sql_uncertainty = 1.0 / np.sqrt(max(N, 1))
        
        # Add technical noise if model specified.
        technical_noise = 0.0
        if self.noise_model:
            technical_noise = self.noise_model.sample_noise()
        
        # Total uncertainty (simplified quadrature sum).
        total_uncertainty = np.sqrt(sql_uncertainty**2 + technical_noise**2)
        
        # Measured value with noise.
        measured = signal + np.random.normal(0, total_uncertainty)
        
        # SNR.
        snr = abs(signal) / max(total_uncertainty, 1e-10)
        
        return SensorReading(
            sensor_type=self.sensor_type,
            value=measured,
            uncertainty=total_uncertainty,
            snr=snr,
            timestamp=np.datetime64('now').astype(float),  # Simplified timestamp.
            metadata={
                'integration_time': integration_time,
                'shots': N,
                'sql_uncertainty': sql_uncertainty,
                'technical_noise': technical_noise
            }
        )
    
    def estimate_sensitivity(self, num_trials: int = 100) -> float:
        """Estimate sensor sensitivity (minimum detectable signal)."""
        readings = []
        for _ in range(num_trials):
            reading = self.measure(signal=0.0, integration_time=1.0)
            readings.append(reading.value)
        
        # Sensitivity = standard deviation of zero-signal measurements.
        return float(np.std(readings))


class Magnetometer(QuantumSensorSimulator):
    """Quantum magnetometer simulation (e.g., NV centers, atomic magnetometers)."""
    
    def __init__(self, sensitivity_nT: float = 1.0):  # nT/sqrt(Hz).
        super().__init__(sensor_type=SensorType.MAGNETOMETER)
        self.base_sensitivity = sensitivity_nT
    
    def measure_field(self, B_field: float, integration_time: float = 1.0) -> SensorReading:
        """Measure magnetic field."""
        # Convert to sensor reading.
        return self.measure(signal=B_field, integration_time=integration_time)
    
    def estimate_cramér_rao_bound(self, B_field: float) -> float:
        """
        Cramér-Rao bound for magnetic field estimation.
        
        Lower bound on variance of any unbiased estimator.
        """
        # Simplified: CRB = 1 / (Fisher information).
        # For magnetometry with coherent spin states: FI ∝ N * T^2.
        N = 1000  # Number of atoms/spins.
        T = 1.0  # Coherence time.
        fisher_info = N * T**2
        crb = 1.0 / max(fisher_info, 1e-10)
        return crb


class Gravimeter(QuantumSensorSimulator):
    """Quantum gravimeter simulation (atom interferometry)."""
    
    def __init__(self, sensitivity_mg: float = 0.1):  # mg/sqrt(Hz).
        super().__init__(sensor_type=SensorType.GRAVIMETER)
        self.base_sensitivity = sensitivity_mg
    
    def measure_gravity(self, g: float = 9.80665, integration_time: float = 1.0) -> SensorReading:
        """Measure gravitational acceleration."""
        return self.measure(signal=g, integration_time=integration_time)
    
    def quantum_fisher_information(self, g: float) -> float:
        """Calculate quantum Fisher information for gravity estimation."""
        # Simplified: QFI ∝ T^2 / sigma^2.
        T = 1.0  # Interferometer time.
        sigma = self.base_sensitivity
        qfi = T**2 / max(sigma**2, 1e-10)
        return qfi


class AtomicClock(QuantumSensorSimulator):
    """Atomic clock simulation."""
    
    def __init__(self, stability: float = 1e-13):  # Allan deviation at 1 second.
        super().__init__(sensor_type=SensorType.ATOMIC_CLOCK)
        self.stability = stability  # Allan deviation τ^(-1/2).
    
    def measure_time(self, true_time: float, integration_time: float = 1.0) -> SensorReading:
        """Measure time/frequency."""
        return self.measure(signal=true_time, integration_time=integration_time)
    
    def allan_deviation(self, tau: float) -> float:
        """Calculate Allan deviation at time τ."""
        return self.stability * np.sqrt(tau)


class Interferometer(QuantumSensorSimulator):
    """Quantum interferometer (optical or matter-wave)."""
    
    def __init__(self, visibility: float = 0.9):
        super().__init__(sensor_type=SensorType.INTERFEROMETER)
        self.visibility = visibility  # Fringe visibility.
    
    def measure_phase(self, phase: float, integration_time: float = 1.0) -> SensorReading:
        """Measure optical phase."""
        # Signal with visibility.
        signal = self.visibility * np.cos(phase)
        return self.measure(signal=signal, integration_time=integration_time)
    
    def cramér_rao_for_phase(self, N: int) -> float:
        """Cramér-Rao bound for phase estimation."""
        # For coherent states: var(φ) ≥ 1/N.
        # For squeezed states: var(φ) ≥ 1/(N * squeezing_factor).
        return 1.0 / max(N, 1)


class SensorNoiseModel:
    """Noise model specific to sensing."""
    
    def __init__(self, decoherence_rate: float = 0.01,
                 technical_noise_std: float = 0.001):
        self.decoherence_rate = decoherence_rate
        self.technical_noise_std = technical_noise_std
        self.enviromental_noise_std = 0.0001
    
    def sample_noise(self) -> float:
        """Sample total noise."""
        decoherence = np.random.normal(0, self.decoherence_rate)
        technical = np.random.normal(0, self.technical_noise_std)
        environmental = np.random.normal(0, self.enviromental_noise_std)
        return decoherence + technical + environmental
    
    def set_environmental(self, noise_std: float):
        """Set environmental noise level."""
        self.enviromental_noise_std = noise_std


class SensitivityEstimator:
    """Estimate sensor sensitivity (Cramér-Rao bound, QFI)."""
    
    def __init__(self):
        self.crb_cache: Dict[str, float] = {}
    
    def cramér_rao_bound(self, sensor: QuantumSensorSimulator,
                          signal: float) -> float:
        """Calculate Cramér-Rao bound."""
        cache_key = f"{sensor.sensor_type.value}_{signal}"
        
        if cache_key in self.crb_cache:
            return self.crb_cache[cache_key]
        
        # Simplified CRB calculation.
        if hasattr(sensor, 'estimate_cramér_rao_bound'):
            crb = sensor.estimate_cramér_rao_bound(signal)
        else:
            # Default: CRB = variance of measurements.
            readings = [sensor.measure(signal, 1.0).value for _ in range(100)]
            crb = np.var(readings)
        
        self.crb_cache[cache_key] = crb
        return crb
    
    def quantum_fisher_information(self, sensor: QuantumSensorSimulator,
                                   parameter: float) -> float:
        """Calculate quantum Fisher information."""
        if hasattr(sensor, 'quantum_fisher_information'):
            return sensor.quantum_fisher_information(parameter)
        
        # Simplified: QFI = 1/CRB.
        crb = self.cramér_rao_bound(sensor, parameter)
        return 1.0 / max(crb, 1e-10)


class CramérRaoBound:
    """Calculate Cramér-Rao bounds for various sensing scenarios."""
    
    @staticmethod
    def for_coherent_state(N: int, T: float = 1.0) -> float:
        """CRB for coherent-state sensing."""
        return 1.0 / max(N * T**2, 1e-10)
    
    @staticmethod
    def for_squeezed_state(N: int, squeezing_db: float) -> float:
        """CRB for squeezed-state sensing."""
        squeezing_factor = 10**(-squeezing_db / 10.0)  # Convert dB to linear.
        return 1.0 / max(N * squeezing_factor, 1e-10)
    
    @staticmethod
    def for_entangled_state(N: int, entanglement_type: str = "ghz") -> float:
        """CRB for entangled-state sensing (Heisenberg limit)."""
        # Heisenberg limit: var ∝ 1/N^2.
        return 1.0 / max(N**2, 1)


class QuantumFisherInformation:
    """Calculate quantum Fisher information."""
    
    @staticmethod
    def for_parametric_family(psi_theta: np.ndarray, d_psi_d_theta: np.ndarray) -> float:
        """
        QFI for a parametric family |ψ(θ)⟩.
        
        QFI = 4 * (⟨∂ψ/∂θ|∂ψ/∂θ⟩ - |⟨ψ|∂ψ/∂θ⟩|^2).
        """
        # Simplified: assume pure states.
        inner = np.dot(d_psi_d_theta.conj(), d_psi_d_theta)
        qfi = 4 * np.real(inner)
        return max(qfi, 0.0)
    
    @staticmethod
    def for_phase_estimation(N: int, squeezing: float = 1.0) -> float:
        """QFI for phase estimation with N resources."""
        return N * squeezing


class SensorNetwork:
    """Simulate network of quantum sensors."""
    
    def __init__(self):
        self.sensors: List[QuantumSensorSimulator] = []
        self.positions: List[Tuple[float, float, float]] = []  # (x, y, z).
    
    def add_sensor(self, sensor: QuantumSensorSimulator,
                  position: Tuple[float, float, float]):
        """Add a sensor to the network."""
        self.sensors.append(sensor)
        self.positions.append(position)
    
    def distributed_measurement(self, signal_func: Callable,
                                integration_time: float = 1.0) -> List[SensorReading]:
        """Perform distributed measurement across network."""
        readings = []
        for sensor, pos in zip(self.sensors, self.positions):
            # Signal depends on position (e.g., field gradient).
            signal = signal_func(pos)
            reading = sensor.measure(signal, integration_time)
            readings.append(reading)
        return readings
    
    def network_sensitivity(self) -> float:
        """Calculate network sensitivity (improves with sqrt(N))."""
        if not self.sensors:
            return float('inf')
        
        # Average individual sensitivities.
        individual_sensitivities = [s.estimate_sensitivity() for s in self.sensors]
        avg_sensitivity = np.mean(individual_sensitivities)
        
        # Network improvement: √N for independent sensors.
        network_improvement = np.sqrt(len(self.sensors))
        return avg_sensitivity / network_improvement
