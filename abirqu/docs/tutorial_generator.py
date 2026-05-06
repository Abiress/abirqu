"""
Task 19.3 — Tutorial & Example Generator.

Generate interactive tutorials with executable code examples.
Support multiple skill levels (beginner, intermediate, advanced).
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time
import re


class SkillLevel(Enum):
    """Tutorial skill levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TutorialType(Enum):
    """Types of tutorials."""
    GETTING_STARTED = "getting_started"
    CORE_CONCEPTS = "core_concepts"
    ADVANCED_TOPICS = "advanced_topics"
    USE_CASE = "use_case"
    TROUBLESHOOTING = "troubleshooting"


@dataclass
class TutorialStep:
    """A single step in a tutorial."""
    step_id: str
    title: str
    content: str
    code: Optional[str] = None
    expected_output: Optional[str] = None
    hints: List[str] = field(default_factory=list)
    order: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_id': self.step_id,
            'title': self.title,
            'content': self.content,
            'code': self.code,
            'expected_output': self.expected_output,
            'hints': self.hints,
            'order': self.order
        }


@dataclass
class Tutorial:
    """A complete tutorial."""
    tutorial_id: str
    title: str
    type: TutorialType
    skill_level: SkillLevel
    description: str = ""
    steps: List[TutorialStep] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    author: str = "Abir Maheshwari"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tutorial_id': self.tutorial_id,
            'title': self.title,
            'type': self.type.value,
            'skill_level': self.skill_level.value,
            'description': self.description,
            'steps': [s.to_dict() for s in self.steps],
            'step_count': len(self.steps),
            'tags': self.tags,
            'author': self.author,
            'version': self.version
        }
    
    def get_step(self, step_id: str) -> Optional[TutorialStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def add_step(self, step: TutorialStep):
        """Add a step to the tutorial."""
        step.order = len(self.steps)
        self.steps.append(step)
        self.updated_at = time.time()


@dataclass
class TutorialResult:
    """Result of a tutorial operation."""
    success: bool
    tutorial_id: Optional[str] = None
    message: str = ""
    output: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'tutorial_id': self.tutorial_id,
            'message': self.message,
            'output_length': len(self.output) if self.output else 0
        }


