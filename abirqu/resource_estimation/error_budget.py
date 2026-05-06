"""
Task 11.2 — Error Budget Manager

Allocates error budgets, supports what-if analysis, and visualization.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class ErrorType(Enum):
    """Types of errors in quantum circuits."""
    GATE = "gate_error"
    MEASUREMENT = "measurement_error"
    STATE_PREP = "state_preparation_error"
    DECOHERENCE = "decoherence_error"
    CROSSTALK = "crosstalk_error"


@dataclass
class ErrorAllocation:
    """Error allocation for a circuit component."""
    component: str
    error_type: ErrorType
    allocated_budget: float  # Max acceptable error rate
    actual_error: float  # Measured/reported error rate
    within_budget: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'component': self.component,
            'error_type': self.error_type.value,
            'allocated_budget': self.allocated_budget,
            'actual_error': self.actual_error,
            'within_budget': self.within_budget,
            'slack': self.allocated_budget - self.actual_error,
        }


@dataclass
class ErrorBudget:
    """Overall error budget for a quantum circuit."""
    total_budget: float  # Overall error rate budget (e.g., 1e-3)
    components: List[ErrorAllocation]
    unused_budget: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_budget': self.total_budget,
            'unused_budget': self.unused_budget,
            'utilization': 1.0 - (self.unused_budget / self.total_budget),
            'num_components': len(self.components),
            'components': [c.to_dict() for c in self.components],
        }


class ErrorBudgetManager:
    """
    Manages error budget allocation across circuit components.
    
    Features:
    - Distributes acceptable error rates across components
    - What-if analysis for code distance changes
    - Error budget visualization data
    - Optimization suggestions
    """
    
    def __init__(self, default_total_budget: float = 1e-3):
        """
        Initialize error budget manager.
        
        Args:
            default_total_budget: Default error rate budget (e.g., 1e-3 = 0.1%)
        """
        self.default_total_budget = default_total_budget
        self.component_weights = {
            ErrorType.GATE: 0.4,
            ErrorType.MEASUREMENT: 0.3,
            ErrorType.STATE_PREP: 0.2,
            ErrorType.DECOHERENCE: 0.05,
            ErrorType.CROSSTALK: 0.05,
        }
    
    def allocate_budget(self, circuit_info: Dict[str, Any]) -> ErrorBudget:
        """
        Allocate error budget across circuit components.
        
        Args:
            circuit_info: Dict with:
                - 'num_gates': total number of gates
                - 'num_measurements': number of measurements
                - 'num_qubits': number of qubits
                - 'execution_time': estimated execution time
                - 'gate_types': dict of gate -> count
                
        Returns:
            ErrorBudget with allocations
        """
        total_budget = circuit_info.get('error_budget', self.default_total_budget)
        
        # Count components by type
        num_gates = circuit_info.get('num_gates', 100)
        num_measurements = circuit_info.get('num_measurements', 10)
        num_qubits = circuit_info.get('num_qubits', 5)
        exec_time = circuit_info.get('execution_time', 1.0)
        
        # Allocate budget proportionally
        components = []
        
        # Gate errors (distributed across all gates)
        gate_budget = total_budget * self.component_weights[ErrorType.GATE]
        gate_error_rate = gate_budget / max(num_gates, 1)
        components.append(ErrorAllocation(
            component="gates",
            error_type=ErrorType.GATE,
            allocated_budget=gate_error_rate,
            actual_error=circuit_info.get('gate_error_rate', 1e-4),
            within_budget=gate_error_rate >= circuit_info.get('gate_error_rate', 1e-4)
        ))
        
        # Measurement errors
        meas_budget = total_budget * self.component_weights[ErrorType.MEASUREMENT]
        meas_error_rate = meas_budget / max(num_measurements, 1)
        components.append(ErrorAllocation(
            component="measurements",
            error_type=ErrorType.MEASUREMENT,
            allocated_budget=meas_error_rate,
            actual_error=circuit_info.get('measurement_error_rate', 1e-3),
            within_budget=meas_error_rate >= circuit_info.get('measurement_error_rate', 1e-3)
        ))
        
        # State preparation errors
        state_budget = total_budget * self.component_weights[ErrorType.STATE_PREP]
        state_error_rate = state_budget / max(num_qubits, 1)
        components.append(ErrorAllocation(
            component="state_preparation",
            error_type=ErrorType.STATE_PREP,
            allocated_budget=state_error_rate,
            actual_error=circuit_info.get('state_prep_error_rate', 1e-4),
            within_budget=state_error_rate >= circuit_info.get('state_prep_error_rate', 1e-4)
        ))
        
        # Decoherence errors (time-based)
        dec_budget = total_budget * self.component_weights[ErrorType.DECOHERENCE]
        dec_error_rate = dec_budget / max(exec_time, 0.001)
        components.append(ErrorAllocation(
            component="decoherence",
            error_type=ErrorType.DECOHERENCE,
            allocated_budget=dec_error_rate,
            actual_error=circuit_info.get('decoherence_rate', 1e-4),
            within_budget=dec_error_rate >= circuit_info.get('decoherence_rate', 1e-4)
        ))
        
        # Calculate unused budget
        total_used = sum(c.allocated_budget for c in components)
        unused = max(0, total_budget - total_used)
        
        return ErrorBudget(
            total_budget=total_budget,
            components=components,
            unused_budget=unused
        )
    
    def what_if_analysis(self, base_budget: ErrorBudget,
                        scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Perform what-if analysis: how does changing parameters affect budget?
        
        Args:
            base_budget: Baseline ErrorBudget
            scenarios: List of dicts with changes, e.g.:
                [{'code_distance': 5}, {'gate_error_rate': 1e-5}]
                
        Returns:
            List of scenario results
        """
        results = []
        
        for i, scenario in enumerate(scenarios):
            # Create modified circuit info
            modified = scenario.copy()
            
            # Recalculate budget with new parameters
            # (Simplified - in practice would re-run full allocation)
            total = base_budget.total_budget
            
            # Estimate how code distance affects error rates
            if 'code_distance' in scenario:
                d = scenario['code_distance']
                # Error rate ~ (some_factor)^(1-d)
                factor = 0.1  # Simplified
                new_logical_error = factor ** (1 - d)
                modified['gate_error_rate'] = new_logical_error
            
            # Calculate new budget utilization
            components_within = sum(1 for c in base_budget.components if c.within_budget)
            
            results.append({
                'scenario_id': i,
                'changes': scenario,
                'total_budget': total,
                'components_within_budget': components_within,
                'components_over_budget': len(base_budget.components) - components_within,
                'feasible': components_within == len(base_budget.components),
            })
        
        return results
    
    def optimize_allocation(self, budget: ErrorBudget,
                           constraints: Optional[Dict[str, float]] = None) -> ErrorBudget:
        """
        Optimize error budget allocation.
        
        Args:
            budget: Current ErrorBudget
            constraints: Optional dict with min/max for each component
            
        Returns:
            Optimized ErrorBudget
        """
        # Simple optimization: redistribute unused budget to tight components
        if budget.unused_budget > 0:
            # Find components over budget
            over_budget = [c for c in budget.components if not c.within_budget]
            if over_budget:
                # Distribute unused budget
                per_component = budget.unused_budget / len(over_budget)
                for comp in over_budget:
                    comp.allocated_budget += per_component
                    comp.within_budget = comp.allocated_budget >= comp.actual_error
        
        return budget
    
    def generate_visualization_data(self, budget: ErrorBudget) -> Dict[str, Any]:
        """
        Generate data for error budget visualization.
        
        Returns:
            Dict with visualization-ready data
        """
        component_names = [c.component for c in budget.components]
        allocated = [c.allocated_budget for c in budget.components]
        actual = [c.actual_error for c in budget.components]
        within = [1 if c.within_budget else 0 for c in budget.components]
        
        return {
            'components': component_names,
            'allocated_budget': allocated,
            'actual_error': actual,
            'within_budget': within,
            'total_budget': budget.total_budget,
            'unused_budget': budget.unused_budget,
            'utilization_percent': (1.0 - budget.unused_budget / budget.total_budget) * 100,
            'summary': {
                'total': budget.total_budget,
                'used': budget.total_budget - budget.unused_budget,
                'unused': budget.unused_budget,
                'num_over_budget': sum(1 for c in budget.components if not c.within_budget),
            }
        }
    
    def suggest_improvements(self, budget: ErrorBudget) -> List[str]:
        """
        Suggest improvements based on budget analysis.
        
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        # Check for over-budget components
        over_budget = [c for c in budget.components if not c.within_budget]
        if over_budget:
            suggestions.append(f"Increase error budget or improve {len(over_budget)} component(s)")
            for c in over_budget:
                suggestions.append(f"  - {c.component}: needs {c.actual_error:.2e} but only has {c.allocated_budget:.2e}")
        
        # Check utilization
        utilization = 1.0 - (budget.unused_budget / budget.total_budget)
        if utilization < 0.5:
            suggestions.append(f"Low budget utilization ({utilization*100:.1f}%) - consider tightening budget")
        elif utilization > 0.95:
            suggestions.append(f"High budget utilization ({utilization*100:.1f}%) - consider increasing budget")
        
        return suggestions
