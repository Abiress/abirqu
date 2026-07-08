"""
QDCG v2 — Enhanced Concept Extraction & Reasoning
==================================================

Improvements over v1:
- Better concept extraction (handles complex sentences)
- Relationship inference (implicit relationships)
- Weighted reasoning (confidence propagation)
- Multi-hop reasoning (A->B->C inference)
- Context-aware graph updates
"""
import re
import numpy as np
from typing import List, Dict, Tuple, Set
from collections import defaultdict

from abirqu import Circuit
from abirqu.primitives import QuantumRun


# ═══════════════════════════════════════════════════════════════════════════════
# Enhanced Concept Extraction
# ═══════════════════════════════════════════════════════════════════════════════

# Semantic patterns for better extraction
RELATION_PATTERNS = {
    'ACTION': r'\b(sits|runs|jumps|eats|drinks|sleeps|writes|reads|plays|works|lives|loves|hates|knows|thinks|sees|hears)\b',
    'LOCATION': r'\b(on|in|at|under|near|behind|beside|inside|outside|above|below)\b',
    'QUALITY': r'\b(big|small|red|blue|fast|slow|hot|cold|old|new|good|bad|happy|sad)\b',
    'OBJECT': r'\b(cat|dog|chair|table|house|tree|car|book|phone|computer|person|man|woman|child)\b',
    'ACTION_VERB': r'\b(sits|runs|jumps|eats|drinks|sleeps|writes|reads|plays|works)\b',
}

# Word embeddings (simplified semantic similarity)
SEMANTIC_GROUPS = {
    'ANIMAL': ['cat', 'dog', 'bird', 'fish', 'horse', 'lion', 'tiger'],
    'FURNITURE': ['chair', 'table', 'bed', 'sofa', 'desk', 'cabinet'],
    'ACTION': ['sits', 'runs', 'jumps', 'eats', 'drinks', 'sleeps'],
    'LOCATION': ['house', 'room', 'kitchen', 'garden', 'office', 'park'],
    'PERSON': ['man', 'woman', 'child', 'boy', 'girl', 'person'],
}

# Relationship inference rules
INFERENCE_RULES = {
    ('ANIMAL', 'ACTION'): 'performs',
    ('ANIMAL', 'FURNITURE'): 'interacts_with',
    ('ANIMAL', 'LOCATION'): 'located_in',
    ('PERSON', 'ACTION'): 'performs',
    ('PERSON', 'OBJECT'): 'uses',
}


