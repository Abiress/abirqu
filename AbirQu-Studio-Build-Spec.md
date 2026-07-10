# AbirQu Studio — IDE + CLI Build Specification
### A native GUI and CLI for the AbirQu Quantum SDK (github.com/Abiress/abirqu)

This spec is written to be handed directly to an agentic coding platform. It is grounded in AbirQu's **actual** module layout (Python package `abirqu`, plus C/C++, Rust, JS, Kotlin, Swift, Java bindings in the same repo) — every panel and CLI command below maps to a real module that already exists in the SDK, not a hypothetical one. Where AbirQu doesn't yet expose something an IDE needs (e.g. a job-history REST endpoint), that gap is called out explicitly as "**NEW — build this**."

---

## 0. What already exists in `Abiress/abirqu` (do not rebuild these)

The SDK is **pure NumPy/OpenBLAS**, so the GUI does not need a heavy compiled backend — it needs a **thin service layer** around the existing Python package. Confirmed top-level modules from the repo:

```
abirqu/
  primitives/          QuantumRun, Sampler, Estimator, QNN, MitigationResult
  library/              RealAmplitudes, EfficientSU2, N-local, QAOA, VQE (UCCSD/HW-eff),
                         ZZFeatureMap, IQP/Angle/Amplitude encoding, GHZ, W, QFT, Grover,
                         Bernstein-Vazirani, random_circuit
  visualization/         CircuitDrawer (text/ascii/svg/html), BlochSphere, histogram_text/svg,
                         stateplot_svg, probability_svg, gate_map_svg, error_map_svg,
                         noise fingerprint, circuit fingerprint
  noise_toolkit/         ZeroNoiseExtrapolator, Gate Folding ZNE, ReadoutMitigator,
                         EnhancedReadoutMitigator, M3Mitigator, PECCorrector, calibration circuits
  addons/                MultiProductFormula, TrotterSuzuki, CircuitCutter, AQCTensor,
                         OperatorBackpropagation, SQDCorrector
  unitary_synthesis/     synthesize_unitary, ScalableUnitarySynthesizer
  adaptive_mitigation/   AdaptiveErrorMitigator, NoiseProfiler, DriftMonitor, StrategySelector
  pulse_translator/       AutomatedPulseEngine, PulseTranslator, PulseScheduler, PulseOptimizer
  dynamic_circuit/        DynamicCircuitSimulator, ForLoop/WhileLoop, StreamingCircuitEngine,
                         VQEParameterPrefetcher
  optimize/noise_adaptive  4-pass noise-adaptive compiler (novel)
  qnlp/spae               SPAE stochastic-phase encoding (novel)
  entanglement_cutting/    Entanglement-aware circuit cutting (novel)
  simulation/hybrid        Hybrid MPS-Clifford simulator (novel)
  simulation/               GPU / Clifford / MPS / Monte Carlo simulators, ode_solver, waveform
  numpy_sim/                 Pure-NumPy portable statevector fallback
  hardware/                  calibration, characterization (RB/interleaved RB/tomography/SPAM),
                         hw_compiler (HardwareAwareCompiler + CompilationTarget), cloud_manager
  qec/                        codes (Repetition/BitFlip/PhaseFlip/Shor/Steane/Surface/Color/LDPC),
                         decoder (5 decoders), magic_state (T/H-state distillation)
  quantum_communication/     bb84, e91, cv_qkd, di_qkd, satellite, repeaters, network
  quantum_os/                 QuantumScheduler, JobQueue (SQLite), ResourceManager, VirtualQPU,
                         CostEstimator, PreemptionManager, ReservationSystem,
                         CircuitPartitioner, VirtualEnvironment, JobMonitor, TenantManager,
                         AccessController
  cloud/abir_guard/           Kyber-768 KEM, Dilithium-2, SPHINCS+-128f, BB84 QKD, circuit encryption
  transpiler/                 target-aware decomposition, CouplingMap, RoutingPass,
                         SchedulingPass, FidelityEstimator
  formats/                     OpenQASM 2/3, Quil, QIR, QASM-XT (import/export)
  dag_circuit/                 DAG compile-once + O(k) parameter rebind, parameter-shift gradients
  quantum_optimizer/           COBYLA, SPSA, Adam, gradient descent, Nelder-Mead, VQE/QAOA loops
  patterns/                     pattern detection + pattern-aware optimizer
  tracker/                     quantum-advantage tracker
  compatibility/                 language/hardware compatibility checks
  security/                     circuit encryption
  plugins/                     entry-point auto-discovery, credential management
  mitigation/                    readout + ZNE pipeline
  industry/                     QAOA portfolio optimization, VQE Hubbard, VRP annealing
  chemistry/                     JordanWigner/BravyiKitaev/Parity mappers, PySCFHook,
                         MolecularData, MatchgateShadows
  osint/                         IntelligenceGraph, GraphToIsingCompiler (6 problems),
                         build_qaoa_circuit, analyze_graph, QuantumDataEncoder, QRAMEmulator,
                         TensorNetworkEmbedding
  crypto/                         OracleSynthesizer, ModularArithmetic, LatticeSimulation
                         (Kyber/Dilithium), quantum_vulnerability_assessment
  space/                         HHLSolver, solve_cfd_linear_system, solve_structural_stress
  qpinn/                         QPINN, PDESpec, NavierStokesQPINN, Adam optimizer
  agentic/                       AgentOrchestrator, batch_execute, MultiGPUSimulator,
                         DistributedQuantumComputer
  backend/                     QuantumBackend abstract base + 12 hardware adapters
                         (IBM, AWS, Azure, Google, IonQ, Rigetti, Quantinuum, Pasqal, OQC,
                          QuEra, D-Wave, SpinQ)
```
Also present at repo root: `dotnet/`, `go/abirqu/`, `java/`, `js/`, `kotlin/`, `swift/`, `rust/src/`, `include/` (C ABI header), `jni/include/` — i.e. multi-language bindings already scaffolded, several marked "Planned" in the README's Compatibility Roadmap. The IDE/CLI spec below treats **Python as the source of truth** and the other languages as future binding targets, consistent with the repo's own roadmap.

