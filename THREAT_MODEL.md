# AbirQu Threat Model
Copyright 2026 Abir Maheshwari

## 1. Scope
This threat model covers all components of AbirQu: core quantum engine, optimization pipeline, quantum error correction (QEC) module, design patterns library, AI integration tools, security subsystem, multi-backend support, and developer experience tooling.

## 2. Data Assets
- User-defined quantum circuits and algorithms
- Encrypted circuit payloads and cryptographic keys
- Simulated QKD key exchange materials
- Hardware attestation tokens and credentials
- Backend API keys (IBM Quantum, Google Cirq, AWS Braket)
- User configuration and preference data

## 3. Threat Actors
- Malicious users attempting circuit injection or code execution
- Network eavesdroppers targeting backend API connections
- Attackers attempting to reverse-engineer proprietary circuits
- Supply chain actors compromising third-party dependencies
- (Internal threats are minimal as AbirQu is maintained by a single author)

## 4. Identified Threats & Mitigations
### 4.1 Malicious Circuit Injection
- **Threat**: Injection of arbitrary code via circuit DSL or user inputs
- **Mitigation**: Strict input validation in `abirqu.core.circuit`, sandboxed QVM execution, no arbitrary code evaluation

### 4.2 Backend Credential Exposure
- **Threat**: Leakage of plaintext API keys for quantum backends
- **Mitigation**: Encrypted credential storage, no hardcoded keys in codebase, secure token passing

### 4.3 QKD Simulation Tampering
- **Threat**: Manipulation of simulated QKD key exchanges
- **Mitigation**: Built-in error checking for BB84 protocol, encrypted classical communication channels

### 4.4 Supply Chain Attacks
- **Threat**: Compromised third-party dependencies (e.g., NumPy, SciPy)
- **Mitigation**: Pinned dependency versions in `setup.py`, checksum verification for critical libraries

### 4.5 Circuit Reverse Engineering
- **Threat**: Unauthorized copying of proprietary quantum circuits
- **Mitigation**: Circuit obfuscation module, encrypted circuit storage

## 5. Assumptions
- AbirQu is run in trusted local or cloud environments
- No intentional backdoors exist in the codebase (single-author maintenance)
- Third-party quantum backends maintain their own security standards