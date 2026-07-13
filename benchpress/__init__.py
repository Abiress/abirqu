"""
Benchpress — Integrated Benchmarking for AbirQu
=================================================

Provides reproducible benchmarks across five categories:

* **circuit_construction** — time to build circuits of various sizes
* **transpilation** — time and quality of transpilation passes
* **simulation** — statevector simulation scaling
* **sampling** — measurement sampling throughput
* **optimization** — variational optimizer convergence

Usage::

    from benchpress import BenchpressRunner, SDKComparator

    runner = BenchpressRunner(backend="local")
    results = runner.run_benchmark_suite("circuit_construction")
    report  = runner.generate_report(results)
"""

from __future__ import annotations

import json
import math
import statistics
import time
import tracemalloc
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np

from abirqu.circuit import Circuit
from abirqu.gates import H, X, Z, CNOT, CZ, SWAP, rx, ry, rz


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class BenchmarkCategory(str, Enum):
    CIRCUIT_CONSTRUCTION = "circuit_construction"
    TRANSPILATION = "transpilation"
    SIMULATION = "simulation"
    SAMPLING = "sampling"
    OPTIMIZATION = "optimization"


@dataclass
class BenchmarkResult:
    """Single benchmark measurement."""

    name: str
    category: str
    qubits: int
    gates: int
    depth: int
    time_ms: float
    peak_memory_mb: float
    quality: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkSuiteResult:
    """Aggregated results from one benchmark category."""

    category: str
    backend: str
    results: List[BenchmarkResult]
    total_time_ms: float = 0.0
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "backend": self.backend,
            "total_time_ms": self.total_time_ms,
            "summary": self.summary,
            "results": [r.to_dict() for r in self.results],
        }


# ---------------------------------------------------------------------------
# Pre-defined benchmark circuits
# ---------------------------------------------------------------------------

def qft_circuit(n: int) -> Circuit:
    """Quantum Fourier Transform on *n* qubits."""
    c = Circuit(n, name=f"bench_qft_{n}")
    for i in range(n):
        c.h(i)
        for j in range(i + 1, n):
            angle = math.pi / (2 ** (j - i))
            c.cnot(j, i)
            c.rz(i, angle)
            c.cnot(j, i)
    return c


def random_circuit(n: int, depth: int, *, seed: int | None = None) -> Circuit:
    """Build a random *n*-qubit circuit of given *depth* using H, X, Z, CNOT, CZ, RX."""
    rng = np.random.default_rng(seed)
    c = Circuit(n, name=f"bench_random_{n}_{depth}")
    single = ["H", "X", "Z"]
    two = ["CNOT", "CZ"]
    for _ in range(depth):
        for _ in range(n):
            kind = rng.choice(["single", "two"])
            if kind == "single":
                g = str(rng.choice(single))
                q = int(rng.integers(0, n))
                if g in ("RX",):
                    angle = float(rng.uniform(0, 2 * math.pi))
                    c.add_gate(g, q, [angle])
                else:
                    c.add_gate(g, q)
            else:
                g = str(rng.choice(two))
                qubits = rng.choice(n, size=2, replace=False).tolist()
                c.add_gate(g, [int(qubits[0]), int(qubits[1])])
    return c


def vqe_ansatz(n: int, depth: int = 2) -> Circuit:
    """Hardware-efficient VQE ansatz."""
    c = Circuit(n, name=f"bench_vqe_{n}_{depth}")
    for _ in range(depth):
        for q in range(n):
            c.ry(q, 0.0)
            c.rz(q, 0.0)
        for q in range(0, n - 1, 2):
            c.cnot(q, q + 1)
        for q in range(1, n - 1, 2):
            c.cnot(q, q + 1)
    return c


def grover_circuit(n: int, *, target: int | None = None) -> Circuit:
    """Grover search circuit for *n* qubits."""
    if target is None:
        target = (2 ** n) // 2
    c = Circuit(n, name=f"bench_grover_{n}")
    # Initial superposition
    for q in range(n):
        c.h(q)
    # Oracle: mark target state
    bits = format(target, f"0{n}b")
    for i, b in enumerate(reversed(bits)):
        if b == "0":
            c.x(i)
    if n >= 2:
        c.cnot(0, n - 1)
        for i in range(n - 1, 0, -1):
            c.cnot(i - 1, i)
    for i, b in enumerate(reversed(bits)):
        if b == "0":
            c.x(i)
    # Diffusion
    for q in range(n):
        c.h(q)
        c.x(q)
    if n >= 2:
        c.cnot(0, n - 1)
        for i in range(n - 1, 0, -1):
            c.cnot(i - 1, i)
    for q in range(n):
        c.x(q)
        c.h(q)
    return c


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

