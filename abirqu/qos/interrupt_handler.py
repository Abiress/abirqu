"""
Task 18.3 — Quantum Interrupt Handler.

Build mid-circuit error detection and recovery.
Implement hardware failure handling, graceful degradation,
emergency circuit cancellation and cleanup.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import traceback


class InterruptType(Enum):
    """Types of interrupts."""
    HARDWARE_FAILURE = "hardware_failure"
    QUBIT_DECOHERENCE = "qubit_decoherence"
    GATE_ERROR = "gate_error"
    READOUT_ERROR = "readout_error"
    TIME_OUT = "timeout"
    USER_CANCEL = "user_cancel"
    RESOURCE_REVOKED = "resource_revoked"


class InterruptSeverity(Enum):
    """Severity levels for interrupts."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class QuantumInterrupt:
    """Representation of a quantum interrupt."""
    interrupt_id: str
    type: InterruptType
    severity: InterruptSeverity
    job_id: str
    qubit_id: Optional[int] = None
    timestamp: float = field(default_factory=time.time)
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'interrupt_id': self.interrupt_id,
            'type': self.type.value,
            'severity': self.severity.value,
            'job_id': self.job_id,
            'qubit_id': self.qubit_id,
            'timestamp': self.timestamp,
            'message': self.message
        }


@dataclass
class InterruptResult:
    """Result of interrupt handling."""
    interrupt_id: str
    action_taken: str  # 'rerouted', 'degraded', 'cancelled', 'ignored'
    success: bool
    recovery_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'interrupt_id': self.interrupt_id,
            'action_taken': self.action_taken,
            'success': self.success,
            'recovery_time': self.recovery_time
        }


class ErrorDetector:
    """Mid-circuit error detection."""
    
    def __init__(self):
        self.error_threshold: Dict[str, float] = {
            'gate_error': 0.01,
            'readout_error': 0.05,
            'decoherence_rate': 0.001
        }
        self.error_history: List[Dict] = []
    
    def detect_gate_error(self, gate: str, qubit: int,
                         expected_fidelity: float,
                         actual_result: Optional[Any] = None) -> Optional[QuantumInterrupt]:
        """Detect gate execution errors."""
        if expected_fidelity < 1.0 - self.error_threshold['gate_error']:
            interrupt = QuantumInterrupt(
                interrupt_id=f"gate_err_{int(time.time())}",
                type=InterruptType.GATE_ERROR,
                severity=InterruptSeverity.MEDIUM,
                job_id="current",
                qubit_id=qubit,
                message=f"Gate {gate} on qubit {qubit} has low fidelity: {expected_fidelity}"
            )
            self.error_history.append({
                'type': 'gate_error',
                'gate': gate,
                'qubit': qubit,
                'fidelity': expected_fidelity
            })
            return interrupt
        return None
    
    def detect_decoherence(self, qubit: int,
                           coherence_time: float,
                           elapsed_time: float) -> Optional[QuantumInterrupt]:
        """Detect qubit decoherence."""
        if elapsed_time > coherence_time * 0.8:  # 80% of coherence time.
            interrupt = QuantumInterrupt(
                interrupt_id=f"decoh_{int(time.time())}",
                type=InterruptType.QUBIT_DECOHERENCE,
                severity=InterruptSeverity.HIGH if elapsed_time > coherence_time else InterruptSeverity.MEDIUM,
                job_id="current",
                qubit_id=qubit,
                message=f"Qubit {qubit} approaching decoherence limit"
            )
            self.error_history.append({
                'type': 'decoherence',
                'qubit': qubit,
                'elapsed': elapsed_time,
                'coherence': coherence_time
            })
            return interrupt
        return None
    
    def detect_readout_error(self, qubit: int,
                             measured_value: int,
                             expected_distribution: List[float]) -> Optional[QuantumInterrupt]:
        """Detect readout errors."""
        # Simplified: check if measurement is too far from expected.
        if measured_value not in [0, 1]:
            interrupt = QuantumInterrupt(
                interrupt_id=f"readout_{int(time.time())}",
                type=InterruptType.READOUT_ERROR,
                severity=InterruptSeverity.LOW,
                job_id="current",
                qubit_id=qubit,
                message=f"Readout error on qubit {qubit}"
            )
            return interrupt
        return None
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        stats = {}
        for error in self.error_history:
            error_type = error['type']
            stats[error_type] = stats.get(error_type, 0) + 1
        return stats


