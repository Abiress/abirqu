import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


class HybridRuntimeEngine:
    def __init__(self) -> None:
        self.shared_memory: Dict[str, Any] = {}

    def partition_workload(self, tasks: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        quantum = [t for t in tasks if t.get("type") == "quantum"]
        classical = [t for t in tasks if t.get("type") != "quantum"]
        return {"quantum": quantum, "classical": classical}

    def run_hybrid(self, tasks: Sequence[Dict[str, Any]], workers: int = 4) -> Dict[str, Any]:
        buckets = self.partition_workload(tasks)

        def _execute(task: Dict[str, Any]) -> Dict[str, Any]:
            fn = task.get("fn")
            args = task.get("args", ())
            kwargs = task.get("kwargs", {})
            if callable(fn):
                result = fn(*args, **kwargs)
            else:
                result = task.get("payload")
            return {"id": task.get("id"), "result": result, "type": task.get("type", "classical")}

        all_tasks = buckets["quantum"] + buckets["classical"]
        with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
            results = list(ex.map(_execute, all_tasks))

        self.shared_memory["last_results"] = results
        return {"results": results, "counts": {"quantum": len(buckets["quantum"]), "classical": len(buckets["classical"])}}


class VariationalAlgorithmAccelerator:
    def __init__(self) -> None:
        self._last_solution: Optional[np.ndarray] = None

    def evaluate_batch(self, objective: Callable[[np.ndarray], float], params_batch: np.ndarray) -> np.ndarray:
        return np.array([objective(p) for p in params_batch], dtype=float)

    def gradient(self, objective: Callable[[np.ndarray], float], params: np.ndarray, method: str = "finite_diff", eps: float = 1e-6) -> np.ndarray:
        grad = np.zeros_like(params, dtype=float)
        for i in range(len(params)):
            shift = np.zeros_like(params)
            shift[i] = eps
            grad[i] = (objective(params + shift) - objective(params - shift)) / (2.0 * eps)
        return grad

    def optimize(
        self,
        objective: Callable[[np.ndarray], float],
        init_params: np.ndarray,
        optimizer: str = "adam",
        steps: int = 200,
        lr: float = 0.05,
        warm_start: bool = True,
    ) -> Dict[str, Any]:
        x = self._last_solution.copy() if (warm_start and self._last_solution is not None) else init_params.astype(float).copy()
        m = np.zeros_like(x)
        v = np.zeros_like(x)
        beta1, beta2 = 0.9, 0.999
        history: List[float] = []

        for t in range(1, steps + 1):
            g = self.gradient(objective, x)
            if optimizer.lower() == "adam":
                m = beta1 * m + (1 - beta1) * g
                v = beta2 * v + (1 - beta2) * (g * g)
                mhat = m / (1 - beta1 ** t)
                vhat = v / (1 - beta2 ** t)
                x = x - lr * mhat / (np.sqrt(vhat) + 1e-8)
            elif optimizer.lower() == "spsa":
                delta = np.random.choice([-1.0, 1.0], size=len(x))
                c = 0.1 / np.sqrt(t)
                y_plus = objective(x + c * delta)
                y_minus = objective(x - c * delta)
                ghat = (y_plus - y_minus) / (2.0 * c) * delta
                x = x - lr * ghat
            else:
                x = x - lr * g
            history.append(float(objective(x)))

        self._last_solution = x.copy()
        return {"best_params": x, "best_value": float(history[-1]), "history": history, "optimizer": optimizer}


class ClassicalPrePostPipeline:
    def encode(self, data: np.ndarray, mode: str = "angle") -> np.ndarray:
        data = np.asarray(data, dtype=float)
        if mode == "amplitude":
            n = np.linalg.norm(data)
            return data / n if n > 0 else data
        if mode == "basis":
            return (data > 0.5).astype(float)
        if mode == "kernel":
            return np.exp(-np.square(data))
        return np.pi * data

    def decode(self, measured_probs: Dict[str, float], mode: str = "expectation") -> Dict[str, float]:
        total = sum(measured_probs.values())
        if total <= 0:
            return {"mean": 0.0, "variance": 0.0}
        values = np.array([int(k, 2) for k in measured_probs.keys()], dtype=float)
        probs = np.array([v / total for v in measured_probs.values()], dtype=float)
        mean = float(np.dot(values, probs))
        var = float(np.dot(np.square(values - mean), probs))
        return {"mean": mean, "variance": var, "mode": mode}


class IterativeHybridLoop:
    def __init__(self) -> None:
        self._checkpoints: Dict[str, Dict[str, Any]] = {}

    def run(
        self,
        init_params: np.ndarray,
        objective: Callable[[np.ndarray], float],
        update: Callable[[np.ndarray, np.ndarray], np.ndarray],
        max_iters: int = 100,
        tol: float = 1e-6,
        budget_quantum_calls: int = 1000,
        checkpoint_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        x = init_params.astype(float).copy()
        prev = objective(x)
        calls = 1
        history = [float(prev)]

        for i in range(1, max_iters + 1):
            if calls >= budget_quantum_calls:
                break
            grad = np.zeros_like(x)
            eps = 1e-5
            for j in range(len(x)):
                shift = np.zeros_like(x)
                shift[j] = eps
                grad[j] = (objective(x + shift) - objective(x - shift)) / (2.0 * eps)
                calls += 2
                if calls >= budget_quantum_calls:
                    break
            x = update(x, grad)
            cur = objective(x)
            calls += 1
            history.append(float(cur))
            if abs(cur - prev) < tol:
                break
            prev = cur

        result = {"params": x, "objective": float(history[-1]), "history": history, "quantum_calls": calls}
        if checkpoint_id:
            self._checkpoints[checkpoint_id] = result
        return result

    def resume(self, checkpoint_id: str) -> Dict[str, Any]:
        if checkpoint_id not in self._checkpoints:
            raise KeyError("checkpoint not found")
        return self._checkpoints[checkpoint_id]


class HybridAlgorithmOrchestrator:
    def execute_workflow(self, steps: Sequence[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = dict(context or {})
        outputs: List[Dict[str, Any]] = []

        for step in steps:
            if "when" in step and not bool(step["when"](ctx)):
                continue

            if step.get("parallel"):
                funcs = step.get("funcs", [])
                with ThreadPoolExecutor(max_workers=max(1, len(funcs))) as ex:
                    vals = list(ex.map(lambda f: f(ctx), funcs))
                out = {"name": step.get("name"), "result": vals}
            else:
                fn = step.get("fn")
                out_val = fn(ctx) if callable(fn) else step.get("value")
                out = {"name": step.get("name"), "result": out_val}

            outputs.append(out)
            if step.get("store_as"):
                ctx[step["store_as"]] = out["result"]

        # Cost-time-quality heuristic: maximize quality / (cost * time)
        candidates = ctx.get("candidates", [])
        best = None
        best_score = -1.0
        for c in candidates:
            cost = max(float(c.get("cost", 1.0)), 1e-9)
            time_s = max(float(c.get("time", 1.0)), 1e-9)
            quality = float(c.get("quality", 0.0))
            score = quality / (cost * time_s)
            if score > best_score:
                best_score = score
                best = c

        return {"outputs": outputs, "context": ctx, "best_candidate": best, "best_score": best_score}
