"""
Property-based tests for AbirQu quantum computing library.
Uses Hypothesis to verify physical invariants hold for random circuits.
"""
import numpy as np
import hypothesis
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from abirqu import Circuit, NumPySimulator
from abirqu.gates import H, X, Y, Z, CNOT, rx, ry, rz


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

@st.composite
def quantum_circuit_strategy(draw, min_qubits=1, max_qubits=8, min_depth=1, max_depth=20):
    """Generate a random quantum circuit with gates, angles, and qubit indices."""
    num_qubits = draw(st.integers(min_value=min_qubits, max_value=max_qubits))
    depth = draw(st.integers(min_value=min_depth, max_value=max_depth))

    circuit = Circuit(num_qubits)
    for _ in range(depth):
        gate_kind = draw(st.sampled_from([
            "H", "X", "Y", "Z", "RX", "RY", "RZ", "CNOT",
        ]))
        if gate_kind in ("H", "X", "Y", "Z", "RX", "RY", "RZ"):
            q = draw(st.integers(min_value=0, max_value=num_qubits - 1))
            if gate_kind == "H":
                circuit.h(q)
            elif gate_kind == "X":
                circuit.x(q)
            elif gate_kind == "Y":
                circuit.y(q)
            elif gate_kind == "Z":
                circuit.z(q)
            else:
                theta = draw(st.floats(min_value=-np.pi, max_value=np.pi))
                if gate_kind == "RX":
                    circuit.rx(q, theta)
                elif gate_kind == "RY":
                    circuit.ry(q, theta)
                else:
                    circuit.rz(q, theta)
        else:
            c = draw(st.integers(min_value=0, max_value=num_qubits - 1))
            t = draw(st.integers(min_value=0, max_value=num_qubits - 1))
            assume(c != t)
            circuit.cnot(c, t)

    return circuit


def build_unitary(circuit):
    """Build the full 2^n x 2^n unitary matrix for a circuit."""
    n = circuit.num_qubits
    dim = 2 ** n
    unitary = np.eye(dim, dtype=complex)

    for gate in circuit.gates:
        name = gate.name.upper()
        qubits = gate.qubits
        params = gate.params or []

        if len(qubits) == 1:
            q = qubits[0]
            if name == "H":
                mat = H
            elif name == "X":
                mat = X
            elif name == "Y":
                mat = Y
            elif name == "Z":
                mat = Z
            elif name == "RX":
                mat = rx(params[0])
            elif name == "RY":
                mat = ry(params[0])
            elif name == "RZ":
                mat = rz(params[0])
            else:
                continue

            full = np.eye(dim, dtype=complex)
            for i in range(dim):
                bit = (i >> q) & 1
                j = i ^ (1 << q)
                if j > i:
                    block = np.array([
                        [full[i, i], full[i, j]],
                        [full[j, i], full[j, j]],
                    ], dtype=complex)
                    new_block = mat @ block
                    full[i, i] = new_block[0, 0]
                    full[i, j] = new_block[0, 1]
                    full[j, i] = new_block[1, 0]
                    full[j, j] = new_block[1, 1]
            unitary = full @ unitary

        elif len(qubits) == 2:
            c, t = qubits
            if name in ("CNOT", "CX"):
                mat = CNOT
            else:
                continue

            full = np.zeros((dim, dim), dtype=complex)
            for i in range(dim):
                ctrl_bit = (i >> c) & 1
                tgt_bit = (i >> t) & 1
                j = i
                if ctrl_bit == 1:
                    j = i ^ (1 << t)
                full[j, i] = 1.0
            unitary = full @ unitary

    return unitary


# ---------------------------------------------------------------------------
# 1. State norm preservation
# ---------------------------------------------------------------------------

