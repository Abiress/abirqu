# AbirQu Desktop GUI — "VS Code for Quantum Computing"

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Tauri (Rust) Shell                                  │
│  ┌───────────────────────────────────────────────┐  │
│  │  React Frontend (TypeScript)                   │  │
│  │                                               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │  │
│  │  │ Circuit   │ │ Code     │ │ Results      │  │  │
│  │  │ Editor    │ │ Editor   │ │ Panel        │  │  │
│  │  │ (Canvas)  │ │ (Monaco) │ │ (Chart.js)   │  │  │
│  │  └──────────┘ └──────────┘ └──────────────┘  │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────┐  │  │
│  │  │ Bloch     │ │ Hardware │ │ Job          │  │  │
│  │  │ Sphere    │ │ Panel    │ │ Dashboard    │  │  │
│  │  │ (Three.js)│ │          │ │              │  │  │
│  │  └──────────┘ └──────────┘ └──────────────┘  │  │
│  │  ┌──────────┐ ┌────────────────────────────┐  │  │
│  │  │ Library   │ │ Console / Terminal          │  │  │
│  │  └──────────┘ └────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Rust Backend (Tauri Commands)                │  │
│  │  - Spawns Python subprocess (abirqu/gui)      │  │
│  │  - Manages IPC via stdin/stdout JSON          │  │
│  │  - File system access                         │  │
│  │  - Process lifecycle                          │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │  Python Backend (abirqu.gui.server)           │  │
│  │  - QuantumServer REST+WebSocket               │  │
│  │  - Circuit simulation                         │  │
│  │  - Job management                             │  │
│  │  - Hardware registry                          │  │
│  │  - Bundled via PyInstaller in release builds  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Shell | **Tauri 2.x** | Native performance, small binaries (~5MB vs Electron ~150MB), Rust backend, cross-platform |
| Frontend | **React 18 + TypeScript** | Mature ecosystem, component reusability |
| Circuit Canvas | **HTML5 Canvas** (custom) | Full control over gate rendering, drag-drop, wire drawing |
| Code Editor | **Monaco Editor** | VS Code's editor, syntax highlighting, IntelliSense, diff view |
| Bloch Sphere | **Three.js** + React Three Fiber | 3D WebGL rendering for Bloch sphere |
| Charts | **Recharts** | Lightweight React charts for measurement histograms |
| State Mgmt | **Zustand** | Minimal, fast state management |
| Styling | **Tailwind CSS** + CSS variables | Theme-aware, matches dark/light from Python backend |
| Backend IPC | **Tauri Commands** (Rust ↔ Python) | Rust spawns Python, communicates via JSON over stdio |
| Python | **abirqu.gui.server** (existing) | All quantum logic already implemented |

## Backend → Frontend Mapping

| Python Module | Frontend Component | Description |
|---------------|-------------------|-------------|
| `server.py` → `QuantumServer` | Rust Tauri commands | Spawned as subprocess, JSON IPC |
| `circuit_editor.py` → `CircuitEditor` | `CircuitCanvas.tsx` | Canvas-based gate grid with drag-drop |
| `code_editor.py` → `CodeEditor` | `CodePanel.tsx` (Monaco) | Python code editing with quantum syntax |
| `bloch_sphere.py` → `BlochSphereWidget` | `BlochSphere.tsx` (Three.js) | 3D interactive Bloch sphere |
| `state_visualizer.py` → `StateVisualizer` | `StateVector.tsx` | State vector bar chart + amplitudes |
| `measurement_panel.py` → `MeasurementPanel` | `MeasurementResults.tsx` | Histogram + statistics |
| `hardware_panel.py` → `HardwarePanel` | `HardwareSidebar.tsx` | Backend selection + status |
| `job_dashboard.py` → `JobDashboard` | `JobPanel.tsx` | Job list + progress tracking |
| `circuit_library.py` → `CircuitLibraryPanel` | `LibrarySidebar.tsx` | Template browser + search |
| `theme.py` → `ThemeManager` | `ThemeProvider.tsx` | CSS variable injection |