---

## 1. Product Definition

**AbirQu Studio** = one desktop application with two faces:
- **GUI** — a VS-Code-style IDE for writing, visualizing, simulating, and executing AbirQu circuits.
- **CLI** — `abirqu` command-line tool, scriptable and CI/CD-friendly, sharing the exact same core logic as the GUI (no duplicated business logic).

Both talk to a single **AbirQu Core Service** (a local Python process) so the GUI is never "reimplementing" SDK behavior — it only visualizes and orchestrates calls into the real `abirqu` package.

```
┌────────────────────────────┐     ┌──────────────────────────────┐
│   AbirQu Studio (GUI)      │     │   abirqu CLI (Typer/Click)   │
│   Tauri + React/TypeScript │     │   Python, ships in same venv │
└─────────────┬───────────────┘     └───────────────┬───────────────┘
              │  local IPC / HTTP (loopback only)     │ direct import
              ▼                                        ▼
        ┌──────────────────────────────────────────────────┐
        │        AbirQu Core Service (FastAPI, Python)      │
        │  thin orchestration layer — imports `abirqu` pkg  │
        │  directly. No reimplementation of SDK internals.  │
        └───────────────┬────────────────────────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  abirqu (SDK)   │  ← the actual GitHub repo, installed as a dependency
                 └─────────────────┘
```

---

## 2. GUI Architecture & Stack

| Layer | Choice | Reason |
|---|---|---|
| Shell | **Tauri (Rust)** | small binary, native menus/window chrome, cross-platform (Win/macOS/Linux) |
| UI | **React 18 + TypeScript + Vite** | component reuse, fast dev loop |
| Styling | **Tailwind CSS** + design tokens (see §5) | consistent theming, dark/light |
| Docking/resizable tabs | **`dockview`** (or `rc-dock`/`golden-layout` as fallback) | VS-Code-grade dockable, resizable, tabbed panel system out of the box — don't hand-roll this |
| Code editor | **Monaco Editor** with custom language definitions for OpenQASM 2/3, Quil, QIR (AbirQu already parses these via `abirqu.formats`) | IntelliSense, minimap, multi-cursor, matches VS Code muscle memory |
| Circuit canvas | **Konva.js** (Canvas2D, retained-mode) for the drag-and-drop gate grid | performant at 50+ qubit circuits, easy hit-testing per gate |
| 3D (Bloch sphere) | **Three.js**, fed by `abirqu.visualization.BlochSphere` SVG/data output converted to a live 3D scene (not just the static SVG) | the SDK already computes the sphere math — GUI just needs to animate it |
| 2D charts | **D3.js** or **Plotly.js** for histogram/probability/error-map/noise-fingerprint panels | AbirQu's `visualization` module returns SVG for these — render server SVG directly for v1, upgrade to native D3 renders in v2 for interactivity (hover tooltips on error-map cells, etc.) |
| State | **Zustand** (client) + **TanStack Query** (server cache of job/circuit/hardware state) | |
| Local process bridge | **Tauri's `sidecar`** feature to spawn/manage the Python `AbirQu Core Service` as a child process | user never manually starts a server |
| Realtime | **WebSocket** for job queue / hardware queue / simulation progress streaming (`abirqu.quantum_os.JobMonitor`) | |

---

