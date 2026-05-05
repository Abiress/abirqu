import numpy as np
from typing import List, Dict, Optional, Union
from enum import Enum

class NoiseType(Enum):
    """Types of quantum noise channels."""
    DEPOLARIZING = "depolarizing"
    AMPLITUDE_DAMPING = "amplitude_damping"
    PHASE_DAMPING = "phase_damping"
    PHASE_FLIP = "phase_flip"
    BIT_FLIP = "bit_flip"
    READOUT_ERROR = "readout_error"
    THERMAL_RELAXATION = "thermal_relaxation"

class NoiseModel:
    """
    Framework for quantum noise models.
    Supports various noise channels that can be applied to quantum circuits.
    """
    
    def __init__(self, num_qubits: int):
        """
        Initialize a noise model for a given number of qubits.
        
        Args:
            num_qubits: Number of qubits in the system
        """
        self.num_qubits = num_qubits
        self.single_qubit_errors: Dict[int, List[Dict]] = {}  # qubit -> list of errors
        self.two_qubit_errors: Dict[tuple, List[Dict]] = {}   # (q1, q2) -> list of errors
        self.readout_errors: Dict[int, tuple] = {}  # qubit -> (p(0|1), p(1|0))
        self.gate_errors: Dict[str, float] = {}  # gate name -> error rate
        
    def add_depolarizing_error(self, qubits: Union[int, List[int]], 
                               probability: float) -> 'NoiseModel':
        """
        Add depolarizing noise channel.
        
        Args:
            qubits: Qubit index or list of qubits
            probability: Error probability (0 to 1)
            
        Returns:
            Self for chaining
        """
        if isinstance(qubits, int):
            qubits = [qubits]
            
        for q in qubits:
            if q not in self.single_qubit_errors:
                self.single_qubit_errors[q] = []
            self.single_qubit_errors[q].append({
                'type': NoiseType.DEPOLARIZING,
                'probability': probability
            })
        return self
    
    def add_amplitude_damping(self, qubit: int, gamma: float) -> 'NoiseModel':
        """
        Add amplitude damping (energy relaxation) noise.
        
        Args:
            qubit: Qubit index
            gamma: Damping rate (0 to 1)
            
        Returns:
            Self for chaining
        """
        if qubit not in self.single_qubit_errors:
            self.single_qubit_errors[qubit] = []
        self.single_qubit_errors[qubit].append({
            'type': NoiseType.AMPLITUDE_DAMPING,
            'gamma': gamma
        })
        return self
    
    def add_phase_damping(self, qubit: int, lambda_: float) -> 'NoiseModel':
        """
        Add phase damping (dephasing) noise.
        
        Args:
            qubit: Qubit index
            lambda_: Dephasing rate (0 to 1)
            
        Returns:
            Self for chaining
        """
        if qubit not in self.single_qubit_errors:
            self.single_qubit_errors[qubit] = []
        self.single_qubit_errors[qubit].append({
            'type': NoiseType.PHASE_DAMPING,
            'lambda': lambda_
        })
        return self
    
    def add_readout_error(self, qubit: int, p0given1: float, p1given0: float) -> 'NoiseModel':
        """
        Add readout error for measurement.
        
        Args:
            qubit: Qubit index
            p0given1: Probability of measuring 0 given state is |1>
            p1given0: Probability of measuring 1 given state is |0>
            
        Returns:
            Self for chaining
        """
        self.readout_errors[qubit] = (p0given1, p1given0)
        return self
    
    def add_gate_error(self, gate_name: str, error_rate: float) -> 'NoiseModel':
        """
        Add gate-specific error rate.
        
        Args:
            gate_name: Name of the gate (e.g., 'X', 'CNOT')
            error_rate: Probability of error during gate
            
        Returns:
            Self for chaining
        """
        self.gate_errors[gate_name] = error_rate
        return self
    
    def get_qubit_errors(self, qubit: int) -> List[Dict]:
        """Get all errors for a specific qubit."""
        return self.single_qubit_errors.get(qubit, [])
    
    def get_readout_error(self, qubit: int) -> Optional[tuple]:
        """Get readout error for a qubit."""
        return self.readout_errors.get(qubit)
    
    def apply_to_state_vector(self, state: np.ndarray, gate_matrix: np.ndarray,
                              target_qubits: List[int]) -> np.ndarray:
        """
        Apply noise to a state vector after a gate operation.
        This is a simplified implementation - full density matrix would be better.
        
        Args:
            state: Current state vector
            gate_matrix: Gate matrix that was applied
            target_qubits: Qubits the gate was applied to
            
        Returns:
            Noisy state vector (approximation)
        """
        # For state vector, we apply noise as a probabilistic mixture
        # This is an approximation - real noise would use density matrices
        
        new_state = state.copy()
        
        # Apply depolarizing noise
        for q in target_qubits:
            errors = self.get_qubit_errors(q)
            for error in errors:
                if error['type'] == NoiseType.DEPOLARIZING:
                    p = error['probability']
                    # With probability p, apply a random Pauli
                    if np.random.random() < p:
                        pauli_choice = np.random.choice([0, 1, 2])  # X, Y, Z
                        new_state = self._apply_pauli(new_state, q, pauli_choice)
                        
        return new_state
    
    def _apply_pauli(self, state: np.ndarray, qubit: int, pauli_idx: int) -> np.ndarray:
        """
        Apply a Pauli operator to a state vector.
        
        Args:
            state: State vector
            qubit: Qubit to apply to
            pauli_idx: 0=X, 1=Y, 2=Z
            
        Returns:
            New state vector
        """
        num_qubits = int(np.log2(len(state)))
        
        if pauli_idx == 0:  # X
            # Flip the qubit
            mask = 1 << (num_qubits - 1 - qubit)
            new_state = np.zeros_like(state)
            for i in range(len(state)):
                new_state[i ^ mask] = state[i]
            return new_state
            
        elif pauli_idx == 1:  # Y
            # Y = i*X*Z
            mask = 1 << (num_qubits - 1 - qubit)
            new_state = np.zeros_like(state, dtype=complex)
            for i in range(len(state)):
                bit = (i >> (num_qubits - 1 - qubit)) & 1
                new_state[i ^ mask] = state[i] * (1j if bit == 0 else -1j)
            return new_state
            
        elif pauli_idx == 2:  # Z
            mask = 1 << (num_qubits - 1 - qubit)
            new_state = state.copy()
            for i in range(len(state)):
                bit = (i >> (num_qubits - 1 - qubit)) & 1
                if bit == 1:
                    new_state[i] *= -1
            return new_state
            
        return state
    
    def to_dict(self) -> Dict:
        """Serialize noise model to dictionary."""
        return {
            'num_qubits': self.num_qubits,
            'single_qubit_errors': {
                str(k): v for k, v in self.single_qubit_errors.items()
            },
            'two_qubit_errors': {
                str(k): v for k, v in self.two_qubit_errors.items()
            },
            'readout_errors': {
                str(k): v for k, v in self.readout_errors.items()
            },
            'gate_errors': self.gate_errors
        }

