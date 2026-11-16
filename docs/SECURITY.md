# AbirQu Studio & Core Threat Model and Security Policy

**Author**: Abir Maheshwari <abhirsxn@gmail.com>  
**Organization**: Artificial Quantum Dyson Intelligence Pvt Ltd  

## 1. Overview
AbirQu and AbirQu Studio provide an integrated quantum development environment and SDK. Because users load foreign quantum circuits, run community plugins, and connect to remote quantum hardware providers, the architecture enforces strict isolation boundaries across all layers.

---

## 2. Threat Model & Boundaries

### 2.1 Untrusted Circuit & File Inputs
- **Threat**: Malicious circuit files (OpenQASM 2/3, JSON, Quirk URLs) attempting remote code execution or prototype pollution.
- **Mitigation**:
  - OpenQASM parsing is performed by deterministic grammar lexers without invoking `eval` or dynamic code generation.
  - JSON and Quirk loaders strictly parse typed ASTs and instantiate primitive quantum gates.
  - Python scripts opened in the Monaco editor are treated strictly as text; parsing to visual circuit representations is done via AST regex/token extraction rather than arbitrary code execution.

### 2.2 Workspace Directory Traversal
- **Threat**: Attackers crafting file paths (e.g. `../../etc/passwd` or `..\..\Windows\System32`) via Tauri RPC commands to read or overwrite arbitrary system files.
- **Mitigation**:
  - The Tauri backend validates all file system access through `resolve_in_workspace()`.
  - Both the workspace root and target path are resolved using canonical path resolution (`canonicalize`).
  - Access is denied if the resolved canonical target path does not strictly start with the canonical workspace root prefix.

### 2.3 Plugin Sandboxing & Out-of-Process Isolation
- **Threat**: Untrusted plugins attempting unauthorized network exfiltration, file system modification, or denial-of-service loops.
- **Mitigation**:
  - Plugins run out-of-process using `OutOfProcessPluginHost` in an isolated Python subprocess.
  - Plugins declare explicit permissions in `PluginManifest`:
    - `filesystem`: Required to open or write files. Without this, standard I/O and file access are blocked with `PermissionError`.
    - `network`: Required for socket connections. Without this, network socket creation/connect is blocked with `PermissionError`.
  - Hard 5-second execution timeout per hook prevents hung threads or infinite loops.

### 2.4 Credential Protection & Hardware Jobs
- **Threat**: Hardware tokens (IBM Quantum, AWS Braket, Rigetti) leaking into source control, logs, or plain-text files.
- **Mitigation**:
  - Credentials must be stored in the OS Keychain / Secret Service API or passed via ephemeral environment variables.
  - All logging and error handlers scrub and mask tokens, showing at most the last 4 characters.
  - Submitting jobs to real or paid quantum hardware backends requires explicit user confirmation with estimated shot count and cost.

### 2.5 Local IPC Protocol
- **Threat**: Unauthorized local processes or cross-site requests tampering with the headless backend server.
- **Mitigation**:
  - Headless server runs over standard I/O (stdio) or binds strictly to `127.0.0.1` with a cryptographically random per-session bearer token.
  - CORS and Host header enforcement reject foreign origins.

