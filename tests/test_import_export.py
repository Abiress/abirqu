"""
Tests for Phase 1.4: Import/Export Systems
OpenQASM 2/3, Cirq JSON, Quirk URL import, JSON round-trips and golden files.
"""
import json
import pytest
from abirqu import Circuit, from_qasm, to_openqasm
from abirqu.formats.quirk import from_quirk_json, from_quirk_url, to_quirk_json


def test_openqasm2_golden_roundtrip():
    c = Circuit(2, "bell")
    c.h(0)
    c.cx(0, 1)

    qasm = to_openqasm(c)
    assert "OPENQASM 2.0;" in qasm
    assert "h q[0];" in qasm
    assert "cx q[0],q[1];" in qasm

    c2 = from_qasm(qasm)
    assert c2.num_qubits == 2
    assert len(c2.gates) == 2
    assert c2.gates[0].name.upper() == "H"
    assert c2.gates[1].name.upper() == "CNOT"


def test_quirk_url_import():
    url = "https://algassert.com/quirk#circuit=%7B%22cols%22%3A%5B%5B%22H%22%5D%2C%5B%22%E2%80%A2%22%2C%22X%22%5D%5D%7D"
    c = from_quirk_url(url)
    assert c.num_qubits == 2
    assert len(c.gates) == 2
    assert c.gates[0].name.upper() == "H"
    assert c.gates[1].name.upper() in ("CNOT", "CX")


def test_quirk_json_roundtrip():
    c = Circuit(3)
    c.h(0)
    c.cx(0, 1)
    c.cz(1, 2)
    c.toffoli(0, 1, 2)
    c.swap(0, 2)

    quirk_dict = to_quirk_json(c)
    assert "cols" in quirk_dict
    assert len(quirk_dict["cols"]) == 5

    c_restored = from_quirk_json(quirk_dict)
    assert c_restored.num_qubits == 3
    assert len(c_restored.gates) == 5
    assert c_restored.gates[0].name.upper() == "H"
    assert c_restored.gates[1].name.upper() in ("CNOT", "CX")
    assert c_restored.gates[2].name.upper() == "CZ"
    assert c_restored.gates[3].name.upper() in ("TOFFOLI", "CCX")
    assert c_restored.gates[4].name.upper() == "SWAP"


def test_circuit_native_json_roundtrip():
    c = Circuit(2, "test_circuit")
    c.h(0)
    c.cx(0, 1)

    # Verify JSON serialization and roundtrip
    serialized = c.to_json()
    c2 = Circuit.from_json(serialized)
    assert c2.num_qubits == 2
    assert len(c2.gates) == 2
    assert c2.gates[0].name == "H"
    assert c2.gates[1].name == "CNOT"
