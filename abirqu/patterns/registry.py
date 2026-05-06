"""
Quantum Pattern Registry for AbirQu
Copyright 2026 Abir Maheshwari

Registry for quantum components and patterns.
"""
from typing import Dict, List, Type, Optional, Any
from ..core.circuit import Circuit

class ComponentRegistry:
    """Registry for quantum components and patterns."""
    
    def __init__(self):
        self.components: Dict[str, Type] = {}
        self.instances: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict] = {}
        
    def register(self, name: str, component: Type, metadata: Optional[Dict] = None):
        """Register a component."""
        self.components[name] = component
        if metadata:
            self.metadata[name] = metadata
            
    def register_instance(self, name: str, instance: Any, metadata: Optional[Dict] = None):
        """Register an instance."""
        self.instances[name] = instance
        if metadata:
            self.metadata[name] = metadata
            
    def get(self, name: str) -> Optional[Type]:
        """Get component by name."""
        return self.components.get(name)
        
    def get_instance(self, name: str) -> Optional[Any]:
        """Get registered instance."""
        return self.instances.get(name)
        
    def list_all(self) -> List[str]:
        """List all registered component names."""
        return list(self.components.keys())
        
    def list_instances(self) -> List[str]:
        """List all registered instance names."""
        return list(self.instances.keys())
        
    def search(self, query: str) -> List[str]:
        """Search components by name (case-insensitive)."""
        query_lower = query.lower()
        return [name for name in self.components.keys() if query_lower in name.lower()]
        
    def get_metadata(self, name: str) -> Optional[Dict]:
        """Get metadata for a component."""
        return self.metadata.get(name)
        
    def create_instance(self, name: str, *args, **kwargs) -> Optional[Any]:
        """Create instance of registered component."""
        component_class = self.get(name)
        if component_class:
            return component_class(*args, **kwargs)
        return None
        
    def unregister(self, name: str):
        """Remove component from registry."""
        self.components.pop(name, None)
        self.instances.pop(name, None)
        self.metadata.pop(name, None)
        
    def clear(self):
        """Clear all registrations."""
        self.components.clear()
        self.instances.clear()
        self.metadata.clear()
        
    def export_registry(self) -> Dict:
        """Export registry to dictionary."""
        return {
            'components': list(self.components.keys()),
            'instances': list(self.instances.keys()),
            'metadata': self.metadata.copy()
        }
        
    def import_registry(self, data: Dict):
        """Import registry from dictionary."""
        # Note: Can't restore classes, only names
        # Would need serialization of class definitions
        pass
        
    def __len__(self):
        return len(self.components)
        
    def __contains__(self, name: str):
        return name in self.components
        
    def __repr__(self):
        return f"ComponentRegistry(components={len(self.components)}, instances={len(self.instances)})"
