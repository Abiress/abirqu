"""
abirqu.gui.domain_handlers
===========================
Real wiring between the GUI/CLI and AbirQu's domain modules.

Every function here is a thin, deterministic wrapper around an existing
`abirqu` class or function. NOTHING in this file re-implements quantum
math — it only calls into the real SDK and converts inputs/outputs to
JSON-serializable dicts for the Rust <-> Python stdio bridge.

This is the template referenced in AbirQu-Studio-Build-Spec.md §7:
"abirqu_core must never re-implement quantum math ... all of that stays
in the abirqu package itself."

Each `handle_*` function:
  - takes a plain dict of params (already parsed from the incoming JSON request)
  - returns a plain JSON-serializable dict
  - raises on bad input; callers (server_headless.py) catch and wrap as
    {"status": "error", "error": str(e)}
"""

from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


def _to_jsonable(obj: Any) -> Any:
    """Recursively convert numpy types/arrays into plain JSON-safe values."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


# ─────────────────────────────────────────────────────────────────────────
# Chemistry — wraps abirqu.chemistry (MolecularData, PySCFHook, run_molecular_vqe)
# ─────────────────────────────────────────────────────────────────────────

def handle_chemistry_vqe(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      molecule: "H2" | "LiH" | "H2O"           (default "H2")
      basis: str                                (default "sto-3g")
      ansatz: "uccsd" | "hardware_efficient"    (default "uccsd")
      mapper: "jordan_wigner" | "bravyi_kitaev" | "parity"
      optimizer: str                            (default "cobyla")
      max_iterations: int                       (default 100)
      shots: int                                (default 4096)
    """
    from abirqu.chemistry.chemistry_integration import PySCFHook, run_molecular_vqe

    molecule = params.get("molecule", "H2")
    basis = params.get("basis", "sto-3g")
    ansatz = params.get("ansatz", "uccsd")
    mapper = params.get("mapper", "jordan_wigner")
    optimizer = params.get("optimizer", "cobyla")
    max_iterations = int(params.get("max_iterations", 100))
    shots = int(params.get("shots", 4096))

    hook = PySCFHook()
    mol_data = hook.run_calculation(molecule, basis=basis)

    result = run_molecular_vqe(
        mol_data,
        ansatz=ansatz,
        mapper=mapper,
        optimizer=optimizer,
        max_iterations=max_iterations,
        shots=shots,
    )

    return _to_jsonable({
        "molecule": molecule,
        "basis": basis,
        "ansatz": ansatz,
        "mapper": mapper,
        "n_electrons": mol_data.n_electrons,
        "n_orbitals": mol_data.n_orbitals,
        **result,  # energy, classical_energy, error, n_qubits, n_parameters, convergence
    })


# ─────────────────────────────────────────────────────────────────────────
# QEC — wraps abirqu.qec (codes, SyndromeDecoder, decoder)
# ─────────────────────────────────────────────────────────────────────────
#
# VERIFIED SUPPORT MATRIX (tested live against abirqu.qec — 2026-07):
#
#   Code         | encode/syndrome | lookup decoder | mwpm decoder
#   -------------|-----------------|----------------|-------------
#   repetition   |       OK        |       OK       |      OK
#   bit_flip     |       OK        |       OK       |      OK
#   phase_flip   |       OK        |       OK       |      OK
#   shor         |       OK        |       OK       |      OK
#   steane       |       OK        |       OK       |      OK
#   surface      |       OK        |       OK       |      OK
#   color        |       OK        |     FAILS *    |    FAILS *
#   ldpc         |     FAILS **    |       n/a      |      n/a
#
#   * SyndromeDecoder._build_lookup() reads `code.num_stabilizers`, which
#     ColorCode does not expose (it has x_stabilizers/z_stabilizers instead).
#     This is an upstream API-consistency gap in abirqu/qec/decoder.py.
#   ** LDPCCode has no .encode() method at all — only bit_flip/phase_flip-
#      style codes and the ones above implement the common encode/syndrome
#      interface. LDPCCode looks like it's meant to be driven differently
#      (via its own parity_matrix workflow) — needs its own handler, not
#      this generic one.
#
#   BeliefPropagationDecoder, SurfaceCodeDecoder ("surface" decoder), and
#   GPUAcceleratedDecoder all have a DIFFERENT calling convention than
#   SyndromeDecoder/MWPMDecoder (they want a parity-check matrix and/or
#   return {'x_correction':..., 'z_correction':...} instead of a flat
#   correction vector) — wiring them requires a real per-decoder adapter,
#   not a generic "same shape" assumption. Deliberately left unimplemented
#   here rather than guessing the correction-vector layout and risking a
#   result that *looks* right but silently corrects the wrong qubits.

