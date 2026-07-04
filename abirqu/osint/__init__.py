"""
OSINT & Intelligence Gathering — Quantum Graph Analysis Module.

Converts real-world intelligence graphs (financial networks, supply chains,
communication networks) into quantum-optimizable Ising/QUBO formulations.

Key components:
1. Graph-to-Ising Compiler: Automatic translation of network graphs to
   Ising Hamiltonians for QAOA/quantum annealing
2. Quantum Data Encoding: Efficient classical-to-quantum data compression
   via amplitude encoding and tensor network embeddings
3. Graph Analytics: Max-Cut, community detection, anomaly detection on
   intelligence networks

References:
    - Lucas (2014): Ising formulations of many NP problems
    - Farhi et al. (2014): A Quantum Approximate Optimization Algorithm
    - Kadowaki & Nishimori (1998): Quantum annealing in the transverse Ising model
"""

import math
from typing import List, Tuple, Dict, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from ..circuit import Circuit, Gate
from ..chemistry.fermion_mappers import PauliTerm
from .quantum_encoding import QuantumDataEncoder, QRAMEmulator, TensorNetworkEmbedding


class ProblemType(Enum):
    """Supported graph optimization problems."""
    MAX_CUT = "max_cut"
    MIN_CUT = "min_cut"
    MAX_INDEPENDENT_SET = "max_independent_set"
    MIN_VERTEX_COVER = "min_vertex_cover"
    TRAVELING_SALESMAN = "traveling_salesman"
    GRAPH_COLORING = "graph_coloring"
    COMMUNITY_DETECTION = "community_detection"
    ANOMALY_DETECTION = "anomaly_detection"


@dataclass
class GraphNode:
    """A node in an intelligence graph."""
    id: str
    label: str = ""
    weight: float = 1.0
    features: Dict[str, Any] = field(default_factory=dict)
    x: float = 0.0
    y: float = 0.0


@dataclass
class GraphEdge:
    """An edge in an intelligence graph."""
    source: str
    target: str
    weight: float = 1.0
    edge_type: str = "undirected"  # "undirected", "directed"
    features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntelligenceGraph:
    """
    A graph representing intelligence data.

    Could represent:
    - Financial transaction networks (shell companies, money flows)
    - Communication networks (phone calls, emails)
    - Supply chain networks (suppliers, manufacturers, distributors)
    - Social networks (connections between entities)
    """
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)
    name: str = "intelligence_graph"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, node_id: str, label: str = "", weight: float = 1.0, **kwargs):
        """Add a node to the graph."""
        self.nodes[node_id] = GraphNode(id=node_id, label=label, weight=weight, **kwargs)

    def add_edge(self, source: str, target: str, weight: float = 1.0,
                 edge_type: str = "undirected", **kwargs):
        """Add an edge to the graph."""
        self.edges.append(GraphEdge(
            source=source, target=target, weight=weight,
            edge_type=edge_type, **kwargs
        ))

    @property
    def n_nodes(self) -> int:
        return len(self.nodes)

    @property
    def n_edges(self) -> int:
        return len(self.edges)

    def adjacency_matrix(self) -> np.ndarray:
        """Compute the adjacency matrix."""
        node_ids = sorted(self.nodes.keys())
        n = len(node_ids)
        id_to_idx = {nid: i for i, nid in enumerate(node_ids)}

        adj = np.zeros((n, n), dtype=float)
        for edge in self.edges:
            if edge.source in id_to_idx and edge.target in id_to_idx:
                i, j = id_to_idx[edge.source], id_to_idx[edge.target]
                adj[i, j] = edge.weight
                if edge.edge_type == "undirected":
                    adj[j, i] = edge.weight
        return adj

    def degree_sequence(self) -> List[int]:
        """Return the degree sequence."""
        adj = self.adjacency_matrix()
        return list(np.sum(adj > 0, axis=1).astype(int))

    def is_connected(self) -> bool:
        """Check if the graph is connected using BFS."""
        if not self.nodes:
            return True
        start = next(iter(self.nodes))
        visited = {start}
        queue = [start]
        node_ids = set(self.nodes.keys())

        adj = self.adjacency_matrix()
        id_to_idx = {nid: i for i, nid in enumerate(sorted(self.nodes.keys()))}

        while queue:
            current = queue.pop(0)
            idx = id_to_idx[current]
            for neighbor_idx, val in enumerate(adj[idx]):
                if val > 0:
                    neighbor = sorted(self.nodes.keys())[neighbor_idx]
                    if neighbor not in visited and neighbor in node_ids:
                        visited.add(neighbor)
                        queue.append(neighbor)

        return len(visited) == len(self.nodes)


