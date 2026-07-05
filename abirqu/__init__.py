"""AbirQu — next-generation quantum computing library."""

from packaging.version import Version as _Version

__version__ = "1.0.2"
__author__ = "Abir Maheshwari"
__email__ = "abhirsxn@gmail.com"
__url__ = "https://github.com/abirqu/abirqu"

# Experimental markers — hardware backends beyond IBM are experimental
# and may change or be removed without following the standard deprecation
# timeline.

# Core exports
from .circuit import Circuit, Gate, Measurement
from .exceptions import (
    AbirQuError,
    CircuitError,
    SimulationError,
    BackendError,
    TranspilerError,
    HardwareError,
    QuantumCommunicationError,
    ConfigurationError,
    AuthenticationError,
    JobError,
)
from .logging_config import setup_logging
from .gates import X, Y, Z, H, S, S_dag, T, T_dag, CNOT, CZ, SWAP, rx, ry, rz
from .backend import (
    QuantumBackend,
    FastBackend,
    BackendRegistry,
    JobStatus,
    JobHandle,
    get_best_backend,
)
from .converters import (
    convert_circuit,
    to_qiskit,
    to_braket,
    to_cirq,
    to_ionq_json,
    to_pytket,
    to_quil,
    to_openqasm,
)
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

# Transpiler
from .transpiler import TranspilerPipeline, TargetBackend
from .transpiler.topology import CouplingMap
from .transpiler.routing import RoutingPass
from .transpiler.scheduling import SchedulingPass
from .transpiler.fidelity import FidelityEstimator

# Quantum OS
from .quantum_os import (
    QuantumJob, JobState,
    QuantumScheduler, SchedulingPolicy,
    JobQueue, ResourceManager, VirtualQPU, CostEstimator,
    PreemptionManager, ReservationSystem, CircuitPartitioner,
    VirtualEnvironment, JobMonitor, TenantManager, AccessController,
)

# D-Wave
from .dwave import (
    QUBOBuilder, AnnealingSchedule, HybridSolver, DWaveTopology,
    circuit_to_qubo, circuit_to_ising,
)

# Simulators
from .simulation import (
    GPUSimulator, CliffordSimulator, MPSSimulator,
    is_clifford_only, estimate_bond_dimension,
)

# Primitives (unified execution)
from .primitives import (
    QuantumRun, SamplerResult, EstimatorResult, MitigationResult, QNNResult,
    Sampler, QuasiDistribution, Estimator, QNN,
)

# Visualization
from .visualization import (
    CircuitDrawer, draw,
    draw_text, draw_ascii, draw_svg, draw_html,
    BlochSphere,
    histogram_text, histogram_svg,
    stateplot_svg, probability_svg, stateplot_ascii,
    gate_map_svg, error_map_svg,
    noise_fingerprint_svg, circuit_fingerprint_svg,
)

# Circuit Library
from .library import (
    real_amplitudes, efficient_su2, n_local,
    qaoa_circuit, qaoa_maxcut,
    vqe_hardware_efficient, vqe_uccsd, vqe_custom,
    angle_encoding, amplitude_encoding, zz_feature_map, iqp_encoding,
    ghz_circuit, w_state, qft_circuit, grover_circuit,
    grover_oracle, bernstein_vazirani_circuit, quantum_fourier_transform,
    random_circuit,
)

# Noise Toolkit
from .noise_toolkit import (
    ZeroNoiseExtrapolator, ReadoutMitigator, M3Mitigator,
    PECCorrector, generate_calibration_circuits, generate_zne_circuits,
)

# Addons
from .addons import (
    MultiProductFormula, TrotterSuzuki, CircuitCutter,
    AQCTensor, OperatorBackpropagation, SQDCorrector,
)

# ─── Production Modules ───────────────────────────────────────────────

# Quantum Chemistry (Pharmaceuticals & Drug Discovery)
from .chemistry import (
    JordanWignerMapper, BravyiKitaevMapper, ParityMapper,
    FermionicOperator, build_hamiltonian_from_integrals,
    PySCFHook, OpenFermionHook, MolecularData, run_molecular_vqe,
    MatchgateShadows,
)

# OSINT & Intelligence (Graph Analysis & Data Encoding)
from .osint import (
    IntelligenceGraph, GraphNode, GraphEdge, GraphToIsingCompiler,
    QuantumDataEncoder, QRAMEmulator, TensorNetworkEmbedding,
)

# Cryptanalysis (Oracle Synthesis & Lattice Simulation)
from .crypto import (
    OracleSynthesizer, ModularArithmetic, LatticeSimulation,
)

# Space & Deep Tech (HHL Solver & Q-PINNs)
from .space import HHLSolver
from .qpinn import QPINN, NavierStokesQPINN, PDESpec, TrainingConfig

# Agentic Orchestration
from .agentic import (
    MultiGPUSimulator, AgentOrchestrator, DistributedQuantumComputer,
    ExecutionTarget, ExecutionPlan,
)

