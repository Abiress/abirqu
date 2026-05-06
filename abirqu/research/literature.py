"""
Task 15.4 — Literature-Aware Circuit Suggestion.

Knowledge base, similarity search, citation recommendations, algorithm adaptation.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
import re


@dataclass
class LiteratureResult:
    """Result of literature-aware suggestion."""
    algorithm: str
    relevance_score: float  # 0-1.
    citations: List[str]
    adaptation_suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'algorithm': self.algorithm,
            'relevance_score': self.relevance_score,
            'citations': self.citations,
            'adaptation_suggestion': self.adaptation_suggestion,
            'metadata': self.metadata
        }


class AlgorithmKnowledgeBase:
    """Knowledge base of known quantum algorithms and techniques."""
    
    def __init__(self):
        self.algorithms: Dict[str, Dict] = {}
        self._load_default_algorithms()
    
    def _load_default_algorithms(self):
        """Load default algorithm knowledge base."""
        self.algorithms['grovers'] = {
            'name': 'Grovers Algorithm',
            'type': 'search',
            'complexity': 'O(sqrt(N))',
            'qubits': 'O(log N)',
            'gates': ['h', 'cnot', 'oracle'],
            'citation': 'Grover (1996)',
            'paper': 'A fast quantum mechanical algorithm for database search',
            'year': 1996,
            'keywords': ['search', 'unstructured', 'quadratic speedup'],
            'problems': ['search', 'optimization', 'SAT']
        }
        self.algorithms['shors'] = {
            'name': "Shor's Algorithm",
            'type': 'factoring',
            'complexity': 'O(n^3)',
            'qubits': 'O(n)',
            'gates': ['qft', 'modular_exponentiation'],
            'citation': 'Shor (1997)',
            'paper': 'Polynomial-Time Algorithms for Prime Factorization and Discrete Logarithms',
            'year': 1997,
            'keywords': ['factoring', 'cryptography', 'exponential speedup'],
            'problems': ['factoring', 'discrete log', 'RSA']
        }
        self.algorithms['vqe'] = {
            'name': 'Variational Quantum Eigensolver',
            'type': 'hybrid',
            'complexity': 'variable',
            'qubits': 'problem-dependent',
            'gates': ['h', 'ry', 'cnot', 'u3'],
            'citation': 'Peruzzo et al. (2014)',
            'paper': 'A variational eigenvalue solver on a quantum processor',
            'year': 2014,
            'keywords': ['VQE', 'hybrid', 'NISQ', 'chemistry'],
            'problems': ['molecular energy', 'optimization', 'ground state']
        }
        self.algorithms['qaoa'] = {
            'name': 'Quantum Approximate Optimization Algorithm',
            'type': 'optimization',
            'complexity': 'variable',
            'qubits': 'problem-dependent',
            'gates': ['h', 'rz', 'cnot', 'mixer'],
            'citation': 'Farhi et al. (2014)',
            'paper': 'A Quantum Approximate Optimization Algorithm',
            'year': 2014,
            'keywords': ['QAOA', 'optimization', 'combinatorial', 'MAX-CUT'],
            'problems': ['MAX-CUT', 'TSP', 'graph problems']
        }
        self.algorithms['qft'] = {
            'name': 'Quantum Fourier Transform',
            'type': 'transform',
            'complexity': 'O(n^2)',
            'qubits': 'n',
            'gates': ['h', 'controlled phase', 'swap'],
            'citation': 'Coppersmith (1994)',
            'paper': 'An approximate Fourier transform useful in quantum factoring',
            'year': 1994,
            'keywords': ['QFT', 'Fourier', 'phase estimation'],
            'problems': ['phase estimation', 'factoring', 'period finding']
        }
    
    def search(self, query: str) -> List[Dict]:
        """
        Search the knowledge base.
        
        Args:
            query: Search query.
            
        Returns:
            List of matching algorithms.
        """
        query_lower = query.lower()
        results = []
        
        for algo_id, algo_data in self.algorithms.items():
            score = self._calculate_relevance(query_lower, algo_data)
            if score > 0.3:  # Threshold for relevance.
                results.append({
                    'id': algo_id,
                    **algo_data,
                    'relevance': score
                })
        
        # Sort by relevance.
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results
    
    def _calculate_relevance(self, query: str, algo: Dict) -> float:
        """Calculate relevance score."""
        score = 0.0
        
        # Check name.
        if algo['name'].lower() in query:
            score += 0.5
        
        # Check keywords.
        for keyword in algo.get('keywords', []):
            if keyword.lower() in query:
                score += 0.2
        
        # Check problem types.
        for problem in algo.get('problems', []):
            if problem.lower() in query:
                score += 0.3
        
        return min(1.0, score)
    
    def get_by_name(self, name: str) -> Optional[Dict]:
        """Get algorithm by name."""
        name_lower = name.lower()
        for algo_id, algo_data in self.algorithms.items():
            if name_lower in algo_data['name'].lower() or name_lower == algo_id:
                return algo_data
        return None
    
    def add_algorithm(self, name: str, data: Dict):
        """Add a new algorithm to the knowledge base."""
        algo_id = name.lower().replace(' ', '_')
        self.algorithms[algo_id] = data
    
    def export_json(self, filepath: str):
        """Export knowledge base to JSON."""
        with open(filepath, 'w') as f:
            json.dump(self.algorithms, f, indent=2)
    
    def import_json(self, filepath: str):
        """Import knowledge base from JSON."""
        with open(filepath, 'r') as f:
            self.algorithms = json.load(f)


class SimilaritySearch:
    """Find algorithms related to user's problem."""
    
    def __init__(self, knowledge_base: AlgorithmKnowledgeBase):
        self.kb = knowledge_base
        self.embedings: Dict[str, np.ndarray] = {}
        self._build_embedings()
    
    def _build_embedings(self):
        """Build simple embeddings for algorithms."""
        for algo_id, algo_data in self.kb.algorithms.items():
            # Create simple bag-of-words embedding.
            text = f"{algo_data['name']} {' '.join(algo_data.get('keywords', []))} {' '.join(algo_data.get('problems', []))}"
            self.embedings[algo_id] = self._text_to_vector(text)
    
    def _text_to_vector(self, text: str) -> np.ndarray:
        """Convert text to simple vector (bag of words)."""
        # Simplified: use character n-grams.
        words = re.findall(r'\w+', text.lower())
        vector = np.zeros(100)  # Simple fixed-size vector.
        for i, word in enumerate(words[:100]):
            vector[i] = hash(word) % 100 / 100.0
        return vector
    
    def find_similar(self, problem_description: str, 
                     top_n: int = 5) -> List[LiteratureResult]:
        """
        Find algorithms similar to the problem.
        
        Args:
            problem_description: Description of the problem.
            top_n: Number of top results to return.
            
        Returns:
            List of LiteratureResult.
        """
        query_vector = self._text_to_vector(problem_description)
        
        similarities = []
        for algo_id, algo_data in self.kb.algorithms.items():
            algo_vector = self.embedings.get(algo_id)
            if algo_vector is not None:
                # Cosine similarity.
                dot = np.dot(query_vector, algo_vector)
                norm1 = np.linalg.norm(query_vector)
                norm2 = np.linalg.norm(algo_vector)
                if norm1 > 0 and norm2 > 0:
                    similarity = dot / (norm1 * norm2)
                else:
                    similarity = 0.0
                
                similarities.append((algo_id, algo_data, similarity))
        
        # Sort by similarity.
        similarities.sort(key=lambda x: x[2], reverse=True)
        
        results = []
        for algo_id, algo_data, sim in similarities[:top_n]:
            results.append(LiteratureResult(
                algorithm=algo_data['name'],
                relevance_score=float(sim),
                citations=[algo_data.get('citation', '')],
                adaptation_suggestion=self._suggest_adaptation(algo_data, problem_description),
                metadata={
                    'type': algo_data.get('type'),
                    'complexity': algo_data.get('complexity'),
                    'year': algo_data.get('year')
                }
            ))
        
        return results
    
    def _suggest_adaptation(self, algo_data: Dict, 
                            problem: str) -> str:
        """Suggest how to adapt the algorithm."""
        algo_type = algo_data.get('type', '')
        if algo_type == 'search':
            return f"Adapt {algo_data['name']} by designing an oracle for your specific problem."
        elif algo_type == 'optimization':
            return f"Use {algo_data['name']} with problem-specific cost Hamiltonian."
        else:
            return f"Study {algo_data['name']} and adapt to your problem context."


