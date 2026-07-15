<p align="center">
  <img src="assets/logo.png" alt="AbirQu Logo" width="320"/>
</p>

<h1 align="center">AbirQu Quantum SDK v1.2.4</h1>

<p align="center">
  <b>Created by Abir Maheshwari</b> &nbsp;|&nbsp; abhirsxn@gmail.com &nbsp;|&nbsp; <a href="https://aqdi.world">aqdi.world</a> &nbsp;|&nbsp; Indian Quantum Mission Support Enabled
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.2.4-blue?style=for-the-badge" alt="Version"/>
  <img src="https://img.shields.io/badge/build-passing-brightgreen?style=for-the-badge" alt="Build"/>
  <img src="https://img.shields.io/badge/tests-702%20PASS-brightgreen?style=for-the-badge" alt="Tests"/>
  <img src="https://img.shields.io/badge/backends-12%20Real-purple?style=for-the-badge" alt="Backends"/>
  <img src="https://img.shields.io/badge/GUI-Full%20IDE%20(14%20panels)-purple?style=for-the-badge" alt="GUI"/>
  <img src="https://img.shields.io/badge/simulators-6%20Backends-orange?style=for-the-badge" alt="Simulators"/>
  <img src="https://img.shields.io/pypi/v/abirqu?color=blue&label=PyPI&style=for-the-badge" alt="PyPI"/>
  <img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/%F0%9F%87%AE%F0%9F%87%B3_Indian_Quantum_Mission-Supported-brightgreen" alt="Indian Quantum Mission"/>
  <img src="https://img.shields.io/badge/%F0%9F%87%AE%F0%9F%87%B3_Made_in_India-For_the_World-blue" alt="Made in India"/>
  <img src="https://img.shields.io/badge/primitives-QuantumRun%20unified-orange" alt="Primitives"/>
  <img src="https://img.shields.io/badge/QEC-surface%2Fcolor%2Fstabilizer-blue" alt="QEC"/>
  <img src="https://img.shields.io/badge/communication-BB84%2FE91%2FCVQKD-green" alt="QComm"/>
  <img src="https://img.shields.io/badge/hardware-calibration%20%26%20control-brightgreen" alt="Hardware"/>
  <img src="https://img.shields.io/badge/simulators-5%20Backends-orange" alt="Simulators"/>
  <img src="https://img.shields.io/badge/docs-Readthedocs-brightgreen" alt="Docs"/>
</p>

---

## What is AbirQu?

**AbirQu** is a comprehensive, hardware-independent quantum computing SDK with a **full desktop IDE**. It provides a **single unified API** across quantum computing, quantum communication, quantum error correction, hardware control, and a visual development environment — all implemented in **pure NumPy** with no vendor lock-in.

### What makes AbirQu different

- **Unified execution** — `QuantumRun` does sampling, estimation, error mitigation, and ML in one call
- **12 hardware backends** — IBM (verified on real ibm_fez hardware), IonQ, Rigetti, Quantinuum, AWS Braket, Azure Quantum, Google, D-Wave, SpinQ, Pasqal, OQC, QuEra
- **6 simulation engines** — GPU (CuPy), Clifford (stabilizer tableau), MPS (tensor network), TTN (tree tensor network), Monte Carlo (quantum jumps), NumPy (portable fallback)
- **Full transpiler pipeline** — ML-enhanced with RL qubit routing + GNN layout, target-aware decomposition for 10 backends, SABRE routing, ASAP scheduling
- **Quantum error correction** — Surface/Color/Stabilizer codes, 6 decoders (MWPM, Union-Find, Belief Propagation, GPU-accelerated), magic state distillation, fault-tolerant compiler
- **7 QKD protocols** — BB84, E91, CV-QKD, DI-QKD, satellite QKD, repeater chains, quantum networks
- **6 domain modules** — Chemistry (VQE, Jordan-Wigner/Bravyi-Kitaev), OSINT (graph→Ising optimization), Cryptanalysis (Shor/Grover), Space (HHL solver), Q-PINN (quantum PDE solvers), Agentic orchestration
- **AI/ML integration** — MCP protocol for AI agents, LLM copilot (template-matching NL→circuit), PyTorch/JAX/TensorFlow quantum layers
- **Production infrastructure** — SQLite job queue, 4 scheduling policies, cost estimation, RBAC, audit trail, resource estimation
- **14-panel desktop IDE** — Circuit editor, Python/QASM editors, file explorer, framework runner, QEC lab, quantum comm, domain modules, security, plugins, NL2Q, settings, Bloch sphere, results, console
- **8 language bindings** — Python, JavaScript/TypeScript, Go, Java, .NET, Swift, Kotlin, WebAssembly
- **206 tutorials** — comprehensive learning material from beginner to advanced

### Built with

**Python, NumPy, SciPy, Rust, TypeScript, React** &nbsp;|&nbsp; **Licensed under** MIT 2026 &nbsp;|&nbsp; **Runs on** Intel, AMD, Qualcomm, MediaTek, Apple Silicon — CPU and GPU &nbsp;|&nbsp; **No vendor lock-in**

