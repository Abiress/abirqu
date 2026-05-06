"""
Task 13.2 — Quantum Internet Protocols.

Quantum teleportation, superdense coding, entanglement swapping, quantum repeaters, routing.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class ProtocolType(Enum):
    """Quantum internet protocol types."""
    TELEPORTATION = "teleportation"
    SUPERDENSE = "superdense_coding"
    SWAPPING = "entanglement_swapping"
    PURIFICATION = "purification"
    REPEATER = "quantum_repeater"


@dataclass
class ProtocolResult:
    """Result of a quantum protocol execution."""
    protocol: ProtocolType
    success: bool
    fidelity: float  # 0-1
    qubits_used: int
    classical_bits_exchanged: int
    time_ns: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'protocol': self.protocol.value,
            'success': self.success,
            'fidelity': self.fidelity,
            'qubits_used': self.qubits_used,
            'classical_bits_exchanged': self.classical_bits_exchanged,
            'time_ns': self.time_ns,
            'metadata': self.metadata,
        }


class QuantumTeleportation:
    """
    Quantum teleportation protocol implementation.
    
    Transfers unknown quantum state from Alice to Bob using EPR pair and classical communication.
    """
    
    def __init__(self, channel_fidelity: float = 0.99):
        self.channel_fidelity = channel_fidelity
        self.stats: List[Dict[str, Any]] = []
    
    def teleport(self, state_to_send: np.ndarray,
                   ep_pair: Optional[np.ndarray] = None) -> Tuple[bool, np.ndarray, Dict[str, Any]]:
        """
        Perform quantum teleportation.
        
        Args:
            state_to_send: 2-element state vector |ψ> to teleport.
            ep_pair: Optional pre-shared EPR pair (|00>+|11>)/√2.
            
        Returns:
            Tuple of (success, received_state, protocol_data).
        """
        # Create EPR pair if not provided.
        if ep_pair is None:
            ep_pair = np.array([1, 0, 0, 1]) / np.sqrt(2)
        
        # Alice has |ψ> and first qubit of EPR.
        # Bob has second qubit of EPR.
        
        # Step 1: Alice performs Bell measurement on |ψ> and her EPR qubit.
        # Simplified: apply Bell basis measurement.
        bell_measurement = self._bell_measurement(state_to_send, ep_pair[:2])
        
        # Step 2: Alice sends 2 classical bits to Bob.
        classical_bits = bell_measurement['outcome']
        
        # Step 3: Bob applies correction based on classical bits.
        received = ep_pair[2:]  # Bob's qubit (simplified).
        
        # Apply correction.
        if classical_bits == '00':
            received = received  # Identity.
        elif classical_bits == '01':
            received = self._apply_pauli(received, 'X')
        elif classical_bits == '10':
            received = self._apply_pauli(received, 'Z')
        elif classical_bits == '11':
            received = self._apply_pauli(received, 'Y')
        
        # Calculate fidelity.
        fidelity = self._calculate_fidelity(state_to_send, received)
        
        # Add channel noise.
        fidelity *= self.channel_fidelity
        
        result = ProtocolResult(
            protocol=ProtocolType.TELEPORTATION,
            success=(fidelity > 0.5),
            fidelity=fidelity,
            qubits_used=3,  # |ψ> + 2 EPR qubits.
            classical_bits_exchanged=2,
            time_ns=1000.0,  # 1 microsecond.
            metadata={
                'bell_outcome': classical_bits,
                'channel_fidelity': self.channel_fidelity,
            }
        )
        
        self.stats.append(result.to_dict())
        return result.success, received, result.to_dict()
    
    def _bell_measurement(self, state: np.ndarray, epr_qubit: np.ndarray) -> Dict[str, Any]:
        """Perform Bell measurement on two qubits."""
        # Combine states: state ⊗ epr_qubit[0] (first qubit of EPR).
        # EPR pair is (|00> + |11>)/√2 = [1, 0, 0, 1]/√2.
        # Measurement is in Bell basis: |Φ+>, |Φ->, |Ψ+>, |Ψ->.

        # Create 2-qubit state: |ψ> ⊗ |0> (Alice's EPR qubit).
        combined = np.kron(state, np.array([1.0, 0.0], dtype=complex))

        # Apply CNOT (control = first qubit (|ψ>), target = second qubit (EPR)).
        # Then apply Hadamard to first qubit.
        # Bell basis measurement.

        # Apply Hadamard to first qubit.
        H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        # Simplified: just compute Bell state probabilities.

        # Bell states:
        # |Φ+> = (|00> + |11>)/√2
        # |Φ-> = (|00> - |11>)/√2
        # |Ψ+> = (|01> + |10>)/√2
        # |Ψ-> = (|01> - |10>)/√2

        # Project onto Bell basis (simplified).
        bell_states = [
            np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2),  # |Φ+>.
            np.array([1, 0, 0, -1], dtype=complex) / np.sqrt(2),  # |Φ->.
            np.array([0, 1, 1, 0], dtype=complex) / np.sqrt(2),  # |Ψ+>.
            np.array([0, 1, -1, 0], dtype=complex) / np.sqrt(2)   # |Ψ->.
        ]

        # Compute probabilities.
        probs = []
        for bell in bell_states:
            overlap = np.abs(np.vdot(bell, combined)) ** 2
            probs.append(overlap)

        # Normalize.
        probs = np.array(probs) / np.sum(probs)

        # Measure (choose outcome based on probabilities).
        outcome_idx = np.random.choice(4, p=probs)
        outcomes = ['00', '01', '10', '11']

        return {'outcome': outcomes[outcome_idx], 'probability': probs[outcome_idx]}
    
    def _apply_pauli(self, state: np.ndarray, pauli: str) -> np.ndarray:
        """Apply Pauli operator."""
        if pauli == 'X':
            return np.array([state[1], state[0]])
        elif pauli == 'Y':
            return np.array([-1j * state[1], 1j * state[0]])
        elif pauli == 'Z':
            return np.array([state[0], -state[1]])
        return state
    
    def _calculate_fidelity(self, original: np.ndarray, received: np.ndarray) -> float:
        """Calculate state fidelity."""
        # |<ψ|φ>|^2.
        overlap = np.abs(np.vdot(original, received)) ** 2
        return min(1.0, float(overlap))
    
    def batch_teleport(self, states: List[np.ndarray]) -> List[ProtocolResult]:
        """Teleport multiple states."""
        results = []
        for state in states:
            success, _, data = self.teleport(state)
            results.append(ProtocolResult(**data))
        return results


class SuperdenseCoding:
    """
    Superdense coding protocol.
    
    Encodes 2 classical bits into 1 qubit using shared entanglement.
    """
    
    def __init__(self):
        self.stats: List[Dict[str, Any]] = []
    
    def encode(self, classical_bits: str, 
                 ep_pair: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Encode 2 classical bits into 1 qubit.
        
        Args:
            classical_bits: 2-bit string ('00', '01', '10', '11').
            ep_pair: Optional pre-shared EPR pair (4-element state vector).
            
        Returns:
            Tuple of (encoded_qubit_for_transmission, metadata).
        """
        if ep_pair is None:
            # Standard EPR pair: (|00> + |11>)/√2
            ep_pair = np.array([1, 0, 0, 1]) / np.sqrt(2)
        
        # Alice's qubit is the first qubit of the EPR pair.
        # The EPR state is: (|00> + |11>)/√2 = [1, 0, 0, 1]/√2
        # Alice has qubit 0, Bob has qubit 1.
        
        # Create the transformed 2-qubit state based on Alice's operations.
        # After Alice applies gates, the state becomes one of the 4 Bell states.
        if classical_bits == '00':
            # Identity: state remains (|00> + |11>)/√2
            new_state = np.array([1, 0, 0, 1]) / np.sqrt(2)
        elif classical_bits == '01':
            # X gate on Alice's qubit: (|10> + |01>)/√2 = (|01> + |10>)/√2
            new_state = np.array([0, 1, 1, 0]) / np.sqrt(2)
        elif classical_bits == '10':
            # Z gate on Alice's qubit: (|00> - |11>)/√2
            new_state = np.array([1, 0, 0, -1]) / np.sqrt(2)
        elif classical_bits == '11':
            # X+Z gate (or Z+X): (|01> - |10>)/√2
            new_state = np.array([0, 1, -1, 0]) / np.sqrt(2)
        else:
            raise ValueError(f"Invalid bits: {classical_bits}")
        
        # Alice sends her qubit (first qubit) to Bob.
        # For simulation, we return the full 2-qubit state.
        # In reality, Alice would send only her physical qubit.
        result = ProtocolResult(
            protocol=ProtocolType.SUPERDENSE,
            success=True,
            fidelity=1.0,
            qubits_used=2,  # 1 EPR pair shared.
            classical_bits_exchanged=2,
            time_ns=500.0,
            metadata={'bits_encoded': classical_bits, 'bell_state': classical_bits}
        )
        
        self.stats.append(result.to_dict())
        return new_state, result.to_dict()
    
    def decode(self, received_state: np.ndarray, 
                  ep_pair: Optional[np.ndarray] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Decode superdense coded qubit.
        
        In superdense coding, Alice applies gates to her EPR qubit and sends it to Bob.
        Bob performs Bell measurement on both qubits to decode 2 classical bits.
        
        Args:
            received_state: The 2-qubit Bell state after Alice's encoding.
            ep_pair: Not used in this simulation (kept for API compatibility).
            
        Returns:
            Tuple of (decoded_bits, metadata).
        """
        # The received_state is already the 2-qubit Bell state.
        # Perform Bell measurement by checking which Bell state it is.
        
        # Define Bell states with correct mapping to original bits.
        # Based on standard superdense coding protocol:
        # '00' -> I on Alice's qubit -> |Φ+> = (|00> + |11>)/√2
        # '01' -> X on Alice's qubit -> |Ψ+> = (|01> + |10>)/√2
        # '10' -> Z on Alice's qubit -> |Φ-> = (|00> - |11>)/√2
        # '11' -> XZ on Alice's qubit -> |Ψ-> = (|01> - |10>)/√2
        
        bell_states = {
            '00': np.array([1, 0, 0, 1]) / np.sqrt(2),  # |Φ+> -> '00'
            '01': np.array([0, 1, 1, 0]) / np.sqrt(2),   # |Ψ+> -> '01'
            '10': np.array([1, 0, 0, -1]) / np.sqrt(2),  # |Φ-> -> '10'
            '11': np.array([0, 1, -1, 0]) / np.sqrt(2),  # |Ψ-> -> '11'
        }
        
        # Find which Bell state we have maximum overlap with.
        max_overlap = -1
        decoded_bits = '00'
        for bits, bell_state in bell_states.items():
            # Compute overlap: |<psi|bell>|^2
            overlap = np.abs(np.dot(received_state.conj(), bell_state))
            if overlap > max_overlap:
                max_overlap = overlap
                decoded_bits = bits
        
        result = ProtocolResult(
            protocol=ProtocolType.SUPERDENSE,
            success=True,
            fidelity=1.0,
            qubits_used=2,
            classical_bits_exchanged=2,
            time_ns=500.0,
            metadata={'decoded_bits': decoded_bits}
        )
        
        return decoded_bits, result.to_dict()


class EntanglementSwapping:
    """
    Entanglement swapping protocol.
    
    Creates entanglement between two nodes that don't share direct EPR pair.
    """
    
    def __init__(self):
        self.swap_count = 0
    
    def swap(self, ep_pair1: np.ndarray, ep_pair2: np.ndarray) -> Tuple[bool, np.ndarray, float]:
        """
        Perform entanglement swapping.
        
        Args:
            ep_pair1: EPR pair between A-B (|00>+|11>)/√2.
            ep_pair2: EPR pair between B-C.
            
        Returns:
            Tuple of (success, entangled_state_AC, fidelity).
        """
        # Node B performs Bell measurement on its two qubits.
        bell_outcome = np.random.choice(['00', '01', '10', '11'])
        
        # After measurement, A and C are entangled.
        # Simplified: return new EPR-like state.
        new_ep = np.array([1, 0, 0, 1]) / np.sqrt(2)
        
        # Apply correction based on Bell outcome.
        fidelity = 0.95  # Simplified.
        
        self.swap_count += 1
        return True, new_ep, fidelity


class EntanglementPurification:
    """
    Entanglement purification protocols (BBPSSW, DEJMPS).
    
    Increases fidelity of noisy entangled pairs.
    """
    
    def __init__(self):
        self.purification_count = 0
    
    def bbssw_protocol(self, pair1: np.ndarray, pair2: np.ndarray,
                         target_fidelity: float = 0.99) -> Tuple[bool, np.ndarray, float]:
        """
        BBPSSW purification protocol.
        
        Uses 2 noisy pairs to produce 1 higher-fidelity pair.
        
        Returns:
            Tuple of (success, purified_pair, fidelity).
        """
        # Simplified: assume success with some probability.
        success_prob = 0.5  # Depends on input fidelity.
        
        if np.random.random() < success_prob:
            purified = np.array([1, 0, 0, 1]) / np.sqrt(2)
            fidelity = min(target_fidelity, 0.98)
            self.purification_count += 1
            return True, purified, fidelity
        else:
            return False, pair1, 0.5  # Failed.
    
    def dejmp_protocol(self, pair1: np.ndarray, pair2: np.ndarray) -> Tuple[bool, np.ndarray, float]:
        """
        DEJMPS (filtering-based) purification using real BBPSSW protocol.

        Uses two entangled pairs to produce one with higher fidelity.
        """
        # Calculate input fidelities.
        # For Bell state |Φ+> = [1,0,0,1]/√2, fidelity with |Φ+> is |<Φ+|ψ>|^2.
        bell_phi_plus = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)

        # Fidelity of input pairs.
        f1 = np.abs(np.vdot(bell_phi_plus, pair1)) ** 2 if len(pair1) == 4 else 0.9
        f2 = np.abs(np.vdot(bell_phi_plus, pair2)) ** 2 if len(pair2) == 4 else 0.9

        # DEJMPS success probability and output fidelity.
        # Based on actual BBPSSW protocol equations.
        if f1 > 0 and f2 > 0:
            # Success probability: p_succ = f1^2 + (1-f1)^2 (for same basis measurements)
            p_succ = f1**2 + (1-f1)**2
            # Output fidelity: F_out = (f1*f2 + (1-f1)*(1-f2)/3) / p_succ
            f_out = (f1*f2 + (1-f1)*(1-f2)/3) / max(p_succ, 1e-10)

            success = np.random.random() < p_succ

            if success:
                # Output purified Bell state.
                purified = bell_phi_plus.copy()
                return True, purified, min(f_out, 0.99)
            else:
                return False, pair1, f1
        else:
            return False, pair1, 0.5


class QuantumRepeaterChain:
    """
    Quantum repeater chain simulation.
    
    Distributes entanglement over long distances using repeaters.
    """
    
    def __init__(self, num_repeaters: int = 3):
        self.num_repeaters = num_repeaters
        self.segments = num_repeaters + 1
        
    def distribute_entanglement(self, distance_km: float,
                              purification_rounds: int = 1) -> Dict[str, Any]:
        """
        Distribute entanglement across repeater chain.
        
        Returns:
            Dict with results.
        """
        segment_distance = distance_km / self.segments
        
        # Fidelity decreases with distance.
        base_fidelity = np.exp(-distance_km / 20.0)  # Simplified attenuation.
        
        # Apply purification.
        fidelity = base_fidelity
        for _ in range(purification_rounds):
            fidelity = min(0.99, fidelity * 1.5)  # Improves but saturates.
        
        # Calculate resources.
        total_qubits = 2 * (self.num_repeaters + 2)  # End nodes + repeaters.
        classical_bits = 4 * self.segments  # Per swapping step.
        
        return {
            'success': fidelity > 0.5,
            'fidelity': fidelity,
            'distance_km': distance_km,
            'segments': self.segments,
            'total_qubits': total_qubits,
            'classical_bits': classical_bits,
            'purification_rounds': purification_rounds,
        }


class QuantumRouting:
    """
    Quantum routing algorithms.
    """
    
    def __init__(self):
        self.routes: Dict[Tuple[str, str], List[str]] = {}
    
    def find_route(self, topology: Any, source: str, target: str,
                    metric: str = "shortest_path") -> List[str]:
        """
        Find route between two nodes.
        
        Args:
            topology: NetworkTopology object.
            source: Source node ID.
            target: Target node ID.
            metric: Routing metric ("shortest_path", "highest_fidelity").
            
        Returns:
            List of node IDs forming the path.
        """
        if metric == "shortest_path":
            return self._bfs_route(topology, source, target)
        else:
            return self._highest_fidelity_route(topology, source, target)
    
    def _bfs_route(self, topology: Any, source: str, target: str) -> List[str]:
        """BFS shortest path."""
        from collections import deque
        queue = deque([source])
        visited = {source: None}
        
        while queue:
            current = queue.popleft()
            if current == target:
                break
            for neighbor in topology.get_neighbors(current):
                if neighbor not in visited:
                    visited[neighbor] = current
                    queue.append(neighbor)
        
        # Reconstruct path.
        path = []
        curr = target
        while curr is not None:
            path.append(curr)
            curr = visited.get(curr)
        path.reverse()
        return path
    
    def _highest_fidelity_route(self, topology: Any, source: str, target: str) -> List[str]:
        """Route with highest fidelity (simplified: just use shortest)."""
        return self._bfs_route(topology, source, target)
