import random
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np

from ..circuit import Circuit
from ..noise import NoiseModel
from ..numpy_sim import NumPySimulator


class CircuitEquivalenceChecker:
    def exact(self, a: Circuit, b: Circuit, atol: float = 1e-10) -> bool:
        if a.num_qubits != b.num_qubits:
            return False
        sa = NumPySimulator(a.num_qubits)
        sb = NumPySimulator(b.num_qubits)
        sa.run_circuit(a)
        sb.run_circuit(b)
        return bool(np.allclose(sa.get_state_vector(), sb.get_state_vector(), atol=atol))

    def approximate(self, a: Circuit, b: Circuit, tolerance: float = 1e-6) -> Dict[str, Any]:
        sa = NumPySimulator(a.num_qubits)
        sb = NumPySimulator(b.num_qubits)
        sa.run_circuit(a)
        sb.run_circuit(b)
        diff = float(np.max(np.abs(sa.get_state_vector() - sb.get_state_vector())))
        return {"equivalent": diff <= tolerance, "max_diff": diff}

    def under_noise(self, a: Circuit, b: Circuit, noise: NoiseModel) -> Dict[str, Any]:
        pa = NumPySimulator(a.num_qubits).run_circuit(a)
        pb = NumPySimulator(b.num_qubits).run_circuit(b)
        na = noise.apply_to_probs(pa)
        nb = noise.apply_to_probs(pb)
        keys = set(na) | set(nb)
        tvd = 0.5 * sum(abs(na.get(k, 0.0) - nb.get(k, 0.0)) for k in keys)
        return {"tvd": tvd, "similar": tvd < 0.1}


class QuantumPropertyBasedTester:
    def generate_random_circuit(self, num_qubits: int, depth: int, seed: int = 0) -> Circuit:
        rng = random.Random(seed)
        c = Circuit(num_qubits)
        ops = ["h", "x", "z", "cnot"]
        for _ in range(depth):
            op = rng.choice(ops)
            if op == "cnot" and num_qubits > 1:
                q1 = rng.randrange(num_qubits)
                q2 = (q1 + 1) % num_qubits
                c.cnot(q1, q2)
            else:
                q = rng.randrange(num_qubits)
                getattr(c, op)(q)
        return c

    def invariant_probability_sum(self, circuit: Circuit) -> bool:
        probs = NumPySimulator(circuit.num_qubits).run_circuit(circuit)
        return abs(sum(probs.values()) - 1.0) < 1e-9

    def run_trials(self, trials: int, num_qubits: int, depth: int) -> Dict[str, Any]:
        passed = 0
        for i in range(trials):
            c = self.generate_random_circuit(num_qubits, depth, seed=i)
            if self.invariant_probability_sum(c):
                passed += 1
        return {"trials": trials, "passed": passed, "coverage": passed / float(max(1, trials))}


class QuantumFormalVerifier:
    def verify_hoare(self, pre: bool, post: bool) -> bool:
        return bool((not pre) or post)

    def weakest_precondition(self, post_condition: bool, guard: bool) -> bool:
        return bool(post_condition and guard)

    def generate_proof_certificate(self, theorem: str, valid: bool) -> Dict[str, Any]:
        return {"theorem": theorem, "valid": valid, "certificate": f"CERT-{abs(hash((theorem, valid))) % 1000000}"}


class NoiseRobustnessTester:
    def monte_carlo(self, circuit: Circuit, noise_strengths: Sequence[float], shots: int = 100) -> Dict[str, Any]:
        results = []
        for p in noise_strengths:
            noise = NoiseModel(circuit.num_qubits)
            noise.add_depolarizing_error(list(range(circuit.num_qubits)), p)
            base = NumPySimulator(circuit.num_qubits).run_circuit(circuit)
            noisy = noise.apply_to_probs(base)
            target = max(base, key=base.get)
            success = noisy.get(target, 0.0)
            results.append({"p": p, "success": success})
        return {"results": results, "threshold": min((r["p"] for r in results if r["success"] > 0.5), default=None)}

    def sensitivity(self, circuit: Circuit) -> Dict[str, Any]:
        counts: Dict[str, int] = {}
        for g in circuit.gates:
            counts[g.name] = counts.get(g.name, 0) + 1
        ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return {"most_sensitive_candidates": ranked[:3]}


class QuantumRegressionSuite:
    def __init__(self) -> None:
        self.snapshots: Dict[str, Dict[str, float]] = {}

    def snapshot(self, name: str, circuit: Circuit) -> Dict[str, float]:
        probs = NumPySimulator(circuit.num_qubits).run_circuit(circuit)
        self.snapshots[name] = probs
        return probs

    def compare(self, name: str, circuit: Circuit, tolerance: float = 1e-9) -> Dict[str, Any]:
        if name not in self.snapshots:
            raise KeyError("snapshot missing")
        cur = NumPySimulator(circuit.num_qubits).run_circuit(circuit)
        base = self.snapshots[name]
        keys = set(base) | set(cur)
        max_diff = max(abs(base.get(k, 0.0) - cur.get(k, 0.0)) for k in keys)
        return {"regression": max_diff > tolerance, "max_diff": max_diff}

    def trend(self) -> Dict[str, Any]:
        return {"snapshot_count": len(self.snapshots), "names": sorted(self.snapshots.keys())}
