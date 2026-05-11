"""Results Visualization for AbirQu. Copyright 2026 Abir Maheshwari"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

class ResultsVisualizer:
    """Visualizes quantum measurement results."""
    
    def __init__(self):
        self.show_percentages = True
        
    def histogram(self, counts: Dict[str, int], title: str = "Measurement Results") -> str:
        """Generate text-based histogram of results."""
        if not counts:
            return "No results to display"
            
        total = sum(counts.values())
        max_count = max(counts.values())
        
        lines = []
        lines.append(f"\n{title}")
        lines.append("=" * 50)
        
        # Sort by count (descending)
        sorted_results = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        
        # Determine display limit
        display_limit = 20 if len(sorted_results) > 20 else len(sorted_results)
        
        for state, count in sorted_results[:display_limit]:
            # Calculate bar length
            bar_len = int((count / max_count) * 40)
            bar = '█' * bar_len
            
            # Percentage
            pct = (count / total) * 100 if total > 0 else 0
            
            if self.show_percentages:
                lines.append(f"{state:>10}: {bar} {count:>6} ({pct:>5.1f}%)")
            else:
                lines.append(f"{state:>10}: {bar} {count:>6}")
                
        if len(sorted_results) > display_limit:
            lines.append(f"... and {len(sorted_results) - display_limit} more states")
            
        lines.append("=" * 50)
        lines.append(f"Total shots: {total}")
        
        return '\n'.join(lines)
        
    def probabilities_table(self, counts: Dict[str, int]) -> str:
        """Generate probability table."""
        if not counts:
            return "No results"
            
        total = sum(counts.values())
        lines = []
        lines.append("\nProbability Distribution")
        lines.append("-" * 40)
        lines.append(f"{'State':<15} {'Count':<10} {'Probability':<12}")
        lines.append("-" * 40)
        
        for state, count in sorted(counts.items()):
            prob = count / total if total > 0 else 0
            lines.append(f"{state:<15} {count:<10} {prob:<12.4f}")
            
        return '\n'.join(lines)
        
    def compare_results(self, result1: Dict[str, int], result2: Dict[str, int], 
                          label1: str = "Run 1", label2: str = "Run 2") -> str:
        """Compare two sets of results."""
        lines = []
        lines.append(f"\nComparison: {label1} vs {label2}")
        lines.append("=" * 60)
        
        all_states = sorted(set(result1.keys()) | set(result2.keys()))
        total1 = sum(result1.values())
        total2 = sum(result2.values())
        
        lines.append(f"{'State':<10} {label1:<20} {label2:<20} Diff")
        lines.append("-" * 60)
        
        for state in all_states:
            c1 = result1.get(state, 0)
            c2 = result2.get(state, 0)
            p1 = c1 / total1 if total1 > 0 else 0
            p2 = c2 / total2 if total2 > 0 else 0
            diff = p2 - p1
            lines.append(f"{state:<10} {p1:<20.3f} {p2:<20.3f} {diff:+.3f}")
            
        return '\n'.join(lines)
        
    def export_csv(self, counts: Dict[str, int], filepath: str):
        """Export results to CSV."""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['State', 'Count', 'Probability'])
            
            total = sum(counts.values())
            for state, count in sorted(counts.items()):
                prob = count / total if total > 0 else 0
                writer.writerow([state, count, prob])
                
    def plot_matplotlib(self, counts: Dict[str, int], title: str = "Results"):
        """Plot using matplotlib (if available)."""
        try:
            import matplotlib.pyplot as plt
            
            states = list(counts.keys())
            values = list(counts.values())
            
            plt.figure(figsize=(10, 6))
            plt.bar(states, values)
            plt.xlabel('Quantum State')
            plt.ylabel('Count')
            plt.title(title)
            plt.xticks(rotation=45)
            plt.tight_layout()
            
            return plt
        except ImportError:
            return "matplotlib not installed"
            
    def top_states(self, counts: Dict[str, int], n: int = 5) -> List[Tuple[str, int]]:
        """Get top N most frequent states."""
        sorted_results = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:n]
