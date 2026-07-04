"""
Hardware Detection & Auto-Scaling Simulator.

Automatically detects CPU, RAM, GPU, and architecture, then selects
the optimal simulation backend and scales operations accordingly.

Flow:
    1. Detect hardware (CPU cores, RAM, GPU VRAM, SIMD, architecture)
    2. For a given circuit (qubit count, depth, entanglement):
       a. Estimate memory for each backend
       b. Pick the fastest backend that fits in memory
       c. Auto-tune parameters (bond dimension, batch size, etc.)
    3. Execute with the best configuration

This means the user never needs to manually choose between
GPU/MPS/statevector/Clifford — AbirQu picks the best one.

References:
    - MPS bond dimension auto-tuning
    - GPU memory-aware batching
    - Architecture-specific SIMD optimization
"""

import os
import sys
import math
import platform
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

import numpy as np


class BackendType(Enum):
    """Available simulation backends."""
    GPU_STATEVECTOR = "gpu_statevector"     # CuPy/NumPy statevector on GPU
    CPU_STATEVECTOR = "cpu_statevector"     # NumPy statevector on CPU
    MPS = "mps"                             # Matrix Product State (tensor network)
    CLIFFORD = "clifford"                   # Stabilizer tableau
    MONTE_CARLO = "monte_carlo"             # Stochastic trajectories
    DENSITY_MATRIX = "density_matrix"       # Full density matrix (very expensive)


@dataclass
class HardwareInfo:
    """Detected hardware characteristics."""
    # CPU
    cpu_cores: int = 0
    cpu_threads: int = 0
    cpu_freq_ghz: float = 0.0
    cpu_arch: str = ""            # x86_64, aarch64, etc.
    cpu_vendor: str = ""          # Intel, AMD, Apple, etc.
    simd_width: int = 0           # 128=SSE, 256=AVX2, 512=AVX-512
    has_avx512: bool = False
    has_avx2: bool = False
    has_neon: bool = False        # ARM NEON

    # Memory
    ram_gb: float = 0.0
    available_ram_gb: float = 0.0

    # GPU
    gpu_available: bool = False
    gpu_name: str = ""
    gpu_vram_gb: float = 0.0
    gpu_available_vram_gb: float = 0.0
    gpu_compute_capability: str = ""
    gpu_driver: str = ""

    # Architecture hints
    is_apple_silicon: bool = False
    is_arm: bool = False
    is_x86: bool = False
    endianness: str = "little"

    @property
    def total_memory_gb(self) -> float:
        """Total usable memory (RAM + GPU VRAM)."""
        return self.available_ram_gb + self.gpu_available_vram_gb


@dataclass
class SimulationEstimate:
    """Estimate for running a circuit on a specific backend."""
    backend: BackendType
    memory_required_gb: float
    time_estimate_s: float
    fits_in_memory: bool
    max_qubits_supported: int
    auto_params: Dict[str, Any] = field(default_factory=dict)


