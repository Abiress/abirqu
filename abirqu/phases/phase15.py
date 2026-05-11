from typing import Any, Dict, Iterable, List, Sequence

import numpy as np


class QuantumSensorSimulator:
    def simulate(self, sensor_type: str, true_signal: float, noise_std: float, shots: int = 1000) -> Dict[str, Any]:
        rng = np.random.default_rng(42)
        samples = rng.normal(loc=true_signal, scale=noise_std, size=shots)
        mean = float(np.mean(samples))
        std = float(np.std(samples))
        crb = (noise_std ** 2) / max(shots, 1)
        return {"sensor": sensor_type, "estimate": mean, "std": std, "cramer_rao_bound": crb}


class QuantumEnhancedMeasurementProtocols:
    def squeezed_state_precision(self, variance_reduction: float) -> Dict[str, float]:
        return {"precision_gain": 1.0 / max(1e-9, variance_reduction)}

    def noon_phase_resolution(self, n_photons: int) -> Dict[str, float]:
        return {"phase_resolution": 1.0 / max(1, n_photons)}

    def entanglement_enhancement(self, n_particles: int) -> Dict[str, float]:
        sql = 1.0 / np.sqrt(max(1, n_particles))
        hl = 1.0 / max(1, n_particles)
        return {"sql": float(sql), "heisenberg_limit": float(hl), "advantage": float(sql / hl)}


class QuantumClockTiming:
    def synchronize(self, offsets_ns: Sequence[float]) -> Dict[str, Any]:
        avg = float(np.mean(offsets_ns)) if offsets_ns else 0.0
        residuals = [float(o - avg) for o in offsets_ns]
        return {"reference_offset_ns": avg, "residuals_ns": residuals}

    def quantum_gps_gain(self, baseline_error_m: float) -> Dict[str, float]:
        return {"baseline_error_m": baseline_error_m, "quantum_enhanced_error_m": baseline_error_m * 0.5}


class QuantumImagingModule:
    def ghost_imaging(self, signal_strength: float, noise: float) -> Dict[str, Any]:
        snr = signal_strength / max(noise, 1e-9)
        return {"snr": snr, "mode": "ghost"}

    def quantum_illumination(self, target_reflectivity: float, background_noise: float) -> Dict[str, Any]:
        score = target_reflectivity / max(background_noise, 1e-9)
        return {"detection_score": score, "detected": score > 1.0}

    def reconstruct(self, pixels: Sequence[float]) -> Dict[str, Any]:
        arr = np.asarray(pixels, dtype=float)
        return {"min": float(np.min(arr)), "max": float(np.max(arr)), "mean": float(np.mean(arr))}


class SensingAlgorithmLibrary:
    def estimate_parameter(self, observations: Sequence[float]) -> Dict[str, float]:
        arr = np.asarray(observations, dtype=float)
        return {"estimate": float(np.mean(arr)), "variance": float(np.var(arr))}

    def multi_parameter_estimation(self, observations: Dict[str, Sequence[float]]) -> Dict[str, Dict[str, float]]:
        return {k: self.estimate_parameter(v) for k, v in observations.items()}

    def optimize_sensitivity(self, baseline: float, control_gain: float) -> Dict[str, float]:
        return {"baseline": baseline, "optimized": baseline / max(control_gain, 1e-9)}
