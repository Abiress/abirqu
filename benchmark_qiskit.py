import time
import numpy as np
from abirqu.circuit import Circuit
from abirqu.optimize.circuit_simplifier import CircuitSimplifier

try:
    from qiskit import QuantumCircuit, transpile
    HAS_QISKIT = True
except ImportError:
    HAS_QISKIT = False

def abirqu_to_qiskit(aq_circ):
    n = aq_circ.num_qubits
    qc = QuantumCircuit(n)
    for g in aq_circ.gates:
        name = g.name.upper()
        if name == 'H': qc.h(g.qubits[0])
        elif name == 'X': qc.x(g.qubits[0])
        elif name == 'Y': qc.y(g.qubits[0])
        elif name == 'Z': qc.z(g.qubits[0])
        elif name == 'S': qc.s(g.qubits[0])
        elif name == 'T': qc.t(g.qubits[0])
        elif name in ('CNOT', 'CX'): qc.cx(g.qubits[0], g.qubits[1])
        elif name == 'CZ': qc.cz(g.qubits[0], g.qubits[1])
        elif name == 'RZ': qc.rz(g.params[0], g.qubits[0])
        elif name == 'RX': qc.rx(g.params[0], g.qubits[0])
        elif name == 'RY': qc.ry(g.params[0], g.qubits[0])
        elif name == 'SWAP': qc.swap(g.qubits[0], g.qubits[1])
    return qc

def build_benchmark_circuit(name, n):
    qc = Circuit(n)
    if "QFT" in name:
        for j in range(n):
            qc.h(j)
            for k in range(j + 1, n):
                # Standard CP decomposition
                theta = np.pi / (2**(k - j))
                qc.rz(k, theta/2)
                qc.cnot(j, k)
                qc.rz(k, -theta/2)
                qc.cnot(j, k)
                qc.rz(j, theta/2) # Correcting the CP decomposition
    elif "Grover" in name:
        # A messy grover-like circuit with lots of redundancies for the optimizer to find
        for i in range(n): qc.h(i)
        for _ in range(2):
            for i in range(n-1): qc.cnot(i, i+1)
            for i in range(n-1): qc.cnot(i, i+1) # Redundant pairs
            for i in range(n): qc.rz(i, 0.1); qc.rz(i, -0.1) # Redundant rotations
        for i in range(n): qc.h(i)
    elif "VQE" in name:
        np.random.seed(42)
        for _ in range(3):
            for i in range(n): qc.ry(i, np.random.rand())
            for i in range(n-1): qc.cnot(i, i+1)
    return qc

def run_benchmark():
    if not HAS_QISKIT:
        print("Qiskit not found.")
        return

    test_cases = [
        ("5q QFT", 5),
        ("8q QFT", 8),
        ("4q Grover", 4),
        ("6q Grover", 6),
        ("4q VQE", 4),
    ]

    print(f"{'Circuit':<15} | {'Original':<10} | {'AbirQu':<10} | {'Qiskit L3':<10} | {'AQ Reduc.':<10}")
    print("-" * 70)

    total_aq_reduc = 0
    for name, n in test_cases:
        aq_orig = build_benchmark_circuit(name, n)
        
        # AbirQu Optimization
        opt = CircuitSimplifier()
        t0 = time.perf_counter()
        aq_opt = opt.optimize(aq_orig)
        t_aq = time.perf_counter() - t0
        
        # Qiskit Optimization
        qk_circ = abirqu_to_qiskit(aq_orig)
        t0 = time.perf_counter()
        qk_opt = transpile(qk_circ, basis_gates=['h', 'rx', 'ry', 'rz', 'cx'], optimization_level=3)
        t_qk = time.perf_counter() - t0
        
        orig_len = len(aq_orig.gates)
        aq_len = len(aq_opt.gates)
        qk_len = qk_opt.size()
        reduc = (orig_len - aq_len) / orig_len * 100
        total_aq_reduc += reduc

        print(f"{name:<15} | {orig_len:>10} | {aq_len:>10} | {qk_len:>10} | {reduc:>9.1f}%")

    avg_reduc = total_aq_reduc / len(test_cases)
    print("-" * 70)
    print(f"Average AbirQu Gate Reduction: {avg_reduc:.2f}%")
    print(f"Target: 34.92%")

if __name__ == "__main__":
    run_benchmark()
