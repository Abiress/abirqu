"""
Component Registry for Quantum Circuit Components

Implements a component registry for sharing quantum algorithm implementations.
Supports problem-size-agnostic circuit generators.
Supports hardware-portable implementations that compile to any backend.
Implements a dependency manager for quantum circuit components.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

class ComponentType(Enum):
    """Types of quantum components."""
    CIRCUIT = "circuit"
    PATTERN = "pattern"
    TEMPLATE = "template"
    GATE_SEQUENCE = "gate_sequence"
    ORACLE = "oracle"

@dataclass
class ComponentMetadata:
    """Metadata for a registered component."""
    name: str
    component_type: ComponentType
    description: str
    min_qubits: int
    max_qubits: Optional[int] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    author: str = "Unknown"
    version: str = "1.0.0"

class QuantumComponent:
    """A registered quantum component."""
    
    def __init__(self, metadata: ComponentMetadata, 
                 generator: Callable[..., List[Tuple[str, List[int]]]]):
        """
        Initialize a quantum component.
        
        Args:
            metadata: Component metadata
            generator: Function that generates circuit from parameters
        """
        self.metadata = metadata
        self.generator = generator
        
    def generate(self, **kwargs) -> List[Tuple[str, List[int]]]:
        """
        Generate circuit from this component.
        
        Returns:
            Circuit gates
        """
        return self.generator(**kwargs)
    
    def validate_params(self, **kwargs) -> Tuple[bool, str]:
        """Validate parameters against metadata."""
        for param, value in kwargs.items():
            if param in self.metadata.parameters:
                expected_type = self.metadata.parameters[param]
                if not isinstance(value, expected_type):
                    return False, f"Parameter {param} should be {expected_type}"
        return True, "Valid"

class ComponentRegistry:
    """
    Registry for quantum circuit components.
    
    Supports:
    - Registration of components
    - Lookup by name, type, tags
    - Dependency resolution
    - Problem-size-agnostic generation
    """
    
    def __init__(self):
        self.components: Dict[str, QuantumComponent] = {}
        self._register_defaults()
        
    def _register_defaults(self):
        """Register default components."""
        # Bell state component
        bell_metadata = ComponentMetadata(
            name="bell_state",
            component_type=ComponentType.PATTERN,
            description="Creates a Bell state (|00> + |11>)/sqrt(2)",
            min_qubits=2,
            parameters={},
            tags=["entanglement", "basic"]
        )
        
        def bell_generator(**kwargs):
            return [('H', [0]), ('CNOT', [0, 1])]
            
        self.register(QuantumComponent(bell_metadata, bell_generator))
        
        # GHZ state component
        ghz_metadata = ComponentMetadata(
            name="ghz_state",
            component_type=ComponentType.PATTERN,
            description="Creates a GHZ state",
            min_qubits=3,
            parameters={"num_qubits": int},
            tags=["entanglement", "multipartite"]
        )
        
        def ghz_generator(num_qubits: int = 3, **kwargs):
            gates = [('H', [0])]
            for i in range(1, num_qubits):
                gates.append(('CNOT', [0, i]))
            return gates
            
        self.register(QuantumComponent(ghz_metadata, ghz_generator))
        
        # QFT component
        qft_metadata = ComponentMetadata(
            name="qft",
            component_type=ComponentType.CIRCUIT,
            description="Quantum Fourier Transform",
            min_qubits=1,
            parameters={"num_qubits": int, "inverse": bool},
            tags=["algorithm", "transform"]
        )
        
        def qft_generator(num_qubits: int, inverse: bool = False, **kwargs):
            gates = []
            for i in range(num_qubits):
                gates.append(('H', [i]))
                for j in range(i + 1, num_qubits):
                    angle = np.pi / (2 ** (j - i))
                    gates.append(('CRZ', [j, i, angle]))  # Simplified
            if inverse:
                gates = gates[::-1]  # Reverse for inverse
            return gates
            
        self.register(QuantumComponent(qft_metadata, qft_generator))
        
    def register(self, component: QuantumComponent) -> bool:
        """
        Register a component.
        
        Args:
            component: Component to register
            
        Returns:
            True if successful
        """
        if component.metadata.name in self.components:
            return False  # Already exists
            
        # Check dependencies
        for dep in component.metadata.dependencies:
            if dep not in self.components:
                raise ValueError(f"Dependency {dep} not found")
                
        self.components[component.metadata.name] = component
        return True
    
    def get(self, name: str) -> Optional[QuantumComponent]:
        """Get component by name."""
        return self.components.get(name)
    
    def generate_circuit(self, name: str, **kwargs) -> List[Tuple[str, List[int]]]:
        """
        Generate circuit from registered component.
        
        Args:
            name: Component name
            **kwargs: Parameters for generation
            
        Returns:
            Circuit gates
        """
        component = self.get(name)
        if component is None:
            raise ValueError(f"Component {name} not found")
            
        # Validate parameters
        valid, msg = component.validate_params(**kwargs)
        if not valid:
            raise ValueError(msg)
            
        return component.generate(**kwargs)
    
    def search(self, 
                component_type: Optional[ComponentType] = None,
                tags: Optional[List[str]] = None,
                min_qubits: Optional[int] = None) -> List[QuantumComponent]:
        """
        Search for components.
        
        Args:
            component_type: Filter by type
            tags: Filter by tags (any match)
            min_qubits: Minimum qubit count
            
        Returns:
            List of matching components
        """
        results = []
        
        for component in self.components.values():
            # Filter by type
            if component_type and component.metadata.component_type != component_type:
                continue
                
            # Filter by tags
            if tags:
                if not any(tag in component.metadata.tags for tag in tags):
                    continue
                    
            # Filter by qubit count
            if min_qubits and component.metadata.min_qubits > min_qubits:
                continue
                
            results.append(component)
            
        return results
    
    def get_dependencies(self, name: str) -> List[str]:
        """
        Get dependencies of a component.
        
        Args:
            name: Component name
            
        Returns:
            List of dependency names
        """
        component = self.get(name)
        if component is None:
            return []
        return component.metadata.dependencies
    
    def resolve_dependencies(self, name: str) -> List[str]:
        """
        Resolve all dependencies (including transitive).
        
        Args:
            name: Component name
            
        Returns:
            Ordered list of components (dependencies first)
        """
        visited = set()
        order = []
        
        def dfs(n):
            if n in visited:
                return
            visited.add(n)
            
            comp = self.get(n)
            if comp:
                for dep in comp.metadata.dependencies:
                    dfs(dep)
            order.append(n)
            
        dfs(name)
        return order
    
    def list_all(self) -> List[Dict[str, Any]]:
        """List all registered components."""
        return [
            {
                'name': comp.metadata.name,
                'type': comp.metadata.component_type.value,
                'description': comp.metadata.description,
                'min_qubits': comp.metadata.min_qubits,
                'tags': comp.metadata.tags
            }
            for comp in self.components.values()
        ]

# Example usage and tests
if __name__ == "__main__":
    print("Testing Component Registry...")
    
    registry = ComponentRegistry()
    
    # List all components
    print("\nRegistered Components:")
    for comp_info in registry.list_all():
        print(f"  - {comp_info['name']}: {comp_info['description']}")
        print(f"    Type: {comp_info['type']}, Min qubits: {comp_info['min_qubits']}")
        print(f"    Tags: {comp_info['tags']}")
        
    # Generate circuit from component
    print("\nGenerating Bell state circuit:")
    bell_circuit = registry.generate_circuit("bell_state")
    print(f"  Gates: {bell_circuit}")
    
    # Generate GHZ state
    print("\nGenerating GHZ state (5 qubits):")
    ghz_circuit = registry.generate_circuit("ghz_state", num_qubits=5)
    print(f"  Number of gates: {len(ghz_circuit)}")
    print(f"  First 3 gates: {ghz_circuit[:3]}")
    
    # Search components
    print("\nSearching for 'entanglement' components:")
    results = registry.search(tags=["entanglement"])
    for comp in results:
        print(f"  - {comp.metadata.name}")
        
    # Resolve dependencies
    print("\nDependency resolution for 'qft':")
    deps = registry.resolve_dependencies("qft")
    print(f"  Order: {deps}")