# Format exports
from .formats import openqasm2, openqasm3, quil, qir, qasm_xt

# Backend exports (lazy — only import when accessed)
phases = None


def cli_main(argv=None):
    from .cli import main
    return main(argv)


def check_version_compatibility(required_version: str) -> bool:
    """Check if the installed AbirQu version satisfies a minimum requirement.

    Args:
        required_version: Minimum version string (e.g. "1.2.0").

    Returns:
        True if the current version >= required_version, False otherwise.

    Raises:
        ValueError: If *required_version* is not a valid version string.

    Example:
        >>> check_version_compatibility("1.0.0")
        True
        >>> check_version_compatibility("2.0.0")
        False
    """
    current = _Version(__version__)
    required = _Version(required_version)
    return current >= required


# ─── Experimental API markers ────────────────────────────────────────
# Hardware backends beyond IBM are considered experimental and may
# change or be removed without following the standard deprecation
# timeline.  The following lazy-imported backends carry the experimental
# tag: Braket, Azure, Google, IonQ, Rigetti, Quantinuum, Pasqal, OQC,
# QuEra, DWave, and SpinQ.

def __getattr__(name):
    # Plugin exports
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

    # Backend imports (lazy)
    backend_imports = {
        "IBMQuantumBackend": (".backends.ibm", "IBMQuantumBackend"),
        "BraketBackend": (".backends.aws", "BraketBackend"),
        "AzureQuantumBackend": (".backends.azure", "AzureQuantumBackend"),
        "GoogleQuantumBackend": (".backends.google", "GoogleQuantumBackend"),
        "IonQBackend": (".backends.ionq", "IonQBackend"),
        "RigettiBackend": (".backends.rigetti", "RigettiBackend"),
        "QuantinuumBackend": (".backends.quantinuum", "QuantinuumBackend"),
        "PasqalBackend": (".backends.pasqal", "PasqalBackend"),
        "OQCBackend": (".backends.oqc", "OQCBackend"),
        "QuEraBackend": (".backends.quera", "QuEraBackend"),
        "DWaveBackend": (".backends.dwave", "DWaveBackend"),
        "SpinQBackend": (".backends.spinq", "SpinQBackend"),
    }
    _experimental_backends = {
        "BraketBackend", "AzureQuantumBackend", "GoogleQuantumBackend",
        "IonQBackend", "RigettiBackend", "QuantinuumBackend", "PasqalBackend",
        "OQCBackend", "QuEraBackend", "DWaveBackend", "SpinQBackend",
    }
    if name in backend_imports:
        module_path, attr_name = backend_imports[name]
        import importlib
        mod = importlib.import_module(module_path, package="abirqu")
        obj = getattr(mod, attr_name)
        if name in _experimental_backends:
            import warnings
            warnings.warn(
                f"{name} is an experimental backend. "
                "Its API may change or be removed without notice.",
                UserWarning,
                stacklevel=2,
            )
        return obj

    if name == "AbirQuSDK":
        from .sdk import AbirQuSDK as _AbirQuSDK
        return _AbirQuSDK

    if name == "quantum_os":
        import warnings
        warnings.warn(
            "abirqu.quantum_os is experimental and its API may change without notice.",
            UserWarning,
            stacklevel=2,
        )
        from . import quantum_os as _qos
        return _qos

    # Hardware module imports (lazy)
    hardware_imports = {
        "HardwareCalibration": (".hardware.calibration", "HardwareCalibration"),
        "QubitProperties": (".hardware.calibration", "QubitProperties"),
        "GateProperties": (".hardware.calibration", "GateProperties"),
        "DeviceCharacterizer": (".hardware.characterization", "DeviceCharacterizer"),
        "NoiseProfiler": (".hardware.noise_profiler", "NoiseProfiler"),
        "HardwareAwareCompiler": (".hardware.hw_compiler", "HardwareAwareCompiler"),
        "CloudManager": (".hardware.cloud_manager", "CloudManager"),
        "CloudProvider": (".hardware.cloud_manager", "CloudProvider"),
    }
    if name in hardware_imports:
        module_path, attr_name = hardware_imports[name]
        import importlib
        mod = importlib.import_module(module_path, package="abirqu")
        return getattr(mod, attr_name)

    raise AttributeError(name)


