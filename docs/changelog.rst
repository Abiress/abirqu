Changelog
=========

Version 1.0.0
-------------

*Initial release*

**Core**
- ``Circuit`` class with full gate set (single-qubit, two-qubit, parameterized)
- ``QuantumRun`` unified execution primitive (Sampler, Estimator, QNN)
- 12 hardware backends: IBM, D-Wave, AWS Braket, Azure, Google, IonQ, Rigetti, Quantinuum, Pasqal, OQC, QuEra, SpinQ
- 5 simulation engines: NumPy, GPU (CuPy), Clifford, MPS, Monte Carlo

**Transpiler**
- ``TranspilerPipeline`` with routing, scheduling, and fidelity passes
- ``CouplingMap`` for hardware topology
- Gate decomposition for multiple target architectures

**Circuit Library**
- QAOA, VQE, Grover, QFT, GHZ, W-state, random circuits
- Encoding: angle, amplitude, ZZ feature map, IQP
- Hardware-efficient ansatz, UCCSD

**Quantum OS**
- Job scheduling with FIFO, priority, fair-share policies
- Resource management and cost estimation
- Virtual QPU abstraction

**Domain Modules**
- Quantum chemistry: Jordan-Wigner, Bravyi-Kitaev, VQE hooks
- OSINT: Intelligence graph, quantum data encoding
- Cryptanalysis: Oracle synthesis, lattice simulation
- Space: HHL linear solver, Q-PINNs for PDEs

**QEC**
- Surface code, color code, stabilizer codes
- LDPC codes, lattice surgery, magic state distillation
- Fault-tolerant compiler

**Communication**
- BB84, E91, BBM92, B92, six-state, quantum teleportation, superdense coding

**Visualization**
- Circuit text/SVG/HTML drawing
- Bloch sphere, histograms, state plots
- Gate maps, error maps, noise fingerprints

**Security**
- Circuit encryption and signing
- Access control

**Noise**
- Noise model (depolarizing, amplitude damping, phase damping, thermal)
- ZNE, readout mitigation, M3, PEC
