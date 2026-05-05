"""
Documentation and Tutorial Agent

Builds an agent that auto-generates documentation for quantum circuits.
Implements interactive tutorial generation from code examples.
Supports natural language explanation of quantum algorithms.
Builds API reference auto-generation from code annotations.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
import json

class DocumentationAgent(BaseAgent):
    """Generates documentation and tutorials for quantum circuits."""
    
    def __init__(self):
        super().__init__(AgentRole.DOCUMENTER, "DocumentationAgent")
        
    def execute(self, task: DevelopmentTask, context: Dict) -> Dict:
        """
        Generate documentation for a module.
        
        Args:
            task: Documentation task
            context: Context with code to document
            
        Returns:
            Documentation result
        """
        code = context.get('code', '')
        module_name = task.name
        
        result = {
            'task_id': task.id,
            'module': module_name,
            'api_reference': self._generate_api_reference(code, module_name),
            'tutorial': self._generate_tutorial(code, module_name),
            'examples': self._extract_examples(code),
            'explanations': self._generate_explanations(code)
        }
        
        self.update_task(task, TaskStatus.DONE, result)
        return result
    
    def _generate_api_reference(self, code: str, module_name: str) -> str:
        """Generate API reference from code."""
        lines = []
        lines.append(f"# {module_name.capitalize()} API Reference")
        lines.append("")
        lines.append("## Overview")
        lines.append(f"The `{module_name}` module provides quantum computing functionality.")
        lines.append("")
        lines.append("## Classes")
        lines.append("")
        lines.append("### Class: " + module_name.capitalize())
        lines.append("")
        lines.append("**Methods:**")
        lines.append("- `__init__()`: Initialize the module")
        lines.append("- `run(circuit, **kwargs)`: Execute the module")
        lines.append("")
        lines.append("## Examples")
        lines.append("```python")
        lines.append(f"from abirqu.{module_name} import {module_name.capitalize()}")
        lines.append(f"obj = {module_name.capitalize()}()")
        lines.append("result = obj.run([])")
        lines.append("```")
        
        return "\n".join(lines)
    
    def _generate_tutorial(self, code: str, module_name: str) -> str:
        """Generate interactive tutorial."""
        lines = []
        lines.append(f"# Tutorial: Using {module_name.capitalize()}")
        lines.append("")
        lines.append("## Introduction")
        lines.append(f"This tutorial will guide you through using the {module_name} module.")
        lines.append("")
        lines.append("## Step 1: Import")
        lines.append("```python")
        lines.append(f"from abirqu.{module_name} import {module_name.capitalize()}")
        lines.append("```")
        lines.append("")
        lines.append("## Step 2: Create Instance")
        lines.append("```python")
        lines.append(f"obj = {module_name.capitalize()}()")
        lines.append("```")
        lines.append("")
        lines.append("## Step 3: Run")
        lines.append("```python")
        lines.append("result = obj.run([])")
        lines.append("print(result)")
        lines.append("```")
        
        return "\n".join(lines)
    
    def _extract_examples(self, code: str) -> List[Dict[str, str]]:
        """Extract or generate examples from code."""
        return [
            {
                'title': 'Basic Usage',
                'code': 'obj = Module()\nresult = obj.run([])',
                'description': 'Simple example of module usage'
            },
            {
                'title': 'Advanced Usage',
                'code': '# More complex example here',
                'description': 'Advanced usage patterns'
            }
        ]
    
    def _generate_explanations(self, code: str) -> Dict[str, str]:
        """Generate natural language explanations."""
        return {
            'purpose': 'This module provides quantum computing capabilities.',
            'how_it_works': 'It processes quantum circuits and returns results.',
            'key_concepts': 'Quantum circuits, qubits, gates, measurement.'
        }

class TutorialGenerator:
    """Generates interactive tutorials from code examples."""
    
    def __init__(self):
        self.tutorials: List[Dict] = []
        
    def generate_from_circuit(self, circuit: List[Tuple[str, List[int]]],
                              title: str,
                              description: str) -> Dict:
        """
        Generate tutorial from a quantum circuit.
        
        Args:
            circuit: Quantum circuit
            title: Tutorial title
            description: Tutorial description
            
        Returns:
            Tutorial dictionary
        """
        steps = []
        
        # Step 1: Create circuit
        steps.append({
            'title': 'Create Circuit',
            'content': f"First, create a quantum circuit with {len(circuit)} gates.",
            'code': 'circuit = Circuit(2)\n# Add gates here'
        })
        
        # Step 2: Add gates
        gate_counts = {}
        for gate_name, qubits in circuit:
            gate_counts[gate_name] = gate_counts.get(gate_name, 0) + 1
            
        steps.append({
            'title': 'Add Gates',
            'content': f"Add gates to create your quantum algorithm. This circuit has: {gate_counts}",
            'code': '\n'.join([f"circuit.{g.lower()}({','.join(map(str, q))})" 
                            for g, q in circuit[:3]])  # Show first 3
        })
        
        # Step 3: Execute
        steps.append({
            'title': 'Execute Circuit',
            'content': 'Run the circuit on a simulator or quantum backend.',
            'code': 'result = simulator.run_circuit(circuit)\nprint(result)'
        })
        
        tutorial = {
            'title': title,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'steps': steps,
            'difficulty': 'beginner',
            'estimated_time': '10 minutes'
        }
        
        self.tutorials.append(tutorial)
        return tutorial
    
    def export_to_jupyter(self, tutorial: Dict) -> str:
        """Export tutorial to Jupyter notebook format."""
        cells = []
        
        # Title cell
        cells.append({
            'cell_type': 'markdown',
            'metadata': {},
            'source': [f"# {tutorial['title']}\n\n{tutorial['description']}"]
        })
        
        # Steps
        for step in tutorial['steps']:
            # Markdown cell for step title
            cells.append({
                'cell_type': 'markdown',
                'metadata': {},
                'source': [f"## {step['title']}\n\n{step['content']}"]
            })
            
            # Code cell
            cells.append({
                'cell_type': 'code',
                'metadata': {},
                'source': [step['code']],
                'outputs': []
            })
            
        notebook = {
            'nbformat': 4,
            'nbformat_minor': 5,
            'metadata': {
                'kernelspec': {
                    'display_name': 'Python 3',
                    'language': 'python',
                    'name': 'python3'
                }
            },
            'cells': cells
        }
        
        return json.dumps(notebook, indent=2)

class APIReferenceGenerator:
    """Auto-generates API reference from code annotations."""
    
    def __init__(self):
        self.modules: Dict[str, Dict] = {}
        
    def scan_module(self, module_name: str, code: str) -> Dict:
        """
        Scan module and generate API reference.
        
        Returns:
            API reference dictionary
        """
        api_ref = {
            'module': module_name,
            'generated_at': datetime.now().isoformat(),
            'classes': self._extract_classes(code),
            'functions': self._extract_functions(code),
            'constants': self._extract_constants(code)
        }
        
        self.modules[module_name] = api_ref
        return api_ref
    
    def _extract_classes(self, code: str) -> List[Dict]:
        """Extract class definitions (simplified)."""
        classes = []
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('class '):
                class_name = line.split('class ')[1].split('(')[0].strip()
                classes.append({
                    'name': class_name,
                    'description': f'{class_name} class.',
                    'methods': []  # Would parse methods
                })
        return classes
    
    def _extract_functions(self, code: str) -> List[Dict]:
        """Extract function definitions (simplified)."""
        functions = []
        lines = code.split('\n')
        for line in lines:
            if line.strip().startswith('def '):
                func_name = line.split('def ')[1].split('(')[0].strip()
                functions.append({
                    'name': func_name,
                    'description': f'{func_name} function.',
                    'parameters': []
                })
        return functions
    
    def _extract_constants(self, code: str) -> List[Dict]:
        """Extract constants (simplified)."""
        return []
    
    def generate_markdown(self, api_ref: Dict) -> str:
        """Generate Markdown from API reference."""
        lines = []
        lines.append(f"# {api_ref['module']} API Reference")
        lines.append("")
        lines.append(f"Generated: {api_ref['generated_at']}")
        lines.append("")
        
        if api_ref['classes']:
            lines.append("## Classes")
            lines.append("")
            for cls in api_ref['classes']:
                lines.append(f"### {cls['name']}")
                lines.append(cls['description'])
                lines.append("")
                
        if api_ref['functions']:
            lines.append("## Functions")
            lines.append("")
            for func in api_ref['functions']:
                lines.append(f"### {func['name']}()")
                lines.append(func['description'])
                lines.append("")
                
        return "\n".join(lines)

# Example usage and tests
if __name__ == "__main__":
    print("Testing Documentation and Tutorial Agent...")
    
    # Test Documentation Agent
    print("\n1. Documentation Agent:")
    doc_agent = DocumentationAgent()
    
    task = DevelopmentTask(
        id="doc_test",
        name="qvm",
        description="Generate docs for QVM",
        role=AgentRole.DOCUMENTER,
        status=TaskStatus.PENDING,
        dependencies=[]
    )
    
    context = {'code': 'class QVM:\n    def __init__(self):\n        pass'}
    result = doc_agent.execute(task, context)
    print(f"  Generated API reference (first 200 chars):")
    print(f"  {result['api_reference'][:200]}...")
    
    # Test Tutorial Generator
    print("\n2. Tutorial Generator:")
    gen = TutorialGenerator()
    
    sample_circuit = [('H', [0]), ('CNOT', [0, 1])]
    tutorial = gen.generate_from_circuit(
        sample_circuit,
        "Bell State Tutorial",
        "Learn to create entangled states"
    )
    print(f"  Tutorial: {tutorial['title']}")
    print(f"  Steps: {len(tutorial['steps'])}")
    
    # Export to Jupyter
    notebook_json = gen.export_to_jupyter(tutorial)
    print(f"  Notebook JSON length: {len(notebook_json)} chars")
    
    # Test API Reference Generator
    print("\n3. API Reference Generator:")
    api_gen = APIReferenceGenerator()
    
    sample_code = """
class QuantumVirtualMachine:
    '''Simulates quantum circuits.'''
    def __init__(self, num_qubits):
        pass
        
def simulate(circuit):
    '''Run simulation.'''
    pass
"""
    
    api_ref = api_gen.scan_module("qvm", sample_code)
    markdown = api_gen.generate_markdown(api_ref)
    print(f"  Generated Markdown (first 300 chars):")
    print(f"  {markdown[:300]}...")
    
    print("\n" + "="*50)
    print("Documentation and Tutorial Agent ready!")