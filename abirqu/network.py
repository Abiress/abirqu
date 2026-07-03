"""Quantum network simulation and protocols."""

import math
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .circuit import Circuit


class QuantumNetworkSimulator:
    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.links: Dict[Tuple[str, str], Dict[str, float]] = {}

    def add_node(self, name: str, role: str = "router") -> None:
        self.nodes[name] = {"role": role}

    def connect(self, a: str, b: str, loss: float = 0.01, noise: float = 0.01, dark_counts: float = 0.0) -> None:
        self.links[(a, b)] = {"loss": loss, "noise": noise, "dark_counts": dark_counts}
        self.links[(b, a)] = {"loss": loss, "noise": noise, "dark_counts": dark_counts}

    def distribute_entanglement(self, path: Sequence[str], initial_fidelity: float = 0.99) -> Dict[str, Any]:
        fid = initial_fidelity
        for i in range(len(path) - 1):
            edge = self.links[(path[i], path[i + 1])]
            fid *= (1.0 - edge["loss"]) * (1.0 - edge["noise"]) * (1.0 - edge["dark_counts"])
        return {"path": list(path), "fidelity": max(0.0, min(1.0, fid))}


class QuantumInternetProtocols:
    def teleportation(self, fidelity: float) -> Dict[str, Any]:
        return {"protocol": "teleportation", "success_probability": max(0.0, min(1.0, fidelity))}

    def superdense_coding(self, channel_fidelity: float) -> Dict[str, Any]:
        bits_per_qubit = 2.0 * max(0.0, min(1.0, channel_fidelity))
        return {"protocol": "superdense", "bits_per_qubit": bits_per_qubit}

    def entanglement_swapping(self, fidelities: Sequence[float]) -> Dict[str, Any]:
        out = 1.0
        for f in fidelities:
            out *= float(f)
        return {"protocol": "swapping", "end_to_end_fidelity": out}

    def repeater_chain(self, hops: int, base_fidelity: float) -> Dict[str, Any]:
        return {"hops": hops, "fidelity": base_fidelity ** max(hops, 1)}

    def route(self, graph: Dict[str, List[str]], src: str, dst: str) -> List[str]:
        queue = [(src, [src])]
        seen = {src}
        while queue:
            node, path = queue.pop(0)
            if node == dst:
                return path
            for nxt in graph.get(node, []):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, path + [nxt]))
        return []


class DistributedCircuitExecutor:
    def partition(self, circuit: Circuit, segments: int) -> List[Circuit]:
        seg = max(1, segments)
        chunk = max(1, int(math.ceil(len(circuit.gates) / float(seg))))
        parts = []
        for i in range(0, len(circuit.gates), chunk):
            c = Circuit(circuit.num_qubits, name=f"{circuit.name}_part_{len(parts)}")
            c.gates = circuit.gates[i : i + chunk]
            parts.append(c)
        return parts

    def estimate_communication_overhead(self, parts: Sequence[Circuit]) -> Dict[str, Any]:
        links = max(0, len(parts) - 1)
        overhead = links * 0.002
        return {"links": links, "seconds": overhead}

    def best_cut(self, circuit: Circuit, candidate_segments: Sequence[int]) -> Dict[str, Any]:
        scores = []
        for s in candidate_segments:
            parts = self.partition(circuit, s)
            cost = self.estimate_communication_overhead(parts)["seconds"] + len(parts) * 0.001
            scores.append({"segments": s, "cost": cost})
        return min(scores, key=lambda x: x["cost"]) if scores else {"segments": 1, "cost": 0.0}


class EntanglementResourceManager:
    def __init__(self) -> None:
        self.pairs: Dict[Tuple[str, str], float] = {}

    def register_pair(self, a: str, b: str, fidelity: float) -> None:
        self.pairs[(a, b)] = fidelity

    def purify(self, a: str, b: str, protocol: str = "BBPSSW") -> Dict[str, Any]:
        f = self.pairs.get((a, b), 0.0)
        gain = 0.05 if protocol == "BBPSSW" else 0.04
        new_f = min(0.999, f + gain * (1.0 - f))
        self.pairs[(a, b)] = new_f
        return {"pair": (a, b), "protocol": protocol, "fidelity": new_f}

    def monitor(self) -> Dict[str, Any]:
        if not self.pairs:
            return {"count": 0, "average_fidelity": 0.0}
        vals = list(self.pairs.values())
        return {"count": len(vals), "average_fidelity": sum(vals) / len(vals)}


class QuantumClassicalNetworkIntegration:
    def qkd_secure_channel(self, classical_latency_ms: float, key_refresh_s: float) -> Dict[str, Any]:
        return {
            "classical_latency_ms": classical_latency_ms,
            "key_refresh_s": key_refresh_s,
            "secure": key_refresh_s <= 60.0,
        }

    def load_balance(self, workloads: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        out = defaultdict(list)
        for w in workloads:
            target = "quantum" if w.get("quantum_benefit", 0.0) > 1.0 else "classical"
            out[target].append(dict(w))
        return dict(out)

    def monitor(self, samples: Sequence[Dict[str, float]]) -> Dict[str, float]:
        if not samples:
            return {"avg_latency_ms": 0.0, "avg_success": 0.0}
        return {
            "avg_latency_ms": sum(s.get("latency_ms", 0.0) for s in samples) / len(samples),
            "avg_success": sum(s.get("success", 0.0) for s in samples) / len(samples),
        }


__all__ = [
    "QuantumNetworkSimulator",
    "QuantumInternetProtocols",
    "DistributedCircuitExecutor",
    "EntanglementResourceManager",
    "QuantumClassicalNetworkIntegration",
]