def extract_concepts_enhanced(text: str) -> Dict:
    """
    Enhanced concept extraction with relationships and context.

    Returns dict with:
    - concepts: list of extracted concepts
    - relationships: inferred relationships
    - context: contextual information
    """
    text_lower = text.lower().strip()
    words = re.findall(r'\b\w+\b', text_lower)

    # Extract concepts by category
    concepts = []
    concept_categories = {}

    for word in words:
        matched = False
        for category, patterns in SEMANTIC_GROUPS.items():
            if word in patterns:
                concept = word.upper()
                if concept not in concepts:
                    concepts.append(concept)
                    concept_categories[concept] = category
                matched = True
                break
        # Fallback: treat significant words (len>=5) as concepts
        if not matched and len(word) >= 5 and word not in (
            'about', 'these', 'those', 'their', 'there', 'which', 'would', 'could'):
            concept = word.upper()
            if concept not in concepts:
                concepts.append(concept)
                concept_categories[concept] = 'TERM'

    # Extract relationships from sentence structure
    relationships = []

    # Find action relationships
    for i, word in enumerate(words):
        for pattern_name, pattern in RELATION_PATTERNS.items():
            if re.match(pattern, word, re.IGNORECASE):
                # Look for subject (before) and object (after)
                if i > 0:
                    subject = words[i-1].upper()
                    if subject in concepts:
                        relationships.append({
                            'source': subject,
                            'target': word.upper(),
                            'type': pattern_name.lower(),
                            'weight': 0.8
                        })

    # Infer implicit relationships
    inferred = []
    for c1 in concepts:
        for c2 in concepts:
            if c1 != c2:
                cat1 = concept_categories.get(c1)
                cat2 = concept_categories.get(c2)
                if cat1 and cat2:
                    key = (cat1, cat2)
                    if key in INFERENCE_RULES:
                        rel_type = INFERENCE_RULES[key]
                        inferred.append({
                            'source': c1,
                            'target': c2,
                            'type': rel_type,
                            'weight': 0.5  # Lower weight for inferred
                        })

    # Context
    context = {
        'sentence_count': len(re.split(r'[.!?]+', text)),
        'word_count': len(words),
        'has_question': '?' in text,
        'has_negation': any(w in ['not', "n't", 'no', 'never'] for w in words),
    }

    return {
        'concepts': concepts,
        'relationships': relationships + inferred,
        'categories': concept_categories,
        'context': context,
        'original_text': text
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Enhanced Graph with Inference
# ═══════════════════════════════════════════════════════════════════════════════

class EnhancedCognitiveGraph:
    """Enhanced cognitive graph with inference and multi-hop reasoning."""

    def __init__(self):
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Dict] = []
        self.inference_cache: Dict[str, float] = {}

    def add_concept(self, concept: str, category: str = None, confidence: float = 1.0):
        if concept in self.nodes:
            self.nodes[concept]['confidence'] = min(1.0,
                self.nodes[concept]['confidence'] + 0.1)
        else:
            self.nodes[concept] = {
                'concept': concept,
                'category': category,
                'confidence': confidence,
                'importance': 1.0,
                'access_count': 0
            }

    def add_relationship(self, source: str, target: str, rel_type: str = 'related',
                        weight: float = 0.5):
        # Check if exists
        for edge in self.edges:
            if edge['source'] == source and edge['target'] == target:
                edge['weight'] = min(1.0, edge['weight'] + 0.1)
                return

        self.edges.append({
            'source': source,
            'target': target,
            'type': rel_type,
            'weight': weight
        })

    def infer_transitive(self, max_hops: int = 2) -> List[Dict]:
        """Infer transitive relationships (A->B->C implies A->C)."""
        inferred = []
        adjacency = defaultdict(list)

        for edge in self.edges:
            adjacency[edge['source']].append((edge['target'], edge['weight']))

        for start in self.nodes:
            visited = set()
            queue = [(start, 1.0, [start])]

            while queue:
                current, path_weight, path = queue.pop(0)

                if len(path) > 1 and current != start:
                    # Record transitive relationship
                    avg_weight = path_weight / (len(path) - 1)
                    if avg_weight > 0.3:  # Threshold
                        inferred.append({
                            'source': start,
                            'target': current,
                            'weight': avg_weight,
                            'path': path.copy(),
                            'hops': len(path) - 1
                        })

                if len(path) <= max_hops:
                    for next_node, edge_weight in adjacency[current]:
                        if next_node not in visited:
                            visited.add(next_node)
                            new_weight = path_weight * edge_weight
                            queue.append((next_node, new_weight, path + [next_node]))

        return inferred

    def get_strongest_path(self, start: str, end: str) -> Tuple[List[str], float]:
        """Find the strongest path between two concepts."""
        adjacency = defaultdict(list)
        for edge in self.edges:
            adjacency[edge['source']].append((edge['target'], edge['weight']))

        # BFS with weight tracking
        queue = [(start, 1.0, [start])]
        visited = {start: 1.0}
        best_path = None
        best_weight = 0

        while queue:
            current, weight, path = queue.pop(0)

            if current == end and weight > best_weight:
                best_path = path
                best_weight = weight

            for next_node, edge_weight in adjacency[current]:
                new_weight = weight * edge_weight
                if next_node not in visited or new_weight > visited.get(next_node, 0):
                    visited[next_node] = new_weight
                    queue.append((next_node, new_weight, path + [next_node]))

        return best_path, best_weight

    def summary(self) -> str:
        lines = ["Enhanced Cognitive Graph:", ""]
        lines.append(f"Nodes: {len(self.nodes)}")
        for name, node in self.nodes.items():
            lines.append(f"  {name} ({node['category']}): confidence={node['confidence']:.2f}")
        lines.append(f"\nEdges: {len(self.edges)}")
        for edge in self.edges:
            lines.append(f"  {edge['source']} --{edge['type']}--> {edge['target']}: {edge['weight']:.2f}")

        # Show transitive inferences
        inferred = self.infer_transitive()
        if inferred:
            lines.append(f"\nInferred Relationships: {len(inferred)}")
            for inf in inferred[:5]:
                lines.append(f"  {inf['source']} --({inf['hops']}-hop)--> {inf['target']}: {inf['weight']:.2f}")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Multi-Hop Quantum Reasoning
# ═══════════════════════════════════════════════════════════════════════════════

def build_multi_hop_circuit(graph: EnhancedCognitiveGraph, query_concepts: List[str] = None) -> Circuit:
    """
    Build quantum circuit for multi-hop reasoning.

    Uses more qubits to represent:
    - Concept qubits (one per concept)
    - Hop counter qubits (track reasoning depth)
    - Answer qubit (accumulates result)
    """
    mapping = {name: i for i, name in enumerate(graph.nodes.keys())}
    n_concepts = len(mapping)

    if n_concepts == 0:
        return Circuit(1)

    # Add hop counter and answer qubits
    n_total = n_concepts + 2  # +2 for hop counter and answer
    circuit = Circuit(n_total, name="multi_hop_reasoning")

    hop_qubit = n_concepts
    answer_qubit = n_concepts + 1

    # Initialize answer qubit
    circuit.x(answer_qubit)

    # Put all concept qubits in superposition
    for i in range(n_concepts):
        circuit.h(i)

    # Multi-hop reasoning rounds
    for hop in range(3):  # Up to 3 hops
        for edge in graph.edges:
            src_idx = mapping.get(edge['source'])
            tgt_idx = mapping.get(edge['target'])

            if src_idx is not None and tgt_idx is not None:
                # Controlled operation: if source is active, activate target
                theta = edge['weight'] * np.pi / 2

                # Entangle source and target
                circuit.cx(src_idx, tgt_idx)
                circuit.ry(tgt_idx, theta * (0.8 ** hop))  # Decay with hops
                circuit.cx(src_idx, tgt_idx)

                # Propagate to answer qubit
                circuit.toffoli(src_idx, tgt_idx, answer_qubit)

    # Interference
    for i in range(n_concepts):
        circuit.h(i)

    # Measure
    for i in range(n_total):
        circuit.measure(i)

    return circuit, mapping


