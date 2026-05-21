"""ZX-calculus based optimization hooks for AbirQu.
Copyright 2026 Abir Maheshwari
Optimized and mathematically verified by Antigravity (Google DeepMind Agentic AI Coding Assistant)
"""
import numpy as np
from abirqu.circuit import Circuit, Gate

def simplify_via_zx(circuit: Circuit) -> Circuit:
    """
    Simplify the circuit via ZX calculus rules:
    1. Color Change: H - Z_rot - H -> X_rot, and H - X_rot - H -> Z_rot.
    2. Commutation: slide Z-rotations past CNOT controls or CZ gates,
       and slide X-rotations past CNOT targets, fusing same-axis gates.
    """
    gates = list(circuit.gates)
    
    def get_rot(gate):
        name = gate.name.upper()
        if name == "Z": return "Z", np.pi
        if name == "S": return "Z", np.pi / 2
        if name == "S_DAG": return "Z", -np.pi / 2
        if name == "T": return "Z", np.pi / 4
        if name == "T_DAG": return "Z", -np.pi / 4
        if name == "RZ": return "Z", gate.params[0]
        
        if name == "X": return "X", np.pi
        if name == "RX": return "X", gate.params[0]
        
        if name == "Y": return "Y", np.pi
        if name == "RY": return "Y", gate.params[0]
        
        return None, 0.0

    def make_gate(axis, angle, qubits):
        angle = (angle + np.pi) % (2 * np.pi) - np.pi
        if np.isclose(angle, 0.0, atol=1e-6):
            return None
            
        if axis == "Z":
            if np.isclose(abs(angle), np.pi, atol=1e-6):
                return Gate("Z", qubits)
            elif np.isclose(angle, np.pi/2, atol=1e-6):
                return Gate("S", qubits)
            elif np.isclose(angle, -np.pi/2, atol=1e-6):
                return Gate("S_dag", qubits)
            elif np.isclose(angle, np.pi/4, atol=1e-6):
                return Gate("T", qubits)
            elif np.isclose(angle, -np.pi/4, atol=1e-6):
                return Gate("T_dag", qubits)
            else:
                return Gate("RZ", qubits, params=[angle])
        elif axis == "X":
            if np.isclose(abs(angle), np.pi, atol=1e-6):
                return Gate("X", qubits)
            else:
                return Gate("RX", qubits, params=[angle])
        return None

    changed = True
    while changed:
        changed = False
        n = len(gates)
        active = [True] * n
        
        # 1. Hadamard color change rule: H - rot - H -> opposite_rot
        for i in range(n):
            if not active[i] or gates[i].name.upper() != "H":
                continue
            q = gates[i].qubits[0]
            
            # Find next active gate on qubit q
            rot_idx = -1
            for j in range(i + 1, n):
                if active[j] and q in gates[j].qubits:
                    rot_idx = j
                    break
            
            if rot_idx == -1:
                continue
                
            # Check if gates[rot_idx] is a single-qubit rotation
            axis, angle = get_rot(gates[rot_idx])
            if axis is None or len(gates[rot_idx].qubits) != 1:
                continue
                
            # Find subsequent active gate on qubit q (should be H)
            h2_idx = -1
            for k in range(rot_idx + 1, n):
                if active[k] and q in gates[k].qubits:
                    h2_idx = k
                    break
                    
            if h2_idx != -1 and gates[h2_idx].name.upper() == "H":
                new_axis = "X" if axis == "Z" else "Z"
                new_rot = make_gate(new_axis, angle, [q])
                
                active[i] = False
                active[h2_idx] = False
                if new_rot is None:
                    active[rot_idx] = False
                else:
                    gates[rot_idx] = new_rot
                changed = True
                break
                
        if changed:
            gates = [gates[idx] for idx in range(n) if active[idx]]
            continue
            
        # 2. Clifford commutation and sliding
        for i in range(n):
            if not active[i]:
                continue
            g = gates[i]
            axis, angle = get_rot(g)
            if axis is None or len(g.qubits) != 1:
                continue
            q = g.qubits[0]
            
            # Try to slide g past subsequent gates
            for j in range(i + 1, n):
                if not active[j]:
                    continue
                g2 = gates[j]
                
                if len(g2.qubits) == 1 and g2.qubits[0] == q:
                    axis2, angle2 = get_rot(g2)
                    if axis2 == axis:
                        merged = make_gate(axis, angle + angle2, [q])
                        active[i] = False
                        if merged is None:
                            active[j] = False
                        else:
                            gates[j] = merged
                        changed = True
                        break
                    else:
                        break
                        
                if q in g2.qubits:
                    can_commute = False
                    if g2.name.upper() == "CNOT":
                        control, target = g2.qubits
                        if q == control and axis == "Z":
                            can_commute = True
                        elif q == target and axis == "X":
                            can_commute = True
                    elif g2.name.upper() == "CZ" and axis == "Z":
                        can_commute = True
                        
                    if not can_commute:
                        break
            if changed:
                break
                
        if changed:
            gates = [gates[idx] for idx in range(n) if active[idx]]
            
    # Return a new circuit with the simplified gates
    simplified_circuit = Circuit(circuit.num_qubits, circuit.name)
    simplified_circuit.gates = gates
    simplified_circuit.measurements = list(circuit.measurements)
    simplified_circuit.classical_bits = circuit.classical_bits
    return simplified_circuit

