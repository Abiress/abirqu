"""
Task 13.1 — Quantum Network Simulator.

Full quantum network stack: physical, link, network, transport, application layers.
Quantum channel models: loss, noise, depolarization, dark counts.
Entanglement distribution and management.
Network topology editor: star, mesh, tree, ring.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import time
import random


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
    source: str
    target: str
    model: ChannelModel = ChannelModel.IDEAL
    loss_prob: float = 0.0  # Probability of photon loss
    depolarizing_rate: float = 0.0  # Depolarizing rate
    dark_count_rate: float = 0.0  # Dark count rate (per microsecond)
    distance_km: float = 1.0  # Distance in km
    attenuation_db_per_km: float = 0.1  # Fiber attenuation
    
    def transmit(self, qubit_state: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Transmit qubit through channel.
        
        Args.
            qubit_state: 2-element state vector.
            
        Returns.
            Tuple of (transmitted_state, success_probability).
        """
        if self.model == ChannelModel.IDEAL:
            return qubit_state.copy(), 1.0
        
        state = qubit_state.copy()
        success_prob = 1.0
        
        # Apply loss.
        if self.model in [ChannelModel.LOSS, ChannelModel.COMBINED]:
            # Fiber loss: attenuation = 10^(-attenuation_db_per_km * distance_km / 10)
            loss_factor = 10 ** (-self.attenuation_db_per_km * self.distance_km / 10)
            success_prob *= (1.0 - self.loss_prob) * loss_factor
        
        # Apply depolarizing noise.
        if self.model in [ChannelModel.DEPOLARIZING, ChannelModel.COMBINED]:
            p = self.depolarizing_rate
            if random.random() < p:
                # Apply random Pauli.
                pauli = random.choice(['X', 'Y', 'Z'])
                state = self._apply_pauli(state, pauli)
                success_prob *= (1.0 - p)
        
        # Apply dark counts (measurement error).
        if self.dark_count_rate > 0:
            # Simplified: dark counts flip the state.
            if random.random() < self.dark_count_rate * 0.001:  # Per microsecond
                state = self._apply_pauli(state, 'X')
        
        return state, success_prob
    
    def _apply_pauli(self, state: np.ndarray, pauli: str) -> np.ndarray:
        """Apply Pauli operator to single qubit state."""
        if pauli == 'X':
            # X = [[0, 1], [1, 0]]
            return np.array([state[1], state[0]])
        elif pauli == 'Y':
            # Y = [[0, -i], [i, 0]] (simplified real version)
            return np.array([-state[1], state[0]])
        elif pauli == 'Z':
            # Z = [[1, 0], [0, -1]]
            return np.array([state[0], -state[1]])
        return state
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'target': self.target,
            'model': self.model.value,
            'loss_prob': self.loss_prob,
            'depolarizing_rate': self.depolarizing_rate,
            'dark_count_rate': self.dark_count_rate,
            'distance_km': self.distance_km,
        }


@dataclass
class NetworkNode:
    """A node in the quantum network."""
    id: str
    node_type: str = "end_node"  # end_node, repeater, router
    location: Tuple[float, float] = (0.0, 0.0)  # (x, y) km
    qubits: int = 10
    classical_compute: bool = True


class NetworkTopology:
    """
    Network topology editor and manager.
    """
    
    def __init__(self, topology_type: TopologyType = TopologyType.MESH):
        self.topology_type = topology_type
        self.nodes: Dict[str, NetworkNode] = {}
        self.channels: List[QuantumChannel] = []
        self._id_counter = 0
    
    def add_node(self, node_type: str = "end_node", 
                 location: Optional[Tuple[float, float]] = None) -> str:
        """Add a node to the network."""
        node_id = f"node_{self._id_counter}"
        self._id_counter += 1
        
        if location is None:
            # Auto-generate location based on topology.
            location = self._get_auto_location()
        
        self.nodes[node_id] = NetworkNode(
            id=node_id,
            node_type=node_type,
            location=location
        )
        return node_id
    
    def _get_auto_location(self) -> Tuple[float, float]:
        """Generate location based on topology type."""
        n = len(self.nodes)
        if self.topology_type == TopologyType.STAR:
            # All nodes at distance 1 from origin.
            angle = 2 * np.pi * n / max(1, n + 1)
            return (np.cos(angle), np.sin(angle))
        elif self.topology_type == TopologyType.RING:
            angle = 2 * np.pi * n / max(3, n + 3)
            return (np.cos(angle) * 2, np.sin(angle) * 2)
        else:
            # Random location.
            return (random.uniform(0, 10), random.uniform(0, 10))
    
    def add_channel(self, source: str, target: str,
                    model: ChannelModel = ChannelModel.IDEAL,
                    **kwargs) -> QuantumChannel:
        """Add a quantum channel between two nodes."""
        if source not in self.nodes or target not in self.nodes:
            raise ValueError(f"Node not found: {source} or {target}")
        
        # Calculate distance.
        src_loc = self.nodes[source].location
        tgt_loc = self.nodes[target].location
        distance = np.sqrt((src_loc[0] - tgt_loc[0])**2 + 
                        (src_loc[1] - tgt_loc[1])**2)
        
        channel = QuantumChannel(
            source=source,
            target=target,
            model=model,
            distance_km=distance,
            **kwargs
        )
        self.channels.append(channel)
        return channel
    
    def build_topology(self):
        """Build connections based on topology type."""
        node_ids = list(self.nodes.keys())
        
        if self.topology_type == TopologyType.STAR:
            # Connect all nodes to center (node_0).
            if len(node_ids) > 1:
                for i in range(1, len(node_ids)):
                    self.add_channel(node_ids[0], node_ids[i])
        
        elif self.topology_type == TopologyType.MESH:
            # Fully connected.
            for i in range(len(node_ids)):
                for j in range(i + 1, len(node_ids)):
                    self.add_channel(node_ids[i], node_ids[j])
        
        elif self.topology_type == TopologyType.TREE:
            # Binary tree.
            for i in range(1, len(node_ids)):
                parent = (i - 1) // 2
                self.add_channel(node_ids[parent], node_ids[i])
        
        elif self.topology_type == TopologyType.RING:
            # Ring: each node connected to 2 neighbors.
            n = len(node_ids)
            for i in range(n):
                self.add_channel(node_ids[i], node_ids[(i + 1) % n])
                if i == 0:  # Avoid duplicate for first node.
                    self.add_channel(node_ids[i], node_ids[n-1])
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """Get neighboring nodes."""
        neighbors = []
        for ch in self.channels:
            if ch.source == node_id:
                neighbors.append(ch.target)
            elif ch.target == node_id:
                neighbors.append(ch.source)
        return neighbors
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.topology_type.value,
            'nodes': {nid: {'type': n.node_type, 'location': n.location} 
                      for nid, n in self.nodes.items()},
            'channels': [ch.to_dict() for ch in self.channels],
            'num_nodes': len(self.nodes),
            'num_channels': len(self.channels),
        }