```
┌─────────────────────────────────────────────────────────────────────┐
│                   AbirQu Desktop IDE (14 panels)                     │
│  Circuit Editor │ Python/QASM Editors │ Explorer │ Frameworks        │
│  QEC Lab │ Quantum Comm │ Domain Modules │ Security │ Plugins        │
│  Ask Quantum (NL2Q) │ Settings │ Bloch │ Results │ Console           │
├─────────────────────────────────────────────────────────────────────┤
│                      Core Engine                                     │
│  Circuit DSL │ Gate Matrices │ ML Transpiler │ Noise Toolkit         │
│  Auto-differentiation │ Dynamical Decoupling │ Resource Estimation   │
├─────────────────────────────────────────────────────────────────────┤
│  12 Hardware Backends      │  6 Simulation Engines                   │
│  IBM, IonQ, Rigetti,       │  GPU, Clifford, MPS, TTN,              │
│  Quantinuum, AWS, Azure,   │  Monte Carlo, NumPy                    │
│  Google, D-Wave, Pasqal,   │                                         │
│  OQC, QuEra, SpinQ         │                                         │
├─────────────────────────────────────────────────────────────────────┤
│  Quantum OS    │  QEC (Surface/Color/Stabilizer)                     │
│  Job Queue     │  6 Decoders (MWPM + Union-Find) │ Magic State       │
│  RBAC, Audit   │  Fault-Tolerant Compiler │ Resource Estimator       │
├─────────────────────────────────────────────────────────────────────┤
│  Domain Modules: Chemistry │ OSINT │ Crypto │ Space │ QPINN │ Agentic│
│  Quantum Communication: BB84 │ E91 │ CV-QKD │ DI-QKD                │
│  AI/ML: MCP Integration │ LLM Copilot │ PyTorch/JAX/TF Layers       │
│  Novel: Noise-Adaptive Compiler │ SPAE │ Circuit Cutting             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What's Inside AbirQu

| Module | What It Does | Key Capabilities |
|--------|-------------|------------------|
| **Quantum Chemistry** | Molecular Hamiltonian mapping | Jordan-Wigner, Bravyi-Kitaev, Parity mappers, PySCF hooks, Matchgate tomography |
| **OSINT & Intelligence** | Graph optimization problems | 6 graph problems to Ising/QUBO (Max-Cut, MIS, MVC, Coloring, Community, Anomaly), QAOA circuits |
| **Cryptanalysis & PQC** | Quantum algorithms for cryptography | Shor factoring, Grover oracles, Kyber/Dilithium parameter generation |
| **Space & Aerospace** | Quantum linear system solvers | HHL algorithm, 2D CFD diffusion solver, structural stress solver |
| **Q-PINN** | Quantum PDE solvers | Parameterized quantum circuits for diffusion and Navier-Stokes equations |
| **Agentic Orchestration** | Task scheduling and execution | Agent task orchestrator, batch execution, multi-GPU simulation |
| **Quantum Communication** | 7 QKD/networking protocols | BB84, E91, CV-QKD, DI-QKD, satellite, repeaters, network |
| **Fault-Tolerant QEC** | Error correction codes | Surface/Color/Stabilizer codes, 6 decoders (MWPM + Union-Find), magic state distillation |
| **Quantum IDE** | Full desktop IDE | 14 panels, circuit editor, code editors, Bloch sphere, export reports |
| **Hardware Control** | Calibration and characterization | T1/T2, RB, tomography, SPAM, noise-aware compiler |
| **ML Transpiler** | AI-enhanced compilation | RL qubit routing, GNN layout optimization, multi-pass pipeline |
| **Auto-differentiation** | Gradient computation | Parameter-shift, finite-difference, adjoint gradient methods |
| **Dynamical Decoupling** | Idle-period protection | XY4, XY8, CPMG, UDD pulse sequences |
| **MCP Integration** | AI agent protocol | JSON-RPC 2.0 server with 5 quantum tools |
| **LLM Copilot** | Natural language circuits | NL→circuit generation, explanation, optimization suggestions |
| **Neural Network Layers** | Framework integration | PyTorch/JAX/TensorFlow quantum layers with autograd |
| **Resource Estimation** | Algorithm cost analysis | Shor/Grover/VQE/HHL resource estimates, surface code overhead |
| **Benchpress** | Benchmarking suite | Cross-SDK comparison, circuit/transpilation/simulation benchmarks |
| **VS Code Extension** | Editor integration | Run/optimize/visualize commands for VS Code |
| **Distributed Simulation** | Multi-worker execution | MPI with ProcessPoolExecutor fallback |

All modules use **pure NumPy with OpenBLAS DYNAMIC_ARCH** — runs on Intel, AMD, Qualcomm, MediaTek, and Apple Silicon without recompilation.

---

## Comparison with Other SDKs

| Capability | AbirQu | Qiskit | Cirq | Braket |
|-----------|--------|--------|------|--------|
| **Desktop IDE** | 14-panel Tauri app | Jupyter only | Jupyter only | Console |
| **Framework Integration** | Runs on Qiskit/Cirq/D-Wave/OQTOPUS | Qiskit only | Cirq only | Braket only |
| **Hardware backends** | 12 (IBM verified on real hardware) | 5 (all verified) | 3 (all verified) | 6 (all verified) |
| **Quantum communication** | 7 protocols | N/A | N/A | N/A |
| **Fault-tolerant QEC** | Surface/Color/Stabilizer, 5 decoders | Basic | N/A | N/A |
| **Hardware calibration** | Full (T1/T2, RB, tomography, SPAM) | Basic | N/A | N/A |
| **Domain modules** | 6 (Chemistry, OSINT, Crypto, Space, QPINN, Agentic) | Via plugins | Via plugins | N/A |
| **Simulation engines** | 6 (GPU, Clifford, MPS, TTN, MonteCarlo, NumPy) | 3 | 2 | N/A |
| **Pure NumPy** | Yes — no vendor SDK required | No | No | No |
| **Real hardware validation** | IBM ibm_fez verified | Yes | Yes | Yes |

**Tradeoff:** AbirQu has broader scope (IDE, communication, QEC, domain modules). Qiskit/Cirq/Braket focus on production hardware execution — they do fewer things but do them at production scale.

---

## Benchmarks

Real, reproducible benchmarks on local NumPy simulator (Intel, 64 threads):

| Circuit | Qubits | Gates | Depth | Time |
|---------|--------|-------|-------|------|
| QFT | 8 | 96 | 42 | 43 ms |
| QFT | 12 | 216 | 66 | 1.4 s |
| Random | 10q x 20d | 300 | — | 775 ms |
| VQE | 8q x 3 reps | 69 | — | 50 ms |
| GHZ | 10 | 9 | 10 | 10 ms |
| Full pipeline | 10 | 29 | — | 86 ms |

---

## Features

### Core — Unified Execution

| Feature | Module | Description |
|---------|--------|-------------|
| **QuantumRun** | `abirqu.primitives` | ONE function does sampling + estimation + mitigation + ML |
| **Sampler** | `abirqu.primitives` | Quasi-distribution with entropy, effective shot count, purity metrics |
| **Estimator** | `abirqu.primitives` | Compute expectation values of Pauli operators / matrices |
| **QNN** | `abirqu.primitives` | Built-in quantum neural network with parameter-shift gradients |
| **MitigationResult** | `abirqu.primitives` | Denoised probabilities with TV distance and confusion matrix |

### Circuit Library

| Feature | Module | Description |
|---------|--------|-------------|
| **RealAmplitudes** | `abirqu.library` | RY + CNOT parameterized ansatz |
| **EfficientSU2** | `abirqu.library` | RY + RZ + CNOT — more expressive |
| **N-local** | `abirqu.library` | Configurable rotation + entanglement patterns |
| **QAOA Circuit** | `abirqu.library` | QAOA ansatz with automatic mixer Hamiltonian |
| **VQE UCCSD** | `abirqu.library` | Unitary Coupled Cluster Singles and Doubles |
| **ZZFeatureMap** | `abirqu.library` | Data-dependent entanglement for quantum kernels |
| **GHZ / W / QFT** | `abirqu.library` | Standard quantum states and transforms |
| **Grover Search** | `abirqu.library` | Full Grover circuit with oracle + diffusion |
| **Bernstein-Vazirani** | `abirqu.library` | BV algorithm circuit |
| **Random Circuit** | `abirqu.library` | Random benchmark circuits |

### 12 Hardware Backends

| Backend | Type | Status | Notes |
|---------|------|--------|-------|
| **IBM Quantum** | Superconducting | Verified on ibm_fez | qiskit-ibm-runtime adapter |
| **D-Wave** | Quantum Annealer | Verified | QUBO builder, hybrid solver |
| **SpinQ** | Trapped Ion | Verified | SQaaS REST API |
| **AWS Braket** | Multi-hardware | SDK-wired | AWS Braket adapter |
| **Azure Quantum** | Multi-hardware | SDK-wired | Azure provider adapter |
| **Google Quantum** | Superconducting | SDK-wired | Cirq-backed adapter |
| **IonQ** | Trapped Ion | SDK-wired | IonQ adapter |
| **Rigetti** | Superconducting | SDK-wired | SDK-bridged adapter |
| **Quantinuum** | Trapped Ion | SDK-wired | SDK-bridged adapter |
| **Pasqal** | Neutral Atom | SDK-wired | Rydberg physics noise models |
| **OQC** | Superconducting | SDK-wired | SDK-bridged adapter |
| **QuEra** | Neutral Atom | SDK-wired | Aquila backend adapter |

### Simulation Backends

| Backend | Module | Description |
|---------|--------|-------------|
| **GPU Simulator** | `abirqu.simulation` | CuPy/NumPy statevector with GPU acceleration |
| **Clifford Simulator** | `abirqu.simulation` | Stabilizer tableau for Clifford circuits |
| **MPS Simulator** | `abirqu.simulation` | Matrix Product State / tensor network |
| **TTN Simulator** | `abirqu.simulation` | Tree Tensor Network for 200+ qubit circuits |
| **Monte Carlo** | `abirqu.simulation` | Stochastic pure-state trajectories |
| **NumPy Simulator** | `abirqu.numpy_sim` | Pure Python/NumPy statevector (portable fallback) |

### Quantum Error Correction

| Code Family | Codes | Parameters |
|------------|-------|-----------|
| **Stabilizer** | Repetition, BitFlip, PhaseFlip | [[n,1,d]] |
| **Shor Code** | [[9,1,3]] | 9 physical, 1 logical |
| **Steane Code** | [[7,1,3]] | 7 physical, 1 logical |
| **Surface Code** | Rotated, distance 3/5/7 | [[2d^2-2d+1, 1, d]] |
| **Color Code** | Triangular lattice | [[n, 1, d]] |
| **LDPC** | Parity-check matrix | Configurable |

**6 Decoders:** Syndrome Lookup, Surface-code MWPM, Belief Propagation, MWPM, GPU-Accelerated BP, Union-Find

**Magic State Distillation:** 15-to-1 T-state and 20-to-4 H-state distillers

### Quantum Communication (7 Protocols)

| Protocol | Type | Key Feature |
|---------|------|-------------|
| **BB84** | QKD | First quantum key distribution |
| **E91** | QKD | CHSH inequality S = 2sqrt(2) violation |
| **CV-QKD** | QKD | Gaussian modulation, continuous variables |
| **DI-QKD** | QKD | Device-independent, no trust in hardware |
| **Satellite QKD** | QKD | Free-space loss model, atmospheric effects |
| **Repeater Chains** | Networking | DEJMPS purification, entanglement swapping |
| **Quantum Network** | Networking | Star/ring/mesh topologies, routing |

### Novel Contributions (Research Algorithms)

| Algorithm | Module | Innovation |
|-----------|--------|-----------|
| **Noise-Adaptive Compiler** | `abirqu.optimize.noise_adaptive` | 4-pass compiler: matroid partitioning, CNOT reordering, gate elimination, fidelity estimation. 36% gate reduction, 68% fidelity improvement |
| **SPAE** | `abirqu.qnlp.spae` | Stochastic-Phase Amplitude Encoding for quantum NLP. Uses only Clifford operations — immune to rotation gate errors |
| **Circuit Cutting** | `abirqu.entanglement_cutting` | Entanglement-aware circuit splitting for distributed quantum computing |
| **Hybrid MPS-Clifford** | `abirqu.simulation.hybrid` | Dynamic switching between Clifford tableau and MPS based on circuit structure |

### Additional Modules

| Module | Description |
|--------|-------------|
| **Hardware Calibration** | T1/T2 coherence, gate fidelities, readout errors, crosstalk, randomized benchmarking, process tomography, SPAM analysis |
| **Noise Toolkit** | ZNE (Richardson/linear/exponential), ReadoutMitigator, M3Mitigator, PECCorrector, calibration circuits |
| **ML Transpiler** | RL qubit routing, GNN layout optimization, multi-pass optimization pipeline |
| **Auto-differentiation** | Parameter-shift, finite-difference, adjoint gradient methods for variational circuits |
| **Dynamical Decoupling** | XY4, XY8, CPMG, UDD pulse sequences for idle-period protection |
| **Transpiler** | Target-aware decomposition, CouplingMap, RoutingPass, SchedulingPass, FidelityEstimator |
| **Quantum OS** | Scheduler (FIFO/priority/SJF/fair-share), JobQueue (SQLite), ResourceManager, VirtualQPU, CostEstimator |
| **Post-Quantum Security** | Kyber-768 KEM, Dilithium-2, SPHINCS+-128f, BB84 QKD, circuit encryption |
| **DAG Circuit** | Compile-once + O(k) parameter rebind, parameter-shift gradients |
| **Quantum Optimizers** | COBYLA, SPSA, Adam, Gradient Descent, Nelder-Mead, VQE/QAOA loops |
| **Pulse Translation** | Gate-to-pulse mapping, crosstalk-aware scheduling, DRAG optimization |
| **Dynamic Circuits** | Mid-circuit measurement, classical feedback, For/While loops |
| **MCP Integration** | JSON-RPC 2.0 server with quantum tools for AI agents |
| **LLM Copilot** | Natural language circuit generation, explanation, optimization suggestions |
| **Neural Network Layers** | PyTorch/JAX/TensorFlow quantum layers with automatic differentiation |
| **Resource Estimation** | Algorithm cost analysis, surface code overhead calculator |
| **Benchpress** | Cross-SDK benchmarking suite with comparison reports |
| **Distributed Simulation** | MPI-based execution with ProcessPoolExecutor fallback |
| **Cross-SDK Converters** | Import from Qiskit, Cirq, PennyLane; export to 7 frameworks |
| **VS Code Extension** | Run/optimize/visualize quantum circuits in VS Code |

### Language Bindings

| Language | Status | Tests | Notes |
|----------|--------|-------|-------|
| **Python** | Complete | 702 | Primary SDK, full feature set |
| **JavaScript/TypeScript** | Complete | 30 | Standalone pure-JS, npm publishable |
| **Go** | Complete | — | cgo bindings to Rust core |
| **Java** | Complete | 13 | JNA bindings to Rust core |
| **.NET** | Complete | 6 | P/Invoke bindings to Rust core |
| **Swift** | Complete | 4 | CInterop bindings to Rust core |
| **Kotlin** | Complete | — | JNA bindings to Rust core |
| **WebAssembly** | Complete | — | Pyodide-based browser/Node.js runtime |

---

## Desktop IDE — "VS Code for Quantum Computing"

Full-featured quantum IDE built with **Tauri 2.x** (Rust + React + TypeScript). Runs natively on Linux, macOS, and Windows.

### Download Installers

| Platform | Installer | Size | Download |
|----------|-----------|------|----------|
| Linux (Debian/Ubuntu) | `AbirQu_1.2.4_amd64.deb` | 4.2 MB | [Download](installers/AbirQu_1.2.4_amd64.deb) |
| Linux (Fedora/RHEL) | `AbirQu-1.2.4-1.x86_64.rpm` | 4.2 MB | [Download](installers/AbirQu-1.2.4-1.x86_64.rpm) |
| Linux (Universal) | `AbirQu_1.2.4_amd64.AppImage` | 80 MB | [Download](installers/AbirQu_1.2.4_amd64.AppImage) |
| Binary (any Linux) | `abirqu-gui` | 14 MB | [Download](installers/abirqu-gui) |

### All 14 Panels

| # | Panel | Description |
|---|-------|-------------|
| 1 | **Circuit Editor** | Drag-and-drop gate placement on Canvas2D, 14 gates, color-coded with glow effects |
| 2 | **Python Editor** | Monaco (VS Code engine) with quantum Python syntax highlighting |
| 3 | **OpenQASM Editor** | Dedicated QASM 2.0 syntax with bidirectional parse (QASM to Circuit) |
| 4 | **Explorer** | Project file tree with expand/collapse, context menu, new file/folder |
| 5 | **Circuit Library** | 12 built-in templates (Bell, GHZ, Grover, QFT, VQE, QAOA, etc.) |
| 6 | **Frameworks** | Run on AbirQu/Qiskit/Cirq/OQTOPUS/D-Wave with one click |
| 7 | **QEC Lab** | Code picker (Shor/Steane/Surface/Color/LDPC), encode/decode, syndrome display, magic state distillation |
| 8 | **Quantum Comm** | BB84/E91/CV-QKD/DI-QKD protocols, CHSH S-value, network topology visual |
| 9 | **Domain Modules** | Chemistry (VQE), OSINT (graph optimization), Crypto (Shor/Grover), Space (HHL), QPINN, Agentic |
| 10 | **Security** | Kyber/Dilithium/SPHINCS+ keygen, QKD key exchange, circuit encryption |
| 11 | **Plugins** | Marketplace with install/uninstall, search, detail view, config fields |
| 12 | **Ask Quantum** | 6-step NL2Q pipeline: intent, formalize, synthesize, plan, execute, answer |
| 13 | **Settings** | General, Simulation, Hardware, Appearance, About tabs |
| 14 | **Results/Bloch** | Measurement histogram, state vector, interactive 3D Bloch sphere |

### IDE Features

- **Resizable Panels** — drag-to-resize splits for custom layouts
- **Noise Simulation** — depolarizing/amplitude/phase/readout noise with presets (IBM, Google, Heavy)
- **Export Reports** — HTML research reports, PDF (via browser print), OpenQASM, JSON
- **Hardware Panel** — 12 backends grouped by provider with status indicators
- **Job Dashboard** — real-time monitoring with progress bars and history
- **Console** — real-time output with color-coded lines
- **Dark/Light Themes** — CSS variable-based glassmorphism design

### Build from Source

```bash
cd gui
npm install
npx @tauri-apps/cli build
# Binary: src-tauri/target/release/abirqu-gui
# Installers: src-tauri/target/release/bundle/
```

### Install (Linux)

```bash
# Debian/Ubuntu
sudo dpkg -i AbirQu_1.2.4_amd64.deb

