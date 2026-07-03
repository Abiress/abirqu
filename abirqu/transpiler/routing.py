"""
Routing Pass
============
Insert SWAP gates to satisfy hardware connectivity constraints.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from ..circuit import Circuit, Gate
from .topology import CouplingMap


class RoutingPass:
    """Route a circuit to satisfy hardware connectivity.

    Uses a greedy SWAP-based routing algorithm.

    Parameters
    ----------
    coupling_map : CouplingMap
        Hardware connectivity.
    """

    def __init__(self, coupling_map: CouplingMap):
        self.coupling_map = coupling_map
        self._swap_count = 0

    def route(self, circuit: Circuit) -> Circuit:
        """Route the circuit, inserting SWAP gates as needed."""
        qubit_mapping = {i: i for i in range(circuit.num_qubits)}
        routed_gates: List[Gate] = []

        for gate in getattr(circuit, "gates", []):
            qubits = list(gate.qubits)
            params = list(gate.params)

            # Map logical qubits to physical qubits
            physical_qubits = [qubit_mapping[q] for q in qubits]

            if len(physical_qubits) == 1:
                # Single-qubit gate — always valid
                routed_gates.append(Gate(gate.name, physical_qubits, params))
            elif len(physical_qubits) == 2:
                # Two-qubit gate — check connectivity
                if self.coupling_map.are_connected(physical_qubits[0], physical_qubits[1]):
                    routed_gates.append(Gate(gate.name, physical_qubits, params))
                else:
                    # Need to insert SWAP gates
                    path = self.coupling_map.shortest_path(
                        physical_qubits[0], physical_qubits[1]
                    )
                    if len(path) > 1:
                        # Insert SWAPs along the path
                        for i in range(len(path) - 2):
                            routed_gates.append(Gate("SWAP", [path[i], path[i + 1]], []))
                            self._swap_count += 1
                        # Now the qubits should be connected
                        routed_gates.append(Gate(gate.name, physical_qubits, params))
                    else:
                        routed_gates.append(Gate(gate.name, physical_qubits, params))
            else:
                routed_gates.append(Gate(gate.name, physical_qubits, params))

        new_circuit = Circuit(circuit.num_qubits)
        for gate in routed_gates:
            new_circuit.add_gate(gate.name, list(gate.qubits), list(gate.params))
        return new_circuit

    def get_swap_count(self) -> int:
        """Return the number of SWAP gates inserted."""
        return self._swap_count

    def estimate_overhead(self, circuit: Circuit) -> dict:
        """Estimate routing overhead."""
        two_qubit_gates = sum(1 for g in getattr(circuit, "gates", []) if len(g.qubits) > 1)
        return {
            "original_gates": len(getattr(circuit, "gates", [])),
            "two_qubit_gates": two_qubit_gates,
            "estimated_swaps": two_qubit_gates * 2,  # rough estimate
            "connectivity": f"{self.coupling_map.num_qubits} qubits, {len(self.coupling_map.edges)} edges",
        }
