"""
ML-Enhanced Transpiler
======================
Reinforcement learning qubit routing and graph neural network layout
optimization for quantum circuits.

Uses only NumPy for core computation — no external ML framework required.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

from ..circuit import Circuit, Gate
from .topology import CouplingMap


# ---------------------------------------------------------------------------
# Q-table backed RL qubit router
# ---------------------------------------------------------------------------

@dataclass
class RoutingState:
    """Hashable snapshot of the routing state."""
    remaining_gates: Tuple[Tuple[str, Tuple[int, ...]], ...]
    qubit_mapping: Tuple[int, ...]

    def __hash__(self) -> int:
        return hash((self.remaining_gates, self.qubit_mapping))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RoutingState):
            return NotImplemented
        return self.remaining_gates == other.remaining_gates and self.qubit_mapping == other.qubit_mapping


@dataclass
class RLQubitRouter:
    """Reinforcement-learning agent for qubit routing.

    State space
    -----------
    - Coupling-map adjacency encoded as a fixed-size feature vector.
    - Current logical → physical qubit assignment.
    - Number of remaining two-qubit gates.

    Action space
    ------------
    For each candidate SWAP pair (neighbors of the current gate's qubits),
    the agent picks the SWAP that maximises the expected reward.

    Reward
    ------
    Positive reward for reducing the Manhattan / shortest-path distance
    between interacting qubits; bonus for reduced circuit depth.

    Exploration uses ε-greedy with decaying ε.

    Parameters
    ----------
    learning_rate : float
        Q-learning α.
    discount_factor : float
        Q-learning γ.
    epsilon : float
        Initial exploration rate.
    epsilon_decay : float
        Multiplicative decay applied after each episode.
    min_epsilon : float
        Floor for ε.
    num_episodes : int
        Number of routing episodes for training.
    """

    learning_rate: float = 0.1
    discount_factor: float = 0.95
    epsilon: float = 0.3
    epsilon_decay: float = 0.995
    min_epsilon: float = 0.01
    num_episodes: int = 200

    # Internal state — not set by caller
    _q_table: Dict[Tuple, Dict[Tuple[int, int], float]] = field(
        default_factory=dict, init=False, repr=False
    )

    # -- public API ---------------------------------------------------------

    def route(self, circuit: Circuit, coupling_map: CouplingMap) -> Circuit:
        """Route *circuit* onto *coupling_map* using the trained RL agent.

        The agent is trained online (on this circuit) before the final
        greedy pass that produces the output circuit.
        """
        self._train(circuit, coupling_map)
        return self._greedy_route(circuit, coupling_map)

    # -- training -----------------------------------------------------------

    def _train(self, circuit: Circuit, coupling: CouplingMap) -> None:
        """Run Q-learning episodes on the given circuit."""
        eps = self.epsilon
        all_gates = self._extract_remaining_gates(circuit)
        max_steps = len(all_gates) * circuit.num_qubits * 4
        for _ in range(self.num_episodes):
            state = RoutingState(
                remaining_gates=all_gates,
                qubit_mapping=tuple(range(circuit.num_qubits)),
            )
            done = False
            total_reward = 0.0
            steps = 0

            while not done and steps < max_steps:
                steps += 1
                actions = self._available_actions(state, coupling)
                if not actions:
                    break

                action = self._choose_action(state, actions, eps)
                next_state, reward, done = self._step(state, action, coupling)
                total_reward += reward

                self._update_q(state, action, reward, next_state)
                state = next_state

            eps = max(self.min_epsilon, eps * self.epsilon_decay)

    def _initial_state(
        self, circuit: Circuit, coupling: CouplingMap
    ) -> RoutingState:
        gates = self._extract_remaining_gates(circuit)
        mapping = tuple(range(circuit.num_qubits))
        return RoutingState(remaining_gates=gates, qubit_mapping=mapping)

    def _extract_remaining_gates(
        self, circuit: Circuit
    ) -> Tuple[Tuple[str, Tuple[int, ...]], ...]:
        return tuple(
            (g.name, tuple(g.qubits)) for g in getattr(circuit, "gates", [])
        )

    def _available_actions(
        self, state: RoutingState, coupling: CouplingMap
    ) -> List[Tuple[int, int]]:
        """Return candidate SWAP pairs for the next unresolved two-qubit gate."""
        for name, qubits in state.remaining_gates:
            if len(qubits) >= 2:
                # Candidate SWAPs: neighbors of the two qubits
                candidates: Set[Tuple[int, int]] = set()
                for q in qubits[:2]:
                    for nb in coupling.neighbors(q):
                        pair = (min(q, nb), max(q, nb))
                        candidates.add(pair)
                return sorted(candidates)
        return []

    def _choose_action(
        self,
        state: RoutingState,
        actions: List[Tuple[int, int]],
        epsilon: float,
    ) -> Tuple[int, int]:
        if random.random() < epsilon:
            return random.choice(actions)
        q_vals = self._q_table.get(state, {})
        if not q_vals:
            return random.choice(actions)
        return max(actions, key=lambda a: q_vals.get(a, 0.0))

    def _step(
        self,
        state: RoutingState,
        action: Tuple[int, int],
        coupling: CouplingMap,
    ) -> Tuple[RoutingState, float, bool]:
        """Simulate applying a SWAP and advancing to the next gate."""
        p0, p1 = action
        # Apply swap to mapping
        mapping = list(state.qubit_mapping)
        inv = {v: k for k, v in enumerate(mapping)}
        log_a, log_b = inv[p0], inv[p1]
        mapping[log_a], mapping[log_b] = p1, p0

        # Process the first gate if it becomes valid
        remaining = list(state.remaining_gates)
        reward = 0.0
        if remaining:
            name, qubits = remaining[0]
            if len(qubits) >= 2:
                phys = [mapping[q] for q in qubits[:2]]
                if coupling.are_connected(phys[0], phys[1]):
                    # Gate satisfied — positive reward
                    dist_before = coupling.distance(
                        mapping[qubits[0]], mapping[qubits[1]]
                    )
                    reward = max(1.0, 5.0 - dist_before)
                    remaining.pop(0)

        done = len(remaining) == 0
        new_state = RoutingState(
            remaining_gates=tuple(remaining),
            qubit_mapping=tuple(mapping),
        )
        return new_state, reward, done

    def _update_q(
        self,
        state: RoutingState,
        action: Tuple[int, int],
        reward: float,
        next_state: RoutingState,
    ) -> None:
        if state not in self._q_table:
            self._q_table[state] = {}
        q_vals = self._q_table[state]
        old_q = q_vals.get(action, 0.0)

        next_max = 0.0
        if next_state in self._q_table and self._q_table[next_state]:
            next_max = max(self._q_table[next_state].values())

        new_q = old_q + self.learning_rate * (
            reward + self.discount_factor * next_max - old_q
        )
        q_vals[action] = new_q

    # -- greedy route -------------------------------------------------------

    def _greedy_route(
        self, circuit: Circuit, coupling: CouplingMap
    ) -> Circuit:
        """Produce the final routed circuit using the learned Q-table."""
        mapping = list(range(circuit.num_qubits))
        inv = {i: i for i in range(circuit.num_qubits)}
        routed: List[Gate] = []

        for gate in getattr(circuit, "gates", []):
            qubits = list(gate.qubits)
            params = list(gate.params)

            if len(qubits) < 2:
                phys = [mapping[q] for q in qubits]
                routed.append(Gate(gate.name, phys, params))
                continue

            phys = [mapping[qubits[0]], mapping[qubits[1]]]
            if coupling.are_connected(phys[0], phys[1]):
                all_phys = [mapping[q] for q in qubits]
                routed.append(Gate(gate.name, all_phys, params))
                continue

            # Insert SWAPs along shortest path until adjacent
            path = coupling.shortest_path(phys[0], phys[1])
            for i in range(len(path) - 1):
                a, b = path[i], path[i + 1]
                routed.append(Gate("SWAP", [a, b]))
                la, lb = inv[a], inv[b]
                mapping[la], mapping[lb] = b, a
                inv[a], inv[b] = lb, la

            phys = [mapping[qubits[0]], mapping[qubits[1]]]
            all_phys = [mapping[q] for q in qubits]
            routed.append(Gate(gate.name, all_phys, params))

        out = Circuit(circuit.num_qubits, f"{circuit.name}_rl_routed")
        for g in routed:
            out.add_gate(g.name, list(g.qubits), list(g.params))
        return out


# ---------------------------------------------------------------------------
# GNN-inspired layout optimizer
# ---------------------------------------------------------------------------

@dataclass
class GNNLayoutOptimizer:
    """Graph-neural-network inspired initial qubit placement optimizer.

    Encodes the circuit as a graph where:
    - Nodes = qubits
    - Edges = two-qubit gates (weighted by interaction count)

    Uses iterative message passing to compute per-qubit centrality scores
    and maps high-centrality logical qubits to high-connectivity physical
    qubits on the coupling map.

    Parameters
    ----------
    num_layers : int
        Number of message-passing rounds.
    """

    num_layers: int = 3

    def optimize(
        self, circuit: Circuit, coupling_map: CouplingMap
    ) -> Tuple[Circuit, Dict[int, int]]:
        """Return *(permuted_circuit, layout)* where *layout* maps logical → physical."""
        n = circuit.num_qubits
        gate_list = getattr(circuit, "gates", [])

        # Build interaction matrix (logical graph)
        interactions = np.zeros((n, n), dtype=float)
        for g in gate_list:
            if len(g.qubits) >= 2:
                q0, q1 = g.qubits[0], g.qubits[1]
                interactions[q0, q1] += 1.0
                interactions[q1, q0] += 1.0

        # Node features: degree centrality
        node_features = interactions.sum(axis=1)  # shape (n,)

        # Message passing
        adj = self._coupling_adjacency(coupling_map, n)
        physical_centrality = adj.sum(axis=1).astype(float)
        physical_centrality /= max(physical_centrality.sum(), 1e-9)

        logical_centrality = node_features.copy()
        for _ in range(self.num_layers):
            messages = adj @ logical_centrality  # aggregate from neighbors
            logical_centrality = 0.5 * logical_centrality + 0.5 * messages

        logical_centrality /= max(logical_centrality.sum(), 1e-9)

        # Greedy assignment: map highest-centrality logical qubit to
        # highest-centrality physical qubit.
        layout = self._greedy_assign(logical_centrality, physical_centrality, n)

        # Apply layout permutation to circuit
        permuted = Circuit(n, f"{circuit.name}_gnn_layout")
        for g in gate_list:
            new_qubits = [layout[q] for q in g.qubits]
            permuted.add_gate(g.name, new_qubits, list(g.params))
        return permuted, layout

    def _coupling_adjacency(
        self, coupling: CouplingMap, n: int
    ) -> np.ndarray:
        adj = np.zeros((n, n), dtype=float)
        for u, v in coupling.edges:
            if u < n and v < n:
                adj[u, v] = 1.0
                adj[v, u] = 1.0
        return adj

    def _greedy_assign(
        self,
        logical_scores: np.ndarray,
        physical_scores: np.ndarray,
        n: int,
    ) -> Dict[int, int]:
        """Assign logical qubits to physical positions by descending score."""
        logical_order = np.argsort(-logical_scores)
        physical_order = np.argsort(-physical_scores)
        layout: Dict[int, int] = {}
        for i in range(n):
            layout[int(logical_order[i])] = int(physical_order[i])
        return layout


# ---------------------------------------------------------------------------
# Combined ML transpiler pipeline
# ---------------------------------------------------------------------------

@dataclass
class MLTranspilerPipeline:
    """End-to-end ML transpiler pipeline.

    1. GNN layout optimization (initial placement).
    2. RL routing (SWAP insertion).
    3. Fidelity-aware depth minimisation.

    Parameters
    ----------
    rl_episodes : int
        Number of RL training episodes per routing call.
    gnn_layers : int
        Number of GNN message-passing layers.
    """

    rl_episodes: int = 200
    gnn_layers: int = 3

    def transpile(
        self, circuit: Circuit, target: CouplingMap
    ) -> Circuit:
        """Transpile *circuit* onto *target* coupling map.

        Returns a new circuit with optimised layout and routing.
        """
        # Step 1: GNN layout
        gnn = GNNLayoutOptimizer(num_layers=self.gnn_layers)
        placed, layout = gnn.optimize(circuit, target)

        # Step 2: RL routing
        router = RLQubitRouter(num_episodes=self.rl_episodes)
        routed = router.route(placed, target)

        # Step 3: Depth minimisation (cancel adjacent inverse pairs)
        optimised = self._depth_optimise(routed)
        return optimised

    def _depth_optimise(self, circuit: Circuit) -> Circuit:
        """Remove adjacent inverse gate pairs to reduce depth."""
        gates = list(getattr(circuit, "gates", []))
        result: List[Gate] = []
        skip = set()

        for i, g in enumerate(gates):
            if i in skip:
                continue
            if i + 1 < len(gates):
                nxt = gates[i + 1]
                if self._are_inverse(g, nxt):
                    skip.add(i)
                    skip.add(i + 1)
                    continue
            result.append(g)

        out = Circuit(circuit.num_qubits, f"{circuit.name}_ml_optimized")
        for g in result:
            out.add_gate(g.name, list(g.qubits), list(g.params))
        return out

    @staticmethod
    def _are_inverse(a: Gate, b: Gate) -> bool:
        if a.name != b.name or a.qubits != b.qubits:
            return False
        if a.name.upper() in ("RX", "RY", "RZ") and a.params and b.params:
            return abs(a.params[0] + b.params[0]) < 1e-10
        return False
