#!/usr/bin/env python3
"""
=============================================================================
AbirQu vs Qiskit vs Cirq — Benchmark Suite
Phase 0: Environment Setup & Validation
=============================================================================
Author:  AbirQu Benchmark Engineering
Date:    2026-05-07
Purpose: Install dependencies, detect system specs, validate all three
         quantum frameworks, and produce a reproducible MACHINE_SPEC block.
=============================================================================
"""
import sys
import os
import json
import platform
import time
import csv
from pathlib import Path

# ── Directory structure ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent / "benchmark_results"
RAW_DIR  = BASE_DIR / "raw_data"
PLOT_DIR = BASE_DIR / "plots"

REQUIRED_CSVS = [
    "circuit_construction.csv",
    "gate_application.csv",
    "simulation_speed.csv",
    "memory_usage.csv",
    "phase_polynomial.csv",
    "transpilation.csv",
    "qec_decoding.csv",
    "noise_simulation.csv",
    "measurement.csv",
    "scalability.csv",
]

def create_directories():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Directory structure created at {BASE_DIR}")


# ── System detection ─────────────────────────────────────────────────────

def detect_cpu() -> str:
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    return line.split(":")[1].strip()
    except Exception:
        pass
    return platform.processor() or "Unknown"

def detect_gpu() -> str:
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0]
    except Exception:
        pass
    return "None (CPU-only)"

def detect_ram_gb() -> float:
    try:
        import psutil
        return round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except Exception:
        try:
            return round(
                os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / (1024**3), 1
            )
        except Exception:
            return 0.0


def get_framework_versions() -> dict:
    versions = {}
    # AbirQu
    try:
        import abirqu
        versions["abirqu"] = getattr(abirqu, "__version__", "0.1.0")
    except ImportError:
        versions["abirqu"] = "NOT INSTALLED"

    # Qiskit
    try:
        import qiskit
        versions["qiskit"] = qiskit.__version__
    except ImportError:
        versions["qiskit"] = "NOT INSTALLED"

    # Qiskit Aer
    try:
        import qiskit_aer
        versions["qiskit_aer"] = qiskit_aer.__version__
    except ImportError:
        versions["qiskit_aer"] = "NOT INSTALLED"

    # Cirq
    try:
        import cirq
        versions["cirq"] = cirq.__version__
    except ImportError:
        versions["cirq"] = "NOT INSTALLED"

    # Supporting libraries
    for lib in ["numpy", "scipy", "psutil", "matplotlib"]:
        try:
            mod = __import__(lib)
            versions[lib] = mod.__version__
        except ImportError:
            versions[lib] = "NOT INSTALLED"

    return versions


def build_machine_spec() -> dict:
    versions = get_framework_versions()
    spec = {
        "cpu": detect_cpu(),
        "cores": os.cpu_count(),
        "ram_gb": detect_ram_gb(),
        "gpu": detect_gpu(),
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "abirqu_version": versions.get("abirqu", "?"),
        "qiskit_version": versions.get("qiskit", "?"),
        "qiskit_aer_version": versions.get("qiskit_aer", "?"),
        "cirq_version": versions.get("cirq", "?"),
        "numpy_version": versions.get("numpy", "?"),
        "scipy_version": versions.get("scipy", "?"),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    }
    return spec


# ── Validation ───────────────────────────────────────────────────────────

def validate_abirqu() -> bool:
    try:
        from abirqu.circuit import Circuit
        from abirqu.simulator import SimulatorBackend
        qc = Circuit(2)
        qc.h(0)
        qc.cnot(0, 1)
        sim = SimulatorBackend()
        result = sim.run(qc)
        assert "probabilities" in result
        print(f"[OK] AbirQu: Circuit + SimulatorBackend working (probs: {result['probabilities']})")
        return True
    except Exception as e:
        print(f"[FAIL] AbirQu: {e}")
        return False


def validate_qiskit() -> bool:
    try:
        from qiskit import QuantumCircuit
        from qiskit_aer import AerSimulator
        from qiskit import transpile

        qc = QuantumCircuit(2, 2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure([0, 1], [0, 1])

        sim = AerSimulator()
        compiled = transpile(qc, sim)
        result = sim.run(compiled, shots=1024).result()
        counts = result.get_counts()
        assert len(counts) > 0
        print(f"[OK] Qiskit: Circuit + Aer simulation working (counts: {counts})")
        return True
    except Exception as e:
        print(f"[FAIL] Qiskit: {e}")
        return False


def validate_cirq() -> bool:
    try:
        import cirq
        q0, q1 = cirq.LineQubit.range(2)
        circuit = cirq.Circuit([
            cirq.H(q0),
            cirq.CNOT(q0, q1),
            cirq.measure(q0, q1, key="result"),
        ])
        sim = cirq.Simulator()
        result = sim.run(circuit, repetitions=1024)
        counts = result.histogram(key="result")
        assert len(counts) > 0
        print(f"[OK] Cirq: Circuit + Simulator working (counts: {dict(counts)})")
        return True
    except Exception as e:
        print(f"[FAIL] Cirq: {e}")
        return False


# ── Report helpers ───────────────────────────────────────────────────────

def save_machine_spec(spec: dict):
    spec_file = BASE_DIR / "machine_spec.json"
    with open(spec_file, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"[OK] Machine spec saved to {spec_file}")


def generate_machine_spec_python(spec: dict) -> str:
    """Returns a copy-pasteable MACHINE_SPEC dict for other benchmark files."""
    lines = ["MACHINE_SPEC = {"]
    for k, v in spec.items():
        if isinstance(v, str):
            lines.append(f'    "{k}": "{v}",')
        else:
            lines.append(f'    "{k}": {v},')
    lines.append("}")
    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("  AbirQu vs Qiskit vs Cirq — Benchmark Environment Setup")
    print("=" * 72)

    # 1. Create directories
    print("\n[1/5] Creating directory structure...")
    create_directories()

    # 2. Detect system
    print("\n[2/5] Detecting system specifications...")
    spec = build_machine_spec()
    for k, v in spec.items():
        print(f"  {k:25s}: {v}")

    # 3. Save spec
    print("\n[3/5] Saving machine specification...")
    save_machine_spec(spec)

    # 4. Generate Python constant
    print("\n[4/5] Generating MACHINE_SPEC block...")
    py_block = generate_machine_spec_python(spec)
    print(py_block)

    # Save as importable module
    spec_module = BASE_DIR / "spec.py"
    with open(spec_module, "w") as f:
        f.write('"""Auto-generated machine specification for benchmarks."""\n\n')
        f.write(py_block + "\n")
    print(f"\n  → Saved to {spec_module}")

    # 5. Validate frameworks
    print("\n[5/5] Validating quantum frameworks...")
    results = {
        "abirqu": validate_abirqu(),
        "qiskit": validate_qiskit(),
        "cirq": validate_cirq(),
    }

    # Summary
    print("\n" + "=" * 72)
    print("  ENVIRONMENT VALIDATION SUMMARY")
    print("=" * 72)
    all_ok = True
    for name, ok in results.items():
        status = "✅ READY" if ok else "❌ FAILED"
        print(f"  {name:12s}: {status}")
        if not ok:
            all_ok = False

    if all_ok:
        print("\n  🚀 All three frameworks validated. Ready for benchmarking.")
    else:
        failed = [k for k, v in results.items() if not v]
        print(f"\n  ⚠️  Framework(s) {failed} failed validation.")
        print("     Benchmarks for failed frameworks will be recorded as N/A.")

    print("=" * 72)
    return spec, results


if __name__ == "__main__":
    spec, results = main()
