# AbirQu Dependencies Guide

Complete list of all dependencies required to run AbirQu across all supported languages and platforms.

---

## 🐍 Python Dependencies

### **Core Python**
```
Python >= 3.9, <= 3.14
  Tested on: 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
  Preferred: Python 3.11 or 3.12
```

### **Required Packages**

| Package | Version | Purpose |
|---------|---------|---------|
| `numpy` | >=1.22 | Statevector simulation, numerical computing |
| `scipy` | >=1.10 | Scientific algorithms, optimization |
| `matplotlib` | >=3.5 | Circuit visualization, plotting |
| `pytest` | >=6.0 | Unit testing framework |
| `maturin` | >=0.14 | Rust-Python bindings |

### **Optional Packages** (for specific features)

| Package | Version | Purpose |
|---------|---------|---------|
| `qiskit` | >=0.41 | IBM Qiskit integration |
| `cirq` | >=1.0 | Google Cirq integration |
| `amazon-braket` | >=2.0 | AWS Braket integration |
| `pycryptodome` | >=3.18 | AES encryption for circuits |
| `websockets` | >=10.0 | Cloud backend communication |
| `black` | >=22.0 | Code formatting (dev) |
| `flake8` | >=4.0 | Code linting (dev) |

### **Installation**

```bash
# Basic installation (core only)
pip install -e .

# With development dependencies
pip install -e ".[dev]"

# With all optional providers
pip install -e ".[dev,qiskit,cirq,braket,crypto]"

# Specific Python version
python3.12 -m pip install -e ".[dev]"
```

---

## 🦀 Rust Dependencies

### **Rust Toolchain**
```
Rustc >= 1.70
Cargo >= 1.70
Edition: 2021
```

### **Cargo Dependencies** (Cargo.toml)

| Crate | Version | Purpose |
|-------|---------|---------|
| `pyo3` | 0.19 | Python-Rust FFI bindings |
| `numpy` | 0.19 | NumPy array interop |
| `ndarray` | 0.15 | N-dimensional arrays |
| `num-complex` | 0.4 | Complex number support |

### **Build Requirements**

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Build release
cargo build --release

# Run tests
cargo test --lib

# Generate bindings
maturin develop
```

---

## 🌐 JavaScript/Node Dependencies

### **Node.js**
```
Node.js >= 14.0
npm >= 8.0 or yarn >= 1.22
```

### **Package Dependencies** (package.json)

| Package | Version | Purpose |
|---------|---------|---------|
| `@abirqu/core` | local | WASM Rust bindings |
| `jest` | ^29.0 | Testing framework |
| `typescript` | ^4.9 | TypeScript support (optional) |

### **Installation**

```bash
cd js
npm install
npm test

# Build WASM
npm run build

# WASM binary size
ls -lh pkg/abirqu_core_wasm_bg.wasm
```

---

## 🔗 Go Dependencies

### **Go Version**
```
Go >= 1.18
CGO enabled (required for C bindings)
```

### **Go Module Dependencies** (go.mod)

```go
go 1.20

// No external dependencies - uses C library directly
// cgo links to Rust-generated C library (abirqu_core)
```

### **Build Requirements**

```bash
cd go/abirqu
go get
go build ./...
go test ./...

# With linking
LD_LIBRARY_PATH=/path/to/abirqu/target/release \
  go run main.go
```

---

## ☕ Java Dependencies

### **Java Version**
```
Java >= 11
JDK (OpenJDK or Oracle JDK recommended)
```

### **Build Tool**
- Maven >= 3.6 (preferred)
- OR Gradle >= 6.0

### **JNI Requirements**

```bash
cd java
mvn clean install
mvn test

