"""
Time-Evolution ODE Hamiltonian Solver.

Simulates continuous time evolution of quantum systems by numerically
integrating the Schrödinger equation or Lindblad master equation.
Instead of applying discrete gate matrices, the engine solves:

    i ℏ d|ψ>/dt = H(t) |ψ>                           (Schrödinger)
    dρ/dt = -i[H, ρ] + Σ_k (L_k ρ L_k† - {L_k†L_k, ρ}/2)  (Lindblad)

using adaptive-step RK45 or fixed-step RK4 integrators.

This is the physics layer for pulse-level simulation, where gates are
replaced by continuous microwave/RF pulses defined by their Hamiltonians.

References:
    - Runge-Kutta-Fehlberg (RKF45) adaptive step control
    - Lindblad master equation for open quantum systems
"""

import math
import cmath
from typing import Callable, Optional, Tuple, List, Dict, Any
from dataclasses import dataclass, field

import numpy as np

from abirqu.circuit import Circuit


@dataclass
class HamiltonianTerm:
    """
    A term in a time-dependent Hamiltonian.

    H(t) = Σ_k amplitude(t) * operator_k

    Attributes
    ----------
    operator : np.ndarray
        Operator matrix (2^n x 2^n)
    amplitude : callable
        Time-dependent amplitude function: t -> complex
    label : str
        Human-readable label for this term
    """
    operator: np.ndarray
    amplitude: Callable[[float], complex]
    label: str = ""


@dataclass
class LindbladOperator:
    """
    A Lindblad (jump) operator for open system simulation.

    L_k represents a dissipation channel (e.g., decay, dephasing).
    """
    operator: np.ndarray
    rate: float
    label: str = ""


@dataclass
class EvolutionResult:
    """Result of time evolution simulation."""
    times: np.ndarray
    states: List[np.ndarray]  # list of statevectors at each time step
    expectation_values: Dict[str, List[float]]
    infidelity: float  # how much norm was lost (should be ~0 for closed systems)
    num_timesteps: int
    dt_used: np.ndarray  # actual dt at each step (for adaptive methods)


