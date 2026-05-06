"""
Task 10.4 — Iterative Quantum-Classical Loops

Feedback loops, convergence detection, checkpoint/resume, resource budget management.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Callable, Generator
from dataclasses import dataclass, field
from enum import Enum
import pickle
import time
import os


class LoopState(Enum):
    """State of iterative loop."""
    RUNNING = "running"
    CONVERGED = "converged"
    MAX_ITER_REACHED = "max_iter_reached"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class LoopCheckpoint:
    """Checkpoint data for iterative loop."""
    iteration: int
    parameters: np.ndarray
    value: float
    history: List[Tuple[int, np.ndarray, float]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def save(self, filepath: str):
        """Save checkpoint to file."""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def load(filepath: str) -> 'LoopCheckpoint':
        """Load checkpoint from file."""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


class ConvergenceDetector:
    """
    Detects convergence in iterative quantum-classical algorithms.
    
    Supports multiple convergence criteria: function value, gradient norm,
    parameter change, and custom criteria.
    """
    
    def __init__(self, tol: float = 1e-6, window_size: int = 10,
                 method: str = "function_value"):
        """
        Initialize convergence detector.
        
        Args:
            tol: Tolerance for convergence
            window_size: Number of recent iterations to consider
            method: Convergence method ('function_value', 'gradient', 'parameters', 'custom')
        """
        self.tol = tol
        self.window_size = window_size
        self.method = method
        self.history = []
    
    def check_convergence(self, iteration: int, value: float,
                         gradient: Optional[np.ndarray] = None,
                         params: Optional[np.ndarray] = None) -> Tuple[bool, str]:
        """
        Check if algorithm has converged.
        
        Args:
            iteration: Current iteration number
            value: Current function value
            gradient: Current gradient (optional)
            params: Current parameters (optional)
            
        Returns:
            Tuple of (converged: bool, reason: str)
        """
        self.history.append({
            'iteration': iteration,
            'value': value,
            'gradient': gradient.copy() if gradient is not None else None,
            'params': params.copy() if params is not None else None
        })
        
        # Keep only recent history  
        if len(self.history) > self.window_size:
            self.history = self.history[-self.window_size:]
        
        if self.method == "function_value":
            return self._check_function_convergence()
        elif self.method == "gradient":
            return self._check_gradient_convergence()
        elif self.method == "parameters":
            return self._check_parameter_convergence()
        else:
            return False, "Unknown method"
    
    def _check_function_convergence(self) -> Tuple[bool, str]:
        """Check convergence based on function value changes."""
        if len(self.history) < 2:
            return False, "Not enough history"
        
        values = [h['value'] for h in self.history]
        changes = [abs(values[i] - values[i-1]) for i in range(1, len(values))]
        
        if max(changes) < self.tol:
            return True, f"Function value converged (max change: {max(changes):.2e})"
        
        return False, f"Function value not converged (max change: {max(changes):.2e})"
    
    def _check_gradient_convergence(self) -> Tuple[bool, str]:
        """Check convergence based on gradient norm."""
        if len(self.history) < 2:
            return False, "Not enough history"
        
        recent = self.history[-1]
        if recent['gradient'] is None:
            return False, "No gradient data"
        
        grad_norm = np.linalg.norm(recent['gradient'])
        if grad_norm < self.tol:
            return True, f"Gradient converged (norm: {grad_norm:.2e})"
        
        return False, f"Gradient not converged (norm: {grad_norm:.2e})"
    
    def _check_parameter_convergence(self) -> Tuple[bool, str]:
        """Check convergence based on parameter changes."""
        if len(self.history) < 2:
            return False, "Not enough history"
        
        params_current = self.history[-1]['params']
        params_prev = self.history[-2]['params']
        
        if params_current is None or params_prev is None:
            return False, "No parameter data"
        
        change = np.linalg.norm(params_current - params_prev)
        if change < self.tol:
            return True, f"Parameters converged (change: {change:.2e})"
        
        return False, f"Parameters not converged (change: {change:.2e})"
    
    def reset(self):
        """Reset convergence detector."""
        self.history = []


class FeedbackController:
    """
    Feedback controller for real-time parameter modification.
    
    Modifies quantum circuit parameters based on classical measurement results.
    """
    
    def __init__(self, feedback_rule: str = "adaptive"):
        """
        Initialize feedback controller.
        
        Args:
            feedback_rule: Rule for feedback ('adaptive', 'pid', 'custom')
        """
        self.feedback_rule = feedback_rule
        self.error_history = []
        self.integral = 0.0
        self.previous_error = 0.0
        self.kp = 1.0  # Proportional gain
        self.ki = 0.1  # Integral gain
        self.kd = 0.01  # Derivative gain
    
    def compute_feedback(self, current_value: float, target_value: float,
                        params: np.ndarray) -> np.ndarray:
        """
        Compute feedback adjustment for parameters.
        
        Args:
            current_value: Current measurement result
            target_value: Desired target value
            params: Current parameters
            
        Returns:
            Adjusted parameters
        """
        error = target_value - current_value
        self.error_history.append(error)
        
        if self.feedback_rule == "adaptive":
            return self._adaptive_feedback(error, params)
        elif self.feedback_rule == "pid":
            return self._pid_feedback(error, params)
        else:
            return params  # No adjustment
    
    def _adaptive_feedback(self, error: float, params: np.ndarray) -> np.ndarray:
        """Adaptive feedback: adjust based on error magnitude."""
        new_params = params.copy()
        learning_rate = 0.1
        
        # Adjust all parameters proportionally to error
        adjustment = learning_rate * error
        new_params = new_params + adjustment
        
        return new_params
    
    def _pid_feedback(self, error: float, params: np.ndarray) -> np.ndarray:
        """PID feedback controller."""
        new_params = params.copy()
        
        # Proportional term
        p_term = self.kp * error
        
        # Integral term
        self.integral += error
        i_term = self.ki * self.integral
        
        # Derivative term
        d_term = self.kd * (error - self.previous_error)
        self.previous_error = error
        
        # Total adjustment
        adjustment = p_term + i_term + d_term
        new_params = new_params + adjustment
        
        return new_params


class ResourceBudgetManager:
    """
    Resource budget manager for quantum-classical loops.
    
    Limits quantum calls, wall time, and computational resources.
    """
    
    def __init__(self, max_quantum_calls: Optional[int] = None,
                 max_wall_time: Optional[float] = None,
                 max_iterations: Optional[int] = None):
        """
        Initialize resource budget manager.
        
        Args:
            max_quantum_calls: Maximum number of quantum circuit executions
            max_wall_time: Maximum wall clock time in seconds
            max_iterations: Maximum number of iterations
        """
        self.max_quantum_calls = max_quantum_calls
        self.max_wall_time = max_wall_time
        self.max_iterations = max_iterations
        
        self.quantum_calls = 0
        self.start_time = time.time()
        self.iterations = 0
    
    def can_continue(self) -> Tuple[bool, str]:
        """
        Check if computation can continue within budget.
        
        Returns:
            Tuple of (can_continue: bool, reason: str)
        """
        # Check quantum calls
        if self.max_quantum_calls and self.quantum_calls >= self.max_quantum_calls:
            return False, f"Quantum call budget exhausted ({self.quantum_calls}/{self.max_quantum_calls})"
        
        # Check wall time
        if self.max_wall_time and (time.time() - self.start_time) >= self.max_wall_time:
            return False, f"Wall time budget exhausted ({time.time() - self.start_time:.1f}s/{self.max_wall_time}s)"
        
        # Check iterations
        if self.max_iterations and self.iterations >= self.max_iterations:
            return False, f"Iteration budget exhausted ({self.iterations}/{self.max_iterations})"
        
        return True, "Within budget"
    
    def record_quantum_call(self):
        """Record a quantum circuit execution."""
        self.quantum_calls += 1
    
    def record_iteration(self):
        """Record an iteration."""
        self.iterations += 1
    
    def get_usage(self) -> Dict[str, Any]:
        """Get current resource usage."""
        return {
            'quantum_calls': self.quantum_calls,
            'max_quantum_calls': self.max_quantum_calls,
            'quantum_calls_remaining': (self.max_quantum_calls - self.quantum_calls) if self.max_quantum_calls else None,
            'wall_time': time.time() - self.start_time,
            'max_wall_time': self.max_wall_time,
            'wall_time_remaining': (self.max_wall_time - (time.time() - self.start_time)) if self.max_wall_time else None,
            'iterations': self.iterations,
            'max_iterations': self.max_iterations,
            'iterations_remaining': (self.max_iterations - self.iterations) if self.max_iterations else None,
        }
    
    def reset(self):
        """Reset resource counters."""
        self.quantum_calls = 0
        self.start_time = time.time()
        self.iterations = 0


class IterativeLoop:
    """
    Iterative quantum-classical loop with feedback and convergence detection.
    
    Supports checkpoint/resume and resource budget management.
    """
    
    def __init__(self, feedback_controller: Optional[FeedbackController] = None,
                 convergence_detector: Optional[ConvergenceDetector] = None,
                 resource_manager: Optional[ResourceBudgetManager] = None):
        """
        Initialize iterative loop.
        
        Args:
            feedback_controller: Feedback controller (creates default if None)
            convergence_detector: Convergence detector (creates default if None)
            resource_manager: Resource manager (creates default if None)
        """
        self.feedback_controller = feedback_controller or FeedbackController()
        self.convergence_detector = convergence_detector or ConvergenceDetector()
        self.resource_manager = resource_manager or ResourceBudgetManager()
        
        self.state = LoopState.RUNNING
        self.history = []
        self.current_iteration = 0
        self.checkpoint_dir = "./checkpoints"
        os.makedirs(self.checkpoint_dir, exist_ok=True)
    
    def run(self, initial_params: np.ndarray,
            quantum_executor: Callable[[np.ndarray], float],
            max_iter: int = 100,
            target_value: Optional[float] = None,
            callback: Optional[Callable] = None) -> Tuple[np.ndarray, float, Dict]:
        """
        Run iterative loop.
        
        Args:
            initial_params: Initial parameters
            quantum_executor: Function that executes quantum circuit and returns result
            max_iter: Maximum iterations
            target_value: Target value for feedback (optional)
            callback: Optional callback function called each iteration
            
        Returns:
            Tuple of (final_params, final_value, stats)
        """
        params = initial_params.copy()
        value = quantum_executor(params)
        self.resource_manager.max_iterations = max_iter
        
        self.history.append({
            'iteration': 0,
            'params': params.copy(),
            'value': value
        })
        
        for iteration in range(1, max_iter + 1):
            self.current_iteration = iteration
            self.resource_manager.record_iteration()
            self.resource_manager.record_quantum_call()
            
            # Check resource budget
            can_continue, reason = self.resource_manager.can_continue()
            if not can_continue:
                self.state = LoopState.RESOURCE_EXHAUSTED
                break
            
            # Execute quantum circuit
            value = quantum_executor(params)
            
            # Check convergence
            converged, conv_reason = self.convergence_detector.check_convergence(
                iteration, value, params=params
            )
            
            if converged:
                self.state = LoopState.CONVERGED
                break
            
            # Apply feedback
            if target_value is not None:
                params = self.feedback_controller.compute_feedback(
                    value, target_value, params
                )
            
            # Record history
            self.history.append({
                'iteration': iteration,
                'params': params.copy(),
                'value': value
            })
            
            # Callback
            if callback:
                callback(iteration, params, value)
            
            # Checkpoint every 10 iterations
            if iteration % 10 == 0:
                self.save_checkpoint(iteration)
        
        if self.state == LoopState.RUNNING:
            self.state = LoopState.MAX_ITER_REACHED
        
        # Compile statistics
        stats = {
            'state': self.state.value,
            'iterations': len(self.history),
            'final_value': self.history[-1]['value'],
            'history': self.history,
            'resource_usage': self.resource_manager.get_usage()
        }
        
        return self.history[-1]['params'], self.history[-1]['value'], stats
    
    def save_checkpoint(self, iteration: int):
        """Save checkpoint."""
        checkpoint = LoopCheckpoint(
            iteration=iteration,
            parameters=self.history[-1]['params'],
            value=self.history[-1]['value'],
            history=self.history
        )
        filepath = os.path.join(self.checkpoint_dir, f"checkpoint_{iteration}.pkl")
        checkpoint.save(filepath)
    
    def resume_from_checkpoint(self, filepath: str) -> LoopCheckpoint:
        """Resume from checkpoint."""
        checkpoint = LoopCheckpoint.load(filepath)
        self.history = checkpoint.history
        self.current_iteration = checkpoint.iteration
        return checkpoint
    
    def stop(self):
        """Stop the loop."""
        self.state = LoopState.STOPPED
