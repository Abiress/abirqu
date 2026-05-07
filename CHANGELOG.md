# Changelog

## v0.1.0 (Initial Release)

### Working Features
- Rust-accelerated statevector simulator (fastest at ≤16q)
- NumPy fallback simulator (bit-exact with Rust)
- Circuit construction API (30-50% faster than Qiskit/Cirq)
- Density matrix simulator with Kraus operators
- Measurement and sampling engine
- Basic noise models (depolarizing, amplitude damping, readout error)
- Surface code and LDPC code infrastructure
- QASM export
- Circuit visualization (ASCII)

### Benchmarked Against
- Qiskit 1.x with AerSimulator (forced statevector)
- Cirq 1.x with cirq.Simulator
- All benchmarks on Intel i9-13900H, 30GB RAM, Linux
- Full benchmark data in benchmark_results/

### Known Issues
- 20q+ simulation slower than Cirq (MKL advantage)
- Optimizer limited to peephole rules
- No GPU native kernels
- Hardware backends need production testing