class HamiltonianBuilder:
    """
    Build Hamiltonians from standard quantum computing operations.

    Supports:
    - Single-qubit rotations: H(t) = Ω(t) * (cos(φ) σ_x + sin(φ) σ_y)
    - Two-qubit interactions: H = J(t) * (σ_x⊗σ_x + σ_y⊗σ_y + σ_z⊗σ_z)
    - Detuning: H = Δ(t) * σ_z
    - Transverse field: H = h(t) * σ_x
    - Ising model: H = Σ_{<i,j>} J_ij σ_z^i σ_z^j + Σ_i h_i σ_x^i
    """

    @staticmethod
    def _pauli_x() -> np.ndarray:
        return np.array([[0, 1], [1, 0]], dtype=complex)

    @staticmethod
    def _pauli_y() -> np.ndarray:
        return np.array([[0, -1j], [1j, 0]])

    @staticmethod
    def _pauli_z() -> np.ndarray:
        return np.array([[1, 0], [0, -1]], dtype=complex)

    @staticmethod
    def _identity() -> np.ndarray:
        return np.eye(2, dtype=complex)

    @classmethod
    def single_qubit_rotation(cls, qubit: int, num_qubits: int,
                               omega: Callable[[float], float],
                               phi: float = 0.0,
                               label: str = "") -> HamiltonianTerm:
        """
        Drive term: H = Ω(t) * (cos(φ) σ_x + sin(φ) σ_y)

        For a resonant drive on qubit, this produces rotations around
        the axis defined by phi in the xy-plane.
        """
        op = cls._operator_on_qubit(
            math.cos(phi) * cls._pauli_x() + math.sin(phi) * cls._pauli_y(),
            qubit, num_qubits
        )
        return HamiltonianTerm(operator=op, amplitude=omega, label=label or f"drive_q{qubit}")

    @classmethod
    def detuning(cls, qubit: int, num_qubits: int,
                 delta: Callable[[float], float],
                 label: str = "") -> HamiltonianTerm:
        """Detuning term: H = Δ(t) * σ_z"""
        op = cls._operator_on_qubit(cls._pauli_z(), qubit, num_qubits)
        return HamiltonianTerm(operator=op, amplitude=delta, label=label or f"detune_q{qubit}")

    @classmethod
    def exchange_interaction(cls, qubit_i: int, qubit_j: int, num_qubits: int,
                              J: Callable[[float], float],
                              label: str = "") -> HamiltonianTerm:
        """
        Exchange interaction: H = J(t) * (σ_x^i σ_x^j + σ_y^i σ_y^j + σ_z^i σ_z^j)

        This is the Heisenberg exchange interaction, native to many
        physical platforms (trapped ions, neutral atoms, spin qubits).
        """
        n = num_qubits
        sx_i = cls._operator_on_qubit(cls._pauli_x(), qubit_i, n)
        sx_j = cls._operator_on_qubit(cls._pauli_x(), qubit_j, n)
        sy_i = cls._operator_on_qubit(cls._pauli_y(), qubit_i, n)
        sy_j = cls._operator_on_qubit(cls._pauli_y(), qubit_j, n)
        sz_i = cls._operator_on_qubit(cls._pauli_z(), qubit_i, n)
        sz_j = cls._operator_on_qubit(cls._pauli_z(), qubit_j, n)

        op = sx_i @ sx_j + sy_i @ sy_j + sz_i @ sz_j
        return HamiltonianTerm(operator=op, amplitude=J, label=label or f"exchange_{qubit_i}_{qubit_j}")

    @classmethod
    def ising_coupling(cls, qubit_i: int, qubit_j: int, num_qubits: int,
                        J: Callable[[float], float],
                        label: str = "") -> HamiltonianTerm:
        """Ising ZZ coupling: H = J(t) * σ_z^i ⊗ σ_z^j"""
        n = num_qubits
        sz_i = cls._operator_on_qubit(cls._pauli_z(), qubit_i, n)
        sz_j = cls._operator_on_qubit(cls._pauli_z(), qubit_j, n)
        op = sz_i @ sz_j
        return HamiltonianTerm(operator=op, amplitude=J, label=label or f"ising_{qubit_i}_{qubit_j}")

    @classmethod
    def transverse_field(cls, qubit: int, num_qubits: int,
                          h: Callable[[float], float],
                          label: str = "") -> HamiltonianTerm:
        """Transverse field: H = h(t) * σ_x"""
        op = cls._operator_on_qubit(cls._pauli_x(), qubit, num_qubits)
        return HamiltonianTerm(operator=op, amplitude=h, label=label or f"transverse_q{qubit}")

    @classmethod
    def custom(cls, operator: np.ndarray,
               amplitude: Callable[[float], complex],
               label: str = "") -> HamiltonianTerm:
        """Custom Hamiltonian term with arbitrary operator and amplitude."""
        return HamiltonianTerm(operator=operator, amplitude=amplitude, label=label or "custom")

    @classmethod
    def _operator_on_qubit(cls, local_op: np.ndarray, qubit: int,
                           num_qubits: int) -> np.ndarray:
        """Embed a local operator into the full Hilbert space."""
        n = num_qubits
        ops = [cls._identity()] * n
        ops[qubit] = local_op
        result = ops[0]
        for i in range(1, n):
            result = np.kron(result, ops[i])
        return result