## 3. UI/UX — Window Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ File  Edit  View  Circuit  Run  Hardware  Chemistry  Security  Help  │  ← Menu bar
│  ⌘K Command Palette          🔍 Search        🌓 Theme     ⚙        │
├───────┬──────────────────────────────────────────────┬────────────────┤
│       │ [ bell.qasm ✕] [ circuit.py ✕] [ Circuit  ]   │  INSPECTOR      │
│  A    │──────────────────────────────────────────────│  ────────────  │
│  C    │                                                │  Gate props    │
│  T    │      CODE  ▏  CIRCUIT DESIGNER (synced)        │  Backend info  │
│  I    │                                                │  Fidelity est. │
│  V    │      (resizable split — drag divider)          │  ────────────  │
│  I    │                                                │  AI ASSISTANT  │
│  T    │                                                │  (optional,    │
│  Y    │                                                │   see §8)      │
│       │                                                │                │
│  B    ├──────────────────────────────────────────────┴────────────────┤
│  A    │  BOTTOM DOCK (tabbed, resizable height)                        │
│  R    │  [Results] [Bloch Sphere] [Job Queue] [Terminal] [Problems]    │
├───────┴──────────────────────────────────────────────────────────────┤
│ Status bar: ● abirqu 1.0.0 | Sim: MPS (CPU) | Backend: IBM (idle) | Qubits: 5│
└──────────────────────────────────────────────────────────────────────┘
```

### Activity Bar (left icon rail — each opens a full docked panel)
1. **Explorer** — project files, `.qasm`/`.py`/`.abirqu` project tree
2. **Circuit Designer** — drag-and-drop canvas (§4.2)
3. **Simulation** — engine selector + run controls (§4.3)
4. **Hardware** — 12-backend browser, calibration, queue (§4.4)
5. **Visualization** — Bloch sphere / histograms / heatmaps gallery (§4.5)
6. **Noise & Mitigation** — ZNE/M3/PEC/adaptive mitigation controls (§4.6)
7. **QEC Lab** — code selection, decoder, syndrome view (§4.7)
8. **Quantum Comm** — BB84/E91/QKD protocol runner (§4.8)
9. **Domain Modules** — Chemistry / OSINT / Crypto / Space / Q-PINN / Agentic (§4.9)
10. **Quantum OS / Jobs** — scheduler, queue, cost estimator (§4.10)
11. **Security (AbirGuard)** — Kyber/Dilithium/SPHINCS+/QKD key management (§4.11)
12. **Plugins & Marketplace** — plugin discovery, install, credentials (§4.12)
13. **Ask Quantum (NL2Q)** — natural-language question → circuit → quantum answer → plain-English answer, full pipeline (§4.13, see §11 for architecture)
14. **Settings**

Every panel is **dockable and resizable** (drag to any edge, split, pop out to a second window) via `dockview`. Users can save a **Workspace Layout** (e.g. "Chemistry Lab" layout vs "Hardware Benchmarking" layout) and switch between saved layouts from the View menu.

### Tab & Split Behavior
- Tabs support drag-reorder, drag-to-split (creates a new resizable pane), and drag-out (pop into a new OS window — useful for a second monitor showing a live Bloch sphere during a long VQE run).
- **Code ↔ Circuit sync**: editing `.qasm`/Python circuit code live-updates the Circuit Designer canvas and vice versa (bridge through `abirqu.formats` parse/serialize + `abirqu.visualization.CircuitDrawer`).
- Every resizable divider persists its position per-workspace (saved to local settings, not just session memory).

---

## 4. Panel-by-Panel Spec (mapped to real `abirqu` calls)

### 4.1 Menu Bar
- **File**: New Project / New Circuit / Open / Save / Export (QASM2/QASM3/Quil/QIR/Qiskit/Braket/Cirq/IonQ-JSON/Pytket via `abirqu.formats` + `to_qiskit()/to_braket()/to_cirq()/to_ionq_json()/to_pytket()/to_quil()/to_openqasm()`)
- **Circuit**: Insert Template (GHZ/W/QFT/Grover/Bernstein-Vazirani/Random from `abirqu.library`), Validate, Optimize (pattern-aware optimizer), Show Fingerprint
- **Run**: Run on Simulator, Run on Hardware, `QuantumRun` Quick-Run (sampling+estimation+mitigation+ML in one call), Stop
- **Hardware**: Manage Credentials (`CloudManager`), Select Backend, View Calibration
- **Chemistry / Security / etc.**: jump shortcuts into domain-module panels

### 4.2 Circuit Designer
- Drag gates from a palette (H, X, Y, Z, S, T, RX/RY/RZ, CNOT, CZ, Toffoli, SWAP, custom unitary) onto a wire grid.
- Parametric gates show an inline slider/number field bound to a circuit parameter (feeds `abirqu.dag_circuit` for O(k) rebind during VQE/QAOA tuning).
- **Template insert menu**: RealAmplitudes, EfficientSU2, N-local (with entanglement pattern: full/linear/circular/sca/pairwise), QAOA ansatz, VQE (hardware-efficient / UCCSD), ZZFeatureMap, IQP/Angle/Amplitude encoding, GHZ, W, QFT, Grover, Bernstein–Vazirani, Random circuit — all straight from `abirqu.library`.
- **Live circuit fingerprint** strip along the canvas edge (barcode visualization, unique to AbirQu) updates as gates are added.
- Dynamic-circuit support: mid-circuit measurement box, classical-feedback arrows, For/While loop containers (`abirqu.dynamic_circuit`).
- Right-click a gate → "Explain," "Show native decomposition for [backend]," "Remove," "Convert to custom unitary."

### 4.3 Simulation Panel
- Engine selector: **NumPy** (portable fallback) / **GPU** (CuPy) / **Clifford** (stabilizer tableau) / **MPS** (tensor network, up to 127K+ qubits per README benchmarks) / **Monte Carlo** (open-system trajectories) / **Hybrid MPS-Clifford** (novel).
- Shots field, seed field, "Run" button → calls `QuantumRun(circuit, shots=..., backend=...)`.
- Live progress bar fed by simulation callbacks (**NEW — build this**: AbirQu's simulators don't currently emit progress events; add a lightweight callback/observer hook in the Core Service wrapper, not in the SDK itself, unless the maintainer wants it upstreamed).
- Time-evolution mode: Hamiltonian builder UI (rotations/detuning/exchange/Ising/transverse-field) → `abirqu.simulation.ode_solver` RK4/RK45/Euler/Lindblad.

### 4.4 Hardware Panel
- Grid of the **12 backends** (IBM, AWS Braket, Azure, Google, IonQ, Rigetti, Quantinuum, Pasqal, OQC, QuEra, D-Wave, SpinQ) with connection status pulled from `abirqu.hardware.cloud_manager.CloudManager.get_connected_providers()`.
- Per-backend detail view: T1/T2 table, gate error rates, readout error, crosstalk matrix — from `HardwareCalibration` + `DeviceCharacterizer` (RB, interleaved RB, process tomography, SPAM).
- "Compile for this backend" button → `HardwareAwareCompiler.compile()`, shows estimated fidelity report inline.
- Credential setup wizard writes to `.env` (mirrors the README's `IBM_QUANTUM_TOKEN`, `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`, `AZURE_QUANTUM_RESOURCE_ID`, `IONQ_API_KEY`, `GOOGLE_CLOUD_PROJECT`, etc.) — never shown in plaintext after entry.
- **NEW — build this**: a unified "Cost Estimator" card per backend, wiring the panel to `abirqu.quantum_os.CostEstimator` before a hardware run is confirmed.

### 4.5 Visualization Gallery
- Tiles: Bloch Sphere (3D, multi-qubit partial trace), State/City Plot (phase-colored amplitudes), Probability Histogram, Density Matrix, Gate/Coupling Map, Error Heatmap, **Noise Fingerprint** (unique), **Circuit Fingerprint** (unique).
- All backed directly by `abirqu.visualization` functions; GUI's job is to fetch the SVG/data payload and render it (Three.js for Bloch sphere so it's interactively rotatable, not just a static SVG).
- Export any visualization as SVG/PNG/HTML.

### 4.6 Noise & Mitigation Panel
- ZNE controls: extrapolation method (Richardson/linear/exponential), gate-folding toggle, run pipeline (`ZeroNoiseExtrapolator`, fold→execute→extrapolate).
- Readout mitigation: basic `ReadoutMitigator`, `EnhancedReadoutMitigator` (Tikhonov + per-qubit + bootstrap CI), `M3Mitigator` (matrix-free, scalable).
- `PECCorrector` toggle for probabilistic error cancellation.
- **Adaptive Error Mitigation** big button: "Auto-mitigate" → `AdaptiveErrorMitigator` auto-profiles noise (`NoiseProfiler`), tracks drift (`DriftMonitor`), and picks a strategy (`StrategySelector`) with zero manual config — surface its chosen strategy and reasoning in the UI so it's not a black box.

### 4.7 QEC Lab
- Code picker: Repetition, Bit-flip, Phase-flip, Shor [[9,1,3]], Steane [[7,1,3]], Surface (distance 3/5/7), Color, LDPC.
- Encode → syndrome injection (manual or random error) → decoder selector (Syndrome Lookup, Surface-code MWPM-inspired, Belief Propagation, MWPM, GPU-accelerated BP) → visual syndrome/correction display.
- Magic State Distillation panel: 15-to-1 T-state and 20-to-4 H-state distillers, T-gate injection via magic-state teleportation.

### 4.8 Quantum Communication Panel
- Protocol runner: BB84, E91 (shows live CHSH S-value, should trend to 2.828), CV-QKD, DI-QKD, Satellite QKD (atmospheric loss model), Repeater Chains (DEJMPS purification + entanglement swapping), Quantum Network (star/ring/mesh topology visual + routing).
- Sifted-key length and QBER (quantum bit error rate) displayed live per run.

### 4.9 Domain Modules
- **Chemistry**: Molecule picker (H2/LiH/H2O presets from `MolecularData`, or PySCF-connected custom molecule via `PySCFHook`), mapper selector (Jordan-Wigner/Bravyi-Kitaev/Parity), VQE ansatz picker (UCCSD/hardware-efficient), live energy-convergence chart during optimization, Matchgate Shadows tomography readout.
- **OSINT & Intelligence**: `IntelligenceGraph` builder (node/edge canvas), problem picker (Max-Cut/MIS/MVC/Coloring/Community/Anomaly) → `GraphToIsingCompiler`, one-click QAOA circuit generation, graph analytics sidebar (density, avg degree, clustering, diameter).
- **Cryptanalysis & PQC**: Grover oracle synthesis form, Shor circuit builder (factoring target N), Kyber-512/768/1024 and Dilithium-2/3/5 keygen buttons, one-click `quantum_vulnerability_assessment` report (Grover feasibility + quantum BKZ complexity).
- **Space & Deep Tech**: HHL solver form (matrix A, vector b input, or CFD grid-size/viscosity, or structural stiffness matrix), residual-norm readout.
- **Q-PINN**: PDE spec builder (name/dimension/domain/time-domain), live loss curve during training, forward-evaluation probe tool.
- **Agentic Orchestration**: task submission form (6 task types), live task-status board, batch execution queue, Multi-GPU / Distributed QPU topology view.

### 4.10 Quantum OS / Job Manager
- Live job queue table (FIFO/priority/SJF/fair-share, from `QuantumScheduler` + `JobQueue` SQLite backing).
- Resource utilization gauges (`ResourceManager`), Virtual QPU allocation view, reservation calendar (`ReservationSystem`).
- Cost estimator side panel (`CostEstimator`) shown before submitting any hardware job.
- Multi-tenant view (org admins only): `TenantManager` + `AccessController` RBAC editor.

### 4.11 Security (AbirGuard)
- Keypair generation UI for Kyber-768, Dilithium-2, SPHINCS+-128f.
- BB84 QKD key-exchange demo runner.
- "Encrypt this circuit before cloud submission" toggle, wired to `abirqu.cloud.abir_guard` circuit encryption — surfaced wherever a circuit is about to leave the local machine toward a cloud backend.

### 4.12 Plugins & Marketplace
- Lists auto-discovered plugins (`abirqu.plugins.PluginDiscovery`), install/uninstall, credential fields per plugin.
- **NEW — build this**: a hosted plugin marketplace/registry is not part of the current SDK; local entry-point discovery is. v1 ships local-only; a hosted registry is a v2 commercial feature (see §9).

### 4.13 Ask Quantum (NL2Q Panel)

A single chat-style input box: *"What's the ground-state energy of LiH?"* / *"Find the best route through these 8 delivery stops"* / *"Is a 2048-bit RSA key safe from a quantum attacker?"* / *"Factor 91."* The panel does **not** just chat back — it shows its work as a **6-step visible trace**, each step expandable, each step's output independently editable/re-runnable before moving to the next:

```
┌─ Ask Quantum ──────────────────────────────────────────────────┐
│ 💬 "Find the ground state energy of LiH"                        │
├───────────────────────────────────────────────────────────────┤
│ ① Understood as: Chemistry / Ground-state energy problem        │
│    Molecule: LiH   Mapper: Jordan-Wigner   Confidence: 94%      │
│    [ Edit interpretation ▾ ]                                    │
├───────────────────────────────────────────────────────────────┤
│ ② Problem formalized: 4-qubit Hamiltonian (12 Pauli terms)      │
│    [ View Hamiltonian ]                                          │
├───────────────────────────────────────────────────────────────┤
│ ③ Circuit generated: VQE, UCCSD ansatz, 4 qubits, depth 18       │
│    [ Open in Circuit Designer ]  [ Explain this circuit ]        │
├───────────────────────────────────────────────────────────────┤
│ ④ Execution plan: MPS simulator, 200 COBYLA iterations           │
│    Est. cost: $0 (local sim)     [ Change backend ]  [ Run ]     │
├───────────────────────────────────────────────────────────────┤
│ ⑤ Raw result: E = -1.1372 Ha, converged in 143 iterations         │
│    [ View convergence chart ] [ View final statevector ]          │
├───────────────────────────────────────────────────────────────┤
│ ⑥ Answer: "The estimated ground-state energy of LiH is           │
│    -1.137 Hartree (-30.95 eV), computed via VQE with a UCCSD      │
│    ansatz on 4 qubits. This is within 3 mHa of the reference      │
│    FCI value, consistent with simulator-level precision."         │
│    [ Copy answer ] [ Export full report (PDF/HTML) ]              │
└───────────────────────────────────────────────────────────────┘
```

Rules the coding agent must follow when building this panel:
- **Nothing runs on real hardware without step ④'s "Run" being explicitly clicked** — the LLM proposes, it never auto-executes anything that costs money or hardware queue time.
- Every step's intermediate artifact (Hamiltonian, circuit, backend choice) is user-editable before proceeding — this is a *guided pipeline*, not an opaque chatbot.
- Low-confidence interpretations (step ①) must surface a disambiguation prompt instead of silently guessing (e.g. "Did you mean the H2O molecule, or are you asking about water as a solvent model?").
- The final answer (step ⑥) always cites which algorithm and which circuit produced it, and states precision/confidence caveats — never a bare number with no provenance.

See **§11** for the full backend architecture behind this panel.

---

## 5. Design System

- **Typography**: Inter (UI), JetBrains Mono (code/QASM, with ligatures for `→`, bra-ket `⟨ ⟩`).
- **Color**: true-neutral base (`#1a1b1e` dark / `#fafafa` light); a single shared red→green scale for every error-rate visualization (calibration table, error heatmap, fidelity estimates) so the eye never re-learns a scale across panels.
- **Semantic mapping**, consistent everywhere: phase angle → hue, amplitude/probability → luminance.
- **Accessibility**: WCAG 2.1 AA contrast, full keyboard nav of the circuit canvas, ARIA labels on gates ("Controlled-NOT, control qubit 0, target qubit 1").
- **Command Palette** (`⌘K`/`Ctrl+K`): fuzzy-matches gate names, backend names, menu commands, and domain-module actions in one list — this is the fastest path through the app for power users and should mirror every CLI command 1:1 (see §6).

