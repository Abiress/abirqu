<p align="center">
  <img src="assets/logo.png" alt="AbirQu Logo" width="320"/>
</p>

<h1 align="center">AbirQu Quantum SDK v1.0.0</h1>

<p align="center">
  <b>Created by Abir Maheshwari</b> &nbsp;|&nbsp; abhirsxn@gmail.com &nbsp;|&nbsp; <a href="https://aqdi.world">aqdi.world</a> &nbsp;|&nbsp; 🇮🇳 Indian Quantum Mission Support Enabled
</p>

---

## What is AbirQu?

**AbirQu** is a **pedagogical and research-oriented** quantum computing SDK written in pure NumPy. It provides a unified API for quantum circuits, simulation backends, quantum communication protocols, error correction codes, and hardware backends — implemented entirely in Python without Rust or C++ compilation.

**This is not a production-grade quantum SDK.** It is a learning tool and research prototype. The algorithms are simplified implementations designed for understanding quantum computing concepts, not for production workloads or publication-quality results.

### Honest Assessment

| What AbirQu actually is | What it is NOT |
|------------------------|----------------|
| A NumPy-based quantum circuit simulator | A replacement for Qiskit, Cirq, or Braket |
| A learning tool with 200 tutorials | A production quantum computing platform |
| A research prototype with novel algorithms | A validated, peer-reviewed implementation |
| Hardware-agnostic simulator | A verified hardware execution tool |
| Educational chemistry/QEC/communication code | Production-grade molecular simulation |

### Created By