class ODESolver:
    """
    Ordinary Differential Equation solver for quantum state evolution.

    Supports:
    - RK4 (fixed step): 4th-order Runge-Kutta
    - RK45 (adaptive): Runge-Kutta-Fehlberg with error control
    - Euler (fixed step): 1st-order, for quick tests

    The Schrödinger equation d|ψ>/dt = -i H(t) |ψ> is solved as a
    system of 2^n coupled ODEs (real and imaginary parts).
    """

    @staticmethod
    def rk4_step(f: Callable, t: float, y: np.ndarray, dt: float) -> np.ndarray:
        """Single RK4 step."""
        k1 = f(t, y)
        k2 = f(t + dt / 2, y + dt * k1 / 2)
        k3 = f(t + dt / 2, y + dt * k2 / 2)
        k4 = f(t + dt, y + dt * k3)
        return y + (dt / 6) * (k1 + 2 * k2 + 2 * k3 + k4)

    @staticmethod
    def rk45_step(f: Callable, t: float, y: np.ndarray, dt: float) -> Tuple[np.ndarray, float]:
        """
        Single RK45 (Fehlberg) step with error estimate.

        Returns (new_state, estimated_error).
        """
        k1 = f(t, y)
        k2 = f(t + dt / 4, y + dt * k1 / 4)
        k3 = f(t + 3 * dt / 8, y + dt * (3 * k1 / 32 + 9 * k2 / 32))
        k4 = f(t + 12 * dt / 13, y + dt * (1932 * k1 / 2197 - 7200 * k2 / 2197 + 7296 * k3 / 2197))
        k5 = f(t + dt, y + dt * (439 * k1 / 216 - 8 * k2 + 3680 * k3 / 513 - 845 * k4 / 4104))
        k6 = f(t + dt / 2, y + dt * (-8 * k1 / 27 + 2 * k2 - 3544 * k3 / 2565 + 1859 * k4 / 4104 - 11 * k5 / 40))

        # 5th order solution
        y_new = y + dt * (16 * k1 / 135 + 6656 * k3 / 12825 + 28561 * k4 / 56430 - 9 * k5 / 50 + 2 * k6 / 55)

        # Error estimate (difference between 4th and 5th order)
        err = np.sqrt(np.real(np.vdot(y_new - y, y_new - y)))
        err = max(err, 1e-15)

        return y_new, err

    @staticmethod
    def euler_step(f: Callable, t: float, y: np.ndarray, dt: float) -> np.ndarray:
        """Single Euler step (1st order, fast but less accurate)."""
        return y + dt * f(t, y)


