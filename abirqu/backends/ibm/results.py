"""
IBM Quantum Results
===================
Parse and normalize IBM Quantum job results.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def parse_ibm_result(
    raw_result: Any,
    num_qubits: Optional[int] = None,
) -> Dict[str, Any]:
    """Parse raw IBM Quantum job result into AbirQu format.

    Parameters
    ----------
    raw_result : qiskit_ibm_runtime result
        Raw result from IBM Quantum job.
    num_qubits : int, optional
        Number of qubits (inferred if None).

    Returns
    -------
    Normalized result dict.
    """
    try:
        pub_result = raw_result[0]
        raw_counts = pub_result.data.meas.get_counts()
    except (AttributeError, IndexError):
        # Try alternative result format
        if hasattr(raw_result, "get_counts"):
            raw_counts = raw_result.get_counts()
        else:
            return {
                "success": False,
                "error": "Unable to parse IBM result",
                "counts": {},
                "probabilities": {},
            }

    total = sum(raw_counts.values())
    probs = {k: v / total for k, v in raw_counts.items()} if total > 0 else {}

    return {
        "success": True,
        "backend": "IBM",
        "shots": total,
        "counts": dict(raw_counts),
        "probabilities": probs,
        "statevector": None,
    }


def parse_statevector_result(raw_result: Any) -> Dict[str, Any]:
    """Parse statevector result from IBM simulator."""
    try:
        statevector = raw_result.get_statevector()
        probs = {format(i, f"0{len(statevector).bit_length()-1}b"): abs(v)**2
                 for i, v in enumerate(statevector)}
        return {
            "success": True,
            "backend": "IBM-simulator",
            "shots": 0,
            "counts": {},
            "probabilities": {k: v for k, v in probs.items() if v > 1e-10},
            "statevector": [complex(v).real + complex(v).imag * 1j for v in statevector],
        }
    except Exception as e:
        return {"success": False, "error": str(e), "counts": {}, "probabilities": {}}
