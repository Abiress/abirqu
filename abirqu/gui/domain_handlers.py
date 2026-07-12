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
# Cryptography / PQC — wraps abirqu.crypto (LatticeSimulation)
# ─────────────────────────────────────────────────────────────────────────

def handle_pqc_keygen(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    params:
      scheme: "kyber" (only lattice keygen currently exposed by the SDK)
    """
    from abirqu.crypto import LatticeSimulation

    lat = LatticeSimulation()
    keypair = lat.generate_keypair()
    return _to_jsonable({
        "scheme": "kyber768",
        "public_key_shape": list(keypair["public_key"].shape),
        "secret_key_shape": list(keypair["secret_key"].shape),
        # keys are large matrices — return shapes + a truncated preview,
        # never dump the full secret key back over the wire in a real product
        "public_key_preview": keypair["public_key"][:2].tolist(),
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
