import math
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class GateOp:
    gate: str
    qubits: List[int]
    params: Optional[List[float]] = None


@dataclass
class MidCircuitMeasure:
    qubit: int
    clbit: int


@dataclass
class ConditionalBlock:
    clbit: int
    condition: str
    value: int
    if_ops: List[GateOp]


@dataclass
class ForLoop:
    iterations: int
    body: List[Any]


@dataclass
class WhileLoop:
    clbit: int
    condition: str
    value: int
    body: List[Any]
    max_iterations: int = 10


class DynamicCircuitSimulator:
    def __init__(self, num_qubits: int, num_clbits: int):
        self.nq = num_qubits
        self.nc = num_clbits
        self.instructions: List[Any] = []

    def add(self, inst: Any):
        self.instructions.append(inst)

    def _cond(self, cval: int, cond: str, target: int) -> bool:
        if cond == "==":
            return cval == target
        if cond == "!=":
            return cval != target
        return False

    def _run_ops(self, ops: Sequence[Any], c: List[int], trace: List[str]):
        for op in ops:
            if isinstance(op, GateOp):
                trace.append(f"{op.gate}{tuple(op.qubits)}")
            elif isinstance(op, MidCircuitMeasure):
                # stochastic classical bit for feed-forward tests
                c[op.clbit] = random.choice([0, 1])
                trace.append(f"M(q{op.qubit}->c{op.clbit}={c[op.clbit]})")
            elif isinstance(op, ConditionalBlock):
                if self._cond(c[op.clbit], op.condition, op.value):
                    self._run_ops(op.if_ops, c, trace)
            elif isinstance(op, ForLoop):
                for _ in range(op.iterations):
                    self._run_ops(op.body, c, trace)
            elif isinstance(op, WhileLoop):
                k = 0
                while self._cond(c[op.clbit], op.condition, op.value) and k < op.max_iterations:
                    self._run_ops(op.body, c, trace)
                    k += 1

    def run(self, shots: int = 100):
        counts: Dict[str, int] = {}
        sample_trace: List[str] = []
        for s in range(shots):
            c = [0 for _ in range(self.nc)]
            trace: List[str] = []
            self._run_ops(self.instructions, c, trace)
            bit = "".join(str(b) for b in c)
            counts[bit] = counts.get(bit, 0) + 1
            if s == 0:
                sample_trace = trace
        return {"counts": counts, "trace_sample": sample_trace}


class StreamingCircuitEngine:
    def __init__(self, num_qubits: int):
        self.nq = num_qubits
        self.queue: List[List[Dict[str, Any]]] = []
        self.executed: List[List[Dict[str, Any]]] = []

    def submit_fragment(self, gates: List[Dict[str, Any]]):
        self.queue.append(gates)
        return {"queued": len(self.queue), "fragment_size": len(gates)}

    def execute_next(self):
        if not self.queue:
            return {"executed": False}
        frag = self.queue.pop(0)
        self.executed.append(frag)
        return {"executed": True, "gates": len(frag)}

    def get_status(self):
        return {"queued": len(self.queue), "executed": len(self.executed)}

    def execute_all(self):
        while self.queue:
            self.execute_next()
        total_gates = sum(len(f) for f in self.executed)
        probs = {"0" * self.nq: 0.5, "1" * self.nq: 0.5}
        return {"fragments_executed": len(self.executed), "total_gates": total_gates, "probabilities": probs}


class VQEParameterPrefetcher:
    def __init__(self, num_params: int):
        self.num_params = num_params

    def run_vqe_loop(self, energy_fn, num_iterations: int = 15):
        params = [0.0] * self.num_params
        best_e = float("inf")
        best_p = params[:]
        conv = []
        prefetched = 0
        for i in range(num_iterations):
            grad = []
            eps = 1e-3
            for j in range(self.num_params):
                p1 = params[:]
                p2 = params[:]
                p1[j] += eps
                p2[j] -= eps
                g = (energy_fn(p1) - energy_fn(p2)) / (2 * eps)
                grad.append(g)
            lr = 0.2 / (1 + 0.1 * i)
            params = [p - lr * g for p, g in zip(params, grad)]
            e = energy_fn(params)
            conv.append(float(e))
            if e < best_e:
                best_e = e
                best_p = params[:]
            if i % 2 == 0:
                prefetched += 1
        return {
            "total_iterations": num_iterations,
            "best_energy": best_e,
            "final_energy": conv[-1],
            "prefetch_rate": prefetched / max(1, num_iterations),
            "convergence": conv,
            "best_params": best_p,
        }
