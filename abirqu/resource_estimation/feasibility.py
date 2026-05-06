"""
Task 11.5 — Feasibility Assessment Tool

Automated feasibility reports, classical comparison, timeline estimation, recommendations.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class FeasibilityStatus(Enum):
    """Feasibility status."""
    FEASIBLE = "feasible"
    PARTIALLY_FEASIBLE = "partially_feasible"
    INFEASIBLE = "infeasible"
    UNKNOWN = "unknown"


class AlgorithmComplexity(Enum):
    """Classical vs Quantum complexity."""
    P = "P"  # Polynomial
    BPP = "BPP"  # Bounded-error Probabilistic Polynomial
    BQP = "BQP"  # Bounded-error Quantum Polynomial
    NP = "NP"  # Non-deterministic Polynomial
    QMA = "QMA"  # Quantum Merlin Arthur


@dataclass
class FeasibilityReport:
    """Complete feasibility assessment report."""
    algorithm_name: str
    status: FeasibilityStatus
    confidence: float  # 0-1
    
    # Quantum analysis
    quantum_advantage: bool
    estimated_qubits_needed: int
    estimated_runtime_hours: float
    
    # Classical comparison
    classical_complexity: str
    quantum_complexity: str
    speedup_factor: float  # Quantum speedup (1.0 = no speedup)
    
    # Timeline
    practical_timeline: str  # e.g., "2-3 years"
    hardware_readiness: float  # 0-1 scale
    
    # Recommendations
    recommendations: List[str]
    alternative_algorithms: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'algorithm': self.algorithm_name,
            'status': self.status.value,
            'confidence': self.confidence,
            'quantum_advantage': self.quantum_advantage,
            'estimated_qubits': self.estimated_qubits_needed,
            'estimated_runtime_hours': self.estimated_runtime_hours,
            'classical_complexity': self.classical_complexity,
            'quantum_complexity': self.quantum_complexity,
            'speedup_factor': self.speedup_factor,
            'practical_timeline': self.practical_timeline,
            'hardware_readiness': self.hardware_readiness,
            'recommendations': self.recommendations,
            'alternative_algorithms': self.alternative_algorithms,
        }
    
    def generate_text_report(self) -> str:
        """Generate human-readable report."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"FEASIBILITY REPORT: {self.algorithm_name}")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append(f"Status: {self.status.value.upper()}")
        lines.append(f"Confidence: {self.confidence*100:.1f}%")
        lines.append("")
        
        lines.append("QUANTUM ANALYSIS:")
        lines.append(f"  - Quantum Advantage: {'Yes' if self.quantum_advantage else 'No'}")
        lines.append(f"  - Estimated Qubits Needed: {self.estimated_qubits_needed}")
        lines.append(f"  - Estimated Runtime: {self.estimated_runtime_hours:.1f} hours")
        lines.append("")
        
        lines.append("CLASSICAL COMPARISON:")
        lines.append(f"  - Classical Complexity: {self.classical_complexity}")
        lines.append(f"  - Quantum Complexity: {self.quantum_complexity}")
        lines.append(f"  - Quantum Speedup Factor: {self.speedup_factor:.1f}x")
        lines.append("")
        
        lines.append("TIMELINE:")
        lines.append(f"  - Practical Timeline: {self.practical_timeline}")
        lines.append(f"  - Hardware Readiness: {self.hardware_readiness*100:.1f}%")
        lines.append("")
        
        if self.recommendations:
            lines.append("RECOMMENDATIONS:")
            for rec in self.recommendations:
                lines.append(f"  • {rec}")
            lines.append("")
        
        if self.alternative_algorithms:
            lines.append("ALTERNATIVE ALGORITHMS:")
            for alt in self.alternative_algorithms:
                lines.append(f"  • {alt}")
            lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)


class ClassicalHardnessAnalyzer:
    """Analyzes if quantum is actually needed (classical hardness)."""
    
    # Known quantum speedups
    KNOWN_QUANTUM_ADVANTAGES = {
        'Shor': {'speedup': 'exponential', 'classical': 'exponential', 'quantum': 'polynomial'},
        'Grover': {'speedup': 'quadratic', 'classical': 'O(N)', 'quantum': 'O(sqrt(N))'},
        'VQE': {'speedup': 'polynomial', 'classical': 'NP-hard', 'quantum': 'BQP'},
        'QAOA': {'speedup': 'polynomial', 'classical': 'NP-hard', 'quantum': 'BQP'},
        'HHL': {'speedup': 'exponential', 'classical': 'O(N^3)', 'quantum': 'O(log(N))'},
        'QFT': {'speedup': 'exponential', 'classical': 'O(2^n)', 'quantum': 'O(n^2)'},
    }
    
    def analyze(self, algorithm_name: str, problem_size: int) -> Dict[str, Any]:
        """
        Analyze if quantum is needed for this problem.
        
        Args:
            algorithm_name: Name of algorithm
            problem_size: Size of problem (e.g., number of qubits)
            
        Returns:
            Dict with classical hardness analysis
        """
        # Check if algorithm has known quantum advantage
        for known_alg, info in self.KNOWN_QUANTUM_ADVANTAGES.items():
            if known_alg.lower() in algorithm_name.lower():
                return {
                    'has_quantum_advantage': True,
                    'speedup_type': info['speedup'],
                    'classical_complexity': info['classical'],
                    'quantum_complexity': info['quantum'],
                    'quantum_needed': True,
                    'reason': f"Known {info['speedup']} speedup for {known_alg}",
                }
        
        # Default: check problem size
        if problem_size > 50:
            return {
                'has_quantum_advantage': True,
                'speedup_type': 'unknown',
                'classical_complexity': 'unknown',
                'quantum_complexity': 'BQP',
                'quantum_needed': True,
                'reason': 'Large problem size may benefit from quantum',
            }
        else:
            return {
                'has_quantum_advantage': False,
                'speedup_type': 'none',
                'classical_complexity': 'P or BPP',
                'quantum_complexity': 'BQP',
                'quantum_needed': False,
                'reason': 'Problem may be efficiently solvable classically',
            }