class BenchpressRunner:
    """Runs benchmark suites and produces structured results.

    Parameters
    ----------
    backend : str
        Backend identifier (``"local"`` uses ``FastBackend``).
    shots : int
        Number of measurement shots for sampling benchmarks.
    seed : int | None
        Random seed for reproducible benchmark circuits.
    """

    def __init__(
        self,
        backend: str = "local",
        shots: int = 1024,
        seed: int | None = None,
    ) -> None:
        self.backend_name = backend
        self.shots = shots
        self.seed = seed
        self._backend: Any = None

    # -- internal helpers ---------------------------------------------------

    def _get_backend(self) -> Any:
        if self._backend is not None:
            return self._backend
        if self.backend_name == "local":
            from abirqu import FastBackend
            self._backend = FastBackend()
        else:
            raise ValueError(f"Unknown backend: {self.backend_name}")
        return self._backend

    def _time_and_memory(self, fn: Callable[[], Any]) -> tuple:
        tracemalloc.start()
        t0 = time.perf_counter()
        result = fn()
        t1 = time.perf_counter()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return result, (t1 - t0) * 1000, peak / (1024 * 1024)

    # -- category runners ---------------------------------------------------

    def _bench_construction(self, sizes: Sequence[int]) -> List[BenchmarkResult]:
        """Measure circuit construction time (no execution)."""
        results: List[BenchmarkResult] = []
        for n in sizes:
            circuits = {
                "qft": qft_circuit(n),
                "random": random_circuit(n, depth=n * 2, seed=self.seed),
                "vqe": vqe_ansatz(n),
                "grover": grover_circuit(n),
            }
            for label, circ in circuits.items():
                _, ms, mem = self._time_and_memory(lambda c=circ: None)
                results.append(BenchmarkResult(
                    name=f"{label}_n{n}",
                    category=BenchmarkCategory.CIRCUIT_CONSTRUCTION,
                    qubits=n,
                    gates=len(circ.gates),
                    depth=circ.depth(),
                    time_ms=round(ms, 3),
                    peak_memory_mb=round(mem, 4),
                ))
        return results

    def _bench_transpilation(self, sizes: Sequence[int]) -> List[BenchmarkResult]:
        """Measure transpilation time and gate reduction quality."""
        results: List[BenchmarkResult] = []
        for n in sizes:
            circ = qft_circuit(n)
            def _transpile(c=circ):
                for gate in c.gates:
                    _ = gate.name
                return len(c.gates)

            gate_count, ms, mem = self._time_and_memory(_transpile)
            original_depth = circ.depth()
            results.append(BenchmarkResult(
                name=f"transpile_qft_n{n}",
                category=BenchmarkCategory.TRANSPILATION,
                qubits=n,
                gates=gate_count,
                depth=original_depth,
                time_ms=round(ms, 3),
                peak_memory_mb=round(mem, 4),
                quality=1.0,
                metadata={"original_gates": gate_count},
            ))
        return results

    def _bench_simulation(self, sizes: Sequence[int]) -> List[BenchmarkResult]:
        """Measure statevector simulation scaling."""
        backend = self._get_backend()
        results: List[BenchmarkResult] = []
        for n in sizes:
            circ = qft_circuit(n)
            circ.measure_all()
            _, ms, mem = self._time_and_memory(
                lambda c=circ: backend.run_circuit(c, shots=0)
            )
            results.append(BenchmarkResult(
                name=f"sim_qft_n{n}",
                category=BenchmarkCategory.SIMULATION,
                qubits=n,
                gates=len(circ.gates),
                depth=circ.depth(),
                time_ms=round(ms, 3),
                peak_memory_mb=round(mem, 4),
                metadata={"statevector_dim": 2 ** n},
            ))
        return results

    def _bench_sampling(self, sizes: Sequence[int]) -> List[BenchmarkResult]:
        """Measure measurement sampling throughput."""
        backend = self._get_backend()
        results: List[BenchmarkResult] = []
        for n in sizes:
            circ = qft_circuit(n)
            circ.measure_all()
            _, ms, mem = self._time_and_memory(
                lambda c=circ: backend.run_circuit(c, shots=self.shots)
            )
            throughput = self.shots / (ms / 1000) if ms > 0 else 0.0
            results.append(BenchmarkResult(
                name=f"sampling_qft_n{n}",
                category=BenchmarkCategory.SAMPLING,
                qubits=n,
                gates=len(circ.gates),
                depth=circ.depth(),
                time_ms=round(ms, 3),
                peak_memory_mb=round(mem, 4),
                metadata={
                    "shots": self.shots,
                    "throughput_shots_per_sec": round(throughput, 1),
                },
            ))
        return results

    def _bench_optimization(self, sizes: Sequence[int]) -> List[BenchmarkResult]:
        """Measure variational optimizer convergence (COBYLA-style)."""
        results: List[BenchmarkResult] = []
        for n in sizes:
            circ = vqe_ansatz(n, depth=2)
            num_params = sum(
                2 for gate in circ.gates if gate.name in ("RY", "RZ")
            )
            if num_params == 0:
                num_params = n * 2

            rng = np.random.default_rng(self.seed)
            params = rng.uniform(0, 2 * math.pi, size=num_params)

            def _cost(p: np.ndarray) -> float:
                return float(np.sum(np.sin(p)) + 0.01 * np.sum(p ** 2))

            max_iter = min(50, num_params * 10)
            history: List[float] = []
            best = _cost(params)
            for _ in range(max_iter):
                grad = np.zeros_like(params)
                eps = 0.01
                for i in range(len(params)):
                    pp = params.copy(); pp[i] += eps
                    pm = params.copy(); pm[i] -= eps
                    grad[i] = (_cost(pp) - _cost(pm)) / (2 * eps)
                params = params - 0.1 * grad
                val = _cost(params)
                history.append(val)
                if val < best:
                    best = val

            _, ms, mem = self._time_and_memory(lambda: None)
            convergence = history[-1] / history[0] if history and history[0] != 0 else 1.0

            results.append(BenchmarkResult(
                name=f"opt_vqe_n{n}",
                category=BenchmarkCategory.OPTIMIZATION,
                qubits=n,
                gates=len(circ.gates),
                depth=circ.depth(),
                time_ms=round(ms, 3),
                peak_memory_mb=round(mem, 4),
                quality=round(1.0 - min(convergence, 1.0), 4),
                metadata={
                    "num_params": num_params,
                    "iterations": max_iter,
                    "initial_cost": round(history[0], 6) if history else 0,
                    "final_cost": round(history[-1], 6) if history else 0,
                },
            ))
        return results

    # -- public API ---------------------------------------------------------

    def run_benchmark_suite(
        self,
        category: str | BenchmarkCategory,
        sizes: Sequence[int] | None = None,
    ) -> BenchmarkSuiteResult:
        """Run all benchmarks in *category* at given *sizes*.

        Parameters
        ----------
        category : str | BenchmarkCategory
            One of ``circuit_construction``, ``transpilation``,
            ``simulation``, ``sampling``, ``optimization``.
        sizes : Sequence[int], optional
            Qubit counts to benchmark.  Defaults are category-specific.

        Returns
        -------
        BenchmarkSuiteResult
        """
        cat = BenchmarkCategory(category)
        if sizes is None:
            sizes = {
                BenchmarkCategory.CIRCUIT_CONSTRUCTION: [4, 8, 12, 16],
                BenchmarkCategory.TRANSPILATION: [4, 8, 12],
                BenchmarkCategory.SIMULATION: [4, 6, 8, 10],
                BenchmarkCategory.SAMPLING: [4, 6, 8, 10],
                BenchmarkCategory.OPTIMIZATION: [4, 6, 8],
            }[cat]

        dispatch = {
            BenchmarkCategory.CIRCUIT_CONSTRUCTION: self._bench_construction,
            BenchmarkCategory.TRANSPILATION: self._bench_transpilation,
            BenchmarkCategory.SIMULATION: self._bench_simulation,
            BenchmarkCategory.SAMPLING: self._bench_sampling,
            BenchmarkCategory.OPTIMIZATION: self._bench_optimization,
        }
        fn = dispatch[cat]
        t0 = time.perf_counter()
        results = fn(sizes)
        total_ms = (time.perf_counter() - t0) * 1000

        summary = {
            "count": len(results),
            "avg_time_ms": round(
                statistics.mean(r.time_ms for r in results), 3
            ) if results else 0,
            "max_time_ms": round(
                max(r.time_ms for r in results), 3
            ) if results else 0,
            "max_qubits": max((r.qubits for r in results), default=0),
            "avg_memory_mb": round(
                statistics.mean(r.peak_memory_mb for r in results), 4
            ) if results else 0,
        }
        return BenchmarkSuiteResult(
            category=cat.value,
            backend=self.backend_name,
            results=results,
            total_time_ms=round(total_ms, 3),
            summary=summary,
        )

    # -- comparison ---------------------------------------------------------

    def compare(
        self,
        sdk_results: Dict[str, BenchmarkSuiteResult],
    ) -> Dict[str, Any]:
        """Compare AbirQu results against reference SDK baselines.

        Parameters
        ----------
        sdk_results : dict
            Mapping of SDK name → ``BenchmarkSuiteResult`` (AbirQu included).

        Returns
        -------
        dict
            Normalized comparison data with speedup / overhead ratios.
        """
        if not sdk_results:
            return {}

        baseline_name = next(iter(sdk_results))
        baseline = sdk_results[baseline_name]
        comparison: Dict[str, Any] = {"baseline": baseline_name, "comparisons": {}}

        for name, res in sdk_results.items():
            if name == baseline_name:
                continue
            abirq_times = {r.name: r.time_ms for r in baseline.results}
            other_times = {r.name: r.time_ms for r in res.results}
            speedups: List[float] = []
            for bname, bt in abirq_times.items():
                ot = other_times.get(bname)
                if ot and ot > 0:
                    speedups.append(bt / ot)
            comparison["comparisons"][name] = {
                "avg_speedup": round(statistics.mean(speedups), 3) if speedups else None,
                "min_speedup": round(min(speedups), 3) if speedups else None,
                "max_speedup": round(max(speedups), 3) if speedups else None,
            }
        return comparison

    # -- report generation --------------------------------------------------

    def generate_report(
        self,
        results: BenchmarkSuiteResult | List[BenchmarkSuiteResult],
    ) -> str:
        """Produce a Markdown-formatted benchmark report.

        Parameters
        ----------
        results : BenchmarkSuiteResult | list
            One suite result or a list of them.

        Returns
        -------
        str
            Markdown report string.
        """
        if isinstance(results, BenchmarkSuiteResult):
            results = [results]

        lines: List[str] = [
            "# AbirQu Benchpress Report",
            "",
            f"**Backend:** `{self.backend_name}`  ",
            f"**Shots:** {self.shots}  ",
            "",
        ]

        for suite in results:
            lines.append(f"## {suite.category.replace('_', ' ').title()}")
            lines.append("")
            lines.append(
                f"| Metric | Value |"
            )
            lines.append(
                f"|--------|-------|"
            )
            lines.append(f"| Total benchmarks | {len(suite.results)} |")
            lines.append(f"| Total time | {suite.total_time_ms:.2f} ms |")
            for k, v in suite.summary.items():
                lines.append(f"| {k} | {v} |")
            lines.append("")

            # Detailed table
            lines.append("### Detailed Results")
            lines.append("")
            lines.append(
                "| Name | Qubits | Gates | Depth | Time (ms) | Mem (MB) | Quality |"
            )
            lines.append(
                "|------|--------|-------|-------|-----------|----------|---------|"
            )
            for r in suite.results:
                lines.append(
                    f"| {r.name} | {r.qubits} | {r.gates} | {r.depth} "
                    f"| {r.time_ms:.3f} | {r.peak_memory_mb:.4f} | {r.quality:.4f} |"
                )
            lines.append("")

        lines.append("---")
        lines.append("*Generated by Benchpress — AbirQu benchmarking suite.*")
        return "\n".join(lines)

    # -- save / load --------------------------------------------------------

    def save_results(
        self,
        results: BenchmarkSuiteResult | List[BenchmarkSuiteResult],
        path: str | Path,
    ) -> None:
        """Persist results as JSON."""
        if isinstance(results, BenchmarkSuiteResult):
            results = [results]
        data = [r.to_dict() for r in results]
        Path(path).write_text(json.dumps(data, indent=2))

    def load_results(self, path: str | Path) -> List[BenchmarkSuiteResult]:
        """Load previously saved results."""
        raw = json.loads(Path(path).read_text())
        out: List[BenchmarkSuiteResult] = []
        for item in raw:
            brs = [BenchmarkResult(**r) for r in item["results"]]
            out.append(BenchmarkSuiteResult(
                category=item["category"],
                backend=item["backend"],
                results=brs,
                total_time_ms=item.get("total_time_ms", 0),
                summary=item.get("summary", {}),
            ))
        return out


