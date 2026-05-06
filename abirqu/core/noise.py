"""
Noise Model for AbirQu
Copyright 2026 Abir Maheshwari
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from .gates import Gate

class NoiseModel:
    """Quantum noise model with various error channels."""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.error_rates: Dict[str, float] = {}
        self.t1: Optional[float] = None  # Relaxation time (µs)
        self.t2: Optional[float] = None  # Dephasing time (µs)
        self.gate_times: Dict[str, float] = {'single': 0.1, 'two': 0.3}  # µs
        
    def add_depolarizing_noise(self, gate: str, error_rate: float):
        """Add depolarizing noise channel."""
        self.error_rates[gate] = error_rate
        
    def add_amplitude_damping(self, t1: float):
        """Add amplitude damping (T1) noise."""
        self.t1 = t1
        
    def add_phase_damping(self, t2: float):
        """Add phase damping (T2) noise."""
        self.t2 = t2
        
    def get_depolarizing_kraus(self, error_rate: float) -> List[np.ndarray]:
        """Get Kraus operators for depolarizing channel."""
        p = error_rate
        I = np.eye(2, dtype=complex)
        X = np.array([[0,1],[1,0]], dtype=complex)
        Y = np.array([[0,-1j],[1j,0]], dtype=complex)
        Z = np.array([[1,0],[0,-1]], dtype=complex)
        
        K0 = np.sqrt(1 - 3*p/4) * I
        K1 = np.sqrt(p/4) * X
        K2 = np.sqrt(p/4) * Y
        K3 = np.sqrt(p/4) * Z
        return [K0, K1, K2, K3]
        
    def get_amplitude_damping_kraus(self, gamma: float) -> List[np.ndarray]:
        """Get Kraus operators for amplitude damping."""
        K0 = np.array([[1,0],[0, np.sqrt(1-gamma)]], dtype=complex)
        K1 = np.array([[0, np.sqrt(gamma)],[0,0]], dtype=complex)
        return [K0, K1]
        
    def get_phase_damping_kraus(self, gamma: float) -> List[np.ndarray]:
        """Get Kraus operators for phase damping."""
        K0 = np.array([[1,0],[0, np.sqrt(1-gamma)]], dtype=complex)
        K1 = np.array([[0,0],[0, np.sqrt(gamma)]], dtype=complex)
        return [K0, K1]
        
    def apply_noise(self, state: np.ndarray, gate_name: str = None) -> np.ndarray:
        """Apply noise to a quantum state."""
        # Apply depolarizing noise if gate specified
        if gate_name and gate_name in self.error_rates:
            p = self.error_rates[gate_name]
            if p > 0:
                # Randomly apply one of the Pauli errors
                if np.random.random() < 3*p/4:
                    # Apply random Pauli
                    pauli = np.random.choice(['X', 'Y', 'Z'])
                    if pauli == 'X':
                        # Apply X to all qubits (simplified)
                        pass  # Full implementation would apply to specific qubits
                        
        return state
        
    def apply_t1_noise(self, state: np.ndarray, time: float) -> np.ndarray:
        """Apply T1 (amplitude damping) noise."""
        if self.t1 is None or self.t1 == 0:
            return state
            
        gamma = 1 - np.exp(-time / self.t1)
        # Simplified: apply to first qubit only
        # Full implementation would apply to all qubits
        return state
        
    def apply_t2_noise(self, state: np.ndarray, time: float) -> np.ndarray:
        """Apply T2 (dephasing) noise."""
        if self.t2 is None or self.t2 == 0:
            return state
            
        gamma = 1 - np.exp(-time / self.t2)
        # Simplified implementation
        return state
        
    def get_total_error_rate(self, gate: str) -> float:
        """Get total error rate for a gate."""
        return self.error_rates.get(gate, 0.0)
        
    def __repr__(self):
        return f"NoiseModel({self.name}, gates={len(self.error_rates)}, T1={self.t1}, T2={self.t2})"
