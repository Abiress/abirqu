"""AbirQu — next-generation quantum computing library."""

__version__ = "0.1.0"
__author__ = "Abir Maheshwari"
__email__ = "abhirsxn@gmail.com"
__url__ = "https://github.com/abirqu/abirqu"

# Core exports
from .circuit import Circuit, Gate, Measurement
from .gates import X, Y, Z, H, S, S_dag, T, T_dag, CNOT, CZ, SWAP, rx, ry, rz
from .backend import QuantumBackend
from .noise import NoiseModel
from .numpy_sim import NumPySimulator
from .tracker import QuantumAdvantageTracker
from .compatibility import CompatibilityManager
from .mitigation import ErrorMitigationFlow, counts_to_probabilities
from .security import CircuitProtector, AccessController, EncryptedCircuit, sign_payload, verify_signature
from .patterns import (
    PatternKind,
    PatternMatch,
    detect_patterns,
    initialization_pattern,
    superposition_pattern,
    entanglement_pattern,
    oracle_pattern,
    PatternAwareOptimizer,
    PatternRegistry,
)

# Format exports
from .formats import openqasm2, openqasm3, quil, qir, qasm_xt

phases = None

def cli_main(argv=None):
    from .cli import main
    return main(argv)

def __getattr__(name):
    plugin_exports = {
        "PluginDiscovery",
        "CredentialManager",
        "CredentialManagerWithMFA",
        "ResultNormalizer",
        "NormalizedResult",
        "NativeGateSet",
        "GateDecomposer",
        "Transpiler",
        "PluginRegistry",
        "PluginManifest",
        "EventBus",
    }
    if name in plugin_exports:
        from . import plugins as _plugins
        return getattr(_plugins, name)
    if name == "AbirQuSDK":
        from .sdk import AbirQuSDK as _AbirQuSDK
        return _AbirQuSDK
    if name == "phases":
        from . import phases as _phases
        return _phases
    raise AttributeError(name)

__all__ = [
    # Core
    "Circuit", "Gate", "Measurement",
    "X", "Y", "Z", "H", "S", "S_dag", "T", "T_dag", "CNOT", "CZ", "SWAP", "rx", "ry", "rz",
    "QuantumBackend", "NoiseModel", "NumPySimulator", "phases",
    # Phase 4/6/8 runtime modules
    "cli_main", "QuantumAdvantageTracker",
    "AbirQuSDK", "ErrorMitigationFlow", "counts_to_probabilities",
    "CompatibilityManager",
    "CircuitProtector", "AccessController", "EncryptedCircuit", "sign_payload", "verify_signature",
    "PatternKind", "PatternMatch", "detect_patterns",
    "initialization_pattern", "superposition_pattern", "entanglement_pattern", "oracle_pattern",
    "PatternAwareOptimizer", "PatternRegistry",
    # Plugins
    "PluginDiscovery", "CredentialManager", "CredentialManagerWithMFA",
    "ResultNormalizer", "NormalizedResult", "NativeGateSet", "GateDecomposer", "Transpiler",
    "PluginRegistry", "PluginManifest", "EventBus",
    # Formats
    "openqasm2", "openqasm3", "quil", "qir", "qasm_xt",
]