## Layout

```
┌──────────────────────────────────────────────────────────────┐
│ Toolbar: [New] [Open] [Save] [Run] [Stop] [Hardware: ▼]    │
├──────┬───────────────────────────────────────┬───────────────┤
│      │  ┌─────┬─────┬─────┬─────┬─────┐    │               │
│ Lib  │  │ q0  │ ──H─┤─────┼─•───┤     │    │  Bloch        │
│      │  │ q1  │ ────┼─────┼─⊕───┤     │    │  Sphere       │
│ 📚   │  │ q2  │ ────┼───X─┼─────┤     │    │  (3D)         │
│      │  └─────┴─────┴─────┴─────┴─────┘    │               │
│      │  Circuit Editor (Canvas)             ├───────────────┤
│      │                                     │  State        │
│      ├─────────────────────────────────────│  Vector       │
│      │  Code Editor (Monaco)               │  (bars)       │
│      │  [Python with quantum highlighting] │               │
│      ├─────────────────────────────────────├───────────────┤
│      │  Results Panel                      │  Measurement  │
│      │  ┌──────────────────────────────┐   │  Histogram    │
│      │  │ Bar chart of |00⟩, |01⟩...  │   │  (Recharts)   │
│      │  └──────────────────────────────┘   │               │
├──────┴─────────────────────────────────────┴───────────────┤
│ Status: Backend: AbirQu Simulator | Qubits: 3 | Depth: 4   │
└──────────────────────────────────────────────────────────────┘
```

## IPC Protocol

Rust backend spawns Python as subprocess and communicates via JSON-over-stdio:

```
Rust → Python (stdin):  {"action": "execute", "circuit": {...}, "shots": 1024}
Python → Rust (stdout): {"status": "ok", "data": {"job_id": "abc123", ...}}
Python → Rust (stdout): {"event": "job_update", "data": {"job_id": "abc123", "status": "completed", ...}}
```

Rust Tauri commands expose this to React frontend:

```rust
#[tauri::command]
async fn compile_circuit(circuit: CircuitData) -> Result<CompiledCircuit, String>
async fn execute_circuit(circuit: CircuitData, backend: String, shots: u32) -> Result<JobInfo, String>
async fn get_job_status(job_id: String) -> Result<JobStatus, String>
async fn get_results(job_id: String) -> Result<MeasurementResults, String>
async fn list_hardware() -> Result<Vec<HardwareInfo>, String>
async fn list_library_circuits() -> Result<Vec<CircuitTemplate>, String>
```

## Installation

### macOS (.dmg)
- Tauri produces `AbirQu.dmg` (~8-12MB)
- Contains bundled Python backend (PyInstaller single-file binary)
- Drag to `/Applications`
- Code signed + notarized for Gatekeeper

### Windows (.msi / .exe)
- Tauri produces `AbirQu Setup.exe` (~8-12MB)
- Standard Windows installer
- Adds to Start Menu + desktop shortcut

### Linux (.AppImage / .deb / .rpm)
- `AbirQu.AppImage` (~8-12MB) — universal, runs anywhere
- `.deb` for Debian/Ubuntu
- `.rpm` for Fedora/RHEL
- Python backend bundled inside

### Build Pipeline
```
cargo tauri build
  → Compiles Rust shell
  → Bundles React frontend (Vite)
  → Bundles Python backend (PyInstaller --onefile)
  → Signs + packages per platform
```

## Implementation Phases

### Phase 1: Scaffold (Day 1)
- [x] Backend audit (complete — 125 tests pass)
- [ ] `cargo tauri init` in `gui/`
- [ ] React + Vite + TypeScript setup
- [ ] Monaco editor integration
- [ ] Basic layout (toolbar, panels, status bar)

### Phase 2: Core Panels (Day 2-3)
- [ ] Circuit Canvas — HTML5 Canvas rendering from `get_render_data()`
- [ ] Gate palette — drag gates onto canvas
- [ ] Wire rendering — horizontal qubit wires with gate connections
- [ ] Code Editor — Monaco with quantum Python syntax
- [ ] Execute button → Rust command → Python subprocess

