#!/usr/bin/env python3
"""
AbirQu Real Hardware Execution
================================
Run quantum circuits on real IBM Quantum hardware.

Usage:
  # Dry run (local simulation, no IBM credentials needed)
  python examples/real_hardware_execution.py --dry-run

  # Real hardware execution
  python examples/real_hardware_execution.py --backend ibm_brisbane --shots 1024

  # With credentials via environment variable
  export IBM_QUANTUM_TOKEN="your_token"
  python examples/real_hardware_execution.py --backend ibm_brisbane

Environment variables:
  IBM_QUANTUM_TOKEN  — IBM Quantum API token (from quantum.ibm.com)
  IBM_TOKEN          — Alternative env var name
"""
import sys
import os
import time
import argparse
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from abirqu import Circuit
from abirqu.library import qft_circuit, grover_circuit, ghz_circuit, vqe_hardware_efficient


def get_ibm_token():
    """Get IBM Quantum token from environment."""
    return os.environ.get('IBM_QUANTUM_TOKEN') or os.environ.get('IBM_TOKEN')


def create_test_circuits():
    """Create a suite of test circuits for hardware execution."""
    circuits = {}
    
    # 1. Bell state (2 qubits)
    bell = Circuit(2, name="Bell State")
    bell.h(0)
    bell.cnot(0, 1)
    bell.measure_all()
    circuits['bell_2q'] = bell
    
    # 2. GHZ state (3 qubits)
    ghz = ghz_circuit(3)
    ghz.measure_all()
    circuits['ghz_3q'] = ghz
    
    # 3. QFT (3 qubits)
    qft = qft_circuit(3)
    qft.measure_all()
    circuits['qft_3q'] = qft
    
    # 4. Grover search (2 qubits, target=3)
    grover = grover_circuit(2, target=3)
    grover.measure_all()
    circuits['grover_2q'] = grover
    
    # 5. VQE ansatz (4 qubits)
    vqe = vqe_hardware_efficient(4, depth=1)
    vqe.measure_all()
    circuits['vqe_4q'] = vqe
    
    # 6. Random circuit (5 qubits)
    from abirqu.library import random_circuit
    rand = random_circuit(5, depth=10, seed=42)
    rand.measure_all()
    circuits['random_5q'] = rand
    
    return circuits


def run_on_simulator(circuits, shots=1024):
    """Run circuits on local simulator (dry run)."""
    from abirqu import FastBackend
    backend = FastBackend()
    
    results = {}
    for name, circuit in circuits.items():
        t0 = time.perf_counter()
        result = backend.run_circuit(circuit, shots=shots)
        t1 = time.perf_counter()
        
        results[name] = {
            'counts': result.get('counts', {}),
            'time_ms': round((t1 - t0) * 1000, 2),
            'qubits': circuit.num_qubits,
            'gates': len(circuit.gates),
            'depth': circuit.depth(),
        }
    return results


def run_on_ibm(circuits, backend_name='ibm_brisbane', shots=1024):
    """Run circuits on real IBM Quantum hardware."""
    from abirqu.backends.ibm import IBMQuantumBackend
    
    backend = IBMQuantumBackend(backend_name=backend_name)
    
    results = {}
    for name, circuit in circuits.items():
        print(f"  Submitting {name} ({circuit.num_qubits} qubits, {len(circuit.gates)} gates)...")
        
        t0 = time.perf_counter()
        try:
            result = backend.run_circuit(circuit, shots=shots)
            t1 = time.perf_counter()
            
            results[name] = {
                'counts': result.get('counts', {}),
                'time_ms': round((t1 - t0) * 1000, 2),
                'qubits': circuit.num_qubits,
                'gates': len(circuit.gates),
                'depth': circuit.depth(),
                'status': 'success',
            }
            print(f"    Completed in {results[name]['time_ms']:.2f} ms")
        except Exception as e:
            t1 = time.perf_counter()
            results[name] = {
                'error': str(e),
                'time_ms': round((t1 - t0) * 1000, 2),
                'status': 'failed',
            }
            print(f"    Failed: {e}")
    
    return results


def print_results(results, title="Results"):
    """Pretty-print benchmark results."""
    print(f"\n{title}")
    print("=" * 70)
    print(f"{'Circuit':15s} {'Qubits':>6s} {'Gates':>6s} {'Depth':>6s} {'Time':>10s} {'States':>7s}")
    print("-" * 70)
    
    for name, r in results.items():
        if r.get('status') == 'failed':
            print(f"{name:15s} {'N/A':>6s} {'N/A':>6s} {'N/A':>6s} {r['time_ms']:>9.2f}ms {'FAILED':>7s}")
        else:
            counts = r.get('counts', {})
            print(f"{name:15s} {r['qubits']:>6d} {r['gates']:>6d} {r['depth']:>6d} {r['time_ms']:>9.2f}ms {len(counts):>7d}")
    
    print("-" * 70)
    
    # Show measurement results for key circuits
    print("\nMeasurement Results:")
    for name, r in results.items():
        if r.get('status') == 'failed':
            continue
        counts = r.get('counts', {})
        if not counts:
            continue
        # Sort by count descending
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        top3 = sorted_counts[:3]
        total = sum(counts.values())
        probs = {k: round(v/total, 3) for k, v in top3}
        print(f"  {name}: {probs}")


def main():
    parser = argparse.ArgumentParser(description='AbirQu Real Hardware Execution')
    parser.add_argument('--backend', default='local',
                       help='Backend: local, ibm_brisbane, ibm_nairobi, etc.')
    parser.add_argument('--shots', type=int, default=1024,
                       help='Number of shots (default: 1024)')
    parser.add_argument('--output', default=None,
                       help='Output JSON file')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run on local simulator instead of real hardware')
    args = parser.parse_args()
    
    circuits = create_test_circuits()
    
    print("AbirQu Real Hardware Execution")
    print("=" * 60)
    print(f"Circuits: {len(circuits)}")
    print(f"Max qubits: {max(c.num_qubits for c in circuits.values())}")
    print(f"Total gates: {sum(len(c.gates) for c in circuits.values())}")
    
    if args.dry_run or args.backend == 'local':
        print(f"\nRunning on local simulator (dry run)...")
        results = run_on_simulator(circuits, shots=args.shots)
        print_results(results, "Local Simulator Results")
    else:
        token = get_ibm_token()
        if not token:
            print("\nERROR: No IBM Quantum token found.")
            print("Set IBM_QUANTUM_TOKEN environment variable:")
            print("  export IBM_QUANTUM_TOKEN='your_token'")
            print("\nGet a token at: https://quantum.ibm.com/")
            print("\nFalling back to local simulator...")
            results = run_on_simulator(circuits, shots=args.shots)
            print_results(results, "Local Simulator Results (fallback)")
            return
        
        print(f"\nRunning on IBM Quantum ({args.backend})...")
        results = run_on_ibm(circuits, args.backend, shots=args.shots)
        print_results(results, f"IBM Quantum Results ({args.backend})")
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")


if __name__ == '__main__':
    main()
