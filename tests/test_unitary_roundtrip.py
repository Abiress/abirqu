"""
Acceptance Test for Phase 1.3:
Circuit -> QASM -> Circuit -> Same Unitary (tolerance 1e-9) across the full gate set.
"""
import math
import numpy as np
import pytest
from abirqu import Circuit, from_qasm, to_openqasm
from abirqu.numpy_sim import NumPySimulator


def compute_circuit_unitary(c: Circuit) -> np.ndarray:
    n = c.num_qubits
    dim = 1 << n
    U = np.zeros((dim, dim), dtype=complex)
    for col in range(dim):
        sim = NumPySimulator(n)
        initial = np.zeros(dim, dtype=complex)
        initial[col] = 1.0
        sim.state = initial
        sim.run_circuit(c)
        U[:, col] = sim.get_state_vector()
    return U


def test_full_gateset_qasm_unitary_roundtrip():
    """Verify that every supported gate roundtrips through QASM with identical unitary <= 1e-9."""
    c = Circuit(3)
    c.h(0)
    c.x(1)
    c.y(2)
    c.z(0)
    c.s(1)
    c.t(2)
    c.rx(0, math.pi / 4)
    c.ry(1, math.pi / 3)
    c.rz(2, math.pi / 6)
    c.cx(0, 1)
    c.cz(1, 2)
    c.swap(0, 2)
    c.toffoli(0, 1, 2)

    qasm = to_openqasm(c)
    c_roundtrip = from_qasm(qasm)

    u_orig = compute_circuit_unitary(c)
    u_rt = compute_circuit_unitary(c_roundtrip)

    max_diff = np.max(np.abs(u_orig - u_rt))
    assert max_diff < 1e-9, f"Unitary difference {max_diff} exceeded 1e-9 tolerance"


def test_two_qubit_entangling_unitary_roundtrip():
    """Verify Bell state entangling unitary roundtrip."""
    c = Circuit(2)
    c.h(0)
    c.cx(0, 1)

    qasm = to_openqasm(c)
    c_rt = from_qasm(qasm)

    u_orig = compute_circuit_unitary(c)
    u_rt = compute_circuit_unitary(c_rt)

    assert np.allclose(u_orig, u_rt, atol=1e-9)


def test_parameterized_rotation_unitary_roundtrip():
    """Verify arbitrary angle rotation unitary roundtrip."""
    c = Circuit(1)
    c.rx(0, 0.123456789)
    c.ry(0, 0.987654321)
    c.rz(0, 1.570796326)

    qasm = to_openqasm(c)
    c_rt = from_qasm(qasm)

    u_orig = compute_circuit_unitary(c)
    u_rt = compute_circuit_unitary(c_rt)

    assert np.allclose(u_orig, u_rt, atol=1e-9)

