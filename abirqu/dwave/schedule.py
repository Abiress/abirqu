"""
D-Wave Annealing Schedule
=========================
Control quantum annealing parameters: anneal time, pause, quench, and freezeout.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


@dataclass
class AnnealingSchedule:
    """Quantum annealing schedule for D-Wave.

    Parameters
    ----------
    anneal_time : float
        Total anneal time in microseconds (default: 20 μs).
    pause_at : float
        Fraction of anneal at which to pause (0-1).  None = no pause.
    pause_time : float
        Duration of pause in microseconds.
    quench_rate : float
        Rate of quench at the end (0-1, where 1 = instant).
    """
    anneal_time: float = 20.0
    pause_at: Optional[float] = None
    pause_time: float = 50.0
    quench_rate: float = 0.0

    def get_s_values(self, num_points: int = 100) -> np.ndarray:
        """Return the s(t) schedule as an array of s values.

        s = 0 at t=0 (start of anneal, all transverse field)
        s = 1 at t=end (end of anneal, classical Ising)
        """
        total_time = self.anneal_time
        if self.pause_at is not None:
            total_time += self.pause_time

        t = np.linspace(0, total_time, num_points)
        s = np.zeros_like(t)

        if self.pause_at is None:
            # Simple linear schedule
            s = t / self.anneal_time
            s = np.clip(s, 0, 1)
        else:
            pause_t = self.anneal_time * self.pause_at
            for i, ti in enumerate(t):
                if ti <= pause_t:
                    s[i] = ti / self.anneal_time
                elif ti <= pause_t + self.pause_time:
                    s[i] = self.pause_at
                else:
                    elapsed = ti - pause_t - self.pause_time
                    remaining = self.anneal_time - pause_t
                    s[i] = self.pause_at + elapsed / remaining
            s = np.clip(s, 0, 1)

        return s

    def get_pause_schedule(self) -> dict:
        """Return schedule parameters for D-Wave API."""
        schedule = {
            "annealing_time": self.anneal_time,
        }
        if self.pause_at is not None:
            schedule["pause_schedule"] = [
                {"s": self.pause_at, "t": self.anneal_time * self.pause_at},
                {"s": self.pause_at, "t": self.anneal_time * self.pause_at + self.pause_time},
            ]
        return schedule


@dataclass
class FreezeoutEstimate:
    """Estimate of quantum annealing freezeout parameters.

    Attributes
    ----------
    freezeout_s : float
        The s value at which the system freezes.
    freezeout_time : float
        The time at which the system freezes (μs).
    effective_temperature : float
        Effective temperature in Kelvin at freezeout.
    tunneling_gap : float
        Minimum spectral gap (GHz).
    """
    freezeout_s: float
    freezeout_time: float
    effective_temperature: float
    tunneling_gap: float

    @classmethod
    def estimate(cls, s_values: np.ndarray, gaps: Optional[np.ndarray] = None) -> "FreezeoutEstimate":
        """Estimate freezeout from annealing schedule and spectral gaps.

        Uses the standard Landau-Zener model: freezeout occurs when
        the relaxation time exceeds the annealing time.
        """
        if gaps is None:
            # Approximate minimum gap at s ≈ 0.6
            gaps = 0.01 * np.ones_like(s_values)

        # Find minimum gap
        min_gap_idx = np.argmin(gaps)
        freezeout_s = float(s_values[min_gap_idx])
        freezeout_time = freezeout_s * 20.0  # approximate

        # Effective temperature from Landau-Zener
        kB = 0.0208366  # GHz/K
        gap_ghz = float(gaps[min_gap_idx])
        effective_temp = gap_ghz / (2 * kB) if gap_ghz > 0 else 10.0

        return cls(
            freezeout_s=freezeout_s,
            freezeout_time=freezeout_time,
            effective_temperature=effective_temp,
            tunneling_gap=gap_ghz,
        )


def linear_schedule(anneal_time: float = 20.0) -> AnnealingSchedule:
    """Create a simple linear annealing schedule."""
    return AnnealingSchedule(anneal_time=anneal_time)


def pause_schedule(
    pause_at: float = 0.5,
    anneal_time: float = 20.0,
    pause_time: float = 50.0,
) -> AnnealingSchedule:
    """Create a schedule with a pause at a given s value."""
    return AnnealingSchedule(
        anneal_time=anneal_time,
        pause_at=pause_at,
        pause_time=pause_time,
    )


def quench_schedule(
    anneal_time: float = 20.0,
    quench_rate: float = 0.5,
) -> AnnealingSchedule:
    """Create a schedule with a quench at the end."""
    return AnnealingSchedule(
        anneal_time=anneal_time,
        quench_rate=quench_rate,
    )
