"""
Task 11.3 — Hardware Requirement Profiler

Profiles algorithms, analyzes thresholds, compares hardware, and aligns roadmaps.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class HardwareType(Enum):
    """Types of quantum hardware."""
    SUPERCONDUCTING = "superconducting"
    TRAPPED_ION = "trapped_ion"
    PHOTONIC = "photonic"
    NEUTRAL_ATOM = "neutral_atom"
    TOPOLOGICAL = "topological"
    NONE = "none"  # For classical simulation


class HardwareSpec:
    """Specifications for a quantum hardware platform."""
    
    def __init__(self, name: str, hw_type: HardwareType,
                 num_qubits: int, gate_fidelity: float,
                 coherence_time_us: float, gate_time_ns: float,
                 connectivity: str = "all-to-all"):
        self.name = name
        self.hw_type = hw_type
        self.num_qubits = num_qubits
        self.gate_fidelity = gate_fidelity  # 1 - error_rate
        self.coherence_time_us = coherence_time_us
        self.gate_time_ns = gate_time_ns
        self.connectivity = connectivity
    
    def error_rate(self) -> float:
        """Get gate error rate."""
        return 1.0 - self.gate_fidelity
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.hw_type.value,
            'num_qubits': self.num_qubits,
            'gate_fidelity': self.gate_fidelity,
            'error_rate': self.error_rate(),
            'coherence_time_us': self.coherence_time_us,
            'gate_time_ns': self.gate_time_ns,
            'connectivity': self.connectivity,
        }


@dataclass
class HardwareRequirement:
    """Minimum hardware requirements for an algorithm."""
    min_qubits: int
    max_error_rate: float  # Maximum acceptable error rate
    min_coherence_time_us: float
    min_fidelity: float
    connectivity_required: str
    estimated_runtime_s: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'min_qubits': self.min_qubits,
            'max_error_rate': self.max_error_rate,
            'min_coherence_time_us': self.min_coherence_time_us,
            'min_fidelity': self.min_fidelity,
            'connectivity_required': self.connectivity_required,
            'estimated_runtime_s': self.estimated_runtime_s,
        }


@dataclass
class ThresholdAnalysis:
    """Result of threshold analysis."""
    algorithm_name: str
    current_error_rate: float
    required_error_rate: float  # Error rate needed for algorithm to work
    threshold_met: bool
    gap_factor: float  # How far we are from threshold (positive = met)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'algorithm': self.algorithm_name,
            'current_error_rate': self.current_error_rate,
            'required_error_rate': self.required_error_rate,
            'threshold_met': self.threshold_met,
            'gap_factor': self.gap_factor,
            'status': 'PASSED' if self.threshold_met else 'FAILED',
        }


class HardwareProfiler:
    """
    Profiles quantum algorithms and determines hardware requirements.
    
    Features:
    - Minimum hardware requirements
    - Threshold analysis
    - Hardware comparison (today vs future)
    - Roadmap alignment
    """
    
    # Known hardware platforms (simplified specs)
    KNOWN_HARDWARE = {
        'IBM_Brisbane': HardwareSpec('IBM Brisbane', HardwareType.SUPERCONDUCTING, 127, 0.9995, 100, 100),
        'IBM_Condor': HardwareSpec('IBM Condor', HardwareType.SUPERCONDUCTING, 1121, 0.999, 150, 80),
        'Google_Sycamore': HardwareSpec('Google Sycamore', HardwareType.SUPERCONDUCTING, 70, 0.999, 50, 25),
        'IonQ_Forte': HardwareSpec('IonQ Forte', HardwareType.TRAPPED_ION, 32, 0.9999, 10000, 10000),
        'QuEra_Aquila': HardwareSpec('QuEra Aquila', HardwareType.NEUTRAL_ATOM, 256, 0.999, 500, 1000),
        'Rigetti_Ankaa': HardwareSpec('Rigetti Ankaa', HardwareType.SUPERCONDUCTING, 84, 0.999, 80, 120),
    }
    
    def __init__(self, hardware_specs: Optional[Dict[str, HardwareSpec]] = None):
        """
        Initialize hardware profiler.
        
        Args:
            hardware_specs: Dict of hardware name -> HardwareSpec (uses KNOWN_HARDWARE if None)
        """
        self.hardware_specs = hardware_specs or self.KNOWN_HARDWARE
    
    def profile_algorithm(self, algorithm_info: Dict[str, Any]) -> HardwareRequirement:
        """
        Profile a quantum algorithm and output minimum hardware requirements.
        
        Args:
            algorithm_info: Dict with:
                - 'name': algorithm name
                - 'num_qubits': number of qubits needed
                - 'num_gates': number of gates
                - 'depth': circuit depth
                - 'critical_path_length': length of critical path
                - 'error_sensitivity': how sensitive to errors (0-1)
                
        Returns:
            HardwareRequirement with minimum specs
        """
        num_qubits = algorithm_info.get('num_qubits', 10)
        num_gates = algorithm_info.get('num_gates', 1000)
        depth = algorithm_info.get('depth', 100)
        critical_path = algorithm_info.get('critical_path_length', depth)
        error_sensitivity = algorithm_info.get('error_sensitivity', 0.5)
        
        # Calculate required error rate
        # Simplified: need error_rate < 1/(num_gates * error_sensitivity)
        max_error_rate = 1.0 / (num_gates * (1.0 + error_sensitivity))
        
        # Calculate required coherence time
        # Need T_coherence >> circuit_execution_time
        gate_time_s = 100e-9  # Assume 100ns per gate
        exec_time = num_gates * gate_time_s
        min_coherence = exec_time * 10  # 10x safety factor
        
        # Calculate required fidelity
        min_fidelity = 1.0 - max_error_rate
        
        return HardwareRequirement(
            min_qubits=num_qubits,
            max_error_rate=max_error_rate,
            min_coherence_time_us=min_coherence * 1e6,  # Convert to microseconds
            min_fidelity=min_fidelity,
            connectivity_required=algorithm_info.get('connectivity', 'all-to-all'),
            estimated_runtime_s=exec_time
        )
    
    def threshold_analysis(self, algorithm_info: Dict[str, Any],
                          hardware: Optional[HardwareSpec] = None) -> ThresholdAnalysis:
        """
        Perform threshold analysis: what error rate is needed?
        
        Args:
            algorithm_info: Algorithm description
            hardware: Hardware to analyze (uses algorithm's target if None)
            
        Returns:
            ThresholdAnalysis with results
        """
        algorithm_name = algorithm_info.get('name', 'Unknown')
        
        # Get current error rate
        if hardware:
            current_error = hardware.error_rate()
        else:
            # Use a typical value
            current_error = 1.0 - algorithm_info.get('target_fidelity', 0.999)
        
        # Calculate required error rate for algorithm
        num_gates = algorithm_info.get('num_gates', 1000)
        success_prob = algorithm_info.get('required_success_prob', 0.9)
        
        # Simplified: need (1 - error_rate)^num_gates >= success_prob
        # => error_rate <= 1 - success_prob^(1/num_gates)
        if num_gates > 0:
            required_error_rate = 1.0 - (success_prob ** (1.0 / num_gates))
        else:
            required_error_rate = current_error
        
        threshold_met = current_error <= required_error_rate
        gap_factor = current_error / max(required_error_rate, 1e-10)
        
        return ThresholdAnalysis(
            algorithm_name=algorithm_name,
            current_error_rate=current_error,
            required_error_rate=required_error_rate,
            threshold_met=threshold_met,
            gap_factor=gap_factor
        )
    
    def compare_hardware(self, algorithm_info: Dict[str, Any],
                         hardware_list: Optional[List[str]] = None) -> List[Tuple[str, bool, float]]:
        """
        Compare hardware platforms for running an algorithm.
        
        Args:
            algorithm_info: Algorithm description
            hardware_list: List of hardware names to compare (all if None)
            
        Returns:
            List of (hardware_name, can_run, score) tuples, sorted by score
        """
        if hardware_list is None:
            hardware_list = list(self.hardware_specs.keys())
        
        requirements = self.profile_algorithm(algorithm_info)
        results = []
        
        for hw_name in hardware_list:
            if hw_name not in self.hardware_specs:
                continue
            
            hw = self.hardware_specs[hw_name]
            
            # Check if hardware can run algorithm
            can_run = (
                hw.num_qubits >= requirements.min_qubits and
                hw.error_rate() <= requirements.max_error_rate and
                hw.coherence_time_us >= requirements.min_coherence_time_us
            )
            
            # Calculate score (higher is better)
            qubit_score = min(1.0, hw.num_qubits / max(requirements.min_qubits, 1))
            error_score = min(1.0, requirements.max_error_rate / max(hw.error_rate(), 1e-10))
            coherence_score = min(1.0, hw.coherence_time_us / max(requirements.min_coherence_time_us, 1))
            
            score = (qubit_score + error_score + coherence_score) / 3.0
            
            results.append((hw_name, can_run, score))
        
        # Sort by score (descending)
        results.sort(key=lambda x: x[2], reverse=True)
        
        return results
    
    def roadmap_alignment(self, algorithm_info: Dict[str, Any],
                          roadmap_year: int = 2026,
                          projection_years: int = 5) -> Dict[str, Any]:
        """
        Align algorithm with hardware roadmap: when will it be practical?
        
        Args:
            algorithm_info: Algorithm description
            roadmap_year: Current year for roadmap
            projection_years: Number of years to project
            
        Returns:
            Dict with roadmap alignment data
        """
        requirements = self.profile_algorithm(algorithm_info)
        
        # Simplified roadmap projection
        # Assume error rates improve by factor of 2 every 2 years
        years = list(range(roadmap_year, roadmap_year + projection_years + 1))
        
        predictions = []
        for year in years:
            years_from_now = year - roadmap_year
            # Improvement factor
            factor = 2.0 ** (years_from_now / 2.0)
            
            # Projected error rate (current best ~ 1e-3, improving)
            projected_error = 1e-3 / factor
            
            # Can we run the algorithm?
            can_run = projected_error <= requirements.max_error_rate
            
            predictions.append({
                'year': year,
                'projected_error_rate': projected_error,
                'can_run_algorithm': can_run,
                'improvement_factor': factor,
            })
        
        # Find when it becomes practical
        practical_year = None
        for pred in predictions:
            if pred['can_run_algorithm']:
                practical_year = pred['year']
                break
        
        return {
            'algorithm': algorithm_info.get('name', 'Unknown'),
            'requirements': requirements.to_dict(),
            'roadmap_projections': predictions,
            'practical_year': practical_year or 'Beyond projection horizon',
            'current_status': 'Practical' if practical_year == roadmap_year else 'Not yet practical',
        }
