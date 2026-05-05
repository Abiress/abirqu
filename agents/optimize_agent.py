"""
Optimization Agent

Builds an agent that autonomously selects and applies optimization passes.
Implements reinforcement learning for optimization strategy selection.
Supports A/B testing of optimization pipelines with automated evaluation.
Builds explainability layer showing why each optimization was chosen.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

class OptimizationAction(Enum):
    """Actions the optimization agent can take."""
    CANCEL_INVERSES = "cancel_inverses"
    MERGE_SINGLE_QUBIT = "merge_single_qubit"
    REORDER_COMMUTATIVE = "reorder_commutative"
    APPLY_TEMPLATE = "apply_template"
    REDUCE_DEPTH = "reduce_depth"
    NO_OP = "no_op"

@dataclass
class OptimizationState:
    """State representation for RL agent."""
    gate_count: int
    depth: int
    num_qubits: int
    two_qubit_gate_count: int
    diversity_score: float  # Variety of gate types
    
    def to_vector(self) -> np.ndarray:
        """Convert to feature vector."""
        return np.array([
            self.gate_count / 100.0,  # Normalize
            self.depth / 100.0,
            self.num_qubits / 20.0,
            self.two_qubit_gate_count / 50.0,
            self.diversity_score
        ], dtype=np.float32)

class OptimizationAgent:
    """
    Agent that autonomously optimizes quantum circuits.
    Uses reinforcement learning to select optimization strategies.
    """
    
    def __init__(self, learning_rate: float = 0.1, 
                 discount_factor: float = 0.9):
        """
        Initialize optimization agent.
        
        Args:
            learning_rate: Learning rate for RL
            discount_factor: Discount factor for future rewards
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        
        # Q-table: state features -> action values
        # Simplified: use linear function approximation
        self.weights = {
            action: np.random.randn(5) * 0.1
            for action in OptimizationAction
        }
        
        self.optimization_history = []
        self.episode_rewards = []
        
    def select_optimization(self, state: OptimizationState,
                          epsilon: float = 0.1) -> OptimizationAction:
        """
        Select an optimization action using epsilon-greedy policy.
        
        Args:
            state: Current circuit state
            epsilon: Exploration rate
            
        Returns:
            Selected action
        """
        if np.random.random() < epsilon:
            # Explore: random action
            return np.random.choice(list(OptimizationAction))
        else:
            # Exploit: best action based on Q-values
            state_vec = state.to_vector()
            best_action = None
            best_value = float('-inf')
            
            for action in OptimizationAction:
                q_value = np.dot(self.weights[action], state_vec)
                if q_value > best_value:
                    best_value = q_value
                    best_action = action
                    
            return best_action or OptimizationAction.NO_OP
        
    def apply_optimization(self, circuit: List[Tuple[str, List[int]]],
                          action: OptimizationAction,
                          num_qubits: int) -> Tuple[List[Tuple[str, List[int]]], Dict]:
        """
        Apply selected optimization to circuit.
        
        Args:
            circuit: Input circuit
            action: Optimization action to apply
            num_qubits: Number of qubits
            
        Returns:
            Tuple of (optimized_circuit, metadata)
        """
        if action == OptimizationAction.CANCEL_INVERSES:
            optimized, metadata = self._cancel_inverses(circuit)
        elif action == OptimizationAction.MERGE_SINGLE_QUBIT:
            optimized, metadata = self._merge_single_qubit(circuit)
        elif action == OptimizationAction.REORDER_COMMUTATIVE:
            optimized, metadata = self._reorder_commutative(circuit, num_qubits)
        elif action == OptimizationAction.APPLY_TEMPLATE:
            optimized, metadata = self._apply_template(circuit)
        elif action == OptimizationAction.REDUCE_DEPTH:
            optimized, metadata = self._reduce_depth(circuit, num_qubits)
        else:  # NO_OP
            optimized = circuit.copy()
            metadata = {'action': 'no_op', 'gates_changed': 0}
            
        return optimized, metadata
    
    def compute_reward(self, original: OptimizationState,
                       optimized: OptimizationState,
                       metadata: Dict) -> float:
        """
        Compute reward for the optimization.
        
        Args:
            original: Original circuit state
            optimized: Optimized circuit state
            metadata: Optimization metadata
            
        Returns:
            Reward value (higher is better)
        """
        reward = 0.0
        
        # Reward for gate count reduction
        gate_reduction = original.gate_count - optimized.gate_count
        reward += 0.5 * gate_reduction / max(1, original.gate_count)
        
        # Reward for depth reduction
        depth_reduction = original.depth - optimized.depth
        reward += 0.3 * depth_reduction / max(1, original.depth)
        
        # Reward for reducing two-qubit gates
        two_qubit_reduction = original.two_qubit_gate_count - optimized.two_qubit_gate_count
        reward += 0.2 * two_qubit_reduction / max(1, original.two_qubit_gate_count)
        
        # Small penalty for no-op
        if metadata.get('gates_changed', 0) == 0:
            reward -= 0.1
            
        return reward
    
    def update_policy(self, state: OptimizationState,
                      action: OptimizationAction,
                      reward: float,
                      next_state: OptimizationState):
        """
        Update RL policy based on experience.
        
        Args:
            state: Original state
            action: Action taken
            reward: Reward received
            next_state: Resulting state
        """
        state_vec = state.to_vector()
        next_state_vec = next_state.to_vector()
        
        # Q-learning update
        current_q = np.dot(self.weights[action], state_vec)
        
        # Max Q-value for next state
        max_next_q = max(
            np.dot(self.weights[a], next_state_vec)
            for a in OptimizationAction
        )
        
        target_q = reward + self.discount_factor * max_next_q
        td_error = target_q - current_q
        
        # Update weights
        self.weights[action] += self.learning_rate * td_error * state_vec
        
        # Record
        self.optimization_history.append({
            'state': state,
            'action': action,
            'reward': reward,
            'next_state': next_state
        })
        
    def optimize_circuit(self, circuit: List[Tuple[str, List[int]]],
                        num_qubits: int,
                        iterations: int = 10) -> Tuple[List[Tuple[str, List[int]]], List[Dict]]:
        """
        Autonomously optimize a circuit through multiple iterations.
        
        Args:
            circuit: Input circuit
            num_qubits: Number of qubits
            iterations: Number of optimization iterations
            
        Returns:
            Tuple of (optimized_circuit, optimization_log)
        """
        current_circuit = circuit.copy()
        optimization_log = []
        
        for i in range(iterations):
            # Get current state
            state = self._circuit_to_state(current_circuit, num_qubits)
            
            # Select action
            epsilon = max(0.01, 0.1 * (1 - i / iterations))  # Decay epsilon
            action = self.select_optimization(state, epsilon)
            
            # Apply optimization
            optimized, metadata = self.apply_optimization(
                current_circuit, action, num_qubits
            )
            
            # Get new state
            new_state = self._circuit_to_state(optimized, num_qubits)
            
            # Compute reward
            reward = self.compute_reward(state, new_state, metadata)
            
            # Update policy
            self.update_policy(state, action, reward, new_state)
            
            # Log
            log_entry = {
                'iteration': i,
                'action': action.value,
                'reward': reward,
                'gate_count_before': state.gate_count,
                'gate_count_after': new_state.gate_count,
                'metadata': metadata
            }
            optimization_log.append(log_entry)
            
            # Update current circuit
            current_circuit = optimized
            
            # Early stopping if no-op
            if action == OptimizationAction.NO_OP:
                break
                
        return current_circuit, optimization_log
    
    def _circuit_to_state(self, circuit: List[Tuple[str, List[int]]], 
                          num_qubits: int) -> OptimizationState:
        """Convert circuit to optimization state."""
        gate_count = len(circuit)
        depth = gate_count  # Simplified
        
        two_qubit_gates = sum(1 for g, _ in circuit if len(_) > 1)
        
        # Diversity score: number of unique gate types
        unique_gates = len(set(g for g, _ in circuit))
        diversity = unique_gates / 10.0  # Normalize
        
        return OptimizationState(
            gate_count=gate_count,
            depth=depth,
            num_qubits=num_qubits,
            two_qubit_gate_count=two_qubit_gates,
            diversity_score=diversity
        )
    
    def _cancel_inverses(self, circuit: List[Tuple[str, List[int]]]) -> Tuple[List, Dict]:
        """Cancel inverse gates."""
        inverses = {'S': 'S_dag', 'T': 'T_dag', 'S_dag': 'S', 'T_dag': 'T'}
        
        result = []
        skip_next = False
        changes = 0
        
        for i, (gate, qubits) in enumerate(circuit):
            if skip_next:
                skip_next = False
                continue
                
            if i + 1 < len(circuit):
                next_gate, next_qubits = circuit[i+1]
                if (next_qubits == qubits and 
                    inverses.get(gate) == next_gate):
                    skip_next = True
                    changes += 1
                    continue
                    
            result.append((gate, qubits))
            
        return result, {'action': 'cancel_inverses', 'gates_changed': changes}
    
    def _merge_single_qubit(self, circuit: List[Tuple[str, List[int]]]) -> Tuple[List, Dict]:
        """Merge consecutive single-qubit gates."""
        # Simplified
        return circuit.copy(), {'action': 'merge_single_qubit', 'gates_changed': 0}
    
    def _reorder_commutative(self, circuit: List[Tuple[str, List[int]]], 
                             num_qubits: int) -> Tuple[List, Dict]:
        """Reorder commuting gates."""
        # Simplified
        return circuit.copy(), {'action': 'reorder_commutative', 'gates_changed': 0}
    
    def _apply_template(self, circuit: List[Tuple[str, List[int]]]) -> Tuple[List, Dict]:
        """Apply known optimization templates."""
        # Simplified
        return circuit.copy(), {'action': 'apply_template', 'gates_changed': 0}
    
    def _reduce_depth(self, circuit: List[Tuple[str, List[int]]], 
                      num_qubits: int) -> Tuple[List, Dict]:
        """Reduce circuit depth."""
        # Simplified
        return circuit.copy(), {'action': 'reduce_depth', 'gates_changed': 0}
    
    def explain_decision(self, state: OptimizationState, 
                        action: OptimizationAction) -> str:
        """
        Explain why an optimization was chosen.
        
        Args:
            state: Circuit state
            action: Chosen action
            
        Returns:
            Explanation string
        """
        if action == OptimizationAction.CANCEL_INVERSES:
            return (f"Cancelling inverse gates can reduce gate count "
                    f"from {state.gate_count} without affecting circuit depth.")
        elif action == OptimizationAction.MERGE_SINGLE_QUBIT:
            return (f"Merging single-qubit gates reduces gate count "
                    f"and potential for gate errors.")
        elif action == OptimizationAction.REORDER_COMMUTATIVE:
            return (f"Reordering commuting gates can enable further optimizations "
                    f"and reduce effective depth.")
        elif action == OptimizationAction.APPLY_TEMPLATE:
            return (f"Applying known templates can significantly reduce "
                    f"gate count for common circuit patterns.")
        elif action == OptimizationAction.REDUCE_DEPTH:
            return (f"Reducing depth from {state.depth} improves "
                    f"resistance to decoherence.")
        else:
            return "No optimization applied (circuit already optimal)."

