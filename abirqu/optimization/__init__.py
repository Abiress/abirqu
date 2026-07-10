"""
Adiabatic Quantum Computing (AQC) Module for AbirQu
====================================================

Implements adiabatic quantum computation for optimization problems.

AQC works by slowly evolving a quantum system from a known ground state
of a simple Hamiltonian H_initial to the ground state of a problem
Hamiltonian H_problem, following the adiabatic theorem.

Reference:
- Farhi, E., et al. (2001) "Quantum computation by adiabatic evolution."
  arXiv:quant-ph/0001106
- Albash, T., Lidar, D.A. (2018) "Adiabatic quantum computing."
  Rev. Mod. Phys. 90, 015002.
"""
import numpy as np
from typing import List, Optional, Callable, Tuple
from ..circuit import Circuit


class AdiabaticSchedule:
    """Defines the annealing schedule s(t) for AQC.

    Parameters
    ----------
    total_time : float
        Total annealing time T.
    n_steps : int
        Number of discrete time steps.
    schedule_type : str
        "linear", "quadratic", or "custom".
    """

    def __init__(
        self,
        total_time: float = 100.0,
        n_steps: int = 50,
        schedule_type: str = "linear",
    ):
        self.total_time = total_time
        self.n_steps = n_steps
        self.schedule_type = schedule_type

    def s(self, t: float) -> float:
        """Return s(t) ∈ [0, 1] — interpolation parameter."""
        tau = t / self.total_time
        if self.schedule_type == "linear":
            return tau
        elif self.schedule_type == "quadratic":
            return tau ** 2
        elif self.schedule_type == "cubic":
            return tau ** 3
        else:
            return tau

    def times(self) -> np.ndarray:
        """Return array of time points."""
        return np.linspace(0, self.total_time, self.n_steps + 1)


