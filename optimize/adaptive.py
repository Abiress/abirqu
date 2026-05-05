"""
Adaptive Compilation

Implements real-time compilation that adapts to current device calibration data.
Includes qubit selection based on live error rates and dynamic remapping.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CalibrationData:
    """Represents real-time calibration data from a quantum device."""
    timestamp: datetime
    qubit_fidelities: Dict[int, float]  # qubit -> fidelity
    gate_fidelities: Dict[Tuple[int, ...], float]  # (qubits) -> fidelity
    readout_errors: Dict[int, float]  # qubit -> readout error
    t1_times: Dict[int, float]  # qubit -> T1 in microseconds
    t2_times: Dict[int, float]  # qubit -> T2 in microseconds
    
    @classmethod
    def from_device_profile(cls, device_name: str, num_qubits: int) -> 'CalibrationData':
        """Generate synthetic calibration data based on device profile."""
        import random
        
        timestamp = datetime.now()
        qubit_fidelities = {}
        gate_fidelities = {}
        readout_errors = {}
        t1_times = {}
        t2_times = {}
        
        # Generate realistic calibration data
        for q in range(num_qubits):
            # Qubit fidelity typically 99.5-99.9%
            qubit_fidelities[q] = random.uniform(0.995, 0.999)
            # Readout error typically 0.5-3%
            readout_errors[q] = random.uniform(0.005, 0.03)
            # T1: 50-150 microseconds
            t1_times[q] = random.uniform(50, 150)
            # T2: 30-100 microseconds
            t2_times[q] = random.uniform(30, 100)
            
        # Two-qubit gate fidelities
        for q1 in range(num_qubits):
            for q2 in range(q1 + 1, num_qubits):
                gate_fidelities[(q1, q2)] = random.uniform(0.98, 0.995)
                
        return cls(
            timestamp=timestamp,
            qubit_fidelities=qubit_fidelities,
            gate_fidelities=gate_fidelities,
            readout_errors=readout_errors,
            t1_times=t1_times,
            t2_times=t2_times
        )

class QubitSelector:
    """
    Selects optimal qubits based on calibration data.
    """
    
    def __init__(self, calibration: CalibrationData):
        self.calibration = calibration
        
    def select_qubits(self, num_required: int, 
                      exclude: Optional[List[int]] = None) -> List[int]:
        """
        Select best qubits for a circuit.
        
        Args:
            num_required: Number of qubits needed
            exclude: Qubits to exclude from selection
            
        Returns:
            List of selected qubit indices
        """
        exclude_set = set(exclude or [])
        
        # Score each qubit based on multiple factors
        qubit_scores = []
        
        for q in self.calibration.qubit_fidelities:
            if q in exclude_set:
                continue
                
            # Compute score (higher is better)
            fidelity = self.calibration.qubit_fidelities.get(q, 0.99)
            readout_err = self.calibration.readout_errors.get(q, 0.01)
            t1 = self.calibration.t1_times.get(q, 100)
            t2 = self.calibration.t2_times.get(q, 50)
            
            # Normalize and combine (weights can be adjusted)
            score = (
                0.4 * fidelity +
                0.2 * (1 - readout_err) +
                0.2 * min(t1 / 150, 1.0) +  # Normalize T1
                0.2 * min(t2 / 100, 1.0)    # Normalize T2
            )
            
            qubit_scores.append((q, score))
            
        # Sort by score (descending)
        qubit_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Return top qubits
        return [q for q, _ in qubit_scores[:num_required]]
    
    def select_qubit_pair(self, exclude: Optional[List[int]] = None) -> Tuple[int, int]:
        """
        Select best pair of connected qubits.
        
        Args:
            exclude: Qubits to exclude
            
        Returns:
            Tuple of (q1, q2) with best fidelity
        """
        exclude_set = set(exclude or [])
        
        best_pair = None
        best_score = -1
        
        for (q1, q2), fidelity in self.calibration.gate_fidelities.items():
            if q1 in exclude_set or q2 in exclude_set:
                continue
                
            # Average with individual qubit fidelities
            q1_fid = self.calibration.qubit_fidelities.get(q1, 0.99)
            q2_fid = self.calibration.qubit_fidelities.get(q2, 0.99)
            
            score = (fidelity + q1_fid + q2_fid) / 3
            
            if score > best_score:
                best_score = score
                best_pair = (q1, q2)
                
        return best_pair

class AdaptiveCompiler:
    """
    Real-time adaptive compiler that adjusts to device conditions.
    """
    
    def __init__(self, topology: Any, gate_set: Any):
        """
        Initialize adaptive compiler.
        
        Args:
            topology: Hardware topology
            gate_set: Native gate set
        """
        self.topology = topology
        self.gate_set = gate_set
        self.calibration_history = []
        
    def compile_with_calibration(self, circuit: List[Tuple[str, List[int]]],
                                calibration: CalibrationData,
                                num_qubits: int) -> Tuple[List[Tuple[str, List[int]]], Dict]:
        """
        Compile circuit with current calibration data.
        
        Args:
            circuit: Input circuit
            calibration: Current calibration data
            num_qubits: Number of qubits
            
        Returns:
            Tuple of (compiled_circuit, metadata)
        """
        metadata = {
            'timestamp': calibration.timestamp.isoformat(),
            'original_depth': len(circuit),
            'qubit_mapping': {},
            'optimizations_applied': []
        }
        
        # Step1: Select best qubits for the circuit
        selector = QubitSelector(calibration)
        
        # Get qubits used in circuit
        circuit_qubits = set()
        for _, qubits in circuit:
            circuit_qubits.update(qubits)
            
        num_required = len(circuit_qubits)
        selected_qubits = selector.select_qubits(num_required)
        
        # Create mapping: logical -> physical
        logical_to_physical = {}
        sorted_circuit_qubits = sorted(circuit_qubits)
        
        for i, logical_q in enumerate(sorted_circuit_qubits):
            if i < len(selected_qubits):
                logical_to_physical[logical_q] = selected_qubits[i]
                
        metadata['qubit_mapping'] = logical_to_physical
        metadata['optimizations_applied'].append('qubit_selection')
        
        # Step2: Remap circuit to selected qubits
        remapped_circuit = []
        for gate_name, qubits in circuit:
            new_qubits = [logical_to_physical.get(q, q) for q in qubits]
            remapped_circuit.append((gate_name, new_qubits))
            
        # Step3: Optimize based on gate fidelities
        optimized = self._optimize_for_fidelity(remapped_circuit, calibration)
        metadata['optimizations_applied'].append('fidelity_optimization')
        
        # Step4: Adjust for readout errors
        final_circuit = self._adjust_for_readout(optimized, calibration)
        metadata['optimizations_applied'].append('readout_adjustment')
        
        metadata['final_depth'] = len(final_circuit)
        metadata['depth_change'] = metadata['final_depth'] - metadata['original_depth']
        
        return final_circuit, metadata
    
    def _optimize_for_fidelity(self, circuit: List[Tuple[str, List[int]]],
                               calibration: CalibrationData) -> List[Tuple[str, List[int]]]:
        """
        Optimize circuit gate choices based on fidelity data.
        """
        optimized = []
        
        for gate_name, qubits in circuit:
            # Check if there's a better alternative for 2-qubit gates
            if len(qubits) == 2 and gate_name == 'CNOT':
                q1, q2 = qubits
                fid_key = (min(q1, q2), max(q1, q2))
                fidelity = calibration.gate_fidelities.get(fid_key, 0.99)
                
                # If fidelity is low, try to use alternative routing
                if fidelity < 0.985:
                    # Could use SWAP network or different gate
                    # For now, just add a note
                    pass
                    
            optimized.append((gate_name, qubits))
            
        return optimized
    
    def _adjust_for_readout(self, circuit: List[Tuple[str, List[int]]],
                            calibration: CalibrationData) -> List[Tuple[str, List[int]]]:
        """
        Adjust circuit to minimize readout errors.
        """
        # Could add dynamical decoupling or other techniques
        # For now, return as-is
        return circuit.copy()
    
    def dynamic_remapping(self, circuit: List[Tuple[str, List[int]]],
                         mid_circuit_calibration: CalibrationData,
                         current_mapping: Dict[int, int]) -> Dict[int, int]:
        """
        Dynamically remap qubits mid-circuit if errors are detected.
        
        Args:
            circuit: Remaining circuit
            mid_circuit_calibration: Updated calibration
            current_mapping: Current logical->physical mapping
            
        Returns:
            New mapping (if changed)
        """
        # Check if any qubits have degraded significantly
        new_mapping = current_mapping.copy()
        
        for logical, physical in current_mapping.items():
            current_fid = mid_circuit_calibration.qubit_fidelities.get(physical, 1.0)
            
            # If fidelity dropped below threshold, try to remap
            if current_fid < 0.98:
                # Find alternative qubit
                selector = QubitSelector(mid_circuit_calibration)
                exclude = list(new_mapping.values())
                alternatives = selector.select_qubits(1, exclude=exclude)
                
                if alternatives:
                    new_mapping[logical] = alternatives[0]
                    
        return new_mapping

# Example usage and tests
if __name__ == "__main__":
    print("Testing Adaptive Compilation...")
    
    # Create synthetic calibration data
    cal = CalibrationData.from_device_profile("ibm_heron", num_qubits=7)
    
    print(f"Calibration timestamp: {cal.timestamp}")
    print(f"Qubit fidelities: {list(cal.qubit_fidelities.items())[:3]}...")
    
    # Test qubit selection
    selector = QubitSelector(cal)
    best_qubits = selector.select_qubits(3)
    print(f"\nBest 3 qubits: {best_qubits}")
    
    best_pair = selector.select_qubit_pair()
    print(f"Best qubit pair: {best_pair}")
    
    # Test adaptive compiler
    print("\n" + "="*50)
    print("Testing Adaptive Compiler...")
    
    # Create a simple topology (simplified)
    class MockTopology:
        def __init__(self):
            self.num_qubits = 7
            
    class MockGateSet:
        def __init__(self):
            self.device_name = "ibm_heron"
    
    compiler = AdaptiveCompiler(MockTopology(), MockGateSet())
    
    # Test circuit
    test_circuit = [
        ('H', [0]),
        ('CNOT', [0, 1]),
        ('T', [1])
    ]
    
    compiled, metadata = compiler.compile_with_calibration(test_circuit, cal, num_qubits=2)
    
    print(f"\nOriginal circuit: {test_circuit}")
    print(f"Compiled circuit: {compiled}")
    print(f"Metadata: {metadata}")