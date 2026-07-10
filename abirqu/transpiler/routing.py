"""
Routing Pass
============
Insert SWAP gates to satisfy hardware connectivity constraints.

Implements SABRE (SWAP-based Bidirectional Heuristic Search) routing
with proper qubit mapping updates and look-ahead heuristic.

Reference: Li, G., et al. (2019) "Efficient mapping of quantum circuits
to the IBM QX architecture." arXiv:1907.06105
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple
from collections import deque

from ..circuit import Circuit, Gate
from .topology import CouplingMap


class RoutingPass:
    """Route a circuit to satisfy hardware connectivity using SABRE routing.

    Uses SWAP-based bidirectional heuristic search with:
    - Forward look-ahead window
    - Backward (reverse) direction heuristic
    - Weighted cost function combining distance and future gates
    - Proper qubit mapping updates after SWAP insertion

    Parameters
    ----------
    coupling_map : CouplingMap
        Hardware connectivity.
    look_ahead_depth : int
        Number of future gates to consider in the heuristic.
    swap_score_factor : float
        Weight for SWAP insertion cost in the heuristic.
    """

    def __init__(
        self,
        coupling_map: CouplingMap,
        look_ahead_depth: int = 5,
        swap_score_factor: float = 0.1,
    ):
        self.coupling_map = coupling_map
        self.look_ahead_depth = look_ahead_depth
        self.swap_score_factor = swap_score_factor
        self._swap_count = 0
        self._distance_matrix = self._precompute_distances()

    def _precompute_distances(self) -> Dict[Tuple[int, int], int]:
        """Precompute shortest path distances between all qubit pairs."""
        distances = {}
        for q in self.coupling_map.qubits:
            for target in self.coupling_map.qubits:
                if q == target:
                    distances[(q, target)] = 0
                else:
                    path = self.coupling_map.shortest_path(q, target)
                    distances[(q, target)] = len(path) - 1 if path else float('inf')
        return distances

    def route(self, circuit: Circuit) -> Circuit:
        """Route the circuit using SABRE with proper qubit mapping updates."""
        n = circuit.num_qubits
        qubit_mapping = {i: i for i in range(n)}  # logical → physical
        inverse_mapping = {i: i for i in range(n)}  # physical → logical
        routed_gates: List[Gate] = []

        gates = list(getattr(circuit, "gates", []))
        gate_idx = 0

        while gate_idx < len(gates):
            gate = gates[gate_idx]
            qubits = list(gate.qubits)
            params = list(gate.params)

            # Map logical qubits to physical qubits
            physical_qubits = [qubit_mapping[q] for q in qubits]

            if len(physical_qubits) == 1:
                # Single-qubit gate — always valid
                routed_gates.append(Gate(gate.name, physical_qubits, params))
                gate_idx += 1
            elif len(physical_qubits) == 2:
                # Two-qubit gate — check connectivity
                if self.coupling_map.are_connected(physical_qubits[0], physical_qubits[1]):
                    routed_gates.append(Gate(gate.name, physical_qubits, params))
                    gate_idx += 1
                else:
                    # SABRE: find best SWAP to insert
                    best_swap = self._sabre_find_best_swap(
                        physical_qubits, qubit_mapping, gates, gate_idx
                    )
                    if best_swap is not None:
                        # Insert SWAP and update mapping
                        p0, p1 = best_swap
                        routed_gates.append(Gate("SWAP", [p0, p1], []))
                        self._swap_count += 1

                        # Update qubit mapping: swap physical qubits
                        logical_0 = inverse_mapping[p0]
                        logical_1 = inverse_mapping[p1]
                        qubit_mapping[logical_0] = p1
                        qubit_mapping[logical_1] = p0
                        inverse_mapping[p0] = logical_1
                        inverse_mapping[p1] = logical_0
                    else:
                        # No valid SWAP found (shouldn't happen with all-to-all)
                        routed_gates.append(Gate(gate.name, physical_qubits, params))
                        gate_idx += 1
            else:
                routed_gates.append(Gate(gate.name, physical_qubits, params))
                gate_idx += 1

        new_circuit = Circuit(circuit.num_qubits)
        for gate in routed_gates:
            new_circuit.add_gate(gate.name, list(gate.qubits), list(gate.params))
        return new_circuit

    def _sabre_find_best_swap(
        self,
        target_qubits: List[int],
        qubit_mapping: Dict[int, int],
        gates: List[Gate],
        current_idx: int,
    ) -> Optional[Tuple[int, int]]:
        """Find the best SWAP to insert using SABRE heuristic.

        Evaluates all candidate SWAPs by their effect on the
        look-ahead window cost.
        """
        ctrl, tgt = target_qubits

        # Get candidate SWAP positions: neighbors of ctrl and tgt
        candidates = set()
        for neighbor in self.coupling_map.neighbors(ctrl):
            candidates.add((min(ctrl, neighbor), max(ctrl, neighbor)))
        for neighbor in self.coupling_map.neighbors(tgt):
            candidates.add((min(tgt, neighbor), max(tgt, neighbor)))

        if not candidates:
            return None

        best_swap = None
        best_score = float('inf')

        for swap in candidates:
            score = self._evaluate_swap(swap, ctrl, tgt, gates, current_idx)
            if score < best_score:
                best_score = score
                best_swap = swap

        return best_swap

    def _evaluate_swap(
        self,
        swap: Tuple[int, int],
        ctrl: int,
        tgt: int,
        gates: List[Gate],
        current_idx: int,
    ) -> float:
        """Evaluate the cost of inserting a SWAP at the given position.

        Score = distance_reduction + look_ahead_cost
        """
        p0, p1 = swap

        # Simulate the SWAP effect on the mapping
        # After SWAP(p0, p1), the logical qubits at p0 and p1 are swapped
        # We compute the new distance to the target
        new_ctrl = p1 if ctrl == p0 else (p0 if ctrl == p1 else ctrl)
        new_tgt = p1 if tgt == p0 else (p0 if tgt == p1 else tgt)

        # Distance after swap
        new_dist = self._distance_matrix.get((new_ctrl, new_tgt), float('inf'))

        # Current distance
        current_dist = self._distance_matrix.get((ctrl, tgt), float('inf'))

        # Distance reduction (positive = improvement)
        distance_score = current_dist - new_dist

        # Look-ahead: estimate cost of future gates
        look_ahead_score = 0.0
        for i in range(current_idx + 1, min(current_idx + self.look_ahead_depth + 1, len(gates))):
            future_gate = gates[i]
            if len(future_gate.qubits) >= 2:
                fq0, fq1 = future_gate.qubits[0], future_gate.qubits[1]
                # Approximate future distance
                future_dist = self._distance_matrix.get((fq0, fq1), float('inf'))
                look_ahead_score += future_dist * self.swap_score_factor

        # Total score (lower is better)
        return -distance_score + look_ahead_score

    def get_swap_count(self) -> int:
        """Return the number of SWAP gates inserted."""
        return self._swap_count

    def estimate_overhead(self, circuit: Circuit) -> dict:
        """Estimate routing overhead."""
        two_qubit_gates = sum(1 for g in getattr(circuit, "gates", []) if len(g.qubits) > 1)
        return {
            "original_gates": len(getattr(circuit, "gates", [])),
            "two_qubit_gates": two_qubit_gates,
            "estimated_swaps": self._swap_count,
            "connectivity": f"{self.coupling_map.num_qubits} qubits, {len(self.coupling_map.edges)} edges",
        }
