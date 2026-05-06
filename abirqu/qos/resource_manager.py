"""
Task 18.2 — Quantum Resource Manager.

Implement qubit allocation and deallocation across multiple users.
Build qubit topology management, dynamic resource reallocation,
resource reservation and backfilling.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import time


class ResourceStatus(Enum):
    """Status of a quantum resource."""
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    RESERVED = "reserved"
    BROKEN = "broken"
    MAINTENANCE = "maintenance"


class QubitType(Enum):
    """Types of qubits."""
    SUPERCONDUCTING = "superconducting"
    TRAPPED_ION = "trapped_ion"
    PHOTONIC = "photonic"
    TOPOLOGICAL = "topological"
    NEUTRAL_ATOM = "neutral_atom"


@dataclass
class QubitInfo:
    """Information about a physical qubit."""
    qubit_id: int
    type: QubitType
    status: ResourceStatus = ResourceStatus.AVAILABLE
    user: Optional[str] = None
    project: Optional[str] = None
    allocated_at: Optional[float] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def is_available(self) -> bool:
        return self.status == ResourceStatus.AVAILABLE
    
    def is_broken(self) -> bool:
        return self.status in (ResourceStatus.BROKEN, ResourceStatus.MAINTENANCE)


@dataclass
class QubitAllocation:
    """Result of qubit allocation."""
    allocation_id: str
    user: str
    project: str
    qubits: List[int]
    timestamp: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'allocation_id': self.allocation_id,
            'user': self.user,
            'project': self.project,
            'qubits': self.qubits,
            'num_qubits': len(self.qubits),
            'timestamp': self.timestamp,
            'expires_at': self.expires_at
        }


@dataclass
class ResourceReservation:
    """Resource reservation for future use."""
    reservation_id: str
    user: str
    project: str
    num_qubits: int
    start_time: float
    end_time: float
    qubits: List[int] = field(default_factory=list)
    status: str = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reservation_id': self.reservation_id,
            'user': self.user,
            'project': self.project,
            'num_qubits': self.num_qubits,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'qubits': self.qubits
        }


class TopologyManager:
    """Manages qubit connectivity topology."""
    
    def __init__(self, num_qubits: int = 20):
        self.num_qubits = num_qubits
        self.adjacency: Dict[int, Set[int]] = {}
        self._initialize_linear_topology()
    
    def _initialize_linear_topology(self):
        """Initialize a linear chain topology."""
        for i in range(self.num_qubits):
            self.adjacency[i] = set()
            if i > 0:
                self.adjacency[i].add(i-1)
                self.adjacency[i-1].add(i)
    
    def set_topology(self, edges: List[Tuple[int, int]]):
        """Set custom topology from edge list."""
        self.adjacency = {i: set() for i in range(self.num_qubits)}
        for u, v in edges:
            if u < self.num_qubits and v < self.num_qubits:
                self.adjacency[u].add(v)
                self.adjacency[v].add(u)
    
    def get_neighbors(self, qubit: int) -> Set[int]:
        """Get neighbors of a qubit."""
        return self.adjacency.get(qubit, set())
    
    def find_path(self, start: int, end: int) -> List[int]:
        """Find shortest path between qubits (BFS)."""
        if start == end:
            return [start]
        
        visited = {start}
        queue = [[start]]
        
        while queue:
            path = queue.pop(0)
            node = path[-1]
            
            for neighbor in self.adjacency.get(node, []):
                if neighbor not in visited:
                    new_path = path + [neighbor]
                    if neighbor == end:
                        return new_path
                    visited.add(neighbor)
                    queue.append(new_path)
        
        return []  # No path found
    
    def get_connectivity_map(self) -> Dict[int, List[int]]:
        """Get full connectivity map."""
        return {k: list(v) for k, v in self.adjacency.items()}


class QuantumResourceManager:
    """Main resource manager for quantum hardware."""
    
    def __init__(self, num_qubits: int = 20):
        self.num_qubits = num_qubits
        self.qubits: Dict[int, QubitInfo] = {}
        self.allocations: Dict[str, QubitAllocation] = {}
        self.reservations: Dict[str, ResourceReservation] = {}
        self.topology = TopologyManager(num_qubits)
        self.allocation_counter = 0
        
        # Initialize qubits.
        for i in range(num_qubits):
            self.qubits[i] = QubitInfo(
                qubit_id=i,
                type=QubitType.SUPERCONDUCTING
            )
    
    def allocate(self, user: str, project: str, 
                 num_qubits: int = 1,
                 preferred_qubits: Optional[List[int]] = None) -> Optional[QubitAllocation]:
        """Allocate qubits to a user/project."""
        available = [q for q in range(self.num_qubits) 
                     if self.qubits[q].is_available()]
        
        if len(available) < num_qubits:
            return None  # Not enough qubits.
        
        # Try preferred qubits first.
        if preferred_qubits:
            selected = [q for q in preferred_qubits 
                       if q in available][:num_qubits]
            remaining_needed = num_qubits - len(selected)
            if remaining_needed > 0:
                additional = [q for q in available if q not in selected][:remaining_needed]
                selected.extend(additional)
        else:
            # Pick qubits with best connectivity.
            selected = self._pick_connected_qubits(available, num_qubits)
        
        # Create allocation.
        self.allocation_counter += 1
        alloc_id = f"alloc_{self.allocation_counter}"
        
        allocation = QubitAllocation(
            allocation_id=alloc_id,
            user=user,
            project=project,
            qubits=selected
        )
        
        # Mark qubits as allocated.
        for q in selected:
            self.qubits[q].status = ResourceStatus.ALLOCATED
            self.qubits[q].user = user
            self.qubits[q].project = project
            self.qubits[q].allocated_at = time.time()
        
        self.allocations[alloc_id] = allocation
        return allocation
    
    def _pick_connected_qubits(self, available: List[int], num_qubits: int) -> List[int]:
        """Pick qubits that are well-connected to each other."""
        if num_qubits <= 1 or not available:
            return available[:num_qubits]
        
        # Start with first available qubit, then pick neighbors.
        selected = [available[0]]
        
        while len(selected) < num_qubits and len(selected) < len(available):
            # Find neighbor of selected qubits that's also available.
            candidates = set()
            for q in selected:
                candidates.update(self.topology.get_neighbors(q))
            
            candidates = candidates - set(selected)
            available_candidates = [q for q in candidates if q in available]
            
            if available_candidates:
                selected.append(available_candidates[0])
            else:
                # No connected qubits left, pick any available.
                for q in available:
                    if q not in selected:
                        selected.append(q)
                        break
        
        return selected[:num_qubits]
    
    def deallocate(self, allocation_id: str) -> bool:
        """Deallocate qubits."""
        if allocation_id not in self.allocations:
            return False
        
        allocation = self.allocations.pop(allocation_id)
        
        for q in allocation.qubits:
            if q in self.qubits:
                self.qubits[q].status = ResourceStatus.AVAILABLE
                self.qubits[q].user = None
                self.qubits[q].project = None
                self.qubits[q].allocated_at = None
        
        return True
    
    def reserve(self, user: str, project: str,
                num_qubits: int, duration: float) -> ResourceReservation:
        """Reserve qubits for future use."""
        self.allocation_counter += 1
        res_id = f"res_{self.allocation_counter}"
        
        start = time.time()
        end = start + duration
        
        reservation = ResourceReservation(
            reservation_id=res_id,
            user=user,
            project=project,
            num_qubits=num_qubits,
            start_time=start,
            end_time=end
        )
        
        self.reservations[res_id] = reservation
        return reservation
    
    def check_reservations(self):
        """Check and activate pending reservations (backfilling)."""
        current_time = time.time()
        
        for res in self.reservations.values():
            if res.status == "pending" and current_time >= res.start_time:
                # Try to allocate.
                allocation = self.allocate(res.user, res.project, res.num_qubits)
                if allocation:
                    res.qubits = allocation.qubits
                    res.status = "active"
    
    def handle_hardware_change(self, broken_qubits: List[int]):
        """Handle hardware status changes (e.g., qubits breaking)."""
        for q in broken_qubits:
            if q in self.qubits:
                self.qubits[q].status = ResourceStatus.BROKEN
                
                # Find and handle affected allocations.
                for alloc in self.allocations.values():
                    if q in alloc.qubits:
                        # Try to migrate to different qubits (simplified).
                        alloc.metadata['migrated'] = True
                        alloc.qubits.remove(q)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get resource usage statistics."""
        available = sum(1 for q in self.qubits.values() if q.is_available())
        allocated = sum(1 for q in self.qubits.values() 
                       if q.status == ResourceStatus.ALLOCATED)
        broken = sum(1 for q in self.qubits.values() if q.is_broken())
        
        return {
            'total': self.num_qubits,
            'available': available,
            'allocated': allocated,
            'broken': broken,
            'utilization': allocated / self.num_qubits if self.num_qubits > 0 else 0,
            'active_allocations': len(self.allocations),
            'pending_reservations': sum(1 for r in self.reservations.values() 
                                       if r.status == "pending")
        }
    
    def get_user_usage(self, user: str) -> Dict[str, Any]:
        """Get resource usage for a specific user."""
        user_qubits = [q for q in self.qubits.values() if q.user == user]
        
        return {
            'user': user,
            'allocated_qubits': len(user_qubits),
            'qubit_ids': [q.qubit_id for q in user_qubits],
            'allocations': [a.allocation_id for a in self.allocations.values() 
                           if a.user == user]
        }
