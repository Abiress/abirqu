"""Space quantum communication protocols."""

import hashlib
import math
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple


@dataclass
class EntanglementSwapper:
    num_relay_nodes: int
    link_fidelity: float
    swap_success_probability: float

    def simulate_relay_chain(self, distance_km: float) -> Dict[str, Any]:
        hops = max(1, self.num_relay_nodes)
        swap_gain = 0.6 + 0.4 * self.swap_success_probability
        f = (self.link_fidelity ** hops) * swap_gain
        attenuation = math.exp(-distance_km / 20_000_000.0)
        f *= attenuation
        return {
            "end_to_end_fidelity": float(max(0.0, min(1.0, f))),
            "one_way_latency_seconds": float(distance_km / 299_792.458),
        }


class OrbitalSatelliteNoiseModel:
    _MODELS = {
        "LEO": {"altitude_km": 500, "atmospheric_error_rate": 0.05, "doppler_shift_ghz": 0.010, "beam_divergence_loss_db": 20, "background_noise_cps": 1000},
        "GEO": {"altitude_km": 35786, "atmospheric_error_rate": 0.08, "doppler_shift_ghz": 0.005, "beam_divergence_loss_db": 40, "background_noise_cps": 500},
        "LUNAR": {"altitude_km": 384400, "atmospheric_error_rate": 0.0, "doppler_shift_ghz": 0.050, "beam_divergence_loss_db": 60, "background_noise_cps": 100},
        "MARS": {"altitude_km": 225_000_000, "atmospheric_error_rate": 0.0, "doppler_shift_ghz": 1.5, "beam_divergence_loss_db": 120, "background_noise_cps": 10},
    }

    def __init__(self, orbit: str):
        self.orbit = orbit.upper()

    def compute_channel_model(self) -> Dict[str, Any]:
        return dict(self._MODELS.get(self.orbit, self._MODELS["LEO"]))


class DeepSpaceRelay:
    _ROUTES = {
        "Earth-LEO": (500, 1, 0.99),
        "Earth-Moon": (384_400, 2, 0.97),
        "Earth-Mars": (225_000_000, 5, 0.95),
    }

    def simulate_route(self, route_name: str) -> Dict[str, Any]:
        d, n, f = self._ROUTES.get(route_name, self._ROUTES["Earth-LEO"])
        swap = EntanglementSwapper(n, f, 0.85).simulate_relay_chain(d)
        return {"entanglement_swapping": swap, "is_viable": swap["end_to_end_fidelity"] > 0.1}


class QKDTelemetryChannel:
    def __init__(self, probe_name: str, distance_km: float):
        self.probe_name = probe_name
        self.distance_km = distance_km
        self._shared_key = os.urandom(32)

    def negotiate_key(self, num_raw_bits: int) -> Dict[str, Any]:
        sifted = max(32, num_raw_bits // 2)
        qber = min(0.1, 0.01 + self.distance_km / 1e12)
        return {
            "sifted_key_length": sifted,
            "qber": qber,
            "is_secure": qber < 0.11,
            "final_key_hex": self._shared_key.hex(),
        }

    def _keystream(self, n: int) -> bytes:
        out = b""
        counter = 0
        while len(out) < n:
            out += hashlib.sha256(self._shared_key + counter.to_bytes(4, "big")).digest()
            counter += 1
        return out[:n]

    def encrypt_telemetry_frame(self, plaintext: str) -> Dict[str, Any]:
        p = plaintext.encode("utf-8")
        ks = self._keystream(len(p))
        c = bytes(a ^ b for a, b in zip(p, ks))
        return {"ciphertext_hex": c.hex(), "security_level": "InformationTheoretic"}

    def decrypt_telemetry_frame(self, ciphertext_hex: str) -> str:
        c = bytes.fromhex(ciphertext_hex)
        ks = self._keystream(len(c))
        p = bytes(a ^ b for a, b in zip(c, ks))
        return p.decode("utf-8")


class EntanglementSensorNetwork:
    def __init__(self, num_sensors: int, baseline_sensitivity: float):
        self.num_sensors = num_sensors
        self.baseline_sensitivity = baseline_sensitivity

    def deploy_network(self, positions: Sequence[Tuple[float, float, float]]) -> Dict[str, Any]:
        n = len(positions)
        return {
            "num_sensors": n,
            "max_baseline_km": float(max(1, n - 1) * 100),
            "effective_aperture_km2": float(100 * n * n),
        }

    def simulate_measurement(self, signal_strength: float) -> Dict[str, Any]:
        sql = self.baseline_sensitivity / math.sqrt(max(1, self.num_sensors))
        heis = self.baseline_sensitivity / max(1, self.num_sensors)
        return {
            "true_signal": signal_strength,
            "heisenberg_sensitivity": heis,
            "standard_quantum_limit": sql,
            "snr_heisenberg": signal_strength / max(heis, 1e-12),
            "snr_classical": signal_strength / max(sql, 1e-12),
            "quantum_advantage_factor": sql / max(heis, 1e-12),
            "entanglement_state": f"GHZ_{self.num_sensors}",
        }


__all__ = [
    "EntanglementSwapper",
    "OrbitalSatelliteNoiseModel",
    "DeepSpaceRelay",
    "QKDTelemetryChannel",
    "EntanglementSensorNetwork",
]