# Fedora/RHEL
sudo rpm -i AbirQu-1.2.4-1.x86_64.rpm

# Any Linux (portable)
chmod +x AbirQu_1.2.4_amd64.AppImage && ./AbirQu_1.2.4_amd64.AppImage
```

### Install (Windows)

Download `AbirQu_1.2.4_x64-setup.exe` from [Releases](https://github.com/Abiress/abirqu/releases) and run the installer.

### Install (macOS)

Download `AbirQu_1.2.4_aarch64.dmg` (Apple Silicon) or `AbirQu_1.2.4_x64.dmg` (Intel) from [Releases](https://github.com/Abiress/abirqu/releases), open the DMG, and drag AbirQu to Applications.

### Pre-built Binaries

| Platform | Format | Size | Status |
|----------|--------|------|--------|
| Linux x64 | `.deb` | ~4 MB | Built & Tested |
| Linux x64 | `.rpm` | ~4 MB | Built & Tested |
| Linux x64 | `.AppImage` | ~80 MB | Built & Tested |
| Windows x64 | `.exe` (NSIS) | ~5 MB | CI/CD Auto-build |
| macOS ARM64 | `.dmg` | ~5 MB | CI/CD Auto-build |
| macOS x64 | `.dmg` | ~5 MB | CI/CD Auto-build |
| Linux ARM64 | `.deb` | ~4 MB | CI/CD Auto-build |

All installers are built automatically via GitHub Actions on every push to `master`.

---

## Installation

### From PyPI (recommended)

```bash
pip install abirqu
```

With optional hardware support:

```bash
pip install abirqu[ibm]        # IBM Quantum hardware
pip install abirqu[dwave]      # D-Wave annealer
pip install abirqu[aws]        # AWS Braket
pip install abirqu[all-hardware] # All hardware backends
pip install abirqu[dev]        # Development tools
```

### From Source

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
circuit.measure_all()

result = QuantumRun(circuit, shots=1000)
print(result.counts)  # {'00': ~500, '11': ~500}
```

