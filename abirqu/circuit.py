"""
Quantum Circuit Representation for AbirQu
Copyright 2026 Abir Maheshwari
"""
import numpy as np
from typing import List, Dict, Optional, Union, Tuple, Any
from enum import Enum
import json
import uuid

# Import gates from our gates module
from .gates import (
    X, Y, Z, H, S, S_dag, T, T_dag, CNOT, CZ, SWAP, TOFFOLI, FREDKIN,
    rx, ry, rz, GATES, PARAMETERIZED_GATES
)

class GateType(Enum):
    """Enumeration of gate types."""
    SINGLE = "single"
    TWO = "two"
    THREE = "three"
    PARAMETERIZED = "parameterized"
    CUSTOM = "custom"

class Gate:
    """Represents a quantum gate in a circuit."""
    
    def __init__(self, name: str, qubits: List[int], 
                 matrix: Optional[np.ndarray] = None,
                 params: Optional[List[float]] = None):
        """
        Initialize a gate.
        
        Args:
            name: Gate name (e.g., 'X', 'H', 'RX')
            qubits: List of qubit indices the gate acts on
            matrix: Unitary matrix (if custom gate)
            params: Parameters for parameterized gates (e.g., rotation angle)
        """
        self.name = name
        self.qubits = qubits
        self.matrix = matrix
        self.params = params or []
        self.id = str(uuid.uuid4())[:8]
        
    def __repr__(self):
        if self.params:
            return f"{self.name}({', '.join(map(str, self.params))}) on qubits {self.qubits}"
        return f"{self.name} on qubits {self.qubits}"
    
    def to_dict(self) -> Dict:
        """Serialize gate to dictionary."""
        matrix_data = None
        if self.matrix is not None:
            matrix_data = [
                [[float(v.real), float(v.imag)] for v in row]
                for row in self.matrix
            ]

        return {
            'id': self.id,
            'name': self.name,
            'qubits': self.qubits,
            'params': self.params,
            'matrix': matrix_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Gate':
        """Deserialize gate from dictionary."""
        matrix = None
        raw_matrix = data.get('matrix')
        if raw_matrix:
            matrix = np.array(
                [[complex(cell[0], cell[1]) for cell in row] for row in raw_matrix],
                dtype=complex,
            )
        return cls(data['name'], data['qubits'], matrix, data.get('params', []))

class Measurement:
    """Represents a measurement operation."""
    
    def __init__(self, qubit: int, cbit: Optional[int] = None):
        """
        Initialize a measurement.
        
        Args:
            qubit: Qubit to measure
            cbit: Classical bit to store result (defaults to same index as qubit)
        """
        self.qubit = qubit
        self.cbit = cbit if cbit is not None else qubit
        self.id = str(uuid.uuid4())[:8]
        
    def __repr__(self):
        return f"Measure q{self.qubit} -> c{self.cbit}"
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'qubit': self.qubit,
            'cbit': self.cbit
        }

