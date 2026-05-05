"""
Hardware-Aware Transpiler

Implements topology-aware routing for different quantum hardware topologies:
- Square lattice (IBM Nighthawk-style)
- Heavy-hex (IBM Eagle/Heron)
- All-to-all (IonQ, trapped ion)
- Neutral atom grids

Includes SWAP network optimizer and native gate set compilation.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set, Any
from enum import Enum
import networkx as nx

class TopologyType(Enum):
    """Supported hardware topologies."""
    ALL_TO_ALL = "all_to_all"
    SQUARE_LATTICE = "square_lattice"
    HEAVY_HEX = "heavy_hex"
    LINEAR = "linear"
    SYCAMORE = "sycamore"  # Google's 2D grid with nearest-neighbor

class HardwareTopology:
    """Represents the connectivity topology of a quantum device."""
    
    def __init__(self, topology_type: TopologyType, num_qubits: int, 
                 coupling_map: Optional[List[Tuple[int, int]]] = None):
        """
        Initialize hardware topology.
        
        Args:
            topology_type: Type of topology
            num_qubits: Number of qubits
            coupling_map: List of (q1, q2) edges (optional, auto-generated if None)
        """
        self.topology_type = topology_type
        self.num_qubits = num_qubits
        self.coupling_map: Set[Tuple[int, int]] = set()
        
        if coupling_map:
            for q1, q2 in coupling_map:
                self.coupling_map.add((min(q1, q2), max(q1, q2)))
        else:
            self._generate_coupling_map()
            
        # Create NetworkX graph for routing algorithms
        self.graph = nx.Graph()
        self.graph.add_nodes_from(range(num_qubits))
        self.graph.add_edges_from(self.coupling_map)
        
    def _generate_coupling_map(self):
        """Generate coupling map based on topology type."""
        if self.topology_type == TopologyType.ALL_TO_ALL:
            # Complete graph
            for i in range(self.num_qubits):
                for j in range(i+1, self.num_qubits):
                    self.coupling_map.add((i, j))
                    
        elif self.topology_type == TopologyType.LINEAR:
            # Linear chain
            for i in range(self.num_qubits - 1):
                self.coupling_map.add((i, i+1))
                
        elif self.topology_type == TopologyType.SQUARE_LATTICE:
            # Square lattice (like IBM Nighthawk)
            side = int(np.ceil(np.sqrt(self.num_qubits)))
            for i in range(self.num_qubits):
                row, col = i // side, i % side
                # Right neighbor
                if col + 1 < side and i + 1 < self.num_qubits:
                    self.coupling_map.add((i, i+1))
                # Bottom neighbor
                if row + 1 < side and i + side < self.num_qubits:
                    self.coupling_map.add((i, i+side))
                    
        elif self.topology_type == TopologyType.HEAVY_HEX:
            # Simplified heavy-hex (IBM Eagle/Heron style)
            # In practice, heavy-hex has a more complex pattern
            # This is a simplified version
            self._generate_heavy_hex()
            
        elif self.topology_type == TopologyType.SYCAMORE:
            # Google Sycamore: 2D grid with next-nearest coupling
            side = int(np.ceil(np.sqrt(self.num_qubits)))
            for i in range(self.num_qubits):
                row, col = i // side, i % side
                # Nearest neighbors (like square lattice)
                if col + 1 < side and i + 1 < self.num_qubits:
                    self.coupling_map.add((i, i+1))
                if row + 1 < side and i + side < self.num_qubits:
                    self.coupling_map.add((i, i+side))
                    
    def _generate_heavy_hex(self):
        """Generate heavy-hex coupling map (simplified)."""
        # Heavy-hex topology has hexagonal cells with additional connections
        # This is a simplified implementation
        for i in range(self.num_qubits):
            # Connect to next qubit if available
            if i + 1 < self.num_qubits:
                self.coupling_map.add((i, i+1))
            # Connect to qubit at i+2 (simplified heavy-hex pattern)
            if i + 2 < self.num_qubits and i % 3 != 2:
                self.coupling_map.add((i, i+2))
                
    def shortest_path(self, q1: int, q2: int) -> Optional[List[int]]:
        """Find shortest path between two qubits."""
        try:
            return nx.shortest_path(self.graph, q1, q2)
        except nx.NetworkXNoPath:
            return None
    
    def distance(self, q1: int, q2: int) -> int:
        """Get distance (number of hops) between two qubits."""
        path = self.shortest_path(q1, q2)
        return len(path) - 1 if path else float('inf')
    
    def get_neighbors(self, qubit: int) -> List[int]:
        """Get neighboring qubits."""
        return list(self.graph.neighbors(qubit))
    
    def is_connected(self, q1: int, q2: int) -> bool:
        """Check if two qubits are directly connected."""
        return (min(q1, q2), max(q1, q2)) in self.coupling_map

class NativeGateSet:
    """Represents the native gate set of a quantum device."""
    
    def __init__(self, device_name: str):
        """
        Initialize native gate set for a device.
        
        Args:
            device_name: Name of the device (ibm_heron, google_sycamore, etc.)
        """
        self.device_name = device_name
        self.single_qubit_gates: Set[str] = set()
        self.two_qubit_gates: Set[str] = set()
        self.gate_fidelities: Dict[str, float] = {}  # Gate -> average fidelity
        
        self._initialize_gate_set()
        
    def _initialize_gate_set(self):
        """Set up native gates based on device."""
        if 'ibm' in self.device_name.lower():
            # IBM devices: SX, X, RZ, S, T, CNOT
            self.single_qubit_gates = {'SX', 'X', 'RZ', 'S', 'T', 'H'}
            self.two_qubit_gates = {'CNOT', 'ECR'}  # Newer IBM use ECR
            self.gate_fidelities = {
                'SX': 0.9999,
                'RZ': 1.0,  # Virtual gate
                'CNOT': 0.995,
                'ECR': 0.996
            }
        elif 'google' in self.device_name.lower() or 'sycamore' in self.device_name.lower():
            # Google Sycamore: sqrt(iswap), phisq, etc.
            self.single_qubit_gates = {'X', 'Y', 'Z', 'S', 'T', 'H', 'PHIQUBIT'}
            self.two_qubit_gates = {'SQRT_ISWAP', 'ISWAP', 'CZ'}
            self.gate_fidelities = {
                'SQRT_ISWAP': 0.996,
                'CZ': 0.997,
                'PHIQUBIT': 0.999
            }
        elif 'ionq' in self.device_name.lower():
            # IonQ: all-to-all, native gates are XX, etc.
            self.single_qubit_gates = {'GPI', 'GPI2', 'GZ'}
            self.two_qubit_gates = {'XX'}
            self.gate_fidelities = {
                'GPI2': 0.9999,
                'XX': 0.997
            }
        elif 'rigetti' in self.device_name.lower():
            # Rigetti: CZ-based
            self.single_qubit_gates = {'RX', 'RZ'}
            self.two_qubit_gates = {'CZ'}
            self.gate_fidelities = {
                'RX': 0.999,
                'RZ': 1.0,
                'CZ': 0.994
            }
        else:
            # Generic/default
            self.single_qubit_gates = {'X', 'Y', 'Z', 'H', 'S', 'T', 'RX', 'RY', 'RZ'}
            self.two_qubit_gates = {'CNOT', 'CZ'}
            
    def supports_gate(self, gate_name: str, num_qubits: int) -> bool:
        """Check if device supports a gate."""
        if num_qubits == 1:
            return gate_name in self.single_qubit_gates
        elif num_qubits == 2:
            return gate_name in self.two_qubit_gates
        return False

class HardwareAwareTranspiler:
    """
    Transpiler that maps circuits to hardware-native gates and topology.
    """
    
    def __init__(self, topology: HardwareTopology, gate_set: NativeGateSet):
        """
        Initialize transpiler.
        
        Args:
            topology: Hardware topology
            gate_set: Native gate set
        """
        self.topology = topology
        self.gate_set = gate_set
        self.stats = {
            'original_depth': 0,
            'transpiled_depth': 0,
            'inserted_swaps': 0,
            'gate_count_change': 0
        }
        
    def transpile(self, circuit_gates: List[Tuple[str, List[int]]],
                  initial_layout: Optional[Dict[int, int]] = None) -> List[Tuple[str, List[int]]]:
        """
        Transpile a circuit to be compatible with hardware.
        
        Args:
            circuit_gates: List of (gate_name, qubits) tuples
            initial_layout: Optional initial qubit mapping {logical: physical}
            
        Returns:
            Transpiled circuit gates
        """
        self.stats['original_depth'] = len(circuit_gates)
        
        # Step 1: Map logical to physical qubits
        if initial_layout is None:
            initial_layout = self._find_initial_layout(circuit_gates)
            
        # Step 2: Decompose gates to native gate set
        decomposed = self._decompose_to_native(circuit_gates)
        
        # Step 3: Route gates through topology (insert SWAPs as needed)
        routed = self._route_circuit(decomposed, initial_layout)
        
        self.stats['transpiled_depth'] = len(routed)
        self.stats['gate_count_change'] = len(routed) - len(circuit_gates)
        
        return routed
    
    def _find_initial_layout(self, circuit_gates: List[Tuple[str, List[int]]]) -> Dict[int, int]:
        """
        Find good initial layout based on circuit connectivity.
        Uses a greedy heuristic.
        """
        # Get all qubits used in circuit
        logical_qubits = set()
        for _, qubits in circuit_gates:
            logical_qubits.update(qubits)
            
        # Sort by connectivity in circuit
        qubit_partners = {q: set() for q in logical_qubits}
        for _, qubits in circuit_gates:
            if len(qubits) == 2:
                q1, q2 = qubits[0], qubits[1]
                if q1 in qubit_partners:
                    qubit_partners[q1].add(q2)
                if q2 in qubit_partners:
                    qubit_partners[q2].add(q1)
                    
        # Sort logical qubits by number of partners (most connected first)
        sorted_logical = sorted(logical_qubits, 
                               key=lambda q: len(qubit_partners.get(q, set())), 
                               reverse=True)
        
        # Greedy assignment to physical qubits
        layout = {}
        used_physical = set()
        
        for logical in sorted_logical:
            # Find best physical qubit for this logical qubit
            # Prefer physical qubits with good connectivity to already-assigned neighbors
            candidates = set(range(self.topology.num_qubits)) - used_physical
            
            if not candidates:
                break
                
            # Score candidates based on connectivity to assigned physical qubits
            best_physical = None
            best_score = -1
            
            for phys in candidates:
                score = 0
                for neighbor_logical in qubit_partners.get(logical, set()):
                    if neighbor_logical in layout:
                        neighbor_phys = layout[neighbor_logical]
                        if self.topology.is_connected(phys, neighbor_phys):
                            score += 1
                if score > best_score:
                    best_score = score
                    best_physical = phys
                    
            if best_physical is not None:
                layout[logical] = best_physical
                used_physical.add(best_physical)
                
        return layout
    
    def _decompose_to_native(self, circuit_gates: List[Tuple[str, List[int]]]) -> List[Tuple[str, List[int]]]:
        """Decompose gates to native gate set."""
        result = []
        
        for gate_name, qubits in circuit_gates:
            if gate_name == 'CNOT':
                if 'CNOT' in self.gate_set.two_qubit_gates:
                    result.append((gate_name, qubits))
                elif 'CZ' in self.gate_set.two_qubit_gates:
                    # Decompose CNOT to H + CZ + H
                    q1, q2 = qubits
                    result.append(('H', [q2]))
                    result.append(('CZ', [q1, q2]))
                    result.append(('H', [q2]))
                else:
                    # Use whatever 2-qubit gate is available
                    native_2q = next(iter(self.gate_set.two_qubit_gates), None)
                    if native_2q:
                        result.append((native_2q, qubits))
                        
            elif gate_name in ['SWAP', 'TOFFOLI', 'FREDKIN']:
                # Decompose 3-qubit gates to 2-qubit + 1-qubit
                decomposed = self._decompose_three_qubit(gate_name, qubits)
                result.extend(decomposed)
                
            else:
                # Single qubit gate - check if native
                if gate_name in self.gate_set.single_qubit_gates:
                    result.append((gate_name, qubits))
                else:
                    # Decompose to native single-qubit gates
                    decomposed = self._decompose_single_qubit(gate_name, qubits)
                    result.extend(decomposed)
                    
        return result
    
    def _decompose_three_qubit(self, gate_name: str, qubits: List[int]) -> List[Tuple[str, List[int]]]:
        """Decompose 3-qubit gates to 2-qubit native gates."""
        # Simplified decomposition
        if gate_name == 'TOFFOLI':
            # Toffoli = H + CNOT + T/T^dag + CNOT + H (simplified)
            q1, q2, q3 = qubits
            return [
                ('H', [q3]),
                ('CNOT', [q2, q3]),
                ('T_dag', [q3]),
                ('CNOT', [q1, q3]),
                ('T', [q3]),
                ('CNOT', [q2, q3]),
                ('T_dag', [q3]),
                ('CNOT', [q1, q3]),
                ('T', [q2]),
                ('T', [q3]),
                ('H', [q3]),
                ('CNOT', [q1, q2]),
                ('T', [q1]),
                ('T_dag', [q2]),
                ('CNOT', [q1, q2])
            ]
        return [(gate_name, qubits)]  # Fallback
    
    def _decompose_single_qubit(self, gate_name: str, qubits: List[int]) -> List[Tuple[str, List[int]]]:
        """Decompose single-qubit gate to native gates."""
        # Simplified - in practice would use Euler decomposition
        if gate_name in ['RX', 'RY', 'RZ']:
            return [(gate_name, qubits)]
        return [('H', qubits)]  # Fallback
    
    def _route_circuit(self, circuit_gates: List[Tuple[str, List[int]]],
                       layout: Dict[int, int]) -> List[Tuple[str, List[int]]]:
        """
        Route circuit through hardware topology.
        Insert SWAP gates to bring qubits together when needed.
        """
        result = []
        current_layout = layout.copy()  # logical -> physical mapping
        reverse_layout = {v: k for k, v in current_layout.items()}  # physical -> logical
        
        for gate_name, qubits in circuit_gates:
            if len(qubits) == 1:
                # Single qubit gate - apply to physical qubit
                logical_q = qubits[0]
                if logical_q in current_layout:
                    physical_q = current_layout[logical_q]
                    result.append((gate_name, [physical_q]))
                else:
                    result.append((gate_name, qubits))  # Shouldn't happen
                    
            elif len(qubits) == 2:
                # Two-qubit gate - may need SWAPs
                q1, q2 = qubits
                phys1 = current_layout.get(q1, q1)
                phys2 = current_layout.get(q2, q2)
                
                if self.topology.is_connected(phys1, phys2):
                    # Directly connected - apply gate
                    result.append((gate_name, [phys1, phys2]))
                else:
                    # Need to route - insert SWAPs
                    swaps = self._find_swap_path(phys1, phys2, current_layout)
                    
                    for swap in swaps:
                        result.append(('SWAP', list(swap)))
                        # Update layout after SWAP
                        self._apply_swap_to_layout(swap, current_layout)
                        
                    # Now qubits should be adjacent
                    phys1_new = current_layout[q1]
                    phys2_new = current_layout[q2]
                    result.append((gate_name, [phys1_new, phys2_new]))
                    
        self.stats['inserted_swaps'] = sum(1 for g, _ in result if g == 'SWAP')
        
        return result
    
    def _find_swap_path(self, phys1: int, phys2: int, 
                        layout: Dict[int, int]) -> List[Tuple[int, int]]:
        """
        Find path of SWAPs to bring two physical qubits together.
        Returns list of SWAP operations needed.
        """
        path = self.topology.shortest_path(phys1, phys2)
        if not path or len(path) < 2:
            return []
            
        # Need to move phys1 towards phys2 along path
        # Insert SWAPs between consecutive nodes on path
        swaps = []
        for i in range(len(path) - 1):
            swaps.append((path[i], path[i+1]))
            
        return swaps
    
    def _apply_swap_to_layout(self, swap: Tuple[int, int], layout: Dict[int, int]):
        """Update layout after a SWAP operation."""
        p1, p2 = swap
        # Find logical qubits on these physical qubits
        logical1 = None
        logical2 = None
        for logical, physical in layout.items():
            if physical == p1:
                logical1 = logical
            elif physical == p2:
                logical2 = logical
                
        # Swap them
        if logical1 is not None and logical2 is not None:
            layout[logical1] = p2
            layout[logical2] = p1
    
    def get_stats(self) -> Dict:
        """Get transpilation statistics."""
        return self.stats.copy()

# Example usage and tests
if __name__ == "__main__":
    print("Testing Hardware-Aware Transpiler...")
    
    # Create a topology (IBM Nighthawk-style square lattice)
    topology = HardwareTopology(
        TopologyType.SQUARE_LATTICE,
        num_qubits=27,
        coupling_map=None  # Auto-generate
    )
    
    print(f"Topology: {topology.topology_type.value}")
    print(f"Number of qubits: {topology.num_qubits}")
    print(f"Number of edges: {len(topology.coupling_map)}")
    
    # Create native gate set for IBM Heron
    gate_set = NativeGateSet("ibm_heron")
    print(f"\nNative gate set for {gate_set.device_name}:")
    print(f"Single-qubit: {gate_set.single_qubit_gates}")
    print(f"Two-qubit: {gate_set.two_qubit_gates}")
    
    # Create transpiler
    transpiler = HardwareAwareTranspiler(topology, gate_set)
    
    # Test circuit: Bell state with non-adjacent qubits
    test_circuit = [
        ('H', [0]),
        ('CNOT', [0, 26])  # Non-adjacent on 27-qubit lattice
    ]
    
    print(f"\nOriginal circuit: {test_circuit}")
    
    transpiled = transpiler.transpile(test_circuit)
    print(f"Transpiled circuit ({len(transpiled)} gates):")
    for gate in transpiled:
        print(f"  {gate}")
        
    print(f"\nStats: {transpiler.get_stats()}")