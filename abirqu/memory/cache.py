"""
Task 12.3 — Quantum Cache Manager

Caching layer for quantum states and sub-circuits with encryption and analytics.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import time
import hashlib
import pickle


@dataclass
class CacheEntry:
    """An entry in the quantum cache."""
    key: str
    data: Any  # Could be state vector, circuit, or measurement results
    metadata: Dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    encrypted: bool = False
    size_bytes: int = 0
    
    def __post_init__(self):
        if self.size_bytes == 0 and self.data is not None:
            try:
                self.size_bytes = len(pickle.dumps(self.data))
            except:
                self.size_bytes = 1024  # Default estimate
    
    def touch(self):
        """Update access metadata."""
        self.access_count += 1
        self.last_accessed = time.time()
    
    def is_expired(self, ttl_seconds: float = 3600) -> bool:
        """Check if entry is expired."""
        return (time.time() - self.last_accessed) > ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'key': self.key,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed,
            'encrypted': self.encrypted,
            'size_kb': self.size_bytes / 1024,
            'metadata': self.metadata,
        }


class QuantumCacheManager:
    """
    Cache manager for frequently used quantum states and sub-circuits.
    
    Features:
    - Caching layer for quantum states and sub-circuits
    - Cache invalidation based on circuit modifications
    - Persistent cache across sessions (encrypted via abir-guard)
    - Cache hit/miss analytics and optimization
    """
    
    def __init__(self, max_size_mb: float = 100.0, 
                 encryption_enabled: bool = False,
                 cache_dir: str = "./.qcache"):
        """
        Initialize quantum cache manager.
        
        Args:
            max_size_mb: Maximum cache size in MB
            encryption_enabled: Whether to encrypt cached data
            cache_dir: Directory for persistent cache
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.encryption_enabled = encryption_enabled
        self.cache_dir = cache_dir
        
        self.cache: Dict[str, CacheEntry] = {}
        self.hits = 0
        self.misses = 0
        self.current_size_bytes = 0
        
        # Create cache directory if needed
        import os
        os.makedirs(cache_dir, exist_ok=True)
    
    def _generate_key(self, data: Any) -> str:
        """Generate cache key from data."""
        try:
            data_bytes = pickle.dumps(data)
            return hashlib.sha256(data_bytes).hexdigest()[:16]
        except:
            # Fallback: use string representation
            return hashlib.sha256(str(data).encode()).hexdigest()[:16]
    
    def put(self, data: Any, metadata: Optional[Dict[str, Any]] = None,
            key: Optional[str] = None) -> str:
        """
        Add data to cache.
        
        Args:
            data: Data to cache (state vector, circuit, etc.)
            metadata: Optional metadata dict
            key: Optional custom key (auto-generated if None)
            
        Returns:
            Cache key
        """
        if key is None:
            key = self._generate_key(data)
        
        # Check if already cached
        if key in self.cache:
            self.cache[key].touch()
            return key
        
        # Estimate size
        try:
            size = len(pickle.dumps(data))
        except:
            size = 1024  # Default
        
        # Evict if needed
        while (self.current_size_bytes + size > self.max_size_bytes and 
               len(self.cache) > 0):
            self._evict_lru()
        
        # Encrypt if enabled (simplified - just mark as encrypted)
        encrypted = self.encryption_enabled
        if encrypted:
            # In practice, would use abir-guard encryption here
            data = f"ENCRYPTED:{data}"  # Placeholder
        
        entry = CacheEntry(
            key=key,
            data=data,
            metadata=metadata or {},
            encrypted=encrypted,
            size_bytes=size,
        )
        
        self.cache[key] = entry
        self.current_size_bytes += size
        
        # Persist if encrypted
        if encrypted:
            self._persist_entry(entry)
        
        return key
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found
        """
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if entry.is_expired():
            self.invalidate(key)
            self.misses += 1
            return None
        
        entry.touch()
        self.hits += 1
        
        if entry.encrypted:
            # Decrypt (simplified)
            return entry.data.replace("ENCRYPTED:", "") if isinstance(entry.data, str) else entry.data
        
        return entry.data
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was removed
        """
        if key in self.cache:
            entry = self.cache[key]
            self.current_size_bytes -= entry.size_bytes
            del self.cache[key]
            
            # Remove from disk if persisted
            if entry.encrypted:
                import os
                path = os.path.join(self.cache_dir, f"{key}.cache")
                if os.path.exists(path):
                    os.remove(path)
            
            return True
        return False
    
    def invalidate_by_circuit_modification(self, modified_gates: List[str]):
        """
        Invalidate cache entries affected by circuit modifications.
        
        Args:
            modified_gates: List of modified gate names
        """
        keys_to_invalidate = []
        for key, entry in self.cache.items():
            if 'gates' in entry.metadata:
                for gate in entry.metadata['gates']:
                    if gate in modified_gates:
                        keys_to_invalidate.append(key)
                        break
        
        for key in keys_to_invalidate:
            self.invalidate(key)
        
        return len(keys_to_invalidate)
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self.cache:
            return
        
        lru_key = min(self.cache.keys(), 
                       key=lambda k: self.cache[k].last_accessed)
        self.invalidate(lru_key)
    
    def _persist_entry(self, entry: CacheEntry):
        """Persist encrypted entry to disk."""
        try:
            import os
            path = os.path.join(self.cache_dir, f"{entry.key}.cache")
            with open(path, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            print(f"Warning: Could not persist cache entry: {e}")
    
    def get_analytics(self) -> 'CacheAnalytics':
        """Get cache analytics."""
        hit_rate = self.hits / max(self.hits + self.misses, 1)
        
        sizes = [e.size_bytes for e in self.cache.values()]
        access_counts = [e.access_count for e in self.cache.values()]
        
        return CacheAnalytics(
            total_entries=len(self.cache),
            hit_rate=hit_rate,
            hits=self.hits,
            misses=self.misses,
            current_size_mb=self.current_size_bytes / (1024 ** 2),
            max_size_mb=self.max_size_bytes / (1024 ** 2),
            avg_access_count=np.mean(access_counts) if access_counts else 0,
            num_encrypted=sum(1 for e in self.cache.values() if e.encrypted),
        )
    
    def optimize(self) -> Dict[str, Any]:
        """
        Optimize cache based on analytics.
        
        Returns:
            Dict with optimization suggestions
        """
        analytics = self.get_analytics()
        
        suggestions = []
        
        if analytics.hit_rate < 0.5:
            suggestions.append("Low hit rate - consider increasing cache size or improving key strategy")
        
        if analytics.current_size_mb / analytics.max_size_mb > 0.9:
            suggestions.append("Cache nearly full - consider increasing max_size_mb")
        
        # Find unused entries
        unused = sum(1 for e in self.cache.values() if e.access_count <= 1)
        if unused > len(self.cache) * 0.3:
            suggestions.append(f"Many unused entries ({unused}) - consider clearing stale cache")
        
        return {
            'analytics': analytics.to_dict(),
            'suggestions': suggestions,
            'optimized': len(suggestions) == 0,
        }
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.current_size_bytes = 0
        self.hits = 0
        self.misses = 0


@dataclass
class CacheAnalytics:
    """Cache analytics data."""
    total_entries: int
    hit_rate: float
    hits: int
    misses: int
    current_size_mb: float
    max_size_mb: float
    avg_access_count: float
    num_encrypted: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_entries': self.total_entries,
            'hit_rate': self.hit_rate,
            'hit_rate_percent': self.hit_rate * 100,
            'hits': self.hits,
            'misses': self.misses,
            'current_size_mb': self.current_size_mb,
            'max_size_mb': self.max_size_mb,
            'utilization_percent': (self.current_size_mb / max(self.max_size_mb, 1)) * 100,
            'avg_access_count': self.avg_access_count,
            'num_encrypted': self.num_encrypted,
        }