@given(circuit=quantum_circuit_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_state_norm_preservation(circuit):
    sim = NumPySimulator(circuit.num_qubits)
    sim.run_circuit(circuit)
    state = sim.get_state_vector()
    norm = np.linalg.norm(state)
    np.testing.assert_allclose(norm, 1.0, atol=1e-10)


# ---------------------------------------------------------------------------
# 2. Unitarity of generated circuits
# ---------------------------------------------------------------------------

@given(circuit=quantum_circuit_strategy(max_qubits=5, max_depth=10))
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_unitarity(circuit):
    unitary = build_unitary(circuit)
    product = unitary @ unitary.conj().T
    identity = np.eye(2 ** circuit.num_qubits, dtype=complex)
    np.testing.assert_allclose(product, identity, atol=1e-10)


# ---------------------------------------------------------------------------
# 3. Measurement probabilities sum to 1
# ---------------------------------------------------------------------------

@given(circuit=quantum_circuit_strategy())
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_measurement_probabilities_sum_to_one(circuit):
    sim = NumPySimulator(circuit.num_qubits)
    sim.run_circuit(circuit)
    probs = sim.get_probabilities()
    total = sum(probs.values())
    np.testing.assert_allclose(total, 1.0, atol=1e-10)


# ---------------------------------------------------------------------------
# 4. CNOT is self-inverse
# ---------------------------------------------------------------------------

@given(
    num_qubits=st.integers(min_value=2, max_value=8),
    control=st.integers(min_value=0, max_value=7),
    target=st.integers(min_value=0, max_value=7),
)
@settings(max_examples=50)
def test_cnot_self_inverse(num_qubits, control, target):
    assume(control < num_qubits and target < num_qubits and control != target)

    sim1 = NumPySimulator(num_qubits)
    sim1.cnot(control, target)
    sim1.cnot(control, target)
    state1 = sim1.get_state_vector()

    expected = np.zeros(2 ** num_qubits, dtype=complex)
    expected[0] = 1.0
    np.testing.assert_allclose(state1, expected, atol=1e-12)


# ---------------------------------------------------------------------------
# 5. Hadamard is self-inverse
# ---------------------------------------------------------------------------

@given(
    num_qubits=st.integers(min_value=1, max_value=8),
    qubit=st.integers(min_value=0, max_value=7),
)
@settings(max_examples=50)
def test_hadamard_self_inverse(num_qubits, qubit):
    assume(qubit < num_qubits)

    sim = NumPySimulator(num_qubits)
    sim.h(qubit)
    sim.h(qubit)
    state = sim.get_state_vector()

    expected = np.zeros(2 ** num_qubits, dtype=complex)
    expected[0] = 1.0
    np.testing.assert_allclose(state, expected, atol=1e-12)


# ---------------------------------------------------------------------------
# 6. Pauli gates are self-inverse: X^2 = Y^2 = Z^2 = I
# ---------------------------------------------------------------------------

@given(
    num_qubits=st.integers(min_value=1, max_value=8),
    qubit=st.integers(min_value=0, max_value=7),
)
@settings(max_examples=50)
def test_pauli_x_self_inverse(num_qubits, qubit):
    assume(qubit < num_qubits)
    sim = NumPySimulator(num_qubits)
    sim.x(qubit)
    sim.x(qubit)
    state = sim.get_state_vector()
    expected = np.zeros(2 ** num_qubits, dtype=complex)
    expected[0] = 1.0
    np.testing.assert_allclose(state, expected, atol=1e-12)


@given(
    num_qubits=st.integers(min_value=1, max_value=8),
    qubit=st.integers(min_value=0, max_value=7),
)
@settings(max_examples=50)
def test_pauli_y_self_inverse(num_qubits, qubit):
    assume(qubit < num_qubits)
    sim = NumPySimulator(num_qubits)
    sim.y(qubit)
    sim.y(qubit)
    state = sim.get_state_vector()
    expected = np.zeros(2 ** num_qubits, dtype=complex)
    expected[0] = 1.0
    np.testing.assert_allclose(state, expected, atol=1e-12)


@given(
    num_qubits=st.integers(min_value=1, max_value=8),
    qubit=st.integers(min_value=0, max_value=7),
)
@settings(max_examples=50)
def test_pauli_z_self_inverse(num_qubits, qubit):
    assume(qubit < num_qubits)
    sim = NumPySimulator(num_qubits)
    sim.z(qubit)
    sim.z(qubit)
    state = sim.get_state_vector()
    expected = np.zeros(2 ** num_qubits, dtype=complex)
    expected[0] = 1.0
    np.testing.assert_allclose(state, expected, atol=1e-12)


# ---------------------------------------------------------------------------
# 7. Probability conservation: total measurement counts == shots
# ---------------------------------------------------------------------------

@given(
    circuit=quantum_circuit_strategy(),
    shots=st.integers(min_value=1, max_value=1000),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
def test_probability_conservation(circuit, shots):
    result = circuit.run(shots=shots)
    total_counts = sum(result["counts"].values())
    assert total_counts == shots
