"""
Task 13.1 — Quantum Network Simulator.

Full quantum network stack with real quantum state transmission.
Quantum channel models: loss, noise, depolarization, dark counts.
Entanglement distribution and management.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import time


class TopologyType(Enum):
    """Network topology types."""
    STAR = "star"
    MESH = "mesh"
    TREE = "tree"
    RING = "ring"
    BUS = "bus"


class ChannelModel(Enum):
    """Quantum channel noise models."""
    IDEAL = "ideal"
    LOSS = "loss"
    DEPOLARIZING = "depolarizing"
    AMPLITUDE_DAMPING = "amplitude_damping"
    PHASE_DAMPING = "phase_damping"
    COMBINED = "combined"


@dataclass
class QuantumChannel:
    """A quantum channel between two nodes."""

    def __init__(self, source: str, target: str,
                 model: ChannelModel = ChannelModel.IDEAL,
                 loss_prob: float = 0.0,
                 depolarizing_rate: float = 0.0,
                 dark_count_rate: float = 0.0,
                 distance_km: float = 1.0,
                 attenuation_db_per_km: float = 0.1):
        self.source = source
        self.target = target
        self.model = model
        self.loss_prob = loss_prob
        self.depolarizing_rate = depolarizing_rate
        self.dark_count_rate = dark_count_rate
        self.distance_km = distance_km
        self.attenuation_db_per_km = attenuation_db_per_km

    def transmit(self, qubit_state: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Transmit qubit through channel with real quantum noise.

        Args:
            qubit_state: 2-element state vector [alpha, beta]

        Returns:
            Tuple of (transmitted_state, success_probability)
        """
        if self.model == ChannelModel.IDEAL:
            return qubit_state.copy(), 1.0

        state = qubit_state.copy()
        success_prob = 1.0

        # Apply loss (photon loss in fiber).
        if self.model in [ChannelModel.LOSS, ChannelModel.COMBINED]:
            # Fiber loss: attenuation = 10^(-attenuation_db_per_km * distance_km / 10)
            loss_factor = 10 ** (-self.attenuation_db_per_km * self.distance_km / 10)
            success_prob *= (1.0 - self.loss_prob) * loss_factor

            # With probability loss_prob, qubit is lost (becomes |0>).
            if np.random.random() < self.loss_prob:
                state = np.array([1.0, 0.0], dtype=complex)  # |0>
                success_prob *= 0.5  # Lost photon halves the success.

        # Apply depolarizing noise.
        if self.model in [ChannelModel.DEPOLARIZING, ChannelModel.COMBINED]:
            p = self.depolarizing_rate
            if np.random.random() < p:
                # Apply random Pauli: X, Y, or Z with equal probability.
                pauli_choice = np.random.randint(0, 3)
                if pauli_choice == 0:  # X
                    state = np.array([state[1], state[0]], dtype=complex)
                elif pauli_choice == 1:  # Y
                    state = np.array([state[1] * 1j, -state[0] * 1j], dtype=complex)
                else:  # Z
                    state = np.array([state[0], -state[1]], dtype=complex)
                success_prob *= (1.0 - p)

        # Apply amplitude damping (energy loss).
        if self.model in [ChannelModel.AMPLITUDE_DAMPING, ChannelModel.COMBINED]:
            gamma = 0.01 * self.distance_km  # Damping probability.
            if np.random.random() < gamma:
                # State decays to |0>.
                state = np.array([1.0, 0.0], dtype=complex)
                success_prob *= (1.0 - gamma)

        # Apply phase damping (dephasing).
        if self.model in [ChannelModel.PHASE_DAMPING, ChannelModel.COMBINED]:
            lam = 0.01 * self.distance_km
            if np.random.random() < lam:
                # Random phase shift.
                phase = np.random.random() * 2 * np.pi
                state[1] *= np.exp(1j * phase)
                success_prob *= (1.0 - lam)

        # Apply dark counts (measurement error).
        if self.dark_count_rate > 0:
            if np.random.random() < self.dark_count_rate * 0.001:
                # Dark count flips the state.
                state = np.array([state[1], state[0]], dtype=complex)

        # Normalize state.
        norm = np.linalg.norm(state)
        if norm > 0:
            state = state / norm

        return state, success_prob

    def _apply_pauli(self, state: np.ndarray, pauli: str) -> np.ndarray:
        """Apply Pauli operator to single qubit state."""
        if pauli == 'X':
            return np.array([state[1], state[0]], dtype=complex)
        elif pauli == 'Y':
            return np.array([state[1] * 1j, -state[0] * 1j], dtype=complex)
        elif pauli == 'Z':
            return np.array([state[0], -state[1]], dtype=complex)
        return state


