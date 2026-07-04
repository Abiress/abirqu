"""
Quantum Physics-Informed Neural Networks (Q-PINNs).

Hybrid quantum-classical framework for solving non-linear differential equations
using parameterized quantum circuits as function approximators.

Q-PINNs combine:
1. Physics-Informed Neural Networks (PINNs): Enforce PDE constraints via loss terms
2. Quantum Circuits: Provide expressive function approximation with potential
   quantum advantage in training

Applications:
- Navier-Stokes equations (aerodynamics, fluid dynamics)
- Schrödinger equation (quantum mechanics)
- Maxwell's equations (electromagnetics)
- Wave equations (acoustics, seismology)

The quantum circuit acts as a universal function approximator:
    u(x, t) = ⟨0|U(θ)† O(x, t) U(θ)|0⟩

Where U(θ) is the parameterized circuit and O(x, t) encodes the input.

References:
    - Raissi et al. (2019): Physics-informed neural networks
    - Lubasch et al. (2020): Tensor network machine learning for differential equations
    - Jeremiah et al. (2022): Quantum algorithm for non-linear PDEs
"""

import math
from typing import List, Tuple, Dict, Optional, Callable
from dataclasses import dataclass

import numpy as np

from .circuit import Circuit, Gate


def adam_optimizer(loss_fn, initial_params, lr=0.01, n_iters=100):
    """Simple Adam optimizer for numpy arrays."""
    params = initial_params.copy()
    m = np.zeros_like(params)
    v = np.zeros_like(params)
    beta1, beta2, epsilon = 0.9, 0.999, 1e-8
    loss_history = []

    for t in range(1, n_iters + 1):
        loss = loss_fn(params)
        loss_history.append(float(loss))

        # Numerical gradient
        grad = np.zeros_like(params)
        eps = 1e-5
        for i in range(len(params)):
            params_plus = params.copy()
            params_plus[i] += eps
            params_minus = params.copy()
            params_minus[i] -= eps
            grad[i] = (loss_fn(params_plus) - loss_fn(params_minus)) / (2 * eps)

        # Adam update
        m = beta1 * m + (1 - beta1) * grad
        v = beta2 * v + (1 - beta2) * grad ** 2
        m_hat = m / (1 - beta1 ** t)
        v_hat = v / (1 - beta2 ** t)
        params = params - lr * m_hat / (np.sqrt(v_hat) + epsilon)

    return params, loss_history


@dataclass
class PDESpec:
    """Specification for a partial differential equation."""
    name: str
    dimension: int  # Spatial dimensions
    domain: List[Tuple[float, float]]  # Domain bounds for each dimension
    time_domain: Optional[Tuple[float, float]] = None  # Time bounds if time-dependent
    boundary_conditions: str = "dirichlet"  # "dirichlet", "neumann", "periodic"
    initial_condition: Optional[Callable] = None


@dataclass
class TrainingConfig:
    """Configuration for Q-PINN training."""
    n_epochs: int = 1000
    learning_rate: float = 0.01
    n_collocation_points: int = 1000
    n_boundary_points: int = 100
    n_initial_points: int = 100
    weight_pde: float = 1.0
    weight_bc: float = 10.0
    weight_ic: float = 10.0
    batch_size: int = 32
    convergence_tol: float = 1e-6


