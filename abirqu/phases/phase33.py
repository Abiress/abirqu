"""
Phase 3.3 Integration for AbirQu
Copyright 2026 Abir Maheshwari
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple


class GateFidelityTracker:
    def __init__(self, gate_names: Sequence[str], target_fidelity: float):
        self.ewma = {g: float(target_fidelity) for g in gate_names}
        self.drift_alerts: List[str] = []
        self._alpha = 0.3

    def record_rb_measurement(self, gate_name: str, fidelity: float) -> None:
        old = self.ewma[gate_name]
        new = self._alpha * fidelity + (1 - self._alpha) * old
        self.ewma[gate_name] = new
        if new < 0.993:
            self.drift_alerts.append(gate_name)

    def get_worst_gates(self, n: int):
        return sorted(self.ewma.items(), key=lambda x: x[1])[:n]


class DynamicErrorSuppressor:
    def __init__(self, tracker: GateFidelityTracker):
        self.tracker = tracker

    def suppress_all(self):
        strategies = {}
        overhead = 1.0
        for g, f in self.tracker.ewma.items():
            if f < 0.990:
                strategies[g] = {"strategy": "Dynamical Decoupling (XY8)", "overhead_factor": 1.5}
                overhead = max(overhead, 1.5)
            elif f < 0.995:
                strategies[g] = {"strategy": "Pauli Twirling", "overhead_factor": 1.1}
                overhead = max(overhead, 1.1)
            else:
                strategies[g] = {"strategy": "None", "overhead_factor": 1.0}
        return {"per_gate_strategies": strategies, "combined_overhead_factor": overhead}


class RecalibrationAgent:
    def __init__(self, gate_names: Sequence[str], target_fidelity: float, recalibration_threshold: float):
        self.tracker = GateFidelityTracker(gate_names, target_fidelity)
        self.recalibration_threshold = recalibration_threshold

    def run_autonomous(self, num_cycles: int):
        recal = 0
        for i in range(num_cycles):
            for g in list(self.tracker.ewma.keys()):
                fid = 0.999 - 0.0012 * i if g == "CZ" else 0.999 - 0.00005 * i
                self.tracker.record_rb_measurement(g, fid)
                if self.tracker.ewma[g] < self.recalibration_threshold:
                    self.tracker.ewma[g] = 0.999
                    recal += 1
        return {
            "total_cycles": num_cycles,
            "total_recalibrations": recal,
            "total_drift_alerts": len(self.tracker.drift_alerts),
            "final_gate_fidelities": dict(self.tracker.ewma),
        }


class NeutralAtomTweezerArray:
    def __init__(self, num_sites: int, num_atoms: int, zone_radius_um: float):
        self.num_sites = num_sites
        self.num_atoms = num_atoms
        self.zone_radius_um = zone_radius_um
        self.positions = list(range(num_atoms))

    def get_connectivity_graph(self):
        return {
            "num_qubits": self.num_atoms,
            "num_edges": max(0, self.num_atoms - 1),
            "edges": [(i, i + 1) for i in range(max(0, self.num_atoms - 1))],
        }

    def optimize_layout_for_circuit(self, required_edges: Sequence[Tuple[int, int]]):
        import numpy as np
        from collections import defaultdict
        
        w = int(np.ceil(np.sqrt(self.num_atoms)))
        h = int(np.ceil(self.num_atoms / w))
        
        site_coords = {s: (s % w, s // w) for s in range(self.num_sites)}
        
        adj = defaultdict(list)
        for u, v in required_edges:
            if u < self.num_atoms and v < self.num_atoms:
                adj[u].append(v)
                adj[v].append(u)
                
        qubits_by_deg = sorted(range(self.num_atoms), key=lambda q: len(adj[q]), reverse=True)
        placed = {}
        occupied = set()
        
        for q in qubits_by_deg:
            best_site = -1
            best_adj_score = -1
            placed_neighbors = [placed[nb] for nb in adj[q] if nb in placed]
            
            candidates = []
            if placed_neighbors:
                for pn in placed_neighbors:
                    px, py = site_coords[pn]
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = px + dx, py + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            ns = ny * w + nx
                            if ns < self.num_sites and ns not in occupied:
                                candidates.append(ns)
                                
            if not candidates:
                candidates = [s for s in range(self.num_sites) if s not in occupied]
                
            for s in candidates:
                if s in occupied:
                    continue
                sx, sy = site_coords[s]
                score = 0
                for pn in placed_neighbors:
                    pnx, pny = site_coords[pn]
                    if abs(sx - pnx) + abs(sy - pny) == 1:
                        score += 1
                if score > best_adj_score:
                    best_adj_score = score
                    best_site = s
                    
            if best_site == -1:
                for s in range(self.num_sites):
                    if s not in occupied:
                        best_site = s
                        break
                        
            placed[q] = best_site
            occupied.add(best_site)
            
        natively_satisfied = 0
        for u, v in required_edges:
            if u in placed and v in placed:
                pu, pv = placed[u], placed[v]
                ux, uy = site_coords[pu]
                vx, vy = site_coords[pv]
                if abs(ux - vx) + abs(uy - vy) == 1:
                    natively_satisfied += 1
                    
        satisfaction_rate = natively_satisfied / max(1, len(required_edges))
        
        pitch = 5.0
        total_dist = 0.0
        max_dist = 0.0
        for q in range(self.num_atoms):
            if q in placed:
                init_x, init_y = site_coords[q]
                new_x, new_y = site_coords[placed[q]]
                dist = pitch * np.sqrt((init_x - new_x)**2 + (init_y - new_y)**2)
                total_dist += dist
                max_dist = max(max_dist, dist)
                
        rearrangement_time = 100.0 + 2.0 * max_dist
        
        return {
            "required_edges": len(required_edges),
            "natively_satisfied": natively_satisfied,
            "satisfaction_rate": satisfaction_rate,
            "rearrangement": {
                "rearrangement_time_us": float(rearrangement_time),
                "total_distance_um": float(total_dist),
                "mapping": placed
            }
        }

    def rearrange_atoms(self, new_sites: Sequence[int]):
        self.positions = list(new_sites)
        return {"time_us": 200, "distance_um": 50.0}


class AdaptiveCompilerPass:
    def __init__(self, topology: Dict[str, Any]):
        self.topology = topology

    def route_circuit(self, gates: Sequence[Tuple[int, int]]):
        from collections import deque
        num_qubits = self.topology.get("num_qubits", 10)
        edges = self.topology.get("edges", [])
        
        adj = {i: [] for i in range(num_qubits)}
        for x, y in edges:
            if x < num_qubits and y < num_qubits:
                adj[x].append(y)
                adj[y].append(x)
                
        physical_to_logical = {i: i for i in range(num_qubits)}
        logical_to_physical = {i: i for i in range(num_qubits)}
        
        def find_path(start, end):
            if start == end:
                return [start]
            queue = deque([[start]])
            visited = {start}
            while queue:
                path = queue.popleft()
                curr = path[-1]
                if curr == end:
                    return path
                for neighbor in adj.get(curr, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(path + [neighbor])
            return []
            
        total_swaps = 0
        routed_gates = []
        
        for u, v in gates:
            if u >= num_qubits or v >= num_qubits:
                continue
            pu = logical_to_physical[u]
            pv = logical_to_physical[v]
            
            path = find_path(pu, pv)
            if not path:
                continue
                
            for step in range(len(path) - 2):
                w1 = path[step]
                w2 = path[step + 1]
                
                l1 = physical_to_logical[w1]
                l2 = physical_to_logical[w2]
                
                logical_to_physical[l1] = w2
                logical_to_physical[l2] = w1
                physical_to_logical[w1] = l2
                physical_to_logical[w2] = l1
                
                routed_gates.append(("SWAP", w1, w2))
                total_swaps += 1
                
            new_pu = logical_to_physical[u]
            new_pv = logical_to_physical[v]
            routed_gates.append(("GATE", new_pu, new_pv))
            
        return {
            "original_gates": len(gates),
            "routed_gates": len(routed_gates),
            "total_swaps_inserted": total_swaps,
            "swap_overhead": f"{int(100 * total_swaps / max(1, len(gates)))}%",
            "final_mapping": {l: p for l, p in logical_to_physical.items()},
        }

    def update_topology(self, new_topology: Dict[str, Any]):
        old = self.topology.get("num_edges", 0)
        self.topology = new_topology
        return {"old_edges": old, "new_edges": new_topology.get("num_edges", 0)}
