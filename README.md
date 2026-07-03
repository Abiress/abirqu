# AbirQu Quantum SDK v0.3.0

**Created by Abir Maheshwari** | abhirsxn@gmail.com | 🇮🇳 Indian Mission Support Enabled

> **Full-stack quantum computing SDK** — 12 hardware backends, unified `QuantumRun` primitives, QNN built-in, noise fingerprinting, circuit library, visualization, transpiler pipeline, Quantum OS, post-quantum security, and 3 simulation backends.

### Status & Badges

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Version](https://img.shields.io/badge/version-0.3.0-blue)
![Backends](https://img.shields.io/badge/backends-12%20Real-purple)
![Primitives](https://img.shields.io/badge/primitives-QuantumRun%20unified-orange)
![QNN](https://img.shields.io/badge/QNN-built--in-green)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What's New in v0.3.0

### QuantumRun — ONE Function That Does Everything

No more separate Sampler/Estimator/QNN classes. AbirQu's `QuantumRun` does everything in a single call:

```python
from abirqu.primitives import QuantumRun

# Sampling + estimation + mitigation — one call
result = QuantumRun(
    circuits=bell_circuit,
    observables={"ZZ": [[1,0,0,0],[0,-1,0,0],[0,0,-1,0],[0,0,0,1]]},
    shots=4096,
    mitigate=True,
)

result.counts          # {'00': 2048, '11': 2048}
result.expectations    # [1.0]
result.mitigation      # MitigationResult with denoised probs
result.statevector     # exact state (if shots=0)
result.entropy         # Shannon entropy
result.effective_shots # statistically independent shots
```

### Built-in QNN — No External Libraries Needed

```python
from abirqu.primitives import QNN
import numpy as np

qnn = QNN(num_qubits=4, layers=3, entanglement="sca")
params = np.random.uniform(0, 2*np.pi, qnn.num_parameters)

# Forward pass
probs = qnn.forward(params)

# Gradient via parameter-shift rule
grads = qnn.gradient(params, observable=zz_matrix)

# Train on data
history = qnn.train(X_train, y_train, epochs=50, lr=0.1)
```

### Noise Fingerprint — Unique to AbirQu

Visualize your noise model as a spectral fingerprint — no other SDK has this:

```python
from abirqu.visualization import noise_fingerprint_svg

svg = noise_fingerprint_svg(
    num_qubits=5,
    single_qubit_errors=[0.001, 0.005, 0.01, 0.02, 0.05],
    readout_errors=[0.002, 0.008, 0.015, 0.03, 0.04],
    t1_times=[50, 40, 30, 20, 10],
)
```

### Circuit Library — Parameterized Ansatz Circuits

```python
from abirqu.library import (
    real_amplitudes, efficient_su2, n_local,
    qaoa_circuit, vqe_hardware_efficient,
    zz_feature_map, iqp_encoding,
    ghz_circuit, grover_circuit, qft_circuit,
)

# N-local with unique "sca" entanglement
ansatz = efficient_su2(6, reps=3, entanglement="sca")

# QAOA with automatic mixer
qaoa = qaoa_circuit(8, edges=[(0,1),(1,2)], p=3)

# Feature maps for quantum ML
features = zz_feature_map(4, features=[0.1, 0.2, 0.3, 0.4])
```

### Advanced Noise Mitigation

```python
from abirqu.noise_toolkit import (
    ZeroNoiseExtrapolator, M3Mitigator, ReadoutMitigator,
)

# ZNE with Richardson extrapolation
zne = ZeroNoiseExtrapolator(method="richardson")
clean = zne.extrapolate([1.0, 1.5, 2.0], [0.8, 0.7, 0.6])

# M3 — matrix-free measurement mitigation
m3 = M3Mitigator(n_qubits=4)
m3.calibrate(calibration_data)
mitigated = m3.mitigate(noisy_counts)
```

### Circuit Cutting for Distributed Quantum Computing

```python
from abirqu.addons import CircuitCutter

cutter = CircuitCutter(max_subcircuit_qubits=5)
sub_circuits = cutter.cut(large_circuit)
# Execute sub-circuits independently, then recombine
```

---

## How AbirQu Compares (Evidence-Based)

| Feature | **AbirQu v0.3.0** | [Qiskit](https://www.ibm.com/quantum/qiskit) | [Cirq](https://quantumai.google/cirq) | [Braket](https://aws.amazon.com/braket/) |
|---------|-----------------|---------|-------|---------|
| **Unified Execution** | ✅ `QuantumRun` does everything | ❌ Separate Sampler/Estimator | ❌ Separate classes | ❌ Separate classes |
| **Built-in QNN** | ✅ No external libs needed | ❌ qiskit-machine-learning | ❌ cirq-contrib | ❌ Not included |
| **Noise Fingerprint** | ✅ Unique spectral visualization | ❌ Not available | ❌ Not available | ❌ Not available |
| **Circuit Library** | ✅ N-local, QAOA, VQE, encoders | ✅ qiskit.circuit.library | ✅ cirq.ion | ❌ Limited |
| **Noise Mitigation** | ✅ ZNE, M3, PEC, readout | ✅ qiskit.ignis (deprecated) | ✅ cirq.work | ❌ Limited |
| **Circuit Cutting** | ✅ Built-in | ❌ qiskit-experiments | ❌ Not native | ❌ Not native |
| **Hardware Backends** | ✅ 12 backends | IBM ecosystem only | Google ecosystem only | AWS only |
| **Quantum OS** | ✅ Scheduler, resource mgr | ❌ External tools | ❌ External tools | ❌ External tools |
| **PQC Security** | ✅ Kyber, Dilithium, SPHINCS+ | ❌ Not included | ❌ Not included | ❌ Not included |
| **Visualization** | ✅ SVG, HTML, ASCII, noise fingerprint | ✅ MPL, text | ✅ MPL | ❌ Basic |
| **Open Source** | ✅ MIT | ✅ Apache 2.0 | ✅ Apache 2.0 | Partial |

---

## Full Feature List

### Primitives (NEW in v0.3.0)
- `QuantumRun` — unified execution (sampling + estimation + mitigation)
- `Sampler` — quasi-distribution with entropy and effective shots
- `Estimator` — expectation values <ψ|O|ψ>
- `QNN` — quantum neural network with parameter-shift gradients
- `QuasiDistribution` — probability distribution with metadata

### Circuit Library (NEW in v0.3.0)
- `real_amplitudes`, `efficient_su2`, `n_local` — parameterized ansatz
- `qaoa_circuit`, `qaoa_maxcut` — QAOA ansatz
- `vqe_hardware_efficient`, `vqe_uccsd` — VQE ansatz
- `angle_encoding`, `amplitude_encoding`, `zz_feature_map`, `iqp_encoding` — data encoders
- `ghz_circuit`, `w_state`, `qft_circuit`, `grover_circuit` — benchmarks

### Visualization (NEW in v0.3.0)
- `CircuitDrawer` — text, ASCII, SVG, HTML output
- `BlochSphere` — multi-qubit partial trace, 3D projection
- `histogram_text`, `histogram_svg` — measurement results
- `stateplot_svg`, `probability_svg` — state vector plots
- `gate_map_svg`, `error_map_svg` — hardware topology
- `noise_fingerprint_svg` — unique noise model visualization
- `circuit_fingerprint_svg` — circuit structure fingerprint

### Noise Toolkit (NEW in v0.3.0)
- `ZeroNoiseExtrapolator` — Richardson, linear, exponential
- `ReadoutMitigator` — confusion matrix inversion
- `M3Mitigator` — matrix-free measurement mitigation
- `PECCorrector` — probabilistic error cancellation
- `generate_calibration_circuits` — calibration circuit generation

### Addons (NEW in v0.3.0)
- `MultiProductFormula` — Hamiltonian simulation
- `TrotterSuzuki` — 1st/2nd order decomposition
- `CircuitCutter` — distributed quantum computing
- `AQCTensor` — approximate quantum compilation
- `OperatorBackpropagation` — measurement reduction
- `SQDCorrector` — sample-based quantum diagonalization

### Core (v0.2.0)
- 12 hardware backends: IBM, AWS, Azure, Google, IonQ, Rigetti, Quantinuum, Pasqal, OQC, QuEra, D-Wave, SpinQ
- Transpiler pipeline: target-aware decomposition, SWAP routing, ASAP scheduling
- Quantum OS: job scheduler, resource manager, virtual QPU, cost estimator
- PQC Security: Kyber-768, Dilithium-2, SPHINCS+-128f, BB84 QKD
- 3 simulators: GPU (CuPy), Clifford (stabilizer), MPS (tensor network)
- Circuit converters: Qiskit, Braket, Cirq, IonQ, Pytket, Quil, OpenQASM

---

## Quick Start

```python
from abirqu import Circuit
from abirqu.primitives import QuantumRun

# Create a Bell state
bell = Circuit(2, "Bell")
bell.h(0)
bell.cnot(0, 1)

# Run — one call does everything
result = QuantumRun(bell, shots=4096)
print(result.counts)  # {'00': ~2048, '11': ~2048}

# Visualize
from abirqu.visualization import draw
print(draw(bell, output="svg"))
```

---

## Installation

```bash
pip install abirqu
```

---

**© 2026 Abir Maheshwari — Artificial Quantum Dyson Intelligence, Biro Labs, Aquilldriver**
**🇮🇳 Made in India, for the World.**