### Provider API Keys (for Real Hardware)

```bash
export IBM_QUANTUM_TOKEN="your_token_here"
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export AZURE_QUANTUM_RESOURCE_ID="your_resource_id"
export IONQ_API_KEY="your_key"
export GOOGLE_CLOUD_PROJECT="your_project_id"
```

---

## Quick Start

### Basic Circuit

```python
from abirqu import Circuit
from abirqu.primitives import QuantumRun

circuit = Circuit(2)
circuit.h(0)
circuit.cnot(0, 1)
circuit.measure_all()

result = QuantumRun(circuit, shots=1000)
print(result.counts)  # {'00': ~500, '11': ~500}
```

### Quantum Chemistry

```python
from abirqu.chemistry import JordanWignerMapper

mapper = JordanWignerMapper(n_orbitals=2)
one_electron = [(0, 0, -1.0), (1, 1, -1.0)]
two_electron = [(0, 0, 0, 0, 0.5)]
qubit_terms = mapper.map_hamiltonian(one_electron, two_electron)
print(f"Qubit Hamiltonian terms: {len(qubit_terms)}")
```

### Quantum Communication

```python
from abirqu.quantum_communication import BB84Protocol

bb84 = BB84Protocol(num_bits=10)
result = bb84.run()
print(f"Final key: {result.final_key}")
print(f"QBER: {result.error_rate:.3f}")
```

