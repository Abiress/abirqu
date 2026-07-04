"""
AbirQu State Vector Visualizer
Copyright 2026 Abir Maheshwari

Real-time state vector visualization with probability bars and phase indicators.
"""
import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class StateEntry:
    """A single basis state with amplitude and probability."""
    bitstring: str
    amplitude_real: float
    amplitude_imag: float
    probability: float

    @property
    def amplitude(self) -> complex:
        return complex(self.amplitude_real, self.amplitude_imag)

    @property
    def phase(self) -> float:
        return math.atan2(self.amplitude_imag, self.amplitude_real)

    @property
    def phase_degrees(self) -> float:
        return math.degrees(self.phase)


class StateVisualizer:
    """Visualizes quantum state vectors with probability bars and phase."""

    def __init__(self, max_display: int = 32):
        self.max_display = max_display
        self.states: List[StateEntry] = []
        self.num_qubits = 0
        self._callbacks = []

    def on(self, event: str, callback):
        self._callbacks.append((event, callback))

    def _emit(self, event: str, data: Any):
        for ev, cb in self._callbacks:
            if ev == event:
                try:
                    cb(data)
                except Exception:
                    pass

    def set_statevector(self, amplitudes: List[complex], num_qubits: int):
        self.num_qubits = num_qubits
        self.states = []
        for i, amp in enumerate(amplitudes):
            prob = abs(amp) ** 2
            if prob > 1e-10:
                bitstring = format(i, f'0{num_qubits}b')
                self.states.append(StateEntry(
                    bitstring=bitstring,
                    amplitude_real=amp.real,
                    amplitude_imag=amp.imag,
                    probability=prob,
                ))
        self.states.sort(key=lambda s: -s.probability)
        self._emit('state_updated', self.get_render_data())

    def set_from_counts(self, counts: Dict[str, int], shots: int):
        self.num_qubits = len(list(counts.keys())[0]) if counts else 0
        self.states = []
        for bitstring, count in sorted(counts.items(), key=lambda x: -x[1]):
            prob = count / shots if shots > 0 else 0
            self.states.append(StateEntry(
                bitstring=bitstring,
                amplitude_real=math.sqrt(prob),
                amplitude_imag=0,
                probability=prob,
            ))
        self._emit('state_updated', self.get_render_data())

    def get_render_data(self) -> Dict:
        display_states = self.states[:self.max_display]
        max_prob = max((s.probability for s in display_states), default=1.0)

        bars = []
        for s in display_states:
            bar_height = (s.probability / max_prob * 100) if max_prob > 0 else 0
            color = self._phase_color(s.phase)
            bars.append({
                'label': s.bitstring,
                'probability': s.probability,
                'bar_height': bar_height,
                'color': color,
                'amplitude': str(s.amplitude),
                'phase': s.phase_degrees,
                'magnitude': abs(s.amplitude),
            })

        total_prob = sum(s.probability for s in self.states)
        entropy = -sum(s.probability * math.log2(s.probability)
                      for s in self.states if s.probability > 1e-10)

        stats = {
            'total_probability': total_prob,
            'entropy': entropy,
            'num_qubits': self.num_qubits,
            'num_states': len(self.states),
        }

        return {
            'num_qubits': self.num_qubits,
            'num_states': len(self.states),
            'total_probability': total_prob,
            'entropy': entropy,
            'bars': bars,
            'statistics': stats,
            'max_displayed': len(display_states),
            'truncated': len(self.states) > self.max_display,
        }

    def get_bloch_data(self) -> Dict:
        """Extract single-qubit Bloch data for each qubit."""
        if self.num_qubits != 1 or not self.states:
            bloch_data = []
            for q in range(self.num_qubits):
                p0, p1 = 0.0, 0.0
                for s in self.states:
                    if q < len(s.bitstring):
                        bit = int(s.bitstring[q])
                        if bit == 0:
                            p0 += s.probability
                        else:
                            p1 += s.probability
                total = p0 + p1
                if total > 0:
                    p0 /= total
                    p1 /= total
                theta = 2 * math.acos(min(1.0, math.sqrt(max(0, p0))))
                bloch_data.append({'qubit': q, 'theta': theta, 'phi': 0.0,
                                   'x': math.sin(theta), 'y': 0, 'z': math.cos(theta)})
            return {'single_qubit': False, 'qubits': bloch_data}

        alpha = 0
        beta = 0
        for s in self.states:
            if s.bitstring == '0':
                alpha = s.amplitude
            elif s.bitstring == '1':
                beta = s.amplitude
        theta = 2 * math.acos(min(1.0, abs(alpha)))
        phi = math.atan2(beta.imag, beta.real) if abs(beta) > 1e-10 else 0
        return {
            'single_qubit': True,
            'theta': theta, 'phi': phi,
            'x': math.sin(theta) * math.cos(phi),
            'y': math.sin(theta) * math.sin(phi),
            'z': math.cos(theta),
        }

    @staticmethod
    def _phase_color(phase: float) -> str:
        h = int(((phase + math.pi) / (2 * math.pi)) * 360) % 360
        s, v = 0.8, 0.9
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c
        if h < 60:
            r, g, b = c, x, 0
        elif h < 120:
            r, g, b = x, c, 0
        elif h < 180:
            r, g, b = 0, c, x
        elif h < 240:
            r, g, b = 0, x, c
        elif h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        return f'#{int((r+m)*255):02x}{int((g+m)*255):02x}{int((b+m)*255):02x}'

    def __len__(self):
        return len(self.states)

    def __repr__(self):
        return f"StateVisualizer(qubits={self.num_qubits}, states={len(self.states)})"