---

## 6. CLI Specification — `abirqu` command

Ship as a `Typer`-based CLI (`abirqu-cli` package or a `cli` extra on the main `abirqu` package) so it installs via `pip install abirqu[cli]`. **Every command below is a thin wrapper around the same Core Service functions the GUI uses** — no logic duplication.

```
abirqu ide                          # launches AbirQu Studio (GUI)

abirqu circuit new <name> --qubits N
abirqu circuit template <ghz|w|qft|grover|bv|random|qaoa|vqe-hw|vqe-uccsd|...> [options]
abirqu circuit show <file> [--format ascii|svg|html]
abirqu circuit convert <file> --to <qiskit|braket|cirq|ionq|pytket|quil|qasm2|qasm3|qir>
abirqu circuit validate <file>
abirqu circuit optimize <file> [--noise-adaptive]
abirqu circuit fingerprint <file>

abirqu run <file> --shots 4096 [--backend numpy|gpu|clifford|mps|montecarlo|hybrid|<hardware-name>]
abirqu run --sampler|--estimator|--mitigate|--qnn ...     # exposes QuantumRun's unified modes directly

abirqu sim engine list
abirqu sim benchmark <file> --engines mps,gpu,clifford     # cross-engine benchmark, mirrors README benchmark tables

abirqu hardware list                                     # 12 backends + connection status
abirqu hardware calibrate <backend> --t1 ... --t2 ...
abirqu hardware characterize <backend> --rb|--interleaved-rb|--tomography|--spam
abirqu hardware compile <file> --target <backend>
abirqu hardware credentials set <provider>                # interactive, writes to local .env, never echoes secrets
abirqu hardware cost-estimate <file> --backend <name>

abirqu noise zne <file> --method richardson|linear|exponential
abirqu noise mitigate <file> --strategy readout|m3|pec|adaptive
abirqu noise profile <backend>

abirqu qec encode <shor|steane|surface|color|repetition> --distance N
abirqu qec decode <syndrome-file> --decoder lookup|surface|bp|mwpm|gpu-bp
abirqu qec distill --type t-state|h-state --rounds N

abirqu qcomm bb84 --bits N
abirqu qcomm e91 --pairs N
abirqu qcomm network --topology star|ring|mesh --nodes N

abirqu chem molecule <h2|lih|h2o|custom> --mapper jw|bk|parity
abirqu chem vqe <molecule> --ansatz uccsd|hardware-efficient

abirqu osint graph build --nodes ... --edges ...
abirqu osint solve <max-cut|mis|mvc|coloring|community|anomaly> --graph <file> --qaoa-p N

abirqu crypto oracle <target-function>
abirqu crypto shor --factor N
abirqu crypto pqc keygen <kyber512|kyber768|kyber1024|dilithium2|dilithium3|dilithium5>
abirqu crypto pqc assess <keyset>

abirqu space hhl --matrix <file> --vector <file>
abirqu space cfd --grid-size N --viscosity F
abirqu space structural <stiffness-file>

abirqu qpinn solve --pde diffusion|navier-stokes --qubits N --depth N

abirqu agent submit <task-type> --params <json-file>
abirqu agent batch <tasks-dir>
abirqu agent status <task-id>

abirqu os queue list
abirqu os schedule --policy fifo|priority|sjf|fair-share
abirqu os cost <job-id>

abirqu security keygen <kyber|dilithium|sphincs>
abirqu security encrypt-circuit <file> --key <keyfile>

abirqu plugin list
abirqu plugin install <name>

abirqu ask "<question>"                    # runs the full NL2Q pipeline non-interactively
abirqu ask "<question>" --dry-run           # stop after step ③ (circuit generated), no execution
abirqu ask "<question>" --backend <name>    # override auto-selected backend
abirqu ask "<question>" --json               # machine-readable trace of all 6 steps, for CI/agents
abirqu ask --interactive                     # REPL mode, keeps conversation context across questions

abirqu config init                 # scaffolds .env from .env.example, prompts per-provider
abirqu doctor                       # environment check: NumPy/OpenBLAS arch, GPU availability, connected providers
```