class HardwareDetector:
    """
    Detect available hardware and capabilities.

    Checks CPU, RAM, GPU (CUDA/ROCm), SIMD, and architecture.
    """

    def __init__(self):
        self._info: Optional[HardwareInfo] = None

    def detect(self) -> HardwareInfo:
        """Run full hardware detection. Cached after first call."""
        if self._info is not None:
            return self._info

        info = HardwareInfo()

        # CPU detection
        info.cpu_cores = os.cpu_count() or 1
        info.cpu_threads = info.cpu_cores
        info.cpu_arch = platform.machine()
        info.cpu_vendor = platform.processor() or "Unknown"
        info.is_arm = "arm" in info.cpu_arch.lower() or "aarch64" in info.cpu_arch.lower()
        info.is_x86 = "x86" in info.cpu_arch.lower() or "amd64" in info.cpu_arch.lower()
        info.is_apple_silicon = (platform.system() == "Darwin" and info.is_arm)
        info.endianness = sys.byteorder

        # CPU frequency
        try:
            if platform.system() == "Linux":
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "cpu MHz" in line:
                            freq = float(line.split(":")[1].strip())
                            info.cpu_freq_ghz = freq / 1000
                            break
            elif platform.system() == "Darwin":
                out = subprocess.run(
                    ["sysctl", "-n", "hw.cpufrequency"],
                    capture_output=True, text=True, timeout=5
                )
                if out.returncode == 0:
                    info.cpu_freq_ghz = int(out.stdout.strip()) / 1e9
        except Exception:
            info.cpu_freq_ghz = 2.5  # Default assumption

        # SIMD detection
        try:
            if platform.system() == "Linux":
                with open("/proc/cpuinfo") as f:
                    flags = f.read()
                    info.has_avx512 = "avx512" in flags
                    info.has_avx2 = "avx2" in flags
                    info.has_neon = "neon" in flags
            elif platform.system() == "Darwin":
                out = subprocess.run(
                    ["sysctl", "-n", "hw.optional.avx2_0"],
                    capture_output=True, text=True, timeout=5
                )
                info.has_avx2 = out.stdout.strip() == "1"
                out = subprocess.run(
                    ["sysctl", "-n", "hw.optional.avx512f"],
                    capture_output=True, text=True, timeout=5
                )
                info.has_avx512 = out.stdout.strip() == "1"
        except Exception:
            pass

        if info.has_avx512:
            info.simd_width = 512
        elif info.has_avx2:
            info.simd_width = 256
        elif info.has_neon:
            info.simd_width = 128
        else:
            info.simd_width = 128

        # RAM detection
        try:
            import psutil
            mem = psutil.virtual_memory()
            info.ram_gb = mem.total / (1024 ** 3)
            info.available_ram_gb = mem.available / (1024 ** 3)
        except ImportError:
            # Fallback: read /proc/meminfo
            try:
                with open("/proc/meminfo") as f:
                    for line in f:
                        if "MemTotal" in line:
                            kb = int(line.split()[1])
                            info.ram_gb = kb / (1024 ** 2)
                            info.available_ram_gb = info.ram_gb * 0.8  # Assume 80% available
                            break
            except Exception:
                info.ram_gb = 8.0  # Conservative default
                info.available_ram_gb = 6.0

        # GPU detection
        self._detect_gpu(info)

        self._info = info
        return info

    def _detect_gpu(self, info: HardwareInfo):
        """Detect GPU via CUDA, ROCm, or system commands."""
        # Try CuPy first
        try:
            import cupy as cp
            info.gpu_available = True
            info.gpu_name = cp.cuda.runtime.getDeviceProperties(0)['name'].decode()
            mem = cp.cuda.mem_get_info()
            info.gpu_vram_gb = mem[1] / (1024 ** 3)
            info.gpu_available_vram_gb = mem[0] / (1024 ** 3)
            info.gpu_compute_capability = f"{cp.cuda.runtime.getDeviceProperties(0)['major']}.{cp.cuda.runtime.getDeviceProperties(0)['minor']}"
            return
        except (ImportError, Exception):
            pass

        # Try nvidia-smi
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.free,driver_version",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if out.returncode == 0 and out.stdout.strip():
                parts = out.stdout.strip().split(", ")
                info.gpu_available = True
                info.gpu_name = parts[0]
                info.gpu_vram_gb = float(parts[1]) / 1024
                info.gpu_available_vram_gb = float(parts[2]) / 1024
                info.gpu_driver = parts[3] if len(parts) > 3 else ""
                return
        except (FileNotFoundError, Exception):
            pass

        # Try rocm-smi (AMD)
        try:
            out = subprocess.run(
                ["rocm-smi", "--showmeminfo", "vram"],
                capture_output=True, text=True, timeout=5
            )
            if out.returncode == 0:
                info.gpu_available = True
                info.gpu_name = "AMD GPU (ROCm)"
                return
        except (FileNotFoundError, Exception):
            pass