class RecoveryStrategy:
    """Strategies for recovering from interrupts."""
    
    def __init__(self):
        self.strategies: Dict[InterruptType, Callable] = {}
        self._register_strategies()
    
    def _register_strategies(self):
        """Register recovery strategies."""
        self.strategies[InterruptType.GATE_ERROR] = self._recover_gate_error
        self.strategies[InterruptType.QUBIT_DECOHERENCE] = self._recover_decoherence
        self.strategies[InterruptType.HARDWARE_FAILURE] = self._recover_hardware_failure
        self.strategies[InterruptType.READOUT_ERROR] = self._recover_readout_error
        self.strategies[InterruptType.TIME_OUT] = self._recover_timeout
        self.strategies[InterruptType.USER_CANCEL] = self._recover_user_cancel
    
    def recover(self, interrupt: QuantumInterrupt,
                resource_manager: Any = None,
                scheduler: Any = None) -> InterruptResult:
        """Apply recovery strategy."""
        if interrupt.type in self.strategies:
            return self.strategies[interrupt.type](interrupt, resource_manager, scheduler)
        
        # Default: ignore.
        return InterruptResult(
            interrupt_id=interrupt.interrupt_id,
            action_taken="ignored",
            success=True,
            metadata={'reason': 'no strategy registered'}
        )
    
    def _recover_gate_error(self, interrupt: QuantumInterrupt,
                           resource_manager: Any = None,
                           scheduler: Any = None) -> InterruptResult:
        """Recover from gate error."""
        # Try to reroute to different qubit.
        if resource_manager and interrupt.qubit_id is not None:
            # Simplified: mark for reroute.
            return InterruptResult(
                interrupt_id=interrupt.interrupt_id,
                action_taken="rerouted",
                success=True,
                recovery_time=0.1,
                metadata={'original_qubit': interrupt.qubit_id}
            )
        return InterruptResult(
            interrupt_id=interrupt.interrupt_id,
            action_taken="degraded",
            success=True,
            recovery_time=0.05,
            metadata={'action': 'continued with lower fidelity'}
        )
    
    def _recover_decoherence(self, interrupt: QuantumInterrupt,
                            resource_manager: Any = None,
                            scheduler: Any = None) -> InterruptResult:
        """Recover from decoherence."""
        return InterruptResult(
            interrupt_id=interrupt.interrupt_id,
            action_taken="degraded",
            success=True,
            recovery_time=0.2,
            metadata={'action': 'reduced circuit fidelity allowed'}
        )
    
    def _recover_hardware_failure(self, interrupt: QuantumInterrupt,
                                  resource_manager: Any = None,
                                  scheduler: Any = None) -> InterruptResult:
        """Recover from hardware failure."""
        if scheduler:
            # Cancel the job.
            scheduler.cancel_job(interrupt.job_id)
            return InterruptResult(
                interrupt_id=interrupt.interrupt_id,
                action_taken="cancelled",
                success=True,
                recovery_time=0.5,
                metadata={'reason': 'hardware failure, job cancelled'}
            )
        return InterruptResult(
            interrupt_id=interrupt.interrupt_id,
            action_taken="ignored",
            success=False,
            metadata={'reason': 'no scheduler available'}
        )
    
    def _recover_readout_error(self, interrupt: QuantumInterrupt,
                              resource_manager: Any = None,
                              scheduler: Any = None) -> InterruptResult:
        """Recover from readout error."""
        return InterruptResult(
            interrupt_id=interrupt.interrupt_id,
            action_taken="degraded",
            success=True,
            recovery_time=0.05,
            metadata={'action': 're-measure or estimate'}
        )
    
    def _recover_timeout(self, interrupt: QuantumInterrupt,
                         resource_manager: Any = None,
                         scheduler: Any = None) -> InterruptResult:
        """Recover from timeout."""
        if scheduler:
            scheduler.cancel_job(interrupt.job_id)
        return InterruptResult(
            interrupt_id=interrupt.interrupt_id,
            action_taken="cancelled",
            success=True,
            metadata={'reason': 'job timed out'}
        )
    
    def _recover_user_cancel(self, interrupt: QuantumInterrupt,
                             resource_manager: Any = None,
                             scheduler: Any = None) -> InterruptResult:
        """Handle user cancellation."""
        if scheduler:
            scheduler.cancel_job(interrupt.job_id)
        return InterruptResult(
            interrupt_id=interrupt.interrupt_id,
            action_taken="cancelled",
            success=True,
            metadata={'reason': 'user requested cancellation'}
        )