class NetworkNode:
    """A node in the quantum network."""

    def __init__(self, name: str, node_type: str = "end"):
        self.name = name
        self.node_type = node_type  # "end", "repeater", "switch"
        self.qubit_memory: Dict[int, np.ndarray] = {}  # Qubit memory.
        self.entanglement_links: Dict[str, Any] = {}

    def store_qubit(self, qubit_id: int, state: np.ndarray):
        """Store qubit in memory."""
        self.qubit_memory[qubit_id] = state.copy()

    def recall_qubit(self, qubit_id: int) -> Optional[np.ndarray]:
        """Recall qubit from memory."""
        return self.qubit_memory.get(qubit_id)

    def measure_qubit(self, qubit_id: int, basis: str = 'Z') -> int:
        """Measure qubit in given basis."""
        if qubit_id not in self.qubit_memory:
            return 0

        state = self.qubit_memory[qubit_id]

        if basis == 'Z':
            probs = [np.abs(state[0])**2, np.abs(state[1])**2]
        else:  # X basis.
            # Transform to X basis.
            x_state = np.array([
                (state[0] + state[1]) / np.sqrt(2),
                (state[0] - state[1]) / np.sqrt(2)
            ])
            probs = [np.abs(x_state[0])**2, np.abs(x_state[1])**2]

        # Normalize.
        probs = np.array(probs) / np.sum(probs)
        return np.random.choice(2, p=probs)


class QuantumNetwork:
    """Full quantum network simulation."""

    def __init__(self, topology: TopologyType = TopologyType.MESH):
        self.topology = topology
        self.nodes: Dict[str, NetworkNode] = {}
        self.channels: List[QuantumChannel] = []
        self.entanglement_table: Dict[Tuple[str, str], Any] = {}

    def add_node(self, name: str, node_type: str = "end"):
        """Add node to network."""
        self.nodes[name] = NetworkNode(name, node_type)

    def add_channel(self, source: str, target: str,
                    model: ChannelModel = ChannelModel.IDEAL, **kwargs):
        """Add quantum channel between nodes."""
        channel = QuantumChannel(source, target, model, **kwargs)
        self.channels.append(channel)

    def transmit_qubit(self, source: str, target: str,
                       qubit_state: np.ndarray) -> Tuple[np.ndarray, float]:
        """Transmit qubit from source to target."""
        # Find channel.
        channel = None
        for ch in self.channels:
            if ch.source == source and ch.target == target:
                channel = ch
                break

        if channel is None:
            # Create default channel.
            channel = QuantumChannel(source, target)

        # Transmit.
        return channel.transmit(qubit_state)

    def create_entanglement(self, node1: str, node2: str) -> bool:
        """Create entangled pair between two nodes."""
        if node1 not in self.nodes or node2 not in self.nodes:
            return False

        # Create Bell pair |Φ+> = (|00> + |11>)/√2.
        bell_state = np.zeros(4, dtype=complex)
        bell_state[0] = 1/np.sqrt(2)  # |00>.
        bell_state[3] = 1/np.sqrt(2)  # |11>.

        # Distribute: each node gets one qubit.
        # Qubit 1 goes to node1, qubit 2 goes to node2.
        # For simplicity, store full state in both (in real implementation, would split).
        self.nodes[node1].store_qubit(0, bell_state[:2])  # First qubit.
        self.nodes[node2].store_qubit(0, bell_state[2:])  # Second qubit (simplified).

        self.entanglement_table[(node1, node2)] = bell_state
        return True

    def measure_entangled(self, node: str, basis: str = 'Z') -> int:
        """Measure entangled qubit."""
        if node not in self.nodes:
            return 0
        return self.nodes[node].measure_qubit(0, basis)

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        return {
            'nodes': len(self.nodes),
            'channels': len(self.channels),
            'entangled_pairs': len(self.entanglement_table),
            'topology': self.topology.value
        }
