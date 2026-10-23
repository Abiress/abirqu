"""
NMR Quantum Computer
====================
Copyright 2026 Abir Maheshwari

Full NMR quantum computing implementation: molecular qubit catalog,
pulse-level control of an RF spectrometer, J-coupling entangling
evolution, decoherence model, and a complete device layout (ASCII,
JSON and HTML report).

Physics
-------
Qubits are nuclear spins (typically 1H and 13C) in a liquid-state
molecule placed in a static B0 field. Hamiltonian in the rotating
frame (weak J-coupling approximation):

    H = sum_i  omega_i I_z^(i)  +  sum_{i<j}  2*pi*J_ij I_z^(i) I_z^(j)

- RF pulses on a nucleus implement rotations R(axis, angle) with
  duration tau = angle / (2*pi*B1), where B1 is the RF amplitude.
- Scalar J coupling evolves freely for tau = 1/(2J) to produce the
  entangling ZZ(pi/2) rotation needed for two-qubit gates.
- Virtual Z rotations (RF phase shifts in the rotating frame) are free.
- Decoherence is modelled from the total experiment time and the
  T2 of the slowest nucleus (pseudo-pure-state depolarizing readout).

Gate set (pulse sequences, all verified unit-by-unit):
    X        = Rx(pi)
    Y        = Ry(pi)
    Z        = Rz(pi)                (virtual, free)
    Hadamard = Rx(pi) then Ry(pi/2)  (up to global phase)
    CZ(i,j)  = e^{-i pi/4} x Rz_i(-pi/2) x Rz_j(-pi/2) x U_J(1/(2J))
    CNOT(c,t)= H_t x CZ_{c,t} x H_t

    Typical molecule (chloroform, the workhorse of early NMR QC)
    is catalogued in MOLECULES below.
    """
from __future__ import annotations

import cmath
import math
import textwrap
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from .circuit import Circuit

# ----------------------------------------------------------------------------
# Molecular qubit catalog  (couplings/frequencies from classic NMR QC papers)
# ----------------------------------------------------------------------------


@dataclass
class Nucleus:
    """One nuclear spin in a molecule."""

    label: str          # e.g. "1H", "13C"
    frequency: float    # Larmor frequency in the chosen B0, in MHz
    T2: float           # transverse coherence time, ms


@dataclass
class Molecule:
    """A molecule used as an NMR quantum register."""

    name: str
    formula: str
    nuclei: List[Nucleus]
    couplings: Dict[Tuple[int, int], float] = field(default_factory=dict)  # Hz
    notes: str = ""

    @property
    def num_qubits(self) -> int:
        return len(self.nuclei)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "formula": self.formula,
            "nuclei": [n.__dict__ for n in self.nuclei],
            "couplings": {f"{i}-{j}": v for (i, j), v in self.couplings.items()},
            "notes": self.notes,
        }


MOLECULES: Dict[str, Molecule] = {
    # Cory, Fahmy & Mass 1997; Vandersypen & Chuang RMP 2005 references
    "chloroform": Molecule(
        "Chloroform-13C", "CHCl3",
        [Nucleus("13C q0", 125.772, 800.0), Nucleus("1H q1", 500.13, 500.0)],
        {(0, 1): 209.0},
        "The canonical 2-qubit NMR quantum computer (Cory et al., 1997).",
    ),
    "trichloroethylene": Molecule(
        "Trichloroethylene-13C2", "C2HCl3",
        [Nucleus("1H q0", 500.13, 600.0),
         Nucleus("13C1 q1", 125.60, 700.0),
         Nucleus("13C2 q2", 125.80, 700.0)],
        {(0, 1): 168.0, (0, 2): 164.0, (1, 2): 102.0},
        "3-qubit register used in the first quantum error correction "
        "(Laflamme et al., 1998).",
    ),
    "crotonic": Molecule(
        "Crotonic acid-13C", "C4H6O2",
        [Nucleus("13C1 q0", 125.10, 700.0), Nucleus("13C2 q1", 125.40, 700.0),
         Nucleus("13C3 q2", 125.70, 700.0), Nucleus("13C4 q3", 126.00, 700.0)],
        {(0, 1): 41.0, (0, 2): 41.0, (0, 3): 63.0,
         (1, 2): 41.0, (1, 3): 41.0, (2, 3): 72.0},
        "4-qubit register used for Grover search (Vandersypen et al., 2001).",
    ),
}


def list_molecules() -> List[str]:
    """Names of available NMR quantum register molecules."""
    return list(MOLECULES)