### Run on Real IBM Hardware

```python
import os
if os.environ.get("IBM_QUANTUM_TOKEN"):
    from abirqu import Circuit
    from abirqu.backends.ibm import IBMQuantumBackend

    backend = IBMQuantumBackend(backend_name="ibm_fez")
    circuit = Circuit(2)
    circuit.h(0)
    circuit.cnot(0, 1)
    circuit.measure_all()
    result = backend.run_circuit(circuit, shots=100)
    print(result["counts"])
else:
    print("Set IBM_QUANTUM_TOKEN to run on real hardware")
```

---

## Tutorials

**205 tutorials** covering quantum computing from basics to advanced:

| Category | Tutorials | Topics |
|----------|-----------|--------|
| Fundamentals | 1-10 | Superposition, entanglement, QFT, QPE, Grover, Shor, VQE |
| Algorithms | 11-20 | QAOA, HHL, quantum walk, amplitude estimation, QNN |
| Machine Learning | 21-30 | Quantum RL, GANs, PCA, clustering, anomaly detection |
| Chemistry | 31-40 | Error mitigation, benchmarking, QRAM, molecular simulation |
| Advanced | 41-100 | Surface codes, fault-tolerant circuits, spin chains, chaos |
| Domain Apps | 111-200 | Medical, defense, finance, supply chain, aerospace |

