"""
Monte Carlo Wavefunction (Quantum Jumps) Simulator.

Simulates noisy quantum systems using stochastic pure-state trajectories
instead of full density matrices. Each trajectory evolves under a non-Hermitian
Hamiltonian with random quantum jumps. Averaging over trajectories reproduces
the density matrix evolution at a fraction of the memory cost.

Memory: O(2^n) per trajectory vs O(4^n) for density matrix.
For 30 qubits: ~4 GB per trajectory vs ~1 exabyte for density matrix.

References:
    - Dalibard, Castin, Mølmer (1992): "Wave-function approach to dissipative
      quantum systems"
    - Plenio & Knight (1998): "The quantum-jump approach to dissipative dynamics"
"""

import math
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

import numpy as np

from abirqu.circuit import Circuit


@dataclass
class QuantumJump:
    """Record of a single quantum jump event."""
    time_step: int
    qubit: int
    operator: str  # 'X', 'Y', 'Z', 'amplitude_damping', 'phase_damping'
    probability: float
    post_state_norm: float


@dataclass
class TrajectoryResult:
    """Result of a single Monte Carlo trajectory."""
    trajectory_id: int
    final_state: np.ndarray  # normalized statevector
    expectation_values: Dict[str, float]
    jump_history: List[QuantumJump]
    total_jump_probability: float
    survival_probability: float


@dataclass
class MonteCarloResult:
    """Aggregated result from multiple Monte Carlo trajectories."""
    num_trajectories: int
    num_qubits: int
    averaged_expectation: Dict[str, float]
    variance: Dict[str, float]
    trajectories: List[TrajectoryResult]
    counts: Dict[str, int]
    probabilities: Dict[str, float]