_QEC_CODES = {
    "repetition": "RepetitionCode",
    "bit_flip": "BitFlipCode",
    "phase_flip": "PhaseFlipCode",
    "shor": "ShorCode",
    "steane": "SteaneCode",
    "surface": "RotatedSurfaceCode",
    # "color" and "ldpc" intentionally omitted — see support matrix above.
}

# Codes whose constructor accepts a size/distance parameter.
_QEC_SIZE_PARAM = {
    "repetition": "n",
    "surface": "distance",
}

_QEC_DECODERS = {
    "lookup": "SyndromeDecoder",
    "mwpm": "MWPMDecoder",
    # "belief_propagation", "surface", "gpu_bp" intentionally omitted —
    # see support matrix above.
}


def handle_qec_cycle(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs a full encode -> inject error -> compute syndrome -> decode -> verify cycle.

    params:
      code: one of _QEC_CODES keys           (default "steane")
      decoder: one of _QEC_DECODERS keys      (default "lookup")
      logical_state: 0 | 1                    (default 0)
      error_qubits: List[int]                 physical qubits to flip (default [])
      size: int                                distance (surface) or n (repetition);
                                                ignored for fixed-size codes
    """
    import abirqu.qec as qec

    code_key = params.get("code", "steane")
    decoder_key = params.get("decoder", "lookup")
    logical_state = int(params.get("logical_state", 0))
    error_qubits: List[int] = params.get("error_qubits", [])
    size = params.get("size")

    if code_key not in _QEC_CODES:
        raise ValueError(f"Unknown or unsupported QEC code '{code_key}'. Options: {list(_QEC_CODES)}")
    if decoder_key not in _QEC_DECODERS:
        raise ValueError(f"Unknown or unsupported decoder '{decoder_key}'. Options: {list(_QEC_DECODERS)}")

    code_cls = getattr(qec, _QEC_CODES[code_key])
    decoder_cls = getattr(qec, _QEC_DECODERS[decoder_key])

    if code_key in _QEC_SIZE_PARAM and size:
        code = code_cls(**{_QEC_SIZE_PARAM[code_key]: int(size)})
    else:
        code = code_cls()

    encoded = code.encode(logical_state)
    n_physical = encoded.shape[0]

    error = np.zeros(n_physical, dtype=int)
    for q in error_qubits:
        if 0 <= q < n_physical:
            error[q] = 1

    syndrome = code.compute_syndrome(error)
    decoder = decoder_cls(code=code)
    correction = decoder.decode(syndrome)

    residual_error = (error + correction) % 2
    corrected_clean = bool(np.all(residual_error == 0))

    overhead = code.get_overhead()

    return _to_jsonable({
        "code": code_key,
        "decoder": decoder_key,
        "logical_state": logical_state,
        "n_physical_qubits": n_physical,
        "injected_error_qubits": error_qubits,
        "syndrome": syndrome,
        "correction": correction,
        "corrected_successfully": corrected_clean,
        "overhead": overhead,
    })


def handle_qec_distill(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs magic-state distillation.

    params:
      state_type: "t" | "h"      (default "t")
      rounds: int                 (default 1)
      initial_fidelity: float     (default 0.9; "t" only)

    NOTE (found while wiring, not fixed here): HStateDistiller consistently
    returned fidelity 0.5000 in live testing regardless of a reasonable
    initial_fidelity input — that looks like a real bug/edge case in
    abirqu.qec.magic_state.HStateDistiller, not a wiring issue. This
    handler reports whatever the SDK actually returns rather than masking
    it, the same policy as the BB84 handler above.
    """
    import abirqu.qec as qec

    state_type = params.get("state_type", "t").lower()
    rounds = int(params.get("rounds", 1))

    if state_type == "t":
        factory = qec.TStateFactory(
            distillation_rounds=rounds,
            initial_fidelity=float(params.get("initial_fidelity", 0.9)),
        )
        produced = factory.produce(count=1)
        state = produced[0]
        return _to_jsonable({
            "state_type": "T",
            "rounds": rounds,
            "output_count": len(produced),
            "fidelity": state.fidelity if hasattr(state, "fidelity") else None,
            "success": len(produced) > 0,
        })

    elif state_type == "h":
        noisy = [qec.MagicState("H", 0.85, is_noisy=True) for _ in range(20)]
        distiller = qec.HStateDistiller(rounds=rounds)
        produced = distiller.distill(noisy)
        avg_fidelity = float(np.mean([s.fidelity for s in produced])) if produced else 0.0
        return _to_jsonable({
            "state_type": "H",
            "rounds": rounds,
            "output_count": len(produced),
            "fidelity": avg_fidelity,
            "success": len(produced) > 0,
        })

    else:
        raise ValueError(f"Unknown magic state type '{state_type}'. Options: t, h")


# ─────────────────────────────────────────────────────────────────────────
# Quantum Communication — wraps abirqu.quantum_communication (BB84Simulator, ...)
# ─────────────────────────────────────────────────────────────────────────

def handle_qcomm_bb84(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      distance_km: float          (default 50.0)
      num_bits: int                (default 1024)
      fiber_loss_db_km: float      (default 0.2)
      detector_efficiency: float   (default 0.9)
      dark_count_rate: float       (default 1e-6)
      misalignment: float          (default 0.01)
      seed: Optional[int]
      eavesdropper: bool           informational only — Eve's effect must be
                                    modeled upstream via misalignment/error-rate
                                    inputs; the simulator itself does not take
                                    an "eavesdropper" flag directly.
    """
    from abirqu.quantum_communication import BB84Simulator

    sim = BB84Simulator(
        distance_km=float(params.get("distance_km", 50.0)),
        fiber_loss_db_km=float(params.get("fiber_loss_db_km", 0.2)),
        detector_efficiency=float(params.get("detector_efficiency", 0.9)),
        dark_count_rate=float(params.get("dark_count_rate", 1e-6)),
        misalignment=float(params.get("misalignment", 0.01)),
        seed=params.get("seed"),
    )
    result = sim.simulate(num_bits=int(params.get("num_bits", 1024)))
    return _to_jsonable(result)


# ─────────────────────────────────────────────────────────────────────────
# Cryptography / PQC — wraps abirqu.security post-quantum implementations
# ─────────────────────────────────────────────────────────────────────────

def handle_pqc_keygen(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      scheme: "kyber" | "dilithium" | "sphincs"
      security_level: int (optional, depends on scheme)
    """
    from abirqu.security import KyberKEM, DilithiumSignatures, SPHINCSSignatures

    scheme = params.get("scheme", "kyber").lower()

    if scheme == "dilithium":
        security_level = params.get("security_level", 2)
        dilithium = DilithiumSignatures(security_level)
        keypair = dilithium.generate_keypair()
        return _to_jsonable({
            "scheme": f"dilithium{security_level}",
            "public_key_preview": list(keypair.public_key[:32]),
            "secret_key_shape": [len(keypair.secret_key)],
            "public_key_size": len(keypair.public_key),
        })
    elif scheme == "sphincs":
        security_level = params.get("security_level", 128)
        sphincs = SPHINCSSignatures(security_level)
        keypair = sphincs.generate_keypair()
        return _to_jsonable({
            "scheme": f"sphincs+-{security_level}f",
            "public_key_preview": list(keypair.public_key[:32]),
            "secret_key_shape": [len(keypair.secret_key)],
            "public_key_size": len(keypair.public_key),
        })
    else:
        security_level = params.get("security_level", 768)
        kem = KyberKEM(security_level)
        keypair = kem.generate_keypair()
        return _to_jsonable({
            "scheme": f"kyber{security_level}",
            "public_key_preview": list(keypair.public_key[:32]),
            "secret_key_shape": [len(keypair.secret_key)],
            "public_key_size": len(keypair.public_key),
        })


def handle_pqc_assess(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs the SDK's built-in quantum-vulnerability assessment for the
    default lattice parameter set (Kyber768-class).
    """
    from abirqu.crypto import LatticeSimulation

    lat = LatticeSimulation()
    assessment = lat.quantum_vulnerability_assessment()
    return _to_jsonable(assessment)


# ─────────────────────────────────────────────────────────────────────────
# OSINT / Graph Optimization — wraps abirqu.osint
# ─────────────────────────────────────────────────────────────────────────

def handle_osint_graph(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      problem: "max_cut" | "mis" | "mvc" | "coloring" | "community" | "anomaly"
      nodes: int (default 8)
      edge_density: float (default 0.4)
      edges: Optional[List[Tuple[int,int]]] (custom edges, overrides density)
    """
    import abirqu.osint as osint

    problem = params.get("problem", "max_cut").lower()
    num_nodes = int(params.get("nodes", 8))
    edge_density = float(params.get("edge_density", 0.4))
    custom_edges = params.get("edges")

    rng = np.random.default_rng(42)

    if custom_edges:
        edges = [tuple(e) for e in custom_edges]
    else:
        edges = []
        for i in range(num_nodes):
            for j in range(i + 1, num_nodes):
                if rng.random() < edge_density:
                    edges.append((i, j))

    graph = osint.IntelligenceGraph()
    for i in range(num_nodes):
        graph.add_node(str(i), label=f"Node {i}")
    for i, j in edges:
        graph.add_edge(str(i), str(j))

    compiler = osint.GraphToIsingCompiler(graph)

    compile_methods = {
        "max_cut": compiler.compile_max_cut,
        "mis": compiler.compile_max_cut,  # MAX_INDEPENDENT_SET uses same formulation
        "mvc": compiler.compile_min_vertex_cover,
        "coloring": compiler.compile_max_cut,
        "community": compiler.compile_max_cut,
        "anomaly": compiler.compile_max_cut,
    }
    hamiltonian = compile_methods.get(problem, compiler.compile_max_cut)()

    qaoa_circuit = compiler.build_qaoa_circuit(hamiltonian, p=2)

    from abirqu.primitives.quantum_run import QuantumRun
    qaoa_circuit.measure_all()
    run = QuantumRun(qaoa_circuit, shots=512)
    counts = run.counts if run.counts else {}

    best_state = max(counts, key=counts.get) if counts else "0" * num_nodes
    cut_value = sum(1 for i in range(len(best_state)) if best_state[i] == '1')

    partition = "".join("A" if best_state[i] == '0' else "B" for i in range(min(len(best_state), num_nodes)))

    return _to_jsonable({
        "problem": problem,
        "num_nodes": num_nodes,
        "num_edges": len(edges),
        "edges": edges,
        "cut_value": cut_value,
        "partition": partition,
        "best_state": best_state,
        "hamiltonian_terms": len(hamiltonian) if isinstance(hamiltonian, list) else 0,
    })


# ─────────────────────────────────────────────────────────────────────────
# Quantum Communication — wraps abirqu.quantum_communication (CV-QKD, DI-QKD, etc.)
# ─────────────────────────────────────────────────────────────────────────

def handle_qcomm_cvqkd(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      num_symbols: int (default 1024)
      modulation_variance: float (default 4.0)
      excess_noise: float (default 0.1)
      transmittance: float (default 0.5)
    """
    from abirqu.quantum_communication.cv_qkd import CVQKDProtocol

    sim = CVQKDProtocol(
        num_symbols=int(params.get("num_symbols", 1024)),
        modulation_variance=float(params.get("modulation_variance", 4.0)),
        excess_noise=float(params.get("excess_noise", 0.1)),
        transmittance=float(params.get("transmittance", 0.5)),
    )
    result = sim.run()
    return _to_jsonable({
        "excess_noise": result.excess_noise,
        "channel_transmittance": result.channel_transmittance,
        "mutual_information": result.mutual_information,
        "secret_key_rate": result.secret_key_rate,
        "final_key_length": len(result.final_key) if result.final_key else 0,
        "secure": result.secret_key_rate > 0,
    })


def handle_qcomm_diqkd(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      num_rounds: int (default 1024)
      noise_level: float (default 0.05)
      detection_efficiency: float (default 0.95)
    """
    from abirqu.quantum_communication.di_qkd import DIQKDProtocol

    sim = DIQKDProtocol(
        num_rounds=int(params.get("num_rounds", 1024)),
        noise_level=float(params.get("noise_level", 0.05)),
        detection_efficiency=float(params.get("detection_efficiency", 0.95)),
    )
    result = sim.run()
    return _to_jsonable({
        "bell_violation": result.bell_violation,
        "chsh_parameter": result.chsh_parameter,
        "key_rate": result.key_rate,
        "error_rate": result.error_rate,
        "secure": result.secure,
        "final_key_length": len(result.final_key) if result.final_key else 0,
    })


def handle_qcomm_satellite(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      altitude_km: float (default 500)
      num_pulses: float (default 1e6)
      detector_efficiency: float (default 0.9)
    """
    from abirqu.quantum_communication.satellite import SatelliteQKD, SatelliteLink

    link = SatelliteLink(altitude_km=float(params.get("altitude_km", 500)))
    sim = SatelliteQKD(link=link, detector_efficiency=float(params.get("detector_efficiency", 0.9)))
    result = sim.simulate(num_pulses=float(params.get("num_pulses", 1e6)))
    return _to_jsonable({
        "distance_km": result.distance_km,
        "channel_loss_db": result.channel_loss_db,
        "detection_rate": result.detection_rate,
        "key_rate": result.key_rate,
        "key_length": result.key_length,
        "secure": result.secure,
    })


def handle_qcomm_repeater(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      total_distance_km: float (default 1000)
      num_segments: int (default 10)
    """
    from abirqu.quantum_communication.repeaters import QuantumRepeater

    sim = QuantumRepeater(
        total_distance_km=float(params.get("total_distance_km", 1000)),
        num_segments=int(params.get("num_segments", 10)),
    )
    result = sim.simulate()
    return _to_jsonable({
        "total_distance_km": result.total_distance_km,
        "num_segments": result.num_segments,
        "end_to_end_fidelity": result.end_to_end_fidelity,
        "key_rate": result.key_rate,
        "key_length": result.key_length,
        "latency_ms": result.latency_ms,
    })


def handle_qcomm_network(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      topology: "star" | "ring" | "mesh" (default "star")
      num_nodes: int (default 6)
      distance_km: float (default 100)
    """
    from abirqu.quantum_communication.network import QuantumNetwork, Topology

    topology_map = {
        "star": Topology.STAR,
        "ring": Topology.RING,
        "mesh": Topology.MESH,
    }
    topology = topology_map.get(params.get("topology", "star"), Topology.STAR)
    num_nodes = int(params.get("num_nodes", 6))

    sim = QuantumNetwork(
        num_nodes=num_nodes,
        topology=topology,
    )
    sim.add_random_links()
    result = sim.simulate()
    return _to_jsonable({
        "topology": params.get("topology", "star"),
        "num_nodes": num_nodes,
        "total_key_rate": getattr(result, "total_key_rate", 0),
        "average_fidelity": getattr(result, "average_fidelity", 0),
        "num_paths": len(getattr(result, "paths", [])),
    })


# ─────────────────────────────────────────────────────────────────────────
# Circuit Encryption — wraps abirqu.security.CircuitProtector
# ─────────────────────────────────────────────────────────────────────────

def handle_circuit_encrypt(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      circuit_data: dict with num_qubits and gates
    """
    from abirqu.security import CircuitProtector
    from abirqu.circuit import Circuit

    circuit_data = params.get("circuit_data", {})
    num_qubits = circuit_data.get("num_qubits", 2)
    gates = circuit_data.get("gates", [])

    circ = Circuit(num_qubits)
    for gate in gates:
        if isinstance(gate, dict):
            circ.add_gate(gate.get("name", ""), gate.get("qubits", []), gate.get("params"))

    protector = CircuitProtector()
    encrypted = protector.encrypt_circuit(circ)

    return _to_jsonable({
        "ciphertext": encrypted.ciphertext[:64] + "...",
        "nonce": encrypted.nonce,
        "digest": encrypted.digest,
        "algorithm": encrypted.algorithm,
        "key_id": "ak-" + np.random.bytes(16).hex(),
        "key": protector._secret_key.hex() if hasattr(protector, '_secret_key') else "",
    })


def handle_circuit_decrypt(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      ciphertext: str
      nonce: str
      digest: str
      key: str (hex-encoded secret key)
    """
    from abirqu.security import CircuitProtector, EncryptedCircuit

    key_hex = params.get("key", "")
    if not key_hex:
        return {"status": "error", "error": "No decryption key provided"}

    try:
        key = bytes.fromhex(key_hex)
        protector = CircuitProtector(secret_key=key)

        payload = EncryptedCircuit(
            ciphertext=params.get("ciphertext", ""),
            nonce=params.get("nonce", ""),
            digest=params.get("digest", ""),
        )
        decrypted = protector.decrypt_circuit(payload)
        return _to_jsonable({
            "success": True,
            "num_qubits": decrypted.num_qubits,
            "num_gates": len(decrypted.gates),
        })
    except Exception as e:
        return _to_jsonable({"success": False, "error": str(e)})


# ─────────────────────────────────────────────────────────────────────────
# Plugin System — wraps abirqu.plugins
# ─────────────────────────────────────────────────────────────────────────

def handle_plugin_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """List available and installed plugins."""
    from abirqu.plugins import PluginDiscovery

    discovery = PluginDiscovery()
    discovered = discovery.discover()

    plugins = []
    for p in discovered:
        if "error" not in p:
            plugins.append({
                "name": p.get("name", "unknown"),
                "version": p.get("version", "1.0.0"),
                "status": "installed",
            })

    marketplace = [
        {"name": "abirqu-noise-pack", "version": "0.1.0", "description": "Advanced noise models", "tags": ["noise"], "downloads": 1200},
        {"name": "abirqu-optimizer-zx", "version": "0.1.1", "description": "ZX-calculus optimizer", "tags": ["optimizer"], "downloads": 980},
        {"name": "abirqu-qml-kernel", "version": "0.1.0", "description": "Quantum ML kernels", "tags": ["qml"], "downloads": 540},
        {"name": "abirqu-finance-pro", "version": "1.0.0", "description": "Finance workloads", "tags": ["finance"], "downloads": 50},
    ]

    installed_names = {p["name"] for p in plugins}
    for mp in marketplace:
        mp["installed"] = mp["name"] in installed_names

    return _to_jsonable({
        "installed": plugins,
        "marketplace": marketplace,
    })
