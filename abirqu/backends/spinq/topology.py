"""
SpinQ Topology
==============
Linear chain topology for SpinQ trapped-ion processors.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


class SpinQTopology:
    """Linear chain topology for SpinQ trapped-ion processors.

    Trapped-ion processors have a linear chain topology where each
    qubit is connected to its nearest neighbors, but can also
    perform gates between non-adjacent qubits via ion shuttling.
    """

    @staticmethod
    def linear_chain(num_qubits: int) -> Dict[int, List[int]]:
        """Generate a linear chain adjacency graph.

        For trapped ions, the native connectivity is linear chain,
        but the MS gate allows all-to-all connectivity.
        """
        graph: Dict[int, List[int]] = {}
        for i in range(num_qubits):
            neighbors = []
            if i > 0:
                neighbors.append(i - 1)
            if i < num_qubits - 1:
                neighbors.append(i + 1)
            graph[i] = neighbors
        return graph

    @staticmethod
    def all_to_all(num_qubits: int) -> Dict[int, List[int]]:
        """Generate an all-to-all connectivity graph.

        With MS (Molmer-Sorensen) gate, trapped ions can perform
        entangling gates between any pair of qubits.
        """
        graph: Dict[int, List[int]] = {}
        for i in range(num_qubits):
            graph[i] = [j for j in range(num_qubits) if j != i]
        return graph

    @staticmethod
    def coupling_map(num_qubits: int, all_to_all: bool = True) -> List[Tuple[int, int]]:
        """Return the coupling map as a list of edges."""
        if all_to_all:
            edges = []
            for i in range(num_qubits):
                for j in range(i + 1, num_qubits):
                    edges.append((i, j))
            return edges
        else:
            return [(i, i + 1) for i in range(num_qubits - 1)]

    @staticmethod
    def max_qubits() -> int:
        """Maximum qubits in SpinQ processors."""
        return 6

    @staticmethod
    def connectivity_type() -> str:
        """Return the connectivity type."""
        return "all-to-all (via MS gate)"