### Phase 3: Visualization (Day 3-4)
- [ ] Bloch Sphere — Three.js 3D rendering from `project_2d()` data
- [ ] State Vector — bar chart from `StateVisualizer.get_render_data()`
- [ ] Measurement Results — Recharts histogram from `MeasurementPanel.get_render_data()`
- [ ] Real-time updates via job status polling

### Phase 4: Panels (Day 4-5)
- [ ] Hardware Sidebar — backend list, select, status indicators
- [ ] Job Dashboard — running jobs, progress bars, history
- [ ] Circuit Library — template browser, search, load into editor
- [ ] Console — Python stdout/stderr display

### Phase 5: Polish & Build (Day 5-6)
- [ ] Theme switching (dark/light via CSS variables)
- [ ] Keyboard shortcuts (Ctrl+R run, Ctrl+S save, etc.)
- [ ] File menu (New, Open, Save, Export QASM)
- [ ] Tauri bundling for macOS/Windows/Linux
- [ ] Installer generation
- [ ] Auto-update mechanism

### Phase 6: Distribution (Day 6-7)
- [ ] GitHub Releases with platform binaries
- [ ] Homebrew tap (macOS)
- [ ] Winget/Chocolatey (Windows)
- [ ] APT/YUM repos (Linux)
- [ ] In-app update checker

## File Structure

```
gui/
├── src-tauri/                  # Rust backend
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── src/
│   │   ├── main.rs            # Tauri app entry
│   │   ├── commands.rs        # IPC command handlers
│   │   └── python.rs          # Python subprocess management
│   └── icons/
├── src/                        # React frontend
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── Toolbar.tsx
│   │   ├── StatusBar.tsx
│   │   ├── CircuitCanvas/
│   │   │   ├── CircuitCanvas.tsx
│   │   │   ├── GatePalette.tsx
│   │   │   └── WireRenderer.tsx
│   │   ├── CodePanel/
│   │   │   └── CodeEditor.tsx
│   │   ├── BlochSphere/
│   │   │   └── BlochSphere.tsx
│   │   ├── StateVector/
│   │   │   └── StateVector.tsx
│   │   ├── MeasurementResults/
│   │   │   └── Histogram.tsx
│   │   ├── HardwareSidebar/
│   │   │   └── HardwarePanel.tsx
│   │   ├── JobDashboard/
│   │   │   └── JobPanel.tsx
│   │   ├── LibrarySidebar/
│   │   │   └── CircuitLibrary.tsx
│   │   └── Console/
│   │       └── Console.tsx
│   ├── stores/
│   │   ├── circuitStore.ts
│   │   ├── jobStore.ts
│   │   ├── hardwareStore.ts
│   │   └── themeStore.ts
│   ├── api/
│   │   └── commands.ts        # Tauri invoke wrappers
│   └── styles/
│       └── themes.css
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Theme System

CSS variables injected from Python `ThemeManager`:

```css
:root {
  --bg-primary: #1a1a2e;
  --bg-secondary: #16213e;
  --bg-editor: #0d1117;
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --accent: #7c3aed;
  --gate-h: #7c3aed;
  --gate-x: #f85149;
  --wire: #8b949e;
  /* ... full set from DARK_THEME */
}
```

Toggle switches `data-theme="dark|light"` on `<html>`, CSS variables update instantly.

## Scope

### In Scope
- Visual circuit editor (drag-drop gates, wire rendering)
- Code editor (Monaco, quantum Python syntax)
- Bloch sphere (3D, interactive rotation)
- State vector visualization
- Measurement histogram
- Hardware selection (local simulators)
- Job execution + monitoring
- Circuit library (templates)
- Dark/light themes
- Cross-platform installers (macOS, Windows, Linux)

### NOT in Scope (for v1)
- Cloud backend submission (add later)
- QASM import/export (add later)
- Multi-file projects (add later)
- Collaborative editing (add later)
- Plugin system (add later)
