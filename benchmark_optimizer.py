#!/usr/bin/env python3
"""
Benchmark: AbirQu Phase Polynomial Optimizer vs Qiskit Level 3
Replicating circuits similar to Amy et al. "A heuristic for phase polynomial optimization"
"""

import time
import numpy as np
from abirqu.circuit import Circuit
from abirqu.optimize.phase_poly import PhasePolynomialOptimizer

import warnings
warnings.filterwarnings('ignore')

try:
    from qiskit import QuantumCircuit, transpile
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False


def generate_hidden_shift_circuit(n: int, cnot_density: int = 3, rz_density: int = 2) -> Circuit:
    """
    Generate a pseudo-random CNOT+RZ circuit similar to Hidden Shift instances.
    Amy et al. benchmarks often use T-count optimized circuits which are dense in CNOTs and RZs.
    """
    np.random.seed(42)
    qc = Circuit(n)
    
    # We only add CNOT and RZ to stress the phase polynomial optimizer
    for _ in range(n * cnot_density):
        c, t = np.random.choice(n, 2, replace=False)
        qc.cnot(int(c), int(t))
        
        # Add RZ gates (like T, S, Z gates)
        for _ in range(rz_density):
            q = np.random.randint(n)
            angle = np.random.choice([np.pi/4, np.pi/2, np.pi])
            qc.rz(int(q), angle)
            
    # Add some final CNOTs
    for _ in range(n):
        c, t = np.random.choice(n, 2, replace=False)
        qc.cnot(int(c), int(t))
        
    return qc


def to_qiskit(circuit: Circuit) -> 'QuantumCircuit':
    qc = QuantumCircuit(circuit.num_qubits)
    for g in circuit.gates:
        name = g.name.upper()
        if name == 'CNOT':
            qc.cx(g.qubits[0], g.qubits[1])
        elif name == 'RZ':
            qc.rz(g.params[0], g.qubits[0])
        elif name == 'H':
            qc.h(g.qubits[0])
    return qc

def count_cnots_abirqu(circuit: Circuit) -> int:
    return sum(1 for g in getattr(circuit, 'gates', []) if g.name.upper() in ('CNOT', 'CX'))

from abirqu.optimize.circuit_simplifier import CircuitSimplifier

def main():
    print("======================================================================")
    print("  AbirQu Phase Polynomial Optimizer vs Qiskit (Level 3)")
    print("======================================================================")
    
    sizes = [8, 12, 16]
    
    opt_phase = PhasePolynomialOptimizer()
    opt_simp = CircuitSimplifier()
    
    for n in sizes:
        qc = generate_hidden_shift_circuit(n, cnot_density=4, rz_density=2)
        initial_cnots = count_cnots_abirqu(qc)
        
        print(f"\n[Circuit: {n} qubits, {initial_cnots} initial CNOTs]")
        
        # AbirQu Simplifier
        t0 = time.perf_counter()
        qc_simp = opt_simp.optimize(qc)
        t_simp = time.perf_counter() - t0
        simp_cnots = count_cnots_abirqu(qc_simp)
        simp_reduction = 100 * (initial_cnots - simp_cnots) / initial_cnots
        
        print(f"  AbirQu Simplifier: {simp_cnots} CNOTs ({simp_reduction:.1f}% reduction) in {t_simp:.3f}s")
        
        # AbirQu PhasePoly
        t0 = time.perf_counter()
        qc_opt = opt_phase.optimize(qc)
        t_abirqu = time.perf_counter() - t0
        abirqu_cnots = count_cnots_abirqu(qc_opt)
        abirqu_reduction = 100 * (initial_cnots - abirqu_cnots) / initial_cnots
        
        print(f"  AbirQu PhasePoly : {abirqu_cnots} CNOTs ({abirqu_reduction:.1f}% reduction) in {t_abirqu:.3f}s")
        
        # Qiskit Optimization
        if HAS_QISKIT:
            qiskit_qc = to_qiskit(qc)
            t0 = time.perf_counter()
            qiskit_opt = transpile(qiskit_qc, optimization_level=3, basis_gates=['cx', 'rz', 'h'])
            t_qiskit = time.perf_counter() - t0
            
            # Count CNOTs in Qiskit
            qiskit_cnots = dict(qiskit_opt.count_ops()).get('cx', 0)
            qiskit_reduction = 100 * (initial_cnots - qiskit_cnots) / initial_cnots
            
            print(f"  Qiskit (Level 3) : {qiskit_cnots} CNOTs ({qiskit_reduction:.1f}% reduction) in {t_qiskit:.3f}s")
            
            # Comparison against best AbirQu
            best_abirqu = min(simp_cnots, abirqu_cnots)
            diff = qiskit_cnots - best_abirqu
            if diff > 0:
                print(f"  🏆 AbirQu wins by {diff} CNOTs!")
            elif diff < 0:
                print(f"  🏆 Qiskit wins by {-diff} CNOTs!")
            else:
                print(f"  🤝 TIE in CNOT count!")

if __name__ == "__main__":
    main()