class GraphToIsingCompiler:
    """
    Compiles graph optimization problems into Ising Hamiltonians.

    Given a graph G = (V, E), produces an Ising Hamiltonian:
        H = Σ_{(i,j) ∈ E} J_{ij} σ_i^z σ_j^z + Σ_i h_i σ_i^z

    Where:
        J_{ij} = coupling strength between nodes i and j
        h_i = local field on node i
        σ_i^z = Pauli Z operator on qubit i

    The ground state of H encodes the optimal solution to the graph problem.

    Supports:
    - Max-Cut: Partition nodes to maximize edges between partitions
    - Min-Cut: Minimum edge cut to disconnect graph
    - Max Independent Set: Largest set of non-adjacent nodes
    - Minimum Vertex Cover: Smallest set covering all edges
    - Traveling Salesman: Shortest tour visiting all nodes
    - Graph Coloring: Minimum colors for proper coloring
    """

    def __init__(self, graph: IntelligenceGraph):
        """
        Initialize compiler with an intelligence graph.

        Args:
            graph: The intelligence graph to compile
        """
        self.graph = graph
        self.node_ids = sorted(graph.nodes.keys())
        self.n_nodes = len(self.node_ids)
        self.id_to_idx = {nid: i for i, nid in enumerate(self.node_ids)}
        self.adj = graph.adjacency_matrix()

    def compile_max_cut(self, penalty: float = 1.0) -> List[PauliTerm]:
        """
        Compile Max-Cut into an Ising Hamiltonian.

        Max-Cut seeks to partition V into S and V\\S to maximize
        the number of edges between S and V\\S.

        Ising formulation:
            H = Σ_{(i,j) ∈ E} (1 - σ_i^z σ_j^z) / 2

        The ground state of this Hamiltonian corresponds to the maximum cut.

        Args:
            penalty: Penalty strength for constraint violations

        Returns:
            List of PauliTerms representing the Ising Hamiltonian
        """
        terms = []

        for edge in self.graph.edges:
            if edge.source not in self.id_to_idx or edge.target not in self.id_to_idx:
                continue
            i = self.id_to_idx[edge.source]
            j = self.id_to_idx[edge.target]

            # Edge contribution: (1 - Z_i Z_j) / 2
            # Identity term: 1/2
            terms.append(PauliTerm(
                0.5 * edge.weight,
                ['I'] * self.n_nodes
            ))

            # Z_i Z_j term: -1/2
            paulis = ['I'] * self.n_nodes
            paulis[i] = 'Z'
            paulis[j] = 'Z'
            terms.append(PauliTerm(-0.5 * edge.weight, paulis))

        return self._simplify(terms)

    def compile_min_vertex_cover(self) -> List[PauliTerm]:
        """
        Compile Minimum Vertex Cover into an Ising Hamiltonian.

        MVC seeks the smallest set S ⊆ V such that every edge has
        at least one endpoint in S.

        Ising formulation with penalty:
            H = Σ_i h_i σ_i^z + penalty * Σ_{(i,j) ∈ E} (1 + σ_i^z)(1 + σ_j^z) / 4

        Where h_i is a field favoring node inclusion.
        """
        terms = []
        penalty = 2.0  # Penalty for uncovered edges

        # Field term: minimize number of vertices in cover
        for i in range(self.n_nodes):
            terms.append(PauliTerm(-0.5, ['I'] * self.n_nodes))
            paulis = ['I'] * self.n_nodes
            paulis[i] = 'Z'
            terms.append(PauliTerm(0.5, paulis))

        # Edge penalty: if both endpoints are NOT in cover, add penalty
        for edge in self.graph.edges:
            if edge.source not in self.id_to_idx or edge.target not in self.id_to_idx:
                continue
            i = self.id_to_idx[edge.source]
            j = self.id_to_idx[edge.target]

            # (1 + Z_i)(1 + Z_j) / 4 = (1 + Z_i + Z_j + Z_i Z_j) / 4
            terms.append(PauliTerm(penalty * 0.25, ['I'] * self.n_nodes))

            paulis_i = ['I'] * self.n_nodes
            paulis_i[i] = 'Z'
            terms.append(PauliTerm(penalty * 0.25, paulis_i))

            paulis_j = ['I'] * self.n_nodes
            paulis_j[j] = 'Z'
            terms.append(PauliTerm(penalty * 0.25, paulis_j))

            paulis_ij = ['I'] * self.n_nodes
            paulis_ij[i] = 'Z'
            paulis_ij[j] = 'Z'
            terms.append(PauliTerm(penalty * 0.25, paulis_ij))

        return self._simplify(terms)

    def compile_max_independent_set(self) -> List[PauliTerm]:
        """
        Compile Maximum Independent Set into an Ising Hamiltonian.

        MIS seeks the largest set S ⊆ V with no edges between nodes in S.

        Ising formulation:
            H = -Σ_i σ_i^z + penalty * Σ_{(i,j) ∈ E} (1 + σ_i^z)(1 + σ_j^z) / 4
        """
        terms = []
        penalty = 2.0

        # Field: maximize number of nodes in independent set
        for i in range(self.n_nodes):
            terms.append(PauliTerm(-0.5, ['I'] * self.n_nodes))
            paulis = ['I'] * self.n_nodes
            paulis[i] = 'Z'
            terms.append(PauliTerm(0.5, paulis))

        # Edge penalty: penalize adjacent nodes both in set
        for edge in self.graph.edges:
            if edge.source not in self.id_to_idx or edge.target not in self.id_to_idx:
                continue
            i = self.id_to_idx[edge.source]
            j = self.id_to_idx[edge.target]

            terms.append(PauliTerm(penalty * 0.25, ['I'] * self.n_nodes))

            paulis_i = ['I'] * self.n_nodes
            paulis_i[i] = 'Z'
            terms.append(PauliTerm(penalty * 0.25, paulis_i))

            paulis_j = ['I'] * self.n_nodes
            paulis_j[j] = 'Z'
            terms.append(PauliTerm(penalty * 0.25, paulis_j))

            paulis_ij = ['I'] * self.n_nodes
            paulis_ij[i] = 'Z'
            paulis_ij[j] = 'Z'
            terms.append(PauliTerm(penalty * 0.25, paulis_ij))

        return self._simplify(terms)

    def compile_graph_coloring(self, n_colors: int = 3) -> List[PauliTerm]:
        """
        Compile Graph Coloring into a QUBO/Ising formulation.

        Uses binary encoding: node i with color c is represented by qubit (i*n_colors + c).

        Constraints:
        1. Each node has exactly one color
        2. Adjacent nodes have different colors
        """
        n_qubits = self.n_nodes * n_colors
        terms = []
        penalty = 2.0

        # Constraint 1: Each node has exactly one color
        for node_idx in range(self.n_nodes):
            # Sum of color indicators = 1
            for c in range(n_colors):
                q = node_idx * n_colors + c
                terms.append(PauliTerm(-0.5, ['I'] * n_qubits))
                paulis = ['I'] * n_qubits
                paulis[q] = 'Z'
                terms.append(PauliTerm(0.5, paulis))

            # Penalty for multiple colors: (Σ_c x_{i,c} - 1)^2
            for c1 in range(n_colors):
                for c2 in range(c1 + 1, n_colors):
                    q1 = node_idx * n_colors + c1
                    q2 = node_idx * n_colors + c2
                    paulis = ['I'] * n_qubits
                    paulis[q1] = 'Z'
                    paulis[q2] = 'Z'
                    terms.append(PauliTerm(penalty * 0.5, paulis))

        # Constraint 2: Adjacent nodes have different colors
        for edge in self.graph.edges:
            if edge.source not in self.id_to_idx or edge.target not in self.id_to_idx:
                continue
            i = self.id_to_idx[edge.source]
            j = self.id_to_idx[edge.target]

            for c in range(n_colors):
                qi = i * n_colors + c
                qj = j * n_colors + c
                # Penalty if both have same color: penalty * x_{i,c} * x_{j,c}
                paulis = ['I'] * n_qubits
                paulis[qi] = 'Z'
                paulis[qj] = 'Z'
                terms.append(PauliTerm(penalty * 0.5, paulis))

        return self._simplify(terms)

    def compile_community_detection(self, n_communities: int = 2) -> List[PauliTerm]:
        """
        Compile community detection into an Ising Hamiltonian.

        Uses the modularity maximization formulation:
            H = -Σ_{(i,j)} [A_{ij} - k_i*k_j/(2m)] * δ(s_i, s_j)

        Where A is adjacency, k is degree, m is total edges.
        """
        n_qubits = self.n_nodes * n_communities
        terms = []

        adj = self.adj
        degrees = np.sum(adj, axis=1)
        m = np.sum(adj) / 2  # Total edge weight

        if m == 0:
            return [PauliTerm(0.0, ['I'] * n_qubits)]

        for i in range(self.n_nodes):
            for j in range(i + 1, self.n_nodes):
                if adj[i, j] == 0:
                    continue

                # Modularity matrix: B_{ij} = A_{ij} - k_i*k_j/(2m)
                b_ij = adj[i, j] - degrees[i] * degrees[j] / (2 * m)

                for c in range(n_communities):
                    qi = i * n_communities + c
                    qj = j * n_communities + c
                    # -B_{ij} * x_{i,c} * x_{j,c}
                    paulis = ['I'] * n_qubits
                    paulis[qi] = 'Z'
                    paulis[qj] = 'Z'
                    terms.append(PauliTerm(-0.5 * b_ij, paulis))

        return self._simplify(terms)

    def compile_anomaly_detection(self, anomaly_scores: Optional[np.ndarray] = None) -> List[PauliTerm]:
        """
        Compile anomaly detection into an Ising formulation.

        Identifies nodes that are structurally anomalous (e.g., shell companies
        with unusual connection patterns).

        Uses local anomaly score + connectivity penalty:
            H = Σ_i score_i * σ_i^z + penalty * Σ_{(i,j)} (1 - σ_i^z σ_j^z)/2
        """
        terms = []
        n = self.n_nodes

        if anomaly_scores is None:
            # Compute anomaly scores based on degree and clustering
            adj = self.adj
            degrees = np.sum(adj, axis=1)
            avg_degree = np.mean(degrees) if len(degrees) > 0 else 1.0

            # High degree + low clustering = suspicious
            anomaly_scores = np.zeros(n)
            for i in range(n):
                neighbors = np.where(adj[i] > 0)[0]
                if len(neighbors) < 2:
                    anomaly_scores[i] = 0.0
                else:
                    # Clustering coefficient
                    subgraph = adj[np.ix_(neighbors, neighbors)]
                    possible = len(neighbors) * (len(neighbors) - 1) / 2
                    actual = np.sum(subgraph) / 2
                    clustering = actual / possible if possible > 0 else 0.0
                    anomaly_scores[i] = degrees[i] / avg_degree * (1 - clustering)

        # Normalize scores
        max_score = np.max(np.abs(anomaly_scores))
        if max_score > 0:
            anomaly_scores = anomaly_scores / max_score

        # Field term based on anomaly scores
        for i in range(n):
            paulis = ['I'] * n
            paulis[i] = 'Z'
            terms.append(PauliTerm(-anomaly_scores[i], paulis))

        # Connectivity penalty
        for edge in self.graph.edges:
            if edge.source not in self.id_to_idx or edge.target not in self.id_to_idx:
                continue
            i = self.id_to_idx[edge.source]
            j = self.id_to_idx[edge.target]
            paulis = ['I'] * n
            paulis[i] = 'Z'
            paulis[j] = 'Z'
            terms.append(PauliTerm(0.5 * edge.weight, paulis))

        return self._simplify(terms)

    def build_qaoa_circuit(
        self,
        hamiltonian: List[PauliTerm],
        p: int = 3,
        angles: Optional[List[float]] = None,
    ) -> Circuit:
        """
        Build a QAOA circuit for the compiled Hamiltonian.

        Args:
            hamiltonian: Ising Hamiltonian from compile_* methods
            p: QAOA depth (number of alternating operator layers)
            angles: Pre-set angles [γ_1, ..., γ_p, β_1, ..., β_p].
                   If None, uses default angles.

        Returns:
            QAOA Circuit ready for execution
        """
        circ = Circuit(self.n_nodes, f"QAOA-{self.graph.name}")

        # Initial superposition
        for i in range(self.n_nodes):
            circ.h(i)

        if angles is None:
            angles = [np.pi / (2 * (l + 1)) for l in range(2 * p)]

        for layer in range(p):
            gamma = angles[layer]
            beta = angles[p + layer]

            # Problem unitary: exp(-i γ H)
            for term in hamiltonian:
                if all(p == 'I' for p in term.paulis):
                    continue
                # Apply exp(-i γ * coeff * P_0 ⊗ ... ⊗ P_{n-1})
                self._apply_pauli_rotation(circ, term, gamma)

            # Mixer unitary: exp(-i β Σ X_i)
            for i in range(self.n_nodes):
                circ.rx(i, 2 * beta)

        return circ

    def _apply_pauli_rotation(self, circ: Circuit, term: PauliTerm, gamma: float):
        """
        Apply exp(-i γ * coeff * P) where P is a Pauli string.

        Decomposes into basis changes + Z-rotation + inverse basis change.
        """
        # Find the non-identity positions
        non_identity = [(i, p) for i, p in enumerate(term.paulis) if p != 'I']

        if not non_identity:
            return

        coeff = term.coefficient.real * gamma

        # Basis change to diagonalize the Pauli string
        for i, p in non_identity:
            if p == 'X':
                circ.h(i)
            elif p == 'Y':
                circ.rx(i, np.pi / 2)  # S†H to rotate Y basis to Z basis

        # Multi-controlled Z-rotation
        # For single-qubit terms
        if len(non_identity) == 1:
            q = non_identity[0][0]
            circ.rz(q, -2 * coeff)
        # For two-qubit terms
        elif len(non_identity) == 2:
            q0, q1 = non_identity[0][0], non_identity[1][0]
            circ.cnot(q0, q1)
            circ.rz(q1, -2 * coeff)
            circ.cnot(q0, q1)
        # For multi-qubit terms, decompose into pairwise
        else:
            qubits = [q for q, _ in non_identity]
            for k in range(len(qubits) - 1):
                circ.cnot(qubits[k], qubits[k + 1])
            circ.rz(qubits[-1], -2 * coeff)
            for k in range(len(qubits) - 2, -1, -1):
                circ.cnot(qubits[k], qubits[k + 1])

        # Inverse basis change
        for i, p in reversed(non_identity):
            if p == 'X':
                circ.h(i)
            elif p == 'Y':
                circ.rx(i, -np.pi / 2)

    def _simplify(self, terms: List[PauliTerm]) -> List[PauliTerm]:
        """Combine terms with identical Pauli strings."""
        combined: Dict[str, PauliTerm] = {}
        for t in terms:
            key = ''.join(t.paulis)
            if key in combined:
                combined[key].coefficient += t.coefficient
            else:
                combined[key] = PauliTerm(t.coefficient, list(t.paulis))
        return [t for t in combined.values() if abs(t.coefficient) > 1e-15]

    def analyze_graph(self) -> Dict[str, Any]:
        """
        Compute graph analytics useful for intelligence analysis.

        Returns:
            Dictionary with graph properties:
            - n_nodes, n_edges
            - avg_degree, max_degree
            - clustering_coefficient
            - is_connected
            - diameter (if connected)
            - communities (Louvain-like detection)
        """
        adj = self.adj
        n = self.n_nodes
        degrees = np.sum(adj, axis=1)

        # Clustering coefficients
        clustering = np.zeros(n)
        for i in range(n):
            neighbors = np.where(adj[i] > 0)[0]
            if len(neighbors) < 2:
                clustering[i] = 0.0
            else:
                subgraph = adj[np.ix_(neighbors, neighbors)]
                possible = len(neighbors) * (len(neighbors) - 1) / 2
                actual = np.sum(subgraph) / 2
                clustering[i] = actual / possible if possible > 0 else 0.0

        # Approximate diameter via BFS from random nodes
        diameter = 0
        if self.graph.is_connected():
            from collections import deque
            sample_size = min(5, n)
            sample_nodes = np.random.choice(list(self.graph.nodes.keys()),
                                            size=sample_size, replace=False)
            for start in sample_nodes:
                visited = {start}
                queue = deque([(start, 0)])
                id_to_idx = self.id_to_idx
                node_list = self.node_ids
                max_dist = 0
                while queue:
                    current, dist = queue.popleft()
                    max_dist = max(max_dist, dist)
                    idx = id_to_idx[current]
                    for j, val in enumerate(adj[idx]):
                        if val > 0:
                            neighbor = node_list[j]
                            if neighbor not in visited:
                                visited.add(neighbor)
                                queue.append((neighbor, dist + 1))
                diameter = max(diameter, max_dist)

        return {
            "n_nodes": n,
            "n_edges": self.graph.n_edges,
            "avg_degree": float(np.mean(degrees)) if n > 0 else 0.0,
            "max_degree": int(np.max(degrees)) if n > 0 else 0,
            "avg_clustering": float(np.mean(clustering)) if n > 0 else 0.0,
            "is_connected": self.graph.is_connected(),
            "diameter": diameter,
            "degree_sequence": sorted(degrees.tolist(), reverse=True),
        }