Design notes for the coding agent:
- Every subcommand returns **both** a human-readable table (default) and `--json` machine-readable output, so CI pipelines can parse results.
- `abirqu ide` should hot-launch the GUI with the current working directory pre-loaded as a project.
- Shared core: put all the actual orchestration logic in `abirqu_core/` (the Core Service), and make both the Typer CLI and the FastAPI HTTP layer (used by the GUI) call into `abirqu_core/` — never let CLI-only or GUI-only logic drift apart.

---

## 7. Backend Service Layer (`abirqu_core`) — the piece that doesn't exist yet

This is the main **NEW** component to build. It is intentionally thin:

```
abirqu_core/
  service.py            FastAPI app, WebSocket endpoints for job/sim progress streaming
  circuits.py           wraps abirqu.library + abirqu.formats + abirqu.visualization
  simulation.py         wraps abirqu.primitives.QuantumRun + abirqu.simulation.*
  hardware.py           wraps abirqu.hardware.* (calibration, characterization, hw_compiler, cloud_manager)
  noise.py               wraps abirqu.noise_toolkit + abirqu.adaptive_mitigation
  qec.py                 wraps abirqu.qec.*
  qcomm.py               wraps abirqu.quantum_communication.*
  chemistry.py            wraps abirqu.chemistry
  osint.py                 wraps abirqu.osint
  crypto.py                 wraps abirqu.crypto
  space.py                   wraps abirqu.space
  qpinn.py                    wraps abirqu.qpinn
  agentic.py                    wraps abirqu.agentic
  quantum_os.py                  wraps abirqu.quantum_os (job persistence already SQLite-backed — reuse it)
  security.py                     wraps abirqu.cloud.abir_guard
  plugins.py                       wraps abirqu.plugins
  nlq/                              NEW — the Ask Quantum pipeline (full design in §11):
    intent_classifier.py            LLM call #1: question → structured problem type + params
    problem_formalizer.py           deterministic, no LLM: structured params → math object
                                     (Ising Hamiltonian / oracle / molecule spec / matrix / PDE spec)
                                     via existing abirqu builders (GraphToIsingCompiler,
                                     OracleSynthesizer, MolecularData, PDESpec, ...)
    circuit_synthesizer.py          deterministic, no LLM: math object → abirqu circuit,
                                     via abirqu.library / chemistry / osint / crypto / qpinn
    execution_planner.py            picks simulator vs hardware, engine, shot count, mitigation
                                     strategy based on problem size + user's cost/latency prefs
    result_interpreter.py           deterministic: raw bitstrings/energy/eigenvalue →
                                     domain-meaningful structured result
    answer_synthesizer.py           LLM call #2: structured result + circuit + algorithm
                                     metadata → plain-English answer with citations/caveats
    pipeline.py                     orchestrates the 6 steps, exposes checkpoints for the GUI
                                     to pause at each step for user edit/confirmation
  db.py                             app-level metadata only (recent projects, saved layouts,
                                     workspace prefs) — NOT circuit/job data, which stays in
                                     abirqu's own JobQueue SQLite store to avoid duplicating
                                     state that the SDK already owns
  progress_events.py               NEW: lightweight callback hooks injected into long-running
                                     simulation/optimization loops so the GUI/CLI can stream
                                     progress; implemented as optional callback params passed
                                     into existing abirqu functions, not forked SDK internals
```

