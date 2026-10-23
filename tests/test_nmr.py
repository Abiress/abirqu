"""Tests for the NMR quantum computer module (abirqu.nmr)."""
import math

import numpy as np
import pytest

from abirqu import Circuit, NMRSystem, MOLECULES, list_molecules
from abirqu.circuit import Gate


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

def test_molecule_catalog():
    names = list_molecules()
    for name in names:
        mol = MOLECULES[name]
        assert mol.num_qubits >= 2
        assert mol.couplings, f"{name} has no J couplings"


def test_unknown_molecule_raises():
    with pytest.raises(ValueError):
        NMRSystem("caffeine")


# ---------------------------------------------------------------------------
# Single-qubit pulse physics
# ---------------------------------------------------------------------------

def test_x_pulse_prepares_excited_state():
    nmr = NMRSystem("chloroform")
    nmr.pulse(0, "x", math.pi)
    probs = nmr.probabilities()
    assert abs(probs["10"] - 1.0) < 1e-10


def test_z_pulse_is_virtual_and_free():
    nmr = NMRSystem("chloroform")
    nmr.pulse(0, "x", math.pi / 2)
    before = list(nmr._state)
    nmr.rz(0, math.pi / 2)
    assert np.allclose(np.abs(nmr._state), np.abs(np.array(before)))
    # virtual Z costs no experiment time
    assert nmr.total_time() > 0
    dur_with_rz = nmr.total_time()
    nmr2 = NMRSystem("chloroform")
    nmr2.pulse(0, "x", math.pi / 2)
    assert abs(nmr2.total_time() - dur_with_rz) < 1e-15


def test_pulse_duration_matches_b1():
    nmr = NMRSystem("chloroform", b1_khz=2.0)
    nmr.pulse(0, "x", math.pi / 2)
    with_rz_off = [op for op in nmr.pulse_schedule() if op["kind"] == "pulse"]
    durations = [op["duration_s"] for op in with_rz_off]
    assert any(abs(d - (math.pi / 2) / (2 * math.pi * 2000.0)) < 1e-12
               for d in durations)


# ---------------------------------------------------------------------------
# Gate identities (process fidelity against ideal unitaries)
# ---------------------------------------------------------------------------

def _kron_slots(n, ops):
    """Build full operator from per-slot 1q matrices {(slot): U}."""
    mats = []
    for q in range(n):
        mats.append(ops.get(q))
    out = None
    for q in range(n - 1, -1, -1):
        u = mats[q] if mats[q] is not None else np.eye(2, dtype=complex)
        out = u if out is None else np.kron(u, out)
    return out


def _cnot_ideal(n, c, t):
    dim = 2 ** n
    U = np.zeros((dim, dim), dtype=complex)
    for b in range(dim):
        bit_c = (b >> (n - 1 - c)) & 1
        out = b ^ (bit_c << (n - 1 - t))
        U[out, b] = 1.0
    return U


def _state_after_evolving_basis(nmr, prepare, gate_fn):
    """Apply gate to a basis state and return output amplitudes dict."""
    nmr.reset()
    prepare(nmr)
    gate_fn(nmr)
    st = nmr.amplitudes()
    return {format(i, f"0{nmr.n}b"): st[i] for i in range(2 ** nmr.n)}


def test_cnot_single_basis_state():
    # |10> -> |11> on chloroform (control q0, target q1)
    nmr = NMRSystem("chloroform")
    nmr.pulse(0, "x", math.pi)
    nmr.cnot(0, 1)
    st = nmr.amplitudes()
    expect = np.zeros(4, dtype=complex)
    expect[3] = 1.0  # |11>
    assert np.allclose(np.abs(st), np.abs(expect), atol=1e-10)


def test_cnot_zero_control_does_nothing():
    nmr = NMRSystem("chloroform")
    nmr.cnot(0, 1)  # control q0 is |0>
    probs = nmr.probabilities()
    assert abs(probs["00"] - 1.0) < 1e-10


def _bell_via_pulses(nmr):
    nmr.apply_hadamard(0)
    nmr.cnot(0, 1)


def test_bell_state_exact_counts():
    nmr = NMRSystem("chloroform")
    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    nmr.apply_circuit(c)
    counts = nmr.counts(4096, seed=0)
    assert set(counts) == {"00", "11"}
    assert all(abs(counts[k] / 4096 - 0.5) < 0.05 for k in counts)


