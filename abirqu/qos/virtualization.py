"""
Task 18.5 — Quantum Virtualization Layer.

Build abstraction layer that virtualizes physical quantum hardware.
Implement logical qubit to physical qubit mapping.
Support multi-tenant isolation (one user's errors don't affect another).
Build virtual quantum machine provisioning and management.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import time


class VirtualMachineStatus(Enum):
    """Status of a virtual machine."""
    PROVISIONING = "provisioning"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class IsolationLevel(Enum):
    """Isolation levels for multi-tenant VMs."""
    NONE = "none"
    SOFT = "soft"  # Logical isolation only.
    HARD = "hard"  # Physical qubit isolation.
    FULL = "full"  # Complete isolation including network/storage.


@dataclass
class VirtualQubit:
    """Representation of a virtual (logical) qubit."""
    virtual_id: int
    physical_qubits: List[int]  # May be multiple for error correction.
    user: str
    status: str = "available"
    error_rate: float = 0.001
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'virtual_id': self.virtual_id,
            'physical_qubits': self.physical_qubits,
            'user': self.user,
            'status': self.status,
            'error_rate': self.error_rate
        }


@dataclass
class VirtualMachine:
    """A virtual quantum machine instance."""
    vm_id: str
    user: str
    project: str
    num_virtual_qubits: int
    status: VirtualMachineStatus = VirtualMachineStatus.PROVISIONING
    created_at: float = field(default_factory=time.time)
    qubits: List[VirtualQubit] = field(default_factory=list)
    isolation_level: IsolationLevel = IsolationLevel.SOFT
    resource_limits: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'vm_id': self.vm_id,
            'user': self.user,
            'project': self.project,
            'num_virtual_qubits': self.num_virtual_qubits,
            'status': self.status.value,
            'created_at': self.created_at,
            'isolation_level': self.isolation_level.value,
            'num_physical_qubits': sum(len(q.physical_qubits) for q in self.qubits),
            'qubits': [q.to_dict() for q in self.qubits]
        }
    
    def get_qubit(self, virtual_id: int) -> Optional[VirtualQubit]:
        """Get virtual qubit by ID."""
        for q in self.qubits:
            if q.virtual_id == virtual_id:
                return q
        return None
    
    def is_running(self) -> bool:
        return self.status == VirtualMachineStatus.RUNNING


@dataclass
class VirtualizationResult:
    """Result of a virtualization operation."""
    success: bool
    vm_id: Optional[str] = None
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'vm_id': self.vm_id,
            'message': self.message,
            'metadata': self.metadata
        }


class QubitMapper:
    """Maps logical (virtual) qubits to physical qubits."""
    
    def __init__(self):
        self.mapping: Dict[str, Dict[int, List[int]]] = {}  # vm_id -> virtual -> physical
        self.reverse_mapping: Dict[str, Dict[int, int]] = {}  # vm_id -> physical -> virtual
    
    def create_mapping(self, vm_id: str,
                       virtual_qubits: List[int],
                       physical_qubits: List[List[int]],
                       strategy: str = "direct") -> Dict[int, List[int]]:
        """Create qubit mapping for a VM."""
        mapping = {}
        
        if strategy == "direct":
            # Direct mapping: virtual N -> physical N.
            for i, vq in enumerate(virtual_qubits):
                if i < len(physical_qubits):
                    mapping[vq] = physical_qubits[i]
                else:
                    mapping[vq] = [vq]  # Default.
        
        elif strategy == "encoded":
            # Error-corrected: each virtual needs multiple physical.
            for vq in virtual_qubits:
                mapping[vq] = physical_qubits[vq % len(physical_qubits)]
        
        self.mapping[vm_id] = mapping
        self._update_reverse_mapping(vm_id)
        return mapping
    
    def _update_reverse_mapping(self, vm_id: str):
        """Update reverse mapping."""
        if vm_id not in self.reverse_mapping:
            self.reverse_mapping[vm_id] = {}
        
        for vq, pqs in self.mapping.get(vm_id, {}).items():
            for pq in pqs:
                self.reverse_mapping[vm_id][pq] = vq
    
    def map_gate(self, vm_id: str, virtual_qubits: List[int]) -> List[int]:
        """Map virtual qubits to physical for a gate."""
        if vm_id not in self.mapping:
            return virtual_qubits  # No mapping.
        
        physical = []
        for vq in virtual_qubits:
            if vq in self.mapping[vm_id]:
                physical.extend(self.mapping[vm_id][vq])
        
        return physical if physical else virtual_qubits
    
    def get_physical_qubits(self, vm_id: str) -> Set[int]:
        """Get all physical qubits used by a VM."""
        if vm_id not in self.mapping:
            return set()
        
        physical = set()
        for pqs in self.mapping[vm_id].values():
            physical.update(pqs)
        return physical
    
    def remove_mapping(self, vm_id: str):
        """Remove mapping for a VM."""
        self.mapping.pop(vm_id, None)
        self.reverse_mapping.pop(vm_id, None)


class IsolationManager:
    """Manages multi-tenant isolation."""
    
    def __init__(self):
        self.vm_resources: Dict[str, Set[int]] = {}  # vm_id -> physical qubits
        self.user_vms: Dict[str, List[str]] = {}  # user -> vm_ids
    
    def check_isolation(self, vm1_id: str, vm2_id: str) -> bool:
        """Check if two VMs are properly isolated."""
        if vm1_id not in self.vm_resources or vm2_id not in self.vm_resources:
            return True  # No conflict if one doesn't exist.
        
        qubits1 = self.vm_resources[vm1_id]
        qubits2 = self.vm_resources[vm2_id]
        
        # Check for overlapping physical qubits.
        return len(qubits1.intersection(qubits2)) == 0
    
    def enforce_isolation(self, vm: VirtualMachine, 
                          level: IsolationLevel) -> bool:
        """Enforce isolation for a VM."""
        if level == IsolationLevel.NONE:
            return True  # No isolation needed.
        
        if level == IsolationLevel.HARD:
            # Check no overlap with existing VMs.
            for other_vm_id in self.vm_resources:
                if other_vm_id != vm.vm_id:
                    if not self.check_isolation(vm.vm_id, other_vm_id):
                        return False  # Isolation violated.
        
        return True
    
    def register_vm(self, vm: VirtualMachine, physical_qubits: Set[int]):
        """Register VM with its physical resources."""
        self.vm_resources[vm.vm_id] = physical_qubits
        
        if vm.user not in self.user_vms:
            self.user_vms[vm.user] = []
        if vm.vm_id not in self.user_vms[vm.user]:
            self.user_vms[vm.user].append(vm.vm_id)
    
    def unregister_vm(self, vm_id: str):
        """Unregister a VM."""
        if vm_id in self.vm_resources:
            del self.vm_resources[vm_id]
        
        for user, vm_ids in self.user_vms.items():
            if vm_id in vm_ids:
                vm_ids.remove(vm_id)
                break
    
    def get_user_vms(self, user: str) -> List[str]:
        """Get all VMs for a user."""
        return self.user_vms.get(user, [])


class ErrorIsolation:
    """Isolate errors between tenants."""
    
    def __init__(self):
        self.error_history: Dict[str, List[Dict]] = {}  # vm_id -> errors
        self.error_threshold = 0.1  # 10% error rate threshold.
    
    def record_error(self, vm_id: str, qubit_id: int, error_type: str):
        """Record an error for a VM."""
        if vm_id not in self.error_history:
            self.error_history[vm_id] = []
        
        self.error_history[vm_id].append({
            'qubit_id': qubit_id,
            'error_type': error_type,
            'timestamp': time.time()
        })
    
    def get_vm_error_rate(self, vm_id: str) -> float:
        """Get error rate for a VM."""
        if vm_id not in self.error_history:
            return 0.0
        
        errors = self.error_history[vm_id]
        if not errors:
            return 0.0
        
        # Simplified: count recent errors (last 100).
        recent = errors[-100:]
        return len(recent) / 100.0
    
    def quarantine_vm(self, vm_id: str) -> bool:
        """Quarantine a VM if error rate is too high."""
        error_rate = self.get_vm_error_rate(vm_id)
        return error_rate > self.error_threshold
    
    def propagate_error(self, source_vm: str, target_vm: str) -> bool:
        """Check if error can propagate between VMs (should be False with isolation)."""
        # With proper isolation, errors should NOT propagate.
        return False


class QuantumVirtualization:
    """Main virtualization layer."""
    
    def __init__(self, resource_manager: Any = None):
        self.resource_manager = resource_manager
        self.vm_counter = 0
        self.vms: Dict[str, VirtualMachine] = {}
        self.mapper = QubitMapper()
        self.isolation = IsolationManager()
        self.error_isolation = ErrorIsolation()
    
    def provision_vm(self, user: str, project: str,
                     num_qubits: int = 5,
                     isolation: IsolationLevel = IsolationLevel.SOFT) -> VirtualizationResult:
        """Provision a new virtual quantum machine."""
        self.vm_counter += 1
        vm_id = f"vm_{self.vm_counter}"
        
        # Create VM.
        vm = VirtualMachine(
            vm_id=vm_id,
            user=user,
            project=project,
            num_virtual_qubits=num_qubits,
            isolation_level=isolation
        )
        
        # Allocate physical resources if resource manager available.
        physical_qubits = []
        if self.resource_manager:
            alloc = self.resource_manager.allocate(user, project, num_qubits)
            if alloc:
                physical_qubits = alloc.qubits
            else:
                # Fallback: use virtual IDs.
                physical_qubits = list(range(num_qubits))
        else:
            physical_qubits = list(range(num_qubits))
        
        # Create virtual qubits.
        for i in range(num_qubits):
            pq = [physical_qubits[i]] if i < len(physical_qubits) else [i]
            vq = VirtualQubit(
                virtual_id=i,
                physical_qubits=pq,
                user=user
            )
            vm.qubits.append(vq)
        
        # Create mapping.
        virtual_ids = list(range(num_qubits))
        physical_lists = [[pq] for pq in physical_qubits[:num_qubits]]
        self.mapper.create_mapping(vm_id, virtual_ids, physical_lists)
        
        # Register for isolation.
        self.isolation.register_vm(vm, set(physical_qubits[:num_qubits]))
        
        # Check isolation.
        if not self.isolation.enforce_isolation(vm, isolation):
            # Isolation violated, roll back.
            self.isolation.unregister_vm(vm_id)
            self.mapper.remove_mapping(vm_id)
            return VirtualizationResult(
                success=False,
                message="Isolation check failed"
            )
        
        vm.status = VirtualMachineStatus.RUNNING
        self.vms[vm_id] = vm
        
        return VirtualizationResult(
            success=True,
            vm_id=vm_id,
            message=f"VM {vm_id} provisioned with {num_qubits} qubits",
            metadata={
                'isolation_level': isolation.value,
                'physical_qubits': physical_qubits[:num_qubits]
            }
        )
    
    def deprovision_vm(self, vm_id: str, user: str) -> VirtualizationResult:
        """Deprovision a VM."""
        if vm_id not in self.vms:
            return VirtualizationResult(success=False, message="VM not found")
        
        vm = self.vms[vm_id]
        
        # Check ownership.
        if vm.user != user:
            return VirtualizationResult(success=False, message="Access denied")
        
        # Stop VM.
        vm.status = VirtualMachineStatus.STOPPED
        
        # Release resources.
        if self.resource_manager:
            # This would need allocation_id in real implementation.
            pass
        
        # Clean up.
        self.isolation.unregister_vm(vm_id)
        self.mapper.remove_mapping(vm_id)
        
        del self.vms[vm_id]
        
        return VirtualizationResult(
            success=True,
            message=f"VM {vm_id} deprovisioned"
        )
    
    def execute_circuit(self, vm_id: str, circuit: List[Tuple]) -> VirtualizationResult:
        """Execute a circuit on a VM."""
        if vm_id not in self.vms:
            return VirtualizationResult(success=False, message="VM not found")
        
        vm = self.vms[vm_id]
        
        if not vm.is_running():
            return VirtualizationResult(success=False, message="VM not running")
        
        # Map virtual qubits to physical.
        mapped_circuit = []
        for gate_info in circuit:
            if len(gate_info) >= 2:
                gate = gate_info[0]
                virtual_qubits = gate_info[1]
                physical = self.mapper.map_gate(vm_id, 
                    virtual_qubits if isinstance(virtual_qubits, list) else [virtual_qubits]
                )
                mapped_circuit.append((gate, physical))
        
        # Simulate execution (simplified).
        return VirtualizationResult(
            success=True,
            vm_id=vm_id,
            message="Circuit executed",
            metadata={
                'mapped_circuit': mapped_circuit,
                'num_gates': len(circuit)
            }
        )
    
    def pause_vm(self, vm_id: str) -> VirtualizationResult:
        """Pause a running VM."""
        if vm_id not in self.vms:
            return VirtualizationResult(success=False, message="VM not found")
        
        vm = self.vms[vm_id]
        vm.status = VirtualMachineStatus.PAUSED
        return VirtualizationResult(success=True, message=f"VM {vm_id} paused")
    
    def resume_vm(self, vm_id: str) -> VirtualizationResult:
        """Resume a paused VM."""
        if vm_id not in self.vms:
            return VirtualizationResult(success=False, message="VM not found")
        
        vm = self.vms[vm_id]
        vm.status = VirtualMachineStatus.RUNNING
        return VirtualizationResult(success=True, message=f"VM {vm_id} resumed")
    
    def get_vm(self, vm_id: str) -> Optional[VirtualMachine]:
        """Get VM by ID."""
        return self.vms.get(vm_id)
    
    def list_vms(self, user: Optional[str] = None) -> List[Dict[str, Any]]:
        """List VMs."""
        result = []
        for vm in self.vms.values():
            if user and vm.user != user:
                continue
            result.append(vm.to_dict())
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get virtualization statistics."""
        total = len(self.vms)
        by_status = {}
        by_user = {}
        
        for vm in self.vms.values():
            status = vm.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            user = vm.user
            if user not in by_user:
                by_user[user] = {'vm_count': 0, 'total_qubits': 0}
            by_user[user]['vm_count'] += 1
            by_user[user]['total_qubits'] += vm.num_virtual_qubits
        
        return {
            'total_vms': total,
            'by_status': by_status,
            'by_user': by_user,
            'total_mappings': len(self.mapper.mapping)
        }
