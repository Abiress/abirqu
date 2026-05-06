"""
Task 11.1 — Physical Resource Calculator

Estimates physical qubits, gate counts, time-to-solution, and resource breakdowns.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class QECCodeType(Enum):
    """Quantum Error Correction Code types."""
    SURFACE_CODE = "surface_code"
    COLOR_CODE = "color_code"
    LDPC = "ldpc"
    REED_MULLER = "reed_muller"
    STEANE = "steane"


@dataclass
class GateCountEstimator:
    """Estimates physical gates per logical gate for different QEC codes."""
    
    code_type: QECCodeType = QECCodeType.SURFACE_CODE
    code_distance: int = 3
    
    # QEC threshold for surface code (~1%)
    SURFACE_CODE_THRESHOLD = 0.01
    
    def estimate_physical_gates(self, logical_gates: Dict[str, int]) -> Dict[str, int]:
        """
        Estimate physical gates needed for logical circuit using real QEC overhead.
        
        Args:
            logical_gates: Dict with gate names and counts {'h': 10, 'cnot': 5, ...}
            
        Returns:
            Dict with physical gate counts
        """
        # Calculate overhead based on code type and distance
        if self.code_type == QECCodeType.SURFACE_CODE:
            clifford_overhead = 2 * (self.code_distance ** 2)  # Clifford gates need ~2d² physical gates
            magic_overhead = 100 * self.code_distance  # T gate distillation overhead
        elif self.code_type == QECCodeType.COLOR_CODE:
            clifford_overhead = 1.5 * (self.code_distance ** 2)
            magic_overhead = 80 * self.code_distance
        elif self.code_type == QECCodeType.LDPC:
            clifford_overhead = 5  # LDPC has low overhead
            magic_overhead = 30
        elif self.code_type == QECCodeType.REED_MULLER:
            clifford_overhead = 3 * (self.code_distance ** 3)
            magic_overhead = 60 * self.code_distance
        elif self.code_type == QECCodeType.STEANE:
            clifford_overhead = 6  # Steane code overhead
            magic_overhead = 35
        else:
            clifford_overhead = 10
            magic_overhead = 50
        
        physical_gates = {}
        for gate, count in logical_gates.items():
            if gate.lower() in ['h', 's', 'cnot', 'cz', 'x', 'y', 'z']:
                physical_gates[f'physical_{gate}'] = int(count * clifford_overhead)
            elif gate.lower() in ['t', 'toffoli', 'r', 'rx', 'ry', 'rz']:
                physical_gates[f'physical_{gate}'] = int(count * clifford_overhead * magic_overhead)
            else:
                physical_gates[f'physical_{gate}'] = int(count * clifford_overhead)
        
        return physical_gates
    
    def qubits_per_logical(self) -> int:
        """Get number of physical qubits per logical qubit."""
        if self.code_type == QECCodeType.SURFACE_CODE:
            return 2 * (self.code_distance ** 2)
        elif self.code_type == QECCodeType.COLOR_CODE:
            return 3 * (self.code_distance ** 2)
        elif self.code_type == QECCodeType.LDPC:
            return 100
        elif self.code_type == QECCodeType.REED_MULLER:
            return 4 * (self.code_distance ** 3)
        elif self.code_type == QECCodeType.STEANE:
            return 7
        else:
            return 2 * (self.code_distance ** 2)
    
    def syndrome_extraction_cost(self) -> int:
        """Get syndrome extraction overhead."""
        overhead = self.OVERHEAD_FACTORS.get(self.code_type, {})
        return overhead.get('syndrome_extraction', 4)


@dataclass
class ResourceBreakdown:
    """Detailed breakdown of quantum resources."""
    
    logical_qubits: int
    physical_qubits: int
    logical_gates: Dict[str, int]
    physical_gates: Dict[str, int]
    estimated_time: float  # seconds
    memory_mb: float
    code_type: QECCodeType
    code_distance: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'logical_qubits': self.logical_qubits,
            'physical_qubits': self.physical_qubits,
            'logical_gates': self.logical_gates,
            'physical_gates': self.physical_gates,
            'estimated_time_s': self.estimated_time,
            'memory_mb': self.memory_mb,
            'code_type': self.code_type.value,
            'code_distance': self.code_distance,
        }


class PhysicalResourceCalculator:
    """
    Tool that estimates physical resources needed for any logical circuit.
    
    Features:
    - Physical qubit estimation given QEC code
    - Gate count estimation (physical gates per logical gate)
    - Time-to-solution estimation
    - Resource breakdown visualization data
    """
    
    def __init__(self, code_type: QECCodeType = QECCodeType.SURFACE_CODE,
                 code_distance: int = 3,
                 gate_time_ns: float = 100.0,  # nanoseconds
                 measurement_time_ns: float = 300.0):
        """
        Initialize resource calculator.
        
        Args:
            code_type: QEC code type
            code_distance: Code distance (higher = better error correction)
            gate_time_ns: Physical gate time in nanoseconds
            measurement_time_ns: Measurement time in nanoseconds
        """
        self.code_type = code_type
        self.code_distance = code_distance
        self.gate_time_ns = gate_time_ns
        self.measurement_time_ns = measurement_time_ns
        self.gate_estimator = GateCountEstimator(code_type, code_distance)
    
    def estimate_resources(self, logical_circuit: Dict[str, Any]) -> ResourceBreakdown:
        """
        Estimate physical resources for a logical circuit.
        
        Args:
            logical_circuit: Dict with:
                - 'num_qubits': number of logical qubits
                - 'gates': dict of gate counts
                - 'depth': circuit depth (optional)
                - 'num_measurements': number of measurements (optional)
                
        Returns:
            ResourceBreakdown with detailed estimates
        """
        num_logical_qubits = logical_circuit.get('num_qubits', 1)
        logical_gates = logical_circuit.get('gates', {})
        depth = logical_circuit.get('depth', 100)
        num_measurements = logical_circuit.get('num_measurements', 0)
        
        # Calculate physical qubits
        qubits_per_logical = self.gate_estimator.qubits_per_logical()
        total_physical_qubits = num_logical_qubits * qubits_per_logical
        
        # Calculate physical gates
        physical_gates = self.gate_estimator.estimate_physical_gates(logical_gates)
        total_physical_gates = sum(physical_gates.values())
        
        # Estimate time
        # Time = (physical_gates * gate_time + measurements * measurement_time) * depth
        gate_time_s = self.gate_time_ns * 1e-9
        meas_time_s = self.measurement_time_ns * 1e-9
        estimated_time = (total_physical_gates * gate_time_s + num_measurements * meas_time_s) * depth
        
        # Estimate memory (simplified: store state vector for physical qubits)
        memory_mb = (2 ** num_logical_qubits * 16) / (1024 ** 2)  # Complex128 = 16 bytes
        
        return ResourceBreakdown(
            logical_qubits=num_logical_qubits,
            physical_qubits=total_physical_qubits,
            logical_gates=logical_gates,
            physical_gates=physical_gates,
            estimated_time=estimated_time,
            memory_mb=memory_mb,
            code_type=self.code_type,
            code_distance=self.code_distance
        )
    
    def time_to_solution(self, resource_breakdown: ResourceBreakdown,
                         error_rate: float = 1e-3,
                         shots: int = 1000) -> float:
        """
        Estimate time-to-solution based on gate speeds and error rates.
        
        Args:
            resource_breakdown: Resource breakdown from estimate_resources()
            error_rate: Physical gate error rate
            shots: Number of circuit executions needed
            
        Returns:
            Estimated time in seconds
        """
        # Base time for one execution
        base_time = resource_breakdown.estimated_time
        
        # Adjust for error rate (need more shots if error rate is high)
        # Simplified: shots needed ~ 1/error_rate for good results
        effective_shots = max(shots, int(1.0 / error_rate))
        
        # Time includes error correction overhead
        # Higher code distance = more qubits but lower logical error
        ec_overhead = self.code_distance ** 2
        
        total_time = base_time * effective_shots * (1 + 0.1 * ec_overhead)
        
        return total_time
    
    def compare_codes(self, logical_circuit: Dict[str, Any],
                      code_types: List[QECCodeType] = None) -> Dict[str, ResourceBreakdown]:
        """
        Compare resource estimates across different QEC codes.
        
        Args:
            logical_circuit: Logical circuit description
            code_types: List of code types to compare (default: all)
            
        Returns:
            Dict mapping code type to ResourceBreakdown
        """
        if code_types is None:
            code_types = list(QECCodeType)
        
        results = {}
        for code_type in code_types:
            calculator = PhysicalResourceCalculator(
                code_type=code_type,
                code_distance=self.code_distance,
                gate_time_ns=self.gate_time_ns,
                measurement_time_ns=self.measurement_time_ns
            )
            results[code_type.value] = calculator.estimate_resources(logical_circuit)
        
        return results
    
    def generate_visualization_data(self, breakdown: ResourceBreakdown) -> Dict[str, Any]:
        """
        Generate data for resource visualization.
        
        Returns:
            Dict with visualization-ready data:
            - 'qubits': {'logical': ..., 'physical': ...}
            - 'gates': {'logical': {...}, 'physical': {...}}
            - 'time_breakdown': {...}
            - 'memory': float
        """
        # Gate type breakdown
        logical_gate_types = list(breakdown.logical_gates.keys())
        physical_gate_types = list(breakdown.physical_gates.keys())
        
        # Time breakdown
        total_physical_gates = sum(breakdown.physical_gates.values())
        gate_time = total_physical_gates * self.gate_time_ns * 1e-9
        
        return {
            'qubits': {
                'logical': breakdown.logical_qubits,
                'physical': breakdown.physical_qubits,
                'ratio': breakdown.physical_qubits / max(breakdown.logical_qubits, 1)
            },
            'gates': {
                'logical': breakdown.logical_gates,
                'physical': breakdown.physical_gates,
                'total_physical': total_physical_gates
            },
            'time_breakdown': {
                'gate_time_s': gate_time,
                'total_time_s': breakdown.estimated_time,
                'time_per_shot_s': breakdown.estimated_time / 1000  # Assume 1000 shots
            },
            'memory_mb': breakdown.memory_mb,
            'code_info': {
                'type': breakdown.code_type.value,
                'distance': breakdown.code_distance,
                'qubits_per_logical': breakdown.physical_qubits / max(breakdown.logical_qubits, 1)
            }
        }
    
    def estimate_memory(self, num_qubits: int, representation: str = "state_vector") -> float:
        """
        Estimate memory needed for simulation.
        
        Args:
            num_qubits: Number of qubits
            representation: 'state_vector', 'density_matrix', 'stabilizer'
            
        Returns:
            Memory in MB
        """
        if representation == "state_vector":
            # Complex128 = 16 bytes per amplitude
            bytes_needed = (2 ** num_qubits) * 16
        elif representation == "density_matrix":
            # (2^n x 2^n) complex matrix
            bytes_needed = (2 ** num_qubits) ** 2 * 16
        elif representation == "stabilizer":
            # Stabilizer simulation uses O(n*m) where m is number of stabilizers
            bytes_needed = num_qubits * self.code_distance * 100  # Rough estimate
        else:
            bytes_needed = (2 ** num_qubits) * 16  # Default to state vector
        
        return bytes_needed / (1024 ** 2)  # Convert to MB