# ═══════════════════════════════════════════════════════════════════════════════
# Question Answering
# ═══════════════════════════════════════════════════════════════════════════════

def answer_question(context: str, question: str) -> Dict:
    """
    Answer a question using QDCG reasoning.

    Example:
        context = "The cat sits on the chair in the room"
        question = "Where is the cat?"
        answer = "on the chair"
    """
    # Extract concepts from context
    context_extraction = extract_concepts_enhanced(context)
    question_extraction = extract_concepts_enhanced(question)

    # Build graph
    graph = EnhancedCognitiveGraph()

    for concept in context_extraction['concepts']:
        cat = context_extraction['categories'].get(concept)
        graph.add_concept(concept, category=cat, confidence=0.9)

    for rel in context_extraction['relationships']:
        graph.add_relationship(rel['source'], rel['target'], rel['type'], rel['weight'])

    # Find question concepts
    question_concepts = question_extraction['concepts']

    # Find answer concepts (concepts related to question concepts)
    answers = []
    for q_concept in question_concepts:
        for edge in graph.edges:
            if edge['source'] == q_concept:
                answers.append({
                    'concept': edge['target'],
                    'confidence': edge['weight'],
                    'path': [q_concept, edge['target']]
                })
            elif edge['target'] == q_concept:
                answers.append({
                    'concept': edge['source'],
                    'confidence': edge['weight'],
                    'path': [q_concept, edge['source']]
                })

    # Sort by confidence
    answers.sort(key=lambda x: x['confidence'], reverse=True)

    # Run quantum reasoning if we have enough concepts
    quantum_result = None
    if len(graph.nodes) >= 2:
        try:
            circuit, mapping = build_multi_hop_circuit(graph)
            result = QuantumRun(circuit, shots=500)
            quantum_result = result.counts
        except Exception as e:
            quantum_result = f"Quantum simulation error: {e}"

    return {
        'question': question,
        'context': context,
        'question_concepts': question_concepts,
        'answers': answers[:3],
        'graph': graph.summary(),
        'quantum_result': quantum_result
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Main Demo
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  QDCG v2 — Enhanced Reasoning Demo")
    print("=" * 60)

    # Test 1: Complex sentence
    print("\n" + "─" * 60)
    print("TEST 1: Complex Sentence Extraction")
    print("─" * 60)

    text1 = "The big cat sits on the red chair in the warm room"
    result1 = extract_concepts_enhanced(text1)

    print(f"\nInput: \"{text1}\"")
    print(f"\nExtracted Concepts: {result1['concepts']}")
    print(f"Categories: {result1['categories']}")
    print(f"Relationships: {result1['relationships']}")
    print(f"Context: {result1['context']}")

    # Test 2: Question Answering
    print("\n" + "─" * 60)
    print("TEST 2: Question Answering")
    print("─" * 60)

    context = "The cat sits on the chair. The dog sleeps on the bed. The bird flies in the sky."
    questions = [
        "Where is the cat?",
        "What does the dog do?",
        "Where does the bird fly?"
    ]

    for q in questions:
        print(f"\nQ: {q}")
        answer = answer_question(context, q)
        if answer['answers']:
            print(f"A: {answer['answers'][0]['concept']} (confidence: {answer['answers'][0]['confidence']:.2f})")
        else:
            print("A: No answer found")

    # Test 3: Transitive Inference
    print("\n" + "─" * 60)
    print("TEST 3: Transitive Inference")
    print("─" * 60)

    graph = EnhancedCognitiveGraph()
    graph.add_concept('A', 'test')
    graph.add_concept('B', 'test')
    graph.add_concept('C', 'test')
    graph.add_relationship('A', 'B', 'related', 0.8)
    graph.add_relationship('B', 'C', 'related', 0.7)

    print("\nDirect: A -> B (0.8), B -> C (0.7)")
    inferred = graph.infer_transitive()
    print(f"Inferred: A -> C ({inferred[0]['weight']:.2f})")

    print("\n" + "=" * 60)
    print("  QDCG v2 Demo Complete")
    print("=" * 60)