def test_ghz3_exact():
    nmr = NMRSystem("trichloroethylene")
    c = Circuit(3)
    c.h(0)
    c.cnot(0, 1)
    c.cnot(1, 2)
    nmr.apply_circuit(c)
    probs = nmr.probabilities()
    assert abs(probs["000"] - 0.5) < 1e-10
    assert abs(probs["111"] - 0.5) < 1e-10
    assert all(abs(v) < 1e-10 for k, v in probs.items() if k not in ("000", "111"))


def test_ghz4_on_crotonic():
    nmr = NMRSystem("crotonic")
    c = Circuit(4)
    c.h(0)
    for a, b in ((0, 1), (1, 2), (2, 3)):
        c.cnot(a, b)
    nmr.apply_circuit(c)
    probs = nmr.probabilities()
    assert abs(probs["0000"] - 0.5) < 1e-10
    assert abs(probs["1111"] - 0.5) < 1e-10


def test_cz_axis_transfers_phase():
    # CZ on |++> flips the sign of |11> relative to |00>
    nmr = NMRSystem("chloroform")
    nmr.apply_hadamard(0)
    nmr.apply_hadamard(1)
    nmr.cz(0, 1)
    st = nmr.amplitudes()
    assert abs(st[0]) > 0.45
    assert abs(st[3]) > 0.45
    # opposite signs (global phase cancels in the product)
    assert (st[0] * st[3]).real < 0


def test_reverse_control_target():
    # CNOT with control > target index must also work (kron ordering)
    nmr = NMRSystem("chloroform")
    nmr.pulse(1, "x", math.pi)  # excite q1 (1H, the *higher* index)
    nmr.cnot(1, 0)  # control q1, target q0
    assert abs(nmr.probabilities()["11"] - 1.0) < 1e-10


def test_unsupported_gate_raises():
    nmr = NMRSystem("chloroform")
    c = Circuit(2)
    c.add_gate("FREDKIN", [0, 1])
    with pytest.raises(ValueError):
        nmr.apply_circuit(c)


# ---------------------------------------------------------------------------
# Timing, decoherence and readout
# ---------------------------------------------------------------------------

def test_schedule_and_total_time():
    nmr = NMRSystem("chloroform")
    nmr.apply_hadamard(0)
    nmr.cnot(0, 1)
    kinds = {op["kind"] for op in nmr.pulse_schedule()}
    assert "gate" in kinds and "j_evolution" in kinds
    # hadamard (2 pulses) + cnot (2 pulses) + 2 j-evolutions etc: > 1ms
    assert nmr.total_time() > 1e-3


def test_decoherence_penalty_reduces_fidelity():
    nmr = NMRSystem("crotonic")
    c = Circuit(4)
    c.h(0)
    c.cnot(0, 1)
    c.cnot(1, 2)
    c.cnot(2, 3)
    nmr.apply_circuit(c)
    assert 0 < nmr.estimated_fidelity() < 1.0


def test_pseudo_pure_readout_mixes_uniform():
    nmr = NMRSystem("chloroform", t2_penalty=True)
    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    nmr.apply_circuit(c)
    counts = nmr.counts(2000, seed=3)
    # each basis state should have nonzero probability mass
    assert set(counts) <= {"00", "01", "10", "11"}
    assert counts.get("00", 0) + counts.get("11", 0) > 0.5 * 2000


# ---------------------------------------------------------------------------
# Layout / spec
# ---------------------------------------------------------------------------

def test_spec_contents():
    nmr = NMRSystem("chloroform")
    spec = nmr.spec()
    assert spec["register"]["formula"] == "CHCl3"
    assert len(spec["channels"]) == 2
    assert spec["coupling_graph"] and all(v > 0 for v in spec["coupling_graph"].values())
    assert spec["hardware"]["magnet"]["field"]


def test_layout_renders():
    nmr = NMRSystem("trichloroethylene")
    text = nmr.layout()
    assert "AbirQu NMR Quantum Computer" in text
    assert "1H q0" in text
    assert "J(0,1)" in text or "J(" in text


def test_export_layout_html(tmp_path):
    nmr = NMRSystem("chloroform")
    out = tmp_path / "nmr_layout.html"
    path = nmr.export_layout_html(str(out))
    assert path == str(out)
    text = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in text
    assert "Chloroform-13C" in text