class AQCSolver:
    """Adiabatic Quantum Computing solver for optimization problems.

    Encodes a cost function as a classical Hamiltonian and finds the
    ground state via adiabatic evolution.

    Parameters
    ----------
    n_qubits : int
        Number of qubits.
    schedule : AdiabaticSchedule
        Annealing schedule.
    seed : int, optional
        Random seed for reproducibility.
    """

    def __init__(
        self,
        n_qubits: int,
        schedule: Optional[AdiabaticSchedule] = None,
        seed: Optional[int] = None,
    ):
        self.n_qubits = n_qubits
        self.schedule = schedule or AdiabaticSchedule()
        self.rng = np.random.default_rng(seed)

    def solve_ising(
        self,
        J: np.ndarray,
        h: Optional[np.ndarray] = None,
    ) -> dict:
        """Solve an Ising optimization problem.

        H_problem = Σ_{i<j} J_{ij} Z_i Z_j + Σ_i h_i Z_i

        Parameters
        ----------
        J : np.ndarray
            Coupling matrix (n_qubits × n_qubits, symmetric).
        h : np.ndarray, optional
            Local fields. If None, uses zero fields.

        Returns
        -------
        dict with keys:
            "best_config": Best bitstring found.
            "best_energy": Energy of best configuration.
            "energies": Energy at each time step.
            "schedule": The schedule used.
        """
        n = self.n_qubits
        if h is None:
            h = np.zeros(n)

        # H_initial = -Σ_i X_i (transverse field)
        # H_problem = Σ_{i<j} J_{ij} Z_i Z_j + Σ_i h_i Z_i
        # H(s) = (1-s) * H_initial + s * H_problem

        times = self.schedule.times()
        energies = []
        best_config = np.zeros(n, dtype=int)
        best_energy = float('inf')

        # Simulate adiabatic evolution via Trotterization
        # For each time step, apply evolution under H(s)
        state = self._initial_state()
        dt = self.schedule.total_time / self.schedule.n_steps

        for t in times:
            s_val = self.schedule.s(t)

            # Apply one step of evolution
            # H(s) = (1-s) * H_x + s * H_z
            # Split into X and Z parts and apply sequentially

            # Z part: H_z = Σ J_ij Z_i Z_j + Σ h_i Z_i
            # This is diagonal in the computational basis
            # Evolution under H_z adds phases
            phase_z = self._compute_z_phase(state, J, h, s_val, dt)
            state = state * np.exp(1j * phase_z)

            # X part: H_x = -Σ_i X_i
            # Apply transverse field rotation
            state = self._apply_transverse_field(state, (1 - s_val), dt)

            # Compute energy expectation
            energy = self._compute_energy(state, J, h)
            energies.append(energy)

            # Track best configuration
            probs = np.abs(state) ** 2
            best_idx = np.argmax(probs)
            if energy < best_energy:
                best_energy = energy
                best_config = np.array(
                    [(best_idx >> i) & 1 for i in range(n)], dtype=int
                )

        return {
            "best_config": best_config.tolist(),
            "best_energy": float(best_energy),
            "energies": energies,
            "schedule": self.schedule.schedule_type,
            "n_qubits": n,
        }

    def solve_maxcut(
        self,
        edges: List[Tuple[int, int]],
        weights: Optional[np.ndarray] = None,
    ) -> dict:
        """Solve Max-Cut using AQC.

        Max-Cut: partition vertices to maximize cut weight.
        H_problem = Σ_{(i,j)∈E} w_{ij} (1 - Z_i Z_j) / 2

        Parameters
        ----------
        edges : List[Tuple[int, int]]
            Edge list.
        weights : np.ndarray, optional
            Edge weights. If None, all weights are 1.

        Returns
        -------
        dict with best_config, best_cut, energies, etc.
        """
        n = self.n_qubits
        J = np.zeros((n, n))
        h = np.zeros(n)

        if weights is None:
            weights = np.ones(len(edges))

        for (i, j), w in zip(edges, weights):
            # H_problem contribution: w * (1 - Z_i Z_j)/2 = w/2 - w/2 * Z_i Z_j
            J[i][j] = -w / 2
            J[j][i] = -w / 2
            h[i] += w / 2
            h[j] += w / 2

        result = self.solve_ising(J, h)
        result["best_cut"] = self._evaluate_cut(
            result["best_config"], edges, weights
        )
        return result

    def solve_qubo(
        self,
        Q: np.ndarray,
    ) -> dict:
        """Solve a QUBO (Quadratic Unconstrained Binary Optimization) problem.

        min x^T Q x where x ∈ {0, 1}^n

        Converts to Ising: x_i = (1 + Z_i)/2

        Parameters
        ----------
        Q : np.ndarray
            n × n QUBO matrix (upper triangular).

        Returns
        -------
        dict with best_config, best_energy, etc.
        """
        n = Q.shape[0]
        J = np.zeros((n, n))
        h = np.zeros(n)

        # Convert QUBO to Ising
        for i in range(n):
            for j in range(i + 1, n):
                J[i][j] = Q[i][j] / 4
                J[j][i] = Q[i][j] / 4
            h[i] = Q[i][i] / 2 + np.sum(Q[i, :i]) / 4

        result = self.solve_ising(J, h)

        # Convert from Ising to QUBO variables
        config = np.array(result["best_config"])
        qubo_config = ((1 + 2 * config - 1) // 2).tolist()
        result["best_config"] = qubo_config

        return result

    def _initial_state(self) -> np.ndarray:
        """Create uniform superposition state |+⟩^n."""
        n = self.n_qubits
        state = np.ones(2**n, dtype=complex) / np.sqrt(2**n)
        return state

    def _compute_z_phase(
        self,
        state: np.ndarray,
        J: np.ndarray,
        h: np.ndarray,
        s: float,
        dt: float,
    ) -> np.ndarray:
        """Compute phase from Z-part of Hamiltonian."""
        n = self.n_qubits
        dim = len(state)
        phases = np.zeros(dim)

        for idx in range(dim):
            # Extract bit values
            bits = np.array([(idx >> i) & 1 for i in range(n)])
            z_vals = 1 - 2 * bits  # Map 0→+1, 1→-1

            # H_z energy
            energy = 0.0
            for i in range(n):
                for j in range(i + 1, n):
                    energy += J[i][j] * z_vals[i] * z_vals[j]
                energy += h[i] * z_vals[i]

            phases[idx] = -s * energy * dt

        return phases

    def _apply_transverse_field(
        self,
        state: np.ndarray,
        strength: float,
        dt: float,
    ) -> np.ndarray:
        """Apply transverse field evolution e^{-i dt strength H_x}.

        H_x = -Σ_i X_i, so each X_i acts as a local bit flip.
        The evolution is equivalent to applying local Hadamard-like rotations.
        """
        n = self.n_qubits
        dim = len(state)
        new_state = np.zeros_like(state)

        angle = strength * dt
        c = np.cos(angle)
        s_val = np.sin(angle)

        for idx in range(dim):
            if abs(state[idx]) < 1e-15:
                continue
            # For each qubit, apply rotation
            for q in range(n):
                partner = idx ^ (1 << q)
                # |0⟩ → cos(θ)|0⟩ + sin(θ)|1⟩
                # |1⟩ → sin(θ)|0⟩ + cos(θ)|1⟩
                bit = (idx >> q) & 1
                if bit == 0:
                    new_state[idx] += state[idx] * c
                    new_state[partner] += state[idx] * s_val
                else:
                    new_state[idx] += state[idx] * c
                    new_state[partner] += state[idx] * s_val

        return new_state

    def _compute_energy(
        self,
        state: np.ndarray,
        J: np.ndarray,
        h: np.ndarray,
    ) -> float:
        """Compute energy expectation value <H_problem>."""
        n = self.n_qubits
        dim = len(state)
        probs = np.abs(state) ** 2
        energy = 0.0

        for idx in range(dim):
            if probs[idx] < 1e-15:
                continue
            bits = np.array([(idx >> i) & 1 for i in range(n)])
            z_vals = 1 - 2 * bits

            e = 0.0
            for i in range(n):
                for j in range(i + 1, n):
                    e += J[i][j] * z_vals[i] * z_vals[j]
                e += h[i] * z_vals[i]

            energy += probs[idx] * e

        return energy

    def _evaluate_cut(
        self,
        config,
        edges: List[Tuple[int, int]],
        weights: np.ndarray,
    ) -> float:
        """Evaluate cut value for a given configuration."""
        cut = 0.0
        for (i, j), w in zip(edges, weights):
            if config[i] != config[j]:
                cut += w
        return cut