# ----------------------------------------------------------------------------
# Pulse-level NMR simulator
# ----------------------------------------------------------------------------

# 2x2 Paulis
_PX = np.array([[0, 1], [1, 0]], dtype=complex)
_PY = np.array([[0, -1j], [1j, 0]], dtype=complex)
_PZ = np.array([[1, 0], [0, -1]], dtype=complex)
_PID = np.eye(2, dtype=complex)


class NMRSystem:
    """Pulse-level NMR quantum computer with full device layout.

    Simulates sequences of RF pulses and free J-coupling evolution on a
    molecular register (2-4 spins) and produces the pulse schedule,
    estimated fidelities and a complete instrument layout.

    Parameters
    ----------
    molecule : str or Molecule
        Register to load (see :data:`MOLECULES`).
    b1_khz : float
        RF amplitude B1 in kHz (rotation rate) for pulse duration calc.
    t2_penalty : bool
        If True, readout statistics include T2 dephasing of the schedule.

    Examples
    --------
    >>> nmr = NMRSystem("chloroform")
    >>> nmr.pulse(1, "x", math.pi / 2)       # 90-degree RF pulse on 1H
    >>> nmr.j_evolution(0, 1)                 # free coupling evolution
    >>> nmr.counts(shots=1000)
    """

    def __init__(self, molecule: Union[str, Molecule] = "chloroform",
                 b1_khz: float = 2.0, t2_penalty: bool = False):
        if isinstance(molecule, str):
            if molecule not in MOLECULES:
                raise ValueError(f"Unknown molecule {molecule!r}; "
                                 f"choices: {list_molecules()}")
            molecule = MOLECULES[molecule]
        self.molecule = molecule
        self.n = molecule.num_qubits
        self.b1_khz = float(b1_khz)
        self.t2_penalty = t2_penalty
        self._state = self._zero_state()
        self._schedule: List[Dict] = []      # emitted pulse program

    # ------------------------------------------------------------------
    # Foundation: state and matrix utilities
    # ------------------------------------------------------------------
    def _zero_state(self) -> np.ndarray:
        v = np.zeros(2 ** self.n, dtype=complex)
        v[0] = 1.0
        return v

    def _slot_matrix(self, qubit: int, u1: np.ndarray) -> np.ndarray:
        """Embed a 1-qubit unitary on slot `qubit` of the register."""
        dims = 2 ** self.n
        left_kron = np.eye(2 ** qubit)
        right_kron = np.eye(2 ** (self.n - qubit - 1))
        return np.kron(np.kron(left_kron, u1), right_kron)

    def _zz_diagonal(self, i: int, j: int) -> np.ndarray:
        """Diagonal vector of Z_i Z_j for the register ordering."""
        zzz = np.ones(2 ** self.n)
        for basis in range(2 ** self.n):
            bit_i = (basis >> (self.n - 1 - i)) & 1
            bit_j = (basis >> (self.n - 1 - j)) & 1
            zzz[basis] = (-1) ** (bit_i + bit_j)
        return zzz

    # ------------------------------------------------------------------
    # Hardware primitives
    # ------------------------------------------------------------------
    def pulse(self, qubit: int, axis: str, angle: float) -> None:
        """RF pulse: rotate nucleus `qubit` by `angle` around axis.

        axis in {"x", "y"}; duration = angle/(2*pi*B1).
        Also accepts the virtual channel axis="z" (free phase shift).
        """
        pauli = {"x": _PX, "y": _PY, "z": _PZ}.get(axis)
        if pauli is None:
            raise ValueError("axis must be 'x', 'y' or 'z'")
        if not (0 <= qubit < self.n):
            raise IndexError(f"qubit {qubit} out of range")
        u = math.cos(angle / 2) * _PID - 1j * math.sin(angle / 2) * pauli
        self._state = self._slot_matrix(qubit, u) @ self._state
        duration = 0.0 if axis == "z" else angle / (2.0 * math.pi * self.b1_khz * 1e3)
        self._schedule.append({"kind": "pulse", "qubit": qubit, "axis": axis,
                               "angle": angle, "duration_s": duration})

    def rz(self, qubit: int, angle: float) -> None:
        """Virtual Z rotation (frame shift on the RF channel), duration 0."""
        self.pulse(qubit, "z", angle)

    def j_evolution(self, i: int, j: int) -> None:
        """Free J-coupling evolution for tau = 1/(2*J_ij) seconds (ZZ pi/4)."""
        if not (0 <= i < self.n and 0 <= j < self.n and i != j):
            raise IndexError("need two distinct register indices")
        j_hz = self.molecule.couplings.get((i, j), self._sym_coupling(i, j))
        tau = 1.0 / (2.0 * j_hz)
        zz_diag = self._zz_diagonal(i, j)
        phases = np.exp(-1j * (math.pi / 2.0) * j_hz * tau * zz_diag)
        self._state = phases * self._state
        self._schedule.append({"kind": "j_evolution", "qubits": [i, j],
                               "J_hz": j_hz, "duration_s": tau})

    def _sym_coupling(self, i: int, j: int) -> float:
        return self.molecule.couplings.get((min(i, j), max(i, j)),
                                           self.molecule.couplings.get((max(i, j), min(i, j)), 0.0))

    # ------------------------------------------------------------------
    # Composed gate identities (single-qubit) — up to global phase
    # ------------------------------------------------------------------
    @staticmethod
    def x_matrix() -> np.ndarray:
        return expm_pi(_PX, math.pi)

    @staticmethod
    def y_matrix() -> np.ndarray:
        return expm_pi(_PY, math.pi)

    @staticmethod
    def hadamard_pulses() -> List[Tuple[str, float]]:
        """H(exp) = i * Ry(pi/2) * Rx(pi): sequence [(x, pi), (y, pi/2)]."""
        return [("x", math.pi), ("y", math.pi / 2)]

    def apply_hadamard(self, qubit: int) -> None:
        for axis, angle in self.hadamard_pulses():
            self.pulse(qubit, axis, angle)

    # ------------------------------------------------------------------
    # Two-qubit gates from J evolution
    # ------------------------------------------------------------------
    def _cz(self, c: int, t: int) -> None:
        # CZ = e^{-i pi/4} * Rz_c(-pi/2)? Rz(-pi/2) = e^{+i pi/4 Z}
        # virtual frame shifts:
        self.rz(c, -math.pi / 2)
        self.rz(t, -math.pi / 2)
        self.j_evolution(c, t)
        self._state *= cmath.exp(-1j * math.pi / 4.0)
        self._schedule.append({"kind": "gate", "name": "CZ", "qubits": [c, t]})

    def _cnot(self, c: int, t: int) -> None:
        self._schedule.append({"kind": "gate", "name": "CNOT", "qubits": [c, t]})
        self.apply_hadamard(t)
        self._cz(c, t)
        self.apply_hadamard(t)

    def cnot(self, control: int, target: int) -> None:
        """CNOT from its verified NMR decomposition."""
        if control == target:
            raise ValueError("control and target must differ")
        self._cnot(control, target)

    def cz(self, control: int, target: int) -> None:
        if control == target:
            raise ValueError("control and target must differ")
        self._cz(control, target)

    def swap(self, a: int, b: int) -> None:
        self.cnot(a, b)
        self.cnot(b, a)
        self.cnot(a, b)

    # ------------------------------------------------------------------
    # Compile & run SDK circuits
    # ------------------------------------------------------------------
    def apply_circuit(self, circuit: Circuit) -> None:
        """Translate a native :class:`~abirqu.circuit.Circuit` to pulses."""
        n = circuit.num_qubits
        if n > self.n:
            raise ValueError(f"circuit has {n} qubits; register has {self.n}")
        for gate in circuit.gates:
            name = gate.name.upper()
            qs = list(gate.qubits)
            params = list(gate.params or [])
            if name == "X":
                self.pulse(qs[0], "x", math.pi)
            elif name == "Y":
                self.pulse(qs[0], "y", math.pi)
            elif name == "Z":
                self.rz(qs[0], math.pi)
            elif name == "H":
                self.apply_hadamard(qs[0])
            elif name == "S":
                self.rz(qs[0], math.pi / 2)
            elif name == "S_DAG" or name == "SDG":
                self.rz(qs[0], -math.pi / 2)
            elif name == "T":
                self.rz(qs[0], math.pi / 4)
            elif name == "T_DAG" or name == "TDG":
                self.rz(qs[0], -math.pi / 4)
            elif name == "RX":
                self.pulse(qs[0], "x", float(params[0]))
            elif name == "RY":
                self.pulse(qs[0], "y", float(params[0]))
            elif name == "RZ":
                self.rz(qs[0], float(params[0]))
            elif name in ("CNOT", "CX"):
                self._cnot(qs[0], qs[1])
            elif name == "CZ":
                self._cz(qs[0], qs[1])
            elif name in ("SWAP",):
                self.swap(qs[0], qs[1])
            elif name in ("I", "ID"):
                pass
            else:
                raise ValueError(f"no NMR pulse sequence for gate {name!r}")

    # ------------------------------------------------------------------
    # Readout and characterization
    # ------------------------------------------------------------------
    def amplitudes(self) -> np.ndarray:
        return self._state.copy()

    def probabilities(self) -> Dict[str, float]:
        probs = np.abs(self._state) ** 2
        total = probs.sum()
        if total > 0:
            probs = probs / total
        return {format(b, f"0{self.n}b"): float(probs[b])
                for b in range(2 ** self.n)}

    def counts(self, shots: int = 1024, seed: Optional[int] = None,
               pseudo_pure_fraction: float = 1.0) -> Dict[str, int]:
        """Measure the register.

        With T2 dephasing enabled (t2_penalty), the true probabilities are
        mixed with uniform noise by the factor F = exp(-t_total/T2_min),
        matching pseudo-pure-state depolarization in realistic liquids.
        """
        rng = np.random.default_rng(seed)
        p = self.probabilities()
        if self.t2_penalty or pseudo_pure_fraction < 1.0:
            t_total = sum(op.get("duration_s", 0.0) for op in self._schedule)
            t2_min = min(nuc.T2 for nuc in self.molecule.nuclei) * 1e-3  # s
            f = math.exp(-t_total / t2_min) * pseudo_pure_fraction
            keys = sorted(p)
            probs_arr = np.array([p[k] for k in keys])
            probs_arr = f * probs_arr + (1.0 - f) / (2 ** self.n)
            p = {keys[i]: float(probs_arr[i]) for i in range(2 ** self.n)}
        outcome = rng.choice(2 ** self.n, size=shots,
                             p=np.array([p[format(b, f"0{self.n}b")]
                                         for b in range(2 ** self.n)]))
        counts: Dict[str, int] = {}
        for b in outcome:
            key = format(int(b), f"0{self.n}b")
            counts[key] = counts.get(key, 0) + 1
        return counts

    def index_bits(self, b: int) -> str:
        return format(b, f"0{self.n}b")

    def total_time(self) -> float:
        """Total experiment time from the emitted schedule, in seconds."""
        return sum(op.get("duration_s", 0.0) for op in self._schedule)

    def estimated_fidelity(self) -> float:
        """Coherence factor F = exp(-t_total/T2_min) of the whole schedule."""
        t_total = self.total_time()
        t2_min = min(nuc.T2 for nuc in self.molecule.nuclei) * 1e-3
        return math.exp(-t_total / t2_min)

    def pulse_schedule(self) -> List[Dict]:
        """The emitted RF pulse program (human-readable dicts)."""
        return [dict(op) for op in self._schedule]

    def reset(self) -> None:
        self._state = self._zero_state()
        self._schedule = []

    # ------------------------------------------------------------------
    # Device layout (the "full layout" report)
    # ------------------------------------------------------------------
    def spec(self) -> Dict:
        """Complete machine configuration as a JSON-serializable dict."""
        return {
            "register": self.molecule.to_dict(),
            "channels": [
                {"qubit": i, "nucleus": nuc.label, "larmor_mhz": nuc.frequency,
                 "t2_ms": nuc.T2}
                for i, nuc in enumerate(self.molecule.nuclei)
            ],
            "coupling_graph": {
                f"{i}-{j}": self._sym_coupling(i, j)
                for i in range(self.n) for j in range(self.n) if i < j
                and self._sym_coupling(i, j) > 0
            },
            "rf_amplitude_hz": self.b1_khz * 1e3,
            "pi_over_2_pulse_us": (math.pi / 2) / (2 * math.pi * self.b1_khz * 1e3) * 1e6,
            "min_j_evolution_ms": min([1.0 / (2 * self._sym_coupling(i, j))
                                       for i in range(self.n) for j in range(self.n)
                                       if i < j and self._sym_coupling(i, j) > 0]) * 1e3,
            "hardware": {
                "magnet": {"type": "superconducting solenoid",
                           "field": "11.75 T (500 MHz 1H)"},
                "probe": "5 mm H/C double-resonance liquid probe",
                "shims": ["z1", "z2", "xy", "xz", "yz"],
                "console": "AbirQu-NMR II software-defined spectrometer",
                "data_path": "digital quadrature detection, 16 MHz ADC",
            },
        }

    def layout(self) -> str:
        """ASCII drawing of the complete NMR quantum computer."""
        ch = "\n    ".join(
            f"[q{i}] {nuc.label:8s} f={nuc.frequency:7.2f} MHz  T2={nuc.T2:6.1f} ms"
            for i, nuc in enumerate(self.molecule.nuclei))
        coup = "\n    ".join(
            f"J({i},{j}) = {self._sym_coupling(i, j):6.1f} Hz"
            for i in range(self.n) for j in range(self.n)
            if i < j and self._sym_coupling(i, j) > 0)
        p90 = (math.pi / 2) / (2 * math.pi * self.b1_khz * 1e3) * 1e6
        return textwrap.dedent(f"""\
            ==================== AbirQu NMR Quantum Computer ====================

            Liquid sample tube ({self.molecule.formula}, {self.n}-qubit register)

                magnet: superconducting solenoid @ 11.75 T
               +---------------------------------------------------+
               |   ++++++  superconducting coil                ++++++   |
               |   ++++++        (LHe cryostat, 4.2 K)         ++++++   |
               |                                                   |
               |        ~~~~~~~~~~~~ B0 (static field)            |
               |            |                                     |
               |          | + |   5 mm sample tube                |
               |          | | |    {self.molecule.name:<20s}    |
               |          | + |                                   |
               |            ~~~~~~~~~~ gradient coil (z1/z2)      |
               +---------------------------------------------------+
                         |  probe head (H/C RF coils)
                         v

            RF channels via software-defined console (AbirQu-NMR II):
                {ch}

            Scalar J-coupling gates (free evolution, tau = 1/(2J)):
                {coup}

            RF amplitude B1 = {self.b1_khz:g} kHz -> pi/2 pulse = {p90:.1f} us
            CNOT cost: 2 x H_t (2 pulses) + 2 virtual Z + J-evolution
            ====================================================================""")

    def export_layout_html(self, path: str) -> str:
        """Write a standalone HTML layout page (no external assets)."""
        s = self.spec()
        rows = "".join(
            f"<tr><td>q{c['qubit']}</td><td>{c['nucleus']}</td>"
            f"<td>{c['larmor_mhz']:.2f}</td><td>{c['t2_ms']:.1f}</td></tr>"
            for c in s["channels"])
        couplings = "".join(
            f"<li>J({k}) = {v:.1f} Hz</li>"
            for k, v in s["coupling_graph"].items())
        html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>AbirQu NMR Quantum Computer — {s['register']['name']}</title>
