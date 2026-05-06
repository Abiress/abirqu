"""
Task 20.2 — Performance Profiling System.

Profile CPU, memory, and quantum-specific metrics.
Support profiling of circuit execution, compilation, and simulation.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import sys
import tracemalloc


class ProfilingMetric(Enum):
    """Metrics for performance profiling."""
    CPU_TIME = "cpu_time"
    WALL_TIME = "wall_time"
    MEMORY_USAGE = "memory_usage"
    PEAK_MEMORY = "peak_memory"
    GATE_LATENCY = "gate_latency"
    CIRCUIT_DEPTH = "circuit_depth"
    QUBIT_COUNT = "qubit_count"
    ERROR_RATE = "error_rate"


@dataclass
class ProfilingSession:
    """A profiling session."""
    session_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    metrics: Dict[ProfilingMetric, List[float]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'name': self.name,
            'duration': (self.end_time or time.time()) - self.start_time,
            'metrics': {k.value: v for k, v in self.metrics.items()},
            'metadata': self.metadata
        }
    
    def add_metric(self, metric: ProfilingMetric, value: float):
        """Add a metric measurement."""
        if metric not in self.metrics:
            self.metrics[metric] = []
        self.metrics[metric].append(value)
    
    def get_average(self, metric: ProfilingMetric) -> float:
        """Get average value for a metric."""
        if metric not in self.metrics or not self.metrics[metric]:
            return 0.0
        return sum(self.metrics[metric]) / len(self.metrics[metric])
    
    def get_peak(self, metric: ProfilingMetric) -> float:
        """Get peak value for a metric."""
        if metric not in self.metrics or not self.metrics[metric]:
            return 0.0
        return max(self.metrics[metric])


@dataclass
class ProfileReport:
    """Report generated from profiling session."""
    session_id: str
    summary: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'summary': self.summary,
            'recommendations': self.recommendations,
            'metadata': self.metadata
        }


class MemoryProfiler:
    """Memory profiling using tracemalloc."""
    
    def __init__(self):
        self.snapshots: List[Tuple[float, Any]] = []
        self.baseline = None
    
    def start(self):
        """Start memory profiling."""
        tracemalloc.start()
        self.baseline = tracemalloc.take_snapshot()
    
    def stop(self) -> Dict[str, Any]:
        """Stop and return memory stats."""
        if not tracemalloc.is_tracing():
            return {'error': 'Memory profiling not started'}
        
        current = tracemalloc.take_snapshot()
        
        # Calculate difference.
        if self.baseline:
            stats = current.compare_to(self.baseline, 'lineno')
            top = list(stats)[:10]
        else:
            top = list(current.statistics('lineno'))[:10]
        
        tracemalloc.stop()
        
        return {
            'peak_memory': current.traced_memory()[1],
            'current_memory': current.traced_memory()[0],
            'top_allocations': [
                {
                    'file': str(stat.traceback.format()[0]) if stat.traceback else 'unknown',
                    'size': stat.size,
                    'count': stat.count
                }
                for stat in top
            ]
        }
    
    def get_current_memory(self) -> int:
        """Get current memory usage."""
        if not tracemalloc.is_tracing():
            return 0
        snapshot = tracemalloc.take_snapshot()
        return snapshot.traced_memory()[0]


class CPUMonitor:
    """CPU monitoring (simplified)."""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.start_process_time: Optional[float] = None
    
    def start(self):
        """Start CPU monitoring."""
        self.start_time = time.time()
        self.start_process_time = time.process_time()
    
    def stop(self) -> Dict[str, float]:
        """Stop and return CPU stats."""
        if self.start_time is None:
            return {}
        
        wall_time = time.time() - self.start_time
        cpu_time = time.process_time() - (self.start_process_time or 0.0)
        
        return {
            'wall_time': wall_time,
            'cpu_time': cpu_time,
            'cpu_usage_percent': (cpu_time / max(wall_time, 0.001)) * 100
        }


class GateLatencyProfiler:
    """Profile quantum gate execution latency."""
    
    def __init__(self):
        self.gate_times: Dict[str, List[float]] = {}
        self.total_gates = 0
    
    def profile_gate(self, gate_name: str, execution_fn: Callable) -> Any:
        """Profile a single gate execution."""
        start = time.perf_counter()
        result = execution_fn()
        end = time.perf_counter()
        
        latency = end - start
        
        if gate_name not in self.gate_times:
            self.gate_times[gate_name] = []
        self.gate_times[gate_name].append(latency)
        self.total_gates += 1
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get gate latency statistics."""
        stats = {}
        for gate, times in self.gate_times.items():
            stats[gate] = {
                'avg_latency': sum(times) / len(times),
                'min_latency': min(times),
                'max_latency': max(times),
                'count': len(times)
            }
        return stats
    
    def get_total_time(self) -> float:
        """Get total time spent on gates."""
        total = 0.0
        for times in self.gate_times.values():
            total += sum(times)
        return total


