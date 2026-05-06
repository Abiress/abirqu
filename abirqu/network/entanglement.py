"""
Task 13.4 — Entanglement Management.

Entanglement resource manager, purification protocols, monitoring.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import time


class PairStatus(Enum):
    """Status of entanglement pair."""
    AVAILABLE = "available"
    IN_USE = "in_use"
    CONSUMED = "consumed"
    PURIFIED = "purified"
    LOST = "lost"


@dataclass
class EntanglementPair:
    """An entangled pair between two nodes."""
    pair_id: str
    node_a: str
    node_b: str
    fidelity: float  # 0-1
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 3600)
    status: PairStatus = PairStatus.AVAILABLE
    purification_level: int = 0
    
    def is_valid(self) -> bool:
        """Check if pair is still valid."""
        return (self.status in [PairStatus.AVAILABLE, PairStatus.IN_USE] and 
                time.time() < self.expires_at)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'pair_id': self.pair_id,
            'nodes': (self.node_a, self.node_b),
            'fidelity': self.fidelity,
            'age_seconds': time.time() - self.created_at,
            'status': self.status.value,
            'purification_level': self.purification_level,
        }


class PurificationProtocol(Enum):
    """Entanglement purification protocols."""
    BBPSSW = "bbpssw"  # BBPSSW protocol
    DEJMPS = "dejmps"  # DEJMPS protocol
    SINGLE = "single"  # Single pair purification


class EntanglementManager:
    """
    Entanglement resource manager.
    
    Features:
    - Track available entangled pairs
    - Manage pair lifecycle
    - Support entanglement purification
    - Monitor quality and generate reports
    """
    
    def __init__(self, default_fidelity: float = 0.95,
                 purification_enabled: bool = True):
        """
        Initialize entanglement manager.
        
        Args:
            default_fidelity: Default fidelity for new pairs
            purification_enabled: Whether to auto-purify
        """
        self.default_fidelity = default_fidelity
        self.purification_enabled = purification_enabled
        
        self.pairs: Dict[str, EntanglementPair] = {}
        self._id_counter = 0
        self.purification_count = 0
        self.loss_count = 0
    
    def create_pair(self, node_a: str, node_b: str,
                    fidelity: Optional[float] = None) -> EntanglementPair:
        """
        Create a new entanglement pair.
        
        Args:
            node_a: First node
            node_b: Second node
            fidelity: Optional fidelity (uses default if None)
            
        Returns:
            Created EntanglementPair
        """
        pair_id = f"ep_{self._id_counter}"
        self._id_counter += 1
        
        pair = EntanglementPair(
            pair_id=pair_id,
            node_a=node_a,
            node_b=node_b,
            fidelity=fidelity or self.default_fidelity,
        )
        
        self.pairs[pair_id] = pair
        return pair
    
    def get_available_pair(self, node_a: str, node_b: str) -> Optional[EntanglementPair]:
        """
        Get available pair between two nodes.
        
        Returns:
            EntanglementPair if available, None otherwise
        """
        for pair in self.pairs.values():
            if (pair.node_a == node_a and pair.node_b == node_b or
                pair.node_a == node_b and pair.node_b == node_a):
                if pair.status == PairStatus.AVAILABLE and pair.is_valid():
                    return pair
        return None
    
    def consume_pair(self, pair_id: str) -> bool:
        """
        Mark pair as consumed (used for teleportation, etc.).
        
        Returns:
            True if successful
        """
        if pair_id not in self.pairs:
            return False
        
        pair = self.pairs[pair_id]
        if pair.status != PairStatus.AVAILABLE:
            return False
        
        pair.status = PairStatus.CONSUMED
        return True
    
    def purify_pairs(self, pair_id1: str, pair_id2: str,
                      protocol: PurificationProtocol = PurificationProtocol.BBPSSW,
                      target_fidelity: float = 0.99) -> Optional[EntanglementPair]:
        """
        Purify two noisy pairs into one higher-fidelity pair.
        
        Returns:
            New purified pair if successful, None otherwise
        """
        if pair_id1 not in self.pairs or pair_id2 not in self.pairs:
            return None
        
        pair1 = self.pairs[pair_id1]
        pair2 = self.pairs[pair_id2]
        
        # Check if inputs are valid
        if not (pair1.is_valid() and pair2.is_valid() and
                pair1.status == Pair2.status == PairStatus.AVAILABLE):
            return None
        
        # Simplified purification: improve fidelity
        avg_fidelity = (pair1.fidelity + pair2.fidelity) / 2.0
        
        if protocol == PurificationProtocol.BBPSSW:
            # BBPSSW doubles fidelity roughly
            new_fidelity = min(target_fidelity, avg_fidelity * 1.5)
        elif protocol == PurificationProtocol.DEJMPS:
            # DEJMPS can achieve higher fidelity
            new_fidelity = min(target_fidelity, avg_fidelity * 1.8)
        else:
            new_fidelity = avg_fidelity
        
        # Mark old pairs as purified
        pair1.status = PairStatus.PURIFIED
        pair2.status = PairStatus.PURIFIED
        
        # Create new purified pair
        new_pair = self.create_pair(
            pair1.node_a, pair1.node_b,
            fidelity=new_fidelity
        )
        new_pair.purification_level = pair1.purification_level + 1
        
        self.purification_count += 1
        return new_pair
    
    def cleanup_expired(self) -> int:
        """
        Remove expired pairs.
        
        Returns:
            Number of pairs removed
        """
        expired = [pid for pid, p in self.pairs.items() if not p.is_valid()]
        
        for pid in expired:
            self.pairs[pid].status = PairStatus.LOST
            self.loss_count += 1
            del self.pairs[pid]
        
        return len(expired)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get entanglement statistics."""
        valid_pairs = [p for p in self.pairs.values() if p.is_valid()]
        
        if not valid_pairs:
            return {
                'total_pairs': 0,
                'available': 0,
                'in_use': 0,
                'average_fidelity': 0.0,
                'purification_count': self.purification_count,
                'loss_count': self.loss_count,
            }
        
        fidelities = [p.fidelity for p in valid_pairs]
        
        return {
            'total_pairs': len(valid_pairs),
            'available': sum(1 for p in valid_pairs if p.status == PairStatus.AVAILABLE),
            'in_use': sum(1 for p in valid_pairs if p.status == PairStatus.IN_USE),
            'average_fidelity': float(np.mean(fidelities)),
            'min_fidelity': float(np.min(fidelities)),
            'max_fidelity': float(np.max(fidelities)),
            'purification_count': self.purification_count,
            'loss_count': self.loss_count,
        }
    
    def monitor_quality(self, threshold: float = 0.9) -> Dict[str, Any]:
        """
        Monitor entanglement quality.
        
        Args:
            threshold: Fidelity threshold for alerts
            
        Returns:
            Quality report
        """
        stats = self.get_statistics()
        alerts = []
        
        if stats['average_fidelity'] < threshold:
            alerts.append(f"Average fidelity {stats['average_fidelity']:.2f} below threshold {threshold}")
        
        low_fidelity_pairs = [
            p.to_dict() for p in self.pairs.values()
            if p.is_valid() and p.fidelity < threshold
        ]
        
        return {
            'timestamp': time.time(),
            'total_pairs': stats['total_pairs'],
            'average_fidelity': stats['average_fidelity'],
            'threshold': threshold,
            'alerts': alerts,
            'low_fidelity_pairs': low_fidelity_pairs,
            'status': 'HEALTHY' if not alerts else 'DEGRADED',
        }


