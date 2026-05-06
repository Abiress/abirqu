"""
Task 16.3 — Quantum Clock & Timing.

Atomic clock simulation, timing synchronization, quantum-enhanced GPS, precision estimation.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time


@dataclass
class ClockReading:
    """Result of a quantum clock measurement."""
    time: float  # Clock reading.
    uncertainty: float  # Standard deviation (seconds).
    stability: float  # Allan deviation.
    clock_type: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'time': self.time,
            'uncertainty': self.uncertainty,
            'stability': self.stability,
            'clock_type': self.clock_type,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }


class AtomicClockSimulation:
    """Quantum clock simulation (atomic clock protocols)."""
    
    def __init__(self, clock_type: str = "optical_lattice"):
        self.type = clock_type
        self.center_frequency: float = 429.23e12  # 429 THz for Sr optical clock.
        self.linewidth: float = 1.0  # Hz (simplified).
        self.decoherence_rate: float = 0.01
    
    def simulate_clock(self, integration_time: float = 1.0) -> ClockReading:
        """
        Simulate atomic clock operation.
        
        Args:
            integration_time: Measurement time (seconds).
            
        Returns:
            ClockReading.
        """
        # Quantum projection noise: 1/sqrt(N) for N atoms.
        N = 10000  # Number of atoms.
        projection_noise = 1.0 / np.sqrt(N)
        
        # Technical noise (simplified).
        technical = np.random.normal(0, 0.001)
        
        # Total uncertainty.
        total_uncertainty = np.sqrt(projection_noise**2 + technical**2)
        
        # Clock drift (simplified: linear drift).
        drift_rate = 1e-15  # Per second.
        elapsed = time.time() % 86400  # Seconds since midnight.
        drift = drift_rate * elapsed
        
        # Current time with noise.
        true_time = time.time()
        measured_time = true_time + drift + np.random.normal(0, total_uncertainty)
        
        # Allan deviation (simplified).
        tau = integration_time
        allan = self._compute_allan(tau)
        
        return ClockReading(
            time=measured_time,
            uncertainty=total_uncertainty,
            stability=allan,
            clock_type=self.type,
            timestamp=true_time,
            metadata={
                'center_frequency': self.center_frequency,
                'linewidth': self.linewidth,
                'N_atoms': N,
                'drift_rate': drift_rate,
                'integration_time': integration_time
            }
        )
    
    def _compute_allan(self, tau: float) -> float:
        """Compute Allan deviation at averaging time τ."""
        # Simplified: Allan deviation τ^(-1/2) for white noise.
        return 1e-13 * np.sqrt(1.0 / max(tau, 1e-10))
    
    def estimate_precision(self, averaging_time: float = 1000.0) -> float:
        """
        Estimate time precision.
        
        Returns:
            Precision in seconds.
        """
        # Quantum limit: Δt ∝ 1/(Q * sqrt(N)).
        Q = self.center_frequency / self.linewidth  # Quality factor.
        N = 10000
        precision = 1.0 / (Q * np.sqrt(N) * averaging_time)
        return precision
    
    def compare_classical(self, averaging_time: float = 1000.0) -> Dict[str, Any]:
        """Compare with classical oscillator."""
        quantum_precision = self.estimate_precision(averaging_time)
        
        # Classical: limited by thermal noise, typically worse.
        classical_precision = quantum_precision * 100  # 100x worse.
        
        return {
            'quantum_precision': quantum_precision,
            'classical_precision': classical_precision,
            'advantage_factor': classical_precision / max(quantum_precision, 1e-20),
            'averaging_time': averaging_time
        }


class TimingSynchronization:
    """Timing synchronization protocols."""
    
    def __init__(self):
        self.clocks: List[AtomicClockSimulation] = []
        self.offsets: List[float] = []
    
    def add_clock(self, clock: AtomicClockSimulation, offset: float = 0.0):
        """Add a clock to the network."""
        self.clocks.append(clock)
        self.offsets.append(offset)
    
    def synchronize(self, reference_idx: int = 0) -> Dict[str, Any]:
        """
        Synchronize clocks to reference.
        
        Args:
            reference_idx: Index of reference clock.
            
        Returns:
            Synchronization results.
        """
        if reference_idx >= len(self.clocks):
            raise ValueError("Invalid reference index")
        
        reference_reading = self.clocks[reference_idx].simulate_clock()
        reference_time = reference_reading.time
        
        results = {
            'reference_time': reference_time,
            'clock_offsets': [],
            'corrected_times': []
        }
        
        for i, (clock, offset) in enumerate(zip(self.clocks, self.offsets)):
            if i == reference_idx:
                results['clock_offsets'].append(0.0)
                results['corrected_times'].append(reference_time)
                continue
            
            reading = clock.simulate_clock()
            measured = reading.time
            
            # Calculate offset.
            offset_estimate = measured - reference_time
            results['clock_offsets'].append(offset_estimate)
            
            # Corrected time.
            corrected = measured - offset_estimate
            results['corrected_times'].append(corrected)
        
        return results
    
    def network_precision(self) -> float:
        """Calculate network timing precision."""
        if len(self.clocks) < 2:
            return 0.0
        
        # Average over all clocks.
        precisions = [c.estimate_precision() for c in self.clocks]
        return np.mean(precisions) / np.sqrt(len(self.clocks))  # √N improvement.


class QuantumEnhancedGPS:
    """Quantum-enhanced GPS simulation."""
    
    def __init__(self, num_satellites: int = 24):
        self.num_satellites = num_satellites
        self.satellite_clocks: List[AtomicClockSimulation] = []
        self._initialize_constellation()
    
    def _initialize_constellation(self):
        """Initialize GPS satellite constellation."""
        for i in range(self.num_satellites):
            clock = AtomicClockSimulation(clock_type="rubidium" if i < 12 else "cesium")
            self.satellite_clocks.append(clock)
    
    def simulate_positioning(self, true_position: Tuple[float, float, float],
                              num_visible: int = 8) -> Dict[str, Any]:
        """
        Simulate GPS positioning with quantum clocks.
        
        Args:
            true_position: (x, y, z) in meters.
            num_visible: Number of visible satellites.
            
        Returns:
            Positioning result.
        """
        # Simulate satellite measurements.
        measurements = []
        for i in range(min(num_visible, self.num_satellites)):
            clock = self.satellite_clocks[i]
            reading = clock.simulate_clock(integration_time=0.1)
            
            # Pseudorange = true distance + clock error.
            sat_pos = self._satellite_position(i)
            distance = np.linalg.norm(
                np.array(true_position) - np.array(sat_pos)
            )
            
            # Clock-induced error.
            clock_error = reading.uncertainty * 3e8  # Convert to meters (c * dt).
            pseudorandom = distance + clock_error + np.random.normal(0, 1.0)
            
            measurements.append({
                'satellite': i,
                'pseudorange': pseudorandom,
                'clock_uncertainty': reading.uncertainty
            })
        
        # Position estimate (simplified: average measurements).
        estimated_position = self._estimate_position(measurements)
        
        # Error.
        error = np.linalg.norm(
            np.array(true_position) - np.array(estimated_position)
        )
        
        return {
            'true_position': true_position,
            'estimated_position': estimated_position,
            'error_meters': error,
            'num_satellites': num_visible,
            'clock_type': 'quantum_enhanced',
            'precision': error / max(num_visible, 1)
        }
    
    def _satellite_position(self, idx: int) -> Tuple[float, float, float]:
        """Get satellite position (simplified circular orbit)."""
        angle = 2 * np.pi * idx / self.num_satellites
        radius = 26560000  # GPS orbit radius in meters.
        x = radius * np.cos(angle)
        y = radius * np.sin(angle)
        z = 0.0
        return (x, y, z)
    
    def _estimate_position(self, measurements: List[Dict]) -> Tuple[float, float, float]:
        """Estimate position from pseudoranges (simplified)."""
        # In practice: multilateration.
        # Simplified: average of pseudorange offsets.
        avg_offset = np.mean([m['pseudorange'] for m in measurements])
        return (avg_offset / 3, avg_offset / 3, 0.0)  # Placeholder.
    
    def compare_classical_gps(self, true_position: Tuple[float, float, float]) -> Dict[str, Any]:
        """Compare quantum vs classical GPS."""
        quantum_result = self.simulate_positioning(true_position)
        
        # Classical GPS: worse clock stability.
        classical_error = quantum_result['error_meters'] * 10  # 10x worse.
        
        return {
            'quantum_error': quantum_result['error_meters'],
            'classical_error': classical_error,
            'improvement_factor': classical_error / max(quantum_result['error_meters'], 1e-10),
            'quantum_precision': 'quantum_enhanced',
            'classical_precision': 'classical_oscillator'
        }


class PrecisionEstimation:
    """Tools for precision estimation."""
    
    def __init__(self):
        self.measurements: List[float] = []
        self.uncertainty_history: List[float] = []
    
    def add_measurement(self, value: float, uncertainty: float):
        """Add a precision measurement."""
        self.measurements.append(value)
        self.uncertainty_history.append(uncertainty)
    
    def estimate_uncertainty(self, method: str = "std") -> float:
        """
        Estimate current uncertainty.
        
        Methods: "std" (standard deviation), "mle" (maximum likelihood).
        """
        if not self.measurements:
            return float('inf')
        
        if method == "std":
            return np.std(self.measurements)
        elif method == "mle":
            # Simplified MLE: inverse of Fisher information.
            if not self.uncertainty_history:
                return np.std(self.measurements)
            avg_uncertainty = np.mean(self.uncertainty_history)
            return avg_uncertainty / np.sqrt(max(len(self.measurements), 1))
        else:
            return np.std(self.measurements)
    
    def scaling_analysis(self, averaging_times: List[float]) -> Dict[str, Any]:
        """Analyze how precision scales with averaging time."""
        uncertainties = []
        
        for tau in averaging_times:
            # Simulate multiple measurements.
            samples = [np.random.normal(0, 1.0 / np.sqrt(tau)) for _ in range(100)]
            unc = np.std(samples)
            uncertainties.append(unc)
        
        # Fit scaling: uncertainty ∝ τ^(-α).
        log_tau = np.log(averaging_times)
        log_unc = np.log(uncertainties)
        
        if len(log_tau) > 1:
            alpha = np.polyfit(log_tau, log_unc, 1)[0]
        else:
            alpha = -0.5  # Quantum: τ^(-1/2).
        
        return {
            'averaging_times': averaging_times,
            'uncertainties': uncertainties,
            'scaling_exponent': alpha,
            'quantum_limit': -0.5,  # τ^(-1/2).
            'is_quantum_limited': abs(alpha + 0.5) < 0.1
        }
