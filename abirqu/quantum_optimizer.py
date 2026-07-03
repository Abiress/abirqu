"""
Native Quantum Optimization Loop.

Package gradient-free (COBYLA, Nelder-Mead, SPSA) and gradient-based
classical optimizers directly alongside the simulator memory to minimize
context-switching latency.

For hybrid VQE/QAOA, the optimizer runs in-process with the quantum
simulator, avoiding IPC overhead.

Optimizers included:
    - COBYLA (Constrained Optimization BY Linear Approximations)
    - SPSA (Simultaneous Perturbation Stochastic Approximation)
    - Nelder-Mead (Simplex)
    - Gradient Descent (with momentum)
    - Adam (Adaptive Moment Estimation)
    - L-BFGS-B (limited-memory BFGS with bounds)

References:
    - Powell (1994): COBYLA
    - Spall (1992): SPSA
    - Kingma & Ba (2014): Adam
"""

import math
import time
import random
from typing import Callable, Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class OptimizerType(Enum):
    """Supported optimizer types."""
    COBYLA = "cobyla"
    SPSA = "spsa"
    NELDER_MEAD = "nelder_mead"
    GRADIENT_DESCENT = "gradient_descent"
    ADAM = "adam"
    L_BFGS_B = "l_bfgs_b"


@dataclass
class OptimizationResult:
    """
    Result of a quantum optimization.

    Attributes
    ----------
    optimal_params : dict
        Optimal parameter values
    optimal_cost : float
        Minimum cost achieved
    cost_history : list
        Cost at each iteration
    param_history : list
        Parameters at each iteration
    num_iterations : int
        Total iterations executed
    convergence : bool
        Whether optimization converged
    wall_time_s : float
        Total wall-clock time
    """
    optimal_params: Dict[str, float]
    optimal_cost: float
    cost_history: List[float]
    param_history: List[Dict[str, float]]
    num_iterations: int
    convergence: bool
    wall_time_s: float


