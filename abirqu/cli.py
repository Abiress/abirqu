"""Command-line helpers for quick circuit build/execute workflows."""

from __future__ import annotations

import argparse
import json
from typing import Optional, Sequence

from .algorithms import (
    bernstein_vazirani,
    grover_search,
    hamiltonian_simulation,
    qaoa_maxcut,
    qft_circuit,
    quantum_walk,
    shor_factorization,
    vqe_hardware_efficient,
)
from .benchmark_spec import run_and_write_benchmark
from .circuit import Circuit
from .optimize.transpiler import HardwareAwareTranspiler
from .sdk import AbirQuSDK
from .tracker import QuantumAdvantageTracker


def build_bell() -> Circuit:
    c = Circuit(2, name="bell")
    c.h(0).cnot(0, 1)
    return c


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="abirqu", description="AbirQu CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run-bell", help="Execute a Bell-state demo")
    run.add_argument("--shots", type=int, default=256)

    draw = sub.add_parser("draw-bell", help="Print Bell circuit")
    draw.add_argument("--ascii", action="store_true", dest="ascii_output")

    template = sub.add_parser("run-template", help="Run an algorithm template")
    template.add_argument(
        "--name",
        choices=["grover", "shor", "qft", "bernstein-vazirani", "qaoa", "vqe", "hamiltonian-sim", "quantum-walk"],
        required=True,
    )
    template.add_argument("--shots", type=int, default=256)
    template.add_argument("--num-qubits", type=int, default=4)
    template.add_argument("--target-state", type=int, default=1)
    template.add_argument("--num-to-factor", type=int, default=15)
    template.add_argument("--hidden-string", default="1011")
    template.add_argument("--beta", type=float, default=0.4)
    template.add_argument("--gamma", type=float, default=0.7)
    template.add_argument("--depth", type=int, default=2)
    template.add_argument("--time", type=float, default=0.2)
    template.add_argument("--steps", type=int, default=6)

    transpile = sub.add_parser("transpile-bell", help="Transpile Bell circuit for a backend")
    transpile.add_argument("--backend", default="generic")
    transpile.add_argument("--coupling", default="", help="Comma-separated edges, e.g. 0-1,1-2")

    track = sub.add_parser("track-demo", help="Record two sample benchmarks and print summary")

    compatibility = sub.add_parser("compatibility-report", help="Print full SDK compatibility report")
    compatibility.add_argument("--summary-only", action="store_true", help="Print only aggregate summary and runtime checks")

    capabilities = sub.add_parser("capability-matrix", help="Print one-shot SDK capability matrix")
    capabilities.add_argument("--summary-only", action="store_true", help="Print only readiness, runtime checks, and summary")

    benchmark = sub.add_parser("benchmark-spec", help="Run Quantum SDK Benchmark Specification v1.0")
    benchmark.add_argument("--profile", choices=["quick", "full"], default="full")
    benchmark.add_argument("--output", default="benchmark_results/spec_benchmark_results.json")
    benchmark.add_argument("--stdout", action="store_true", help="Also print full benchmark JSON to stdout")

    args = parser.parse_args(argv)

    if args.command == "run-bell":
        result = build_bell().run(shots=args.shots)
        print(json.dumps({"counts": result["counts"], "shots": args.shots}, indent=2))
        return 0

    if args.command == "draw-bell":
        c = build_bell()
        print(c.draw("ascii" if args.ascii_output else "text"))
        return 0

    if args.command == "run-template":
        metadata = {}
        if args.name == "grover":
            c = grover_search(target_state=args.target_state, num_qubits=args.num_qubits)
        elif args.name == "shor":
            c, metadata = shor_factorization(num_to_factor=args.num_to_factor, num_qubits=max(4, args.num_qubits))
        elif args.name == "qft":
            c = qft_circuit(num_qubits=args.num_qubits)
        elif args.name == "bernstein-vazirani":
            c = bernstein_vazirani(secret=args.hidden_string)
        elif args.name == "qaoa":
            edges = [(i, i + 1) for i in range(max(1, args.num_qubits - 1))]
            c = qaoa_maxcut(num_qubits=args.num_qubits, edges=edges, beta=args.beta, gamma=args.gamma)
        elif args.name == "hamiltonian-sim":
            c = hamiltonian_simulation(num_qubits=args.num_qubits, dt=args.time)
        elif args.name == "quantum-walk":
            c = quantum_walk(num_qubits=max(2, args.num_qubits), steps=args.steps)
        else:
            c = vqe_hardware_efficient(num_qubits=args.num_qubits, depth=args.depth)
        result = c.run(shots=args.shots)
        print(
            json.dumps(
                {
                    "template": args.name,
                    "num_gates": len(c.gates),
                    "counts": result["counts"],
                    "metadata": metadata,
                },
                indent=2,
            )
        )
        return 0

    if args.command == "transpile-bell":
        tr = HardwareAwareTranspiler(args.backend)
        if args.coupling:
            edges = []
            for token in args.coupling.split(","):
                a, b = token.strip().split("-")
                edges.append((int(a), int(b)))
            tr.set_coupling_map(edges)
        tc = tr.transpile(build_bell())
        print(
            json.dumps(
                {
                    "backend": args.backend,
                    "original_gates": tc.stats.original_gates,
                    "transpiled_gates": tc.stats.transpiled_gates,
                    "inserted_swaps": tc.stats.inserted_swaps,
                },
                indent=2,
            )
        )
        return 0

    if args.command == "track-demo":
        tracker = QuantumAdvantageTracker()
        tracker.record("bell", quantum_ms=0.5, classical_ms=1.4)
        tracker.record("qaoa", quantum_ms=2.1, classical_ms=3.9)
        print(json.dumps(tracker.summary(), indent=2))
        return 0

    if args.command == "compatibility-report":
        sdk = AbirQuSDK()
        report = sdk.compatibility_report()
        if args.summary_only:
            report = {
                "summary": report.get("summary", {}),
                "runtime_checks": report.get("runtime_checks", {}),
            }
        print(json.dumps(report, indent=2))
        return 0

    if args.command == "capability-matrix":
        sdk = AbirQuSDK()
        report = sdk.capability_matrix()
        if args.summary_only:
            report = {
                "ready": report.get("ready", {}),
                "runtime_checks": report.get("runtime_checks", {}),
                "compatibility_summary": report.get("compatibility_summary", {}),
            }
        print(json.dumps(report, indent=2))
        return 0

    if args.command == "benchmark-spec":
        report = run_and_write_benchmark(output_path=args.output, profile=args.profile)
        summary = {
            "output": args.output,
            "profile": args.profile,
            "accuracy": report.get("accuracy", {}),
            "performance": report.get("performance", {}),
            "pass_fail": report.get("benchmark_spec_v1", {}).get("pass_fail", {}),
        }
        print(json.dumps(summary, indent=2))
        if args.stdout:
            print(json.dumps(report, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