class NoiseChannel:
    """
    Quantum noise channel represented as Kraus operators.

    Supports: amplitude_damping, phase_damping, depolarizing, bit_flip,
    phase_flip, thermal_relaxation.
    """

    def __init__(self, channel_type: str, **params):
        self.channel_type = channel_type
        self.params = params
        self._kraus_ops = self._build_kraus_ops()

    def _build_kraus_ops(self) -> List[Tuple[np.ndarray, float]]:
        """Build Kraus operators and their probabilities for Monte Carlo sampling."""
        if self.channel_type == "amplitude_damping":
            gamma = self.params.get("gamma", 0.01)
            K0 = np.array([[1, 0], [0, math.sqrt(1 - gamma)]])
            K1 = np.array([[0, math.sqrt(gamma)], [0, 0]])
            return [(K0, 1 - gamma), (K1, gamma)]

        elif self.channel_type == "phase_damping":
            gamma = self.params.get("gamma", 0.01)
            K0 = np.array([[1, 0], [0, math.sqrt(1 - gamma)]])
            K1 = np.array([[0, 0], [0, math.sqrt(gamma)]])
            return [(K0, 1 - gamma), (K1, gamma)]

        elif self.channel_type == "depolarizing":
            p = self.params.get("p", 0.01)
            K0 = np.array([[math.sqrt(1 - p), 0],
                           [0, math.sqrt(1 - p)]])
            K1 = np.array([[math.sqrt(p / 3), 0],
                           [0, -math.sqrt(p / 3)]])
            K2 = np.array([[0, math.sqrt(p / 3)],
                           [math.sqrt(p / 3), 0]])
            K3 = np.array([[0, -1j * math.sqrt(p / 3)],
                           [1j * math.sqrt(p / 3), 0]])
            return [(K0, 1 - p), (K1, p / 3), (K2, p / 3), (K3, p / 3)]

        elif self.channel_type == "bit_flip":
            p = self.params.get("p", 0.01)
            K0 = np.array([[math.sqrt(1 - p), 0],
                           [0, math.sqrt(1 - p)]])
            K1 = np.array([[0, math.sqrt(p)],
                           [math.sqrt(p), 0]])
            return [(K0, 1 - p), (K1, p)]

        elif self.channel_type == "phase_flip":
            p = self.params.get("p", 0.01)
            K0 = np.array([[math.sqrt(1 - p), 0],
                           [0, math.sqrt(1 - p)]])
            K1 = np.array([[math.sqrt(p), 0],
                           [0, -math.sqrt(p)]])
            return [(K0, 1 - p), (K1, p)]

        elif self.channel_type == "thermal_relaxation":
            t1 = self.params.get("t1", 100.0)
            t2 = self.params.get("t2", 50.0)
            gate_time = self.params.get("gate_time", 1.0)
            p_flip = 0.5 * (1 - math.exp(-gate_time / t1))
            p_decay = 1 - math.exp(-gate_time / t1)
            p_dephase = 1 - math.exp(-gate_time / t2)
            K0 = np.array([[1, 0],
                           [0, math.sqrt(1 - p_decay - p_dephase)]])
            K1 = np.array([[0, math.sqrt(p_flip)],
                           [0, 0]])
            K2 = np.array([[0, 0],
                           [math.sqrt(p_decay - p_flip), 0]])
            return [(K0, 0.5), (K1, 0.25), (K2, 0.25)]

        else:
            raise ValueError(f"Unknown noise channel: {self.channel_type}")

    def sample_jump(self, state: np.ndarray, qubit: int, num_qubits: int) -> Tuple[bool, int, np.ndarray]:
        """
        Sample a quantum jump for the given qubit.

        Returns
        -------
        jumped : bool
            Whether a jump occurred
        jump_index : int
            Which Kraus operator was applied
        new_state : np.ndarray
            State after jump (normalized)
        """
        dim = 2 ** num_qubits

        # Compute probabilities for each Kraus operator
        probs = []
        post_states = []
        for idx, (K, _) in enumerate(self._kraus_ops):
            # Apply K to the target qubit
            new_state = self._apply_kraus(state, K, qubit, num_qubits)
            prob = np.real(np.vdot(new_state, new_state))
            probs.append(prob)
            post_states.append(new_state)

        total = sum(probs)
        if total < 1e-15:
            return False, 0, state

        probs = [p / total for p in probs]

        # Sample
        r = random.random()
        cumulative = 0.0
        for idx, (p, ps) in enumerate(zip(probs, post_states)):
            cumulative += p
            if r < cumulative:
                # Normalize
                norm = np.sqrt(np.real(np.vdot(ps, ps)))
                if norm > 1e-15:
                    ps = ps / norm
                return True, idx, ps

        # Fallback to last
        norm = np.sqrt(np.real(np.vdot(post_states[-1], post_states[-1])))
        if norm > 1e-15:
            post_states[-1] = post_states[-1] / norm
        return True, len(probs) - 1, post_states[-1]

    def _apply_kraus(self, state: np.ndarray, K: np.ndarray,
                     qubit: int, num_qubits: int) -> np.ndarray:
        """Apply a single-qubit Kraus operator to the statevector."""
        dim = 2 ** num_qubits
        result = np.zeros(dim, dtype=complex)
        n = num_qubits

        for i in range(dim):
            if abs(state[i]) < 1e-15:
                continue
            # Check bit at position qubit
            bit = (i >> (n - 1 - qubit)) & 1
            for k_out in range(2):
                # K[k_out, bit] is the amplitude
                val = K[k_out, bit]
                if abs(val) < 1e-15:
                    continue
                # Build new index: flip the qubit bit to k_out
                new_i = (i & ~(1 << (n - 1 - qubit))) | (k_out << (n - 1 - qubit))
                result[new_i] += val * state[i]

        return result


