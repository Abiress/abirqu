# Contributing to AbirQu

Welcome — and thank you for your interest in AbirQu! This guide will help you get started testing, using, and contributing to the AbirQu Quantum SDK.

AbirQu is a comprehensive, hardware-independent quantum computing SDK. It provides a single unified API across quantum computing, quantum communication, quantum error correction, hardware control, and a full visual development environment — all implemented in pure NumPy.

Whether you are a quantum researcher, a software developer, a student, or just curious about quantum computing, your contributions are welcome.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Quick Start](#2-quick-start)
3. [Testing the SDK](#3-testing-the-sdk)
4. [Running on Real Hardware](#4-running-on-real-hardware)
5. [Reporting Issues](#5-reporting-issues)
6. [Contributing Code](#6-contributing-code)
7. [Code Standards](#7-code-standards)
8. [Project Structure](#8-project-structure)
9. [Development Setup](#9-development-setup)
10. [Contact](#10-contact)

---

## 1. Getting Started

### What is AbirQu?

AbirQu is a full-stack quantum computing SDK that eliminates the fragmentation across quantum providers. Instead of learning separate APIs for IBM Qiskit, Google Cirq, Amazon Braket, and others, AbirQu gives you:

- **One unified function** — `QuantumRun` — for sampling, estimation, error mitigation, and ML
- **One circuit library** — works across 12 hardware backends
- **One transpiler pipeline** — decomposes gates for any target architecture
- **5 simulation engines** — GPU, Clifford, MPS, Monte Carlo, NumPy
- **6 domain modules** — Chemistry, OSINT, Cryptanalysis, Space, Q-PINN, Agentic
- **7 quantum communication protocols** — BB84, E91, CV-QKD, and more
- **Fault-tolerant QEC** — Surface, Color, and Stabilizer codes with 5 decoders

### Who is AbirQu for?

- **Quantum Researchers** — single SDK with algorithms from multiple quantum domains
- **Software Developers** — unified API across different hardware backends
- **Students and Educators** — learn quantum computing with a hardware-independent SDK
- **Enterprise Teams** — post-quantum cryptography and job scheduling
- **Pharmaceutical Researchers** — quantum chemistry simulation
- **Cybersecurity Teams** — post-quantum cryptographic algorithms

### System Requirements

| Requirement | Minimum | Recommended |
|------------|---------|-------------|
| Python | 3.9+ | 3.10+ |
| NumPy | 1.21+ | 1.24+ |
| RAM | 4 GB | 16 GB+ |
| Disk | 100 MB | 500 MB |
| OS | Linux, macOS, Windows | Linux (best OpenBLAS support) |

Optional for GPU acceleration: CUDA 11.0+ with CuPy and an NVIDIA GPU (compute capability 3.5+).

---

## 2. Quick Start

### Install from Source

AbirQu is not yet published on PyPI. Install from the GitHub repository:

```bash
git clone https://github.com/Abiress/abirqu.git
cd abirqu
pip install -e .
```

### Install with Optional Features

```bash
# GPU acceleration (requires CUDA + CuPy)
pip install -e ".[gpu]"

# Visualization (matplotlib, pillow)
pip install -e ".[visualization]"

# All optional features
pip install -e ".[gpu,visualization]"

# Development tools (pytest, pytest-cov, hypothesis)
pip install -e ".[dev]"
```

### Verify Installation

```python
import abirqu
print(f"AbirQu version: {abirqu.__version__}")

from abirqu import Circuit, H, CNOT
bell = Circuit(2)
bell.h(0)
bell.cnot(0, 1)

from abirqu.primitives import QuantumRun
result = QuantumRun(bell, shots=1000)
print(f"Bell state counts: {result.counts}")
# Expected: {'00': ~500, '11': ~500}
```

### Run Your First Circuit

Create a file called `my_first_circuit.py`:

```python
from abirqu import Circuit, H, CNOT
from abirqu.primitives import QuantumRun

# Create a Bell state — the "Hello World" of quantum computing
circuit = Circuit(2)
circuit.h(0)       # Put qubit 0 into superposition
circuit.cnot(0, 1) # Entangle qubit 1 with qubit 0
circuit.measure([0, 1])

result = QuantumRun(circuit, shots=1000)
print(result.counts)  # {'00': ~500, '11': ~500}
```

```bash
python my_first_circuit.py
```

### Run More Examples

```bash
# Quick start with state visualization
python examples/quick_start.py

# Grover's search algorithm
python examples/grover_search.py

# QAOA for Max-Cut
python examples/qaoa_maxcut.py

# VQE for H2 molecule
python examples/vqe_h2.py

# Surface code error correction
python examples/qec_surface_code.py
```

### Run Benchmarks

```bash
# Run the full benchmark suite on local simulator
python benchmarks/run_benchmarks.py

# Run with a specific backend
python benchmarks/run_benchmarks.py --backend local

# Save results to JSON
python benchmarks/run_benchmarks.py --output results.json
```

Benchmark results are saved to `benchmark_results.json` in the project root.

---

## 3. Testing the SDK

### Running the Test Suite

AbirQu has **627 tests** covering all modules. Run them with:

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=abirqu --cov-report=term-missing

# Run a specific test file
pytest tests/test_comprehensive.py

# Run a specific test class or method
pytest tests/test_comprehensive.py::TestCircuit::test_create_empty
```

### Test Files

| File | What It Tests |
|------|---------------|
| `tests/test_comprehensive.py` | Core circuits, backends, noise, primitives, chemistry, QEC, simulation |
| `tests/test_gui.py` | Quantum IDE/GUI components |
| `tests/test_hardware.py` | Hardware calibration, characterization, noise profiling |
| `tests/test_hybrid_simulator.py` | Hybrid MPS-Clifford simulator |
| `tests/test_novel_contributions.py` | Noise-adaptive compiler, SPAE, circuit cutting |
| `tests/test_properties.py` | Quantum circuit properties |
| `tests/test_qec.py` | Quantum error correction codes and decoders |
| `tests/test_quantum_communication.py` | BB84, E91, CV-QKD, and other protocols |
| `tests/test_tutorials.py` | Tutorial code snippets |

### Running Tutorials

AbirQu includes **205 tutorials** covering quantum computing from basics to advanced applications. Tutorials are in the `tutorials/` directory.

```bash
# View the full tutorial index
cat tutorials/INDEX.md

# Run a specific tutorial (tutorials are markdown with code)
# For example, Tutorial 1 — Bell States:
python -c "
from abirqu import Circuit, H, CNOT
from abirqu.primitives import QuantumRun

circuit = Circuit(2)
circuit.h(0)
circuit.cnot(0, 1)
circuit.measure([0, 1])

result = QuantumRun(circuit, shots=1000)
print(result.counts)
"
```

Tutorial categories:

| Category | Tutorials | Topics |
|----------|-----------|--------|
| Fundamentals | 1–10 | Superposition, entanglement, QFT, QPE, Grover, Shor, VQE |
| Algorithms | 11–20 | QAOA, HHL, quantum walk, amplitude estimation, QNN |
| Machine Learning | 21–30 | Quantum RL, GANs, PCA, clustering, anomaly detection |
| Chemistry & Info | 31–40 | Error mitigation, benchmarking, QRAM, molecular simulation |
| Advanced | 41–50 | Surface codes, fault-tolerant circuits, compilers, sensing |
| Expert | 51–100 | Spin chains, chaos, advanced optimization, QML |
| Cutting-Edge | 111–120 | Novel algorithms, research frontiers |
| Domain Apps | 121–150 | Medical, defense, finance, supply chain, agriculture |
| Industry | 151–170 | Manufacturing, retail, aerospace, telecom, energy |
| Business | 171–200 | R&D, IP, M&A, Web3, DevOps, ML Ops |

### Running Benchmarks

```bash
# Full benchmark suite
python benchmarks/run_benchmarks.py

# Specific backend
python benchmarks/run_benchmarks.py --backend local

# Save to custom output file
python benchmarks/run_benchmarks.py --output my_results.json
```

Benchmarks measure wall-clock time and memory for: QFT, random circuits, VQE, Grover search, state preparation, and full pipeline simulation.

---

## 4. Running on Real Hardware

AbirQu supports 12 hardware backends. IBM Quantum is the most complete integration.

### IBM Quantum Setup

**Step 1: Get an IBM Quantum Token**

1. Go to [quantum.ibm.com](https://quantum.ibm.com)
2. Create a free account (or sign in)
3. Navigate to **Account Settings** → **API Tokens**
4. Click **Create Token** and copy it

**Step 2: Set Your Token as an Environment Variable**

```bash
export IBM_QUANTUM_TOKEN="your_token_here"
```

Or add it to a `.env` file in the project root:

```bash
cp .env.example .env
# Edit .env and set IBM_QUANTUM_TOKEN=your_token_here
```

**Step 3: Install IBM Backend Dependencies**

```bash
pip install -e ".[ibm]"
```

**Step 4: Run on Real Hardware**

```bash
# Dry run (local simulation, no credentials needed)
python examples/real_hardware_execution.py --dry-run

# Real hardware execution
python examples/real_hardware_execution.py --backend ibm_brisbane --shots 1024
```

### Other Hardware Backends

AbirQu also supports (with varying levels of verification):

| Backend | Install | Status |
|---------|---------|--------|
| IBM Quantum | `pip install -e ".[ibm]"` | SDK-wired |
| D-Wave | `pip install -e ".[dwave]"` | Verified |
| SpinQ | `pip install -e ".[spinq]"` | Verified |
| AWS Braket | `pip install -e ".[aws]"` | SDK-wired |
| Azure Quantum | `pip install -e ".[azure]"` | SDK-wired |
| Google Quantum | `pip install -e ".[cirq]"` | SDK-wired |
| IonQ | `pip install -e ".[ionq]"` | SDK-wired |

**Note:** "SDK-wired" means adapter code exists but has not been validated against real hardware. D-Wave and SpinQ have been verified.

### Provider API Keys

Set environment variables or create a `.env` file (see `.env.example` for a template):

```bash
# IBM Quantum
export IBM_QUANTUM_TOKEN="your_token_here"

# AWS Braket
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"

# Azure Quantum
export AZURE_QUANTUM_RESOURCE_ID="your_resource_id"

# IonQ
export IONQ_API_KEY="your_key"

# Google Quantum
export GOOGLE_CLOUD_PROJECT="your_project_id"
```

AbirQu auto-discovers credentials from environment variables via `CloudManager`.

---

## 5. Reporting Issues

If you find a bug, have a feature request, or run into a problem, please open a GitHub issue:

**[https://github.com/Abiress/abirqu/issues](https://github.com/Abiress/abirqu/issues)**

### What to Include

A good issue report helps us fix the problem faster. Please include:

1. **A clear title** — e.g., "QuantumRun raises IndexError on 3-qubit circuit"
2. **Your environment** — OS, Python version, NumPy version, AbirQu version
3. **Steps to reproduce** — minimal code that triggers the issue
4. **Expected behavior** — what you thought would happen
5. **Actual behavior** — the error message or unexpected output
6. **Full traceback** — if there is an error, paste the complete traceback

### Example Issue Report

```markdown
**Title:** QuantumRun crashes with empty circuit

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.11.5
- NumPy: 2.4.4
- AbirQu: 1.2.0

**Steps to reproduce:**
```python
from abirqu import Circuit
from abirqu.primitives import QuantumRun

circuit = Circuit(0)
result = QuantumRun(circuit, shots=100)
```

**Expected:** Either a clear error message or an empty result.

**Actual:** `IndexError: list index out of range` in `abirqu/primitives/__init__.py:42`

**Full traceback:**
```
Traceback (most recent call last):
  File "test.py", line 6, in <module>
    result = QuantumRun(circuit, shots=100)
  ...
```
```

### Quick Way to Get Your Environment Info

```bash
python -c "import sys, numpy, abirqu; print(f'Python {sys.version}\nNumPy {numpy.__version__}\nAbirQu {abirqu.__version__}')"
```

---

## 6. Contributing Code

### Fork, Branch, Test, PR Workflow

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/your-username/abirqu.git
   cd abirqu
   ```
3. **Install** in development mode:
   ```bash
   pip install -e ".[dev]"
   ```
4. **Create a branch** for your change:
   ```bash
   git checkout -b feature/your-feature-name
   ```
   Use a descriptive branch name: `feature/add-pauli-y`, `fix/noise-model-bug`, `docs/update-readme`
5. **Make your changes** and write tests
6. **Run the test suite** to make sure nothing is broken:
   ```bash
   pytest
   ```
7. **Commit** with a clear message:
   ```bash
   git add .
   git commit -m "Add Pauli-Y gate to circuit library"
   ```
8. **Push** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
9. **Open a Pull Request** on the [main repository](https://github.com/Abiress/abirqu/pulls)

### Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Include a clear description of what changed and why
- Add tests for new functionality
- Update documentation if your change affects the public API
- Make sure all existing tests pass before submitting
- Reference any related issues (e.g., "Closes #42")

### What Makes a Good Contribution

- **Bug fixes** — anything that makes AbirQu more reliable
- **Tests** — improve coverage for under-tested modules
- **Documentation** — clarify confusing APIs, fix typos, add examples
- **New algorithms** — implement well-known quantum algorithms
- **Performance** — optimize simulation or compilation code
- **Backend improvements** — improve hardware adapter accuracy

---

## 7. Code Standards

### Python Style

AbirQu follows PEP 8 with a line length of 100 characters.

```bash
# Check style with ruff (configured in pyproject.toml)
ruff check abirqu/

# Auto-fix style issues
ruff check --fix abirqu/

# Format code
ruff format abirqu/
```

Key conventions:

- Use `snake_case` for functions and variables
- Use `PascalCase` for classes
- Use `UPPER_SNAKE_CASE` for constants
- Maximum line length: 100 characters
- Import sorting: standard library, third-party, local (enforced by ruff)

### Test Requirements

- Every new feature should include at least one test
- Test functions must start with `test_`
- Test classes must start with `Test`
- Tests should verify behavior, not just absence of errors
- Use `pytest` fixtures for shared setup

```python
# Example test
def test_circuit_create():
    from abirqu import Circuit
    c = Circuit(3, "test")
    assert c.num_qubits == 3
    assert len(c.gates) == 0
    assert c.name == "test"
```

### Documentation Expectations

- All public functions and classes should have docstrings
- Use NumPy-style docstrings when possible
- Include type hints where practical
- Update `README.md` if you add a new feature
- Update `tutorials/INDEX.md` if you add a new tutorial

```python
def my_function(param1: int, param2: str = "default") -> bool:
    """Do something quantum.

    Parameters
    ----------
    param1 : int
        The first parameter.
    param2 : str, optional
        The second parameter. Default is "default".

    Returns
    -------
    bool
        True if successful.
    """
    return True
```

---

## 8. Project Structure

```
abirqu/
├── abirqu/                  # Main package — the SDK itself
│   ├── __init__.py          # Package entry point
│   ├── circuit.py           # Circuit and Gate classes
│   ├── gates.py             # Gate definitions (H, X, CNOT, etc.)
│   ├── primitives/          # QuantumRun, Sampler, Estimator, QNN
│   ├── library/             # Pre-built circuits (QFT, Grover, VQE, etc.)
│   ├── simulation/          # 5 simulation backends (GPU, Clifford, MPS, etc.)
│   ├── numpy_sim.py         # Pure NumPy statevector simulator
│   ├── transpiler/          # Gate decomposition pipeline
│   ├── noise_toolkit.py     # ZNE, readout mitigation, PEC
│   ├── qec/                 # Quantum error correction codes and decoders
│   ├── quantum_communication/  # BB84, E91, CV-QKD, etc.
│   ├── chemistry/           # Molecular Hamiltonian mapping
│   ├── osint/               # Graph optimization → Ising/QUBO
│   ├── crypto/              # Shor, Grover, Kyber, Dilithium
│   ├── space/               # HHL, CFD, structural solvers
│   ├── qpinn.py             # Quantum PDE solvers
│   ├── agentic/             # Task orchestration
│   ├── hardware/            # Calibration, characterization, noise profiling
│   ├── backends/            # Hardware backend adapters (IBM, D-Wave, etc.)
│   ├── cloud/               # Cloud manager, credential management
│   ├── quantum_os/          # Job scheduling, resource management
│   ├── visualization/       # Circuit drawer, Bloch sphere, histograms
│   ├── gui/                 # Full IDE/GUI
│   ├── optimize/            # Noise-adaptive compiler, circuit simplifier
│   ├── addons/              # Trotter, circuit cutting, AQCTensor
│   ├── formats/             # Import/export (Qiskit, Cirq, Braket, etc.)
│   ├── docs/                # Beginner guide
│   └── cli.py               # Command-line interface
├── tests/                   # Test suite (627 tests)
│   ├── test_comprehensive.py
│   ├── test_gui.py
│   ├── test_hardware.py
│   ├── test_hybrid_simulator.py
│   ├── test_novel_contributions.py
│   ├── test_properties.py
│   ├── test_qec.py
│   ├── test_quantum_communication.py
│   └── test_tutorials.py
├── tutorials/               # 205 tutorials (markdown with code)
│   ├── INDEX.md             # Full tutorial index
│   ├── 01_bell_states_and_circuits.md
│   ├── 02_quantum_algorithms.md
│   └── ... (1.md through 200.md)
├── examples/                # Runnable example scripts
│   ├── quick_start.py
│   ├── grover_search.py
│   ├── qaoa_maxcut.py
│   ├── vqe_h2.py
│   ├── qec_surface_code.py
│   ├── real_hardware_execution.py
│   └── ...
├── benchmarks/              # Benchmark suite
│   └── run_benchmarks.py
├── scripts/                 # Utility scripts
├── assets/                  # Logo, architecture diagrams
├── pyproject.toml           # Build config, dependencies, tool settings
├── setup.py                 # Backward-compatible setup script
├── README.md                # Project overview and documentation
├── CONTRIBUTING.md          # This file
├── CODE_OF_CONDUCT.md       # Community standards
├── SECURITY.md              # Security policy
├── LICENSE                  # MIT License
└── .env.example             # Provider credentials template
```

---

## 9. Development Setup

### Full Development Environment

```bash
# Clone and install
git clone https://github.com/Abiress/abirqu.git
cd abirqu
pip install -e ".[dev,visualization]"

# Verify everything works
pytest -v
```

### Running Tests

```bash
# All tests
pytest

# Verbose output
pytest -v

# With coverage
pytest --cov=abirqu --cov-report=term-missing

# Specific file
pytest tests/test_comprehensive.py

# Specific test
pytest tests/test_comprehensive.py::TestCircuit::test_create_empty

# Stop on first failure
pytest -x
```

### Linting and Formatting

```bash
# Check for style issues
ruff check abirqu/

# Auto-fix style issues
ruff check --fix abirqu/

# Format code
ruff format abirqu/

# Type checking (if you set it up)
mypy abirqu/
```

### Pre-commit Checks

Before submitting a PR, run this full check:

```bash
ruff check abirqu/ && ruff format --check abirqu/ && pytest
```

If any of these fail, fix the issues before pushing.

### Git Configuration (Optional)

```bash
# Set up a pre-commit hook to run tests automatically
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Running tests before commit..."
pytest --tb=short -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

---

## 10. Contact

- **GitHub Issues:** [https://github.com/Abiress/abirqu/issues](https://github.com/Abiress/abirqu/issues) — for bug reports, feature requests, and questions
- **Email:** abhirsxn@gmail.com — for private inquiries
- **Website:** [aqdi.world](https://aqdi.world) — Artificial Quantum Dyson Intelligence

### Getting Help

- Read the [Beginner Guide](abirqu/docs/beginner_guide.md)
- Browse the [Tutorial Index](tutorials/INDEX.md)
- Check the [README](README.md) for a full feature overview
- Search [existing issues](https://github.com/Abiress/abirqu/issues) before opening a new one

---

## License

By contributing to AbirQu, you agree that your contributions will be licensed under the [MIT License](LICENSE).

**Copyright 2026 Abir Maheshwari.**

---

Thank you for contributing to AbirQu! Every improvement — no matter how small — helps make quantum computing more accessible.
