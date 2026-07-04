"""
Quantum Network Simulator
Copyright 2026 Abir Maheshwari

Simulates multi-node quantum networks for QKD and distributed quantum computing.

Supports:
- Star, ring, mesh topologies
- Entanglement routing
- Multi-hop key distribution
- Network capacity analysis
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class Topology(Enum):
    """Network topology types."""
    STAR = "star"
    RING = "ring"
    MESH = "mesh"
    LINE = "line"


@dataclass
class QuantumChannel:
    """Quantum channel between two nodes."""
    node_a: int
    node_b: int
    distance_km: float
    loss_db_km: float = 0.2
    fidelity: float = 0.95
    key_rate: float = 0.0

    def __post_init__(self):
        loss_db = self.loss_db_km * self.distance_km
        self.transmission = 10 ** (-loss_db / 10)
        self.key_rate = self.transmission * 0.5  # Simplified


@dataclass
class QuantumNode:
    """Quantum network node."""
    node_id: int
    position: Tuple[float, float] = (0.0, 0.0)
    num_qubits: int = 10
    memory_coherence_time_s: float = 1.0
    entanglement_rate: float = 1000.0


@dataclass
class NetworkPath:
    """Path through the network."""
    source: int
    destination: int
    hops: List[int]
    total_distance_km: float
    total_loss_db: float
    effective_key_rate: float


@dataclass
class QuantumNetworkResult:
    """Result of network simulation."""
    num_nodes: int
    num_edges: int
    topology: Topology
    paths: List[NetworkPath]
    total_key_rate: float
    average_fidelity: float
    network_diameter: float


class QuantumNetwork:
    """
    Quantum Network Simulator.

    Usage:
        net = QuantumNetwork(num_nodes=5, topology=Topology.MESH)
        net.add_random_links(max_distance=100)
        result = net.simulate()
        print(f"Network: {result.num_nodes} nodes, {result.num_edges} edges")
    """

    def __init__(self, num_nodes: int = 5,
                 topology: Topology = Topology.STAR,
                 seed: Optional[int] = None):
        self.num_nodes = num_nodes
        self.topology = topology
        self.rng = np.random.default_rng(seed)

        self.nodes: Dict[int, QuantumNode] = {}
        self.channels: Dict[Tuple[int, int], QuantumChannel] = {}

        self._initialize_nodes()

    def _initialize_nodes(self):
        """Initialize network nodes."""
        for i in range(self.num_nodes):
            # Random position
            x = self.rng.uniform(0, 100)
            y = self.rng.uniform(0, 100)
            self.nodes[i] = QuantumNode(
                node_id=i,
                position=(x, y),
                num_qubits=10,
            )

    def add_link(self, node_a: int, node_b: int,
                 distance_km: Optional[float] = None):
        """Add a quantum channel between two nodes."""
        if distance_km is None:
            pos_a = self.nodes[node_a].position
            pos_b = self.nodes[node_b].position
            distance_km = np.sqrt((pos_a[0] - pos_b[0])**2 +
                                  (pos_a[1] - pos_b[1])**2)

        channel = QuantumChannel(
            node_a=node_a,
            node_b=node_b,
            distance_km=distance_km,
        )
        self.channels[(node_a, node_b)] = channel
        self.channels[(node_b, node_a)] = channel

    def add_random_links(self, max_distance: float = 100.0,
                          avg_degree: float = 3.0):
        """Add random links to create network."""
        target_edges = int(self.num_nodes * avg_degree / 2)

        for _ in range(target_edges):
            a = self.rng.integers(0, self.num_nodes)
            b = self.rng.integers(0, self.num_nodes)
            if a != b and (a, b) not in self.channels:
                pos_a = self.nodes[a].position
                pos_b = self.nodes[b].position
                dist = np.sqrt((pos_a[0] - pos_b[0])**2 +
                               (pos_a[1] - pos_b[1])**2)
                if dist <= max_distance:
                    self.add_link(a, b, dist)

    def build_topology(self):
        """Build predefined topology."""
        if self.topology == Topology.STAR:
            center = self.num_nodes // 2
            for i in range(self.num_nodes):
                if i != center:
                    self.add_link(center, i)

        elif self.topology == Topology.RING:
            for i in range(self.num_nodes):
                self.add_link(i, (i + 1) % self.num_nodes)

        elif self.topology == Topology.LINE:
            for i in range(self.num_nodes - 1):
                self.add_link(i, i + 1)

        elif self.topology == Topology.MESH:
            for i in range(self.num_nodes):
                for j in range(i + 1, self.num_nodes):
                    if self.rng.random() < 0.5:
                        self.add_link(i, j)

    def find_path(self, source: int, destination: int) -> Optional[NetworkPath]:
        """Find shortest path using BFS."""
        if source == destination:
            return None

        visited = {source}
        queue = [(source, [source], 0.0)]

        while queue:
            current, path, dist = queue.pop(0)

            for neighbor in self._get_neighbors(current):
                if neighbor == destination:
                    total_dist = dist + self._get_distance(current, neighbor)
                    total_loss = 0.2 * total_dist  # Simplified
                    key_rate = 10 ** (-total_loss / 10) * 0.5

                    return NetworkPath(
                        source=source,
                        destination=destination,
                        hops=path + [neighbor],
                        total_distance_km=total_dist,
                        total_loss_db=total_loss,
                        effective_key_rate=key_rate,
                    )

                if neighbor not in visited:
                    visited.add(neighbor)
                    new_dist = dist + self._get_distance(current, neighbor)
                    queue.append((neighbor, path + [neighbor], new_dist))

        return None

    def _get_neighbors(self, node: int) -> List[int]:
        """Get neighboring nodes."""
        neighbors = []
        for (a, b) in self.channels:
            if a == node:
                neighbors.append(b)
        return neighbors

    def _get_distance(self, node_a: int, node_b: int) -> float:
        """Get distance between nodes."""
        if (node_a, node_b) in self.channels:
            return self.channels[(node_a, node_b)].distance_km
        return float('inf')

    def simulate(self) -> QuantumNetworkResult:
        """Simulate network operation."""
        # Find all paths
        paths = []
        for i in range(self.num_nodes):
            for j in range(i + 1, self.num_nodes):
                path = self.find_path(i, j)
                if path:
                    paths.append(path)

        # Compute network metrics
        total_key_rate = sum(p.effective_key_rate for p in paths)
        avg_fidelity = np.mean([c.fidelity for c in self.channels.values()]) if self.channels else 0

        # Network diameter (longest shortest path)
        diameters = [p.total_distance_km for p in paths]
        diameter = max(diameters) if diameters else 0

        return QuantumNetworkResult(
            num_nodes=self.num_nodes,
            num_edges=len(self.channels) // 2,
            topology=self.topology,
            paths=paths,
            total_key_rate=total_key_rate,
            average_fidelity=avg_fidelity,
            network_diameter=diameter,
        )

    def get_adjacency_matrix(self) -> np.ndarray:
        """Get adjacency matrix of the network."""
        adj = np.zeros((self.num_nodes, self.num_nodes))
        for (a, b), channel in self.channels.items():
            adj[a, b] = channel.transmission
            adj[b, a] = channel.transmission
        return adj