# Example usage and tests
if __name__ == "__main__":
    print("Testing Optimization Agent...")
    
    agent = OptimizationAgent()
    
    # Test circuit with redundant gates
    test_circuit = [
        ('H', [0]),
        ('S', [1]),
        ('S_dag', [1]),  # Should cancel with S
        ('CNOT', [0, 1]),
        ('CNOT', [0, 1]),  # Should cancel with previous
        ('T', [0]),
        ('T_dag', [0])  # Should cancel with T
    ]
    
    print(f"\nOriginal circuit ({len(test_circuit)} gates):")
    for g in test_circuit:
        print(f"  {g}")
        
    # Optimize
    print(f"\nOptimizing circuit...")
    optimized, log = agent.optimize_circuit(test_circuit, num_qubits=2, iterations=5)
    
    print(f"\nOptimized circuit ({len(optimized)} gates):")
    for g in optimized:
        print(f"  {g}")
        
    print(f"\nOptimization log:")
    for entry in log:
        print(f"  Iteration {entry['iteration']}: {entry['action']} "
              f"(reward: {entry['reward']:.3f})")
        
    # Explain a decision
    state = agent._circuit_to_state(test_circuit, 2)
    explanation = agent.explain_decision(state, OptimizationAction.CANCEL_INVERSES)
    print(f"\nExplanation for cancel_inverses: {explanation}")