"""
Task 16.5 — Sensing Algorithm Library.

Template library, parameter estimation, multi-parameter estimation, sensitivity optimization, sensing-integrated circuits.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum


class SensingTask(Enum):
    """Types of sensing tasks."""
    MAGNETIC_FIELD = "magnetic_field"
    GRAVITY = "gravity"
    ROTATION = "rotation"
    PHASE = "phase"
    TEMPERATURE = "temperture"
    TIMING = "timing"


@dataclass
class SensingResult:
    """Result of a sensing algorithm."""
    task: SensingTask
    estimated_value: float
    uncertainty: float
    snr: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task': self.task.value,
            'estimated_value': self.estimated_value,
            'uncertainty': self.uncertainty,
            'snr': self.snr,
            'metadata': self.metadata
        }


class SensingTemplateLibrary:
    """Template library for common sensing tasks."""
    
    def __init__(self):
        self.templates: Dict[str, Dict] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load sensing templates."""
        self.templates['ramsey'] = {
            'name': 'Ramsey Interferometry',
            'type': SensingTask.PHASE,
            'pulses': ['pi/2', 'wait', 'pi/2'],
            'sensitivity': '1/T^2',
            'description': 'Phase estimation via Ramsey fringes.'
        }
        self.templates['spin_echo'] = {
            'name': 'Spin Echo',
            'type': SensingTask.MAGNETIC_FIELD,
            'pulses': ['pi/2', 'wait', 'pi', 'wait', 'pi/2'],
            'sensitivity': '1/T^(3/2)',
            'description': 'Reoves low-frequency noise.'
        }
        self.templates['optical_lattice'] = {
            'name': 'Optical Lattice Clock',
            'type': SensingTask.TIMING,
            'pulses': ['prepare', 'wait', 'measure'],
            'sensitivity': '1/sqrt(N*T)',
            'description': 'Atomic clock protocol.'
        }
        self.templates['matter_wave'] = {
            'name': 'Matter-Wave Interferometry',
            'type': SensingTask.GRAVITY,
            'pulses': ['split', 'propagate', 'recombine'],
            'sensitivity': '1/T^(2)',
            'description': 'Gravity measurement with matter waves.'
        }
        self.templates['squeezed_ramsey'] = {
            'name': 'Squeezed Ramsey',
            'type': SensingTask.PHASE,
            'pulses': ['squeeze', 'pi/2', 'wait', 'pi/2'],
            'sensitivity': '1/(T^2 * squeezing)',
            'description': 'Enhanced Ramsey with squeezing.'
        }
    
    def get_template(self, name: str) -> Optional[Dict]:
        """Get a sensing template."""
        return self.templates.get(name.lower())
    
    def list_templates(self, task_type: Optional[SensingTask] = None) -> List[str]:
        """List available templates."""
        if task_type:
            return [t['name'] for t in self.templates.values() 
                    if t['type'] == task_type]
        return [t['name'] for t in self.templates.values()]
    
    def suggest_template(self, task_description: str) -> Optional[Dict]:
        """Suggest template based on task description."""
        desc_lower = task_description.lower()
        
        if 'magnetic' in desc_lower or 'field' in desc_lower:
            return self.templates.get('spin_echo')
        elif 'gravity' in desc_lower or 'gravitational' in desc_lower:
            return self.templates.get('matter_wave')
        elif 'phase' in desc_lower:
            return self.templates.get('ramsey')
        elif 'time' in desc_lower or 'clock' in desc_lower:
            return self.templates.get('optical_lattice')
        elif 'squeezed' in desc_lower:
            return self.templates.get('squeezed_ramsey')
        
        return None