class TimelineEstimator:
    """Estimates when an algorithm will become practical."""
    
    def __init__(self):
        # Historical qubit growth: ~doubling every 2 years
        self.qubit_growth_rate = 2.0  # Factor every 2 years
        self.error_improvement_rate = 0.5  # Error halves every 2 years
    
    def estimate(self, current_qubits: int, required_qubits: int,
                 current_error: float, required_error: float) -> str:
        """
        Estimate when algorithm will be practical.
        
        Args:
            current_qubits: Current available qubits
            required_qubits: Qubits needed
            current_error: Current error rate
            required_error: Required error rate
            
        Returns:
            Timeline string (e.g., "2-3 years")
        """
        # Calculate qubit timeline
        if current_qubits >= required_qubits:
            qubit_years = 0
        else:
            qubit_years = np.ceil(np.log2(required_qubits / current_qubits) * 2)
        
        # Calculate error timeline
        if current_error <= required_error:
            error_years = 0
        else:
            error_years = np.ceil(np.log2(current_error / required_error))
        
        # Take the max
        years = max(qubit_years, error_years)
        
        if years <= 0:
            return "Now (already practical)"
        elif years <= 1:
            return "Less than 1 year"
        elif years <= 2:
            return "1-2 years"
        elif years <= 5:
            return "2-5 years"
        elif years <= 10:
            return "5-10 years"
        else:
            return f"More than {int(years)} years"
    
    def hardware_readiness(self, current_qubits: int, required_qubits: int,
                          current_error: float, required_error: float) -> float:
        """Calculate hardware readiness score (0-1)."""
        qubit_score = min(1.0, current_qubits / max(required_qubits, 1))
        error_score = min(1.0, required_error / max(current_error, 1e-10))
        return (qubit_score + error_score) / 2.0