**Abir Maheshwari** at **Artificial Quantum Dyson Intelligence (AQDI)** ([aqdi.world](https://aqdi.world)), built as part of the **Indian Quantum Mission**.

---

## Architecture Overview

See the full architecture diagram: [assets/architecture.md](assets/architecture.md)

**Quick Summary:** AbirQu is organized into **7 layers**:

1. **Quantum IDE/GUI** — Visual circuit editor, Bloch sphere, code editor, themes
2. **Hardware Control** — Calibration, characterization, noise profiling, cloud management
3. **Quantum Error Correction** — Stabilizer/Surface/Color codes, 5 decoders, magic state distillation
4. **Quantum Communication** — BB84, E91, CV-QKD, DI-QKD, satellite, repeaters, network
5. **Novel Contributions** — Noise-adaptive compiler, SPAE, circuit cutting, hybrid simulator
6. **Hardware Backends** — IBM, IonQ, Rigetti, Quantinuum, AWS, Azure, Google, Pasqal, OQC, QuEra, D-Wave, SpinQ
7. **Simulation Engines** — GPU, Clifford, MPS, Monte Carlo, NumPy

**Important:** Most hardware backends are adapter stubs that call vendor SDKs (qiskit, cirq, amazon-braket). They have not been tested against real quantum hardware. Only D-Wave and SpinQ have been verified locally.

---

## What's Inside AbirQu

AbirQu brings together quantum computing algorithms from multiple domains into a single SDK:

| Module | What It Does | Implementation Depth |
|--------|-------------|---------------------|
| **Quantum Chemistry** | Molecular Hamiltonian mapping | Jordan-Wigner, Bravyi-Kitaev, Parity mappers · PySCF hooks · Matchgate tomography — **simplified, not validated against literature** |
| **OSINT & Intelligence** | Graph optimization problems | 6 graph problems → Ising/QUBO (Max-Cut, MIS, MVC, Coloring, Community, Anomaly) · QAOA circuit generation |
| **Cryptanalysis & PQC** | Quantum algorithms for cryptography | Shor factoring circuit · Grover oracle synthesis · Kyber/Dilithium parameter generation — **educational, not cryptographically secure** |
| **Space & Aerospace** | Quantum linear system solvers | HHL algorithm · 2D CFD diffusion solver · Structural stress solver — **toy-scale problems only** |
| **Q-PINN** | Quantum PDE solvers | Parameterized quantum circuits for diffusion and Navier-Stokes equations |
| **Agentic Orchestration** | Task scheduling and execution | Agent task orchestrator · Batch execution · Multi-GPU simulation |

All modules use **pure NumPy with OpenBLAS** — runs on Intel, AMD, Qualcomm, MediaTek, and Apple Silicon without recompilation.

---

## Features

### Core — Unified Execution

| Feature | Module | Description |
|---------|--------|-------------|
| **QuantumRun** | `abirqu.primitives` | One function does sampling + estimation + mitigation + ML |
| **Sampler** | `abirqu.primitives` | Quasi-distribution with entropy, effective shot count, purity metrics |
| **Estimator** | `abirqu.primitives` | Compute expectation values of Pauli operators / matrices |
| **QNN** | `abirqu.primitives` | Quantum neural network with parameter-shift gradients |

### Circuit Library

| Feature | Module | Description |
|---------|--------|-------------|
| **RealAmplitudes** | `abirqu.library` | RY + CNOT parameterized ansatz |
| **EfficientSU2** | `abirqu.library` | RY + RZ + CNOT — more expressive than RealAmplitudes |
| **N-local** | `abirqu.library` | Configurable rotation gates + entanglement patterns |
| **QAOA Circuit** | `abirqu.library` | QAOA ansatz with automatic mixer Hamiltonian |
| **VQE Hardware-Efficient** | `abirqu.library` | EfficientSU2-based VQE ansatz |
| **VQE UCCSD** | `abirqu.library` | Unitary Coupled Cluster Singles and Doubles |
| **Angle Encoding** | `abirqu.library` | 1 qubit per feature, rotation-based |
| **Amplitude Encoding** | `abirqu.library` | log2(n) qubits for n features, tree-based |
| **ZZFeatureMap** | `abirqu.library` | Data-dependent entanglement for quantum kernels |
| **GHZ State** | `abirqu.library` | (|00...0⟩ + |11...1⟩) / √2 |
| **W State** | `abirqu.library` | Equal superposition of single-excitation states |
| **QFT** | `abirqu.library` | Quantum Fourier Transform |
| **Grover Search** | `abirqu.library` | Full Grover circuit with oracle + diffusion |
| **Bernstein-Vazirani** | `abirqu.library` | BV algorithm circuit |
| **Random Circuit** | `abirqu.library` | Random benchmark circuits with configurable seed |

### Visualization

| Feature | Module | Description |
|---------|--------|-------------|
| **CircuitDrawer** | `abirqu.visualization` | text, ASCII, SVG, HTML output with gate coloring |
| **BlochSphere** | `abirqu.visualization` | Multi-qubit partial trace, 3D projection |
| **histogram_text/svg** | `abirqu.visualization` | Measurement result bar charts |
| **stateplot_svg** | `abirqu.visualization` | Phase-colored amplitude bars |
| **Noise Fingerprint** | `abirqu.visualization` | Spectral visualization of noise models |
| **Circuit Fingerprint** | `abirqu.visualization` | Barcode-like circuit structure visualization |

### Simulation Backends

| Backend | Module | Description |
|---------|--------|-------------|
| **GPU Simulator** | `abirqu.simulation` | CuPy/NumPy statevector with GPU acceleration |
| **Clifford Simulator** | `abirqu.simulation` | Stabilizer tableau for Clifford circuits |
| **MPS Simulator** | `abirqu.simulation` | Matrix Product State / tensor network simulation |
| **Monte Carlo Simulator** | `abirqu.simulation` | Quantum Jumps — stochastic pure-state trajectories |
| **NumPy Simulator** | `abirqu.numpy_sim` | Pure Python/NumPy statevector (portable fallback) |

### Hardware Backends

| Backend | Type | Status | Notes |
|---------|------|--------|-------|
| **D-Wave** | Quantum Annealer | ✅ Verified | QUBO builder, simulated annealing, hybrid solver |
| **SpinQ** | Trapped Ion | ✅ Verified | SQaaS REST API, native gate transpiler |
| **IBM Quantum** | Superconducting | ⚠️ SDK-wired | Adapter using qiskit-ibm-runtime |
| **AWS Braket** | Multi-hardware | ⚠️ SDK-wired | Adapter using amazon-braket |
| **Azure Quantum** | Multi-hardware | ⚠️ SDK-wired | Adapter using azure-quantum |
| **Google Quantum** | Superconducting | ⚠️ SDK-wired | Adapter using cirq |
| **IonQ** | Trapped Ion | ⚠️ SDK-wired | Adapter code exists |
| **Rigetti** | Superconducting | ⚠️ SDK-wired | Adapter code exists |
| **Quantinuum** | Trapped Ion | ⚠️ SDK-wired | Adapter code exists |
| **Pasqal** | Neutral Atom | ⚠️ SDK-wired | Adapter code exists |
| **OQC** | Superconducting | ⚠️ SDK-wired | Adapter code exists |
| **QuEra** | Neutral Atom | ⚠️ SDK-wired | Adapter code exists |

**Note:** "SDK-wired" means adapter code exists that calls the vendor's SDK. These have NOT been tested against real quantum hardware. D-Wave and SpinQ are verified against simulated/real environments.

### Quantum Error Correction

| Code Family | Codes | Implementation |
|------------|-------|---------------|
| **Stabilizer** | Repetition, BitFlip, PhaseFlip | Basic [[n,1,d]] codes |
| **Shor Code** | [[9,1,3]] | First QEC code |
| **Steane Code** | [[7,1,3]] | CSS code, transversal Clifford |
| **Surface Code** | Rotated, distance 3/5/7 | Threshold ~1% |
| **Color Code** | Triangular lattice | Transversal Clifford group |
| **LDPC** | Parity-check matrix | Configurable |

**5 Decoders:** Syndrome Lookup, Surface Code, Belief Propagation, MWPM, GPU-Accelerated

**Magic State Distillation:** 15-to-1 T-state distiller, 20-to-4 H-state distiller

### Quantum Communication

7 quantum communication protocols:

| Protocol | Type | Implementation |
|---------|------|---------------|
| **BB84** | QKD | First quantum key distribution |
| **E91** | QKD | CHSH inequality S = 2√2 violation |
| **CV-QKD** | QKD | Gaussian modulation, continuous variables |
| **DI-QKD** | QKD | Device-independent, no trust in hardware |
| **Satellite QKD** | QKD | Free-space loss model, atmospheric effects |
| **Repeater Chains** | Networking | DEJMPS purification, entanglement swapping |
| **Quantum Network** | Networking | Star/ring/mesh topologies, routing |

### Quantum OS

| Feature | Module | Description |
|---------|--------|-------------|
| **QuantumScheduler** | `abirqu.quantum_os` | FIFO, priority, SJF, fair-share scheduling |
| **JobQueue** | `abirqu.quantum_os` | SQLite-backed persistent job queue |
| **ResourceManager** | `abirqu.quantum_os` | Qubit allocation, utilization tracking |
| **CostEstimator** | `abirqu.quantum_os` | Per-provider cost estimation |

### Post-Quantum Security (AbirGuard)

| Feature | Module | Description |
|---------|--------|-------------|
| **Kyber-768 KEM** | `abirqu.cloud.abir_guard` | Key encapsulation mechanism — **simplified, not cryptographically secure** |
| **Dilithium-2** | `abirqu.cloud.abir_guard` | Lattice-based digital signatures — **simplified, not cryptographically secure** |
| **SPHINCS+-128f** | `abirqu.cloud.abir_guard` | Hash-based signatures (stateless) |

### Novel Contributions

These are algorithms developed specifically for AbirQu:

#### 1. Noise-Adaptive Circuit Compiler (`abirqu.optimize.noise_adaptive`)

A 4-pass compiler that optimizes circuits for specific hardware noise profiles:
- **Pass 1: Matroid Partitioning** — maps qubits to physical locations weighted by noise
- **Pass 2: CNOT Reordering** — minimizes total noise cost across CNOT operations
- **Pass 3: Gate Elimination** — identity detection and commutation-based removal
- **Pass 4: Fidelity Estimation** — multiplicative model across all gate errors

#### 2. SPAE: Stochastic-Phase Amplitude Encoding (`abirqu.qnlp.spae`)

A noise-native encoding for quantum NLP that uses only Clifford operations (X + CNOT gates).

#### 3. Entanglement-Aware Circuit Cutting (`abirqu.entanglement_cutting`)

Splits large circuits into smaller subcircuits for distributed execution using bond dimension analysis.

#### 4. Hybrid MPS-Clifford Simulator (`abirqu.simulation.hybrid`)

Dynamically switches between MPS and Clifford simulation based on circuit structure.

### Language Bindings

| Language | Status | Notes |
|----------|--------|-------|
| **Python** | ✅ Complete | Primary SDK, full feature set |
| **Go** | ⚠️ Stub | cgo bindings to Rust shared library |
| **Java** | ⚠️ Stub | JNA bindings to Rust shared library |
| **.NET** | ⚠️ Stub | P/Invoke bindings to Rust shared library |
| **Swift** | ⚠️ Stub | ctypes bindings to Rust shared library |
| **Kotlin** | ⚠️ Stub | JNA bindings to Rust shared library |
| **WebAssembly** | ❌ Planned | Not implemented |

**Note:** Non-Python bindings are stubs that call a Rust shared library (`libabirqu_core.so`). They are not tested or verified.

---

## Installation

**Note:** AbirQu is not yet published on PyPI. Install from source only.

```bash
git clone https://github.com/Abiress/abirqu.git
cd abirqu
pip install -e .
```

### System Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| **Python** | 3.8+ | 3.10+ |
| **NumPy** | 1.20+ | 1.24+ |
| **RAM** | 4 GB | 16 GB+ |
| **OS** | Linux, macOS, Windows | Linux (best OpenBLAS support) |

### Verify Installation

```python
import abirqu
print(f"AbirQu version: {abirqu.__version__}")

from abirqu import Circuit
from abirqu.primitives import QuantumRun

circuit = Circuit(2)
circuit.h(0)
circuit.cnot(0, 1)
circuit.measure([0, 1])

result = QuantumRun(circuit, shots=1000)
print(f"Bell state counts: {result.counts}")
```

---

## Quick Start

### Basic Circuit

```python
from abirqu import Circuit, H, X, CNOT, Measure
from abirqu.primitives import QuantumRun

# Create a Bell state
circuit = Circuit(2)
circuit.h(0)
circuit.cnot(0, 1)
circuit.measure([0, 1])

result = QuantumRun(circuit, shots=1000)
print(result.counts)  # {'00': ~500, '11': ~500}
```

### Grover's Algorithm

```python
from abirqu import Circuit, H, X, CNOT, Measure
from abirqu.primitives import QuantumRun
import math

n = 3
circuit = Circuit(n)

# Initialize superposition
for i in range(n):
    circuit.h(i)

# Oracle (mark |101>)
circuit.x(1)
circuit.cnot(0, 2)
circuit.cnot(1, 2)
circuit.x(1)

# Diffusion
for i in range(n):
    circuit.h(i)
    circuit.x(i)
circuit.cnot(0, 1)
circuit.cnot(1, 2)
for i in range(n):
    circuit.x(i)
    circuit.h(i)

circuit.measure(list(range(n)))
result = QuantumRun(circuit, shots=1000)
print(result.counts)
```

### Quantum Chemistry (Simplified)

```python
from abirqu.chemistry import MolecularData, JWMapper

# Create a simple H2 molecule representation
mol = MolecularData(
    num_orbitals=2,
    num_electrons=2,
    h1=[[0, 0], [0, 0]],
    h2=[[[0, 0], [0, 0]], [[0, 0], [0, 0]]],
    nuclear_repulsion=0.5
)

# Map to qubit Hamiltonian using Jordan-Wigner
mapper = JWMapper(mol)
qubit_hamiltonian = mapper.map()
print(f"Qubit Hamiltonian terms: {len(qubit_hamiltonian.terms)}")
```

### Quantum Communication

```python
from abirqu.quantum_communication import BB84

# Run BB84 key exchange
bb84 = BB84(num_qubits=10)
result = bb84.run()
print(f"Key bits: {result.key_bits}")
print(f"QBER: {result.qber:.3f}")
```

---

## 200 Tutorials

AbirQu includes **200 tutorials** covering quantum computing from basics to advanced applications:

| Category | Tutorials | Topics |
|----------|-----------|--------|
| Fundamentals | 1-10 | Superposition, entanglement, QFT, QPE, Grover, Shor, VQE |
| Algorithms | 11-20 | QAOA, HHL, quantum walk, amplitude estimation, QNN |
| Machine Learning | 21-30 | Quantum RL, GANs, PCA, clustering, anomaly detection |
| Chemistry & Info | 31-40 | Error mitigation, benchmarking, QRAM, molecular simulation |
| Advanced | 41-50 | Surface codes, fault-tolerant circuits, compilers, sensing |
| Expert | 51-100 | Spin chains, chaos, advanced optimization, QML |
| Cutting-Edge | 111-120 | Novel algorithms, research frontiers |
| Domain Apps | 121-150 | Medical, defense, finance, supply chain, agriculture |
| Industry | 151-170 | Manufacturing, retail, aerospace, telecom, energy |
| Business | 171-200 | R&D, IP, M&A, Web3, DevOps, ML Ops |

**Full index:** [tutorials/INDEX.md](tutorials/INDEX.md)

**Beginner Guide:** [abirqu/docs/beginner_guide.md](abirqu/docs/beginner_guide.md)

---

## Test Results

```
Platform:   x86_64 | Python 3.14.4 | NumPy 2.4.4
OpenBLAS:   DYNAMIC_ARCH (Haswell) — Intel/AMD compatible
CPU:        20 cores | 30.6 GB RAM

Total:      412 tests passing, 5 warnings
```

The tests verify that modules run without errors. They do NOT verify correctness against literature values or real hardware. For example:
- Chemistry tests verify mappers run, not that energies match exact diagonalization
- QEC tests verify encoding/decoding runs, not that error rates match theoretical thresholds
- Communication tests verify protocols run, not that key rates match theoretical bounds

---

## Version History

| Version | Date | Key Additions |
|---------|------|---------------|
| **v0.1.0** | 2026-04 | Initial release — Rust simulator, density matrix, QEC, 12 hardware backends |
| **v0.2.0** | 2026-05 | Quantum OS, PQC security, simulation backends |
| **v0.3.0** | 2026-06 | QuantumRun primitives, QNN, domain modules |
| **v0.4.0** | 2026-07 | Novel contributions (noise-adaptive compiler, SPAE, circuit cutting, hybrid sim) |
| **v0.5.0** | 2026-07 | Pauli string optimizer, state tomography, randomized benchmarking |
| **v0.6.0** | 2026-07 | Quantum Communication — 7 protocols |
| **v0.7.0** | 2026-07 | Fault-Tolerant QEC — stabilizer/surface/color codes, 5 decoders |
| **v0.8.0** | 2026-07 | Full Quantum IDE/GUI |
| **v0.9.0** | 2026-07 | Quantum Communication (enhanced) |
| **v1.0.0** | 2026-07 | Full Stack + Hardware Control — calibration, characterization, noise profiling |

---

## What's Missing

This section honestly lists what AbirQu does NOT have:

- **No validated algorithms** — implementations are simplified for learning, not publication-quality
- **No real hardware execution** — only D-Wave and SpinQ adapters are verified
- **No PyPI package** — install from source only
- **No CI/CD pipeline** — no automated testing on real hardware
- **No peer review** — no independent validation of results
- **No production-grade QEC** — simplified decoders, no fault-tolerant threshold analysis
- **No production chemistry** — simplified mappers, no VQE/VQD convergence validation
- **No real cryptanalysis** — simplified Shor/Grover, not cryptographically secure
- **No WebAssembly** — planned, not implemented
- **Non-Python SDKs** — stubs only, not tested

---

## How This Compares

**Use AbirQu if:**
- You want to learn quantum computing concepts
- You need a single SDK for educational purposes
- You want to experiment with quantum algorithms in pure Python
- You're building a teaching curriculum

**Don't use AbirQu if:**
- You need production-grade quantum simulation (use Qiskit, Cirq, PennyLane)
- You need real hardware execution (use IBM Quantum, AWS Braket, Google Quantum)
- You need validated chemical simulations (use PySCF, OpenFermion)
- You need cryptographically secure PQC (use liboqs, pqcrypto)
- You need peer-reviewed algorithms for research

---

## License

MIT License — see [LICENSE](LICENSE)

**Built with** Python, NumPy, SciPy, Rust

---

**© 2026 Abir Maheshwari — [Artificial Quantum Dyson Intelligence](https://aqdi.world), Biro Labs, Aquilldriver**

🇮🇳 Built in India, for the World.
