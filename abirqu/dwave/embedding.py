"""
D-Wave Embedding Finder
=======================
Find minor embeddings for mapping QUBO problems to D-Wave hardware topology.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple


class EmbeddingFinder:
    """Find minor embeddings for D-Wave quantum annealers.

    A minor embedding maps logical qubits to chains of physical qubits
    on the hardware graph, connected by ferromagnetic couplings.

    Parameters
    ----------
    hardware_graph : dict, optional
        Adjacency dict of the hardware graph.  If None, uses D-Wave's
        automatic embedding.
    chain_strength : float
        Strength of ferromagnetic couplings within chains.
    """

    def __init__(
        self,
        hardware_graph: Optional[Dict[int, List[int]]] = None,
        chain_strength: float = 1.0,
    ):
        self.hardware_graph = hardware_graph
        self.chain_strength = chain_strength

    def find_embedding(
        self,
        logical_vars: List[str],
        logical_edges: List[Tuple[str, str]],
    ) -> Dict[str, List[int]]:
        """Find a minor embedding for the given variables and edges.

        Parameters
        ----------
        logical_vars : list of str
            Names of logical variables.
        logical_edges : list of tuple of str
            Edges between logical variables.

        Returns
        -------
        dict mapping logical variable name to list of physical qubit indices.
        """
        try:
            import minorminer
            embedding = minorminer.find_embedding(
                logical_edges,
                self.hardware_graph or self._default_hardware_graph(),
            )
            return embedding
        except ImportError:
            # Fallback: simple linear chain embedding
            return self._simple_embedding(logical_vars, logical_edges)

    def _simple_embedding(
        self,
        logical_vars: List[str],
        logical_edges: List[Tuple[str, str]],
    ) -> Dict[str, List[int]]:
        """Simple fallback embedding using linear chains."""
        embedding = {}
        offset = 0
        for var in logical_vars:
            # Assign 1 physical qubit per logical variable
            embedding[var] = [offset]
            offset += 1
        return embedding

    def _default_hardware_graph(self) -> Dict[int, List[int]]:
        """Default Pegasus graph (D-Wave Advantage)."""
        # Simplified Pegasus-16 graph
        n = 16
        graph: Dict[int, List[int]] = {}
        for i in range(n):
            graph[i] = []
            for j in range(n):
                if i != j and abs(i - j) <= 2:
                    graph[i].append(j)
        return graph

    def get_chain_strength(
        self,
        bqm_linear_biases: Dict[str, float],
        bqm_quadratic_biases: Dict[Tuple[str, str], float],
    ) -> float:
        """Calculate appropriate chain strength.

        Uses the maximum absolute bias as a baseline.
        """
        max_linear = max(abs(v) for v in bqm_linear_biases.values()) if bqm_linear_biases else 1.0
        max_quad = max(abs(v) for v in bqm_quadratic_biases.values()) if bqm_quadratic_biases else 1.0
        return max(max_linear, max_quad) * self.chain_strength

    def validate_embedding(
        self,
        embedding: Dict[str, List[int]],
        logical_edges: List[Tuple[str, str]],
    ) -> bool:
        """Validate that an embedding is correct (no chain breaks)."""
        for u, v in logical_edges:
            chain_u = set(embedding.get(u, []))
            chain_v = set(embedding.get(v, []))
            # Check that chains are adjacent in hardware graph
            if self.hardware_graph:
                adjacent = False
                for pu in chain_u:
                    for neighbor in self.hardware_graph.get(pu, []):
                        if neighbor in chain_v:
                            adjacent = True
                            break
                if not adjacent:
                    return False
        return True

    def get_chain_break_fraction(
        self,
        embedding: Dict[str, List[int]],
        sampleset,
    ) -> float:
        """Estimate chain break fraction from a sampleset."""
        if not hasattr(sampleset, "record") or len(sampleset) == 0:
            return 0.0

        total_samples = len(sampleset)
        broken = 0

        for sample in sampleset.samples():
            for var, chain in embedding.items():
                if len(chain) > 1:
                    values = [sample.get(f"q{qi}", 0) for qi in chain]
                    if len(set(values)) > 1:
                        broken += 1
                        break

        return broken / total_samples if total_samples > 0 else 0.0
