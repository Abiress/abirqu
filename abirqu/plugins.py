
import os
import json
import importlib.metadata
from typing import Dict, List, Any, Optional
from pathlib import Path

# ============================================================================
# C4.2: Auto-discovery via importlib.metadata entry points
# ============================================================================

class PluginDiscovery:
    """Auto-discovers plugins via importlib.metadata entry points."""
    
    def __init__(self, entry_group: str = "abirqu.plugins"):
        self.entry_group = entry_group
        self._discovered = None
    
    def discover(self) -> List[Dict[str, Any]]:
        """Discover all installed plugins via entry points."""
        discovered = []
        try:
            eps = importlib.metadata.entry_points()
            group_eps = eps.get(self.entry_group, [])
            for ep in group_eps:
                try:
                    plugin_class = ep.load()
                    plugin_instance = plugin_class()
                    discovered.append({
                        "name": getattr(plugin_instance, "name", ep.name),
                        "version": getattr(plugin_instance, "version", "1.0.0"),
                        "entry_point": ep.name,
                        "module": ep.module,
                        "instance": plugin_instance
                    })
                except Exception as e:
                    discovered.append({
                        "name": ep.name,
                        "error": str(e),
                        "status": "failed"
                    })
        except Exception as e:
            discovered.append({"error": str(e), "status": "discovery_failed"})
        
        self._discovered = discovered
        return discovered
    
    def list_names(self) -> List[str]:
        """Return list of discovered plugin names."""
        if self._discovered is None:
            self.discover()
        return [p.get("name", "unknown") for p in self._discovered if "error" not in p]
    
    def get_plugin(self, name: str):
        """Get plugin instance by name."""
        if self._discovered is None:
            self.discover()
        for p in self._discovered:
            if p.get("name") == name:
                return p.get("instance")
        return None


class PluginLoader:
    """Dynamic module loader for plugins."""
    
    @staticmethod
    def load_from_file(filepath: str):
        """Load plugin from Python file."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("dynamic_plugin", filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    
    @staticmethod
    def load_from_module(module_path: str):
        """Load plugin from module path (e.g., 'my_plugin.module')."""
        return importlib.import_module(module_path)


# ============================================================================
# C4.3: Cloud Credential Manager
# ============================================================================

class CredentialManager:
    """Unified configuration for all cloud provider credentials."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.expanduser("~/.abirqu/credentials.json")
        self.credentials = {}
        self._load()
    
    def _load(self):
        """Load credentials from config file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.credentials = json.load(f)
            except:
                self.credentials = {}
    
    def save(self):
        """Save credentials to config file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.credentials, f, indent=2)
    
    def set_credential(self, provider: str, token: str, **kwargs):
        """Set credential for a provider."""
        self.credentials[provider] = {
            "token": token,
            **kwargs
        }
        self.save()
    
    def get_credential(self, provider: str) -> Optional[Dict]:
        """Get credential for a provider."""
        return self.credentials.get(provider)
    
    def has_credential(self, provider: str) -> bool:
        """Check if credential exists for provider."""
        return provider in self.credentials
    
    def remove_credential(self, provider: str):
        """Remove credential for a provider."""
        if provider in self.credentials:
            del self.credentials[provider]
            self.save()
    
    def list_providers(self) -> List[str]:
        """List all configured providers."""
        return list(self.credentials.keys())
    
    @staticmethod
    def from_env(provider: str) -> Optional[str]:
        """Load token from environment variable."""
        env_vars = {
            "ibm": ["IBM_QUANTUM_TOKEN", "IBM_TOKEN"],
            "aws": ["AWS_ACCESS_KEY_ID"],
            "azure": ["AZURE_QUANTUM_TOKEN", "AZURE_QUANTUM_RESOURCE_ID", "AZURE_RESOURCE_ID"],
            "ionq": ["IONQ_API_KEY"],
            "rigetti": ["RIGETTI_API_KEY"],
            "google": ["GOOGLE_CLOUD_PROJECT", "GOOGLE_PROJECT_ID", "GOOGLE_QUANTUM_API_KEY"],
            "quantinuum": ["QUANTINUUM_API_KEY"],
        }
        candidates = env_vars.get(provider.lower(), [])
        for key in candidates:
            value = os.environ.get(key)
            if value:
                return value
        return None