class ParameterEstimation:
    """Parameter estimation protocols."""
    
    def __init__(self):
        self.estimators: Dict[str, Callable] = {}
        self._register_estimators()
    
    def _register_estimators(self):
        """Register estimation methods."""
        self.estimators['mle'] = self._maximum_likelihood
        self.estimators['bayesian'] = self._bayesian_estimation
        self.estimators['quantum_fisher'] = self._quantum_fisher_estimation
    
    def estimate(self, measurements: List[float], 
                 method: str = "mle", **kwargs) -> SensingResult:
        """
        Estimate parameter from measurements.
        
        Args:
            measurements: List of measurement outcomes.
            method: Estimation method.
            **kwargs: Additional parameters.
            
        Returns:
            SensingResult.
        """
        if method not in self.estimators:
            raise ValueError(f"Unknown method: {method}")
        
        task_type = kwargs.get('task', SensingTask.PHASE)
        return self.estimators[method](measurements, task_type, **kwargs)
    
    def _maximum_likelihood(self, measurements: List[float], 
                           task_type: SensingTask, **kwargs) -> SensingResult:
        """Maximum likelihood estimation."""
        if not measurements:
            return SensingResult(task_type, 0.0, float('inf'), 0.0)
        
        estimate = np.mean(measurements)
        uncertainty = np.std(measurements) / np.sqrt(len(measurements))
        snr = abs(estimate) / max(uncertainty, 1e-10)
        
        return SensingResult(
            task=task_type,
            estimated_value=estimate,
            uncertainty=uncertainty,
            snr=snr,
            metadata={'method': 'MLE', 'num_measurements': len(measurements)}
        )
    
    def _bayesian_estimation(self, measurements: List[float],
                            task_type: SensingTask, **kwargs) -> SensingResult:
        """Bayesian estimation (simplified)."""
        if not measurements:
            return SensingResult(task_type, 0.0, float('inf'), 0.0)
        
        # Simplified: use prior-weighted average.
        prior_mean = kwargs.get('prior_mean', 0.0)
        prior_std = kwargs.get('prior_std', 1.0)
        
        # Update with measurements.
        data_mean = np.mean(measurements)
        data_std = np.std(measurements)
        
        # Inverse variance weighting.
        prior_weight = 1.0 / max(prior_std**2, 1e-10)
        data_weight = len(measurements) / max(data_std**2, 1e-10)
        
        posterior_mean = (prior_mean * prior_weight + data_mean * data_weight) / (prior_weight + data_weight)
        posterior_std = 1.0 / np.sqrt(prior_weight + data_weight)
        
        return SensingResult(
            task=task_type,
            estimated_value=posterior_mean,
            uncertainty=posterior_std,
            snr=abs(posterior_mean) / max(posterior_std, 1e-10),
            metadata={'method': 'Bayesian', 'prior_mean': prior_mean, 'posterior_std': posterior_std}
        )
    
    def _quantum_fisher_estimation(self, measurements: List[float],
                                   task_type: SensingTask, **kwargs) -> SensingResult:
        """Quantum Fisher-based estimation."""
        # Simplified: QFI gives ultimate precision limit.
        N = len(measurements)
        qfi = N * kwargs.get('qfi_value', 1.0)  # Fisher information.
        
        uncertainty = 1.0 / np.sqrt(max(qfi, 1e-10))
        estimate = np.mean(measurements) if measurements else 0.0
        
        return SensingResult(
            task=task_type,
            estimated_value=estimate,
            uncertainty=uncertainty,
            snr=abs(estimate) / max(uncertainty, 1e-10),
            metadata={'method': 'Quantum_Fisher', 'qfi': qfi, 'crb': uncertainty**2}
        )


class MultiParameterEstimation:
    """Multi-parameter estimation."""
    
    def __init__(self):
        self.parameters: List[str] = []
        self.covariance_matrix: Optional[np.ndarray] = None
    
    def estimate_multiple(self, measurements: np.ndarray, 
                          parameter_names: List[str]) -> Dict[str, SensingResult]:
        """
        Estimate multiple parameters simultaneously.
        
        Args:
            measurements: 2D array (measurements x parameters).
            parameter_names: Names of parameters.
            
        Returns:
            Dictionary mapping parameter name to SensingResult.
        """
        if len(measurements.shape) != 2:
            raise ValueError("Measurements must be 2D array")
        
        if len(parameter_names) != measurements.shape[1]:
            raise ValueError("Mismatch in number of parameters")
        
        results = {}
        
        for i, param in enumerate(parameter_names):
            # Extract measurements for this parameter.
            param_measurements = measurements[:, i].tolist()
            
            estimator = ParameterEstimation()
            # Determine task type from parameter name.
            if 'phase' in param.lower():
                task = SensingTask.PHASE
            elif 'field' in param.lower() or 'b_' in param.lower():
                task = SensingTask.MAGNETIC_FIELD
            elif 'gravity' in param.lower() or 'g' in param.lower():
                task = SensingTask.GRAVITY
            else:
                task = SensingTask.PHASE  # Default.
            
            result = estimator.estimate(
                param_measurements, 
                method='mle',
                task=task
            )
            results[param] = result
        
        # Calculate covariance matrix.
        self.covariance_matrix = np.cov(measurements.T)
        
        return results
    
    def get_correlation_matrix(self) -> Optional[np.ndarray]:
        """Get correlation matrix between parameters."""
        if self.covariance_matrix is None:
            return None
        
        std = np.sqrt(np.diag(self.covariance_matrix))
        return self.covariance_matrix / np.outer(std, std)