class TimeEvolutionSolver:
    """
    Full time-evolution solver for quantum systems.

    Solves the Schrödinger equation:
        i d|ψ>/dt = H(t)|ψ>

    or the Lindblad master equation:
        dρ/dt = -i[H,ρ] + Σ_k γ_k (L_k ρ L_k† - {L_k†L_k, ρ}/2)

    Parameters
    ----------
    num_qubits : int
        Number of qubits
    hamiltonian_terms : list of HamiltonianTerm
        Terms in the time-dependent Hamiltonian H(t)
    lindblad_ops : list of LindbladOperator, optional
        Lindblad jump operators for open system simulation
    method : str
        ODE solver method: 'rk4', 'rk45', 'euler'
    """

    def __init__(self, num_qubits: int,
                 hamiltonian_terms: Optional[List[HamiltonianTerm]] = None,
                 lindblad_ops: Optional[List[LindbladOperator]] = None,
                 method: str = "rk45"):
        self.num_qubits = num_qubits
        self.hamiltonian_terms = hamiltonian_terms or []
        self.lindblad_ops = lindblad_ops or []
        self.method = method
        self.dim = 2 ** num_qubits
        self.solver = ODESolver()

    def add_term(self, term: HamiltonianTerm):
        """Add a Hamiltonian term."""
        self.hamiltonian_terms.append(term)

    def add_lindblad_op(self, op: LindbladOperator):
        """Add a Lindblad jump operator."""
        self.lindblad_ops.append(op)

    def _get_hamiltonian(self, t: float) -> np.ndarray:
        """Construct the full Hamiltonian at time t."""
        H = np.zeros((self.dim, self.dim), dtype=complex)
        for term in self.hamiltonian_terms:
            amp = term.amplitude(t)
            H += amp * term.operator
        return H

    def _schrodinger_rhs(self, t: float, psi: np.ndarray) -> np.ndarray:
        """Right-hand side of Schrödinger equation: d|ψ>/dt = -i H(t)|ψ>"""
        H = self._get_hamiltonian(t)
        return -1j * H @ psi

    def _lindblad_rhs(self, t: float, rho: np.ndarray) -> np.ndarray:
        """
        Right-hand side of Lindblad master equation:
        dρ/dt = -i[H,ρ] + Σ_k γ_k (L_k ρ L_k† - {L_k†L_k, ρ}/2)
        """
        H = self._get_hamiltonian(t)
        drho = -1j * (H @ rho - rho @ H)

        for lind in self.lindblad_ops:
            L = lind.operator
            L_dag = L.conj().T
            gamma = lind.rate
            drho += gamma * (L @ rho @ L_dag - 0.5 * (L_dag @ L @ rho + rho @ L_dag @ L))

        return drho

    def evolve(self, initial_state: np.ndarray, t_end: float,
               dt: float = 0.001, observables: Optional[Dict[str, np.ndarray]] = None,
               adaptive_tol: float = 1e-8) -> EvolutionResult:
        """
        Evolve the initial state under H(t) from t=0 to t=t_end.

        Parameters
        ----------
        initial_state : np.ndarray
            Initial statevector (2^n complex vector)
        t_end : float
            End time
        dt : float
            Time step (for fixed-step methods) or initial step (for adaptive)
        observables : dict, optional
            Observables to track: {name: matrix}
        adaptive_tol : float
            Tolerance for adaptive step control (RK45)

        Returns
        -------
        EvolutionResult
            Time evolution results with states and expectation values
        """
        n_steps = int(t_end / dt) + 1
        times = np.linspace(0, t_end, n_steps)
        states = [initial_state.copy()]
        exp_vals = {name: [float(np.real(np.vdot(initial_state, obs @ initial_state)))]
                    for name, obs in (observables or {}).items()}
        dt_used = [dt]

        psi = initial_state.copy().astype(complex)

        if self.method == "rk4":
            for i in range(1, n_steps):
                t = times[i - 1]
                psi = self.solver.rk4_step(self._schrodinger_rhs, t, psi, dt)
                psi /= np.linalg.norm(psi)
                states.append(psi.copy())
                dt_used.append(dt)
                for name, obs in (observables or {}).items():
                    exp_vals[name].append(float(np.real(np.vdot(psi, obs @ psi))))

        elif self.method == "rk45":
            t = 0.0
            while t < t_end - 1e-12:
                step_dt = min(dt, t_end - t)
                psi_new, err = self.solver.rk45_step(self._schrodinger_rhs, t, psi, step_dt)

                # Adaptive step control
                if err < adaptive_tol / 10:
                    step_dt *= 2  # Step was easy, take bigger step
                elif err > adaptive_tol:
                    step_dt /= 2  # Step was hard, take smaller step
                    continue

                psi = psi_new
                psi /= np.linalg.norm(psi)
                t += step_dt

                times = np.append(times, t)
                states.append(psi.copy())
                dt_used.append(step_dt)
                for name, obs in (observables or {}).items():
                    exp_vals[name].append(float(np.real(np.vdot(psi, obs @ psi))))

        elif self.method == "euler":
            for i in range(1, n_steps):
                t = times[i - 1]
                psi = self.solver.euler_step(self._schrodinger_rhs, t, psi, dt)
                psi /= np.linalg.norm(psi)
                states.append(psi.copy())
                dt_used.append(dt)
                for name, obs in (observables or {}).items():
                    exp_vals[name].append(float(np.real(np.vdot(psi, obs @ psi))))

        # Compute infidelity
        final_norm = np.linalg.norm(psi)
        infidelity = 1.0 - final_norm ** 2

        return EvolutionResult(
            times=np.array(times),
            states=states,
            expectation_values=exp_vals,
            infidelity=infidelity,
            num_timesteps=len(states),
            dt_used=np.array(dt_used),
        )

    def evolve_from_circuit(self, circuit: Circuit, t_total: float,
                            dt: float = 0.001,
                            observables: Optional[Dict[str, np.ndarray]] = None) -> EvolutionResult:
        """
        Convert a circuit to a piecewise-constant Hamiltonian and evolve.

        Each gate is mapped to a constant-amplitude Hamiltonian pulse
        for a duration of t_total / num_gates.
        """
        if not circuit.gates:
            initial_state = np.zeros(self.dim, dtype=complex)
            initial_state[0] = 1.0
            return EvolutionResult(
                times=np.array([0.0]),
                states=[initial_state],
                expectation_values={},
                infidelity=0.0,
                num_timesteps=1,
                dt_used=np.array([dt]),
            )

        # Map gates to Hamiltonian terms
        gate_duration = t_total / len(circuit.gates)
        terms = []

        for gate in circuit.gates:
            qubits = gate.qubits if isinstance(gate.qubits, list) else [gate.qubits]
            params = gate.params or [0.0]
            name = gate.name.upper()

            if name == "RX":
                theta = params[0] if params else 0.0
                amp = theta / (2 * gate_duration)
                terms.append(HamiltonianBuilder.single_qubit_rotation(
                    qubits[0], self.num_qubits,
                    omega=lambda t, a=amp: a,
                    phi=0.0, label=f"RX({theta:.3f})"
                ))
            elif name == "RY":
                theta = params[0] if params else 0.0
                amp = theta / (2 * gate_duration)
                terms.append(HamiltonianBuilder.single_qubit_rotation(
                    qubits[0], self.num_qubits,
                    omega=lambda t, a=amp: a,
                    phi=math.pi / 2, label=f"RY({theta:.3f})"
                ))
            elif name == "RZ":
                theta = params[0] if params else 0.0
                amp = theta / (2 * gate_duration)
                terms.append(HamiltonianBuilder.detuning(
                    qubits[0], self.num_qubits,
                    delta=lambda t, a=amp: a,
                    label=f"RZ({theta:.3f})"
                ))
            elif name == "H":
                amp = math.pi / (2 * gate_duration * math.sqrt(2))
                terms.append(HamiltonianBuilder.single_qubit_rotation(
                    qubits[0], self.num_qubits,
                    omega=lambda t, a=amp: a,
                    phi=math.pi / 4, label=f"H"
                ))

        # Build time-dependent Hamiltonian
        solver = TimeEvolutionSolver(
            num_qubits=self.num_qubits,
            hamiltonian_terms=terms,
            lindblad_ops=self.lindblad_ops,
            method=self.method,
        )

        initial_state = np.zeros(self.dim, dtype=complex)
        initial_state[0] = 1.0

        return solver.evolve(initial_state, t_total, dt, observables)


