"""Compatibility matrix and validation helpers for AbirQu SDK."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class CompatibilityItem:
    milestone: str
    name: str
    status: str
    notes: str


class CompatibilityManager:
    """Build runtime/file-system-backed compatibility reports."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self._repo_root = repo_root or Path(__file__).resolve().parent.parent

    def _exists(self, relative: str) -> bool:
        return (self._repo_root / relative).exists()

    def language_compatibility(self) -> List[Dict[str, str]]:
        shared_lib_present = any(self._exists(p) for p in [
            "abirqu/abirqu_core.so",
            "abirqu/abirqu_core.cpython-314-x86_64-linux-gnu.so",
            "target/release/libabirqu_core.so",
        ])
        rows = [
            CompatibilityItem("C1.1", "Python", "✅ Complete", "Native package and SDK entrypoints"),
            CompatibilityItem(
                "C1.2",
                "C / C++",
                "✅ Complete" if self._exists("include/abirqu.h") and shared_lib_present else "⚠️ Partial",
                "Stable C ABI via include/abirqu.h and shared library",
            ),
            CompatibilityItem(
                "C1.3",
                "JavaScript / Node.js",
                "✅ Complete" if self._exists("js/package.json") else "⚠️ Partial",
                "JS SDK, npm metadata, and WASM build assets",
            ),
            CompatibilityItem("C1.4", "Java", "✅ Complete" if self._exists("java/src") else "⚠️ Partial", "JNA wrapper over C ABI"),
            CompatibilityItem("C1.5", "Go", "✅ Complete" if self._exists("go/abirqu") else "⚠️ Partial", "cgo bindings"),
            CompatibilityItem("C1.6", "Rust", "✅ Complete" if self._exists("Cargo.toml") else "⚠️ Partial", "Public crate and core sources"),
            CompatibilityItem("C1.7", ".NET / C#", "✅ Complete" if self._exists("dotnet/AbirQu") else "⚠️ Partial", "P/Invoke wrapper"),
            CompatibilityItem("C1.8", "Swift / Objective-C", "✅ Complete" if self._exists("swift/AbirQuSimulator.swift") else "⚠️ Partial", "C interop wrapper"),
            CompatibilityItem("C1.9", "Kotlin / JVM", "✅ Complete" if self._exists("kotlin/src") else "⚠️ Partial", "JVM bindings"),
            CompatibilityItem("C1.10", "WebAssembly (browser)", "✅ Complete" if self._exists("wasm") else "⚠️ Partial", "WASM package and browser import path"),
        ]
        return [r.__dict__ for r in rows]

    def hardware_compatibility(self) -> List[Dict[str, str]]:
        rows = [
            CompatibilityItem("C2.1", "Local Rust Simulator", "✅ Complete", "FastBackend statevector simulator"),
            CompatibilityItem("C2.2", "IBM Quantum (IBMQ)", "✅ SDK-wired", "Credential-gated provider execution"),
            CompatibilityItem("C2.3", "Google Quantum AI", "✅ SDK-wired", "Cirq-backed provider adapter"),
            CompatibilityItem("C2.4", "AWS Braket", "✅ SDK-wired", "boto3/AWS Braket adapter"),
            CompatibilityItem("C2.5", "Azure Quantum", "✅ SDK-wired", "Azure backend adapter"),
            CompatibilityItem("C2.6", "IonQ", "✅ SDK-wired", "REST adapter and SDK routing"),
            CompatibilityItem("C2.7", "Rigetti / QCS", "✅ SDK-wired", "pyquil backend adapter"),
            CompatibilityItem("C2.8", "Quantinuum (H-Series)", "✅ SDK-wired", "pytket backend adapter"),
            CompatibilityItem("C2.9", "Pasqal (neutral atoms)", "✅ SDK-wired", "Pulser backend adapter"),
            CompatibilityItem("C2.10", "OQC (Superconducting)", "✅ SDK-wired", "REST backend adapter"),
            CompatibilityItem("C2.11", "QuEra (Aquila)", "✅ SDK-wired", "AWS Braket analog adapter"),
        ]
        return [r.__dict__ for r in rows]

    def interchange_compatibility(self) -> List[Dict[str, str]]:
        rows = [
            CompatibilityItem("C3.1", "OpenQASM 2.0", "✅ Complete", "Import/export parser and serializer"),
            CompatibilityItem("C3.2", "OpenQASM 3.0", "✅ Complete", "Parser/serializer with gate modifiers"),
            CompatibilityItem("C3.3", "Quil (Rigetti)", "✅ Complete", "Quil program model + conversion"),
            CompatibilityItem("C3.4", "QASM-XT (AbirQu ext.)", "✅ Complete", "LDPC and phase-poly extension metadata"),
            CompatibilityItem("C3.5", "QIR (LLVM-based)", "✅ Complete", "JSON + LLVM IR model and converter"),
        ]
        return [r.__dict__ for r in rows]

    def plugin_compatibility(self) -> List[Dict[str, str]]:
        rows = [
            CompatibilityItem("C4.1", "Backend plugin API", "✅ Complete", "QuantumBackend abstract contract"),
            CompatibilityItem("C4.2", "Auto-discovery", "✅ Complete", "importlib.metadata entry-point discovery"),
            CompatibilityItem("C4.3", "Cloud credential manager", "✅ Complete", "Unified provider credential storage"),
            CompatibilityItem("C4.4", "Result normalisation layer", "✅ Complete", "Provider-agnostic NormalizedResult"),
            CompatibilityItem("C4.5", "Transpilation to native gate sets", "✅ Complete", "Gate decomposition and transpilation layer"),
        ]
        return [r.__dict__ for r in rows]

    def validate_interchange_runtime(self) -> Dict[str, bool]:
        from .formats.openqasm2 import OpenQASM2Parser, create_bell_state_qasm
        from .formats.openqasm3 import OpenQASM3Parser, create_bell_state_qasm3
        from .formats.qasm_xt import QASMXTParser, create_bell_state_qasm_xt
        from .formats.qir import create_bell_state_qir, QIRModule
        from .formats.quil import QuilProgram, QuilGate

        q2 = OpenQASM2Parser().parse(create_bell_state_qasm())
        q3 = OpenQASM3Parser().parse(create_bell_state_qasm3())
        qx = QASMXTParser().parse(create_bell_state_qasm_xt())
        qir = QIRModule.from_json(create_bell_state_qir())
        qp = QuilProgram()
        qp.gates.append(QuilGate("H", [0]))
        qp.gates.append(QuilGate("CNOT", [0, 1]))

        return {
            "openqasm2": q2.num_qubits == 2 and len(q2.gates) >= 4,
            "openqasm3": q3.num_qubits == 2 and len(q3.gates) >= 2,
            "qasm_xt": len(qx.gates) >= 2,
            "qir": len(qir.functions) >= 1,
            "quil": "CNOT" in qp.to_quil(),
        }

    def full_report(self) -> Dict[str, object]:
        languages = self.language_compatibility()
        hardware = self.hardware_compatibility()
        interchange = self.interchange_compatibility()
        plugins = self.plugin_compatibility()
        runtime_checks = self.validate_interchange_runtime()

        return {
            "languages": languages,
            "hardware": hardware,
            "interchange": interchange,
            "plugins": plugins,
            "runtime_checks": runtime_checks,
            "summary": {
                "language_count": len(languages),
                "hardware_count": len(hardware),
                "interchange_count": len(interchange),
                "plugin_count": len(plugins),
                "runtime_checks_passed": all(runtime_checks.values()),
            },
        }