class RecommendationEngine:
    """Suggests alternative algorithms if current one is infeasible."""
    
    ALGORITHM_ALTERNATIVES = {
        'VQE': ['QAOA', 'Quantum Annealing', 'Classical VQE-varients'],
        'QAOA': ['VQE', 'Grover + Classical', 'Simulated Annealing'],
        'Shor': ['Quadratic Sieve (Classical)', 'General Number Field Sieve'],
        'Grover': ['Classical Search', 'Hash-based methods'],
        'HHL': ['Classical Linear Algebra', 'Iterative Methods'],
    }
    
    def recommend(self, algorithm_name: str, status: FeasibilityStatus,
                 issue: Optional[str] = None) -> List[str]:
        """
        Generate recommendations based on feasibility analysis.
        
        Args:
            algorithm_name: Current algorithm
            status: Feasibility status
            issue: Specific issue (e.g., 'too_many_qubits', 'error_rate')
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if status == FeasibilityStatus.INFEASIBLE:
            recommendations.append(f"Algorithm {algorithm_name} is currently infeasible")
            
            if issue == 'too_many_qubits':
                recommendations.append("Consider reducing problem size or using qubit multiplexing")
                recommendations.append("Explore hybrid quantum-classical approaches")
            elif issue == 'error_rate':
                recommendations.append("Wait for better hardware or use more error correction")
                recommendations.append("Consider error mitigation techniques")
            
            # Suggest alternatives
            for alg, alternatives in self.ALGORITHM_ALTERNATIVES.items():
                if alg.lower() in algorithm_name.lower():
                    recommendations.append(f"Consider alternatives: {', '.join(alternatives)}")
        
        elif status == FeasibilityStatus.PARTIALLY_FEASIBLE:
            recommendations.append(f"{algorithm_name} may be feasible for small problem sizes")
            recommendations.append("Consider using error mitigation techniques")
            recommendations.append("Test on simulators first before running on hardware")
        
        else:  # FEASIBLE
            recommendations.append(f"{algorithm_name} is feasible with current hardware")
            recommendations.append("Optimize circuit depth and gate count for better performance")
            recommendations.append("Consider running on multiple hardware platforms for comparison")
        
        return recommendations
    
    def suggest_alternatives(self, algorithm_name: str) -> List[str]:
        """Suggest alternative algorithms."""
        for alg, alternatives in self.ALGORITHM_ALTERNATIVES.items():
            if alg.lower() in algorithm_name.lower():
                return alternatives
        return []


class FeasibilityAssessment:
    """
    Automated feasibility assessment for quantum algorithms.
    
    Features:
    - Automated feasibility report
    - Classical hardness comparison
    - Timeline estimation
    - Recommendation engine
    """
    
    def __init__(self):
        self.classical_analyzer = ClassicalHardnessAnalyzer()
        self.timeline_estimator = TimelineEstimator()
        self.recommendation_engine = RecommendationEngine()
    
    def assess(self, algorithm_info: Dict[str, Any]) -> FeasibilityReport:
        """
        Perform complete feasibility assessment.
        
        Args:
            algorithm_info: Dict with:
                - 'name': algorithm name
                - 'num_qubits': qubits needed
                - 'gate_count': number of gates
                - 'depth': circuit depth
                - 'current_hardware_qubits': available qubits
                - 'current_error_rate': current hardware error rate
                - 'required_error_rate': algorithm's error requirement
                
        Returns:
            FeasibilityReport with complete assessment
        """
        name = algorithm_info.get('name', 'Unknown')
        num_qubits = algorithm_info.get('num_qubits', 100)
        current_qubits = algorithm_info.get('current_hardware_qubits', 127)
        current_error = algorithm_info.get('current_error_rate', 1e-3)
        required_error = algorithm_info.get('required_error_rate', 1e-4)
        
        # Analyze classical hardness
        classical_analysis = self.classical_analyzer.analyze(name, num_qubits)
        
        # Determine feasibility status
        if (num_qubits <= current_qubits and 
            current_error <= required_error * 10 and
            classical_analysis['quantum_needed']):
            status = FeasibilityStatus.FEASIBLE
            confidence = 0.9
        elif num_qubits <= current_qubits * 2:
            status = FeasibilityStatus.PARTIALLY_FEASIBLE
            confidence = 0.6
        else:
            status = FeasibilityStatus.INFEASIBLE
            confidence = 0.8
        
        # Estimate runtime
        gate_time_ns = 100e-9  # 100 ns per gate
        num_gates = algorithm_info.get('gate_count', num_qubits * 100)
        depth = algorithm_info.get('depth', 100)
        runtime_seconds = num_gates * gate_time_ns * depth
        runtime_hours = runtime_seconds / 3600.0
        
        # Timeline estimation
        timeline = self.timeline_estimator.estimate(
            current_qubits, num_qubits, current_error, required_error
        )
        readiness = self.timeline_estimator.hardware_readiness(
            current_qubits, num_qubits, current_error, required_error
        )
        
        # Generate recommendations
        issue = None
        if num_qubits > current_qubits:
            issue = 'too_many_qubits'
        elif current_error > required_error * 10:
            issue = 'error_rate'
        
        recommendations = self.recommendation_engine.recommend(name, status, issue)
        alternatives = self.recommendation_engine.suggest_alternatives(name)
        
        return FeasibilityReport(
            algorithm_name=name,
            status=status,
            confidence=confidence,
            quantum_advantage=classical_analysis['quantum_needed'],
            estimated_qubits_needed=num_qubits,
            estimated_runtime_hours=runtime_hours,
            classical_complexity=classical_analysis['classical_complexity'],
            quantum_complexity=classical_analysis['quantum_complexity'],
            speedup_factor=self._calculate_speedup(classical_analysis['speedup_type']),
            practical_timeline=timeline,
            hardware_readiness=readiness,
            recommendations=recommendations,
            alternative_algorithms=alternatives,
        )
    
    def _calculate_speedup(self, speedup_type: str) -> float:
        """Convert speedup type to numerical factor."""
        if speedup_type == 'exponential':
            return 1000.0  # Arbitrary large number
        elif speedup_type == 'quadratic':
            return 100.0  # sqrt(N) speedup
        elif speedup_type == 'polynomial':
            return 10.0  # Polynomial speedup
        else:
            return 1.0  # No speedup
    
    def quick_assessment(self, algorithm_name: str, 
                        num_qubits: int) -> Tuple[bool, str]:
        """
        Quick feasibility check.
        
        Args:
            algorithm_name: Name of algorithm
            num_qubits: Number of qubits needed
            
        Returns:
            Tuple of (is_feasible, reason)
        """
        current_max_qubits = 1000  # Current state-of-the-art
        
        if num_qubits <= current_max_qubits:
            return True, f"Feasible: {num_qubits} qubits within current capability"
        else:
            return False, f"Infeasible: {num_qubits} qubits exceeds current max ({current_max_qubits})"
