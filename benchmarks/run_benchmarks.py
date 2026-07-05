#!/usr/bin/env python3
"""
AbirQu Benchmark Suite
======================
Real, reproducible benchmarks measuring wall-clock time and memory
for core quantum operations across increasing problem sizes.

Benchmarks:
  1. QFT (Quantum Fourier Transform) — depth scaling
  2. Random circuits — gate-count scaling
  3. VQE hardware-efficient ansatz — parameter scaling
  4. Grover search — iteration scaling
  5. State preparation — qubit scaling
  6. Circuit simulation — full pipeline

Run with:
  python benchmarks/run_benchmarks.py [--backend local|ibm] [--output results.json]
"""
import sys
import os
import time
import json
import argparse
import tracemalloc
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
from abirqu import Circuit
from abirqu.library import (
    qft_circuit, grover_circuit, qaoa_maxcut,
    vqe_hardware_efficient, real_amplitudes, ghz_circuit,
    random_circuit
)


def get_backend(name="local"):
    """Get simulation backend."""
    if name == "local":
        from abirqu import FastBackend
        return FastBackend()
    elif name == "ibm":
        from abirqu.backends.ibm import IBMQuantumBackend
        return IBMQuantumBackend()
    else:
        raise ValueError(f"Unknown backend: {name}")


def benchmark_qft(sizes, backend, shots=1024):
    """Benchmark Quantum Fourier Transform at increasing qubit counts."""
    results = []
    for n in sizes:
        circuit = qft_circuit(n)
        
        tracemalloc.start()
        t0 = time.perf_counter()
        result = backend.run_circuit(circuit, shots=shots)
        t1 = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        counts = result.get('counts', {})
        results.append({
            'circuit': f'QFT-{n}',
            'qubits': n,
            'gates': len(circuit.gates),
            'depth': circuit.depth(),
            'time_ms': round((t1 - t0) * 1000, 2),
            'peak_memory_kb': round(peak / 1024, 1),
            'unique_states': len(counts),
            'shots': shots,
        })
    return results


def benchmark_random_circuits(sizes, depths, backend, shots=1024):
    """Benchmark random circuits at increasing size and depth."""
    results = []
    for n in sizes:
        for d in depths:
            circuit = random_circuit(n, d, seed=42)
            
            tracemalloc.start()
            t0 = time.perf_counter()
            result = backend.run_circuit(circuit, shots=shots)
            t1 = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            counts = result.get('counts', {})
            results.append({
                'circuit': f'Random-{n}q-{d}d',
                'qubits': n,
                'gates': len(circuit.gates),
                'depth': circuit.depth(),
                'time_ms': round((t1 - t0) * 1000, 2),
                'peak_memory_kb': round(peak / 1024, 1),
                'unique_states': len(counts),
                'shots': shots,
            })
    return results


def benchmark_vqe_ansatz(sizes, reps_list, backend, shots=1024):
    """Benchmark VQE hardware-efficient ansatz at increasing size."""
    results = []
    for n in sizes:
        for reps in reps_list:
            circuit = vqe_hardware_efficient(n, depth=reps)
            
            tracemalloc.start()
            t0 = time.perf_counter()
            result = backend.run_circuit(circuit, shots=shots)
            t1 = time.perf_counter()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            counts = result.get('counts', {})
            results.append({
                'circuit': f'VQE-{n}q-r{reps}',
                'qubits': n,
                'gates': len(circuit.gates),
                'depth': circuit.depth(),
                'time_ms': round((t1 - t0) * 1000, 2),
                'peak_memory_kb': round(peak / 1024, 1),
                'unique_states': len(counts),
                'shots': shots,
            })
    return results


def benchmark_grover(sizes, backend, shots=1024):
    """Benchmark Grover's search at increasing qubit counts."""
    results = []
    for n in sizes:
        target = (2 ** n) // 2  # mark middle state
        circuit = grover_circuit(n, target=target)
        
        tracemalloc.start()
        t0 = time.perf_counter()
        result = backend.run_circuit(circuit, shots=shots)
        t1 = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        counts = result.get('counts', {})
        target_str = format(target, f'0{n}b')
        success_prob = counts.get(target_str, 0) / shots
        
        results.append({
            'circuit': f'Grover-{n}q',
            'qubits': n,
            'gates': len(circuit.gates),
            'depth': circuit.depth(),
            'time_ms': round((t1 - t0) * 1000, 2),
            'peak_memory_kb': round(peak / 1024, 1),
            'success_probability': round(success_prob, 3),
            'target_state': target_str,
            'shots': shots,
        })
    return results


def benchmark_ghz(sizes, backend, shots=1024):
    """Benchmark GHZ state preparation at increasing qubit counts."""
    results = []
    for n in sizes:
        circuit = ghz_circuit(n)
        
        tracemalloc.start()
        t0 = time.perf_counter()
        result = backend.run_circuit(circuit, shots=shots)
        t1 = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        counts = result.get('counts', {})
        all_zeros = counts.get('0' * n, 0) / shots
        all_ones = counts.get('1' * n, 0) / shots
        ghz_fidelity = all_zeros + all_ones
        
        results.append({
            'circuit': f'GHZ-{n}q',
            'qubits': n,
            'gates': len(circuit.gates),
            'depth': circuit.depth(),
            'time_ms': round((t1 - t0) * 1000, 2),
            'peak_memory_kb': round(peak / 1024, 1),
            'ghz_fidelity': round(ghz_fidelity, 3),
            'shots': shots,
        })
    return results


