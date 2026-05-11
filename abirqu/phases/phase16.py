from typing import Any, Dict, Iterable, List, Sequence

from ..circuit import Circuit


class PhotonicBackendCompiler:
    def compile(self, circuit: Circuit) -> Dict[str, Any]:
        return {
            "backend": "photonic",
            "mode": "linear-optics",
            "operations": len(circuit.gates),
            "loss_model": "photon-loss-gaussian",
        }

    def gaussian_boson_sampling(self, modes: int, photons: int) -> Dict[str, Any]:
        return {"modes": modes, "photons": photons, "supported": photons <= modes}


class TopologicalBackendCompiler:
    def compile_braiding(self, braid_sequence: Sequence[str]) -> Dict[str, Any]:
        return {"backend": "topological", "braids": list(braid_sequence), "depth": len(braid_sequence)}

    def fusion_model(self, anyon_pairs: int) -> Dict[str, Any]:
        return {"anyon_pairs": anyon_pairs, "fusion_steps": max(0, anyon_pairs - 1)}


class QuantumAnnealingBackend:
    def qubo_to_ising(self, qubo: List[List[float]]) -> Dict[str, Any]:
        n = len(qubo)
        h = [float(qubo[i][i]) for i in range(n)]
        j = []
        for i in range(n):
            for k in range(i + 1, n):
                if qubo[i][k] != 0:
                    j.append((i, k, float(qubo[i][k] / 2.0)))
        return {"h": h, "J": j}

    def compile_native(self, qubo: List[List[float]]) -> Dict[str, Any]:
        return {"backend": "annealing", "ising": self.qubo_to_ising(qubo), "target": "D-Wave-compatible"}


class MeasurementBasedCompiler:
    def cluster_state_plan(self, qubits: int) -> Dict[str, Any]:
        return {"cluster_nodes": qubits, "cluster_edges": max(0, qubits - 1)}

    def compile_measurement_pattern(self, circuit: Circuit) -> Dict[str, Any]:
        pattern = [{"gate": g.name, "measure_basis": "X" if g.name == "H" else "Z"} for g in circuit.gates]
        return {"pattern": pattern, "steps": len(pattern)}


class ArchitectureOptimizationPasses:
    def optimize(self, circuit: Circuit, architecture: str) -> Dict[str, Any]:
        reductions = {
            "photonic": 0.9,
            "topological": 0.85,
            "annealing": 1.0,
            "mbqc": 0.88,
        }
        factor = reductions.get(architecture, 1.0)
        return {
            "architecture": architecture,
            "original_gates": len(circuit.gates),
            "estimated_gates": int(len(circuit.gates) * factor),
        }

    def translate(self, circuit: Circuit, source: str, target: str) -> Dict[str, Any]:
        return {"source": source, "target": target, "operation_count": len(circuit.gates), "compatible": True}

    def compare_architectures(self, circuit: Circuit, architectures: Iterable[str]) -> List[Dict[str, Any]]:
        rows = [self.optimize(circuit, a) for a in architectures]
        return sorted(rows, key=lambda x: x["estimated_gates"])