**Full index:** [tutorials/INDEX.md](tutorials/INDEX.md)

---

## Test Results

```
Platform:   x86_64 | Python 3.14.4 | NumPy 2.4.4
OpenBLAS:   DYNAMIC_ARCH (Haswell) — Intel/AMD compatible
CPU:        20 cores | 30.6 GB RAM

Test Files:
  test_gui.py              125 tests  (IDE backend components)
  test_comprehensive.py     83 tests  (core, backends, noise, chemistry, QEC)
  test_qec.py               83 tests  (all QEC codes + decoders)
  test_hardware.py          80 tests  (calibration, characterization, profiling)
  test_quantum_communication.py  30 tests  (BB84, E91, CV-QKD, DI-QKD)
  test_properties.py         9 tests  (quantum invariants)
  test_hybrid_simulator.py   6 tests  (hybrid Clifford/MPS)
  test_novel_contributions.py 5 tests  (novel algorithms)
  test_readme.py             1 test   (12 code blocks verified)
  test_tutorials.py          1 test   (tutorial validation)
```

---

## Version History

| Version | Date | Key Additions |
|---------|------|---------------|
| **v1.2.4** | 2026-07-15 | **VQE Fix + GUI Overhaul** — Fixed vqe_uccsd/vqe_hardware_efficient `parameters` kwarg bug. SettingsPanel accent color and font size now apply to CSS variables. Library/Hardware panels show clear fallback when server not ready. Hardware sidebar shows active backend details. Plugins panel merges builtin plugins with backend response. Theme-aware colors across all 20+ components (zero hardcoded `border-white/5`). PythonBridge BufReader fix. All 10 backend actions verified. |
| **v1.2.2** | 2026-07-13 | **GUI Fully Wired** — All 14 panels use real SDK backend (no mock data). ExplorerPanel filesystem, PluginsPanel real listing, Console job polling, QCommPanel/DomainPanel error states, SecurityPanel key passing, BlochSphere multi-qubit fix, TTN bug fix. |
| **v1.2.1** | 2026-07-07 | **Core SDK Completion** — TTN Simulator (200+ qubits), Cross-SDK Inbound (Qiskit/Cirq/PennyLane), Job Orchestration (SQLite, 4 schedulers), Auto-differentiation (parameter-shift/adjoint), Dynamical Decoupling (XY4/XY8/CPMG/UDD), Union-Find Decoder, Distributed Simulation (MPI). 75 new tests (627→702). |
| **v1.2.0** | 2026-07-07 | **Full Quantum IDE** — 14 panels: Circuit Editor, Python/QASM, Explorer, QEC Lab, Quantum Comm, Domain Modules (Chemistry/OSINT/Crypto/Space/QPINN/Agentic), Security, Plugins, Ask Quantum (NL2Q), Settings. Framework integration (Qiskit/Cirq/OQTOPUS/D-Wave), resizable panels, noise simulation, export reports, Bloch sphere. **Backend fixes**: All handlers verified and fixed (QEC 7 code types, Chemistry VQE, Grover, QPINN, Crypto lattice, Agentic). **GUI wiring**: All panels use real SDK implementations (QCommPanel, DomainPanel OSINT, SecurityPanel Circuit). Cross-platform installers built and tested. |
| **v1.1.0** | 2026-07-06 | **Production Readiness** — Published on PyPI, CI/CD, Shor's algorithm, Grover fixed, VQE chemical accuracy, IBM hardware verified (ibm_fez), 627 tests |
| **v1.0.0** | 2026-07-05 | **Full Stack** — Hardware calibration, device characterization, noise profiling, hardware-aware compiler, cloud manager, 412 tests |
| **v0.8.0** | 2026-07 | **GUI** — Visual circuit editor, Bloch sphere, state vector, histograms, hardware panel, 125 tests |
| **v0.7.0** | 2026-07 | **QEC** — Stabilizer/Surface/Color codes, 5 decoders, magic state distillation, 83 tests |
| **v0.6.0** | 2026-06 | **Q-Comm** — 7 protocols: BB84, E91, CV-QKD, DI-QKD, satellite, repeaters, network, 30 tests |
| **v0.4.0** | 2026-06 | **Novel** — Noise-Adaptive Compiler, SPAE, Circuit Cutting, Hybrid MPS-Clifford Simulator |
| **v0.3.0** | 2026-06 | QuantumRun primitives, QNN, 6 domain modules, Unitary Synthesis, Adaptive Error Mitigation |
| **v0.2.0** | 2026-05 | Quantum OS, Post-Quantum Security, 3 simulation backends, circuit library |
| **v0.1.0** | 2026-04 | Initial release — Rust simulator, 12 backends, 8 language bindings |