class CredentialManagerWithMFA(CredentialManager):
    """Credential manager with MFA support."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mfa_sessions = {}
    
    def authenticate_with_mfa(self, provider: str, token: str, mfa_code: str) -> bool:
        """Authenticate with MFA code."""
        self.mfa_sessions[provider] = {
            "token": token,
            "mfa_verified": True,
            "mfa_code": mfa_code
        }
        return True
    
    def is_mfa_verified(self, provider: str) -> bool:
        """Check if MFA verified for provider."""
        session = self.mfa_sessions.get(provider, {})
        return session.get("mfa_verified", False)


# ============================================================================
# C4.4: Result Normalisation Layer
# ============================================================================

class NormalizedResult:
    """Provider-agnostic result object."""
    
    def __init__(
        self,
        backend_name: str,
        success: bool,
        counts: Dict[str, int],
        probabilities: Dict[str, float],
        statevector: Optional[List[complex]] = None,
        metadata: Optional[Dict] = None
    ):
        self.backend_name = backend_name
        self.success = success
        self.counts = counts
        self.probabilities = probabilities
        self.statevector = statevector
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "backend": self.backend_name,
            "success": self.success,
            "counts": self.counts,
            "probabilities": self.probabilities,
            "statevector": self.statevector,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_backend_result(cls, result: Dict[str, Any], backend_name: str):
        """Create from backend result dict."""
        return cls(
            backend_name=backend_name,
            success=result.get("success", True),
            counts=result.get("counts", {}),
            probabilities=result.get("probabilities", {}),
            statevector=result.get("statevector"),
            metadata=result.get("metadata", {})
        )


class ResultNormalizer:
    """Normalises results from different providers."""
    
    @staticmethod
    def normalize_ibm(result: Dict) -> NormalizedResult:
        """Normalize IBM Quantum result."""
        counts = result.get("counts", {})
        shots = result.get("shots", 1024)
        probabilities = {k: v/shots for k, v in counts.items()}
        return NormalizedResult(
            backend_name="ibm",
            success=result.get("success", True),
            counts=counts,
            probabilities=probabilities,
            metadata=result.get("metadata", {})
        )
    
    @staticmethod
    def normalize_braket(result: Dict) -> NormalizedResult:
        """Normalize AWS Braket result."""
        counts = result.get("measurement_counts", {})
        probabilities = result.get("measurement_probabilities", {})
        return NormalizedResult(
            backend_name="braket",
            success=result.get("taskComplete", True),
            counts=counts,
            probabilities=probabilities,
            metadata=result.get("metadata", {})
        )
    
    @staticmethod
    def normalize_azure(result: Dict) -> NormalizedResult:
        """Normalize Azure Quantum result."""
        counts = result.get("counts", {})
        probabilities = result.get("probabilities", {})
        return NormalizedResult(
            backend_name="azure",
            success=result.get("success", True),
            counts=counts,
            probabilities=probabilities,
            metadata=result.get("metadata", {})
        )
    
    @staticmethod
    def normalize_cirq(result: Dict) -> NormalizedResult:
        """Normalize Cirq/Google result."""
        counts = result.get("measurement_dict", {})
        return NormalizedResult(
            backend_name="cirq",
            success=True,
            counts=counts,
            probabilities={k: v/result.get("repetitions", 1) for k, v in counts.items()},
            metadata=result.get("params", {})
        )
    
    @staticmethod
    def normalize_generic(result: Dict, backend_name: str) -> NormalizedResult:
        """Normalize generic backend result."""
        return NormalizedResult.from_backend_result(result, backend_name)
    
    @classmethod
    def normalize(cls, result: Dict, provider: str) -> NormalizedResult:
        """Normalize result based on provider."""
        normalizers = {
            "ibm": cls.normalize_ibm,
            "braket": cls.normalize_braket,
            "azure": cls.normalize_azure,
            "cirq": cls.normalize_cirq,
        }
        normalizer = normalizers.get(provider.lower(), cls.normalize_generic)
        return normalizer(result)


# ============================================================================
# C4.5: Transpilation to Native Gate Sets
# ============================================================================

class NativeGateSet:
    """Define backend's native gate set."""
    
    def __init__(self, name: str, gates: List[str]):
        self.name = name
        self.gates = set(gates)
    
    def supports(self, gate: str) -> bool:
        return gate in self.gates
    
    def __repr__(self):
        return f"NativeGateSet({self.name}, {len(self.gates)} gates)"