class CodeExecutor:
    """Safely execute tutorial code examples."""
    
    def __init__(self):
        self.allowed_modules = ['numpy', 'abirqu', 'math', 'random']
        self.forbidden_patterns = ['import os', 'import sys', '__import__', 'eval', 'exec', 'open']
    
    def execute(self, code: str, context: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        Execute code safely.
        Returns: (success, output_or_error)
        """
        # Check for forbidden patterns.
        for pattern in self.forbidden_patterns:
            if pattern in code:
                return False, f"Forbidden pattern detected: {pattern}"
        
        # Create restricted globals.
        safe_globals = {
            '__builtins__': {
                'range': range,
                'len': len,
                'print': print,
                'int': int,
                'float': float,
                'str': str,
                'list': list,
                'dict': dict,
                'zip': zip,
                'enumerate': enumerate,
            }
        }
        
        # Add allowed modules.
        for module_name in self.allowed_modules:
            try:
                safe_globals[module_name] = __import__(module_name)
            except ImportError:
                pass
        
        # Add context.
        if context:
            safe_globals.update(context)
        
        try:
            # Redirect output (simplified).
            import io
            from contextlib import redirect_stdout
            
            f = io.StringIO()
            with redirect_stdout(f):
                exec(code, safe_globals)
            
            output = f.getvalue()
            return True, output or "Code executed successfully (no output)"
        
        except Exception as e:
            return False, f"Error: {str(e)}"


class ExampleGenerator:
    """Generate code examples for tutorials."""
    
    def __init__(self):
        self.templates: Dict[str, str] = {}
        self._load_templates()
    
    def _load_templates(self):
        """Load example templates."""
        self.templates['hello_quantum'] = """
from abirqu import QVM, gates

# Create a simple quantum circuit
qvm = QVM(num_qubits=1)
qvm.apply_gate(gates.H(), 0)
result = qvm.measure(0)
print(f"Measurement result: {result}")
"""
        
        self.templates['entanglement'] = """
from abirqu import QVM, gates

# Create entangled qubits
qvm = QVM(num_qubits=2)
qvm.apply_gate(gates.H(), 0)
qvm.apply_gate(gates.CNOT(), 0, 1)
results = qvm.measure_all()
print(f"Entangled state measurement: {results}")
"""
    
    def generate(self, topic: str, skill_level: SkillLevel) -> str:
        """Generate an example for a topic."""
        if topic in self.templates:
            return self.templates[topic]
        
        # Generate based on topic and skill level.
        if skill_level == SkillLevel.BEGINNER:
            return f"# Example: {topic}\n# This is a beginner-level example\nprint('Hello from {topic}!')"
        elif skill_level == SkillLevel.INTERMEDIATE:
            return f"# Example: {topic}\n# This is an intermediate example\nimport numpy as np\nprint('Intermediate {topic} example')"
        else:
            return f"# Example: {topic}\n# Advanced example\n# Implementing {topic} with custom parameters\nprint('Advanced {topic}')"
    
    def validate(self, code: str) -> Tuple[bool, str]:
        """Validate example code."""
        if not code.strip():
            return False, "Empty code"
        
        # Check for basic syntax.
        try:
            compile(code, '<string>', 'exec')
            return True, "Valid code"
        except SyntaxError as e:
            return False, f"Syntax error: {e}"


class TutorialGenerator:
    """Main tutorial generator."""
    
    def __init__(self):
        self.tutorials: Dict[str, Tutorial] = {}
        self.executor = CodeExecutor()
        self.example_gen = ExampleGenerator()
        self.tutorial_counter = 0
    
    def create_tutorial(self, title: str,
                        type: TutorialType,
                        skill_level: SkillLevel,
                        description: str = "",
                        tags: Optional[List[str]] = None) -> Tutorial:
        """Create a new tutorial."""
        self.tutorial_counter += 1
        tutorial_id = f"tutorial_{self.tutorial_counter}"
        
        tutorial = Tutorial(
            tutorial_id=tutorial_id,
            title=title,
            type=type,
            skill_level=skill_level,
            description=description,
            tags=tags or []
        )
        
        self.tutorials[tutorial_id] = tutorial
        return tutorial
    
    def add_step(self, tutorial_id: str,
                  title: str,
                  content: str,
                  code: Optional[str] = None,
                  expected_output: Optional[str] = None,
                  hints: Optional[List[str]] = None) -> TutorialResult:
        """Add a step to a tutorial."""
        if tutorial_id not in self.tutorials:
            return TutorialResult(
                success=False,
                message=f"Tutorial {tutorial_id} not found"
            )
        
        tutorial = self.tutorials[tutorial_id]
        step_id = f"step_{len(tutorial.steps) + 1}"
        
        step = TutorialStep(
            step_id=step_id,
            title=title,
            content=content,
            code=code,
            expected_output=expected_output,
            hints=hints or []
        )
        
        tutorial.add_step(step)
        
        return TutorialResult(
            success=True,
            tutorial_id=tutorial_id,
            message=f"Step {step_id} added"
        )
    
    def generate_examples(self, tutorial_id: str) -> TutorialResult:
        """Generate code examples for all steps in a tutorial."""
        if tutorial_id not in self.tutorials:
            return TutorialResult(
                success=False,
                message=f"Tutorial {tutorial_id} not found"
            )
        
        tutorial = self.tutorials[tutorial_id]
        generated = 0
        
        for step in tutorial.steps:
            if step.code is None:
                # Generate example based on step title/topic.
                code = self.example_gen.generate(
                    topic=step.title,
                    skill_level=tutorial.skill_level
                )
                step.code = code
                generated += 1
        
        return TutorialResult(
            success=True,
            tutorial_id=tutorial_id,
            message=f"Generated {generated} code examples",
            metadata={'generated_count': generated}
        )
    
    def execute_step(self, tutorial_id: str, step_id: str) -> TutorialResult:
        """Execute code for a tutorial step."""
        if tutorial_id not in self.tutorials:
            return TutorialResult(
                success=False,
                message=f"Tutorial {tutorial_id} not found"
            )
        
        tutorial = self.tutorials[tutorial_id]
        step = tutorial.get_step(step_id)
        
        if step is None:
            return TutorialResult(
                success=False,
                message=f"Step {step_id} not found"
            )
        
        if step.code is None:
            return TutorialResult(
                success=False,
                message="No code to execute"
            )
        
        success, output = self.executor.execute(step.code)
        
        return TutorialResult(
            success=success,
            tutorial_id=tutorial_id,
            output=output,
            metadata={'step_id': step_id}
        )
    
    def get_tutorial(self, tutorial_id: str) -> Optional[Tutorial]:
        """Get a tutorial by ID."""
        return self.tutorials.get(tutorial_id)
    
    def list_tutorials(self,
                       type: Optional[TutorialType] = None,
                       skill_level: Optional[SkillLevel] = None,
                       tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """List tutorials with optional filtering."""
        result = []
        
        for tutorial in self.tutorials.values():
            if type and tutorial.type != type:
                continue
            if skill_level and tutorial.skill_level != skill_level:
                continue
            if tag and tag not in tutorial.tags:
                continue
            result.append(tutorial.to_dict())
        
        return result
    
    def search_tutorials(self, query: str) -> List[Dict[str, Any]]:
        """Search tutorials by title and description."""
        query_lower = query.lower()
        result = []
        
        for tutorial in self.tutorials.values():
            if (query_lower in tutorial.title.lower() or
                query_lower in tutorial.description.lower() or
                any(query_lower in tag for tag in tutorial.tags)):
                result.append(tutorial.to_dict())
        
        return result
    
    def export_tutorial(self, tutorial_id: str,
                        format: str = "markdown") -> Optional[str]:
        """Export tutorial to specified format."""
        if tutorial_id not in self.tutorials:
            return None
        
        tutorial = self.tutorials[tutorial_id]
        
        if format == "markdown":
            md = f"# {tutorial.title}\n\n"
            md += f"**Type:** {tutorial.type.value}\n"
            md += f"**Level:** {tutorial.skill_level.value}\n"
            md += f"**Author:** {tutorial.author}\n\n"
            md += f"## Description\n\n{tutorial.description}\n\n"
            
            for step in tutorial.steps:
                md += f"### Step {step.order + 1}: {step.title}\n\n"
                md += f"{step.content}\n\n"
                if step.code:
                    md += f"```python\n{step.code}\n```\n\n"
                if step.expected_output:
                    md += f"**Expected Output:**\n```\n{step.expected_output}\n```\n\n"
            
            return md
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get tutorial statistics."""
        stats = {
            'total_tutorials': len(self.tutorials),
            'by_type': {},
            'by_skill_level': {},
            'total_steps': 0
        }
        
        for tutorial in self.tutorials.values():
            # By type.
            type_name = tutorial.type.value
            stats['by_type'][type_name] = stats['by_type'].get(type_name, 0) + 1
            
            # By skill level.
            level_name = tutorial.skill_level.value
            stats['by_skill_level'][level_name] = stats['by_skill_level'].get(level_name, 0) + 1
            
            # Total steps.
            stats['total_steps'] += len(tutorial.steps)
        
        return stats
