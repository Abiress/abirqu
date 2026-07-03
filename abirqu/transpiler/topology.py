"""
Coupling Map / Hardware Topology
================================
Hardware topology representations for routing.
"""

from __future__ import annotations

from typing import Dict, List, Set, Tuple


class CouplingMap:
    """Hardware coupling map for gate routing.

    Parameters
    ----------
    num_qubits : int
        Number of qubits.
    edges : list of tuple
        Pairs of connected qubit indices.
    """

    def __init__(self, num_qubits: int, edges: List[Tuple[int, int]]):
        self.num_qubits = num_qubits
        self.edges = edges
        self._adj: Dict[int, Set[int]] = {i: set() for i in range(num_qubits)}
        for u, v in edges:
            self._adj[u].add(v)
            self._adj[v].add(u)

    def are_connected(self, q0: int, q1: int) -> bool:
        """Check if two qubits are directly connected."""
        return q1 in self._adj[q0]

    def neighbors(self, qubit: int) -> Set[int]:
        """Return the set of qubits connected to the given qubit."""
        return self._adj[qubit]

    def distance(self, q0: int, q1: int) -> int:
        """Compute shortest path distance between two qubits (BFS)."""
        if q0 == q1:
            return 0
        visited = {q0}
        queue = [(q0, 0)]
        while queue:
            node, dist = queue.pop(0)
            for neighbor in self._adj[node]:
                if neighbor == q1:
                    return dist + 1
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
        return -1  # Not connected

    def shortest_path(self, q0: int, q1: int) -> List[int]:
        """Find shortest path between two qubits."""
        if q0 == q1:
            return [q0]
        visited = {q0}
        queue = [(q0, [q0])]
        while queue:
            node, path = queue.pop(0)
            for neighbor in self._adj[node]:
                if neighbor == q1:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return []

    @classmethod
    def linear_chain(cls, num_qubits: int) -> "CouplingMap":
        """Create a linear chain coupling map."""
        edges = [(i, i + 1) for i in range(num_qubits - 1)]
        return cls(num_qubits, edges)

    @classmethod
    def all_to_all(cls, num_qubits: int) -> "CouplingMap":
        """Create an all-to-all coupling map."""
        edges = [(i, j) for i in range(num_qubits) for j in range(i + 1, num_qubits)]
        return cls(num_qubits, edges)

    @classmethod
    def grid(cls, rows: int, cols: int) -> "CouplingMap":
        """Create a grid coupling map."""
        n = rows * cols
        edges = []
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                if c + 1 < cols:
                    edges.append((idx, idx + 1))
                if r + 1 < rows:
                    edges.append((idx, idx + cols))
        return cls(n, edges)

    @classmethod
    def heavy_hex(cls, rows: int, cols: int) -> "CouplingMap":
        """Create a heavy-hex coupling map (IBM-style)."""
        # Simplified heavy-hex
        return cls.grid(rows, cols)

    def __repr__(self) -> str:
        return f"CouplingMap(qubits={self.num_qubits}, edges={len(self.edges)})"
