"""
D-Wave Hybrid Solver
====================
Wrap D-Wave Leap hybrid solvers for large-scale optimization problems.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from .qubo import QUBOBuilder


class HybridSolver:
    """D-Wave Leap hybrid solver wrapper.

    Hybrid solvers combine classical and quantum resources to solve
    problems larger than the QPU's qubit count.

    Parameters
    ----------
    token : str, optional
        D-Wave API token.  Falls back to DWAVE_API_TOKEN env var.
    solver_name : str
        Name of the hybrid solver, e.g.
        ``'hybrid_binary_quadratic_model_version2'`` or
        ``'hybrid_dqo_v2'``.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        solver_name: str = "hybrid_binary_quadratic_model_version2",
    ):
        self.token = token or os.getenv("DWAVE_API_TOKEN", "")
        self.solver_name = solver_name
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            from dwave.cloud import Client
            self._client = Client.from_config(token=self.token)
            return self._client
        except ImportError as exc:
            raise RuntimeError(
                "Hybrid solver requires 'dwave-ocean-sdk'. "
                "Install with: pip install dwave-ocean-sdk"
            ) from exc

    def solve_bqm(
        self,
        linear: Dict[str, float],
        quadratic: Dict[Tuple[str, str], float],
        time_limit: float = 5.0,
    ) -> Dict[str, Any]:
        """Solve a Binary Quadratic Model using the hybrid solver.

        Parameters
        ----------
        linear : dict
            Linear biases {variable: bias}.
        quadratic : dict
            Quadratic biases {(var_i, var_j): bias}.
        time_limit : float
            Time limit in seconds.

        Returns
        -------
        dict with keys: sample, energy, num_occurrences, timing.
        """
        try:
            from dwave.system import LeapHybridBQMSampler
        except ImportError as exc:
            raise RuntimeError(
                "Hybrid solver requires 'dwave-system'. "
                "Install with: pip install dwave-system"
            ) from exc

        from dimod import BinaryQuadraticModel

        bqm = BinaryQuadraticModel(linear, quadratic, "BINARY")

        sampler = LeapHybridBQMSampler(token=self.token)
        sampleset = sampler.sample(bqm, time_limit=time_limit)

        best = sampleset.first
        return {
            "sample": dict(best.sample),
            "energy": float(best.energy),
            "num_occurrences": best.num_occurrences,
            "timing": sampleset.info.get("timing", {}),
        }

    def solve_qubo(
        self,
        qubo: QUBOBuilder,
        time_limit: float = 5.0,
    ) -> Dict[str, Any]:
        """Solve a QUBOBuilder instance using the hybrid solver."""
        qubo_dict = qubo.build()
        linear_qubo = {f"x{i}": v for i, v in qubo_dict["linear"].items()}
        quadratic_qubo = {(f"x{i}", f"x{j}"): v for (i, j), v in qubo_dict["quadratic"].items()}
        return self.solve_bqm(
            linear=linear_qubo,
            quadratic=quadratic_qubo,
            time_limit=time_limit,
        )

    def solve_max_cut(
        self,
        edges: List[Tuple[int, int]],
        num_nodes: int,
        time_limit: float = 5.0,
    ) -> Dict[str, Any]:
        """Solve a MaxCut problem using the hybrid solver."""
        builder = QUBOBuilder.from_max_cut(edges, num_nodes)
        qubo_dict = builder.build()
        linear_qubo = {f"x{i}": v for i, v in qubo_dict["linear"].items()}
        quadratic_qubo = {(f"x{i}", f"x{j}"): v for (i, j), v in qubo_dict["quadratic"].items()}
        return self.solve_bqm(
            linear=linear_qubo,
            quadratic=quadratic_qubo,
            time_limit=time_limit,
        )

    def solve_ising(
        self,
        linear: Dict[str, float],
        quadratic: Dict[Tuple[str, str], float],
        time_limit: float = 5.0,
    ) -> Dict[str, Any]:
        """Solve an Ising model using the hybrid solver."""
        try:
            from dwave.system import LeapHybridIsingSampler
        except ImportError as exc:
            raise RuntimeError("dwave-system required.") from exc

        from dimod import BinaryQuadraticModel

        bqm = BinaryQuadraticModel(linear, quadratic, "SPIN")

        sampler = LeapHybridIsingSampler(token=self.token)
        sampleset = sampler.sample(bqm, time_limit=time_limit)

        best = sampleset.first
        return {
            "sample": dict(best.sample),
            "energy": float(best.energy),
            "num_occurrences": best.num_occurrences,
            "timing": sampleset.info.get("timing", {}),
        }

    def list_solvers(self) -> List[Dict[str, Any]]:
        """List available hybrid solvers."""
        try:
            client = self._get_client()
            solvers = client.get_solvers()
            return [
                {
                    "name": s.id,
                    "type": "hybrid",
                    "max_variables": getattr(s, "max_num_variables", None),
                }
                for s in solvers
                if "hybrid" in s.id
            ]
        except Exception:
            return [{"name": self.solver_name, "type": "hybrid"}]
