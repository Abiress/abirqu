"""
D-Wave QUBO Builder
===================
Build Quadratic Unconstrained Binary Optimization (QUBO) models
for D-Wave quantum annealers.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Union
import numpy as np


class QUBOBuilder:
    """Builder for QUBO (Quadratic Unconstrained Binary Optimization) problems.

    A QUBO problem is defined as:
        minimize  x^T Q x
    where Q is an upper-triangular matrix and x is a binary vector.

    Example
    -------
    >>> builder = QUBOBuilder(num_variables=3)
    >>> builder.set_linear(0, -1.0)  # x_0 bias
    >>> builder.set_linear(1, -1.0)  # x_1 bias
    >>> builder.set_quadratic(0, 1, 2.0)  # x_0 * x_1 coupling
    >>> qubo = builder.build()
    """

    def __init__(self, num_variables: int):
        self.n = num_variables
        self._linear: Dict[int, float] = {}
        self._quadratic: Dict[Tuple[int, int], float] = {}
        self._offset: float = 0.0

    def set_linear(self, i: int, bias: float) -> "QUBOBuilder":
        """Set the linear bias for variable i."""
        self._linear[i] = self._linear.get(i, 0.0) + bias
        return self

    def set_quadratic(self, i: int, j: int, bias: float) -> "QUBOBuilder":
        """Set the quadratic bias between variables i and j (i < j)."""
        key = (min(i, j), max(i, j))
        self._quadratic[key] = self._quadratic.get(key, 0.0) + bias
        return self

    def set_offset(self, offset: float) -> "QUBOBuilder":
        """Set a constant offset."""
        self._offset += offset
        return self

    def add_penalty(
        self,
        penalty: float,
        constraint_type: str = "equality",
        target: float = 0.0,
    ) -> "QUBOBuilder":
        """Add a penalty term for constraint enforcement.

        Parameters
        ----------
        penalty : float
            Penalty strength (must be > 0).
        constraint_type : str
            ``'equality'`` for sum(x_i) == target,
            ``'inequality'`` for sum(x_i) <= target.
        target : float
            Target value for the constraint.
        """
        if constraint_type == "equality":
            # P * (sum(x_i) - target)^2
            for i in range(self.n):
                self.set_linear(i, penalty * (1 - 2 * target))
                for j in range(i + 1, self.n):
                    self.set_quadratic(i, j, 2 * penalty)
            self._offset += penalty * target * target
        elif constraint_type == "inequality":
            # For sum(x_i) <= target, add slack variables
            pass
        return self

    def from_dict(
        self,
        linear: Dict[int, float],
        quadratic: Dict[Tuple[int, int], float],
        offset: float = 0.0,
    ) -> "QUBOBuilder":
        """Load QUBO from dictionaries."""
        self._linear.update(linear)
        self._quadratic.update(quadratic)
        self._offset += offset
        return self

    def from_matrix(self, Q: np.ndarray) -> "QUBOBuilder":
        """Load QUBO from an upper-triangular matrix."""
        n = Q.shape[0]
        self.n = max(self.n, n)
        for i in range(n):
            if Q[i, i] != 0:
                self.set_linear(i, float(Q[i, i]))
            for j in range(i + 1, n):
                if Q[i, j] != 0:
                    self.set_quadratic(i, j, float(Q[i, j]))
        return self

    def build(self) -> Dict:
        """Build the QUBO problem.

        Returns
        -------
        dict with keys:
            linear      – Dict[int, float]
            quadratic   – Dict[Tuple[int,int], float]
            offset      – float
            num_variables – int
        """
        return {
            "linear": dict(self._linear),
            "quadratic": dict(self._quadratic),
            "offset": self._offset,
            "num_variables": self.n,
        }

    def to_qubo_dict(self) -> Dict[Tuple[str, str], float]:
        """Build QUBO as a dictionary with string keys for D-Wave API."""
        qubo: Dict[Tuple[str, str], float] = {}
        for i, bias in self._linear.items():
            qubo[(f"x{i}", f"x{i}")] = bias
        for (i, j), bias in self._quadratic.items():
            qubo[(f"x{i}", f"x{j}")] = bias
        return qubo

    def to_ising(self) -> Tuple[Dict[str, float], Dict[Tuple[str, str], float]]:
        """Convert QUBO to Ising model (spin variables).

        Returns
        -------
        (linear, quadratic) where:
            linear     – Dict[str, float] with spin biases
            quadratic  – Dict[Tuple[str,str], float] with spin couplings
        """
        linear: Dict[str, float] = {}
        quadratic: Dict[Tuple[str, str], float] = {}

        # QUBO to Ising: x_i = (s_i + 1) / 2
        for i, bias in self._linear.items():
            linear[f"s{i}"] = linear.get(f"s{i}", 0.0) + bias / 2

        for (i, j), bias in self._quadratic.items():
            quadratic[(f"s{i}", f"s{j}")] = quadratic.get((f"s{i}", f"s{j}"), 0.0) + bias / 4

        # Offset adjustment
        total_linear = sum(self._linear.values())
        total_quadratic = sum(self._quadratic.values())
        offset_correction = total_linear / 2 + total_quadratic / 4

        return linear, quadratic

    @classmethod
    def from_max_cut(cls, edges: List[Tuple[int, int]], num_nodes: int) -> "QUBOBuilder":
        """Create a MaxCut QUBO from a graph edge list."""
        builder = cls(num_variables=num_nodes)
        for i, j in edges:
            builder.set_linear(i, -1.0)
            builder.set_linear(j, -1.0)
            builder.set_quadratic(i, j, 2.0)
        return builder

    @classmethod
    def from_tsp(cls, distances: np.ndarray, num_cities: int) -> "QUBOBuilder":
        """Create a TSP QUBO from a distance matrix.

        Uses n^2 binary variables where x_{i,j} = 1 iff city i is
        visited at position j.
        """
        n = num_cities
        builder = QUBOBuilder(num_variables=n * n)

        # Constraint 1: each city visited exactly once
        for i in range(n):
            for j in range(n):
                builder.set_linear(i * n + j, -1.0)
            for j1 in range(n):
                for j2 in range(j1 + 1, n):
                    builder.set_quadratic(i * n + j1, i * n + j2, 2.0)

        # Constraint 2: each position occupied exactly once
        for j in range(n):
            for i1 in range(n):
                for i2 in range(i1 + 1, n):
                    builder.set_quadratic(i1 * n + j, i2 * n + j, 2.0)

        # Objective: minimize total distance
        for i1 in range(n):
            for i2 in range(n):
                if i1 != i2:
                    for j1 in range(n):
                        j2 = (j1 + 1) % n
                        builder.set_quadratic(
                            i1 * n + j1, i2 * n + j2,
                            float(distances[i1, i2])
                        )

        return builder