**Explicit non-goals for `abirqu_core`**: it must never re-implement quantum math, gate decomposition, mitigation, or hardware adapters — all of that stays in the `abirqu` package itself so the SDK remains the single source of truth and future `abirqu` releases drop in as a dependency bump.

---

## 8. Optional: AI Assistant Panel (Claude-powered)

Since this is going to an agentic coding platform, worth speccing now even as a v2 feature:
- Chat grounded in the open circuit + project files.
- "Explain this circuit" → sends the circuit's QASM + `CircuitDrawer` output + fidelity estimate to the model, returns plain-language explanation.
- "Suggest optimization" → proposes template/pattern swaps, but always executes the actual optimization through `abirqu.patterns` / `abirqu.optimize.noise_adaptive` rather than letting the model hand-edit circuits directly — the model proposes, the SDK executes and verifies.
- Ship this as a separate panel that can be fully disabled for air-gapped/classified deployments (DRDO/ISRO-type users mentioned in the repo's own README will need an offline mode with this panel removed entirely, not just hidden).

---

## 9. Commercial/Industry Layering

| Tier | Scope |
|---|---|
| **Community (OSS, MIT-aligned with the SDK's own license)** | Full GUI + CLI, local simulators only, local plugin discovery, no hosted marketplace |
| **Pro** | Cloud hardware credential management UI, job cost estimator, saved workspace sync across machines |
| **Enterprise** | SSO/SAML, RBAC via `TenantManager`/`AccessController`, on-prem/air-gapped deployment (AI panel disabled), audit logs on every hardware submission and circuit encryption event, hosted plugin marketplace, SLA-backed hardware reservation via `ReservationSystem` |

---

## 10. Build Order (hand this straight to the coding agent as milestones)

1. **M0 — Core Service skeleton**: FastAPI app importing `abirqu`, expose `circuits.py` + `simulation.py` only (create/run/visualize a circuit end-to-end).
2. **M1 — Minimal GUI shell**: Tauri + React shell, dockview layout, Monaco editor + Circuit Designer canvas synced via `abirqu.formats`, Simulation panel calling `QuantumRun`, Bloch sphere + histogram visualization panels.
3. **M2 — CLI parity**: Typer CLI covering `circuit`, `run`, `sim` command groups, calling the same `abirqu_core` functions as M1.
4. **M3 — Hardware + Quantum OS**: hardware panel, calibration/characterization views, job queue/scheduler UI, cost estimator, credential wizard.
5. **M4 — Noise & Mitigation, QEC, Quantum Comm panels.**
6. **M5 — Domain modules**: Chemistry, OSINT, Crypto, Space, Q-PINN, Agentic — each as its own dockable panel following the same pattern established in M1–M4.
7. **M6 — Security (AbirGuard) + Plugins panel + workspace layouts/save-restore.**
8. **M7 — Enterprise layer**: SSO, RBAC UI, audit logs, air-gapped packaging profile.
9. **M8 (optional)**: AI Assistant panel.
10. **M9**: Ask Quantum (NL2Q) pipeline — build only after M0–M6 exist, since NL2Q's circuit-synthesis step calls into the domain-module wrappers built in M5. See §11 for the full design.

Each milestone should ship with its own CLI commands and GUI panel **together**, since they share `abirqu_core` — building them in lockstep prevents the two surfaces from drifting apart.

---

## 11. Ask Quantum (NL2Q) — Architecture

This is the "human English question → quantum circuit → QPU/simulator → human English answer" feature. It is the highest-value and highest-risk feature in the whole product: highest-value because it's what makes AbirQu usable by non-quantum-experts (a chemist, a logistics analyst, a security auditor); highest-risk because an LLM freelancing raw circuit code will silently produce wrong physics. The design below exists specifically to prevent that.

### 11.1 Core principle: LLM proposes, SDK executes, nothing is opaque

The LLM is used for exactly two things — **understanding the question** and **writing the final answer in English**. It is **never** used to generate circuit code, gate sequences, or numeric results directly. Everything in between is deterministic code calling AbirQu's real functions. This is the same "propose → verify → execute" pattern as the AI Assistant panel in §8, just applied end-to-end.

### 11.2 The Six-Stage Pipeline

```
Human question (English)
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│ ① INTENT CLASSIFICATION  (LLM call)                        │
│   Input: raw question + short domain-glossary system prompt│
│   Output (structured JSON): problem_domain, sub_type,      │
│     extracted_parameters, confidence_score                  │
│   If confidence < threshold → ask a clarifying question      │
│   instead of proceeding (surfaced in GUI, see §4.13)         │
└───────────────────────────────────────────────────────────┘
        │  structured intent (JSON, not prose)
        ▼
┌───────────────────────────────────────────────────────────┐
│ ② PROBLEM FORMALIZATION  (deterministic, no LLM)            │
│   Routes structured intent → the matching abirqu builder:   │
│   see routing table §11.3                                    │
│   Output: a concrete math object (Hamiltonian, oracle fn,   │
│   molecule spec, matrix, PDE spec, graph, key params)        │
└───────────────────────────────────────────────────────────┘
        │  math object
        ▼
┌───────────────────────────────────────────────────────────┐
│ ③ CIRCUIT SYNTHESIS  (deterministic, no LLM)                │
│   Math object → abirqu.library / chemistry / osint / crypto│
│   / qpinn / space builder → an actual AbirQu Circuit object │
│   Rendered immediately in the Circuit Designer (§4.2)        │
└───────────────────────────────────────────────────────────┘
        │  Circuit object
        ▼
┌───────────────────────────────────────────────────────────┐
│ ④ EXECUTION PLANNING + RUN                                  │
│   Picks: simulator engine (size-based) or hardware backend,  │
│   shot count, mitigation strategy (via                        │
│   AdaptiveErrorMitigator if hardware-bound), cost estimate    │
│   (CostEstimator). Requires explicit user "Run" confirmation  │
│   before anything touches real hardware or spends money.       │
│   Output: raw result (bitstring counts / eigenvalue /          │
│   statevector / decoded key / factors)                          │
└───────────────────────────────────────────────────────────┘
        │  raw quantum result
        ▼
┌───────────────────────────────────────────────────────────┐
│ ⑤ RESULT INTERPRETATION  (deterministic, no LLM)             │
│   Raw output → domain-meaningful structured result:            │
│   e.g. bitstring → "partition {1,3} vs {2,4,5}, cut value 7";  │
│   eigenvalue → "-1.137 Hartree"; factors → "7 × 13"             │
└───────────────────────────────────────────────────────────┘
        │  structured result + provenance (algorithm, circuit, backend, shots, error bars)
        ▼
┌───────────────────────────────────────────────────────────┐
│ ⑥ ANSWER SYNTHESIS  (LLM call)                               │
│   Input: structured result + provenance, NOT raw numbers      │
│   alone — the LLM is told exactly what algorithm/circuit/      │
│   backend produced this, and what the precision/error bars     │
│   are, so it cannot overstate confidence.                       │
│   Output: plain-English answer, always includes: the answer,   │
│   which algorithm/circuit produced it, precision/confidence,   │
│   and one caveat sentence if the result came from a NISQ/       │
│   noisy backend or an approximate method (VQE/QAOA are           │
│   heuristic, not exact — the answer must say so).                │
└───────────────────────────────────────────────────────────┘
        │
        ▼
Human answer (English) + circuit + algorithm + full trace, exportable as PDF/HTML report
```

### 11.3 Intent → AbirQu Builder Routing Table

| Question pattern | `problem_domain` | Formalization builder | Circuit synthesis | Result interpretation |
|---|---|---|---|---|
| "ground state energy of \<molecule\>", "bond energy", "electronic structure of X" | chemistry | `MolecularData` + JW/BK/Parity mapper | `abirqu.chemistry` VQE (UCCSD/hardware-efficient) | eigenvalue → Hartree/eV, compare to FCI reference if available |
| "best route/assignment/partition/schedule for X", "optimize this graph/network" | combinatorial optimization | `GraphToIsingCompiler` (Max-Cut/MIS/MVC/Coloring/Community/Anomaly) | `abirqu.osint` QAOA circuit builder | bitstring → partition/assignment + objective value |
| "optimize this portfolio", "minimize risk for these assets" | finance | `abirqu.industry` portfolio Ising formulation | QAOA via `abirqu.industry` | bitstring → asset allocation + expected return/risk |
| "factor N", "break this RSA key" | cryptanalysis | `abirqu.crypto.ModularArithmetic` | Shor's algorithm circuit via `abirqu.crypto` | measured register → continued-fraction → factors |
| "is this key/algorithm quantum-safe" | PQC assessment | `abirqu.crypto` vulnerability model | (no circuit — assessment runs Grover/BKZ complexity estimate) | complexity numbers → safety verdict + recommended PQC scheme |
| "search this list/database for X" | unstructured search | oracle spec from query predicate | `OracleSynthesizer` → Grover circuit via `abirqu.library` | measured index → matching item(s) |
| "generate a secure key between two parties" | quantum communication | protocol choice (BB84 default) | `abirqu.quantum_communication.bb84` | sifted key + QBER → key material + security margin |
| "solve this system of linear equations", "solve this CFD/structural problem" | linear algebra / space | matrix/vector from user input or CSV upload | `abirqu.space.HHLSolver` | statevector → solution vector + residual norm |
| "solve/simulate this PDE" | PDE / physics | `PDESpec` (diffusion, Navier-Stokes, etc.) | `abirqu.qpinn` | trained QPINN → field values at query points |
| "classify this data", "predict X from these features" | quantum ML | dataset + label spec | `abirqu.primitives.QNN` + `ZZFeatureMap`/`Angle` encoding | trained model output → class/prediction + accuracy |
| *no match found* | — | — | — | surface: "I don't have a quantum algorithm mapped to this question yet — did you mean one of: [suggest 3 closest domains]?" Never silently guess. |

This table is the actual spec for `intent_classifier.py`'s system prompt and `problem_formalizer.py`'s dispatch logic — the coding agent should implement it as a literal routing table (e.g. a Python dict of `problem_domain → formalizer_fn, synthesizer_fn, interpreter_fn`), not as free-form LLM reasoning at every stage.

### 11.4 Ambiguity, Safety, and Cost Guardrails
- **Ambiguity**: if step ① confidence is below threshold, or the question maps to more than one domain (e.g. "optimize my network" could mean graph routing or QKD network topology), the pipeline stops and the GUI/CLI surfaces a disambiguation choice — it never silently picks one.
- **Unsupported questions**: if no routing-table entry matches, say so plainly and suggest the nearest supported domains. Never fabricate a plausible-looking circuit for a problem AbirQu can't actually solve.
- **Cost/hardware safety**: step ④ always requires explicit confirmation before submitting to paid or queued hardware backends (reuses the credential/cost-estimate flow from §4.4/§4.10). `--dry-run` in the CLI stops before this step entirely.
- **Reproducibility**: every run's full 6-stage trace (question, extracted params, math object, circuit, backend, raw result, final answer) is persisted (reuse `abirqu.quantum_os.JobQueue`'s SQLite store, tagged as an NL2Q job) so a user or auditor can replay exactly what happened.
- **Offline/air-gapped mode**: for the enterprise tier (§9), both LLM calls (① and ⑥) must be swappable to a **local model** or disabled entirely, with steps ②–⑤ still usable directly through the GUI/CLI without any natural-language layer — the deterministic core must never *require* an external LLM API to function.

### 11.5 Why this design, not "one big LLM agent with tool access"
A tempting shortcut is giving an LLM agent tool-call access to run arbitrary AbirQu functions and let it "figure it out." That's explicitly the wrong architecture here: it makes results non-reproducible (different runs can silently take different paths), makes it easy for the model to construct a plausible-but-wrong Hamiltonian or oracle, and makes cost/safety guardrails much harder to enforce consistently. The fixed six-stage pipeline with a literal routing table gives you LLM flexibility exactly where it's safe (parsing English, writing English) and hard determinism everywhere the physics has to be right.
