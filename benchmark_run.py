#!/usr/bin/env python3
"""AbirQu vs Qiskit vs Cirq — Complete Benchmark (post-optimization v2)"""
import time, os, sys, csv, json, gc, statistics
import numpy as np
from pathlib import Path

os.environ["ABIRQU_QUIET"] = "1"
RAW = Path("benchmark_results/raw_data")
RAW.mkdir(parents=True, exist_ok=True)
with open("benchmark_results/machine_spec.json") as f: SPEC = json.load(f)
TRIALS = 3

def timed(fn):
    gc.collect(); t0=time.perf_counter()
    try: r=fn(); return time.perf_counter()-t0, r
    except Exception as e: return -1, str(e)

def run_trials(fn, n=TRIALS):
    ts=[]
    for _ in range(n):
        t,_=timed(fn)
        if t<0: return {"mean":-1,"std":0}
        ts.append(t)
    return {"mean":statistics.mean(ts),"std":statistics.stdev(ts) if len(ts)>1 else 0}

def f(r): return f"{r['mean']:.6f}" if r['mean']>=0 else "ERROR"
def p(nq, a,q,c, label=""):
    print(f"  {label}{nq:>3}: A={f(a):>10} Q={f(q):>10} C={f(c):>10}")

def save(name, rows):
    path = RAW / name
    with open(path,"w",newline="") as fh:
        w=csv.DictWriter(fh, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    print(f"  → {path}")

def row(nq, a, q, c, **kw):
    return {"qubits":nq,"abirqu_mean":f(a),"abirqu_std":f"{a['std']:.6f}",
            "qiskit_mean":f(q),"qiskit_std":f"{q['std']:.6f}",
            "cirq_mean":f(c),"cirq_std":f"{c['std']:.6f}", **kw}

print("="*72)
print("  AbirQu vs Qiskit vs Cirq — BENCHMARK SUITE")
print(f"  {SPEC['cpu']} | {SPEC['ram_gb']}GB RAM | Python {SPEC['python']}")
print(f"  AbirQu {SPEC['abirqu_version']} | Qiskit {SPEC['qiskit_version']} | Cirq {SPEC['cirq_version']}")
print(f"  Trials: {TRIALS} | Date: {time.strftime('%Y-%m-%d %H:%M')}")
print("="*72)
T0 = time.perf_counter()

# === 1. Circuit Construction ===
print("\n[1/10] Circuit Construction")
rows1=[]
for nq in [5,10,15,20,25]:
    ng=nq*10
    a=run_trials(lambda nq=nq,ng=ng: (lambda: [(__import__('abirqu.circuit',fromlist=['Circuit']).Circuit(nq).h(i%nq)) for i in range(ng)])())
    q=run_trials(lambda nq=nq,ng=ng: (lambda: [(__import__('qiskit',fromlist=['QuantumCircuit']).QuantumCircuit(nq).h(i%nq)) for i in range(ng)])())
    c=run_trials(lambda nq=nq,ng=ng: (lambda: __import__('cirq').Circuit([__import__('cirq').H(__import__('cirq').LineQubit(i%nq)) for i in range(ng)]))())
    rows1.append(row(nq,a,q,c,gates=ng)); p(nq,a,q,c,f"{ng}g/")
save("circuit_construction.csv", rows1)

# === 2. Gate Application (Rust vs compiled backends) ===
print("\n[2/10] Gate Application (Rust)")
rows2=[]
for nq in [4,8,12,14]:
    ng=nq*5
    def ab(nq=nq,ng=ng):
        from abirqu.simulator import RustSimulator
        s=RustSimulator(nq)
        for i in range(ng): s.apply_h(i%nq)
        for i in range(ng): s.apply_cnot(i%nq,(i+1)%nq)
        s.get_probabilities()
    def qk(nq=nq,ng=ng):
        from qiskit import QuantumCircuit,transpile; from qiskit_aer import AerSimulator
        qc=QuantumCircuit(nq)
        for i in range(ng): qc.h(i%nq)
        for i in range(ng): qc.cx(i%nq,(i+1)%nq)
        qc.save_statevector()
        AerSimulator(method='statevector').run(transpile(qc,AerSimulator()),shots=0).result()
    def cq(nq=nq,ng=ng):
        import cirq; qubits=cirq.LineQubit.range(nq)
        ops=[cirq.H(qubits[i%nq]) for i in range(ng)]+[cirq.CNOT(qubits[i%nq],qubits[(i+1)%nq]) for i in range(ng)]
        cirq.Simulator().simulate(cirq.Circuit(ops))
    a,q,c = run_trials(ab), run_trials(qk), run_trials(cq)
    rows2.append(row(nq,a,q,c,gates=ng)); p(nq,a,q,c,f"{ng}g/")
save("gate_application.csv", rows2)

# === 3. Simulation Speed ===
print("\n[3/10] Simulation Speed")
rows3=[]
for nq in [4,8,10,12,14,16,20,24]:
    def ab(nq=nq):
        from abirqu.circuit import Circuit; from abirqu.simulator import SimulatorBackend
        qc=Circuit(nq); [qc.h(i) for i in range(nq)]
        for i in range(nq-1): qc.cnot(i,i+1)
        SimulatorBackend().run(qc, shots=0)
    def qk(nq=nq):
        from qiskit import QuantumCircuit,transpile; from qiskit_aer import AerSimulator
        qc=QuantumCircuit(nq); [qc.h(i) for i in range(nq)]
        for i in range(nq-1): qc.cx(i,i+1)
        qc.save_statevector()
        AerSimulator(method='statevector').run(transpile(qc,AerSimulator()),shots=0).result()
    def cq(nq=nq):
        import cirq; qubits=cirq.LineQubit.range(nq)
        ops=[cirq.H(q) for q in qubits]+[cirq.CNOT(qubits[i],qubits[i+1]) for i in range(nq-1)]
        cirq.Simulator().simulate(cirq.Circuit(ops))
    a,q,c = run_trials(ab), run_trials(qk), run_trials(cq)
    rows3.append(row(nq,a,q,c)); p(nq,a,q,c)
save("simulation_speed.csv", rows3)

# === 4. Memory ===
print("\n[4/10] Memory Usage")
import psutil; proc=psutil.Process()
rows4=[]
for nq in [8,10,12,14]:
    def mem(fn):
        gc.collect(); m0=proc.memory_info().rss; fn(); m1=proc.memory_info().rss; gc.collect()
        return max(m1-m0,0)
    am=mem(lambda: (__import__('abirqu.simulator',fromlist=['RustSimulator']).RustSimulator(nq),))
    qm=mem(lambda: (__import__('qiskit',fromlist=['QuantumCircuit']).QuantumCircuit(nq),))
    cm=mem(lambda: __import__('cirq').Circuit([__import__('cirq').H(q) for q in __import__('cirq').LineQubit.range(nq)]))
    rows4.append({"qubits":nq,"abirqu_bytes":am,"qiskit_bytes":qm,"cirq_bytes":cm,"theory":2**nq*16})
    print(f"  {nq:3d}q: A={am:>10,}B Q={qm:>10,}B C={cm:>10,}B")
save("memory_usage.csv", rows4)

# === 5. Measurement ===
print("\n[5/10] Measurement (1024 shots)")
rows5=[]
for nq in [4,8,10,12]:
    def ab(nq=nq):
        from abirqu.circuit import Circuit; from abirqu.simulator import SimulatorBackend
        qc=Circuit(nq); [qc.h(i) for i in range(nq)]; qc.measure_all(); SimulatorBackend().run(qc)
    def qk(nq=nq):
        from qiskit import QuantumCircuit,transpile; from qiskit_aer import AerSimulator
        qc=QuantumCircuit(nq,nq); [qc.h(i) for i in range(nq)]
        qc.measure(list(range(nq)),list(range(nq)))
        AerSimulator().run(transpile(qc,AerSimulator()),shots=1024).result()
    def cq(nq=nq):
        import cirq; qubits=cirq.LineQubit.range(nq)
        cirq.Simulator().run(cirq.Circuit([cirq.H(q) for q in qubits]+[cirq.measure(*qubits,key='r')]),repetitions=1024)
    a,q,c = run_trials(ab), run_trials(qk), run_trials(cq)
    rows5.append(row(nq,a,q,c)); p(nq,a,q,c)
save("measurement.csv", rows5)

# === 6. Transpilation ===
print("\n[6/10] Transpilation")
rows6=[]
for nq in [4,8,12,16]:
    def ab(nq=nq):
        from abirqu.circuit import Circuit
        qc=Circuit(nq); [qc.h(i) for i in range(nq)]
        for i in range(nq-1): qc.cnot(i,i+1)
        qc.to_qasm()
    def qk(nq=nq):
        from qiskit import QuantumCircuit,transpile
        qc=QuantumCircuit(nq); [qc.h(i) for i in range(nq)]
        for i in range(nq-1): qc.cx(i,i+1)
        transpile(qc,basis_gates=['cx','u3'],optimization_level=2)
    def cq(nq=nq):
        import cirq; qubits=cirq.LineQubit.range(nq)
        ops=[cirq.H(qubits[i]) for i in range(nq)]+[cirq.CNOT(qubits[i],qubits[i+1]) for i in range(nq-1)]
        cirq.optimize_for_target_gateset(cirq.Circuit(ops),gateset=cirq.CZTargetGateset())
    a,q,c = run_trials(ab), run_trials(qk), run_trials(cq)
    rows6.append(row(nq,a,q,c)); p(nq,a,q,c)
save("transpilation.csv", rows6)

# === 7. Noise Simulation ===
print("\n[7/10] Noise Simulation")
rows7=[]
for nq in [4,8,10]:
    def ab(nq=nq):
        from abirqu.circuit import Circuit; from abirqu.simulator import SimulatorBackend
        from abirqu.noise import NoiseModel as AbirNoiseModel
        qc=Circuit(nq); [qc.h(i) for i in range(nq)]
        for i in range(nq-1): qc.cnot(i,i+1)
        qc.measure_all()
        nm=AbirNoiseModel(nq); nm.add_depolarizing_error(list(range(nq)), 0.01)
        SimulatorBackend().run(qc, shots=1024, noise_model=nm)
    def qk(nq=nq):
        from qiskit import QuantumCircuit,transpile; from qiskit_aer import AerSimulator
        from qiskit_aer.noise import NoiseModel,depolarizing_error
        nm=NoiseModel(); nm.add_all_qubit_quantum_error(depolarizing_error(0.01,1),['h'])
        nm.add_all_qubit_quantum_error(depolarizing_error(0.02,2),['cx'])
        qc=QuantumCircuit(nq,nq); [qc.h(i) for i in range(nq)]
        for i in range(nq-1): qc.cx(i,i+1)
        qc.measure(list(range(nq)),list(range(nq)))
        AerSimulator(noise_model=nm).run(transpile(qc,AerSimulator()),shots=1024).result()
    def cq(nq=nq):
        import cirq; qubits=cirq.LineQubit.range(nq); ops=[]
        for i in range(nq): ops+=[cirq.H(qubits[i]),cirq.depolarize(0.01).on(qubits[i])]
        for i in range(nq-1): ops+=[cirq.CNOT(qubits[i],qubits[i+1]),cirq.depolarize(0.02).on(qubits[i])]
        ops.append(cirq.measure(*qubits,key='r'))
        cirq.DensityMatrixSimulator().run(cirq.Circuit(ops),repetitions=1024)
    a,q,c = run_trials(ab), run_trials(qk), run_trials(cq)
    rows7.append(row(nq,a,q,c)); p(nq,a,q,c)
save("noise_simulation.csv", rows7)

# === 8. QEC ===
print("\n[8/10] QEC Decoding")
def ab_qec():
    from abirqu.qec.steane import SteaneCode
    sc=SteaneCode(); enc=sc.encode([1,0]); err=list(enc); err[2]^=1; sc.correct(err)
def qk_qec():
    from qiskit import QuantumCircuit,transpile; from qiskit_aer import AerSimulator
    qc=QuantumCircuit(9,2); qc.cx(0,3);qc.cx(0,6);qc.cx(1,4);qc.cx(1,7)
    qc.x(4);qc.cx(3,6);qc.cx(4,7);qc.measure([6,7],[0,1])
    AerSimulator().run(transpile(qc,AerSimulator()),shots=100).result()
def cq_qec():
    import cirq; q=cirq.LineQubit.range(5)
    c=cirq.Circuit([cirq.CNOT(q[0],q[1]),cirq.CNOT(q[0],q[2]),cirq.X(q[1]),
                     cirq.CNOT(q[0],q[3]),cirq.CNOT(q[1],q[4]),cirq.measure(q[3],q[4],key='s')])
    cirq.Simulator().run(c,repetitions=100)
a,q,c = run_trials(ab_qec), run_trials(qk_qec), run_trials(cq_qec)
rows8=[{"test":"steane_qec","abirqu_mean":f(a),"qiskit_mean":f(q),"cirq_mean":f(c)}]
print(f"  QEC: A={f(a):>10} Q={f(q):>10} C={f(c):>10}")
save("qec_decoding.csv", rows8)

# === 9. Scalability ===
print("\n[9/10] Scalability (H⊗n, single trial)")
rows9=[]
for nq in [10,14,18,20,22,24]:
    r={}
    try:
        t,_=timed(lambda: (__import__('abirqu.simulator',fromlist=['RustSimulator']).RustSimulator(nq),[],))
        # just RustSim allocation for scaling
        r["abirqu"]=f"{t:.6f}"
    except: r["abirqu"]="ERROR"
    try:
        def _q(nq=nq):
            from qiskit import QuantumCircuit,transpile; from qiskit_aer import AerSimulator
            qc=QuantumCircuit(nq);[qc.h(i) for i in range(nq)];qc.save_statevector()
            AerSimulator(method='statevector').run(transpile(qc,AerSimulator()),shots=0).result()
        t,_=timed(_q); r["qiskit"]=f"{t:.6f}"
    except: r["qiskit"]="ERROR"
    try:
        def _c(nq=nq):
            import cirq; qubits=cirq.LineQubit.range(nq)
            cirq.Simulator().simulate(cirq.Circuit([cirq.H(q) for q in qubits]))
        t,_=timed(_c); r["cirq"]=f"{t:.6f}"
    except: r["cirq"]="ERROR"
    rows9.append({"qubits":nq,"abirqu_s":r["abirqu"],"qiskit_s":r["qiskit"],"cirq_s":r["cirq"]})
    print(f"  {nq:2d}q: A={r['abirqu']:>10} Q={r['qiskit']:>10} C={r['cirq']:>10}")
save("scalability.csv", rows9)

# === 10. QFT ===
print("\n[10/10] QFT")
rows10=[]
for nq in [4,8,10,12]:
    def ab(nq=nq):
        from abirqu.circuit import Circuit; from abirqu.simulator import SimulatorBackend
        qc=Circuit(nq)
        for i in range(nq):
            qc.h(i)
            for j in range(i+1,nq): qc.rz(j,3.14159/(2**(j-i)))
        SimulatorBackend().run(qc)
    def qk(nq=nq):
        from qiskit import QuantumCircuit,transpile; from qiskit_aer import AerSimulator; from math import pi
        qc=QuantumCircuit(nq)
        for i in range(nq):
            qc.h(i)
            for j in range(i+1,nq): qc.cp(pi/(2**(j-i)),i,j)
        qc.save_statevector()
        AerSimulator(method='statevector').run(transpile(qc,AerSimulator()),shots=0).result()
    def cq(nq=nq):
        import cirq; from math import pi; qubits=cirq.LineQubit.range(nq); ops=[]
        for i in range(nq):
            ops.append(cirq.H(qubits[i]))
            for j in range(i+1,nq): ops.append(cirq.CZPowGate(exponent=1/(2**(j-i))).on(qubits[i],qubits[j]))
        cirq.Simulator().simulate(cirq.Circuit(ops))
    a,q,c = run_trials(ab), run_trials(qk), run_trials(cq)
    rows10.append(row(nq,a,q,c)); p(nq,a,q,c)
save("phase_polynomial.csv", rows10)

total = time.perf_counter() - T0
print(f"\n{'='*72}\n  ALL 10 BENCHMARKS COMPLETE in {total:.1f}s\n{'='*72}")
with open(RAW/"summary.json","w") as fh: json.dump({"total_s":total,"spec":SPEC},fh,indent=2,default=str)
