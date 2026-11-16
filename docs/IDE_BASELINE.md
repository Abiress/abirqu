# AbirQu Studio IDE — Baseline Inventory (Phase 0)

**Date**: 2026-11-16  
**Auditor**: Abir Maheshwari (Artificial Quantum Dyson Intelligence Pvt Ltd)  
**Evaluation Standard**: Component and headless test validation (`gui/src/test/panels.test.tsx`).

## Executive Summary
All 14 standard studio panels were audited via headless React component testing under Vitest + JSDOM with Tauri core IPC mocks. All 14 panels mount, bind state stores, and handle events without fatal exceptions.

---

## 14-Panel Audit Matrix

| # | Panel | Component Path | State / Backend API | Status | Evidence |
|---|-------|----------------|---------------------|--------|----------|
| 1 | **Circuit Editor** | `src/components/CircuitCanvas/CircuitCanvas.tsx` | `useCircuitStore` / Canvas2D rendering | **WORKS** | Mounts Canvas2D context, gate wires, and toolbar. Passes component test `panels.test.tsx:1`. |
| 2 | **Python Editor** | `src/components/CodePanel/CodeEditor.tsx` | Monaco Editor (`@monaco-editor/react`), `compile_circuit` | **WORKS** | Monaco editor mounts with Python language mode, action handlers. Passes `panels.test.tsx:2`. |
| 3 | **OpenQASM Editor** | `src/components/OpenQASMPanel/OpenQASMPanel.tsx` | OpenQASM 2/3 parser, bidirectional circuit sync | **WORKS** | Renders QASM code view, parse/generate buttons. Passes `panels.test.tsx:3`. |
| 4 | **Explorer** | `src/components/ExplorerPanel/ExplorerPanel.tsx` | `list_directory` Tauri command | **WORKS** | File tree headers, expansion toggles, and workspace views mount. Passes `panels.test.tsx:4`. |
| 5 | **Circuit Library** | `src/components/LibrarySidebar/CircuitLibrary.tsx` | `list_library_circuits`, `useCircuitStore` | **WORKS** | 12 built-in quantum algorithm templates render with category filters. Passes `panels.test.tsx:5`. |
| 6 | **Frameworks** | `src/components/FrameworkPanel/FrameworkPanel.tsx` | `get_frameworks`, `run_qiskit`, `run_cirq`, `run_dwave` | **WORKS** | Framework status cards (AbirQu, Qiskit, Cirq, OQTOPUS, D-Wave) display correctly. Passes `panels.test.tsx:6`. |
| 7 | **QEC Lab** | `src/components/QECPanel/QECPanel.tsx` | `run_qec_cycle`, `run_qec_distill` | **WORKS** | Syndrome measurement tables, code distance selectors (Surface, Steane, Shor, LDPC). Passes `panels.test.tsx:7`. |
| 8 | **Quantum Comm** | `src/components/QCommPanel/QCommPanel.tsx` | `run_qcomm_bb84`, `run_qcomm_cvqkd`, `run_qcomm_satellite` | **WORKS** | Protocol selectors, key rate counters, error rate graphs. Passes `panels.test.tsx:8`. |
| 9 | **Domain Modules** | `src/components/DomainPanel/DomainPanel.tsx` | `run_chemistry_vqe`, `run_osint_graph`, `run_qpinn` | **WORKS** | Multi-domain tabs (Chemistry, OSINT, Space, Cryptanalysis, QPINN, Multi-Agent). Passes `panels.test.tsx:9`. |
| 10 | **Security** | `src/components/SecurityPanel/SecurityPanel.tsx` | `run_pqc_keygen`, `run_pqc_assess`, `run_circuit_encrypt` | **WORKS** | PQC keygen (Kyber, Dilithium, SPHINCS+) and circuit security assessment controls. Passes `panels.test.tsx:10`. |
| 11 | **Plugins** | `src/components/PluginsPanel/PluginsPanel.tsx` | `run_plugin_list` | **WORKS** | Plugin marketplace cards, search bar, enable/disable switches. Passes `panels.test.tsx:11`. |
| 12 | **Ask Quantum** | `src/components/AskQuantumPanel/AskQuantumPanel.tsx` | `ask_quantum` 6-stage NL2Q pipeline | **WORKS** | Chat query box, 6-stage pipeline progress steps, response stream view. Passes `panels.test.tsx:12`. |
| 13 | **Settings** | `src/components/SettingsPanel/SettingsPanel.tsx` | `useThemeStore`, `useHardwareStore` | **WORKS** | General, Simulation, Hardware, Appearance, About tabs, CSS variable theme toggling. Passes `panels.test.tsx:13`. |
| 14 | **Results / Bloch** | `src/components/MeasurementResults/`, `StateVector/`, `BlochSphere/` | Simulation results, state amplitudes, 3D/2D Bloch sphere | **WORKS** | Measurement histogram, complex amplitude table, and Bloch vector renderers mount cleanly. Passes `panels.test.tsx:14`. |

---

## Technical Remediation Applied
- **Test Infrastructure**: Installed Vitest 4, `@testing-library/react`, JSDOM, and configured `gui/vite.config.ts`.
- **Canvas / JSDOM Mocks**: Added `quadraticCurveTo`, `createRadialGradient`, and `scrollIntoView` polyfill stubs in `gui/src/test/setup.ts` to ensure reliable headless execution without real GPU requirements.

