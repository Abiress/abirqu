"""
AbirQu Exception Hierarchy
===========================
Production-grade exception classes for structured error handling.
"""


class AbirQuError(Exception):
    """Base exception for all AbirQu errors."""


# ── Circuit & Simulation ──────────────────────────────────────────────

class CircuitError(AbirQuError):
    """Raised for circuit construction or validation errors."""


class SimulationError(AbirQuError):
    """Raised when simulation fails (e.g. statevector overflow, NaN probs)."""


# ── Backend & Hardware ────────────────────────────────────────────────

class BackendError(AbirQuError):
    """Raised for backend connection, discovery, or execution errors."""


class TranspilerError(AbirQuError):
    """Raised when transpilation or circuit compilation fails."""


class HardwareError(AbirQuError):
    """Raised for hardware calibration or characterization failures."""


class AuthenticationError(BackendError):
    """Raised when credentials are missing, invalid, or expired."""


class JobError(BackendError):
    """Raised for job submission, polling, or result-fetch failures."""


# ── Communication & Config ────────────────────────────────────────────

class QuantumCommunicationError(AbirQuError):
    """Raised for QKD, quantum channel, or protocol-level errors."""


class ConfigurationError(AbirQuError):
    """Raised for invalid configuration, parameters, or options."""
