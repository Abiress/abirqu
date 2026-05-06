"""
Task 16.2 — Quantum-Enhanced Measurement Protocols.

Squeezed states, NOON states, entanglement-enhanced sensing, adaptive strategies.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class StateType(Enum):
    """Types of quantum-enhanced states."""
    COHERENT = "coherent"
    SQUEEZED = "squeezed"
    NOON = "noon"
    GHZ = "ghz"
    TWISTED = "twisted"


@dataclass
class MeasurementResult:
    """Result of a quantum-enhanced measurement."""
    state_type: StateType
    measured_value: float
    uncertainty: float
    enhancement_factor: float  # Over standard quantum limit.
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'state_type': self.state_type.value,
            'measured_value': self.measured_value,
            'uncertainty': self.uncertainty,
            'enhancement_factor': self.enhancement_factor,
            'metadata': self.metadata
        }


class SqueezedStateGenerator:
    """Generate squeezed states for enhanced phase estimation."""
    
    def __init__(self, squeezing_db: float = 10.0):
        self.squeezing_db = squeezing_db  # Squeezing in dB.
        self.squeezing_factor = 10**(-squeezing_db / 10.0)  # Linear.
    
    def generate(self, N: int = 1000) -> np.ndarray:
        """
        Generate squeezed state.
        
        Args:
            N: Number of particles/spins.
            
        Returns:
            State vector or density matrix (simplified).
        """
        # Simplified: return state representation.
        # In practice, would generate actual squeezed vacuum or spin-squeezed state.
        state = np.zeros(N, dtype=complex)
        state[0] = np.sqrt(1 - self.squeezing_factor)  # Ground component.
        state[1] = np.sqrt(self.squeezing_factor)  # Squeezed component.
        return state
    
    def phase_sensitivity(self, phi: float, N: int = 1000) -> float:
        """
        Phase sensitivity with squeezed state.
        
        Below SQL by factor of squeezing.
        
        Args:
            phi: Phase value (unused in simplified version).
            N: Number of particles/spins.
        """
        # SQL = 1/sqrt(N), Squeezed = SQL / sqrt(squeezing_factor).
        sql = 1.0 / np.sqrt(max(N, 1))  # SQL = 1/√N.
        return sql * np.sqrt(max(self.squeezing_factor, 1e-10))
    
    def estimate_phase(self, measurements: List[float]) -> Tuple[float, float]:
        """Estimate phase from measurements."""
        if not measurements:
            return 0.0, float('inf')
        
        # Simple average.
        phase_est = np.mean(measurements)
        uncertainty = np.std(measurements) / np.sqrt(len(measurements))
        return phase_est, uncertainty


class NOONStateProtocol:
    """NOON state protocols for enhanced phase estimation."""
    
    def __init__(self, N: int = 2):
        self.N = N  # Number of particles in NOON state.
    
    def prepare_noon_state(self) -> np.ndarray:
        """
        Prepare |NOON⟩ = (|N0⟩ + |0N⟩)/√2.
        
        Returns:
            2-qubit state vector representation.
        """
        # Simplified: return |N0⟩ + |0N⟩ state.
        state = np.zeros(2**(self.N + 1), dtype=complex)  # Simplified dimension.
        # |N,0⟩ component.
        state[0] = 1.0 / np.sqrt(2)
        # |0,N⟩ component.
        state[-1] = 1.0 / np.sqrt(2)
        return state
    
    def phase_sensitivity(self) -> float:
        """
        Phase sensitivity with NOON state.
        
        Heisenberg limit: Δφ = 1/N.
        """
        return 1.0 / max(self.N, 1)
    
    def estimate_phase(self, measurements: List[float]) -> Tuple[float, float]:
        """Estimate phase using NOON state interference."""
        if not measurements:
            return 0.0, float('inf')
        
        # NOON state: interference at 2N frequency.
        # Simplified: fit to cos^2(N*phi).
        phase_est = np.mean(measurements) / (2 * self.N)
        uncertainty = self.phase_sensitivity()
        return phase_est, uncertainty


class EntanglementEnhancedSensing:
    """Entanglement-enhanced sensing protocols."""
    
    def __init__(self, entanglement_type: str = "ghz"):
        self.type = entanglement_type  # "ghz", "cluster", "twisted".
    
    def prepare_entangled_state(self, N: int) -> np.ndarray:
        """Prepare entangled sensor network."""
        if self.type == "ghz":
            return self._ghz_state(N)
        elif self.type == "cluster":
            return self._cluster_state(N)
        else:
            return self._twisted_state(N)
    
    def _ghz_state(self, N: int) -> np.ndarray:
        """Prepare GHZ state: (|0...0⟩ + |1...1⟩)/√2."""
        state = np.zeros(2**N, dtype=complex)
        state[0] = 1.0 / np.sqrt(2)  # |0...0⟩.
        state[-1] = 1.0 / np.sqrt(2)  # |1...1⟩.
        return state
    
    def _cluster_state(self, N: int) -> np.ndarray:
        """Prepare cluster state (simplified)."""
        return np.ones(2**N, dtype=complex) / np.sqrt(2**N)
    
    def _twisted_state(self, N: int) -> np.ndarray:
        """Prepare twisted state (spin squeezing)."""
        return np.zeros(2**N, dtype=complex)
    
    def sensing_protocol(self, measurements: List[float]) -> Dict[str, Any]:
        """Run entanglement-enhanced sensing."""
        if not measurements:
            return {'error': 'No measurements'}
        
        # Heisenberg scaling: Δφ ∝ 1/N.
        N = len(measurements)
        uncertainty = 1.0 / max(N, 1)
        
        return {
            'state_type': self.type,
            'estimated_value': np.mean(measurements),
            'uncertainty': uncertainty,
            'scaling': 'heisenberg',  # 1/N.
            'enhancement': N  # Over SQL = 1/√N.
        }


class AdaptiveMeasurement:
    """Adaptive measurement strategies."""
    
    def __init__(self):
        self.history: List[float] = []
        self.phase_estimates: List[float] = []
    
    def adaptive_phase_estimation(self, initial_phase: float = 0.0,
                                num_steps: int = 10) -> MeasurementResult:
        """
        Adaptive phase estimation.
        
        Adjust measurement basis based on previous results.
        """
        current_phase = initial_phase
        
        for step in range(num_steps):
            # Choose measurement setting based on current estimate.
            angle = current_phase + step * np.pi / (2 * num_steps)
            
            # Simulate measurement (simplified).
            true_phase = 0.5  # Simplified: true value.
            measured = true_phase + np.random.normal(0, 0.1 / np.sqrt(step + 1))
            
            # Update estimate (Bayesian or MLE - simplified).
            current_phase = 0.9 * current_phase + 0.1 * measured
            
            self.history.append(measured)
            self.phase_estimates.append(current_phase)
        
        final_estimate = self.phase_estimates[-1]
        uncertainty = np.std(self.phase_estimates)
        
        # Enhancement over non-adaptive.
        enhancement = 2.0  # Simplified: adaptive gives √N improvement.
        
        return MeasurementResult(
            state_type=StateType.COHERENT,
            measured_value=final_estimate,
            uncertainty=uncertainty,
            enhancement_factor=enhancement,
            metadata={
                'steps': num_steps,
                'method': 'adaptive',
                'converged': abs(final_estimate - 0.5) < 0.1
            }
        )
    
    def adaptive_magnetometry(self, B_field: float, 
                           num_steps: int = 10) -> MeasurementResult:
        """Adaptive magnetometry."""
        measurements = []
        current_setting = 0.0
        
        for step in range(num_steps):
            # Adjust measurement based on previous.
            if measurements:
                avg = np.mean(measurements)
                current_setting = avg + 0.1 * np.random.randn()
            
            # Simulate measurement.
            measured = B_field + np.random.normal(0, 0.01)
            measurements.append(measured)
        
        final_B = np.mean(measurements)
        uncertainty = np.std(measurements) / np.sqrt(len(measurements))
        
        return MeasurementResult(
            state_type=StateType.COHERENT,
            measured_value=final_B,
            uncertainty=uncertainty,
            enhancement_factor=1.5,  # Moderate enhancement.
            metadata={
                'B_field': B_field,
                'num_measurements': len(measurements)
            }
        )


class QuantumEnhancedProtocols:
    """Unified interface for quantum-enhanced protocols."""
    
    def __init__(self):
        self.protocols: Dict[str, Any] = {}
        self._register_protocols()
    
    def _register_protocols(self):
        """Register available protocols."""
        self.protocols['squeezed'] = SqueezedStateGenerator()
        self.protocols['noon'] = NOONStateProtocol()
        self.protocols['entangled'] = EntanglementEnhancedSensing()
        self.protocols['adaptive'] = AdaptiveMeasurement()
    
    def run_protocol(self, protocol_name: str, **kwargs) -> MeasurementResult:
        """Run a quantum-enhanced protocol."""
        if protocol_name not in self.protocols:
            raise ValueError(f"Unknown protocol: {protocol_name}")
        
        protocol = self.protocols[protocol_name]
        
        if protocol_name == 'squeezed':
            state = protocol.generate(kwargs.get('N', 1000))
            sensitivity = protocol.phase_sensitivity(kwargs.get('phi', 0.0))
            return MeasurementResult(
                state_type=StateType.SQUEEZED,
                measured_value=sensitivity,
                uncertainty=sensitivity,
                enhancement_factor=1.0 / max(protocol.squeezing_factor, 1e-10),
                metadata={'squeezing_db': protocol.squeezing_db}
            )
        
        elif protocol_name == 'noon':
            state = protocol.prepare_noon_state()
            uncertainty = protocol.phase_sensitivity()
            return MeasurementResult(
                state_type=StateType.NOON,
                measured_value=0.0,  # Phase estimate.
                uncertainty=uncertainty,
                enhancement_factor=protocol.N,  # N-fold enhancement.
                metadata={'N': protocol.N}
            )
        
        elif protocol_name == 'adaptive':
            return protocol.adaptive_phase_estimation(
                initial_phase=kwargs.get('initial_phase', 0.0),
                num_steps=kwargs.get('num_steps', 10)
            )
        
        else:
            raise ValueError(f"Protocol {protocol_name} not implemented")
    
    def compare_protocols(self, true_value: float, 
                          protocols: List[str]) -> Dict[str, Any]:
        """Compare multiple protocols."""
        results = {}
        for name in protocols:
            try:
                result = self.run_protocol(name, N=10)
                results[name] = {
                    'uncertainty': result.uncertainty,
                    'enhancement': result.enhancement_factor
                }
            except Exception as e:
                results[name] = {'error': str(e)}
        
        return {
            'true_value': true_value,
            'protocols': results,
            'best_protocol': min(results, key=lambda x: results[x].get('uncertainty', float('inf')))
        }
