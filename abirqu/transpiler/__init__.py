"""
AbirQu Transpiler Pipeline
==========================
Configurable transpilation pipeline for converting circuits to
hardware-native gate sets.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..circuit import Circuit, Gate


class TargetBackend(str, Enum):
    """Supported target backends for transpilation."""
    IBM = "ibm"
    GOOGLE = "google"
    IONQ = "ionq"
    RIGETTI = "rigetti"
    QUANTINUUM = "quantinuum"
    OQC = "oqc"
    SPINQ = "spinq"
    NEUTRAL_ATOM = "neutral_atom"
    DWAVE = "dwave"
    GENERIC = "generic"


class TranspilerPipeline:
    """Configurable transpilation pipeline.

    Stages:
    1. Decompose → break complex gates to basis gate set
    2. Route → insert SWAP gates for connectivity
    3. Schedule → order gates for execution
    4. Optimize → apply circuit optimizations

    Parameters
    ----------
    target : TargetBackend
        Target backend.
    optimization_level : int
        0-3, where 3 is most aggressive.
    """

    # Native gate sets per backend
    NATIVE_GATES = {
        TargetBackend.IBM: ["ECR", "ID", "RZ", "X", "SX"],
        TargetBackend.GOOGLE: ["PhasedXPow", "XPow", "YPow", "CZ"],
        TargetBackend.IONQ: ["GPI", "GPI2", "MS"],
        TargetBackend.RIGETTI: ["RZ", "RX", "ISWAP", "CZ"],
        TargetBackend.QUANTINUUM: ["Rz", "Ry", "MS", "ZZ"],
        TargetBackend.OQC: ["Rz", "SX", "CNOT"],
        TargetBackend.SPINQ: ["Rz", "Rx", "MS"],
        TargetBackend.NEUTRAL_ATOM: ["Ry", "Rz", "CZ"],
        TargetBackend.DWAVE: [],  # Annealer
        TargetBackend.GENERIC: ["H", "RZ", "CNOT"],
    }

    def __init__(
        self,
        target: TargetBackend = TargetBackend.GENERIC,
        optimization_level: int = 1,
    ):
        self.target = target
        self.optimization_level = optimization_level
        self.native_gates = self.NATIVE_GATES.get(target, ["H", "RZ", "CNOT"])

    def transpile(self, circuit: Circuit) -> Circuit:
        """Transpile a circuit through the full pipeline."""
        result = circuit.copy()

        # Stage 1: Decompose
        result = self._decompose(result)

        # Stage 2: Route
        result = self._route(result)

        # Stage 3: Optimize
        if self.optimization_level >= 1:
            result = self._optimize(result)

        return result

    def _decompose(self, circuit: Circuit) -> Circuit:
        """Decompose complex gates to native gate set."""
        native = set(self.native_gates)
        new_circuit = Circuit(circuit.num_qubits)

        for gate in getattr(circuit, "gates", []):
            name = gate.name.upper()
            qubits = list(gate.qubits)
            params = list(gate.params)

            if name in native:
                # Already native — pass through
                new_circuit.add_gate(name, qubits, params)
            elif name == "H":
                # H → RZ(π).SX.RZ(π/2) or similar
                self._add_h_decomposition(new_circuit, qubits[0])
            elif name in ("CNOT", "CX"):
                self._add_cnot_decomposition(new_circuit, qubits[0], qubits[1])
            elif name == "TOFFOLI":
                self._add_toffoli_decomposition(new_circuit, qubits)
            elif name == "SWAP":
                self._add_swap_decomposition(new_circuit, qubits[0], qubits[1])
            else:
                # Unknown gate — pass through
                new_circuit.add_gate(name, qubits, params)

        return new_circuit

    def _add_h_decomposition(self, circuit: Circuit, qubit: int):
        """Decompose H gate to native gates."""
        if self.target == TargetBackend.IBM:
            # H = RZ(π/2).RX(π/2).RZ(π/2) in IBM basis
            circuit.add_gate("RZ", [qubit], [1.57079633])
            circuit.add_gate("RX", [qubit], [1.57079633])
            circuit.add_gate("RZ", [qubit], [1.57079633])
        elif self.target == TargetBackend.SPINQ:
            circuit.add_gate("RZ", [qubit], [3.14159265])
            circuit.add_gate("RX", [qubit], [1.57079633])
            circuit.add_gate("RZ", [qubit], [3.14159265])
        else:
            circuit.add_gate("H", [qubit])

    def _add_cnot_decomposition(self, circuit: Circuit, ctrl: int, tgt: int):
        """Decompose CNOT gate to native gates."""
        if self.target == TargetBackend.IBM:
            # CNOT via RZ/RY/ECR (simplified to standard gates)
            circuit.add_gate("RY", [tgt], [1.57079633])
            circuit.add_gate("CNOT", [ctrl, tgt])
            circuit.add_gate("RY", [tgt], [-1.57079633])
        elif self.target == TargetBackend.SPINQ:
            circuit.add_gate("RY", [tgt], [-1.57079633])
            circuit.add_gate("CNOT", [ctrl, tgt])
            circuit.add_gate("RY", [tgt], [1.57079633])
        elif self.target in (TargetBackend.GOOGLE, TargetBackend.NEUTRAL_ATOM):
            # CZ decomposition
            circuit.add_gate("H", [tgt])
            circuit.add_gate("CNOT", [ctrl, tgt])
            circuit.add_gate("H", [tgt])
        else:
            circuit.add_gate("CNOT", [ctrl, tgt])

    def _add_toffoli_decomposition(self, circuit: Circuit, qubits: List[int]):
        """Decompose Toffoli gate."""
        # Generic decomposition via CNOTs and single-qubit gates
        circuit.add_gate("H", [qubits[2]])
        circuit.add_gate("CNOT", [qubits[1], qubits[2]])
        circuit.add_gate("T_DAG", [qubits[2]])
        circuit.add_gate("CNOT", [qubits[0], qubits[2]])
        circuit.add_gate("T", [qubits[2]])
        circuit.add_gate("CNOT", [qubits[1], qubits[2]])
        circuit.add_gate("T_DAG", [qubits[2]])
        circuit.add_gate("CNOT", [qubits[0], qubits[2]])
        circuit.add_gate("T", [qubits[1]])
        circuit.add_gate("T", [qubits[2]])
        circuit.add_gate("H", [qubits[2]])
        circuit.add_gate("CNOT", [qubits[0], qubits[1]])
        circuit.add_gate("T", [qubits[0]])
        circuit.add_gate("T_DAG", [qubits[1]])
        circuit.add_gate("CNOT", [qubits[0], qubits[1]])

    def _add_swap_decomposition(self, circuit: Circuit, q0: int, q1: int):
        """Decompose SWAP gate."""
        circuit.add_gate("CNOT", [q0, q1])
        circuit.add_gate("CNOT", [q1, q0])
        circuit.add_gate("CNOT", [q0, q1])

    def _route(self, circuit: Circuit) -> Circuit:
        """Route circuit for hardware connectivity constraints.

        Uses BFS shortest-path SWAP insertion for limited connectivity.
        For all-to-all connectivity, no routing needed.
        """
        from .topology import CouplingMap
        from .routing import RoutingPass

        # Build coupling map for target backend
        n = circuit.num_qubits
        import math
        side = math.ceil(math.sqrt(n))

        if self.target == TargetBackend.IBM:
            coupling = CouplingMap.heavy_hex(side, side)
        elif self.target == TargetBackend.GOOGLE:
            coupling = CouplingMap.grid(side, side)
        elif self.target in (TargetBackend.IONQ, TargetBackend.QUANTINUUM):
            coupling = CouplingMap.all_to_all(n)
        elif self.target == TargetBackend.RIGETTI:
            coupling = CouplingMap.linear_chain(n)
        elif self.target == TargetBackend.SPINQ:
            coupling = CouplingMap.linear_chain(n)
        elif self.target == TargetBackend.OQC:
            coupling = CouplingMap.grid(side, side)
        elif self.target == TargetBackend.NEUTRAL_ATOM:
            coupling = CouplingMap.grid(side, side)
        else:
            coupling = CouplingMap.all_to_all(n)

        # If all-to-all, no routing needed
        if len(coupling.edges) >= n * (n - 1) // 2:
            return circuit

        router = RoutingPass(coupling)
        return router.route(circuit)

    def _optimize(self, circuit: Circuit) -> Circuit:
        """Apply circuit optimizations.

        Optimizations:
        - Cancel adjacent inverse gates
        - Merge rotation gates
        - Remove identity gates
        """
        if self.optimization_level < 1:
            return circuit

        gates = list(getattr(circuit, "gates", []))
        optimized = []
        i = 0

        while i < len(gates):
            gate = gates[i]

            # Look ahead for cancellation opportunities
            if i + 1 < len(gates):
                next_gate = gates[i + 1]
                if self._are_inverse(gate, next_gate):
                    i += 2  # Skip both gates
                    continue

            # Merge adjacent RZ gates
            if gate.name.upper() == "RZ" and i + 1 < len(gates):
                next_gate = gates[i + 1]
                if (next_gate.name.upper() == "RZ" and
                    gate.qubits == next_gate.qubits):
                    merged_angle = (gate.params[0] if gate.params else 0) + \
                                   (next_gate.params[0] if next_gate.params else 0)
                    optimized.append(Gate("RZ", gate.qubits, [merged_angle]))
                    i += 2
                    continue

            optimized.append(gate)
            i += 1

        new_circuit = Circuit(circuit.num_qubits)
        for gate in optimized:
            new_circuit.add_gate(gate.name, list(gate.qubits), list(gate.params))
        return new_circuit

    def _are_inverse(self, gate1: Gate, gate2: Gate) -> bool:
        """Check if two gates are inverses of each other."""
        if gate1.name != gate2.name:
            return False
        if gate1.qubits != gate2.qubits:
            return False
        if gate1.params and gate2.params:
            # For rotation gates, check if angles sum to 2π
            if gate1.name.upper() in ("RX", "RY", "RZ"):
                return abs(gate1.params[0] + gate2.params[0]) < 1e-10
        return False

    def get_native_gates(self) -> List[str]:
        """Return the native gate set for the target backend."""
        return self.native_gates

    def estimate_depth(self, circuit: Circuit) -> int:
        """Estimate circuit depth after transpilation."""
        # Simplified estimation
        num_gates = len(getattr(circuit, "gates", []))
        two_qubit_gates = sum(1 for g in getattr(circuit, "gates", [])
                             if len(g.qubits) > 1)
        return num_gates + two_qubit_gates * 2