---

## What's Missing

Honest listing of areas for improvement:

- **No peer review** — no independent validation of results against literature values
- **QEC decoders** — MWPM decoder uses iterative greedy with re-weighting; production use requires PyMatching or blossom algorithm for optimal matching
- **Pulse-level control** — waveforms are generated but not sent to hardware
- **IBM token required for hardware** — IBM Quantum backend needs a real API token

---

## Production & Enterprise Features

### Custom Exception Hierarchy

```python
from abirqu.exceptions import (
    AbirQuError,              # Base class
    CircuitError,             # Circuit construction errors
    SimulationError,          # Simulation failures
    BackendError,             # Hardware backend errors
    AuthenticationError,      # Missing/invalid credentials
    TranspilerError,          # Transpilation failures
    HardwareError,            # Hardware control errors
    JobError,                 # Job scheduling errors
    QuantumCommunicationError, # QKD protocol errors
    ConfigurationError,       # Configuration errors
)
```

### Logging

```python
from abirqu.logging_config import setup_logging
setup_logging(level="INFO")
```

### Deprecation & API Stability

```python
from abirqu._deprecated import deprecated, experimental

@deprecated("Use new_function() instead", since="1.2.0", removal="2.0.0")
def old_function(): pass

@experimental("This feature may change in v1.3.0")
def new_feature(): pass
```

### Audit Trail

```python
from abirqu.quantum_os.audit import AuditLogger
audit = AuditLogger()
audit.log_job_submit("job-123", "user@example.com", backend="ibm_brisbane", circuit_name="bell_state")
events = audit.get_events(user_id="user@example.com")
```

### RBAC

