"""
QDCG Real-World Applications
===========================

Demonstrates using Quantum Dynamic Cognitive Graph for:
1. Document Summarization (extract key concepts)
2. Logic Puzzle Solving (reason over constraints)
3. Knowledge Graph Reasoning (multi-hop inference)
"""
from typing import List, Dict, Tuple
from collections import defaultdict, Counter

from abirqu import Circuit
from abirqu.primitives import QuantumRun

from qdcg_v2 import (
    extract_concepts_enhanced,
    EnhancedCognitiveGraph,
    build_multi_hop_circuit,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Document Summarization
# ═══════════════════════════════════════════════════════════════════════════════

def summarize_document(text: str, top_k: int = 5) -> Dict:
    """
    Summarize a document by extracting and ranking key concepts.

    Instead of frequency-based TF-IDF, we build a concept graph
    and rank by centrality (importance in the graph).
    """
    # Split into sentences
    sentences = [s.strip() for s in text.replace('\n', ' ').split('.') if s.strip()]

    # Extract concepts from each sentence
    all_concepts = []
    sentence_concepts = []

    for sent in sentences:
        extraction = extract_concepts_enhanced(sent)
        concepts = extraction['concepts']
        all_concepts.extend(concepts)
        sentence_concepts.append(concepts)

    # Build concept graph
    graph = EnhancedCognitiveGraph()
    for sent_concepts in sentence_concepts:
        for c in sent_concepts:
            graph.add_concept(c, confidence=0.9)
        # Connect co-occurring concepts
        for i, c1 in enumerate(sent_concepts):
            for c2 in sent_concepts[i+1:]:
                graph.add_relationship(c1, c2, 'co-occurs', 0.6)

    # Rank concepts by degree centrality
    concept_scores = defaultdict(float)
    for edge in graph.edges:
        concept_scores[edge['source']] += edge['weight']
        concept_scores[edge['target']] += edge['weight']

    # Sort by score
    ranked = sorted(concept_scores.items(), key=lambda x: x[1], reverse=True)

    # Find most central sentence (contains most top concepts)
    top_concepts = [c for c, _ in ranked[:top_k]]
    best_sentence = None
    best_score = -1
    for i, sent_concepts in enumerate(sentence_concepts):
        score = sum(1 for c in sent_concepts if c in top_concepts)
        if score > best_score:
            best_score = score
            best_sentence = sentences[i]

    return {
        'key_concepts': ranked[:top_k],
        'summary': best_sentence,
        'total_concepts': len(set(all_concepts)),
        'graph_size': len(graph.nodes),
        'num_sentences': len(sentences)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Logic Puzzle Solver
# ═══════════════════════════════════════════════════════════════════════════════

def solve_logic_puzzle(facts: List[str], query: str) -> Dict:
    """
    Solve a logic puzzle using graph reasoning.

    Facts are statements like:
    - "Alice likes Bob"
    - "Bob likes Carol"
    - "Carol likes Alice"

    Query: "Who does Alice like?" -> "Bob"
    """
    graph = EnhancedCognitiveGraph()

    for fact in facts:
        extraction = extract_concepts_enhanced(fact)

        # Extract subject-verb-object
        words = fact.lower().split()
        if len(words) >= 3:
            subject = words[0].upper()
            verb = words[1] if len(words) > 1 else 'likes'
            obj = words[-1].upper().rstrip('.,!?')

            # Add concepts
            for concept in [subject, obj]:
                graph.add_concept(concept, confidence=0.9)

            # Add relationship
            graph.add_relationship(subject, obj, verb, 0.9)

    # Find answer to query
    query_words = query.lower().split()
    query_subject = query_words[2].upper() if len(query_words) > 2 else None

    answers = []
    if query_subject:
        for edge in graph.edges:
            if edge['source'] == query_subject:
                answers.append({
                    'answer': edge['target'],
                    'relation': edge['type'],
                    'confidence': edge['weight']
                })
            elif edge['target'] == query_subject:
                answers.append({
                    'answer': edge['source'],
                    'relation': edge['type'],
                    'confidence': edge['weight']
                })

    # Multi-hop inference
    inferred = graph.infer_transitive()

    return {
        'query': query,
        'answers': answers,
        'inferred_relationships': inferred[:3],
        'graph_size': len(graph.nodes)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Knowledge Graph Reasoning
# ═══════════════════════════════════════════════════════════════════════════════

def reason_over_knowledge_graph(triples: List[Tuple[str, str, str]]) -> Dict:
    """
    Reason over a knowledge graph using quantum circuit.

    Triples: (subject, relation, object)
    Example: ("Einstein", "born_in", "Germany")
    """
    graph = EnhancedCognitiveGraph()

    for subj, rel, obj in triples:
        graph.add_concept(subj.upper(), confidence=0.9)
        graph.add_concept(obj.upper(), confidence=0.9)
        graph.add_relationship(subj.upper(), obj.upper(), rel, 0.9)

    # Find multi-hop paths
    inferred = graph.infer_transitive()

    # Build quantum circuit for reasoning
    circuit = None
    mapping = None
    if len(graph.nodes) >= 2:
        circuit, mapping = build_multi_hop_circuit(graph)

    return {
        'triples': triples,
        'inferred_paths': inferred,
        'num_concepts': len(graph.nodes),
        'quantum_circuit_qubits': circuit.num_qubits if circuit else 0
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Main Demo
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  QDCG Real-World Applications")
    print("=" * 60)

    # 1. Document Summarization
    print("\n" + "─" * 60)
    print("1. DOCUMENT SUMMARIZATION")
    print("─" * 60)

    doc = """
    Quantum computing uses superposition and entanglement to process information.
    IBM has built quantum computers with over 1000 qubits.
    Google demonstrated quantum supremacy with their Sycamore processor.
    Machine learning models require large amounts of training data.
    Neural networks use backpropagation to learn patterns from data.
    Quantum machine learning combines quantum computing with neural networks.
    Error correction is essential for building fault-tolerant quantum computers.
    """

    summary = summarize_document(doc, top_k=5)
    print(f"\nDocument: {len(doc)} chars, {summary['num_sentences']} sentences")
    print(f"Total concepts: {summary['total_concepts']}")
    print(f"\nTop concepts: {[c for c, _ in summary['key_concepts']]}")
    print(f"\nSummary: \"{summary['summary']}\"")

    # 2. Logic Puzzle
    print("\n" + "─" * 60)
    print("2. LOGIC PUZZLE SOLVER")
    print("─" * 60)

    facts = [
        "Alice likes Bob",
        "Bob likes Carol",
        "Carol likes Alice",
        "Dave likes Alice",
    ]

    query = "Who does Alice like?"
    puzzle = solve_logic_puzzle(facts, query)

    print(f"\nFacts: {facts}")
    print(f"Query: {query}")
    if puzzle['answers']:
        for ans in puzzle['answers'][:2]:
            print(f"Answer: Alice --{ans['relation']}--> {ans['answer']} ({ans['confidence']:.0%})")
    else:
        print("No direct answer found")

    # 3. Knowledge Graph
    print("\n" + "─" * 60)
    print("3. KNOWLEDGE GRAPH REASONING")
    print("─" * 60)

    triples = [
        ("Einstein", "born_in", "Germany"),
        ("Germany", "located_in", "Europe"),
        ("Europe", "has_capital", "Brussels"),
        ("Newton", "born_in", "England"),
        ("England", "located_in", "Europe"),
    ]

    kg = reason_over_knowledge_graph(triples)
    print(f"\nKnowledge graph: {kg['num_concepts']} concepts")
    print(f"Quantum circuit: {kg['quantum_circuit_qubits']} qubits")
    print(f"\nInferred paths (multi-hop):")
    for path in kg['inferred_paths'][:3]:
        print(f"  {' -> '.join(path['path'])} ({path['hops']}-hop, {path['weight']:.2f})")

    print("\n" + "=" * 60)
    print("  QDCG Real-World Demo Complete")
    print("=" * 60)