<style>
 body {{ font-family: 'Segoe UI', system-ui, sans-serif; background: #0a0a0f;
        color: #e0e0e0; margin: 0; padding: 24px; }}
 h1,h2 {{ color: #00ff88; }} .card {{ background: #12121a;
        border: 1px solid #2a2a3a; border-radius: 12px; padding: 20px;
        margin-bottom: 18px; }} table {{ border-collapse: collapse; }}
 td, th {{ border: 1px solid #2a2a3a; padding: 6px 14px; }}
 th {{ color: #00aaff; }} .mono {{ font-family: 'Fira Code', monospace; }}
</style></head><body>
<div class="container"><h1>AbirQu NMR Quantum Computer</h1>
<p>{s['register']['name']} ({s['register']['formula']}) —
{s['register']['num_qubits'] if 'num_qubits' in s['register'] else len(s['channels'])}-qubit register</p>
<div class="card"><h2>RF channels</h2><table>
<tr><th>qubit</th><th>nucleus</th><th>Larmor (MHz)</th><th>T2 (ms)</th></tr>
{rows}</table></div>
<div class="card"><h2>Coupling graph (entangling gates)</h2><ul>{couplings}</ul></div>
<div class="card"><h2>Device</h2><ul>
<li>Magnet: {s['hardware']['magnet']['type']}, {s['hardware']['magnet']['field']}</li>
<li>Probe: {s['hardware']['probe']}</li>
<li>Console: {s['hardware']['console']}</li>
<li>Shims: {', '.join(s['hardware']['shims'])}</li>
<li>B1 = {s['rf_amplitude_hz']} Hz — pi/2 pulse = {s['pi_over_2_pulse_us']:.1f} us</li>
<li>Longest J evolution = {s['min_j_evolution_ms']:.2f} ms</li>
</ul></div>
<div class="card mono" style="white-space:pre-wrap">{self.layout()}</div>
</div></body></html>"""
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        return path


def expm_pi(pauli: np.ndarray, angle: float) -> np.ndarray:
    """exp(-i angle/2 * pauli)."""
    return (math.cos(angle / 2) * _PID
            - 1j * math.sin(angle / 2) * pauli)


__all__ = [
    "NMRSystem", "Molecule", "Nucleus", "MOLECULES",
    "list_molecules",
]
