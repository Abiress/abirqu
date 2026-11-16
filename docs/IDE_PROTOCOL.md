# AbirQu Studio IDE — Backend Protocol Specification (IDE_PROTOCOL.md)

**Version**: 2.0.0  
**Status**: Standard  
**Maintainer**: Artificial Quantum Dyson Intelligence Pvt Ltd / Abir Maheshwari

---

## 1. Architectural Model

```
┌────────────────────────────────────────────────────────┐
│             AbirQu Studio Frontend (Webview)           │
│        React 18 + TypeScript + Zustand + Monaco        │
└───────────────────────────┬────────────────────────────┘
                            │ Tauri IPC (invoke)
┌───────────────────────────▼────────────────────────────┐
│                  Tauri Rust Core                       │
│    Session Token Management • Path Canonicalization    │
└───────────────────────────┬────────────────────────────┘
                            │ Stdio Pipe / Localhost:127.0.0.1
┌───────────────────────────▼────────────────────────────┐
│            Python Subprocess (server_headless)         │
│         Quantum Simulation & Transpilation Engine       │
└────────────────────────────────────────────────────────┘
```

The communication layer supports two validated transports:
1. **Stdio JSON-RPC Pipe (Default)**: Subprocess spawned with dedicated `stdin`, `stdout`, `stderr` pipes.
2. **Localhost TCP Transport**: Bound exclusively to `127.0.0.1` with a cryptographically random per-session token (64 hex characters) generated at startup by the Rust core.

---

## 2. Wire Protocol

All messages are UTF-8 encoded line-delimited JSON objects following JSON-RPC 2.0 semantics.

### 2.1 Request Structure
```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "method": "compile_circuit",
  "params": {
    "circuit": {
      "num_qubits": 2,
      "gates": [
        {"name": "H", "qubits": [0]},
        {"name": "CNOT", "qubits": [0, 1]}
      ]
    },
    "backend": "abirqu_simulator"
  }
}
```

### 2.2 Response Structure
```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "result": {
    "compiled": true,
    "depth": 2,
    "num_qubits": 2,
    "backend": "abirqu_simulator"
  }
}
```

### 2.3 Error Structure
```json
{
  "jsonrpc": "2.0",
  "id": "req-001",
  "error": {
    "code": -32600,
    "message": "Invalid circuit parameter: qubit index out of bounds"
  }
}
```

### 2.4 Server Notification / Stream Event
```json
{
  "jsonrpc": "2.0",
  "method": "job_progress",
  "params": {
    "job_id": "job-789a",
    "status": "running",
    "progress": 0.75,
    "current_step": "shot_sampling"
  }
}
```

---

## 3. Security Invariants & Path Sandboxing

### 3.1 Workspace Path Containment
Arbitrary file reads and writes are strictly forbidden. All file-system operations (project open, save, code file reading, export, directory listing) must resolve inside the user-configured workspace root:

```python
def validate_workspace_path(path: str, workspace_root: str) -> str:
    root = os.path.realpath(workspace_root)
    target = os.path.realpath(os.path.join(root, path) if not os.path.isabs(path) else path)
    if os.path.commonpath([root, target]) != root:
        raise PermissionError(f"Access denied: path '{path}' escapes workspace root")
    return target
```

In Rust (Tauri Core):
```rust
let canonical_root = workspace_root.canonicalize()?;
let target = canonical_root.join(relative_path).canonicalize()?;
if !target.starts_with(&canonical_root) {
    return Err("Path traversal attempt detected");
}
```

### 3.2 Network Binding Constraint
When TCP socket transport is activated, listeners MUST bind strictly to `127.0.0.1` (never `0.0.0.0`). Every request must carry the session token:
`X-AbirQu-Session-Token: <token>`

---

## 4. Standard Action Catalog

| Method | Parameters | Return Type | Description |
|--------|------------|-------------|-------------|
| `compile_circuit` | `{ circuit, backend }` | `CompiledCircuit` | Synthesize and optimize circuit |
| `execute_circuit` | `{ circuit, backend, shots, noise }` | `JobHandle` | Schedule circuit simulation |
| `get_job_status` | `{ job_id }` | `JobInfo` | Poll execution progress |
| `get_results` | `{ job_id }` | `SimulationResult` | Retrieve counts, statevector |
| `cancel_job` | `{ job_id }` | `string` | Abort running job |
| `list_hardware` | `{}` | `HardwareInfo[]` | Enumerate available backends |
| `list_library_circuits` | `{}` | `CircuitTemplate[]` | Fetch algorithmic templates |
| `convert_circuit` | `{ circuit, target }` | `string` | Transpile to QASM/Qiskit/Cirq |
| `run_qec_cycle` | `{ params }` | `QECCycleResult` | Simulate error correction cycle |
| `run_chemistry_vqe` | `{ params }` | `VQEOutput` | Ground state molecular search |
| `list_directory` | `{ path }` | `DirEntry[]` | Enumerate workspace directory |
| `read_file` | `{ path }` | `string` | Read file within workspace |
| `write_file` | `{ path, content }` | `boolean` | Atomic file write in workspace |