class PerformanceProfiler:
    """Main performance profiler."""
    
    def __init__(self):
        self.sessions: Dict[str, ProfilingSession] = {}
        self.memory_profiler = MemoryProfiler()
        self.cpu_monitor = CPUMonitor()
        self.gate_profiler = GateLatencyProfiler()
        self.session_counter = 0
        self.active_session: Optional[ProfilingSession] = None
    
    def start_session(self, name: str,
                     metrics: List[ProfilingMetric] = None) -> str:
        """Start a new profiling session."""
        self.session_counter += 1
        session_id = f"profile_{self.session_counter}"
        
        session = ProfilingSession(
            session_id=session_id,
            name=name,
            start_time=time.time()
        )
        
        self.sessions[session_id] = session
        self.active_session = session
        
        # Start subprocess profilers.
        if metrics and ProfilingMetric.MEMORY_USAGE in metrics:
            self.memory_profiler.start()
        
        if metrics and ProfilingMetric.CPU_TIME in metrics:
            self.cpu_monitor.start()
        
        return session_id
    
    def stop_session(self) -> Optional[ProfileReport]:
        """Stop the active session and generate report."""
        if self.active_session is None:
            return None
        
        session = self.active_session
        session.end_time = time.time()
        
        # Collect metrics from subprocess profilers.
        if self.memory_profiler.baseline is not None:
            memory_stats = self.memory_profiler.stop()
            session.add_metric(
                ProfilingMetric.PEAK_MEMORY,
                memory_stats.get('peak_memory', 0)
            )
        
        cpu_stats = self.cpu_monitor.stop()
        if cpu_stats:
            session.add_metric(
                ProfilingMetric.WALL_TIME,
                cpu_stats.get('wall_time', 0.0)
            )
            session.add_metric(
                ProfilingMetric.CPU_TIME,
                cpu_stats.get('cpu_time', 0.0)
            )
        
        # Generate report.
        report = self.generate_report(session.session_id)
        
        self.active_session = None
        return report
    
    def profile_circuit_execution(self, circuit: List[Tuple],
                                  execution_fn: Callable) -> ProfileReport:
        """Profile circuit execution."""
        session_id = self.start_session(
            name="circuit_execution",
            metrics=[
                ProfilingMetric.WALL_TIME,
                ProfilingMetric.CPU_TIME,
                ProfilingMetric.MEMORY_USAGE,
                ProfilingMetric.GATE_LATENCY
            ]
        )
        
        # Execute and profile each gate.
        for gate_info in circuit:
            gate_name = gate_info[0] if len(gate_info) > 0 else 'unknown'
            self.gate_profiler.profile_gate(gate_name, execution_fn)
        
        # Add gate stats to session.
        gate_stats = self.gate_profiler.get_stats()
        for gate, stats in gate_stats.items():
            self.active_session.add_metric(
                ProfilingMetric.GATE_LATENCY,
                stats['avg_latency']
            )
        
        return self.stop_session()
    
    def profile_compilation(self, circuit: List[Tuple],
                            compile_fn: Callable) -> ProfileReport:
        """Profile circuit compilation."""
        session_id = self.start_session(
            name="compilation",
            metrics=[
                ProfilingMetric.WALL_TIME,
                ProfilingMetric.CPU_TIME,
                ProfilingMetric.MEMORY_USAGE
            ]
        )
        
        # Profile compilation.
        start_mem = self.memory_profiler.get_current_memory() if self.memory_profiler.baseline else 0
        
        result = compile_fn(circuit)
        
        end_mem = self.memory_profiler.get_current_memory() if self.memory_profiler.baseline else 0
        
        # Add memory delta.
        if start_mem and end_mem:
            self.active_session.add_metric(
                ProfilingMetric.MEMORY_USAGE,
                end_mem - start_mem
            )
        
        return self.stop_session()
    
    def generate_report(self, session_id: str) -> ProfileReport:
        """Generate a report from a session."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Build summary.
        summary = {
            'session_name': session.name,
            'duration': session.end_time - session.start_time if session.end_time else 0,
            'metrics_summary': {}
        }
        
        for metric, values in session.metrics.items():
            if values:
                summary['metrics_summary'][metric.value] = {
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
        
        # Generate recommendations.
        recommendations = self._generate_recommendations(session)
        
        return ProfileReport(
            session_id=session_id,
            summary=summary,
            recommendations=recommendations,
            metadata={'generated_at': time.time()}
        )
    
    def _generate_recommendations(self, session: ProfilingSession) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        
        # Check memory usage.
        if ProfilingMetric.PEAK_MEMORY in session.metrics:
            peak = session.get_peak(ProfilingMetric.PEAK_MEMORY)
            if peak > 100 * 1024 * 1024:  # > 100MB.
                recommendations.append(
                    "High memory usage detected. Consider optimizing data structures."
                )
        
        # Check gate latency.
        if ProfilingMetric.GATE_LATENCY in session.metrics:
            avg_latency = session.get_average(ProfilingMetric.GATE_LATENCY)
            if avg_latency > 0.01:  # > 10ms.
                recommendations.append(
                    "High gate latency detected. Consider circuit optimization."
                )
        
        if not recommendations:
            recommendations.append("Performance looks good!")
        
        return recommendations
    
    def get_session(self, session_id: str) -> Optional[ProfilingSession]:
        """Get a profiling session."""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all profiling sessions."""
        return [
            {
                'session_id': sid,
                'name': s.name,
                'duration': (s.end_time or time.time()) - s.start_time,
                'num_metrics': sum(len(m) for m in s.metrics.values())
            }
            for sid, s in self.sessions.items()
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get profiler statistics."""
        return {
            'total_sessions': len(self.sessions),
            'active_session': self.active_session.session_id if self.active_session else None,
            'total_gates_profiled': self.gate_profiler.total_gates,
            'gate_types_profiled': list(self.gate_profiler.gate_times.keys())
        }