# JNI header generation
javah -d include com.abirqu.Simulator
```

---

## 🎯 Kotlin Dependencies

### **Kotlin Version**
```
Kotlin >= 1.8
Kotlin Gradle Plugin >= 1.8
```

### **Build Requirements**

```bash
cd kotlin
./gradlew build
./gradlew test
```

---

## 🔷 .NET Dependencies

### **.NET Version**
```
.NET >= 6.0
C# >= 9.0
```

### **NuGet Packages**
- (To be determined based on P/Invoke requirements)

### **Build Requirements**

```bash
cd dotnet
dotnet build
dotnet test
```

---

## 🍎 Swift Dependencies

### **Swift Version**
```
Swift >= 5.5
SwiftPM (Swift Package Manager)
```

### **Build Requirements**

```bash
cd swift
swift build
swift test
```

---

## 🖥️ C/C++ Dependencies

### **Compiler Requirements**

| Platform | Compiler | Version |
|----------|----------|---------|
| Linux | GCC/Clang | >= 9 |
| macOS | Clang | >= 12 |
| Windows | MSVC | >= 2019 |

### **C++ Standard**
```
C++17 minimum (C++20 recommended)
```

### **Build System**
- CMake >= 3.15 (recommended)
- OR direct compilation

### **Compilation Example**

```bash
# Linux/macOS
g++ -std=c++17 -I./include -L./target/release \
  -Wl,-rpath,./target/release \
  -o my_quantum_app my_quantum_app.cpp \
  -labirqu_core -lm

# Windows (MSVC)
cl.exe /std:c++17 /I.\include \
  /link abirqu_core.lib
```

---

## 🐧 System-Level Dependencies

### **Linux (Ubuntu/Debian)**

```bash
sudo apt-get update
sudo apt-get install -y \
  build-essential \
  cmake \
  python3-dev \
  python3-pip \
  curl \
  git \
  rustup \
  golang-go \
  openjdk-11-jdk \
  libssl-dev \
  pkg-config

# Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
rustup default stable
```

### **macOS (Homebrew)**

```bash
brew install python@3.11 rust go cmake

# Java (optional)
brew install openjdk@11

# Node.js (optional)
brew install node
```

### **Windows (Chocolatey)**

```powershell
choco install python rustup golang cmake visualstudio2019-community

# Node.js (optional)
choco install nodejs
```

---

## 📊 Hardware Requirements

### **Minimum**
- CPU: Dual-core 2GHz
- RAM: 4GB
- Storage: 1GB (500MB after cleanup)
- OS: Windows 10+, macOS 10.15+, Linux 5.0+

### **Recommended**
- CPU: Quad-core 2.5GHz+ (better for multi-threaded compilation)
- RAM: 8GB+ (important for 20+ qubit simulation)
- Storage: 10GB (allows room for builds, caches)
- GPU: Optional (future CUDA/Metal support)

### **Development**
- RAM: 16GB+ (for full cross-language build)
- CPU: 8+ cores (fast compilation)
- SSD: 50GB (project + multiple language toolchains)

---

## 🔧 Docker Installation

### **Complete Environment in Container**

```dockerfile
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    python3.11 python3-pip \
    rustup build-essential \
    golang-go openjdk-11-jdk \
    curl git cmake pkg-config

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Clone AbirQu
RUN git clone https://github.com/abirqu/abirqu.git /abirqu
WORKDIR /abirqu

# Install Python SDK
RUN python3 -m pip install -e ".[dev]"

# Build all
RUN cargo build --release
RUN cd js && npm install && npm test
RUN cd go/abirqu && go test ./...

CMD ["bash"]
```

### **Build Docker Image**

```bash
docker build -t abirqu:latest .
docker run -it abirqu:latest
```

---

## ✅ Verification Checklist

After installation, verify all dependencies:

```bash
# Python
python3 -c "import numpy, scipy, matplotlib; print('✅ Python OK')"

# Rust
cargo --version && rustc --version

# JavaScript
node --version && npm --version

# Go
go version

# Java (if used)
java -version

# Run tests
pytest tests/ -q
cargo test --lib -q
cd js && npm test
cd go/abirqu && go test ./...
```

---

## 🆘 Troubleshooting

### **Issue**: `ModuleNotFoundError: No module named 'numpy'`
```bash
pip install --upgrade numpy scipy
```

### **Issue**: `error: could not compile 'abirqu'`
```bash
# Update Rust
rustup update
rustup default stable

# Clean and rebuild
cargo clean
cargo build --release
```

### **Issue**: `ImportError: cannot import name 'build'`
```bash
pip install --upgrade maturin
maturin develop --release
```

### **Issue**: `cgo: cannot find -labirqu_core`
```bash
# Build Rust library first
cargo build --release

# Set library path
export LD_LIBRARY_PATH=$PWD/target/release:$LD_LIBRARY_PATH
```

---

**Total Installation Size**: ~1GB (Python + Rust + JS + Go)
**Cleanup Size**: ~311MB (sources only, no build artifacts)
