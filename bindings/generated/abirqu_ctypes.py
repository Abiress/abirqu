"""Auto-generated AbirQu Python ctypes bindings — do not edit manually."""

import ctypes
import os
from pathlib import Path

_LIB_DIR = Path(__file__).resolve().parent.parent
# Try release first, then debug
_LIB_NAMES = [
    "libabirqu_core.so",
    "abirqu_core.dll",
    "libabirqu_core.dylib",
]

_lib = None
for _name in _LIB_NAMES:
    _path = _LIB_DIR / _name
    if _path.exists():
        _lib = ctypes.CDLL(str(_path))
        break
if _lib is None:
    raise OSError("Could not find abirqu_core shared library")

AbirQuSimulator = ctypes.c_void_p

# Create a new simulator for `num_qubits` qubits.
# Returns a non-null opaque handle.  Must be freed with
# `abirqu_simulator_destroy`.
_abirqu_simulator_create = _lib.abirqu_simulator_create
_abirqu_simulator_create.restype = AbirQuSimulator
_abirqu_simulator_create.argtypes = [ctypes.c_void_p]

# Free a handle created by `abirqu_simulator_create`.  Passing NULL is safe.
_abirqu_simulator_destroy = _lib.abirqu_simulator_destroy
_abirqu_simulator_destroy.restype = None
_abirqu_simulator_destroy.argtypes = [ctypes.c_void_p]

# Reset the simulator to |0…0⟩ without reallocating.
_abirqu_simulator_reset = _lib.abirqu_simulator_reset
_abirqu_simulator_reset.restype = None
_abirqu_simulator_reset.argtypes = [ctypes.c_void_p]

# Return the number of qubits this simulator was created with.
_abirqu_num_qubits = _lib.abirqu_num_qubits
_abirqu_num_qubits.restype = ctypes.c_uint32
_abirqu_num_qubits.argtypes = [ctypes.c_void_p]

# Return the Hilbert space dimension (2^num_qubits).
_abirqu_hilbert_dim = _lib.abirqu_hilbert_dim
_abirqu_hilbert_dim.restype = ctypes.c_size_t
_abirqu_hilbert_dim.argtypes = [ctypes.c_void_p]

_abirqu_h = _lib.abirqu_h
_abirqu_h.restype = None
_abirqu_h.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_abirqu_x = _lib.abirqu_x
_abirqu_x.restype = None
_abirqu_x.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_abirqu_y = _lib.abirqu_y
_abirqu_y.restype = None
_abirqu_y.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_abirqu_z = _lib.abirqu_z
_abirqu_z.restype = None
_abirqu_z.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_abirqu_s = _lib.abirqu_s
_abirqu_s.restype = None
_abirqu_s.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_abirqu_t = _lib.abirqu_t
_abirqu_t.restype = None
_abirqu_t.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

_abirqu_rx = _lib.abirqu_rx
_abirqu_rx.restype = None
_abirqu_rx.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

_abirqu_ry = _lib.abirqu_ry
_abirqu_ry.restype = None
_abirqu_ry.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

_abirqu_rz = _lib.abirqu_rz
_abirqu_rz.restype = None
_abirqu_rz.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

_abirqu_cnot = _lib.abirqu_cnot
_abirqu_cnot.restype = None
_abirqu_cnot.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

_abirqu_cz = _lib.abirqu_cz
_abirqu_cz.restype = None
_abirqu_cz.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

_abirqu_swap = _lib.abirqu_swap
_abirqu_swap.restype = None
_abirqu_swap.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

# Execute a batch of gates described by the `gates` array of length `n_gates`.
# 
# # Safety
# `handle` must be a valid non-null pointer from `abirqu_simulator_create`.
# `gates`  must point to at least `n_gates` consecutive `AbirQuGate` values.
_abirqu_run_circuit = _lib.abirqu_run_circuit
_abirqu_run_circuit.restype = None
_abirqu_run_circuit.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

# Copy measurement probabilities into caller-supplied buffer `out_probs`.
# 
# `out_probs` must have room for at least `abirqu_hilbert_dim(handle)` doubles.
# Returns the number of values written, or 0 on error.
_abirqu_get_probabilities = _lib.abirqu_get_probabilities
_abirqu_get_probabilities.restype = ctypes.c_size_t
_abirqu_get_probabilities.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

# Copy the statevector into caller-supplied buffers `out_re` and `out_im`.
# 
# Both buffers must have room for at least `abirqu_hilbert_dim(handle)` doubles.
# Returns the number of complex amplitudes written, or 0 on error.
_abirqu_get_statevector = _lib.abirqu_get_statevector
_abirqu_get_statevector.restype = ctypes.c_size_t
_abirqu_get_statevector.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]


class Simulator:
    """High-level wrapper around the AbirQu C API."""

    def __init__(self, num_qubits: int) -> None:
        self._handle = _abirqu_simulator_create(ctypes.c_uint32(num_qubits))

    def __del__(self) -> None:
        if self._handle:
            _abirqu_simulator_destroy(self._handle)

    def reset(self) -> None:
        _abirqu_simulator_reset(self._handle)

    @property
    def num_qubits(self) -> int:
        return _abirqu_num_qubits(self._handle)

    def h(self, q: int) -> None:
        _abirqu_h(self._handle, ctypes.c_uint32(q))

    def x(self, q: int) -> None:
        _abirqu_x(self._handle, ctypes.c_uint32(q))

    def y(self, q: int) -> None:
        _abirqu_y(self._handle, ctypes.c_uint32(q))

    def z(self, q: int) -> None:
        _abirqu_z(self._handle, ctypes.c_uint32(q))

    def rx(self, q: int, angle: float) -> None:
        _abirqu_rx(self._handle, ctypes.c_uint32(q), ctypes.c_double(angle))

    def ry(self, q: int, angle: float) -> None:
        _abirqu_ry(self._handle, ctypes.c_uint32(q), ctypes.c_double(angle))

    def rz(self, q: int, angle: float) -> None:
        _abirqu_rz(self._handle, ctypes.c_uint32(q), ctypes.c_double(angle))

    def cnot(self, ctrl: int, tgt: int) -> None:
        _abirqu_cnot(self._handle, ctypes.c_uint32(ctrl), ctypes.c_uint32(tgt))

    def cz(self, ctrl: int, tgt: int) -> None:
        _abirqu_cz(self._handle, ctypes.c_uint32(ctrl), ctypes.c_uint32(tgt))

    def get_probabilities(self) -> list[float]:
        dim = _abirqu_hilbert_dim(self._handle)
        buf = (ctypes.c_double * dim)()
        _abirqu_get_probabilities(self._handle, buf)
        return list(buf)
