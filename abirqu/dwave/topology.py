"""
D-Wave Topology
===============
Hardware topology loaders for D-Wave Chimera and Pegasus graphs.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

import numpy as np


class DWaveTopology:
    """D-Wave hardware topology manager.

    Provides graph generators for Chimera and Pegasus topologies,
    and topology-aware operations.
    """

    @staticmethod
    def chimera_graph(m: int, n: int) -> Dict[int, List[int]]:
        """Generate a Chimera graph C(m, n).

        Chimera graphs are bipartite lattices of K_{4,4} unit cells.

        Parameters
        ----------
        m : int
            Number of rows in the Chimera lattice.
        n : int
            Number of columns in the Chimera lattice.

        Returns
        -------
        Adjacency dict mapping qubit index to list of neighbors.
        """
        graph: Dict[int, List[int]] = {}
        # Chimera: 8 qubits per unit cell (2 layers of 4)
        for i in range(m):
            for j in range(n):
                base = 8 * (i * n + j)
                # Layer A: qubits 0-3
                for a in range(4):
                    q = base + a
                    graph[q] = []
                    # Connect to layer B within cell
                    for b in range(4):
                        graph[q].append(base + 4 + b)
                    # Connect to adjacent cells
                    if i > 0:
                        graph[q].append(base - 8 * n + 4 + a)
                    if i < m - 1:
                        graph[q].append(base + 8 * n + 4 + a)
                # Layer B: qubits 4-7
                for b in range(4):
                    q = base + 4 + b
                    if q not in graph:
                        graph[q] = []
                    # Connect to layer A within cell
                    for a in range(4):
                        neighbor = base + a
                        if neighbor not in graph[q]:
                            graph[q].append(neighbor)
                    # Connect to adjacent cells
                    if j > 0:
                        neighbor = base - 8 + b
                        if neighbor not in graph[q]:
                            graph[q].append(neighbor)
                    if j < n - 1:
                        neighbor = base + 8 + b
                        if neighbor not in graph[q]:
                            graph[q].append(neighbor)

        return graph

    @staticmethod
    def pegasus_graph(m: int) -> Dict[int, List[int]]:
        """Generate a Pegasus graph P(m).

        Pegasus graphs have higher connectivity than Chimera.

        Parameters
        ----------
        m : int
            Pegasus graph size parameter.

        Returns
        -------
        Adjacency dict mapping qubit index to list of neighbors.
        """
        n = 12 * m * (m - 1) + 3 * m  # Total qubits
        graph: Dict[int, List[int]] = {i: [] for i in range(n)}

        # Simplified Pegasus connectivity
        for i in range(n):
            # Cross-unit-cell connections
            for offset in [1, 3, 12]:
                neighbor = (i + offset) % n
                if neighbor != i and neighbor not in graph[i]:
                    graph[i].append(neighbor)
                    graph[neighbor].append(i)

        return graph

    @staticmethod
    def advantage_topology() -> Dict[int, List[int]]:
        """Topology of D-Wave Advantage (Pegasus-16)."""
        return DWaveTopology.pegasus_graph(16)

    @staticmethod
    def advantage2_topology() -> Dict[int, List[int]]:
        """Topology of D-Wave Advantage2 (Zephyr)."""
        # Zephyr graph — higher connectivity
        n = 4400  # Approximate
        graph: Dict[int, List[int]] = {i: [] for i in range(n)}
        for i in range(n):
            for offset in [1, 2, 4, 10, 20]:
                neighbor = (i + offset) % n
                if neighbor not in graph[i]:
                    graph[i].append(neighbor)
                    graph[neighbor].append(i)
        return graph

    @staticmethod
    def num_qubits(topology: str = "advantage") -> int:
        """Return the number of qubits for a given topology."""
        sizes = {
            "chimera-8": 8 * 8 * 8,  # C(8,8)
            "chimera-12": 12 * 12 * 8,  # C(12,12)
            "pegasus-16": 12 * 16 * 15 + 3 * 16,  # P(16)
            "pegasus-12": 12 * 12 * 11 + 3 * 12,  # P(12)
            "advantage": 5000,
            "advantage2": 7000,
        }
        return sizes.get(topology, 5000)

    @staticmethod
    def get_coupling_map(topology: str = "advantage") -> List[Tuple[int, int]]:
        """Return the coupling map as a list of edges."""
        if topology.startswith("chimera"):
            parts = topology.split("-")
            m = int(parts[1]) if len(parts) > 1 else 8
            graph = DWaveTopology.chimera_graph(m, m)
        elif topology.startswith("pegasus"):
            parts = topology.split("-")
            m = int(parts[1]) if len(parts) > 1 else 16
            graph = DWaveTopology.pegasus_graph(m)
        elif topology == "advantage2":
            graph = DWaveTopology.advantage2_topology()
        else:
            graph = DWaveTopology.advantage_topology()

        edges = []
        for q, neighbors in graph.items():
            for n in neighbors:
                if q < n:
                    edges.append((q, n))
        return edges

    @staticmethod
    def plot_topology(topology: str = "advantage", save_path: Optional[str] = None):
        """Plot the hardware topology using networkx and matplotlib."""
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
        except ImportError as exc:
            raise RuntimeError("Requires networkx and matplotlib.") from exc

        graph = DWaveTopology.advantage_topology() if topology == "advantage" else DWaveTopology.pegasus_graph(12)
        G = nx.Graph()
        for q, neighbors in graph.items():
            for n in neighbors:
                G.add_edge(q, n)

        pos = nx.spring_layout(G, k=0.3, iterations=50)
        plt.figure(figsize=(12, 12))
        nx.draw(G, pos, node_size=5, node_color="blue", edge_color="gray", alpha=0.6, width=0.5)
        plt.title(f"D-Wave {topology} topology ({G.number_of_nodes()} qubits)")
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.show()