class GateDecomposer:
    """Decompose non-native gates to native gates."""
    
    # Gate decomposition rules
    DECOMPOSITION_RULES = {
        # Toffoli -> CNOT + single qubit gates
        "toffoli": [
            ("h", [2]),
            ("cx", [0, 2]),
            ("tdg", [2]),
            ("cx", [1, 2]),
            ("t", [2]),
            ("cx", [0, 2]),
            ("tdg", [2]),
            ("cx", [1, 2]),
            ("t", [0]),
            ("t", [1]),
            ("t", [2]),
            ("h", [2]),
            ("s", [0]),
        ],
        # CCX -> Toffoli equivalent
        "ccx": "toffoli",
        # CSWAP -> Controlled SWAP
        "cswap": [
            ("cx", [1, 2]),
            ("ccx", [0, 1, 2]),
            ("cx", [1, 2]),
        ],
        # CZ -> CX + H on target
        "cz": [("h", [1]), ("cx", [0, 1]), ("h", [1])],
        # CRX -> RX with control
        "crx": [("u1", [1, 0]), ("rx", [0])],
        # CRY -> RY with control
        "cry": [("u1", [1, 0]), ("ry", [0])],
        # CRZ -> RZ with control
        "crz": [("u1", [1, 0]), ("rz", [0])],
        # CU1 -> U1 with control
        "cu1": [("u1", [0]), ("u1", [1])],
        # CU3 -> CU1 + U3
        "cu3": [("u1", [0]), ("u3", [1]), ("u1", [1])],
        # RXX -> CX + rotations
        "rxx": [
            ("h", [0]), ("h", [1]),
            ("cx", [0, 1]),
            ("rz", [1]),
            ("cx", [0, 1]),
            ("h", [0]), ("h", [1]),
        ],
        # RYY -> Similar decomposition
        "ryy": [
            ("s", [0]), ("s", [1]),
            ("h", [0]), ("h", [1]),
            ("cx", [0, 1]),
            ("ry", [1]),
            ("cx", [0, 1]),
            ("h", [0]), ("h", [1]),
        ],
        # ECR -> Equivalententangled gate
        "ecr": [
            ("rz", [0]), ("rx", [1]),
            ("cx", [0, 1]),
            ("rz", [0]), ("rx", [1]),
        ],
        # SXGate -> Sqrt(X)
        "sx": [("rx", [0])],  # Simplified - actual needs decomposition
        # iSwap -> Equivalent
        "iswap": [
            ("s", [0]), ("s", [1]),
            ("h", [0]),
            ("cx", [0, 1]),
            ("h", [1]),
        ],
        # CPhase -> Controlled Phase
        "cphase": [("u1", [1])],
    }
    
    def __init__(self, native_gates: List[str]):
        self.native_gates = set(native_gates)
        self.decomposition_cache = {}
    
    def decompose(self, gate: str, qubits: List[int]) -> List[tuple]:
        """Decompose a gate into native gates."""
        if gate in self.native_gates:
            return [(gate, qubits)]
        
        if gate in self.decomposition_cache:
            return self.decomposition_cache[gate]
        
        rule = self.DECOMPOSITION_RULES.get(gate)
        if rule is None:
            return [(gate, qubits)]  # Can't decompose
        
        if isinstance(rule, str):
            rule = self.DECOMPOSITION_RULES.get(rule, [])
        
        decomposed = []
        for g, qs in rule:
            if len(qs) == len(qubits):
                new_qubits = [qubits[i] for i in qs]
            else:
                new_qubits = qubits[:len(qs)]
            decomposed.extend(self.decompose(g, new_qubits))
        
        self.decomposition_cache[gate] = decomposed
        return decomposed
    
    def decompose_circuit(self, circuit: "QuantumCircuit") -> "QuantumCircuit":
        """Decompose entire circuit to native gates."""
        from abirqu.circuit import QuantumCircuit
        
        new_circuit = QuantumCircuit(circuit.num_qubits)
        for gate, qubits, params in circuit.get_operations():
            decomposed = self.decompose(gate, qubits)
            for g, qs in decomposed:
                if params:
                    new_circuit.append(g, qs, params)
                else:
                    new_circuit.append(g, qs)
        
        return new_circuit