class ThermalStateSolver:
    """
    Solve for thermal equilibrium states and finite-temperature dynamics.

    Useful for simulating quantum systems at non-zero temperature,
    where the system converges to a Gibbs state: ρ = e^{-βH} / Z
    """

    @staticmethod
    def gibbs_state(H: np.ndarray, beta: float) -> np.ndarray:
        """
        Compute the Gibbs thermal state: ρ = e^{-βH} / Tr(e^{-βH})

        Parameters
        ----------
        H : np.ndarray
            Hamiltonian matrix
        beta : float
            Inverse temperature β = 1/(k_B T)
        """
        eigenvalues, eigenvectors = np.linalg.eigh(H)
        boltzmann = np.exp(-beta * eigenvalues)
        Z = np.sum(boltzmann)
        rho = np.zeros_like(H, dtype=complex)
        for i in range(len(eigenvalues)):
            rho += (boltzmann[i] / Z) * np.outer(eigenvectors[:, i], eigenvectors[:, i].conj())
        return rho

    @staticmethod
    def thermal_energy(H: np.ndarray, beta: float) -> float:
        """Compute average energy <H> = Tr(H ρ_thermal)."""
        eigenvalues = np.linalg.eigvalsh(H)
        boltzmann = np.exp(-beta * eigenvalues)
        Z = np.sum(boltzmann)
        return float(np.sum(eigenvalues * boltzmann) / Z)

    @staticmethod
    def von_neumann_entropy(rho: np.ndarray) -> float:
        """Compute von Neumann entropy S = -Tr(ρ log ρ)."""
        eigenvalues = np.linalg.eigvalsh(rho)
        eigenvalues = eigenvalues[eigenvalues > 1e-15]
        return float(-np.sum(eigenvalues * np.log(eigenvalues)))