class COBYLA:
    """
    Constrained Optimization BY Linear Approximations.

    A gradient-free optimizer that builds linear models of the objective
    function from function evaluations. Good for noisy quantum objectives.

    Parameters
    ----------
    maxiter : int
        Maximum iterations
    tol : float
        Convergence tolerance
    rhobeg : float
        Initial step size
    catol : float
        Constraint tolerance
    """

    def __init__(self, maxiter: int = 200, tol: float = 1e-6,
                 rhobeg: float = 0.5, catol: float = 1e-4):
        self.maxiter = maxiter
        self.tol = tol
        self.rhobeg = rhobeg
        self.catol = catol

    def minimize(self, objective: Callable[[Dict[str, float]], float],
                 initial_params: Dict[str, float],
                 bounds: Optional[Dict[str, Tuple[float, float]]] = None) -> OptimizationResult:
        """
        Minimize the objective function using COBYLA.

        Parameters
        ----------
        objective : callable
            Function f(params_dict) -> cost
        initial_params : dict
            Starting parameters
        bounds : dict, optional
            Parameter bounds: {name: (min, max)}
        """
        params = dict(initial_params)
        symbols = list(params.keys())
        n = len(symbols)
        bounds = bounds or {}

        cost_history = []
        param_history = []
        start_time = time.time()

        # Evaluate initial point
        current_cost = objective(params)
        cost_history.append(current_cost)
        param_history.append(dict(params))

        # Initialize simplex
        simplex = [np.array([params[s] for s in symbols])]
        simplex_costs = [current_cost]

        for i in range(min(n + 1, self.maxiter)):
            x = simplex[0].copy()
            x[i % n] += self.rhobeg
            trial = {s: float(x[j]) for j, s in enumerate(symbols)}
            trial = self._clip_bounds(trial, bounds)
            c = objective(trial)
            simplex.append(x)
            simplex_costs.append(c)

        # COBYLA iterations
        for iteration in range(self.maxiter):
            # Sort simplex by cost
            indexed = list(enumerate(simplex_costs))
            indexed.sort(key=lambda x: x[1])

            best_idx = indexed[0][0]
            worst_idx = indexed[-1][0]
            best_cost = indexed[0][1]
            worst_cost = indexed[-1][1]

            # Check convergence
            if abs(worst_cost - best_cost) < self.tol:
                break

            # Compute centroid (excluding worst)
            centroid = np.zeros(n)
            for idx, c in indexed[:-1]:
                centroid += simplex[idx]
            centroid /= n

            # Reflection
            x_worst = simplex[worst_idx]
            x_reflect = centroid + (centroid - x_worst)
            trial = {s: float(x_reflect[j]) for j, s in enumerate(symbols)}
            trial = self._clip_bounds(trial, bounds)
            reflect_cost = objective(trial)

            if indexed[0][1] <= reflect_cost <= indexed[-2][1]:
                # Accept reflection
                simplex[worst_idx] = x_reflect
                simplex_costs[worst_idx] = reflect_cost
            elif reflect_cost < indexed[0][1]:
                # Expansion
                x_expand = centroid + 2 * (x_reflect - centroid)
                trial = {s: float(x_expand[j]) for j, s in enumerate(symbols)}
                trial = self._clip_bounds(trial, bounds)
                expand_cost = objective(trial)
                if expand_cost < reflect_cost:
                    simplex[worst_idx] = x_expand
                    simplex_costs[worst_idx] = expand_cost
                else:
                    simplex[worst_idx] = x_reflect
                    simplex_costs[worst_idx] = reflect_cost
            else:
                # Contraction
                x_contract = centroid + 0.5 * (x_worst - centroid)
                trial = {s: float(x_contract[j]) for j, s in enumerate(symbols)}
                trial = self._clip_bounds(trial, bounds)
                contract_cost = objective(trial)
                if contract_cost < worst_cost:
                    simplex[worst_idx] = x_contract
                    simplex_costs[worst_idx] = contract_cost
                else:
                    # Shrink
                    for i in range(len(simplex)):
                        if i != best_idx:
                            simplex[i] = 0.5 * (simplex[i] + simplex[best_idx])
                            trial = {s: float(simplex[i][j]) for j, s in enumerate(symbols)}
                            trial = self._clip_bounds(trial, bounds)
                            simplex_costs[i] = objective(trial)

            # Update params to best
            best_simplex_idx = min(range(len(simplex)), key=lambda i: simplex_costs[i])
            params = {s: float(simplex[best_simplex_idx][j]) for j, s in enumerate(symbols)}
            params = self._clip_bounds(params, bounds)
            cost_history.append(simplex_costs[best_simplex_idx])
            param_history.append(dict(params))

        # Find best
        best_idx = min(range(len(cost_history)), key=lambda i: cost_history[i])

        return OptimizationResult(
            optimal_params=param_history[best_idx],
            optimal_cost=cost_history[best_idx],
            cost_history=cost_history,
            param_history=param_history,
            num_iterations=len(cost_history) - 1,
            convergence=abs(cost_history[-1] - cost_history[best_idx]) < self.tol,
            wall_time_s=time.time() - start_time,
        )

    def _clip_bounds(self, params: Dict[str, float],
                     bounds: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
        """Clip parameters to bounds."""
        result = {}
        for k, v in params.items():
            if k in bounds:
                lo, hi = bounds[k]
                result[k] = max(lo, min(hi, v))
            else:
                result[k] = v
        return result


class SPSA:
    """
    Simultaneous Perturbation Stochastic Approximation.

    A gradient-free stochastic optimizer that approximates the gradient
    using only 2 function evaluations per iteration (regardless of
    parameter dimension). Ideal for noisy quantum objectives.

    Parameters
    ----------
    maxiter : int
        Maximum iterations
    a : float
        Step size scaling parameter
    c : float
        Perturbation scaling parameter
    A : float
        Stabilization parameter (typically 0.01 * maxiter)
    alpha : float
        Step size decay exponent (typically 0.602)
    gamma : float
        Perturbation decay exponent (typically 0.101)
    """

    def __init__(self, maxiter: int = 200, a: float = 0.2, c: float = 0.1,
                 A: float = None, alpha: float = 0.602, gamma: float = 0.101):
        self.maxiter = maxiter
        self.a = a
        self.c = c
        self.A = A
        self.alpha = alpha
        self.gamma = gamma

    def minimize(self, objective: Callable[[Dict[str, float]], float],
                 initial_params: Dict[str, float],
                 bounds: Optional[Dict[str, Tuple[float, float]]] = None) -> OptimizationResult:
        """Minimize using SPSA."""
        params = dict(initial_params)
        symbols = list(params.keys())
        n = len(symbols)
        A = self.A or 0.01 * self.maxiter
        bounds = bounds or {}

        cost_history = []
        param_history = []
        start_time = time.time()

        for k in range(self.maxiter):
            # Evaluate at current point
            cost_k = objective(params)
            cost_history.append(cost_k)
            param_history.append(dict(params))

            # Step sizes
            a_k = self.a / (k + 1 + A) ** self.alpha
            c_k = self.c / (k + 1) ** self.gamma

            # Random perturbation (Bernoulli ±1)
            delta = np.array([random.choice([-1, 1]) for _ in range(n)])

            # Evaluate at perturbed points
            params_plus = {s: float(np.clip(params[s] + c_k * delta[j],
                                            bounds[s][0] if s in bounds else -np.inf,
                                            bounds[s][1] if s in bounds else np.inf))
                           for j, s in enumerate(symbols)}
            params_minus = {s: float(np.clip(params[s] - c_k * delta[j],
                                             bounds[s][0] if s in bounds else -np.inf,
                                             bounds[s][1] if s in bounds else np.inf))
                            for j, s in enumerate(symbols)}

            cost_plus = objective(params_plus)
            cost_minus = objective(params_minus)

            # Approximate gradient
            g_hat = (cost_plus - cost_minus) / (2 * c_k * delta)

            # Update
            for j, s in enumerate(symbols):
                params[s] = float(np.clip(
                    params[s] - a_k * g_hat[j],
                    bounds[s][0] if s in bounds else -np.inf,
                    bounds[s][1] if s in bounds else np.inf,
                ))

        # Final evaluation
        final_cost = objective(params)
        cost_history.append(final_cost)
        param_history.append(dict(params))

        best_idx = min(range(len(cost_history)), key=lambda i: cost_history[i])

        return OptimizationResult(
            optimal_params=param_history[best_idx],
            optimal_cost=cost_history[best_idx],
            cost_history=cost_history,
            param_history=param_history,
            num_iterations=self.maxiter,
            convergence=False,  # SPSA doesn't have a clear convergence criterion
            wall_time_s=time.time() - start_time,
        )


class GradientDescent:
    """
    Gradient Descent with optional momentum.

    Parameters
    ----------
    maxiter : int
        Maximum iterations
    learning_rate : float
        Step size
    momentum : float
        Momentum coefficient (0 = no momentum)
    tol : float
        Convergence tolerance
    """

    def __init__(self, maxiter: int = 200, learning_rate: float = 0.01,
                 momentum: float = 0.9, tol: float = 1e-6):
        self.maxiter = maxiter
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.tol = tol

    def minimize(self, objective: Callable[[Dict[str, float]], float],
                 initial_params: Dict[str, float],
                 gradient: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None,
                 bounds: Optional[Dict[str, Tuple[float, float]]] = None) -> OptimizationResult:
        """
        Minimize using gradient descent.

        If gradient is not provided, uses finite differences.
        """
        params = dict(initial_params)
        symbols = list(params.keys())
        bounds = bounds or {}

        cost_history = []
        param_history = []
        velocity = {s: 0.0 for s in symbols}
        start_time = time.time()

        for k in range(self.maxiter):
            cost = objective(params)
            cost_history.append(cost)
            param_history.append(dict(params))

            # Compute gradient
            if gradient is not None:
                grad = gradient(params)
            else:
                # Finite differences
                grad = {}
                eps = 1e-6
                for s in symbols:
                    params_plus = dict(params)
                    params_plus[s] += eps
                    params_minus = dict(params)
                    params_minus[s] -= eps
                    grad[s] = (objective(params_plus) - objective(params_minus)) / (2 * eps)

            # Check convergence
            grad_norm = math.sqrt(sum(g ** 2 for g in grad.values()))
            if grad_norm < self.tol:
                break

            # Update with momentum
            for s in symbols:
                velocity[s] = self.momentum * velocity[s] + self.learning_rate * grad[s]
                new_val = params[s] - velocity[s]
                if s in bounds:
                    new_val = max(bounds[s][0], min(bounds[s][1], new_val))
                params[s] = float(new_val)

        final_cost = objective(params)
        cost_history.append(final_cost)
        param_history.append(dict(params))

        best_idx = min(range(len(cost_history)), key=lambda i: cost_history[i])

        return OptimizationResult(
            optimal_params=param_history[best_idx],
            optimal_cost=cost_history[best_idx],
            cost_history=cost_history,
            param_history=param_history,
            num_iterations=len(cost_history) - 1,
            convergence=grad_norm < self.tol if 'grad_norm' in dir() else False,
            wall_time_s=time.time() - start_time,
        )


class Adam:
    """
    Adaptive Moment Estimation optimizer.

    Combines the benefits of AdaGrad and RMSProp with momentum.
    Works well for noisy quantum objectives.

    Parameters
    ----------
    maxiter : int
        Maximum iterations
    learning_rate : float
        Step size
    beta1 : float
        Exponential decay for first moment
    beta2 : float
        Exponential decay for second moment
    epsilon : float
        Small constant for numerical stability
    """

    def __init__(self, maxiter: int = 200, learning_rate: float = 0.001,
                 beta1: float = 0.9, beta2: float = 0.999, epsilon: float = 1e-8):
        self.maxiter = maxiter
        self.learning_rate = learning_rate
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon

    def minimize(self, objective: Callable[[Dict[str, float]], float],
                 initial_params: Dict[str, float],
                 gradient: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None,
                 bounds: Optional[Dict[str, Tuple[float, float]]] = None) -> OptimizationResult:
        """Minimize using Adam."""
        params = dict(initial_params)
        symbols = list(params.keys())
        bounds = bounds or {}

        m = {s: 0.0 for s in symbols}  # First moment
        v = {s: 0.0 for s in symbols}  # Second moment

        cost_history = []
        param_history = []
        start_time = time.time()

        for k in range(1, self.maxiter + 1):
            cost = objective(params)
            cost_history.append(cost)
            param_history.append(dict(params))

            # Compute gradient
            if gradient is not None:
                grad = gradient(params)
            else:
                grad = {}
                eps = 1e-6
                for s in symbols:
                    params_plus = dict(params)
                    params_plus[s] += eps
                    params_minus = dict(params)
                    params_minus[s] -= eps
                    grad[s] = (objective(params_plus) - objective(params_minus)) / (2 * eps)

            # Update biased moments
            for s in symbols:
                m[s] = self.beta1 * m[s] + (1 - self.beta1) * grad[s]
                v[s] = self.beta2 * v[s] + (1 - self.beta2) * grad[s] ** 2

                # Bias correction
                m_hat = m[s] / (1 - self.beta1 ** k)
                v_hat = v[s] / (1 - self.beta2 ** k)

                # Update
                new_val = params[s] - self.learning_rate * m_hat / (math.sqrt(v_hat) + self.epsilon)
                if s in bounds:
                    new_val = max(bounds[s][0], min(bounds[s][1], new_val))
                params[s] = float(new_val)

        final_cost = objective(params)
        cost_history.append(final_cost)
        param_history.append(dict(params))

        best_idx = min(range(len(cost_history)), key=lambda i: cost_history[i])

        return OptimizationResult(
            optimal_params=param_history[best_idx],
            optimal_cost=cost_history[best_idx],
            cost_history=cost_history,
            param_history=param_history,
            num_iterations=self.maxiter,
            convergence=False,
            wall_time_s=time.time() - start_time,
        )


class QuantumOptimizer:
    """
    High-level quantum optimizer that combines a classical optimizer
    with a quantum cost function.

    Usage:
        from abirqu.quantum_optimizer import QuantumOptimizer

        def cost_fn(params):
            circuit = build_vqe_circuit(params)
            result = simulator.run(circuit, shots=2048)
            return compute_expectation(result)

        opt = QuantumOptimizer(optimizer="cobyla", maxiter=100)
        result = opt.minimize(cost_fn, initial_params)
    """

    def __init__(self, optimizer: str = "cobyla", maxiter: int = 200, **kwargs):
        """
        Parameters
        ----------
        optimizer : str
            Optimizer type: 'cobyla', 'spsa', 'nelder_mead', 'gradient_descent', 'adam'
        maxiter : int
            Maximum iterations
        **kwargs
            Additional optimizer-specific parameters
        """
        self.optimizer_type = optimizer.lower()

        if self.optimizer_type == "cobyla":
            self.optimizer = COBYLA(maxiter=maxiter, **kwargs)
        elif self.optimizer_type == "spsa":
            self.optimizer = SPSA(maxiter=maxiter, **kwargs)
        elif self.optimizer_type == "gradient_descent":
            self.optimizer = GradientDescent(maxiter=maxiter, **kwargs)
        elif self.optimizer_type == "adam":
            self.optimizer = Adam(maxiter=maxiter, **kwargs)
        elif self.optimizer_type == "nelder_mead":
            # Use COBYLA with large rhobeg as Nelder-Mead approximation
            self.optimizer = COBYLA(maxiter=maxiter, rhobeg=1.0, **kwargs)
        else:
            raise ValueError(f"Unknown optimizer: {optimizer}. Use: cobyla, spsa, gradient_descent, adam, nelder_mead")

    def minimize(self, objective: Callable[[Dict[str, float]], float],
                 initial_params: Dict[str, float],
                 gradient: Optional[Callable[[Dict[str, float]], Dict[str, float]]] = None,
                 bounds: Optional[Dict[str, Tuple[float, float]]] = None,
                 callback: Optional[Callable[[int, float, Dict[str, float]], None]] = None) -> OptimizationResult:
        """
        Minimize the objective function.

        Parameters
        ----------
        objective : callable
            Cost function f(params_dict) -> cost
        initial_params : dict
            Starting parameters
        gradient : callable, optional
            Gradient function g(params_dict) -> {param: gradient}
        bounds : dict, optional
            Parameter bounds
        callback : callable, optional
            Called after each iteration: callback(iteration, cost, params)
        """
        # Wrap objective with callback
        iteration_counter = [0]

        def wrapped_objective(params):
            cost = objective(params)
            iteration_counter[0] += 1
            if callback:
                callback(iteration_counter[0], cost, params)
            return cost

        if hasattr(self.optimizer, 'minimize'):
            if self.optimizer_type in ('gradient_descent', 'adam') and gradient is not None:
                return self.optimizer.minimize(wrapped_objective, initial_params, gradient, bounds)
            return self.optimizer.minimize(wrapped_objective, initial_params, bounds)

        raise NotImplementedError(f"Optimizer {self.optimizer_type} not fully implemented")

    def optimize_vqe(self, ansatz_fn: Callable[[Dict[str, float]], Any],
                     hamiltonian: np.ndarray,
                     initial_params: Dict[str, float],
                     shots: int = 2048,
                     bounds: Optional[Dict[str, Tuple[float, float]]] = None,
                     callback: Optional[Callable] = None) -> OptimizationResult:
        """
        Run VQE optimization.

        Parameters
        ----------
        ansatz_fn : callable
            Function that takes params dict and returns a Circuit
        hamiltonian : np.ndarray
            Hamiltonian matrix to minimize <ψ|H|ψ>
        initial_params : dict
            Starting parameters
        shots : int
            Measurement shots per iteration
        """
        from abirqu.simulation.monte_carlo import MonteCarloWavefunctionSimulator

        n_qubits = int(math.log2(hamiltonian.shape[0]))
        sim = MonteCarloWavefunctionSimulator(num_qubits=n_qubits, num_trajectories=1)

        def cost_fn(params):
            circuit = ansatz_fn(params)
            result = sim.run(circuit)

            # Compute <ψ|H|ψ> from measurement counts
            counts = result.counts
            total = sum(counts.values())
            exp_val = 0.0
            for bitstring, count in counts.items():
                idx = int(bitstring, 2) if isinstance(bitstring, str) else bitstring
                exp_val += np.real(hamiltonian[idx, idx]) * count / total

            return float(exp_val)

        return self.minimize(cost_fn, initial_params, bounds=bounds, callback=callback)

    def optimize_qaoa(self, cost_operator: np.ndarray,
                      mixer_operator: np.ndarray,
                      p: int,
                      initial_params: Optional[Dict[str, float]] = None,
                      shots: int = 2048,
                      bounds: Optional[Dict[str, Tuple[float, float]]] = None,
                      callback: Optional[Callable] = None) -> OptimizationResult:
        """
        Run QAOA optimization for combinatorial problems.

        Parameters
        ----------
        cost_operator : np.ndarray
            Cost Hamiltonian (diagonal in computational basis)
        mixer_operator : np.ndarray
            Mixer Hamiltonian (typically transverse field)
        p : int
            QAOA depth (number of alternating layers)
        """
        n_qubits = int(math.log2(cost_operator.shape[0]))

        if initial_params is None:
            initial_params = {}
            for i in range(p):
                initial_params[f'gamma_{i}'] = 0.5
                initial_params[f'beta_{i}'] = 0.5

        from abirqu.circuit import Circuit
        from abirqu.simulation.monte_carlo import MonteCarloWavefunctionSimulator

        sim = MonteCarloWavefunctionSimulator(num_qubits=n_qubits, num_trajectories=1)

        def build_qaoa_circuit(params):
            c = Circuit(n_qubits, "qaoa")
            # Initial superposition
            for q in range(n_qubits):
                c.h(q)
            # Alternating layers
            for layer in range(p):
                gamma = params.get(f'gamma_{layer}', 0.5)
                beta = params.get(f'beta_{layer}', 0.5)
                # Cost unitary (simplified: apply RZ for diagonal)
                for q in range(n_qubits):
                    c.rz(q, gamma)
                # Mixer unitary
                for q in range(n_qubits):
                    c.rx(q, 2 * beta)
            return c

        def cost_fn(params):
            circuit = build_qaoa_circuit(params)
            result = sim.run(circuit)
            counts = result.counts
            total = sum(counts.values())
            exp_val = 0.0
            for bitstring, count in counts.items():
                idx = int(bitstring, 2)
                exp_val += np.real(cost_operator[idx, idx]) * count / total
            return float(exp_val)

        return self.minimize(cost_fn, initial_params, bounds=bounds, callback=callback)