class InterruptHandler:
    """Main interrupt handler."""
    
    def __init__(self):
        self.error_detector = ErrorDetector()
        self.recovery = RecoveryStrategy()
        self.interrupt_history: List[QuantumInterrupt] = []
        self.interrupt_counter = 0
        self.handlers: Dict[InterruptType, List[Callable]] = {}
        
        # Register default handlers.
        for interrupt_type in InterruptType:
            self.handlers[interrupt_type] = []
    
    def handle(self, interrupt: QuantumInterrupt,
              resource_manager: Any = None,
              scheduler: Any = None) -> InterruptResult:
        """Handle an interrupt."""
        self.interrupt_history.append(interrupt)
        
        # Call custom handlers first.
        for handler in self.handlers.get(interrupt.type, []):
            try:
                handler(interrupt)
            except Exception as e:
                print(f"Error in custom handler: {e}")
        
        # Apply recovery strategy.
        result = self.recovery.recover(interrupt, resource_manager, scheduler)
        
        return result
    
    def raise_interrupt(self, type: InterruptType,
                       job_id: str,
                       qubit_id: Optional[int] = None,
                       severity: Optional[InterruptSeverity] = None,
                       message: str = "") -> InterruptResult:
        """Raise a new interrupt."""
        self.interrupt_counter += 1
        
        if severity is None:
            # Default severity based on type.
            if type in (InterruptType.HARDWARE_FAILURE, InterruptType.TIME_OUT):
                severity = InterruptSeverity.CRITICAL
            elif type in (InterruptType.QUBIT_DECOHERENCE,):
                severity = InterruptSeverity.HIGH
            else:
                severity = InterruptSeverity.MEDIUM
        
        interrupt = QuantumInterrupt(
            interrupt_id=f"int_{self.interrupt_counter}",
            type=type,
            severity=severity,
            job_id=job_id,
            qubit_id=qubit_id,
            message=message
        )
        
        return self.handle(interrupt)
    
    def register_handler(self, type: InterruptType, handler: Callable):
        """Register a custom interrupt handler."""
        self.handlers[type].append(handler)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get interrupt statistics."""
        stats = {
            'total_interrupts': len(self.interrupt_history),
            'by_type': {},
            'by_severity': {}
        }
        
        for interrupt in self.interrupt_history:
            # By type.
            type_name = interrupt.type.value
            stats['by_type'][type_name] = stats['by_type'].get(type_name, 0) + 1
            
            # By severity.
            sev_name = interrupt.severity.value
            stats['by_severity'][sev_name] = stats['by_severity'].get(sev_name, 0) + 1
        
        return stats
    
    def cleanup_job(self, job_id: str):
        """Clean up resources for a job."""
        # Remove any pending interrupts for this job.
        self.interrupt_history = [
            i for i in self.interrupt_history 
            if i.job_id != job_id
        ]
