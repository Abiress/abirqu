"""Peephole optimization passes for quantum circuits.
Copyright 2026 Abir Maheshwari
Optimized and mathematically verified by Antigravity (Google DeepMind Agentic AI Coding Assistant)
"""
import numpy as np
from abirqu.circuit import Gate

def optimize_paired_gates(gates):
    """
    Cancel adjacent inverse gates and merge adjacent rotation gates of the same type,
    sliding them past commuting intermediate gates that act on disjoint qubits.
    """
    changed = True
    current_gates = list(gates)
    
    def get_rotation_info(gate):
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
        elif axis == "Y":
            if np.isclose(abs(angle), np.pi, atol=1e-6):
                return Gate("Y", qubits)
            else:
                return Gate("RY", qubits, params=[angle])
        return None

    while changed:
        changed = False
        n = len(current_gates)
        active = [True] * n
        
        for i in range(n):
            if not active[i]:
                continue
                
            g1 = current_gates[i]
            for j in range(i + 1, n):
                if not active[j]:
                    continue
                g2 = current_gates[j]
                
                # Check if g1 commutes with all active intermediate gates
                can_slide = True
                for k in range(i + 1, j):
                    if active[k]:
                        gk = current_gates[k]
                        if not set(g1.qubits).isdisjoint(gk.qubits):
                            # Not disjoint, check if they are same-axis rotations on same qubit
                            g1_axis, _ = get_rotation_info(g1)
                            gk_axis, _ = get_rotation_info(gk)
                            if g1_axis is not None and gk_axis is not None and g1.qubits == gk.qubits and g1_axis == gk_axis:
                                continue
                            can_slide = False
                            break
                            
                if not can_slide:
                    break
                
                # If they act on the same qubits, try to fuse/cancel
                q1 = g1.qubits
                q2 = g2.qubits
                same_qubits = (q1 == q2) or (g1.name in ("CZ", "SWAP") and sorted(q1) == sorted(q2))
                
                if same_qubits:
                    # Identical self-inverse gates
                    if g1.name.upper() == g2.name.upper() and g1.name.upper() in ("X", "Y", "Z", "H", "CNOT", "CZ", "SWAP", "TOFFOLI"):
                        active[i] = False
                        active[j] = False
                        changed = True
                        break
                    
                    # Inverse pairs
                    g1_name = g1.name.upper()
                    g2_name = g2.name.upper()
                    if (g1_name == "S" and g2_name == "S_DAG") or (g1_name == "S_DAG" and g2_name == "S") or \
                       (g1_name == "T" and g2_name == "T_DAG") or (g1_name == "T_DAG" and g2_name == "T"):
                        active[i] = False
                        active[j] = False
                        changed = True
                        break
                        
                    # Rotations on same axis
                    axis1, ang1 = get_rotation_info(g1)
                    axis2, ang2 = get_rotation_info(g2)
                    if axis1 is not None and axis1 == axis2:
                        merged = make_gate(axis1, ang1 + ang2, q1)
                        if merged is None:
                            active[i] = False
                            active[j] = False
                        else:
                            current_gates[i] = merged
                            active[j] = False
                        changed = True
                        break
                        
        if changed:
            current_gates = [current_gates[idx] for idx in range(n) if active[idx]]
            
    return current_gates