class QPINN:
    """
    Quantum Physics-Informed Neural Network.

    Uses a parameterized quantum circuit as the function approximator
    for solving PDEs. The circuit parameters are optimized to minimize
    the PDE residual loss.
    """

    def __init__(
        self,
        pde: PDESpec,
        n_qubits: int = 4,
        circuit_depth: int = 3,
        config: Optional[TrainingConfig] = None,
    ):
        """
        Initialize Q-PINN.

        Args:
            pde: PDE specification
            n_qubits: Number of qubits for the quantum circuit
            circuit_depth: Depth of the parameterized circuit
            config: Training configuration
        """
        self.pde = pde
        self.n_qubits = n_qubits
        self.circuit_depth = circuit_depth
        self.config = config or TrainingConfig()

        # Number of parameters: depth * n_qubits (rotation angles) + entangling params
        self.n_parameters = circuit_depth * n_qubits * 3  # 3 rotation axes per gate

        # Training state
        self.parameters: Optional[np.ndarray] = None
        self.loss_history: List[float] = []

    def _build_ansatz_circuit(
        self,
        parameters: np.ndarray,
        inputs: np.ndarray,
    ) -> Circuit:
        """
        Build the parameterized quantum circuit.

        Uses a hardware-efficient ansatz:
        1. Input encoding layer (angle encoding of x, t)
        2. Parameterized rotation layers (RY, RZ)
        3. Entangling layers (CNOT)
        4. Measurement

        Args:
            parameters: Circuit parameters θ
            inputs: Input values [x_1, ..., x_d, t]

        Returns:
            Parameterized circuit
        """
        circ = Circuit(self.n_qubits, "QPINN-Ansatz")

        # Layer 1: Input encoding
        for i in range(min(len(inputs), self.n_qubits)):
            circ.ry(i, inputs[i] * np.pi)  # Scale inputs to [0, π]

        # Layer 2: Parameterized rotation + entangling layers
        param_idx = 0
        for layer in range(self.circuit_depth):
            # Rotation layer
            for q in range(self.n_qubits):
                if param_idx < len(parameters):
                    circ.rx(q, parameters[param_idx])
                    param_idx += 1
                if param_idx < len(parameters):
                    circ.ry(q, parameters[param_idx])
                    param_idx += 1
                if param_idx < len(parameters):
                    circ.rz(q, parameters[param_idx])
                    param_idx += 1

            # Entangling layer (linear connectivity)
            for q in range(self.n_qubits - 1):
                circ.cnot(q, q + 1)

        return circ

    def forward(
        self,
        parameters: np.ndarray,
        inputs: np.ndarray,
    ) -> float:
        """
        Forward pass: evaluate the Q-PINN at given inputs.

        Computes ⟨0|U(θ)† O(x) U(θ)|0⟩ as the function value.

        Args:
            parameters: Circuit parameters
            inputs: Input coordinates [x, t]

        Returns:
            Function value u(x, t)
        """
        # Build circuit
        circ = self._build_ansatz_circuit(parameters, inputs)

        # Simulate the circuit to get expectation value
        # <Z_0> as the function output
        expectation = self._simulate_expectation(circ)

        return float(expectation)

    def _simulate_expectation(self, circ: Circuit) -> float:
        """
        Simulate the circuit and compute ⟨Z_0⟩.

        Uses classical statevector simulation.
        """
        n = circ.num_qubits
        dim = 2 ** n

        # Initialize state
        state = np.zeros(dim, dtype=complex)
        state[0] = 1.0

        # Apply gates (simplified simulation)
        for gate in circ.gates:
            if gate.name == 'H':
                self._apply_h(state, gate.qubits[0], n)
            elif gate.name == 'X':
                self._apply_x(state, gate.qubits[0], n)
            elif gate.name == 'RY':
                self._apply_ry(state, gate.qubits[0], gate.params[0], n)
            elif gate.name == 'RX':
                self._apply_rx(state, gate.qubits[0], gate.params[0], n)
            elif gate.name == 'RZ':
                self._apply_rz(state, gate.qubits[0], gate.params[0], n)
            elif gate.name == 'CNOT':
                self._apply_cnot(state, gate.qubits[0], gate.qubits[1], n)
            elif gate.name == 'CZ':
                self._apply_cz(state, gate.qubits[0], gate.qubits[1], n)

        # Compute <Z_0> = Σ_i |α_i|^2 (1 if bit 0 of i is 0, -1 if 1)
        expectation = 0.0
        for i in range(dim):
            prob = abs(state[i]) ** 2
            if (i & 1) == 0:  # Bit 0 is 0
                expectation += prob
            else:  # Bit 0 is 1
                expectation -= prob

        return expectation

    def _apply_h(self, state: np.ndarray, qubit: int, n_qubits: int):
        """Apply Hadamard gate."""
        dim = 2 ** n_qubits
        step = 2 ** qubit
        for i in range(0, dim, 2 * step):
            for j in range(i, i + step):
                a, b = state[j], state[j + step]
                state[j] = (a + b) / np.sqrt(2)
                state[j + step] = (a - b) / np.sqrt(2)

    def _apply_x(self, state: np.ndarray, qubit: int, n_qubits: int):
        """Apply X (NOT) gate."""
        dim = 2 ** n_qubits
        step = 2 ** qubit
        for i in range(0, dim, 2 * step):
            for j in range(i, i + step):
                state[j], state[j + step] = state[j + step], state[j]

    def _apply_ry(self, state: np.ndarray, qubit: int, theta: float, n_qubits: int):
        """Apply RY rotation."""
        dim = 2 ** n_qubits
        step = 2 ** qubit
        c, s = np.cos(theta / 2), np.sin(theta / 2)
        for i in range(0, dim, 2 * step):
            for j in range(i, i + step):
                a, b = state[j], state[j + step]
                state[j] = c * a - s * b
                state[j + step] = s * a + c * b

    def _apply_rx(self, state: np.ndarray, qubit: int, theta: float, n_qubits: int):
        """Apply RX rotation."""
        dim = 2 ** n_qubits
        step = 2 ** qubit
        c, s = np.cos(theta / 2), -1j * np.sin(theta / 2)
        for i in range(0, dim, 2 * step):
            for j in range(i, i + step):
                a, b = state[j], state[j + step]
                state[j] = c * a + s * b
                state[j + step] = s * a + c * b

    def _apply_rz(self, state: np.ndarray, qubit: int, theta: float, n_qubits: int):
        """Apply RZ rotation."""
        dim = 2 ** n_qubits
        step = 2 ** qubit
        for i in range(0, dim, 2 * step):
            for j in range(i, i + step):
                if (j >> qubit) & 1 == 0:
                    state[j] *= np.exp(-1j * theta / 2)
                else:
                    state[j] *= np.exp(1j * theta / 2)

    def _apply_cnot(self, state: np.ndarray, control: int, target: int, n_qubits: int):
        """Apply CNOT gate."""
        dim = 2 ** n_qubits
        for i in range(dim):
            if (i >> control) & 1 == 1:  # Control is |1⟩
                j = i ^ (1 << target)  # Flip target
                if i < j:
                    state[i], state[j] = state[j], state[i]

    def _apply_cz(self, state: np.ndarray, qubit1: int, qubit2: int, n_qubits: int):
        """Apply CZ gate."""
        dim = 2 ** n_qubits
        for i in range(dim):
            if ((i >> qubit1) & 1) == 1 and ((i >> qubit2) & 1) == 1:
                state[i] *= -1

    def pde_residual(
        self,
        parameters: np.ndarray,
        x: float,
        t: float,
    ) -> float:
        """
        Compute the PDE residual at a point.

        For the diffusion equation ∂u/∂t = ν∂²u/∂x²:
            residual = ∂u/∂t - ν∂²u/∂x²

        Uses finite differences for derivatives.
        """
        h = 1e-5

        # Compute derivatives via finite differences
        u = self.forward(parameters, np.array([x, t]))
        u_t = (self.forward(parameters, np.array([x, t + h])) - u) / h
        u_x = (self.forward(parameters, np.array([x + h, t])) -
               self.forward(parameters, np.array([x - h, t]))) / (2 * h)
        u_xx = (self.forward(parameters, np.array([x + h, t])) -
                2 * u +
                self.forward(parameters, np.array([x - h, t]))) / (h ** 2)

        # Diffusion equation: ∂u/∂t = ν∂²u/∂x²
        viscosity = 0.01
        residual = u_t - viscosity * u_xx

        return float(residual)

    def compute_loss(
        self,
        parameters: np.ndarray,
        collocation_points: np.ndarray,
        boundary_points: np.ndarray,
        initial_points: np.ndarray,
        initial_values: np.ndarray,
    ) -> float:
        """
        Compute the total loss.

        Loss = L_pde + L_bc + L_ic

        L_pde: PDE residual loss at collocation points
        L_bc: Boundary condition loss
        L_ic: Initial condition loss
        """
        # PDE residual loss
        pde_loss = 0.0
        for pt in collocation_points:
            residual = self.pde_residual(parameters, pt[0], pt[1])
            pde_loss += residual ** 2
        pde_loss /= len(collocation_points)

        # Boundary condition loss (Dirichlet: u = 0 at boundaries)
        bc_loss = 0.0
        for pt in boundary_points:
            u_val = self.forward(parameters, pt)
            bc_loss += u_val ** 2  # u = 0 at boundaries
        bc_loss /= max(len(boundary_points), 1)

        # Initial condition loss
        ic_loss = 0.0
        for i, pt in enumerate(initial_points):
            u_val = self.forward(parameters, pt)
            target = initial_values[i] if i < len(initial_values) else 0.0
            ic_loss += (u_val - target) ** 2
        ic_loss /= max(len(initial_points), 1)

        total_loss = (
            self.config.weight_pde * pde_loss +
            self.config.weight_bc * bc_loss +
            self.config.weight_ic * ic_loss
        )

        return float(total_loss)

    def train(
        self,
        initial_parameters: Optional[np.ndarray] = None,
        callback: Optional[Callable] = None,
    ) -> Dict:
        """
        Train the Q-PINN.

        Args:
            initial_parameters: Starting parameters. If None, random initialization.
            callback: Optional callback function(parameters, loss, epoch)

        Returns:
            Training results dictionary
        """
        if initial_parameters is None:
            self.parameters = np.random.uniform(
                -np.pi, np.pi, self.n_parameters
            )
        else:
            self.parameters = initial_parameters.copy()

        # Generate training points
        collocation_pts = self._generate_collocation_points()
        boundary_pts = self._generate_boundary_points()
        initial_pts = self._generate_initial_points()
        initial_vals = self._evaluate_initial_condition(initial_pts)

        # Training loop with Adam optimizer
        def loss_fn(params):
            return self.compute_loss(
                params, collocation_pts, boundary_pts, initial_pts, initial_vals
            )

        self.parameters, self.loss_history = adam_optimizer(
            loss_fn, self.parameters,
            lr=self.config.learning_rate,
            n_iters=self.config.n_epochs,
        )

        if callback:
            callback(self.parameters, self.loss_history[-1], len(self.loss_history))

        return {
            "parameters": self.parameters,
            "final_loss": self.loss_history[-1],
            "loss_history": self.loss_history,
            "n_epochs": len(self.loss_history),
        }

    def predict(self, x: np.ndarray, t: float) -> np.ndarray:
        """
        Predict solution at given spatial points and time.

        Args:
            x: Spatial coordinates
            t: Time value

        Returns:
            Solution values u(x, t)
        """
        if self.parameters is None:
            raise ValueError("Model not trained. Call train() first.")

        results = np.zeros(len(x))
        for i, xi in enumerate(x):
            results[i] = self.forward(self.parameters, np.array([xi, t]))

        return results

    def _generate_collocation_points(self) -> np.ndarray:
        """Generate random collocation points in the domain."""
        x_min, x_max = self.pde.domain[0]
        t_min, t_max = self.pde.time_domain or (0.0, 1.0)

        x = np.random.uniform(x_min, x_max, self.config.n_collocation_points)
        t = np.random.uniform(t_min, t_max, self.config.n_collocation_points)

        return np.column_stack([x, t])

    def _generate_boundary_points(self) -> np.ndarray:
        """Generate boundary points."""
        x_min, x_max = self.pde.domain[0]
        t_min, t_max = self.pde.time_domain or (0.0, 1.0)

        points = []
        # Left and right boundaries
        for _ in range(self.config.n_boundary_points // 2):
            t = np.random.uniform(t_min, t_max)
            points.append([x_min, t])
            points.append([x_max, t])

        return np.array(points[:self.config.n_boundary_points])

    def _generate_initial_points(self) -> np.ndarray:
        """Generate initial condition points."""
        x_min, x_max = self.pde.domain[0]
        t_min = self.pde.time_domain[0] if self.pde.time_domain else 0.0

        x = np.random.uniform(x_min, x_max, self.config.n_initial_points)
        t = np.full_like(x, t_min)

        return np.column_stack([x, t])

    def _evaluate_initial_condition(self, points: np.ndarray) -> np.ndarray:
        """Evaluate the initial condition at given points."""
        if self.pde.initial_condition is not None:
            return np.array([self.pde.initial_condition(p[0]) for p in points])

        # Default: Gaussian initial condition
        return np.exp(-((points[:, 0] - 0.5) ** 2) / 0.01)


class NavierStokesQPINN(QPINN):
    """
    Q-PINN specialized for the Navier-Stokes equations.

    Incompressible Navier-Stokes:
        ∂u/∂t + u·∇u = -∇p + ν∇²u
        ∇·u = 0

    Uses the vorticity-streamfunction formulation for 2D flows.
    """

    def __init__(
        self,
        reynolds_number: float = 100.0,
        n_qubits: int = 6,
        circuit_depth: int = 4,
        config: Optional[TrainingConfig] = None,
    ):
        pde = PDESpec(
            name="Navier-Stokes (2D)",
            dimension=2,
            domain=[(0.0, 1.0), (0.0, 1.0)],
            time_domain=(0.0, 1.0),
            boundary_conditions="dirichlet",
        )
        super().__init__(pde, n_qubits, circuit_depth, config)
        self.reynolds_number = reynolds_number
        self.viscosity = 1.0 / reynolds_number

    def vorticity_residual(
        self,
        parameters: np.ndarray,
        x: float,
        y: float,
        t: float,
    ) -> float:
        """
        Compute vorticity equation residual.

        ∂ω/∂t + u·∇ω = ν∇²ω

        Where ω = ∂v/∂x - ∂u/∂y is the vorticity.
        """
        h = 1e-5

        # Velocity components from streamfunction
        psi = self.forward(parameters, np.array([x, y, t]))
        psi_x = (self.forward(parameters, np.array([x + h, y, t])) -
                 self.forward(parameters, np.array([x - h, y, t]))) / (2 * h)
        psi_y = (self.forward(parameters, np.array([x, y + h, t])) -
                 self.forward(parameters, np.array([x, y - h, t]))) / (2 * h)

        # Vorticity
        omega = psi_x  # Simplified: ω ≈ ∂²ψ/∂x² + ∂²ψ/∂y²

        # Time derivative
        omega_t = (self.forward(parameters, np.array([x, y, t + h])) -
                   self.forward(parameters, np.array([x, y, t]))) / h

        # Advection term
        omega_x = (self.forward(parameters, np.array([x + h, y, t])) -
                   self.forward(parameters, np.array([x - h, y, t]))) / (2 * h)
        omega_y = (self.forward(parameters, np.array([x, y + h, t])) -
                   self.forward(parameters, np.array([x, y - h, t]))) / (2 * h)

        advection = psi_y * omega_x - psi_x * omega_y

        # Diffusion term
        omega_xx = (self.forward(parameters, np.array([x + h, y, t])) -
                    2 * self.forward(parameters, np.array([x, y, t])) +
                    self.forward(parameters, np.array([x - h, y, t]))) / (h ** 2)
        omega_yy = (self.forward(parameters, np.array([x, y + h, t])) -
                    2 * self.forward(parameters, np.array([x, y, t])) +
                    self.forward(parameters, np.array([x, y - h, t]))) / (h ** 2)

        diffusion = self.viscosity * (omega_xx + omega_yy)

        return omega_t + advection - diffusion
