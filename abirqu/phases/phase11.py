import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from ..circuit import Circuit


class QRAMSimulator:
    def __init__(self, address_qubits: int) -> None:
        self.address_qubits = address_qubits
        self.capacity = 2 ** address_qubits
        self._mem: Dict[int, Any] = {}

    def write(self, address: int, value: Any) -> None:
        if address < 0 or address >= self.capacity:
            raise ValueError("address out of range")
        self._mem[address] = value

    def read(self, address: int) -> Any:
        return self._mem.get(address)

    def superposed_read(self, amplitudes: Sequence[Tuple[int, complex]]) -> List[Dict[str, Any]]:
        out = []
        for addr, amp in amplitudes:
            if addr in self._mem:
                out.append({"address": addr, "value": self._mem[addr], "probability": float(abs(amp) ** 2)})
        return out

    def estimate_resources(self, query_count: int) -> Dict[str, Any]:
        return {
            "router_depth": int(np.ceil(np.log2(max(2, self.capacity)))),
            "query_count": query_count,
            "estimated_two_qubit_gates": query_count * self.address_qubits * 4,
        }


@dataclass
class CompressedState:
    coeffs: np.ndarray
    basis_idx: np.ndarray
    original_dim: int


class QuantumStateCompression:
    def compress(self, state: np.ndarray, keep_ratio: float = 0.2) -> CompressedState:
        state = np.asarray(state, dtype=complex)
        k = max(1, int(len(state) * keep_ratio))
        idx = np.argsort(np.abs(state))[-k:]
        return CompressedState(coeffs=state[idx], basis_idx=idx, original_dim=len(state))

    def decompress(self, compressed: CompressedState) -> np.ndarray:
        out = np.zeros(compressed.original_dim, dtype=complex)
        out[compressed.basis_idx] = compressed.coeffs
        n = np.linalg.norm(out)
        return out / n if n > 0 else out

    def fidelity(self, original: np.ndarray, reconstructed: np.ndarray) -> float:
        o = np.asarray(original, dtype=complex)
        r = np.asarray(reconstructed, dtype=complex)
        if np.linalg.norm(o) == 0 or np.linalg.norm(r) == 0:
            return 0.0
        o = o / np.linalg.norm(o)
        r = r / np.linalg.norm(r)
        return float(abs(np.vdot(o, r)) ** 2)


class QuantumCacheManager:
    def __init__(self, cache_path: Optional[str] = None) -> None:
        self._cache: Dict[str, Any] = {}
        self.hits = 0
        self.misses = 0
        self.cache_path = Path(cache_path) if cache_path else None
        if self.cache_path and self.cache_path.exists():
            self._cache = json.loads(self.cache_path.read_text())

    def key_for_circuit(self, circuit: Circuit) -> str:
        digest = hashlib.sha256(circuit.to_json().encode("utf-8")).hexdigest()
        return digest

    def get(self, key: str) -> Any:
        if key in self._cache:
            self.hits += 1
            return self._cache[key]
        self.misses += 1
        return None

    def put(self, key: str, value: Any) -> None:
        self._cache[key] = value
        if self.cache_path:
            self.cache_path.write_text(json.dumps(self._cache, indent=2))

    def invalidate(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        return {
            "entries": len(self._cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": (self.hits / total) if total else 0.0,
        }


class QuantumGarbageCollector:
    def find_unused_qubits(self, circuit: Circuit) -> List[int]:
        used = set()
        for g in circuit.gates:
            used.update(g.qubits)
        return [q for q in range(circuit.num_qubits) if q not in used]

    def uncompute_auxiliary(self, circuit: Circuit, aux_qubits: Iterable[int]) -> Circuit:
        aux = set(aux_qubits)
        out = Circuit(circuit.num_qubits, name=circuit.name + "_uncomputed")
        out.gates = [g for g in circuit.gates if not any(q in aux for q in g.qubits)]
        return out

    def qubit_reuse_schedule(self, circuit: Circuit) -> Dict[int, List[Tuple[int, int]]]:
        windows: Dict[int, List[int]] = {q: [] for q in range(circuit.num_qubits)}
        for i, g in enumerate(circuit.gates):
            for q in g.qubits:
                windows[q].append(i)
        schedule: Dict[int, List[Tuple[int, int]]] = {}
        for q, idx in windows.items():
            if idx:
                schedule[q] = [(idx[0], idx[-1])]
            else:
                schedule[q] = []
        return schedule


class MemoryAwareCompiler:
    def profile(self, circuit: Circuit) -> Dict[str, Any]:
        active = [0 for _ in range(circuit.num_qubits)]
        peak = 0
        for g in circuit.gates:
            for q in g.qubits:
                active[q] = 1
            peak = max(peak, sum(active))
        return {"peak_qubits": peak, "gates": len(circuit.gates)}

    def circuit_cut(self, circuit: Circuit, max_qubits_per_chunk: int) -> List[Circuit]:
        chunks: List[Circuit] = []
        cur = Circuit(circuit.num_qubits, name=circuit.name + "_chunk0")
        idx = 0
        for g in circuit.gates:
            if len(set(g.qubits)) > max_qubits_per_chunk and cur.gates:
                chunks.append(cur)
                idx += 1
                cur = Circuit(circuit.num_qubits, name=f"{circuit.name}_chunk{idx}")
            cur.gates.append(g)
        if cur.gates:
            chunks.append(cur)
        return chunks

    def optimize_space_time(self, circuit: Circuit, prefer: str = "space") -> Dict[str, Any]:
        if prefer == "space":
            return {"strategy": "cut-and-stitch", "estimated_peak_qubits": max(1, circuit.num_qubits // 2), "time_multiplier": 1.8}
        return {"strategy": "parallel-heavy", "estimated_peak_qubits": circuit.num_qubits, "time_multiplier": 1.0}