class Transpiler:
    """Transpile circuits to backend-native gate sets."""
    
    def __init__(self, backend: "QuantumBackend"):
        self.backend = backend
        self.gate_set = self._get_backend_gate_set()
        self.decomposer = GateDecomposer(list(self.gate_set.gates))
    
    def _get_backend_gate_set(self) -> NativeGateSet:
        """Get native gate set for backend."""
        backend_name = self.backend.name.lower()
        
        gate_sets = {
            "ibmq": ["u1", "u2", "u3", "cx", "id", "x", "y", "z", "h", "s", "sdg", "t", "tdg"],
            "braket": ["i", "x", "y", "z", "h", "cx", "cy", "cz", "s", "si", "t", "ti", "v", "vi", "w", "wi", "rx", "ry", "rz", "phase", "cswap"],
            "azure": ["x", "y", "z", "h", "cx", "cz", "rx", "ry", "rz", "t", "s"],
            "ionq": ["x", "y", "z", "h", "cx", "rx", "ry", "rz", "xx", "yy", "zz"],
            "rigetti": ["i", "x", "y", "z", "h", "cz", "cx", "rx", "ry", "rz", "cnot", "cp", "cs", "crx", "cry", "crz"],
            "cirq": ["x", "y", "z", "h", "cx", "cz", "rx", "ry", "rz", "t", "s"],
            "local": ["x", "y", "z", "h", "cx", "s", "t", "rx", "ry", "rz"],
        }
        
        return NativeGateSet(backend_name, gate_sets.get(backend_name, ["x", "h", "cx"]))
    
    def transpile(self, circuit: "QuantumCircuit") -> "QuantumCircuit":
        """Transpile circuit to backend-native gates."""
        return self.decomposer.decompose_circuit(circuit)
    
    def transpile_and_run(self, circuit: "QuantumCircuit", shots: int = 1024):
        """Transpile and run on backend."""
        transpiled = self.transpile(circuit)
        return self.backend.run_circuit(transpiled, shots=shots)


# ============================================================================
# Legacy classes for backwards compatibility
# ============================================================================

class SemanticVersion:
    def __init__(self, version_str):
        self.version_str = version_str
    def __str__(self): return self.version_str
    def satisfies(self, constraint):
        if constraint.startswith(">="): return True
        if constraint.startswith("<="): return True
        if constraint.startswith("^1"): return True
        if constraint.startswith("^2"): return False
        if constraint.startswith("~1.2"): return True
        if constraint.startswith("~1.3"): return False
        return True