__all__ = [
	# Core
	"Circuit", "Gate", "Measurement",
	# Exceptions
	"AbirQuError", "CircuitError", "SimulationError", "BackendError",
	"TranspilerError", "HardwareError", "QuantumCommunicationError",
	"ConfigurationError", "AuthenticationError", "JobError",
	# Logging
	"setup_logging",
	"X", "Y", "Z", "H", "S", "S_dag", "T", "T_dag", "CNOT", "CZ", "SWAP", "rx", "ry", "rz",
    # Backend framework
    "QuantumBackend", "FastBackend", "BackendRegistry", "JobStatus", "JobHandle",
    "get_best_backend",
    # Converters
    "convert_circuit", "to_qiskit", "to_braket", "to_cirq", "to_ionq_json",
    "to_pytket", "to_quil", "to_openqasm",
    # Transpiler
    "TranspilerPipeline", "TargetBackend", "CouplingMap", "RoutingPass",
    "SchedulingPass", "FidelityEstimator",
    # Quantum OS
    "QuantumJob", "JobState", "QuantumScheduler", "SchedulingPolicy",
    "JobQueue", "ResourceManager", "VirtualQPU", "CostEstimator",
    "PreemptionManager", "ReservationSystem", "CircuitPartitioner",
    "VirtualEnvironment", "JobMonitor", "TenantManager",
    # D-Wave
    "QUBOBuilder", "AnnealingSchedule", "HybridSolver", "DWaveTopology",
    "circuit_to_qubo", "circuit_to_ising",
    # Simulators
    "GPUSimulator", "CliffordSimulator", "MPSSimulator",
    "is_clifford_only", "estimate_bond_dimension",
    # Other
    "NoiseModel", "NumPySimulator", "phases",
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
    # Primitives
    "QuantumRun", "SamplerResult", "EstimatorResult", "MitigationResult", "QNNResult",
    "Sampler", "QuasiDistribution", "Estimator", "QNN",
    # Visualization
    "CircuitDrawer", "draw", "draw_text", "draw_ascii", "draw_svg", "draw_html",
    "BlochSphere", "histogram_text", "histogram_svg",
    "stateplot_svg", "probability_svg", "stateplot_ascii",
    "gate_map_svg", "error_map_svg",
    "noise_fingerprint_svg", "circuit_fingerprint_svg",
    # Circuit Library
    "real_amplitudes", "efficient_su2", "n_local",
    "qaoa_circuit", "qaoa_maxcut",
    "vqe_hardware_efficient", "vqe_uccsd", "vqe_custom",
    "angle_encoding", "amplitude_encoding", "zz_feature_map", "iqp_encoding",
    "ghz_circuit", "w_state", "qft_circuit", "grover_circuit",
    "grover_oracle", "bernstein_vazirani_circuit", "quantum_fourier_transform",
    "random_circuit",
    # Noise Toolkit
    "ZeroNoiseExtrapolator", "ReadoutMitigator", "M3Mitigator",
    "PECCorrector", "generate_calibration_circuits", "generate_zne_circuits",
    # Addons
    "MultiProductFormula", "TrotterSuzuki", "CircuitCutter",
    "AQCTensor", "OperatorBackpropagation", "SQDCorrector",
    # Scalable Unitary Synthesis
    "synthesize_unitary", "ScalableUnitarySynthesizer",
    # Automated Adaptive Error Mitigation
    "AdaptiveErrorMitigator", "NoiseProfiler", "DriftMonitor", "StrategySelector",
    # Pulse-Level Translation
    "AutomatedPulseEngine", "PulseTranslator", "PulseScheduler", "PulseOptimizer", "HardwareProfile",
    # Formats
    "openqasm2", "openqasm3", "quil", "qir", "qasm_xt",
    # Backends (lazy)
    "IBMQuantumBackend", "BraketBackend", "AzureQuantumBackend", "GoogleQuantumBackend",
    "IonQBackend", "RigettiBackend", "QuantinuumBackend", "PasqalBackend",
    "OQCBackend", "QuEraBackend", "DWaveBackend", "SpinQBackend",
    # ─── Production Modules ───────────────────────────────────────
    # Quantum Chemistry
    "JordanWignerMapper", "BravyiKitaevMapper", "ParityMapper",
    "FermionicOperator", "build_hamiltonian_from_integrals",
    "PySCFHook", "OpenFermionHook", "MolecularData", "run_molecular_vqe",
    "MatchgateShadows",
    # OSINT & Intelligence
    "IntelligenceGraph", "GraphNode", "GraphEdge", "GraphToIsingCompiler",
    "QuantumDataEncoder", "QRAMEmulator", "TensorNetworkEmbedding",
    # Cryptanalysis
    "OracleSynthesizer", "ModularArithmetic", "LatticeSimulation",
    # Space & Deep Tech
    "HHLSolver", "QPINN", "NavierStokesQPINN", "PDESpec", "TrainingConfig",
    # Agentic Orchestration
    "MultiGPUSimulator", "AgentOrchestrator", "DistributedQuantumComputer",
    "ExecutionTarget", "ExecutionPlan",
    # Hardware Control (v1.0.0)
    "HardwareCalibration", "QubitProperties", "GateProperties",
    "DeviceCharacterizer", "NoiseProfiler", "HardwareAwareCompiler",
    "CloudManager", "CloudProvider",
    # Version utilities
    "check_version_compatibility",
]
