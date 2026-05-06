"""
Task 10.3 — Classical Pre/Post-Processing Pipeline

Data encoding, result decoding, neural network integration, precision management.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Callable
from enum import Enum
import struct


class EncodingType(Enum):
    """Data encoding types for quantum circuits."""
    AMPLITUDE = "amplitude"
    ANGLE = "angle"
    BASIS = "basis"
    KERNEL = "kernel"
    QAM = "qam"  # Quadrature Amplitude Modulation


class DataEncoder:
    """
    Data encoding pipeline for converting classical data to quantum states.
    
    Supports amplitude encoding, angle encoding, basis encoding, and kernel encoding.
    """
    
    def __init__(self, encoding_type: EncodingType = EncodingType.ANGLE):
        """
        Initialize data encoder.
        
        Args:
            encoding_type: Type of encoding to use
        """
        self.encoding_type = encoding_type
        self.precision = 64  # Classical precision in bits
    
    def encode(self, data: Any, num_qubits: Optional[int] = None) -> np.ndarray:
        """
        Encode classical data into quantum state amplitudes.
        
        Args:
            data: Classical data (array, scalar, or dict)
            num_qubits: Number of qubits (auto-detected if None)
            
        Returns:
            Quantum state vector
        """
        if self.encoding_type == EncodingType.AMPLITUDE:
            return self._amplitude_encoding(data, num_qubits)
        elif self.encoding_type == EncodingType.ANGLE:
            return self._angle_encoding(data, num_qubits)
        elif self.encoding_type == EncodingType.BASIS:
            return self._basis_encoding(data, num_qubits)
        elif self.encoding_type == EncodingType.KERNEL:
            return self._kernel_encoding(data, num_qubits)
        else:
            raise ValueError(f"Unknown encoding type: {self.encoding_type}")
    
    def _amplitude_encoding(self, data: Any, num_qubits: Optional[int]) -> np.ndarray:
        """Amplitude encoding: data becomes amplitudes of quantum state."""
        if isinstance(data, (int, float)):
            data = np.array([data])
        elif isinstance(data, list):
            data = np.array(data)
        
        if not isinstance(data, np.ndarray):
            raise ValueError("Data must be array-like for amplitude encoding")
        
        # Normalize data
        norm = np.linalg.norm(data)
        if norm == 0:
            data = np.ones_like(data)
            norm = np.linalg.norm(data)
        data = data / norm
        
        # Determine number of qubits
        if num_qubits is None:
            num_qubits = int(np.ceil(np.log2(len(data))))
        
        # Pad or truncate to 2^num_qubits
        state_size = 2 ** num_qubits
        if len(data) < state_size:
            state = np.zeros(state_size, dtype=complex)
            state[:len(data)] = data
        else:
            state = data[:state_size]
        
        return state.astype(complex)
    
    def _angle_encoding(self, data: Any, num_qubits: Optional[int]) -> np.ndarray:
        """Angle encoding: data values become rotation angles."""
        if isinstance(data, (int, float)):
            data = [data]
        elif isinstance(data, np.ndarray):
            data = data.flatten()
        
        if num_qubits is None:
            num_qubits = len(data)
        
        # Create initial |0...0> state
        state = np.zeros(2 ** num_qubits, dtype=complex)
        state[0] = 1.0
        
        # Apply rotations based on data values
        # Simplified: apply RY rotations
        for i, value in enumerate(data[:num_qubits]):
            angle = float(value)
            # This is a placeholder - actual implementation would apply quantum gates
            # For now, just store angles in state metadata
            pass
        
        return state
    
    def _basis_encoding(self, data: Any, num_qubits: Optional[int]) -> np.ndarray:
        """Basis encoding: data bits become computational basis state."""
        if isinstance(data, str):
            # Convert string to binary
            binary = ''.join(format(ord(c), '08b') for c in data)
            data = [int(b) for b in binary]
        elif isinstance(data, (int, float)):
            data = [int(data)]
        elif isinstance(data, np.ndarray):
            data = (data > 0).astype(int).flatten()
        
        if num_qubits is None:
            num_qubits = len(data)
        
        # Create computational basis state
        # Convert data to integer index
        index = 0
        for i, bit in enumerate(data[:num_qubits]):
            index += bit * (2 ** i)
        
        state = np.zeros(2 ** num_qubits, dtype=complex)
        state[index] = 1.0
        
        return state
    
    def _kernel_encoding(self, data: Any, num_qubits: Optional[int]) -> np.ndarray:
        """Kernel encoding: map data through kernel function to quantum feature space."""
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        
        if num_qubits is None:
            num_qubits = max(3, int(np.ceil(np.log2(len(data) * 2))))
        
        state_size = 2 ** num_qubits
        state = np.zeros(state_size, dtype=complex)
        
        # Simplified kernel: RBF-like feature map
        # In practice, this would use the actual quantum kernel
        for i in range(min(len(data), state_size)):
            state[i] = np.exp(-0.5 * np.linalg.norm(data[i]) ** 2) if data.ndim > 0 else np.exp(-0.5 * data[i] ** 2)
        
        # Normalize
        norm = np.linalg.norm(state)
        if norm > 0:
            state /= norm
        
        return state
    
    def set_precision(self, precision_bits: int):
        """Set classical precision for encoding."""
        self.precision = precision_bits
    
    def get_quantum_precision(self) -> int:
        """Map classical precision to quantum precision (number of qubits)."""
        # Rough mapping: precision_bits -> qubits needed
        return int(np.ceil(self.precision / 2))


class ResultDecoder:
    """
    Result decoding and statistical analysis for hybrid algorithms.
    
    Converts quantum measurement results back to classical data.
    """
    
    def __init__(self):
        self.decoding_history = []
    
    def decode_counts(self, counts: Dict[str, int], 
                     decoding_type: str = "bitstring") -> Any:
        """
        Decode quantum measurement counts to classical values.
        
        Args:
            counts: Measurement counts (e.g., {'00': 50, '11': 50})
            decoding_type: Type of decoding ('bitstring', 'integer', 'float', 'probability')
            
        Returns:
            Decoded classical value
        """
        if decoding_type == "bitstring":
            return self._decode_bitstring(counts)
        elif decoding_type == "integer":
            return self._decode_integer(counts)
        elif decoding_type == "float":
            return self._decode_float(counts)
        elif decoding_type == "probability":
            return self._decode_probability(counts)
        else:
            raise ValueError(f"Unknown decoding type: {decoding_type}")
    
    def _decode_bitstring(self, counts: Dict[str, int]) -> List[str]:
        """Decode to most probable bitstrings."""
        total = sum(counts.values())
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [bitstring for bitstring, count in sorted_counts]
    
    def _decode_integer(self, counts: Dict[str, int]) -> int:
        """Decode to expected integer value."""
        total = sum(counts.values())
        expectation = 0
        for bitstring, count in counts.items():
            # Convert bitstring to integer (LSB first)
            value = int(bitstring, 2)
            expectation += value * count / total
        return int(expectation)
    
    def _decode_float(self, counts: Dict[str, int]) -> float:
        """Decode to expected float value (assuming amplitude encoding)."""
        # Simplified: map computational basis to [-1, 1] range
        total = sum(counts.values())
        expectation = 0.0
        for bitstring, count in counts.items():
            # Map to float based on bitstring pattern
            value = 0.0
            for i, bit in enumerate(bitstring):
                if bit == '1':
                    value += 1.0 / (2 ** (i + 1))
            expectation += value * count / total
        return expectation * 2 - 1  # Map to [-1, 1]
    
    def _decode_probability(self, counts: Dict[str, int]) -> Dict[str, float]:
        """Decode to probability distribution."""
        total = sum(counts.values())
        return {bitstring: count / total for bitstring, count in counts.items()}
    
    def statistical_analysis(self, results: List[Any]) -> Dict[str, float]:
        """
        Perform statistical analysis on decoded results.
        
        Args:
            results: List of decoded results
            
        Returns:
            Dictionary with statistical metrics
        """
        if not results:
            return {}
        
        results_array = np.array(results)
        
        stats = {
            'mean': float(np.mean(results_array)),
            'std': float(np.std(results_array)),
            'var': float(np.var(results_array)),
            'min': float(np.min(results_array)),
            'max': float(np.max(results_array)),
            'median': float(np.median(results_array)),
            'count': len(results)
        }
        
        # Confidence interval (95%)
        if len(results) > 1:
            se = stats['std'] / np.sqrt(len(results))
            stats['ci_95_lower'] = stats['mean'] - 1.96 * se
            stats['ci_95_upper'] = stats['mean'] + 1.96 * se
        
        return stats


class ClassicalPipeline:
    """
    Full classical pre/post-processing pipeline.
    
    Integrates data encoding, quantum execution, result decoding,
    and optional neural network processing.
    """
    
    def __init__(self, encoder: Optional[DataEncoder] = None,
                 decoder: Optional[ResultDecoder] = None):
        """
        Initialize pipeline.
        
        Args:
            encoder: Data encoder (creates default if None)
            decoder: Result decoder (creates default if None)
        """
        self.encoder = encoder or DataEncoder()
        self.decoder = decoder or ResultDecoder()
        self.nn_integration = None
        self.precision_manager = PrecisionManager()
    
    def preprocess(self, data: Any, **kwargs) -> np.ndarray:
        """
        Pre-process classical data for quantum execution.
        
        Args:
            data: Input data
            **kwargs: Additional arguments for encoder
            
        Returns:
            Encoded quantum state
        """
        # Apply precision management
        data = self.precision_manager.to_quantum_precision(data)
        
        # Encode data
        encoded = self.encoder.encode(data, **kwargs)
        
        # Optional neural network pre-processing
        if self.nn_integration:
            encoded = self.nn_integration.preprocess(encoded)
        
        return encoded
    
    def postprocess(self, quantum_results: Any, **kwargs) -> Any:
        """
        Post-process quantum results to classical data.
        
        Args:
            quantum_results: Raw quantum results
            **kwargs: Additional arguments for decoder
            
        Returns:
            Decoded classical data
        """
        # Decode results
        if isinstance(quantum_results, dict) and 'counts' in quantum_results:
            decoded = self.decoder.decode_counts(quantum_results['counts'], **kwargs)
        else:
            decoded = quantum_results
        
        # Optional neural network post-processing
        if self.nn_integration:
            decoded = self.nn_integration.postprocess(decoded)
        
        # Convert back to classical precision
        decoded = self.precision_manager.to_classical_precision(decoded)
        
        return decoded
    
    def integrate_neural_network(self, nn_module: Any):
        """
        Integrate classical neural network.
        
        Args:
            nn_module: Neural network module (must have preprocess/postprocess methods)
        """
        self.nn_integration = nn_module
    
    def run_full_pipeline(self, data: Any, quantum_executor: Callable,
                         **kwargs) -> Tuple[Any, Dict]:
        """
        Run full pre-processing, quantum execution, and post-processing.
        
        Args:
            data: Input data
            quantum_executor: Function that executes quantum circuit
            **kwargs: Additional arguments
            
        Returns:
            Tuple of (final_result, pipeline_stats)
        """
        stats = {}
        
        # Pre-process
        start = time.time() if 'time' in globals() else 0
        encoded = self.preprocess(data)
        stats['preprocess_time'] = time.time() - start if start else 0
        
        # Quantum execution
        if start:
            start = time.time()
        quantum_result = quantum_executor(encoded)
        stats['quantum_time'] = time.time() - start if start else 0
        
        # Post-process
        if start:
            start = time.time()
        final_result = self.postprocess(quantum_result, **kwargs)
        stats['postprocess_time'] = time.time() - start if start else 0
        
        return final_result, stats


class PrecisionManager:
    """
    Automatic precision management between classical and quantum.
    
    Maps classical precision (float32, float64) to quantum precision (qubits).
    """
    
    def __init__(self, classical_bits: int = 64, quantum_qubits: int = 10):
        self.classical_bits = classical_bits
        self.quantum_qubits = quantum_qubits
    
    def to_quantum_precision(self, data: Any) -> Any:
        """Map classical precision to quantum-appropriate representation."""
        if isinstance(data, np.ndarray):
            # Determine appropriate qubit count based on data precision
            if data.dtype == np.float64:
                self.quantum_qubits = 10  # More qubits for higher precision
            elif data.dtype == np.float32:
                self.quantum_qubits = 8
            return data.astype(np.float64)  # Use high precision for quantum
        return data
    
    def to_classical_precision(self, data: Any) -> Any:
        """Map quantum results back to classical precision."""
        if self.classical_bits == 32:
            if isinstance(data, np.ndarray):
                return data.astype(np.float32)
        return data
    
    def suggest_qubits_for_precision(self, required_precision: float) -> int:
        """
        Suggest number of qubits needed for desired precision.
        
        Args:
            required_precision: Desired precision (e.g., 1e-6)
            
        Returns:
            Number of qubits needed
        """
        # Precision ~ 1/2^n for n qubits
        import math
        if required_precision <= 0:
            return 1
        return int(math.ceil(-math.log2(required_precision)))