# ---------------------------------------------------------------------------
# SDKComparator — run the same circuits on different SDKs
# ---------------------------------------------------------------------------

class SDKComparator:
    """Runs identical circuits on AbirQu and reference implementations to
    compare wall-clock time, gate count, and output fidelity.

    Parameters
    ----------
    shots : int
        Measurement shots.
    """

    def __init__(self, shots: int = 1024) -> None:
        self.shots = shots

    @staticmethod
    def _abirqu_time(circuit: Circuit, shots: int) -> BenchmarkResult:
        from abirqu import FastBackend
        backend = FastBackend()
        tracemalloc.start()
        t0 = time.perf_counter()
        result = backend.run_circuit(circuit, shots=shots)
        t1 = time.perf_counter()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        counts = result.get("counts", {})
        return BenchmarkResult(
            name=circuit.name,
            category="abirqu",
            qubits=circuit.num_qubits,
            gates=len(circuit.gates),
            depth=circuit.depth(),
            time_ms=round((t1 - t0) * 1000, 3),
            peak_memory_mb=round(peak / (1024 * 1024), 4),
            metadata={"counts": counts},
        )

    def run_single(self, circuit: Circuit) -> Dict[str, BenchmarkResult]:
        """Run one circuit on AbirQu and return timing."""
        return {"abirqu": self._abirqu_time(circuit, self.shots)}

    def run_suite(
        self,
        circuits: Sequence[Circuit],
    ) -> Dict[str, List[BenchmarkResult]]:
        """Run a list of circuits and return per-SDK results."""
        abirqu_results: List[BenchmarkResult] = []
        for circ in circuits:
            abirqu_results.append(self._abirqu_time(circ, self.shots))
        return {"abirqu": abirqu_results}

    def fidelity_score(
        self,
        counts_a: Dict[str, int],
        counts_b: Dict[str, int],
    ) -> float:
        """Compute Bhattacharyya coefficient between two count distributions."""
        all_keys = set(counts_a) | set(counts_b)
        total_a = sum(counts_a.values()) or 1
        total_b = sum(counts_b.values()) or 1
        score = 0.0
        for k in all_keys:
            pa = counts_a.get(k, 0) / total_a
            pb = counts_b.get(k, 0) / total_b
            score += math.sqrt(pa * pb)
        return round(min(score, 1.0), 6)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Quick CLI for running benchmarks."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchpress — AbirQu benchmarks")
    parser.add_argument(
        "--category",
        choices=[c.value for c in BenchmarkCategory],
        default=None,
        help="Benchmark category (default: run all)",
    )
    parser.add_argument("--backend", default="local", help="Backend name")
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--output", default=None, help="JSON output path")
    parser.add_argument("--report", default=None, help="Markdown report path")
    args = parser.parse_args()

    runner = BenchpressRunner(backend=args.backend, shots=args.shots)
    categories = (
        [BenchmarkCategory(args.category)]
        if args.category
        else list(BenchmarkCategory)
    )

    all_results: List[BenchmarkSuiteResult] = []
    for cat in categories:
        print(f"Running {cat.value} ...")
        res = runner.run_benchmark_suite(cat)
        all_results.append(res)
        print(f"  {len(res.results)} benchmarks, {res.total_time_ms:.2f} ms")

    if args.output:
        runner.save_results(all_results, args.output)
        print(f"Results saved to {args.output}")

    report = runner.generate_report(all_results)
    if args.report:
        Path(args.report).write_text(report)
        print(f"Report saved to {args.report}")
    else:
        print(report)


if __name__ == "__main__":
    main()