class CitationRecommender:
    """Citation-aware recommendations linking to original papers."""
    
    def __init__(self):
        self.citation_graph: Dict[str, List[str]] = {}
        self._build_citation_graph()
    
    def _build_citation_graph(self):
        """Build citation graph."""
        # Simplified citation relationships.
        self.citation_graph['grovers'] = [
            'citation:grover1996fast',
            'citation:boyer1998optimal',  # Follow-up work.
            'citation:nielsen2010quantum'  # Textbook reference.
        ]
        self.citation_graph['shors'] = [
            'citation:shor1997polynomial',
            'citation:nielsen2010quantum',
            'citation:ekert1996quantum'  # Related work.
        ]
        self.citation_graph['vqe'] = [
            'citation:peruzzo2014variational',
            'citation:mcclean2016theory',  # Theoretical foundation.
            'citation:cerezo2021variational'  # Review.
        ]
        self.citation_graph['qaoa'] = [
            'citation:farhi2014quantum',
            'citation:zhou2018quantum',  # Performance analysis.
            'citation:crooks2018performance'  # Benchmarking.
        ]
    
    def get_citations(self, algorithm_name: str) -> List[str]:
        """
        Get citations for an algorithm.
        
        Args:
            algorithm_name: Name of the algorithm.
            
        Returns:
            List of citation strings.
        """
        algo_id = algorithm_name.lower().replace(' ', '_')
        return self.citation_graph.get(algo_id, [])
    
    def recommend_reading(self, problem: str, 
                          max_papers: int = 5) -> List[Dict[str, Any]]:
        """
        Recommend papers to read for a problem.
        
        Args:
            problem: Problem description.
            max_papers: Maximum number of papers to recommend.
            
        Returns:
            List of paper recommendations.
        """
        kb = AlgorithmKnowledgeBase()
        results = kb.search(problem)
        
        recommendations = []
        for result in results[:max_papers]:
            recommendations.append({
                'title': result.get('paper', 'Unknown'),
                'citation': result.get('citation', ''),
                'year': result.get('year', 0),
                'relevance': result.get('relevance', 0.0),
                'algorithm': result.get('name', '')
            })
        
        return recommendations
    
    def generate_bibliography(self, algorithms: List[str], 
                               style: str = "APA") -> str:
        """
        Generate bibliography for a list of algorithms.
        
        Args:
            algorithms: List of algorithm names.
            style: Citation style (APA, IEEE, etc.).
            
        Returns:
            Formatted bibliography string.
        """
        lines = []
        if style == "APA":
            for i, algo in enumerate(algorithms, 1):
                citations = self.get_citations(algo)
                if citations:
                    lines.append(f"{i}. {citations[0]}")
        elif style == "IEEE":
            for i, algo in enumerate(algorithms):
                citations = self.get_citations(algo)
                if citations:
                    lines.append(f"[{i+1}] {citations[0]}")
        
        return "\n".join(lines)


