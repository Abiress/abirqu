# AbirQu Roadmap (Reality-Based, Full Phase Coverage)

Version: 2026-05-11

This roadmap is intentionally practical and evidence-driven.
No item is treated as production-ready unless it passes the validation gate defined below.

## Validation Gate (What "100% True Working" Means)

A feature is marked fully working only when all conditions are met:

1. Code exists in the main repository and imports cleanly.
2. Local execution path works with deterministic smoke checks.
3. Error paths are graceful (clear messages, no hard crashes for missing credentials/deps).
4. Compatibility checks pass for the claimed formats/backends.
5. Security controls are present where required, including AbirGuard for protected flows.
6. Release artifacts and docs reflect the same behavior.

## Current Verified Snapshot

As of this update:

1. Python package import is working (`import abirqu`).
2. Repository-wide module import sweep passed (excluding optional binary extension module loader mismatch).
3. Compatibility summary command passes runtime checks for:
   - OpenQASM2
   - OpenQASM3
   - QASM-XT
   - QIR
   - Quil
4. Reported compatibility counts:
   - Languages: 10
   - Hardware adapters: 11
   - Interchange formats: 5
   - Plugin capabilities: 5
5. AbirGuard implementation exists at `abirqu/cloud/abir_guard.py` and is wired in phase security workflows (not yet claimed as complete end-to-end coverage for every cloud path).

## Compatibility Program (Practical Delivery)

### C1 Language Compatibility

Status target: keep all currently supported language bindings buildable from source and runnable with minimal examples.

1. Python
2. Rust
3. C/C++
4. JavaScript/Node
5. Java
6. Kotlin
7. Go
8. .NET
9. Swift
10. WebAssembly/browser path (partial in current snapshot; explicit completion target below)

### C2 Hardware Compatibility

Status target: adapter path functional + credential validation + one reproducible job path per provider.

1. Local simulator (complete baseline)
2. IBM
3. Google
4. AWS Braket
5. Azure Quantum
6. IonQ
7. Rigetti
8. Quantinuum
9. Pasqal
10. OQC
11. QuEra

### C3 Interchange Compatibility

Status target: round-trip conversions plus runtime checks for each format.

1. OpenQASM2
2. OpenQASM3
3. Quil
4. QASM-XT
5. QIR

### C4 Plugin Compatibility

Status target: stable plugin API, discovery, credential handling, normalized results, and native transpilation flow.

### C5 AbirGuard Compatibility (New Program)

Status target: all security-sensitive workflows use AbirGuard where applicable.

1. Protected key lifecycle for hybrid and cloud execution flows.
2. Encrypted result transport options where provider APIs allow.
3. Policy checks before dispatching remote jobs.
4. Security audit log schema integrated with execution metadata.
5. Validation scripts for guard policy enforcement.

## Full Phase Coverage (1-40)

Legend:
- Complete Baseline: code present and currently practical for local execution paths.
- Practical In Progress: code exists, requires broader validation/hardening.
- Prototype/Research: exploratory, not yet production-validated.