class Circuit:
    """
    Quantum circuit representation with a Python-native DSL.
    More ergonomic than Qiskit's API.
    """
    
    def __init__(self, num_qubits: int, name: Optional[str] = None):
        """
        Initialize a quantum circuit.
        
        Args:
            num_qubits: Number of qubits in the circuit
            name: Optional name for the circuit
        """
        self.num_qubits = num_qubits
        self.name = name or f"circuit_{uuid.uuid4().hex[:8]}"
        self.gates: List[Gate] = []
        self.measurements: List[Measurement] = []
        self.classical_bits = 0  # Number of classical bits needed

    def copy(self) -> 'Circuit':
        """Create a deep copy of this circuit."""
        new_circuit = Circuit(self.num_qubits, name=f"{self.name}_copy")
        for gate in self.gates:
            new_circuit.gates.append(
                Gate(gate.name, list(gate.qubits), gate.matrix, list(gate.params))
            )
        for meas in self.measurements:
            new_circuit.measurements.append(
                Measurement(meas.qubit, meas.cbit)
            )
        new_circuit.classical_bits = self.classical_bits
        return new_circuit
        
    def add_gate(self, gate_name: str, qubits: Union[int, List[int]], 
                 params: Optional[List[float]] = None) -> 'Circuit':
        """
        Add a gate to the circuit.
        
        Args:
            gate_name: Name of the gate ('X', 'H', 'CNOT', 'RX', etc.)
            qubits: Qubit index or list of qubit indices
            params: Parameters for parameterized gates
            
        Returns:
            Self for method chaining
        """
        if isinstance(qubits, int):
            qubits = [qubits]
            
        # Check if gate exists in standard gates
        if gate_name in GATES:
            matrix = GATES[gate_name]
            gate = Gate(gate_name, qubits, matrix, params)
        elif gate_name in PARAMETERIZED_GATES:
            # For parameterized gates, store the function
            if params is None:
                raise ValueError(f"Parameterized gate {gate_name} requires parameters")
            gate_func = PARAMETERIZED_GATES[gate_name]
            matrix = gate_func(*params)
            gate = Gate(gate_name, qubits, matrix, params)
        else:
            raise ValueError(f"Unknown gate: {gate_name}")
            
        self.gates.append(gate)
        return self
        
    # Convenience methods for common gates
    def x(self, qubit: int) -> 'Circuit':
        return self.add_gate('X', qubit)
    
    def y(self, qubit: int) -> 'Circuit':
        return self.add_gate('Y', qubit)
    
    def z(self, qubit: int) -> 'Circuit':
        return self.add_gate('Z', qubit)
    
    def h(self, qubit: int) -> 'Circuit':
        return self.add_gate('H', qubit)
    
    def s(self, qubit: int) -> 'Circuit':
        return self.add_gate('S', qubit)
    
    def s_dag(self, qubit: int) -> 'Circuit':
        return self.add_gate('S_dag', qubit)
    
    def t(self, qubit: int) -> 'Circuit':
        return self.add_gate('T', qubit)
    
    def t_dag(self, qubit: int) -> 'Circuit':
        return self.add_gate('T_dag', qubit)
    
    def rx(self, qubit: int, theta: float) -> 'Circuit':
        return self.add_gate('RX', qubit, [theta])
    
    def ry(self, qubit: int, theta: float) -> 'Circuit':
        return self.add_gate('RY', qubit, [theta])
    
    def rz(self, qubit: int, theta: float) -> 'Circuit':
        return self.add_gate('RZ', qubit, [theta])
    
    def cnot(self, control: int, target: int) -> 'Circuit':
        return self.add_gate('CNOT', [control, target])
    
    def cx(self, control: int, target: int) -> 'Circuit':
        """CNOT gate (alias for cnot)."""
        return self.cnot(control, target)
    
    def cz(self, control: int, target: int) -> 'Circuit':
        return self.add_gate('CZ', [control, target])
    
    def swap(self, q1: int, q2: int) -> 'Circuit':
        return self.add_gate('SWAP', [q1, q2])
    
    def toffoli(self, c1: int, c2: int, target: int) -> 'Circuit':
        return self.add_gate('TOFFOLI', [c1, c2, target])
    
    def run(self, shots: int = 1024, backend: Optional[Any] = None) -> Dict[str, Any]:
        """
        Execute the circuit and return results.
        
        Args:
            shots: Number of measurement shots (0 for exact statevector)
            backend: Optional backend (defaults to NumPy simulator)
            
        Returns:
            Dict with keys: success, counts, probabilities, statevector
        """
        from .numpy_sim import NumPySimulator
        if backend is None:
            backend = NumPySimulator(num_qubits=self.num_qubits)
        
        # Run the circuit
        if hasattr(backend, 'run_circuit'):
            result = backend.run_circuit(self)
        else:
            result = backend.run(self, shots=shots)
        
        probabilities = result if isinstance(result, dict) else result
        
        # Format output
        output = {
            "success": True,
            "backend": getattr(backend, "name", "NumPySimulator"),
            "shots": shots,
            "probabilities": probabilities,
            "counts": {},
            "statevector": None
        }
        
        # If shots=0, return statevector
        if shots == 0 and hasattr(backend, 'get_state_vector'):
            output["statevector"] = backend.get_state_vector().tolist()
        else:
            # Sample from probabilities
            import random
            states = list(probabilities.keys())
            probs = list(probabilities.values())
            counts = {}
            for _ in range(shots):
                state = random.choices(states, weights=probs)[0]
                counts[state] = counts.get(state, 0) + 1
            output["counts"] = counts
        
        return output
    
    def measure(self, qubit: int, cbit: Optional[int] = None) -> 'Circuit':
        """
        Add a measurement operation.
        
        Args:
            qubit: Qubit to measure
            cbit: Classical bit to store result (defaults to qubit index)
            
        Returns:
            Self for method chaining
        """
        measurement = Measurement(qubit, cbit)
        self.measurements.append(measurement)
        if measurement.cbit + 1 > self.classical_bits:
            self.classical_bits = measurement.cbit + 1
        return self
    
    def measure_all(self) -> 'Circuit':
        """Measure all qubits."""
        for q in range(self.num_qubits):
            self.measure(q, q)
        return self

    def depth(self) -> int:
        """Estimate circuit depth by scheduling gates on qubit availability."""
        if not self.gates:
            return 0

        qubit_depth = [0] * self.num_qubits
        max_depth = 0

        for gate in self.gates:
            gate_depth = 1 + max(qubit_depth[q] for q in gate.qubits)
            for q in gate.qubits:
                qubit_depth[q] = gate_depth
            if gate_depth > max_depth:
                max_depth = gate_depth

        return max_depth

    def count_gates(self) -> Dict[str, int]:
        """Return a gate-name histogram for the circuit."""
        counts: Dict[str, int] = {}
        for gate in self.gates:
            name = gate.name.split('(')[0].upper()
            counts[name] = counts.get(name, 0) + 1
        return counts
    
    def __add__(self, other: 'Circuit') -> 'Circuit':
        """
        Circuit composition (series).
        The other circuit is appended after this one.
        """
        if self.num_qubits != other.num_qubits:
            raise ValueError("Circuits must have same number of qubits to compose")
        
        new_circuit = Circuit(self.num_qubits, f"{self.name}_plus_{other.name}")
        new_circuit.gates = self.gates + other.gates
        new_circuit.measurements = self.measurements + other.measurements
        new_circuit.classical_bits = max(self.classical_bits, other.classical_bits)
        return new_circuit
    
    def __or__(self, other: 'Circuit') -> 'Circuit':
        """
        Parallel composition (tensor product).
        Qubits of other circuit are appended after this circuit's qubits.
        """
        new_num_qubits = self.num_qubits + other.num_qubits
        new_circuit = Circuit(new_num_qubits, f"{self.name}_tensor_{other.name}")
        
        # Add gates from self (qubits unchanged)
        new_circuit.gates = self.gates.copy()
        
        # Add gates from other (qubit indices shifted by self.num_qubits)
        for gate in other.gates:
            new_qubits = [q + self.num_qubits for q in gate.qubits]
            new_gate = Gate(gate.name, new_qubits, gate.matrix, gate.params)
            new_gate.id = gate.id  # Preserve ID for tracking
            new_circuit.gates.append(new_gate)
            
        return new_circuit
    
    def slice(self, start: int, end: Optional[int] = None) -> 'Circuit':
        """
        Get a slice of the circuit (subset of gates).
        
        Args:
            start: Start index (inclusive)
            end: End index (exclusive), or None for rest
            
        Returns:
            New circuit with sliced gates
        """
        if end is None:
            end = len(self.gates)
            
        new_circuit = Circuit(self.num_qubits, f"{self.name}_slice_{start}_{end}")
        new_circuit.gates = self.gates[start:end]
        new_circuit.measurements = self.measurements.copy()
        new_circuit.classical_bits = self.classical_bits
        return new_circuit
    
    def to_qasm(self) -> str:
        """
        Export circuit to OpenQASM 2.0 format.
        """
        lines = []
        lines.append('OPENQASM 2.0;')
        lines.append('include "qelib1.inc";')
        lines.append('')
        lines.append(f'qreg q[{self.num_qubits}];')
        if self.classical_bits > 0:
            lines.append(f'creg c[{self.classical_bits}];')
        lines.append('')
        
        for gate in self.gates:
            if len(gate.qubits) == 1:
                lines.append(f'{gate.name.lower()} q[{gate.qubits[0]}];')
            elif len(gate.qubits) == 2:
                if gate.name == 'CNOT':
                    lines.append(f'cx q[{gate.qubits[0]}],q[{gate.qubits[1]}];')
                else:
                    qargs = ','.join([f'q[{q}]' for q in gate.qubits])
                    lines.append(f'{gate.name.lower()} {qargs};')
            else:
                qargs = ','.join([f'q[{q}]' for q in gate.qubits])
                lines.append(f'{gate.name.lower()} {qargs};')
                
        for meas in self.measurements:
            lines.append(f'measure q[{meas.qubit}] -> c[{meas.cbit}];')
            
        return '\n'.join(lines)
    
    def to_json(self) -> str:
        """Export circuit to JSON format."""
        data = {
            'name': self.name,
            'num_qubits': self.num_qubits,
            'classical_bits': self.classical_bits,
            'gates': [g.to_dict() for g in self.gates],
            'measurements': [m.to_dict() for m in self.measurements]
        }
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Circuit':
        """Import circuit from JSON format."""
        data = json.loads(json_str)
        circuit = cls(data['num_qubits'], data['name'])
        circuit.classical_bits = data.get('classical_bits', 0)
        
        for gate_data in data['gates']:
            gate = Gate.from_dict(gate_data)
            circuit.gates.append(gate)
            
        for meas_data in data.get('measurements', []):
            meas = Measurement(meas_data['qubit'], meas_data['cbit'])
            circuit.measurements.append(meas)
            
        return circuit
    
    def draw(self, output: str = 'text') -> str:
        """
        Draw the circuit.
        
        Args:
            output: Output format ('text', 'ascii')
            
        Returns:
            String representation of the circuit
        """
        if output == 'ascii':
            return self._draw_ascii()
        else:
            return self._draw_text()
    
    def _draw_text(self) -> str:
        """Simple text representation of the circuit."""
        lines = []
        lines.append(f"Circuit: {self.name}")
        lines.append(f"Qubits: {self.num_qubits}, Classical bits: {self.classical_bits}")
        lines.append("-" * 50)
        
        for i, gate in enumerate(self.gates):
            lines.append(f"{i:3d}: {gate}")
            
        if self.measurements:
            lines.append("-" * 50)
            lines.append("Measurements:")
            for meas in self.measurements:
                lines.append(f"  {meas}")
                
        return '\n'.join(lines)
    
    def _draw_ascii(self) -> str:
        """ASCII art representation of the circuit."""
        # Simple wire representation
        wires = {q: [f"q{q}: ─"] for q in range(self.num_qubits)}
        
        for gate in self.gates:
            if len(gate.qubits) == 1:
                q = gate.qubits[0]
                wires[q][-1] = wires[q][-1] + f"──{gate.name}──"
            elif len(gate.qubits) == 2:
                q1, q2 = gate.qubits
                if gate.name == 'CNOT':
                    wires[q1][-1] = wires[q1][-1] + "──●──"
                    wires[q2][-1] = wires[q2][-1] + "──⊕──"
                else:
                    wires[q1][-1] = wires[q1][-1] + f"──{gate.name}──"
                    wires[q2][-1] = wires[q2][-1] + f"──{gate.name}──"
                    
        # End wires
        for q in range(self.num_qubits):
            wires[q][-1] = wires[q][-1] + "─"
            
        return '\n'.join([''.join(w) for w in wires.values()])
    
    def __repr__(self):
        return f"Circuit({self.name}, qubits={self.num_qubits}, gates={len(self.gates)})"

# Example usage and tests
if __name__ == "__main__":
    print("Testing Circuit DSL...")
    
    # Create a simple Bell state circuit
    circ = Circuit(2, "Bell State")
    circ.h(0)
    circ.cnot(0, 1)
    circ.measure_all()
    
    print(circ)
    print("\nText drawing:")
    print(circ.draw('text'))
    print("\nASCII drawing:")
    print(circ.draw('ascii'))
    
    print("\nQASM output:")
    print(circ.to_qasm())
    
    print("\nJSON output:")
    json_str = circ.to_json()
    print(json_str[:200] + "...")
    
    # Test circuit composition
    circ2 = Circuit(2, "Rotation")
    circ2.rx(0, np.pi/4)
    circ2.ry(1, np.pi/3)
    
    combined = circ + circ2
    print(f"\nCombined circuit: {combined}")
    print(f"Total gates: {len(combined.gates)}")
    
    # Test parallel composition
    circ3 = circ | circ2
    print(f"\nParallel circuit: {circ3}")
    print(f"Qubits: {circ3.num_qubits}")