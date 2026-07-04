"""
AbirQu Measurement Panel
Copyright 2026 Abir Maheshwari

Measurement histogram and statistics display.
"""
import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class MeasurementBin:
    """A single bin in the measurement histogram."""
    label: str
    count: int
    probability: float
    percentage: float


class MeasurementPanel:
    """Measurement results panel with histogram and statistics."""

    def __init__(self):
        self.counts: Dict[str, int] = {}
        self.shots: int = 0
        self.num_qubits: int = 0
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

    def set_results(self, counts: Dict[str, int], shots: int):
        self.counts = counts
        self.shots = shots
        self.num_qubits = len(list(counts.keys())[0]) if counts else 0
        self._emit('measurement_updated', self.get_render_data())

    def get_bins(self, sort_by: str = 'probability') -> List[MeasurementBin]:
        if not self.counts:
            return []

        bins = []
        for label, count in self.counts.items():
            prob = count / self.shots if self.shots > 0 else 0
            bins.append(MeasurementBin(
                label=label, count=count,
                probability=prob, percentage=prob * 100,
            ))

        if sort_by == 'probability':
            bins.sort(key=lambda b: -b.count)
        elif sort_by == 'label':
            bins.sort(key=lambda b: b.label)

        return bins

    def get_statistics(self) -> Dict:
        if not self.counts:
            return {
                'total_shots': 0, 'unique_outcomes': 0,
                'entropy': 0, 'max_probability': 0,
                'min_probability': 0, 'mean_probability': 0,
                'most_likely': None, 'least_likely': None,
            }

        bins = self.get_bins()
        probs = [b.probability for b in bins]

        entropy = -sum(p * math.log2(p) for p in probs if p > 1e-10)
        max_entropy = math.log2(len(bins)) if bins else 0
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

        return {
            'total_shots': self.shots,
            'unique_outcomes': len(bins),
            'entropy': entropy,
            'max_entropy': max_entropy,
            'normalized_entropy': normalized_entropy,
            'max_probability': max(probs),
            'min_probability': min(probs),
            'mean_probability': sum(probs) / len(probs),
            'most_likely': bins[0].label if bins else None,
            'least_likely': bins[-1].label if bins else None,
            'bias': self._compute_bias(),
        }

    def _compute_bias(self) -> Dict:
        if not self.counts or self.shots == 0:
            return {}
        bias = {}
        for q in range(self.num_qubits):
            p0 = 0
            for label, count in self.counts.items():
                if q < len(label) and int(label[q]) == 0:
                    p0 += count
            bias[f'q{q}'] = {
                'P(0)': p0 / self.shots,
                'P(1)': 1 - p0 / self.shots,
                'bias': abs(p0 / self.shots - 0.5) * 2,
            }
        return bias

    def get_render_data(self) -> Dict:
        bins = self.get_bins()
        stats = self.get_statistics()
        max_count = max((b.count for b in bins), default=1)

        bars = []
        for b in bins:
            bar_width = (b.count / max_count * 100) if max_count > 0 else 0
            bars.append({
                'label': b.label,
                'count': b.count,
                'probability': b.probability,
                'percentage': b.percentage,
                'bar_width': bar_width,
            })

        return {
            'bars': bars,
            'statistics': stats,
            'num_qubits': self.num_qubits,
            'shots': self.shots,
        }

    def get_per_qubit_data(self) -> List[Dict]:
        if not self.counts or self.shots == 0:
            return []
        result = []
        for q in range(self.num_qubits):
            p0, p1 = 0.0, 0.0
            for label, count in self.counts.items():
                if q < len(label):
                    if int(label[q]) == 0:
                        p0 += count
                    else:
                        p1 += count
            total = p0 + p1
            result.append({
                'qubit': q,
                'p_zero': p0 / total if total > 0 else 0.5,
                'p_one': p1 / total if total > 0 else 0.5,
            })
        return result

    def clear(self):
        self.counts = {}
        self.shots = 0
        self.num_qubits = 0
        self._emit('measurement_cleared', None)

    def __repr__(self):
        return f"MeasurementPanel(shots={self.shots}, outcomes={len(self.counts)})"