def benchmark_full_pipeline(sizes, backend, shots=1024):
    """Benchmark complete circuit construction + simulation pipeline."""
    results = []
    for n in sizes:
        # Build a complex circuit: QFT + entanglement + measurement
        circuit = Circuit(n, name=f"Pipeline-{n}")
        for i in range(n):
            circuit.h(i)
        for i in range(n - 1):
            circuit.cnot(i, i + 1)
        for i in range(n):
            circuit.ry(i, np.pi / 4)
        circuit.measure_all()
        
        tracemalloc.start()
        t0 = time.perf_counter()
        result = backend.run_circuit(circuit, shots=shots)
        t1 = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        counts = result.get('counts', {})
        results.append({
            'circuit': f'Pipeline-{n}q',
            'qubits': n,
            'gates': len(circuit.gates),
            'depth': circuit.depth(),
            'time_ms': round((t1 - t0) * 1000, 2),
            'peak_memory_kb': round(peak / 1024, 1),
            'unique_states': len(counts),
            'shots': shots,
        })
    return results


def run_all_benchmarks(backend_name="local", output_file=None):
    """Run the complete benchmark suite."""
    backend = get_backend(backend_name)
    
    print(f"AbirQu Benchmark Suite — backend: {backend_name}")
    print("=" * 60)
    
    all_results = {}
    
    # 1. QFT
    print("\n[1/6] QFT benchmarks...")
    qft_sizes = [2, 4, 6, 8, 10, 12]
    all_results['qft'] = benchmark_qft(qft_sizes, backend)
    for r in all_results['qft']:
        print(f"  {r['circuit']:12s}: {r['time_ms']:8.2f} ms, {r['gates']:4d} gates, {r['depth']:3d} depth")
    
    # 2. Random circuits
    print("\n[2/6] Random circuit benchmarks...")
    all_results['random'] = benchmark_random_circuits(
        sizes=[3, 5, 7, 10],
        depths=[5, 10, 20],
        backend=backend
    )
    for r in all_results['random']:
        print(f"  {r['circuit']:20s}: {r['time_ms']:8.2f} ms, {r['gates']:4d} gates")
    
    # 3. VQE ansatz
    print("\n[3/6] VQE ansatz benchmarks...")
    all_results['vqe'] = benchmark_vqe_ansatz(
        sizes=[2, 4, 6, 8],
        reps_list=[1, 2, 3],
        backend=backend
    )
    for r in all_results['vqe']:
        print(f"  {r['circuit']:16s}: {r['time_ms']:8.2f} ms, {r['gates']:4d} gates")
    
    # 4. Grover search
    print("\n[4/6] Grover search benchmarks...")
    all_results['grover'] = benchmark_grover([2, 3, 4, 5], backend)
    for r in all_results['grover']:
        print(f"  {r['circuit']:12s}: {r['time_ms']:8.2f} ms, success={r['success_probability']:.3f}")
    
    # 5. GHZ state
    print("\n[5/6] GHZ state benchmarks...")
    all_results['ghz'] = benchmark_ghz([2, 4, 6, 8, 10], backend)
    for r in all_results['ghz']:
        print(f"  {r['circuit']:12s}: {r['time_ms']:8.2f} ms, fidelity={r['ghz_fidelity']:.3f}")
    
    # 6. Full pipeline
    print("\n[6/6] Full pipeline benchmarks...")
    all_results['pipeline'] = benchmark_full_pipeline([2, 4, 6, 8, 10], backend)
    for r in all_results['pipeline']:
        print(f"  {r['circuit']:16s}: {r['time_ms']:8.2f} ms, {r['gates']:4d} gates")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_flat = []
    for category, results in all_results.items():
        all_flat.extend(results)
    
    total_gates = sum(r['gates'] for r in all_flat)
    total_time = sum(r['time_ms'] for r in all_flat)
    max_qubits = max(r['qubits'] for r in all_flat)
    
    print(f"  Total benchmarks: {len(all_flat)}")
    print(f"  Max qubits tested: {max_qubits}")
    print(f"  Total gates simulated: {total_gates:,}")
    print(f"  Total time: {total_time:.2f} ms")
    print(f"  Average time per circuit: {total_time/len(all_flat):.2f} ms")
    
    # Save results
    output = {
        'metadata': {
            'backend': backend_name,
            'timestamp': datetime.now().isoformat(),
            'total_benchmarks': len(all_flat),
            'max_qubits': max_qubits,
            'total_gates': total_gates,
            'total_time_ms': round(total_time, 2),
        },
        'results': all_results,
    }
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\nResults saved to {output_file}")
    
    return output


def main():
    parser = argparse.ArgumentParser(description='AbirQu Benchmark Suite')
    parser.add_argument('--backend', default='local', choices=['local', 'ibm'],
                       help='Simulation backend (default: local)')
    parser.add_argument('--output', default='benchmark_results.json',
                       help='Output file for results (default: benchmark_results.json)')
    args = parser.parse_args()
    
    run_all_benchmarks(args.backend, args.output)


if __name__ == '__main__':
    main()