class MemoryEstimator:
    """
    Estimate memory requirements for different simulation backends.

    Uses analytical formulas to predict memory usage without
    actually allocating it.
    """

    @staticmethod
    def statevector_bytes(n_qubits: int) -> int:
        """Statevector memory: 2^n complex128 values."""
        return (2 ** n_qubits) * 16  # complex128 = 16 bytes

    @staticmethod
    def density_matrix_bytes(n_qubits: int) -> int:
        """Density matrix memory: 2^n × 2^n complex128 values."""
        dim = 2 ** n_qubits
        return dim * dim * 16

    @staticmethod
    def mps_bytes(n_qubits: int, bond_dimension: int) -> int:
        """
        MPS memory: n × bond_dim² × 2 × 16 bytes.

        Each tensor has shape (bond_left, 2, bond_right).
        """
        chi = bond_dimension
        return n_qubits * chi * chi * 2 * 16

    @staticmethod
    def monte_carlo_bytes(n_qubits: int, num_trajectories: int) -> int:
        """Monte Carlo memory: num_trajectories × statevector."""
        return num_trajectories * (2 ** n_qubits) * 16

    @staticmethod
    def estimate_mps_bond_dimension(n_qubits: int, circuit_depth: int,
                                     entanglement: str = "medium") -> int:
        """
        Estimate required bond dimension for MPS.

        For low entanglement: χ = O(1)
        For medium entanglement: χ = O(poly(depth))
        For high entanglement: χ = O(2^(depth/2))
        """
        if entanglement == "low":
            return min(4, 2 ** (circuit_depth // 10 + 1))
        elif entanglement == "medium":
            return min(64, 2 ** min(circuit_depth // 3, 6))
        else:  # high
            return min(256, 2 ** min(circuit_depth // 2, 8))


class SmartBackendRouter:
    """
    Automatically select the best simulation backend.

    Decision logic:
    1. If Clifford-only circuit → Clifford (fastest)
    2. If qubits ≤ 25 and GPU available → GPU statevector
    3. If qubits ≤ 25 and enough RAM → CPU statevector
    4. If qubits > 25 or low entanglement → MPS
    5. If noise simulation needed → Monte Carlo
    6. If density matrix needed → density matrix (if memory allows)
    """

    def __init__(self, hardware: Optional[HardwareInfo] = None):
        self.hardware = hardware or HardwareDetector().detect()
        self.estimator = MemoryEstimator()

    def select_backend(self, n_qubits: int,
                        circuit_depth: int = 1,
                        entanglement: str = "medium",
                        needs_noise: bool = False,
                        needs_density_matrix: bool = False,
                        prefer_gpu: Optional[bool] = None,
                        circuit=None) -> SimulationEstimate:
        """
        Select the best backend for a given circuit.

        Parameters
        ----------
        n_qubits : int
            Number of qubits
        circuit_depth : int
            Circuit depth (number of gate layers)
        entanglement : str
            Expected entanglement: 'low', 'medium', 'high'
        needs_noise : bool
            Whether noise simulation is required
        needs_density_matrix : bool
            Whether full density matrix is needed
        prefer_gpu : bool, optional
            Force GPU preference

        Returns
        -------
        SimulationEstimate
            Recommended backend with memory/time estimates
        """
        estimates = []

        # 1. Clifford (if applicable - only for Clifford-only circuits)
        clifford_gates = {"H", "X", "Y", "Z", "S", "S_DAG", "CNOT", "CZ", "SWAP"}
        non_clifford_gates = {"T", "T_DAG", "RX", "RY", "RZ"}
        # Check if circuit has non-Clifford gates by looking at gate names
        has_non_clifford = False
        if hasattr(circuit, 'gates'):
            for g in circuit.gates:
                if g.name.upper() in non_clifford_gates:
                    has_non_clifford = True
                    break
        if not needs_noise and not needs_density_matrix and not has_non_clifford:
            estimates.append(self._estimate_clifford(n_qubits, circuit_depth))

        # 2. GPU Statevector
        if self.hardware.gpu_available and (prefer_gpu is not False):
            estimates.append(self._estimate_gpu_statevector(n_qubits, circuit_depth))

        # 3. CPU Statevector
        estimates.append(self._estimate_cpu_statevector(n_qubits, circuit_depth))

        # 4. MPS
        estimates.append(self._estimate_mps(n_qubits, circuit_depth, entanglement))

        # 5. Monte Carlo (if noise needed)
        if needs_noise:
            estimates.append(self._estimate_monte_carlo(n_qubits, circuit_depth))

        # 6. Density Matrix
        if needs_density_matrix:
            estimates.append(self._estimate_density_matrix(n_qubits, circuit_depth))

        # Filter: only backends that fit in memory
        viable = [e for e in estimates if e.fits_in_memory]

        if not viable:
            # Emergency fallback: MPS with minimum bond dimension
            return SimulationEstimate(
                backend=BackendType.MPS,
                memory_required_gb=self.estimator.mps_bytes(n_qubits, 2) / (1024**3),
                time_estimate_s=n_qubits * 0.1,
                fits_in_memory=True,
                max_qubits_supported=n_qubits,
                auto_params={"bond_dimension": 2, "cutoff": 1e-6}
            )

        # Pick the fastest viable backend
        viable.sort(key=lambda e: e.time_estimate_s)
        return viable[0]

    def _estimate_clifford(self, n_qubits: int, depth: int) -> SimulationEstimate:
        """Clifford simulator estimate."""
        # Stabilizer tableau: O(n²) per gate
        time_per_gate = (n_qubits ** 2) * 1e-9  # nanoseconds
        total_time = time_per_gate * depth * n_qubits
        mem_gb = (n_qubits * 2 * (n_qubits // 8)) / (1024 ** 3)  # bit arrays

        return SimulationEstimate(
            backend=BackendType.CLIFFORD,
            memory_required_gb=max(mem_gb, 0.001),
            time_estimate_s=max(total_time, 0.001),
            fits_in_memory=mem_gb < self.hardware.available_ram_gb * 0.5,
            max_qubits_supported=min(n_qubits, 10000),
        )

    def _estimate_gpu_statevector(self, n_qubits: int, depth: int) -> SimulationEstimate:
        """GPU statevector estimate."""
        mem_bytes = self.estimator.statevector_bytes(n_qubits)
        mem_gb = mem_bytes / (1024 ** 3)

        # GPU kernel launch overhead + computation
        # ~1μs per gate on GPU for small circuits
        gates_per_layer = n_qubits
        total_gates = gates_per_layer * depth
        time_s = total_gates * 1e-6  # 1μs per gate

        # GPU memory available
        vram_ok = mem_gb < self.hardware.gpu_available_vram_gb * 0.8

        return SimulationEstimate(
            backend=BackendType.GPU_STATEVECTOR,
            memory_required_gb=mem_gb,
            time_estimate_s=max(time_s, 0.001),
            fits_in_memory=vram_ok,
            max_qubits_supported=int(math.log2(
                self.hardware.gpu_available_vram_gb * 0.8 * (1024**3) / 16
            )),
        )

    def _estimate_cpu_statevector(self, n_qubits: int, depth: int) -> SimulationEstimate:
        """CPU statevector estimate."""
        mem_bytes = self.estimator.statevector_bytes(n_qubits)
        mem_gb = mem_bytes / (1024 ** 3)

        # CPU simulation: ~100ns per gate (NumPy)
        gates_per_layer = n_qubits
        total_gates = gates_per_layer * depth
        time_s = total_gates * 100e-9

        # Bonus for SIMD
        if self.hardware.has_avx512:
            time_s *= 0.5
        elif self.hardware.has_avx2:
            time_s *= 0.7

        ram_ok = mem_gb < self.hardware.available_ram_gb * 0.8

        return SimulationEstimate(
            backend=BackendType.CPU_STATEVECTOR,
            memory_required_gb=mem_gb,
            time_estimate_s=max(time_s, 0.001),
            fits_in_memory=ram_ok,
            max_qubits_supported=int(math.log2(
                self.hardware.available_ram_gb * 0.8 * (1024**3) / 16
            )),
        )

    def _estimate_mps(self, n_qubits: int, depth: int,
                       entanglement: str) -> SimulationEstimate:
        """MPS estimate."""
        bond = self.estimator.estimate_mps_bond_dimension(n_qubits, depth, entanglement)
        mem_bytes = self.estimator.mps_bytes(n_qubits, bond)
        mem_gb = mem_bytes / (1024 ** 3)

        # MPS: O(n × bond² × depth) time
        time_s = n_qubits * bond * bond * depth * 1e-9

        # MPS can always fit (bond dims auto-scale)
        max_qubits = int(self.hardware.available_ram_gb * (1024**3) /
                         (bond * bond * 2 * 16))

        return SimulationEstimate(
            backend=BackendType.MPS,
            memory_required_gb=mem_gb,
            time_estimate_s=max(time_s, 0.001),
            fits_in_memory=mem_gb < self.hardware.available_ram_gb * 0.8,
            max_qubits_supported=max(max_qubits, n_qubits),
            auto_params={"bond_dimension": bond, "cutoff": 1e-10}
        )

    def _estimate_monte_carlo(self, n_qubits: int, depth: int) -> SimulationEstimate:
        """Monte Carlo estimate."""
        num_traj = 100  # Default
        mem_bytes = self.estimator.monte_carlo_bytes(n_qubits, num_traj)
        mem_gb = mem_bytes / (1024 ** 3)

        # Each trajectory: statevector cost × depth
        time_per_traj = depth * n_qubits * 100e-9
        total_time = time_per_traj * num_traj

        ram_ok = mem_gb < self.hardware.available_ram_gb * 0.8

        return SimulationEstimate(
            backend=BackendType.MONTE_CARLO,
            memory_required_gb=mem_gb,
            time_estimate_s=max(total_time, 0.001),
            fits_in_memory=ram_ok,
            max_qubits_supported=int(math.log2(
                self.hardware.available_ram_gb * 0.8 * (1024**3) / (16 * num_traj)
            )),
            auto_params={"num_trajectories": num_traj}
        )

    def _estimate_density_matrix(self, n_qubits: int, depth: int) -> SimulationEstimate:
        """Density matrix estimate."""
        mem_bytes = self.estimator.density_matrix_bytes(n_qubits)
        mem_gb = mem_bytes / (1024 ** 3)

        # Density matrix: O(4^n) memory, O(4^n × n) time
        dim = 2 ** n_qubits
        time_s = dim * dim * n_qubits * depth * 1e-9

        ram_ok = mem_gb < self.hardware.available_ram_gb * 0.8

        return SimulationEstimate(
            backend=BackendType.DENSITY_MATRIX,
            memory_required_gb=mem_gb,
            time_estimate_s=max(time_s, 0.001),
            fits_in_memory=ram_ok,
            max_qubits_supported=int(math.log2(
                math.sqrt(self.hardware.available_ram_gb * 0.8 * (1024**3) / 16)
            )),
        )


class AutoScalingSimulator:
    """
    High-level simulator that automatically picks the best backend
    and scales operations based on available hardware.

    Usage:
        from abirqu.auto_scale import AutoScalingSimulator

        sim = AutoScalingSimulator()
        result = sim.run(circuit, shots=1024)

        # Or with explicit options:
        result = sim.run(circuit, shots=1024, prefer_mps=True)
    """

    def __init__(self, hardware: Optional[HardwareInfo] = None):
        self.hardware = hardware or HardwareDetector().detect()
        self.router = SmartBackendRouter(self.hardware)

    def get_hardware_info(self) -> HardwareInfo:
        """Return detected hardware info."""
        return self.hardware

    def get_recommendation(self, n_qubits: int, depth: int = 1,
                            entanglement: str = "medium",
                            circuit=None) -> Dict[str, Any]:
        """
        Get backend recommendation without executing.

        Returns a human-readable recommendation with all estimates.
        """
        est = self.router.select_backend(n_qubits, depth, entanglement)

        return {
            "recommended_backend": est.backend.value,
            "memory_required_gb": round(est.memory_required_gb, 3),
            "estimated_time_s": round(est.time_estimate_s, 4),
            "max_qubits": est.max_qubits_supported,
            "auto_params": est.auto_params,
            "hardware": {
                "cpu_cores": self.hardware.cpu_cores,
                "ram_gb": round(self.hardware.ram_gb, 1),
                "available_ram_gb": round(self.hardware.available_ram_gb, 1),
                "gpu": self.hardware.gpu_name if self.hardware.gpu_available else "None",
                "gpu_vram_gb": round(self.hardware.gpu_vram_gb, 1),
                "simd": f"AVX-512" if self.hardware.has_avx512 else
                         f"AVX2" if self.hardware.has_avx2 else
                         f"NEON" if self.hardware.has_neon else "SSE",
            },
        }

    def run(self, circuit, shots: int = 1024,
            entanglement: str = "medium",
            prefer_gpu: Optional[bool] = None,
            prefer_mps: Optional[bool] = None,
            observables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute circuit on the best available backend.

        Parameters
        ----------
        circuit : Circuit
            Quantum circuit to execute
        shots : int
            Number of measurement shots
        entanglement : str
            Expected entanglement level
        prefer_gpu : bool, optional
            Force GPU preference
        prefer_mps : bool, optional
            Force MPS preference
        observables : dict, optional
            Observables to measure
        """
        from abirqu.circuit import Circuit

        n_qubits = circuit.num_qubits
        depth = len(circuit.gates)

        # Select backend
        est = self.router.select_backend(
            n_qubits, depth, entanglement,
            prefer_gpu=prefer_gpu,
            circuit=circuit
        )

        if prefer_mps:
            est = self.router._estimate_mps(n_qubits, depth, entanglement)
            est.fits_in_memory = True

        # Execute on selected backend
        start_time = __import__('time').time()

        if est.backend == BackendType.MPS:
            result = self._run_mps(circuit, shots, est.auto_params)
        elif est.backend == BackendType.GPU_STATEVECTOR:
            result = self._run_gpu(circuit, shots)
        elif est.backend == BackendType.CPU_STATEVECTOR:
            result = self._run_cpu(circuit, shots)
        elif est.backend == BackendType.CLIFFORD:
            result = self._run_clifford(circuit, shots)
        elif est.backend == BackendType.MONTE_CARLO:
            result = self._run_monte_carlo(circuit, shots, est.auto_params, observables)
        elif est.backend == BackendType.DENSITY_MATRIX:
            result = self._run_density(circuit, shots)
        else:
            result = self._run_mps(circuit, shots, est.auto_params)

        elapsed = __import__('time').time() - start_time

        result['backend_used'] = est.backend.value
        result['execution_time_s'] = round(elapsed, 4)
        result['memory_estimate_gb'] = round(est.memory_required_gb, 3)
        result['auto_scaled'] = True

        return result

    def _run_mps(self, circuit, shots, params):
        """Execute on MPS backend."""
        from abirqu.simulation.mps import MPSSimulator
        bond = params.get("bond_dimension", 32)
        sim = MPSSimulator(n_qubits=circuit.num_qubits, max_bond=bond)
        return sim.run_circuit(circuit, shots=shots)

    def _run_gpu(self, circuit, shots):
        """Execute on GPU statevector backend."""
        from abirqu.simulation.gpu_sim import GPUSimulator
        sim = GPUSimulator(use_gpu=True)
        return sim.run_circuit(circuit, shots=shots)

    def _run_cpu(self, circuit, shots):
        """Execute on CPU statevector backend."""
        from abirqu.simulation.gpu_sim import GPUSimulator
        sim = GPUSimulator(use_gpu=False)
        return sim.run_circuit(circuit, shots=shots)

    def _run_clifford(self, circuit, shots):
        """Execute on Clifford simulator (or fallback to Monte Carlo for non-Clifford)."""
        from abirqu.simulation.clifford import CliffordSimulator, is_clifford_only
        if is_clifford_only(circuit):
            sim = CliffordSimulator(n_qubits=circuit.num_qubits)
            return sim.run_circuit(circuit, shots=shots)
        else:
            # Non-Clifford gates: fall back to Monte Carlo
            from abirqu.simulation.monte_carlo import MonteCarloWavefunctionSimulator
            sim = MonteCarloWavefunctionSimulator(
                num_qubits=circuit.num_qubits, num_trajectories=min(shots, 50)
            )
            result = sim.run(circuit)
            return {"counts": result.counts}

    def _run_monte_carlo(self, circuit, shots, params, observables=None):
        """Execute on Monte Carlo backend."""
        from abirqu.simulation.monte_carlo import MonteCarloWavefunctionSimulator
        n_traj = params.get("num_trajectories", 100)
        sim = MonteCarloWavefunctionSimulator(
            num_qubits=circuit.num_qubits,
            num_trajectories=n_traj
        )
        result = sim.run(circuit, observables=observables)
        return {
            "counts": result.counts,
            "probabilities": result.probabilities,
        }

    def _run_density(self, circuit, shots):
        """Execute on density matrix backend."""
        from abirqu.simulation.density_sim import DensityMatrixSimulator
        sim = DensityMatrixSimulator(n_qubits=circuit.num_qubits)
        sim.run_circuit(circuit)
        probs = sim.get_probabilities()
        # Sample from probabilities
        n_qubits = circuit.num_qubits
        counts = {}
        for _ in range(shots):
            r = np.random.random()
            cumulative = 0
            for i, p in enumerate(probs):
                cumulative += p
                if r < cumulative:
                    bitstring = format(i, f'0{n_qubits}b')
                    counts[bitstring] = counts.get(bitstring, 0) + 1
                    break
        return {"counts": counts}

    def profile_hardware(self) -> Dict[str, Any]:
        """
        Profile hardware and return a comprehensive report.
        """
        info = self.hardware

        # Estimate max capabilities
        max_sv_qubits = int(math.log2(
            info.available_ram_gb * 0.8 * (1024**3) / 16
        )) if info.available_ram_gb > 0 else 0

        max_mps_qubits = int(
            info.available_ram_gb * 0.8 * (1024**3) / (32 * 32 * 2 * 16)
        ) if info.available_ram_gb > 0 else 0

        return {
            "cpu": {
                "cores": info.cpu_cores,
                "threads": info.cpu_threads,
                "freq_ghz": info.cpu_freq_ghz,
                "arch": info.cpu_arch,
                "vendor": info.cpu_vendor,
                "simd": "AVX-512" if info.has_avx512 else
                        "AVX2" if info.has_avx2 else
                        "NEON" if info.has_neon else "None",
            },
            "memory": {
                "ram_gb": round(info.ram_gb, 1),
                "available_gb": round(info.available_ram_gb, 1),
            },
            "gpu": {
                "available": info.gpu_available,
                "name": info.gpu_name,
                "vram_gb": round(info.gpu_vram_gb, 1),
                "available_vram_gb": round(info.gpu_available_vram_gb, 1),
                "compute": info.gpu_compute_capability,
            },
            "capabilities": {
                "max_statevector_qubits": max_sv_qubits,
                "max_mps_qubits": max_mps_qubits,
                "max_density_matrix_qubits": min(max_sv_qubits // 2, 16),
                "gpu_accelerated": info.gpu_available,
            },
            "platform": {
                "system": platform.system(),
                "machine": platform.machine(),
                "python": platform.python_version(),
                "apple_silicon": info.is_apple_silicon,
            },
        }
