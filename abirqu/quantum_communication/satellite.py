"""
Satellite Quantum Key Distribution
Copyright 2026 Abir Maheshwari

Long-distance QKD via satellite links.
Supports India's 1,000-km and 2,000-km QKD network plans.

Key advantage: Free-space loss scales as 1/R² (vs exponential in fiber).
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class SatelliteLink:
    """Parameters for a satellite quantum link."""
    altitude_km: float = 500.0
    ground_station_altitude_km: float = 0.0
    beam_divergence_urad: float = 10.0
    telescope_diameter_m: float = 0.5
    atmospheric_transmission: float = 0.3
    pointing_error_urad: float = 1.0


@dataclass
class SatelliteQKDResult:
    """Result of satellite QKD simulation."""
    distance_km: float
    channel_loss_db: float
    detection_rate: float
    key_rate: float
    key_length: int
    secure: bool
    link_budget: Dict[str, float]


class SatelliteQKD:
    """
    Satellite QKD Simulator.

    Simulates QKD via low-earth orbit (LEO) satellites.

    Usage:
        sat = SatelliteQKD(link=SatelliteLink(altitude_km=500))
        result = sat.simulate(num_pulses=1e6)
        print(f"Key length: {result.key_length} bits")
    """

    def __init__(self, link: Optional[SatelliteLink] = None,
                 detector_efficiency: float = 0.9,
                 dark_count_rate: float = 1e-6,
                 wavelength_nm: float = 810,
                 seed: Optional[int] = None):
        self.link = link or SatelliteLink()
        self.detector_efficiency = detector_efficiency
        self.dark_count_rate = dark_count_rate
        self.wavelength_nm = wavelength_nm
        self.rng = np.random.default_rng(seed)

    def simulate(self, num_pulses: int = 1000000) -> SatelliteQKDResult:
        """Simulate satellite QKD link."""
        # Compute slant range
        slant_range = self._compute_slant_range()

        # Free-space loss (1/R² scaling)
        free_space_loss_db = self._free_space_loss(slant_range)

        # Atmospheric loss
        atm_loss_db = -10 * np.log10(self.link.atmospheric_transmission)

        # Beam pointing loss
        pointing_loss_db = self._pointing_loss()

        # Total loss
        total_loss_db = free_space_loss_db + atm_loss_db + pointing_loss_db
        total_transmission = 10 ** (-total_loss_db / 10)

        # Detection rate
        detection_rate = total_transmission * self.detector_efficiency

        # Key rate (simplified)
        key_rate = detection_rate * 0.5  # After sifting

        # Key length
        key_length = int(num_pulses * key_rate)

        # Link budget
        link_budget = {
            'slant_range_km': slant_range,
            'free_space_loss_db': free_space_loss_db,
            'atmospheric_loss_db': atm_loss_db,
            'pointing_loss_db': pointing_loss_db,
            'total_loss_db': total_loss_db,
            'total_transmission': total_transmission,
        }

        return SatelliteQKDResult(
            distance_km=slant_range,
            channel_loss_db=total_loss_db,
            detection_rate=detection_rate,
            key_rate=key_rate,
            key_length=key_length,
            secure=key_length > 0,
            link_budget=link_budget,
        )

    def _compute_slant_range(self) -> float:
        """Compute slant range from ground station to satellite."""
        R_earth = 6371.0  # km
        h_sat = self.link.altitude_km
        h_gs = self.link.ground_station_altitude_km

        # Simplified slant range (zenith pass)
        slant = np.sqrt((R_earth + h_sat)**2 - (R_earth + h_gs)**2)
        return slant

    def _free_space_loss(self, distance_km: float) -> float:
        """Free-space path loss in dB."""
        # FSPL = (4πd/λ)²
        wavelength_m = self.wavelength_nm * 1e-9
        distance_m = distance_km * 1000

        fspl = (4 * np.pi * distance_m / wavelength_m) ** 2
        fspl_db = 10 * np.log10(fspl)

        return fspl_db

    def _pointing_loss(self) -> float:
        """Pointing error loss in dB."""
        # Gaussian beam approximation
        theta = self.link.pointing_error_urad * 1e-6
        w0 = self.link.beam_divergence_urad * 1e-6 * self.link.altitude_km * 1000

        if w0 > 0:
            loss = np.exp(-2 * (theta / w0) ** 2)
            return -10 * np.log10(max(loss, 1e-10))
        return 0.0

    def compare_with_fiber(self, fiber_distance_km: float,
                            fiber_loss_db_km: float = 0.2) -> Dict[str, Any]:
        """Compare satellite vs fiber QKD."""
        # Satellite result
        sat_result = self.simulate()

        # Fiber result
        fiber_loss_db = fiber_loss_db_km * fiber_distance_km
        fiber_transmission = 10 ** (-fiber_loss_db / 10)

        return {
            'satellite': {
                'distance_km': sat_result.distance_km,
                'loss_db': sat_result.channel_loss_db,
                'key_rate': sat_result.key_rate,
            },
            'fiber': {
                'distance_km': fiber_distance_km,
                'loss_db': fiber_loss_db,
                'key_rate': fiber_transmission * self.detector_efficiency * 0.5,
            },
        }