class DeviceNoiseProfile:
    """
    Pre-configured noise profiles based on real quantum devices.
    """
    
    @staticmethod
    def ibm_nairobi() -> NoiseModel:
        """
        Noise profile similar to IBM Nairobi (7-qubit, Falcon r5.11).
        Based on typical device parameters.
        """
        noise = NoiseModel(7)
        
        # Single-qubit gate error ~0.1%
        for q in range(7):
            noise.add_depolarizing_error(q, 0.001)
            noise.add_phase_damping(q, 0.001)
            noise.add_readout_error(q, 0.03, 0.02)  # ~2-3% readout error
            
        # Two-qubit gate errors ~1-2%
        coupling_map = [(0,1), (1,0), (1,2), (2,1), (2,3), (3,2), (3,4), (4,3), (4,5), (5,4), (5,6), (6,5)]
        for q1, q2 in coupling_map:
            noise.add_gate_error('CNOT', 0.015)
            
        return noise
    
    @staticmethod
    def google_sycamore() -> NoiseModel:
        """
        Noise profile similar to Google Sycamore (53-qubit).
        Simplified for 10 qubits.
        """
        noise = NoiseModel(10)
        
        # Sycamore has ~0.1-0.2% single-qubit, ~0.5-1% two-qubit errors
        for q in range(10):
            noise.add_depolarizing_error(q, 0.0015)
            noise.add_phase_damping(q, 0.001)
            noise.add_readout_error(q, 0.015, 0.01)
            
        return noise
    
    @staticmethod
    def ionq_harmony() -> NoiseModel:
        """
        Noise profile for IonQ Harmony (trapped ion).
        Generally lower noise than superconducting.
        """
        noise = NoiseModel(11)
        
        for q in range(11):
            noise.add_depolarizing_error(q, 0.0003)  # Very low single-qubit error
            noise.add_readout_error(q, 0.005, 0.005)  # ~0.5% readout error
            
        # All-to-all connectivity with low two-qubit error
        for q1 in range(11):
            for q2 in range(q1+1, 11):
                noise.add_gate_error('CNOT', 0.003)
                
        return noise

# Example usage and tests
if __name__ == "__main__":
    print("Testing Noise Model Framework...")
    
    # Create a simple noise model
    noise = NoiseModel(2)
    noise.add_depolarizing_error(0, 0.01)
    noise.add_amplitude_damping(0, 0.005)
    noise.add_readout_error(0, 0.02, 0.03)
    noise.add_gate_error('CNOT', 0.02)
    
    print("Noise model created:")
    print(f"Qubit 0 errors: {noise.get_qubit_errors(0)}")
    print(f"Readout error q0: {noise.get_readout_error(0)}")
    print(f"CNOT error rate: {noise.gate_errors.get('CNOT')}")
    
    # Test device profiles
    print("\nIBM Nairobi profile:")
    ibm_noise = DeviceNoiseProfile.ibm_nairobi()
    print(f"Number of qubits: {ibm_noise.num_qubits}")
    print(f"Qubit 0 errors: {len(ibm_noise.get_qubit_errors(0))}")
    
    print("\nIonQ Harmony profile:")
    ionq_noise = DeviceNoiseProfile.ionq_harmony()
    print(f"Number of qubits: {ionq_noise.num_qubits}")
    print(f"CNOT error rate: {ionq_noise.gate_errors.get('CNOT')}")