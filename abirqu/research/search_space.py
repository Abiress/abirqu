"""
Task 15.1 — Algorithm Search Space Explorer.

Systematic explorer, genetic programming, reinforcement learning, novelty detection.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import random


class SearchStrategy(Enum):
    """Search strategies for algorithm discovery."""
    GENETIC = "genetic"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    SYSTEMATIC = "systematic"
    RANDOM = "random"


@dataclass
class SearchResult:
    """Result of algorithm search."""
    algorithm: Any
    fitness: float
    complexity: int  # Gate count or similar metric.
    novelty_score: float  # 0-1, higher = more novel.
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'fitness': self.fitness,
            'complexity': self.complexity,
            'novelty_score': self.novelty_score,
            'metadata': self.metadata
        }


class AlgorithmSearchSpace:
    """Systematic explorer of quantum algorithm design space."""
    
    def __init__(self, num_qubits: int = 3, max_depth: int = 10):
        self.num_qubits = num_qubits
        self.max_depth = max_depth
        self.gate_set = ['h', 'x', 'y', 'z', 'cnot', 'rx', 'ry', 'rz']
        self.visited_circuits: List[str] = []
    
    def explore(self, strategy: SearchStrategy = SearchStrategy.SYSTEMATIC,
               num_candidates: int = 100) -> List[SearchResult]:
        """
        Explore the algorithm design space.
        
        Args:
            strategy: Search strategy to use.
            num_candidates: Number of candidates to generate.
            
        Returns:
            List of SearchResult.
        """
        if strategy == SearchStrategy.SYSTEMATIC:
            return self._systematic_explore(num_candidates)
        elif strategy == SearchStrategy.RANDOM:
            return self._random_explore(num_candidates)
        elif strategy == SearchStrategy.GENETIC:
            return self._genetic_explore(num_candidates)
        else:
            return self._random_explore(num_candidates)
    
    def _systematic_explore(self, num: int) -> List[SearchResult]:
        """Systematic exploration of circuit space."""
        results = []
        # Generate circuits with increasing depth.
        for depth in range(1, min(self.max_depth + 1, num + 1)):
            circuit = self._generate_circuit(depth)
            fitness = self._evaluate_fitness(circuit)
            novelty = self._compute_novelty(circuit)
            
            result = SearchResult(
                algorithm=circuit,
                fitness=fitness,
                complexity=depth,
                novelty_score=novelty,
                metadata={'depth': depth, 'strategy': 'systematic'}
            )
            results.append(result)
        
        return results[:num]
    
    def _random_explore(self, num: int) -> List[SearchResult]:
        """Random exploration of circuit space."""
        results = []
        for i in range(num):
            depth = random.randint(1, self.max_depth)
            circuit = self._generate_circuit(depth)
            fitness = self._evaluate_fitness(circuit)
            novelty = self._compute_novelty(circuit)
            
            result = SearchResult(
                algorithm=circuit,
                fitness=fitness,
                complexity=depth,
                novelty_score=novelty,
                metadata={'depth': depth, 'strategy': 'random', 'sample': i}
            )
            results.append(result)
        
        return results
    
    def _genetic_explore(self, num: int) -> List[SearchResult]:
        """Genetic programming for circuit evolution."""
        # Initialize population.
        population_size = min(20, num)
        population = [self._generate_circuit(random.randint(1, 5)) 
                     for _ in range(population_size)]
        
        results = []
        for generation in range(10):  # 10 generations.
            # Evaluate fitness.
            fitness_scores = [self._evaluate_fitness(c) for c in population]
            
            # Select top performers.
            sorted_pop = sorted(zip(population, fitness_scores), 
                                key=lambda x: x[1], reverse=True)
            
            # Create next generation.
            new_population = []
            # Keep top 50%.
            elite_count = population_size // 2
            for i in range(elite_count):
                new_population.append(sorted_pop[i][0])
            
            # Crossover and mutate for rest.
            while len(new_population) < population_size:
                parent1 = random.choice(population[:elite_count])
                parent2 = random.choice(population[:elite_count])
                child = self._crossover(parent1, parent2)
                child = self._mutate(child)
                new_population.append(child)
            
            population = new_population
            
            # Record best from this generation.
            best = sorted_pop[0]
            novelty = self._compute_novelty(best[0])
            results.append(SearchResult(
                algorithm=best[0],
                fitness=best[1],
                complexity=len(best[0]),
                novelty_score=novelty,
                metadata={'generation': generation, 'strategy': 'genetic'}
            ))
        
        return results[:num]
    
    def _generate_circuit(self, depth: int) -> List[Tuple]:
        """Generate a circuit with real quantum gates."""
        circuit = []
        for _ in range(depth):
            gate = random.choice(self.gate_set)
            if gate in ['cnot']:
                q1 = random.randint(0, self.num_qubits - 1)
                q2 = random.randint(0, self.num_qubits - 1)
                # Ensure different qubits.
                if q1 == q2:
                    q2 = (q1 + 1) % self.num_qubits
                circuit.append(('cnot', q1, q2))
            elif gate in ['rx', 'ry', 'rz']:
                q = random.randint(0, self.num_qubits - 1)
                angle = random.random() * 2 * np.pi
                circuit.append((gate, q, angle))
            else:
                q = random.randint(0, self.num_qubits - 1)
                circuit.append((gate, q))
        return circuit
    
    def _evaluate_fitness(self, circuit: List) -> float:
        """Evaluate fitness using real quantum circuit simulation."""
        # Simulate circuit and compute real quantum properties.
        num_qubits = self.num_qubits
        n = 2 ** num_qubits
        
        # Build quantum state by applying circuit.
        state = np.zeros(n, dtype=complex)
        state[0] = 1.0  # Start with |00...0>
        
        for gate_info in circuit:
            gate = gate_info[0]
            if gate == 'h':
                q = gate_info[1]
                psi = np.zeros(n, dtype=complex)
                for i in range(n):
                    bit = (i >> q) & 1
                    j = i ^ (1 << q)
                    cos_a = 1.0 / np.sqrt(2.0)
                    sin_a = 1.0 / np.sqrt(2.0)
                    if bit == 0:
                        psi[i] += cos_a * state[i]
                        psi[j] += sin_a * state[i]
                    else:
                        psi[i] += sin_a * state[i]
                        psi[j] += cos_a * state[i]
                state = psi / np.linalg.norm(psi)
            elif gate == 'x' or gate == 'y' or gate == 'z':
                q = gate_info[1]
                psi = np.zeros(n, dtype=complex)
                for i in range(n):
                    bit = (i >> q) & 1
                    j = i ^ (1 << q)
                    if gate == 'x':
                        psi[i] = state[j]
                        psi[j] = state[i]
                    elif gate == 'y':
                        psi[i] = -1j * state[j]
                        psi[j] = 1j * state[i]
                    else:  # z
                        psi[i] = state[i]
                        psi[j] = -state[j]
                state = psi / np.linalg.norm(psi)
            elif gate == 'cnot':
                q1, q2 = gate_info[1], gate_info[2]
                psi = np.zeros(n, dtype=complex)
                for i in range(n):
                    bit1 = (i >> q1) & 1
                    bit2 = (i >> q2) & 1
                    if bit1 == 1:
                        j = i ^ (1 << q2)
                        psi[j] = state[i]
                    else:
                        psi[i] = state[i]
                state = psi / np.linalg.norm(psi)
            elif gate in ['rx', 'ry', 'rz']:
                q = gate_info[1]
                angle = gate_info[2] if len(gate_info) > 2 else 0.1
                psi = np.zeros(n, dtype=complex)
                for i in range(n):
                    bit = (i >> q) & 1
                    j = i ^ (1 << q)
                    cos_a = np.cos(angle / 2)
                    sin_a = np.sin(angle / 2)
                    if gate == 'rx':
                        if bit == 0:
                            psi[i] += cos_a * state[i] - 1j * sin_a * state[j]
                            psi[j] += -1j * sin_a * state[i] + cos_a * state[j]
                        else:
                            psi[i] += cos_a * state[i] + 1j * sin_a * state[j]
                            psi[j] += 1j * sin_a * state[i] + cos_a * state[j]
                    elif gate == 'ry':
                        if bit == 0:
                            psi[i] += cos_a * state[i] - sin_a * state[j]
                            psi[j] += sin_a * state[i] + cos_a * state[j]
                        else:
                            psi[i] += sin_a * state[i] + cos_a * state[j]
                            psi[j] += -cos_a * state[i] + sin_a * state[j]
                    else:  # rz
                        if bit == 0:
                            psi[i] += np.exp(-1j * angle / 2) * state[i]
                        else:
                            psi[i] += np.exp(1j * angle / 2) * state[i]
                        psi[j] = state[j]
                state = psi / np.linalg.norm(psi)
        
        # Compute real quantum properties for fitness.
        # 1. Entanglement (Schmidt rank).
        # Reshape state as matrix for bipartite entanglement.
        half = num_qubits // 2
        if half > 0:
            shape = (2 ** half, 2 ** (num_qubits - half))
            mat = state.reshape(shape)
            S = np.linalg.svd(mat, compute_uv=False)
            schmidt_rank = np.sum(S > 1e-6)
            entanglement_score = min(1.0, schmidt_rank / float(2 ** half))
        else:
            entanglement_score = 0.0
        
        # 2. Uniformity of output distribution (closer to uniform = higher).
        probs = np.abs(state) ** 2
        uniform_dist = np.ones(n) / n
        kl_div = np.sum(probs * np.log((probs + 1e-10) / (uniform_dist + 1e-10)))
        uniformity_score = 1.0 / (1.0 + kl_div)
        
        # 3. Gate count efficiency (fewer gates = better, up to a point).
        depth = len(circuit)
        gate_efficiency = min(1.0, 10.0 / max(depth, 1))
        
        # Combined fitness.
        fitness = 0.4 * entanglement_score + 0.4 * uniformity_score + 0.2 * gate_efficiency
        return fitness
    
    def _compute_novelty(self, circuit: List) -> float:
        """Compute novelty score (how different from visited circuits)."""
        circuit_str = str(circuit)
        if circuit_str in self.visited_circuits:
            return 0.0
        else:
            self.visited_circuits.append(circuit_str)
            return 1.0 / (1.0 + len(self.visited_circuits))
    
    def _crossover(self, parent1: List, parent2: List) -> List:
        """Crossover two parent circuits."""
        if not parent1 or not parent2:
            return parent1 or parent2
        split1 = len(parent1) // 2
        split2 = len(parent2) // 2
        return parent1[:split1] + parent2[split2:]
    
    def _mutate(self, circuit: List, mutation_rate: float = 0.1) -> List:
        """Mutate a circuit."""
        mutated = circuit.copy()
        for i in range(len(mutated)):
            if random.random() < mutation_rate:
                gate = random.choice(self.gate_set)
                q = random.randint(0, self.num_qubits - 1)
                mutated[i] = (gate, q)
        return mutated


class GeneticCircuitEvolution:
    """Genetic programming for circuit evolution."""
    
    def __init__(self, population_size: int = 50, generations: int = 100):
        self.population_size = population_size
        self.generations = generations
        self.fitness_func: Optional[Callable] = None
    
    def set_fitness_function(self, func: Callable[[List], float]):
        """Set the fitness function."""
        self.fitness_func = func
    
    def evolve(self, initial_circuit: Optional[List] = None) -> SearchResult:
        """Run genetic evolution."""
        if self.fitness_func is None:
            raise ValueError("Fitness function not set")
        
        # Initialize population.
        if initial_circuit:
            population = [initial_circuit] + [
                self._mutate(initial_circuit) 
                for _ in range(self.population_size - 1)
            ]
        else:
            population = [self._random_circuit() 
                        for _ in range(self.population_size)]
        
        best_result = None
        
        for gen in range(self.generations):
            # Evaluate.
            fitness = [self.fitness_func(c) for c in population]
            
            # Find best.
            best_idx = np.argmax(fitness)
            if best_result is None or fitness[best_idx] > best_result.fitness:
                best_result = SearchResult(
                    algorithm=population[best_idx],
                    fitness=fitness[best_idx],
                    complexity=len(population[best_idx]),
                    novelty_score=0.5,  # Placeholder.
                    metadata={'generation': gen}
                )
            
            # Selection and reproduction.
            new_pop = []
            # Elitism: keep top 10%.
            elite_count = max(1, self.population_size // 10)
            sorted_indices = np.argsort(fitness)[::-1]
            for i in range(elite_count):
                new_pop.append(population[sorted_indices[i]])
            
            # Fill rest with crossover and mutation.
            while len(new_pop) < self.population_size:
                p1 = population[random.choice(sorted_indices[:10])]
                p2 = population[random.choice(sorted_indices[:10])]
                child = self._crossover(p1, p2)
                child = self._mutate(child)
                new_pop.append(child)
            
            population = new_pop
        
        return best_result
    
    def _random_circuit(self) -> List[Tuple]:
        """Generate random circuit."""
        depth = random.randint(1, 10)
        gates = ['h', 'x', 'cnot']
        circuit = []
        for _ in range(depth):
            gate = random.choice(gates)
            if gate == 'cnot':
                circuit.append((gate, 0, 1))
            else:
                circuit.append((gate, 0))
        return circuit
    
    def _crossover(self, p1: List, p2: List) -> List:
        """Crossover two circuits."""
        split = min(len(p1), len(p2)) // 2
        return p1[:split] + p2[split:]
    
    def _mutate(self, circuit: List) -> List:
        """Mutate circuit."""
        mutated = circuit.copy()
        idx = random.randint(0, len(mutated) - 1)
        gate = random.choice(['h', 'x', 'cnot'])
        if gate == 'cnot':
            mutated[idx] = (gate, 0, 1)
        else:
            mutated[idx] = (gate, 0)
        return mutated


class RLCircuitDiscovery:
    """Reinforcement learning-based circuit discovery."""
    
    def __init__(self, learning_rate: float = 0.01, epsilon: float = 0.1):
        self.lr = learning_rate
        self.epsilon = epsilon
        self.q_table: Dict[str, Dict[str, float]] = {}
        self.actions = ['h', 'x', 'y', 'z', 'cnot', 'measure']
    
    def discover(self, target_state: np.ndarray, 
                max_steps: int = 100) -> SearchResult:
        """
        Discover circuit to reach target state using RL.
        
        Args:
            target_state: Desired final state vector.
            max_steps: Maximum RL steps.
            
        Returns:
            SearchResult with discovered circuit.
        """
        state = np.array([1] + [0] * (len(target_state) - 1), dtype=complex)  # |00...0>
        circuit = []
        
        for step in range(max_steps):
            state_key = str(state[:3])  # Simplified state representation.
            
            # Epsilon-greedy action selection.
            if random.random() < self.epsilon:
                action = random.choice(self.actions)
            else:
                q_values = self.q_table.get(state_key, {})
                if q_values:
                    action = max(q_values, key=q_values.get)
                else:
                    action = random.choice(self.actions)
            
            # Execute action (simplified).
            new_state = self._apply_action(state, action)
            
            # Calculate reward.
            reward = self._calculate_reward(new_state, target_state)
            
            # Update Q-value.
            if state_key not in self.q_table:
                self.q_table[state_key] = {}
            if action not in self.q_table[state_key]:
                self.q_table[state_key][action] = 0.0
            
            # Simplified Q-learning update.
            next_key = str(new_state[:3])
            next_q = max(self.q_table.get(next_key, {}).values() or [0.0])
            self.q_table[state_key][action] += self.lr * (
                reward + 0.9 * next_q - self.q_table[state_key][action]
            )
            
            circuit.append((action, step))
            state = new_state
            
            if reward > 0.95:  # Good enough.
                break
        
        fitness = self._calculate_reward(state, target_state)
        return SearchResult(
            algorithm=circuit,
            fitness=fitness,
            complexity=len(circuit),
            novelty_score=0.5,
            metadata={'steps': len(circuit), 'method': 'rl'}
        )
    
    def _apply_action(self, state: np.ndarray, action: str) -> np.ndarray:
        """Apply action to state (simplified)."""
        # In practice, would apply actual quantum gates.
        return state  # Placeholder.
    
    def _calculate_reward(self, state: np.ndarray, target: np.ndarray) -> float:
        """Calculate reward based on state similarity."""
        fidelity = np.abs(np.dot(state.conj(), target))**2
        return fidelity


class NoveltyDetector:
    """Detect when a discovered circuit is genuinely new."""
    
    def __init__(self, similarity_threshold: float = 0.9):
        self.threshold = similarity_threshold
        self.known_circuits: List[Any] = []
        self.novelty_scores: List[float] = []
    
    def is_novel(self, circuit: Any, 
                 similarity_func: Optional[Callable] = None) -> Tuple[bool, float]:
        """
        Check if circuit is novel.
        
        Returns:
            Tuple of (is_novel, novelty_score).
        """
        if not self.known_circuits:
            self.known_circuits.append(circuit)
            return True, 1.0
        
        # Compute similarity to known circuits.
        if similarity_func is None:
            similarity_func = self._default_similarity
        
        similarities = [similarity_func(circuit, known) 
                      for known in self.known_circuits]
        max_similarity = max(similarities) if similarities else 0.0
        
        novelty_score = 1.0 - max_similarity
        is_novel = novelty_score > (1.0 - self.threshold)
        
        if is_novel:
            self.known_circuits.append(circuit)
            self.novelty_scores.append(novelty_score)
        
        return is_novel, novelty_score
    
    def _default_similarity(self, c1: Any, c2: Any) -> float:
        """Default similarity based on structure."""
        if isinstance(c1, list) and isinstance(c2, list):
            # Compare as strings (simplified).
            return 1.0 if str(c1) == str(c2) else 0.0
        return 0.0
    
    def get_novelty_statistics(self) -> Dict[str, Any]:
        """Get statistics about novelty detection."""
        if not self.novelty_scores:
            return {}
        return {
            'mean_novelty': np.mean(self.novelty_scores),
            'min_novelty': np.min(self.novelty_scores),
            'max_novelty': np.max(self.novelty_scores),
            'num_known': len(self.known_circuits)
        }