class MonteCarloWavefunctionSimulator:
    """
    Monte Carlo Wavefunction (Quantum Jumps) Simulator.

    Simulates open quantum systems by evolving pure-state trajectories
    under a non-Hermitian Hamiltonian with stochastic quantum jumps.
    Memory-efficient: O(2^n) per trajectory vs O(4^n) for density matrix.

    Parameters
    ----------
    num_qubits : int
        Number of qubits (supports 100+ qubits with low entanglement)
    noise_channels : dict, optional
        Per-qubit noise channels: {qubit_index: [NoiseChannel, ...]}
    dt : float
        Time step for evolution (dimensionless)
    num_trajectories : int
        Number of Monte Carlo trajectories to average
    seed : int, optional
        Random seed for reproducibility
    """

    def __init__(self, num_qubits: int,
                 noise_channels: Optional[Dict[int, List[NoiseChannel]]] = None,
                 dt: float = 0.01,
                 num_trajectories: int = 100,
                 seed: Optional[int] = None):
        self.num_qubits = num_qubits
        self.noise_channels = noise_channels or {}
        self.dt = dt
        self.num_trajectories = num_trajectories
        self.seed = seed
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def _init_state(self) -> np.ndarray:
        """Initialize |00...0> state."""
        dim = 2 ** self.num_qubits
        state = np.zeros(dim, dtype=complex)
        state[0] = 1.0
        return state

    def _apply_gate(self, state: np.ndarray, gate_name: str,
                    qubits: List[int], params: List[float]) -> np.ndarray:
        """Apply a unitary gate to the statevector."""
        n = self.num_qubits
        dim = 2 ** n
        name = gate_name.upper()

        if name == "H":
            q = qubits[0]
            return self._apply_single_qubit(state, self._H, q, n)
        elif name == "X":
            q = qubits[0]
            return self._apply_single_qubit(state, self._X, q, n)
        elif name == "Y":
            q = qubits[0]
            return self._apply_single_qubit(state, self._Y, q, n)
        elif name == "Z":
            q = qubits[0]
            return self._apply_single_qubit(state, self._Z, q, n)
        elif name == "S":
            q = qubits[0]
            return self._apply_single_qubit(state, self._S, q, n)
        elif name == "S_DAG":
            q = qubits[0]
            return self._apply_single_qubit(state, self._S_DAG, q, n)
        elif name == "T":
            q = qubits[0]
            return self._apply_single_qubit(state, self._T, q, n)
        elif name == "T_DAG":
            q = qubits[0]
            return self._apply_single_qubit(state, self._T_DAG, q, n)
        elif name in ("RX", "RY", "RZ"):
            q = qubits[0]
            theta = params[0] if params else 0.0
            if name == "RX":
                U = np.array([[math.cos(theta / 2), -1j * math.sin(theta / 2)],
                              [-1j * math.sin(theta / 2), math.cos(theta / 2)]])
            elif name == "RY":
                U = np.array([[math.cos(theta / 2), -math.sin(theta / 2)],
                              [math.sin(theta / 2), math.cos(theta / 2)]])
            else:  # RZ
                U = np.array([[np.exp(-1j * theta / 2), 0],
                              [0, np.exp(1j * theta / 2)]])
            return self._apply_single_qubit(state, U, q, n)
        elif name == "CNOT":
            return self._apply_cnot(state, qubits[0], qubits[1], n)
        elif name == "CZ":
            return self._apply_cz(state, qubits[0], qubits[1], n)
        elif name == "SWAP":
            state = self._apply_cnot(state, qubits[0], qubits[1], n)
            state = self._apply_cnot(state, qubits[1], qubits[0], n)
            return self._apply_cnot(state, qubits[0], qubits[1], n)
        else:
            return state  # Unknown gate -> identity

    def _apply_single_qubit(self, state: np.ndarray, U: np.ndarray,
                            qubit: int, n: int) -> np.ndarray:
        """Apply single-qubit gate via einsum."""
        dim = 2 ** n
        result = np.zeros(dim, dtype=complex)
        for i in range(dim):
            if abs(state[i]) < 1e-15:
                continue
            bit = (i >> (n - 1 - qubit)) & 1
            for k in range(2):
                val = U[k, bit]
                if abs(val) < 1e-15:
                    continue
                new_i = (i & ~(1 << (n - 1 - qubit))) | (k << (n - 1 - qubit))
                result[new_i] += val * state[i]
        return result

    def _apply_cnot(self, state: np.ndarray, control: int, target: int, n: int) -> np.ndarray:
        """Apply CNOT gate."""
        dim = 2 ** n
        result = np.zeros(dim, dtype=complex)
        for i in range(dim):
            c_bit = (i >> (n - 1 - control)) & 1
            t_bit = (i >> (n - 1 - target)) & 1
            if c_bit == 1:
                new_i = i ^ (1 << (n - 1 - target))
                result[new_i] += state[i]
            else:
                result[i] += state[i]
        return result

    def _apply_cz(self, state: np.ndarray, q1: int, q2: int, n: int) -> np.ndarray:
        """Apply CZ gate."""
        dim = 2 ** n
        result = np.zeros(dim, dtype=complex)
        for i in range(dim):
            b1 = (i >> (n - 1 - q1)) & 1
            b2 = (i >> (n - 1 - q2)) & 1
            if b1 == 1 and b2 == 1:
                result[i] -= state[i]
            else:
                result[i] += state[i]
        return result

    # Standard gate matrices
    _H = np.array([[1, 1], [1, -1]]) / math.sqrt(2)
    _X = np.array([[0, 1], [1, 0]], dtype=complex)
    _Y = np.array([[0, -1j], [1j, 0]])
    _Z = np.array([[1, 0], [0, -1]], dtype=complex)
    _S = np.array([[1, 0], [0, 1j]])
    _S_DAG = np.array([[1, 0], [0, -1j]])
    _T = np.array([[1, 0], [0, np.exp(1j * math.pi / 4)]])
    _T_DAG = np.array([[1, 0], [0, np.exp(-1j * math.pi / 4)]])

    def run_trajectory(self, circuit: Circuit, trajectory_id: int) -> TrajectoryResult:
        """
        Run a single Monte Carlo trajectory.

        The state evolves under the unitary circuit with stochastic quantum
        jumps sampled from the noise channels.
        """
        state = self._init_state()
        jump_history = []
        total_jump_prob = 0.0

        # Apply circuit gates with noise
        for gate in circuit.gates:
            qubits = gate.qubits if isinstance(gate.qubits, list) else [gate.qubits]
            params = gate.params or []

            # Apply ideal gate
            state = self._apply_gate(state, gate.name, qubits, params)

            # Apply noise channels for each qubit involved
            for q in qubits:
                if q in self.noise_channels:
                    for channel in self.noise_channels[q]:
                        jumped, jump_idx, new_state = channel.sample_jump(
                            state, q, self.num_qubits
                        )
                        if jumped:
                            jump_prob = channel._kraus_ops[jump_idx][1]
                            total_jump_prob += jump_prob
                            jump_history.append(QuantumJump(
                                time_step=len(jump_history),
                                qubit=q,
                                operator=channel.channel_type,
                                probability=jump_prob,
                                post_state_norm=float(np.sqrt(
                                    np.real(np.vdot(new_state, new_state))
                                ))
                            ))
                            state = new_state

        # Normalize
        norm = np.sqrt(np.real(np.vdot(state, state)))
        if norm > 1e-15:
            state = state / norm

        return TrajectoryResult(
            trajectory_id=trajectory_id,
            final_state=state,
            expectation_values={},
            jump_history=jump_history,
            total_jump_probability=total_jump_prob,
            survival_probability=1.0 - total_jump_prob,
        )

    def compute_expectation(self, state: np.ndarray,
                            observable: np.ndarray) -> float:
        """Compute <state|observable|state>."""
        return float(np.real(np.vdot(state, observable @ state)))

    def compute_pauli_expectation(self, state: np.ndarray,
                                  pauli_string: str) -> float:
        """
        Compute expectation value of a Pauli string.

        pauli_string: e.g., "ZZIX" means Z on qubit 0, Z on qubit 1,
                       I on qubit 2, X on qubit 3.
        """
        n = self.num_qubits
        dim = 2 ** n
        pauli_map = {
            'I': np.eye(2, dtype=complex),
            'X': np.array([[0, 1], [1, 0]], dtype=complex),
            'Y': np.array([[0, -1j], [1j, 0]]),
            'Z': np.array([[1, 0], [0, -1]], dtype=complex),
        }

        # Build full observable via tensor product
        obs = np.array([[1]], dtype=complex)
        for i, p in enumerate(pauli_string):
            if p in pauli_map:
                obs = np.kron(obs, pauli_map[p])

        return self.compute_expectation(state, obs)

    def run(self, circuit: Circuit,
            observables: Optional[Dict[str, Any]] = None) -> MonteCarloResult:
        """
        Run multiple Monte Carlo trajectories and aggregate results.

        Parameters
        ----------
        circuit : Circuit
            Quantum circuit to simulate
        observables : dict, optional
            Observables to measure: {name: pauli_string_or_matrix}

        Returns
        -------
        MonteCarloResult
            Averaged results with variance estimates
        """
        trajectories = []
        all_expectations = {}

        for t_id in range(self.num_trajectories):
            traj = self.run_trajectory(circuit, t_id)

            # Compute expectation values for observables
            if observables:
                expvals = {}
                for name, obs in observables.items():
                    if isinstance(obs, str):
                        expvals[name] = self.compute_pauli_expectation(
                            traj.final_state, obs
                        )
                    elif isinstance(obs, np.ndarray):
                        expvals[name] = self.compute_expectation(
                            traj.final_state, obs
                        )
                traj.expectation_values = expvals

                for name, val in expvals.items():
                    if name not in all_expectations:
                        all_expectations[name] = []
                    all_expectations[name].append(val)

            trajectories.append(traj)

        # Compute averages and variance
        averaged = {}
        variance = {}
        for name, vals in all_expectations.items():
            arr = np.array(vals)
            averaged[name] = float(np.mean(arr))
            variance[name] = float(np.var(arr) / len(arr))  # standard error

        # Build measurement counts from final states
        counts = {}
        for traj in trajectories:
            probs = np.abs(traj.final_state) ** 2
            # Sample one measurement outcome per trajectory
            outcome_idx = np.random.choice(len(probs), p=probs)
            outcome = format(outcome_idx, f'0{self.num_qubits}b')
            counts[outcome] = counts.get(outcome, 0) + 1

        total = sum(counts.values())
        probabilities = {k: v / total for k, v in counts.items()}

        return MonteCarloResult(
            num_trajectories=self.num_trajectories,
            num_qubits=self.num_qubits,
            averaged_expectation=averaged,
            variance=variance,
            trajectories=trajectories,
            counts=counts,
            probabilities=probabilities,
        )

    def simulate_noise_evolution(self, circuit: Circuit,
                                  time_steps: int = 10) -> List[MonteCarloResult]:
        """
        Simulate circuit execution with noise at multiple time steps.

        Useful for studying decoherence effects over time.
        """
        results = []
        for step in range(1, time_steps + 1):
            # Scale noise by time step
            scaled_channels = {}
            for q, channels in self.noise_channels.items():
                scaled_channels[q] = []
                for ch in channels:
                    scaled_params = dict(ch.params)
                    if 'gamma' in scaled_params:
                        scaled_params['gamma'] *= step / time_steps
                    elif 'p' in scaled_params:
                        scaled_params['p'] *= step / time_steps
                    scaled_channels[q].append(NoiseChannel(ch.channel_type, **scaled_params))

            sim = MonteCarloWavefunctionSimulator(
                num_qubits=self.num_qubits,
                noise_channels=scaled_channels,
                dt=self.dt,
                num_trajectories=self.num_trajectories // time_steps + 1,
            )
            result = sim.run(circuit)
            results.append(result)

        return results