class AlgorithmAdapter:
    """Automatic adaptation of known algorithms to new problem instances."""
    
    def __init__(self):
        self.adaptation_rules: List[Callable] = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default adaptation rules."""
        self.adaptation_rules.append(self._adapt_oracle_based)
        self.adaptation_rules.append(self._adapt_hamiltonian_based)
        self.adaptation_rules.append(self._adapt_parameterized)
    
    def adapt(self, algorithm: Dict, problem_instance: Dict) -> Dict[str, Any]:
        """
        Adapt an algorithm to a new problem instance.
        
        Args:
            algorithm: Algorithm dictionary from knowledge base.
            problem_instance: Problem instance description.
            
        Returns:
            Adaptation result with suggested circuit structure.
        """
        for rule in self.adaptation_rules:
            result = rule(algorithm, problem_instance)
            if result:
                return result
        
        return {
            'algorithm': algorithm.get('name'),
            'adapted': False,
            'suggestion': 'Manual adaptation required',
            'circuit_template': None
        }
    
    def _adapt_oracle_based(self, algorithm: Dict, 
                            problem: Dict) -> Optional[Dict]:
        """Adapt oracle-based algorithms (e.g., Grover's)."""
        if algorithm.get('type') != 'search':
            return None
        
        oracle_desc = problem.get('oracle_description', '')
        return {
            'algorithm': algorithm['name'],
            'adapted': True,
            'suggestion': f"Design oracle for: {oracle_desc}",
            'circuit_template': {
                'gates': algorithm.get('gates', []),
                'note': 'Replace oracle with problem-specific implementation'
            },
            'estimated_qubits': problem.get('num_variables', 4)
        }
    
    def _adapt_hamiltonian_based(self, algorithm: Dict, 
                                 problem: Dict) -> Optional[Dict]:
        """Adapt Hamiltonian-based algorithms (VQE, QAOA)."""
        if algorithm.get('type') not in ['optimization', 'hybrid']:
            return None
        
        hamiltonian = problem.get('hamiltonian', '')
        return {
            'algorithm': algorithm['name'],
            'adapted': True,
            'suggestion': f"Construct cost Hamiltonian: {hamiltonian}",
            'circuit_template': {
                'gates': algorithm.get('gates', []),
                'layers': problem.get('layers', 3),
                'note': 'Parameterize and optimize'
            },
            'estimated_qubits': problem.get('num_qubits', 4)
        }
    
    def _adapt_parameterized(self, algorithm: Dict, 
                            problem: Dict) -> Optional[Dict]:
        """Generic adaptation for parameterized algorithms."""
        return {
            'algorithm': algorithm['name'],
            'adapted': True,
            'suggestion': f"Adapt {algorithm['name']} to your problem context.",
            'circuit_template': {
                'gates': algorithm.get('gates', []),
                'parameters': 'problem-specific'
            },
            'metadata': {
                'original_paper': algorithm.get('paper'),
                'year': algorithm.get('year')
            }
        }