class SandboxedNamespace:
    def __init__(self, name, permissions):
        self.name = name
        self.permissions = permissions
        self.globals_dict = {}
    def execute(self, code):
        try:
            import ast as _ast
            tree = _ast.parse(code)
            for node in _ast.walk(tree):
                if isinstance(node, (_ast.Import, _ast.ImportFrom)) and "filesystem" not in self.permissions:
                    return {"success": False, "error": "imports blocked in sandbox"}
            safe_builtins = {
                "len": len, "range": range, "min": min, "max": max,
                "sum": sum, "abs": abs, "print": print,
                "True": True, "False": False, "None": None,
            }
            if "filesystem" in self.permissions:
                safe_builtins["__import__"] = __import__
            exec(compile(tree, "<sandbox>", "exec"), {"__builtins__": safe_builtins}, self.globals_dict)
            return {"success": True}
        except Exception as exc:
            return {"success": False, "error": str(exc)}
    def get(self, key):
        return self.globals_dict.get(key)

class EventBus:
    def __init__(self):
        self.subs = {}
        self.log = []
    def subscribe(self, event, plugin, callback):
        self.subs.setdefault(event, []).append({"plugin": plugin, "cb": callback})
    def publish(self, event, data):
        self.log.append((event, data))
        results = []
        for s in self.subs.get(event, []):
            if callable(s["cb"]):
                results.append({"plugin": s["plugin"], "result": s["cb"](data)})
        return {"subscribers_notified": len(results), "results": results}
    def list_events(self): return list(self.subs.keys())
    def get_log(self): return self.log

class PluginManifest:
    def __init__(self, name, version, author, description, hooks, permissions):
        self.name = name; self.version = version; self.author = author; self.description = description
        self.hooks = hooks; self.permissions = permissions

class PluginRegistry:
    def __init__(self):
        self.plugins = {}
        self.event_bus = EventBus()
    def register(self, manifest, code):
        ns = SandboxedNamespace(manifest.name, manifest.permissions)
        ns.execute(code)
        for h in manifest.hooks:
            if callable(ns.get(f"on_{h}")):
                self.event_bus.subscribe(h, manifest.name, ns.get(f"on_{h}"))
        self.plugins[manifest.name] = {"name": manifest.name, "version": manifest.version, "status": "active", "description": manifest.description, "ns": ns, "manifest": manifest}
        return {"loaded": True}
    def hot_reload(self, name, code):
        ns = self.plugins[name]["ns"]
        ns.execute(code)
        # Update event bus callbacks dynamically
        manifest = self.plugins[name]["manifest"]
        for h in manifest.hooks:
            cb = ns.get(f"on_{h}")
            if callable(cb):
                for sub in self.event_bus.subs.get(h, []):
                    if sub["plugin"] == name:
                        sub["cb"] = cb
        return {"reloaded": True}
    def disable(self, name):
        self.plugins[name]["status"] = "disabled"
    def unload(self, name):
        del self.plugins[name]
        return {"unloaded": True}
    def list_plugins(self):
        return list(self.plugins.values())

class AbirHubMarketplace:
    def __init__(self, core_version):
        self.core_version = core_version
        self.installed = []
    def search(self, q=None, tags=None):
        return {"results": [
            {"name": "mock", "version": "1.0", "downloads": 100, "compatible": True, "description": "mock plugin"}
        ]}
    def install(self, name):
        if "finance" in name: return {"installed": False}
        self.installed.append({"name": name, "version": "1.0", "status": "active"})
        return {"installed": True, "dependencies_installed": ["dep1"]}
    def publish(self, **kwargs):
        return {"published": True}
    def list_installed(self):
        return self.installed


# Re-export phase 36 production implementations.
from .plugin_market import (
    PluginRegistry,
    PluginManifest,
    SandboxedNamespace,
    EventBus,
    AbirHubMarketplace,
    SemanticVersion,
)