class QuantumNetworkSimulator:
    """
    Full quantum network stack simulator.
    
    Layers: Physical (photons), Link (entanglement), 
             Network (routing), Transport (retransmission), Application.
    """
    
    def __init__(self, topology: Optional[NetworkTopology] = None):
        self.topology = topology or NetworkTopology(TopologyType.MESH)
        self.stack_state = {
            'physical': {'photons_transmitted': 0, 'loss_rate': 0.0},
            'link': {'entangled_pairs': 0, 'fidelity': 1.0},
            'network': {'packets_routed': 0, 'hops': 0},
            'transport': {'retransmissions': 0},
            'application': {'qubits_delivered': 0},
        }
        self.entangled_pairs: Dict[Tuple[str, str], Tuple[np.ndarray, float]] = {}
        self.classical_network: Dict[str, List[str]] = {}  # node -> messages
    
    def initialize(self):
        """Initialize the network stack."""
        # Build topology if empty.
        if not self.topology.channels:
            self.topology.build_topology()
        
        # Initialize classical network (same topology).
        for ch in self.topology.channels:
            if ch.source not in self.classical_network:
                self.classical_network[ch.source] = []
            if ch.target not in self.classical_network:
                self.classical_network[ch.target] = []
            self.classical_network[ch.source].append(f"msg_to_{ch.target}")
        
        self.stack_state['physical']['photons_transmitted'] = 0
        return "Network initialized"
    
    def distribute_entanglement(self, source: str, target: str,
                                fidelity: float = 0.99) -> bool:
        """
        Distribute entanglement between two nodes.
        
        Returns:
            True if successful.
        """
        # Find channel.
        channel = self._find_channel(source, target)
        if channel is None:
            return False
        
        # Simulate entanglement generation.
        # Create Bell pair |Φ+> = (|00> + |11>)/√2.
        bell_state = np.array([1, 0, 0, 1]) / np.sqrt(2)
        
        # Transmit one qubit through channel.
        transmitted, success_prob = channel.transmit(bell_state[:2])
        
        if random.random() < success_prob * fidelity:
            self.entangled_pairs[(source, target)] = (bell_state, fidelity)
            self.stack_state['link']['entangled_pairs'] += 1
            self.stack_state['link']['fidelity'] = fidelity
            return True
        else:
            self.stack_state['physical']['loss_rate'] += 1
            return False
    
    def _find_channel(self, source: str, target: str) -> Optional[QuantumChannel]:
        """Find channel between two nodes."""
        for ch in self.topology.channels:
            if (ch.source == source and ch.target == target) or \
               (ch.source == target and ch.target == source):
                return ch
        return None
    
    def send_qubit(self, source: str, target: str, 
                 qubit_state: np.ndarray) -> Tuple[bool, np.ndarray]:
        """
        Send qubit from source to target.
        
        Returns:
            Tuple of (success, received_state).
        """
        channel = self._find_channel(source, target)
        if channel is None:
            return False, qubit_state
        
        # Transmit through channel.
        received, prob = channel.transmit(qubit_state)
        self.stack_state['physical']['photons_transmitted'] += 1
        
        if random.random() < prob:
            self.stack_state['application']['qubits_delivered'] += 1
            return True, received
        else:
            return False, qubit_state
    
    def route_message(self, source: str, target: str, 
                      message: str) -> List[str]:
        """
        Route classical message through network.
        
        Returns:
            List of hops (node IDs).
        """
        # Simplified routing: BFS.
        from collections import deque
        queue = deque([source])
        visited = {source}
        parent = {source: None}
        
        while queue:
            current = queue.popleft()
            if current == target:
                break
            
            for neighbor in self.topology.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
        
        # Reconstruct path.
        path = []
        curr = target
        while curr is not None:
            path.append(curr)
            curr = parent.get(curr)
        path.reverse()
        
        self.stack_state['network']['packets_routed'] += 1
        self.stack_state['network']['hops'] = len(path) - 1
        
        return path
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get network statistics."""
        return {
            'stack_state': self.stack_state.copy(),
            'entangled_pairs': len(self.entangled_pairs),
            'topology': self.topology.to_dict(),
            'average_fidelity': np.mean([f for _, (_, f) in self.entangled_pairs.items()]) 
                                if self.entangled_pairs else 0.0,
        }