class EntanglementDistributionProtocol:
    """
    Protocols for distributing entanglement across network.
    """
    
    def __init__(self, manager: EntanglementManager):
        self.manager = manager
        self.distribution_count = 0
    
    def distribute(self, node_a: str, node_b: str,
                   method: str = "direct",
                   **kwargs) -> Optional[EntanglementPair]:
        """
        Distribute entanglement between two nodes.
        
        Args:
            node_a: First node
            node_b: Second node
            method: "direct", "swapping", or "purified"
            
        Returns:
            EntanglementPair if successful, None otherwise
        """
        if method == "direct":
            return self._direct_distribution(node_a, node_b, **kwargs)
        elif method == "swapping":
            return self._swapping_distribution(node_a, node_b, **kwargs)
        elif method == "purified":
            return self._purified_distribution(node_a, node_b, **kwargs)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _direct_distribution(self, node_a: str, node_b: str,
                             **kwargs) -> EntanglementPair:
        """Direct entanglement generation."""
        fidelity = kwargs.get('fidelity', 0.95)
        pair = self.manager.create_pair(node_a, node_b, fidelity=fidelity)
        self.distribution_count += 1
        return pair
    
    def _swapping_distribution(self, node_a: str, node_b: str,
                                **kwargs) -> Optional[EntanglementPair]:
        """Use entanglement swapping through intermediate nodes."""
        # Simplified: assume success
        fidelity = kwargs.get('fidelity', 0.90)  # Lower due to swapping
        pair = self.manager.create_pair(node_a, node_b, fidelity=fidelity)
        self.distribution_count += 1
        return pair
    
    def _purified_distribution(self, node_a: str, node_b: str,
                               **kwargs) -> Optional[EntanglementPair]:
        """Distribute with purification."""
        # Create two pairs and purify
        pair1 = self._direct_distribution(node_a, node_b, fidelity=kwargs.get('fidelity', 0.93))
        pair2 = self._direct_distribution(node_a, node_b, fidelity=kwargs.get('fidelity', 0.93))
        
        if pair1 and pair2:
            return self.manager.purify_pairs(
                pair1.pair_id, pair2.pair_id,
                protocol=PurificationProtocol.BBPSSW,
                target_fidelity=kwargs.get('target_fidelity', 0.99)
            )
        return None