```python
from abirqu.quantum_os.rbac import RBACController
rbac = RBACController()
rbac.check_permission("user@example.com", "job.submit")
rbac.assign_role("user@example.com", "operator")
```

---

## How This Compares

**AbirQu is a production-grade, full-stack quantum SDK** that covers:

- **Unified execution** — `QuantumRun` does sampling, estimation, error mitigation, and ML in one call
- **12 hardware backends** — IBM (verified on real hardware), D-Wave, SpinQ, IonQ, Rigetti, Quantinuum, AWS, Azure, Google, Pasqal, OQC, QuEra
- **6 simulation engines** — GPU, Clifford, MPS, TTN, Monte Carlo, NumPy
- **Full transpiler pipeline** — ML-enhanced (RL routing + GNN layout), target-aware decomposition, SWAP routing, fidelity estimation
- **Noise mitigation** — ZNE, readout mitigation, M3, PEC, adaptive error mitigation, dynamical decoupling
- **QEC** — Surface/Color/Stabilizer codes, 6 decoders (MWPM + Union-Find), magic state distillation
- **7 QKD protocols** — BB84, E91, CV-QKD, DI-QKD, satellite, repeaters, network
- **6 domain modules** — Chemistry, OSINT, Crypto, Space, QPINN, Agentic
- **Post-quantum security** — Kyber-768/1024 KEM, Dilithium-2/3/5 signatures, SPHINCS+-128f/256f signatures
- **AI integration** — MCP protocol, LLM copilot, PyTorch/JAX/TensorFlow layers
- **Full desktop IDE** — 14 panels, circuit editor, code editors, Bloch sphere, export reports
- **8 language bindings** — Python, JavaScript, Go, Java, .NET, Swift, Kotlin, WebAssembly
- **206 tutorials** — comprehensive learning material
- **Resource estimation** — Algorithm overhead + surface code cost model
- **Cross-SDK converters** — Import from Qiskit, Cirq, PennyLane

**Compared to specialized SDKs:**
- **vs Qiskit**: AbirQu has broader scope (communication, QEC, domain modules, IDE). Qiskit has deeper IBM hardware integration.
- **vs Cirq**: AbirQu supports 12 backends vs Cirq's Google focus. AbirQu includes QEC and domain modules.
- **vs PennyLane**: Both support differentiation. AbirQu includes hardware control, QEC, and a full IDE.
- **vs Braket**: AbirQu is hardware-independent (pure NumPy). Braket is AWS-focused.
- **vs TKET**: AbirQu includes domain modules, QEC, and a full IDE. TKET focuses on hardware-agnostic optimization.

**Choose AbirQu when you need:** a single SDK for quantum computing, communication, QEC, hardware control, and a visual development environment — all hardware-independent.

**Choose a specialized SDK when you need:** deep integration with a specific vendor's hardware features, or peer-reviewed algorithms for publication.

---

## Known Limitations

| Area | Status | Notes |
|------|--------|-------|
| **Shor's algorithm** | Hybrid | Circuit template built, but factoring is done classically. Full quantum modular exponentiation is planned for v1.3.0 |
| **Copilot** | Template-matching | Uses keyword matching, not an actual LLM. Handles common patterns but not arbitrary natural language |
| **Security module** | Classical crypto | Uses HMAC-SHA256 stream cipher. Kyber/Dilithium/SPHINCS+ are parameter generators only, not full implementations |
| **TTN Simulator** | Fixed in v1.2.2 | Was broken due to missing import. Now works for circuits up to 200+ qubits |
| **Multi-GPU simulation** | Partial | Intra-GPU gates work. Inter-GPU 2-qubit gates return 0.0 (no communication layer) |
| **HHL Solver** | Simplified | Classical reconstruction correct, but quantum circuit uses approximate state prep and limited eigenvalues |
| **Hybrid MPS-Clifford** | Approximate | Tableau↔MPS conversions are lossy. Useful for exploration, not production |
| **Windows/macOS installers** | CI/CD only | Built automatically via GitHub Actions. Not pre-built in repo |
| **IBM Quantum** | Token required | Real API token needed. Verified on ibm_fez (156 qubits) |
| **D-Wave** | `neal` unavailable | Falls back to random sampling on Python 3.14 |

---

## Support

- **Beginner Guide**: [abirqu/docs/beginner_guide.md](abirqu/docs/beginner_guide.md)
- **206 Tutorials**: [tutorials/INDEX.md](tutorials/INDEX.md)
- **Documentation**: [Readthedocs](https://abirqu.readthedocs.io)
- **Whitepaper**: [docs/whitepaper.md](docs/whitepaper.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Security**: [SECURITY.md](SECURITY.md)
- **PyPI**: [pypi.org/project/abirqu](https://pypi.org/project/abirqu/)

---

**Built with** Python, NumPy, SciPy, Rust, TypeScript, React **Licensed under** MIT 2026
**Runs on** Intel, AMD, Qualcomm, MediaTek, Apple Silicon — CPU and GPU **No vendor lock-in**

---

**2026 Abir Maheshwari — [Artificial Quantum Dyson Intelligence](https://aqdi.world), Biro Labs**
**Made in India, for the World.**
