"""
AbirQu Backends
===============
All supported quantum computing backends.

Each backend inherits from ``QuantumBackend`` ABC defined in ``abirqu.backend``
and provides a unified ``run_circuit()`` / ``submit()`` interface.

Available backends:
- ``abirqu.backends.ibm.IBMQuantumBackend`` — IBM Quantum (qiskit-ibm-runtime)
- ``abirqu.backends.aws.BraketBackend`` — AWS Braket (amazon-braket-sdk)
- ``abirqu.backends.azure.AzureQuantumBackend`` — Azure Quantum (azure-quantum)
- ``abirqu.backends.google.GoogleQuantumBackend`` — Google Quantum (cirq/cirq-google)
- ``abirqu.backends.ionq.IonQBackend`` — IonQ (REST API)
- ``abirqu.backends.rigetti.RigettiBackend`` — Rigetti/QCS (pyquil)
- ``abirqu.backends.quantinuum.QuantinuumBackend`` — Quantinuum H-Series (pytket)
- ``abirqu.backends.pasqal.PasqalBackend`` — Pasqal neutral atoms (pulser)
- ``abirqu.backends.oqc.OQCBackend`` — OQC superconducting (REST API)
- ``abirqu.backends.quera.QuEraBackend`` — QuEra Aquila (AWS Braket analog)
"""

from ..backend import QuantumBackend, FastBackend, BackendRegistry, JobStatus, JobHandle

__all__ = [
    "QuantumBackend",
    "FastBackend",
    "BackendRegistry",
    "JobStatus",
    "JobHandle",
]