| Phase | Title | Current State | 2026-2027 Practical Target |
|---|---|---|---|
| 1 | Core Engine | Complete Baseline | Keep stable API and deterministic simulator checks |
| 2 | Optimization Engine | Practical In Progress | Validate optimizer quality on reproducible benchmark set |
| 3 | Error Correction | Practical In Progress | Harden decoder/runtime integration and publish benchmark protocol |
| 4 | Design Patterns | Practical In Progress | Add conformance examples per pattern |
| 5 | Workflow Automation | Practical In Progress | Stabilize orchestration utilities and examples |
| 6 | Backend Connectors | Practical In Progress | Per-provider validated job flow with credential diagnostics |
| 7 | Developer Experience | Practical In Progress | CLI and docs consistency gates in CI |
| 8 | Visualization and Analysis | Practical In Progress | Export/report API compatibility tests |
| 9 | Hybrid Runtime | Practical In Progress | Reproducible hybrid loop examples |
| 10 | Quantum Networking | Prototype/Research | Formalize simulation assumptions and test vectors |
| 11 | Testing and Verification | Practical In Progress | Rebuild top-level regression suite and enforce pass threshold |
| 12 | Algorithm Discovery | Prototype/Research | Add deterministic research harness with fixed seeds |
| 13 | Sensing and Metrology | Prototype/Research | Document model boundaries and calibration assumptions |
| 14 | Novel Architectures Compilation | Prototype/Research | Add architecture-specific validation fixtures |
| 15 | Quantum OS Runtime | Prototype/Research | Define production scope and minimal operable subset |
| 16 | Education Platform | Practical In Progress | Ship runnable tutorial set with versioned outputs |
| 17 | Resource Estimation | Practical In Progress | Cross-check estimates vs reference datasets |
| 18 | Memory Management | Practical In Progress | Validate compression/error bounds on reference circuits |
| 19 | Advanced Algorithms | Practical In Progress | Maintain algorithm smoke suite across canonical problems |
| 20 | GPU Acceleration | Practical In Progress | Device matrix validation (CPU fallback always reliable) |
| 21 | Benchmarking | Practical In Progress | Reproducible benchmark manifest and report schema |
| 22 | Error Mitigation | Practical In Progress | Add mitigation comparison baselines |
| 23 | Advanced Extensions | Prototype/Research | Promote validated modules into practical tier |
| 24 | Quantum ML | Practical In Progress | Standardized dataset/metric harness |
| 25 | Quantum Learning Integration | Prototype/Research | Clearly separate research modules from production APIs |
| 26 | Quantum Chemistry | Practical In Progress | Canonical molecule benchmark pack |
| 27 | Advantage Measurement | Practical In Progress | Publish strict claims policy and confidence intervals |
| 28 | Secure Distributed Execution | Practical In Progress | Expand AbirGuard coverage across distributed flows |
| 29 | Post-Quantum Security | Practical In Progress | AbirGuard end-to-end reference pipeline |
| 30 | Hardware Capability Layer | Practical In Progress | Complete provider capability probe matrix |
| 31 | Quantum Internet and Inter-Planetary Simulation | Prototype/Research | Scenario libraries with reproducible assumptions |
| 32 | Biological Quantum Simulation | Prototype/Research | Mark all outputs as model-estimated until validated |
| 33 | Autonomous Quantum Control | Prototype/Research | Hardware-in-the-loop validation plan |
| 34 | Q-AGI Concepts | Prototype/Research | Keep as concept track, no production claims |
| 35 | Space-Time and High-Energy Simulation | Prototype/Research | Physics model validation scope document |
| 36 | Plugin Marketplace and Extensibility | Practical In Progress | Signed plugin metadata and compatibility checks |
| 37 | Heterogeneous Orchestration | Practical In Progress | Multi-provider dry-run plus live-run checkpoint gates |
| 38 | Dynamic Circuit Runtime | Practical In Progress | Mid-circuit control-flow validation fixtures |
| 39 | Developer Tooling Suite | Practical In Progress | Lint/debug quality gates integrated in CI |
| 40 | Extreme-Scale Compression | Prototype/Research | Quantified fidelity-memory tradeoff reports |

## AbirGuard Integration Plan

### Track A: Security Surface Standardization

1. Define a single security contract used by cloud execution, plugins, and distributed orchestration.
2. Route credential-dependent operations through validated guard checks.
3. Add policy mode (`strict`, `balanced`, `off`) with explicit runtime behavior.

### Track B: Runtime Enforcement

1. Pre-dispatch policy validation for remote providers.
2. Key management wrappers for post-quantum primitives.
3. Structured security events attached to execution results.

### Track C: Compatibility and Verification

1. Add compatibility checks to ensure guard behavior does not break C1-C4 guarantees.
2. Add AbirGuard smoke scenarios for local, simulated cloud, and plugin flows.
3. Add release checklist requiring guard tests for security-affected changes.

## Upcoming Features (Practical, Measurable)

### Near Term

1. Restore a top-level regression test pack in repository and wire it to CI.
2. Complete WASM/browser path verification (build + minimal runtime example).
3. Harden all provider adapters with consistent missing-credential guidance.
4. Add compatibility evidence artifacts (machine-readable JSON + human report).

### Mid Term

1. Provider live-validation matrix for IBM/AWS/Azure/IonQ/Google with reproducible scripts.
2. Benchmark reproducibility toolkit with fixed seeds and reference hardware profiles.
3. AbirGuard enforcement for phase 28/29/37 execution paths.
4. Plugin signing and trust policy support.

### Long Term

1. Promote selected prototype phases (31-40) to practical tier only after passing validation gate.
2. Publish a strict claim policy for performance and quantum-advantage statements.
3. Expand operational telemetry and incident response playbooks for production contexts.

## Release Truth Policy

For every release, all claims in docs must map to one of:

1. Verified: tested and reproducible in repo.
2. SDK-wired: integration path exists, live provider validation may still be required.
3. Prototype/Research: exploratory, not production-validated.

Any claim without evidence is removed before release.