class SensitivityOptimizer:
    """Sensitivity optimization tools."""
    
    def __init__(self):
        self.optimization_history: List[Dict] = []
    
    def optimize_squeezing(self, target_sensitivity: float, 
                            max_squeezing: float = 20.0) -> Dict[str, Any]:
        """
        Optimize squeezing level for target sensitivity.
        
        Returns:
            Dictionary with optimization result.
        """
        best_squeezing = 0.0
        best_achieved = float('inf')
        
        for squeezing_db in np.linspace(0.0, max_squeezing, 50):
            # Sensitivity improves with squeezing.
            squeezing_factor = 10**(-squeezing_db / 10.0)
            achieved = target_sensitivity * squeezing_factor
            
            if achieved < best_achieved:
                best_achieved = achieved
                best_squeezing = squeezing_db
            
            self.optimization_history.append({
                'squeezing_db': squeezing_db,
                'achieved_sensitivity': achieved
            })
        
        return {
            'optimal_squeezing_db': best_squeezing,
            'achieved_sensitivity': best_achieved,
            'target_sensitivity': target_sensitivity,
            'enhancement_factor': target_sensitivity / max(best_achieved, 1e-10)
        }
    
    def optimize_resources(self, N_values: List[int], 
                            sensitivities: List[float]) -> Dict[str, Any]:
        """
        Optimize resource allocation (N, T, etc.).
        
        Returns:
            Dictionary with optimal resource allocation.
        """
        if len(N_values) != len(sensitivities):
            raise ValueError("N_values and sensitivities must have same length")
        
        # Find best N for given sensitivities.
        best_idx = int(np.argmin(sensitivities))
        
        return {
            'optimal_N': N_values[best_idx],
            'optimal_sensitivity': sensitivities[best_idx],
            'all_options': [
                {'N': n, 'sensitivity': s} 
                for n, s in zip(N_values, sensitivities)
            ]
        }
    
    def plot_optimization(self, filepath: Optional[str] = None) -> str:
        """Generate optimization plot (returns ASCII art)."""
        if not self.optimization_history:
            return "No optimization history."
        
        lines = ["Squeezing (dB) vs Sensitivity:", "-" * 40]
        
        for entry in self.optimization_history[:10]:  # Show first 10.
            line = f"{entry['squeezing_db']:5.1f} dB -> {entry['achieved_sensitivity']:.2e}"
            lines.append(line)
        
        result = "\n".join(lines)
        
        if filepath:
            with open(filepath, 'w') as f:
                f.write(result)
        
        return result


class SensingIntegratedCircuit:
    """Sensing-integrated quantum circuits."""
    
    def __init__(self):
        self.circuit: List[Tuple] = []
        self.qubit_count: int = 0
    
    def add_preparation(self, state_type: str, qubit: int):
        """Add state preparation."""
        self.circuit.append(('prepare', state_type, qubit))
        if qubit + 1 > self.qubit_count:
            self.qubit_count = qubit + 1
    
    def add_interaction(self, gate: str, qubits: List[int], 
                          duration: float = 1.0):
        """Add sensing interaction."""
        self.circuit.append(('interaction', gate, qubits, duration))
    
    def add_measurement(self, basis: str, qubit: int):
        """Add measurement."""
        self.circuit.append(('measure', basis, qubit))
    
    def simulate(self, num_shots: int = 1000) -> List[float]:
        """
        Simulate the sensing circuit.
        
        Returns:
            List of measurement outcomes.
        """
        outcomes = []
        
        for _ in range(num_shots):
            # Simplified simulation.
            # In practice, would run actual quantum circuit.
            outcome = np.random.randn()  # Placeholder.
            outcomes.append(outcome)
        
        return outcomes
    
    def to_circuit_description(self) -> Dict[str, Any]:
        """Convert to circuit description."""
        return {
            'num_qubits': self.qubit_count,
            'depth': len(self.circuit),
            'gates': [str(g) for g in self.circuit],
            'type': 'sensing_circuit'
        }
    
    def optimize_for_task(self, task: SensingTask) -> 'SensingIntegratedCircuit':
        """
        Optimize circuit for specific sensing task.
        
        Returns:
            Optimized circuit (simplified: returns self).
        """
        # Simplified: add task-specific optimizations.
        if task == SensingTask.PHASE:
            # Add Ramsey sequence.
            self.add_preparation('coherent', 0)
            self.add_interaction('wait', [0], duration=1.0)
            self.add_measurement('x', 0)
        elif task == SensingTask.MAGNETIC_FIELD:
            # Add spin echo.
            self.add_preparation('coherent', 0)
            self.add_interaction('pi', [0], duration=0.5)
            self.add_interaction('wait', [0], duration=1.0)
            self.add_interaction('pi', [0], duration=0.5)
            self.add_measurement('y', 0)
        
        return self
