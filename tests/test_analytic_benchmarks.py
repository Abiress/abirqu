"""
Phase 2.2 Acceptance Test:
Verification of Step-through simulation statevector amplitudes against analytic results
for Bell, GHZ, QFT(3), and Grover(2) circuits within 1e-9 tolerance.
"""
import numpy as np
import pytest
from abirqu import Circuit
from abirqu.algorithms import qft_circuit
from abirqu.numpy_sim import NumPySimulator


def test_bell_state_analytic_amplitudes():
    """Bell State (|00> + |11>) / sqrt(2) exact amplitudes."""
    c = Circuit(2)
    c.h(0)
    c.cx(0, 1)

    sim = NumPySimulator(2)
    sim.run_circuit(c)
    sv = sim.get_state_vector()

    expected_00 = 1.0 / np.sqrt(2)
    expected_11 = 1.0 / np.sqrt(2)

    assert abs(abs(sv[0]) - expected_00) < 1e-9
    assert abs(abs(sv[3]) - expected_11) < 1e-9
    assert abs(sv[1]) < 1e-9
    assert abs(sv[2]) < 1e-9


def test_ghz_state_analytic_amplitudes():
    """3-Qubit GHZ State (|000> + |111>) / sqrt(2) exact amplitudes."""
    c = Circuit(3)
    c.h(0)
    c.cx(0, 1)
    c.cx(1, 2)

    sim = NumPySimulator(3)
    sim.run_circuit(c)
    sv = sim.get_state_vector()

    expected = 1.0 / np.sqrt(2)
    assert abs(abs(sv[0]) - expected) < 1e-9
    assert abs(abs(sv[7]) - expected) < 1e-9

    for i in range(1, 7):
        assert abs(sv[i]) < 1e-9


def test_qft3_analytic_amplitudes():
    """QFT on |000> yields uniform superposition 1/sqrt(8) across all 8 basis states."""
    c = qft_circuit(3)
    sim = NumPySimulator(3)
    sim.run_circuit(c)
    sv = sim.get_state_vector()

    expected_mag = 1.0 / np.sqrt(8)
    for amp in sv:
        assert abs(abs(amp) - expected_mag) < 1e-9


def test_grover2_analytic_amplitudes():
    """2-Qubit Grover search for target |11> yields deterministic amplitude 1.0 at index 3."""
    c = Circuit(2)
    # Superposition
    c.h(0)
    c.h(1)
    # Oracle for |11>
    c.cz(0, 1)
    # Diffusion operator
    c.h(0)
    c.h(1)
    c.x(0)
    c.x(1)
    c.cz(0, 1)
    c.x(0)
    c.x(1)
    c.h(0)
    c.h(1)

    sim = NumPySimulator(2)
    sim.run_circuit(c)
    sv = sim.get_state_vector()

    # Probability of target state |11> must be exactly 1.0 within 1e-9
    assert abs(abs(sv[3]) - 1.0) < 1e-9
    assert abs(sv[0]) < 1e-9
    assert abs(sv[1]) < 1e-9
    assert abs(sv[2]) < 1e-9

