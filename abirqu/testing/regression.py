"""
Task 14.5 — Regression & Continuous Testing.

Quantum circuit regression test suite, CI/CD integration, snapshot testing, test dashboard, auto test generation.
"""
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class TestStatus(Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class RegressionResult:
    """Result of regression test."""
    test_name: str
    status: TestStatus
    runtime: float  # seconds
    output: Any = None
    expected: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'status': self.status.value,
            'runtime': self.runtime,
            'output': str(self.output) if self.output else None,
            'expected': str(self.expected) if self.expected else None,
            'error': self.error,
            'metadata': self.metadata
        }


class QuantumRegressionSuite:
    """Regression test suite for quantum circuits."""
    
    def __init__(self, suite_name: str = "default"):
        self.suite_name = suite_name
        self.tests: List[Dict[str, Any]] = []
        self.results: List[RegressionResult] = []
        self.snapshots: Dict[str, Any] = {}
    
    def add_test(self, name: str, circuit_func: callable,
                 expected_output: Optional[Any] = None,
                 tolerance: float = 1e-6):
        """Add a test to the suite."""
        self.tests.append({
            'name': name,
            'func': circuit_func,
            'expected': expected_output,
            'tolerance': tolerance
        })
    
    def run_all(self) -> List[RegressionResult]:
        """Run all tests in the suite."""
        self.results = []
        
        for test in self.tests:
            start = time.time()
            
            try:
                output = test['func']()
                runtime = time.time() - start
                
                # Check against expected.
                status = TestStatus.PASSED
                error = None
                
                if test['expected'] is not None:
                    if isinstance(output, (int, float, complex)):
                        if abs(output - test['expected']) > test['tolerance']:
                            status = TestStatus.FAILED
                    elif hasattr(output, '__iter__'):
                        # Compare arrays/vectors.
                        import numpy as np
                        if not np.allclose(output, test['expected'], 
                                           atol=test['tolerance']):
                            status = TestStatus.FAILED
                
                result = RegressionResult(
                    test_name=test['name'],
                    status=status,
                    runtime=runtime,
                    output=output,
                    expected=test['expected'],
                    error=error,
                    metadata={'tolerance': test['tolerance']}
                )
                
            except Exception as e:
                runtime = time.time() - start
                result = RegressionResult(
                    test_name=test['name'],
                    status=TestStatus.ERROR,
                    runtime=runtime,
                    error=str(e),
                    metadata={'exception': type(e).__name__}
                )
            
            self.results.append(result)
        
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        
        return {
            'suite_name': self.suite_name,
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'pass_rate': passed / total if total > 0 else 0,
            'avg_runtime': sum(r.runtime for r in self.results) / total if total > 0 else 0
        }
    
    def save_snapshot(self, name: str, state: Any):
        """Save quantum state snapshot."""
        self.snapshots[name] = {
            'state': state,
            'timestamp': time.time()
        }
    
    def compare_snapshot(self, name: str, current_state: Any) -> bool:
        """Compare current state with snapshot."""
        if name not in self.snapshots:
            return False
        
        import numpy as np
        saved = self.snapshots[name]['state']
        
        if hasattr(saved, '__iter__') and hasattr(current_state, '__iter__'):
            return np.allclose(saved, current_state, atol=1e-6)
        else:
            return saved == current_state


class CIRegression:
    """Continuous testing in CI/CD pipelines."""
    
    def __init__(self, ci_platform: str = "github"):
        self.ci_platform = ci_platform
        self.pipeline_results: List[Dict] = []
    
    def run_pipeline(self, test_suites: List[QuantumRegressionSuite]) -> Dict:
        """
        Run test pipeline in CI.
        
        Args:
            test_suites: List of test suites to run.
            
        Returns:
            Pipeline result dictionary.
        """
        pipeline_start = time.time()
        all_results = []
        
        for suite in test_suites:
            suite_results = suite.run_all()
            all_results.extend(suite_results)
        
        pipeline_runtime = time.time() - pipeline_start
        
        # Check for failures.
        failures = [r for r in all_results if r.status != TestStatus.PASSED]
        success = len(failures) == 0
        
        result = {
            'success': success,
            'total_tests': len(all_results),
            'passed': sum(1 for r in all_results if r.status == TestStatus.PASSED),
            'failed': len(failures),
            'runtime': pipeline_runtime,
            'failures': [r.to_dict() for r in failures[:10]],  # Limit.
            'ci_platform': self.ci_platform
        }
        
        self.pipeline_results.append(result)
        return result
    
    def generate_ci_config(self, filepath: str):
        """Generate CI configuration file."""
        if self.ci_platform == "github":
            config = self._github_actions_config()
        elif self.ci_platform == "gitlab":
            config = self._gitlab_ci_config()
        else:
            config = self._generic_config()
        
        with open(filepath, 'w') as f:
            f.write(config)
    
    def _github_actions_config(self) -> str:
        """Generate GitHub Actions workflow."""
        return """name: Quantum Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -e .
      - name: Run quantum tests
        run: python -m pytest tests/ -v
"""
    
    def _gitlab_ci_config(self) -> str:
        """Generate GitLab CI config."""
        return """test_quantum:
  stage: test
  script:
    - pip install -e .
    - python -m pytest tests/ -v
"""
    
    def _generic_config(self) -> str:
        return "# Generic CI config - customize for your platform\n"


class SnapshotTester:
    """Snapshot testing for quantum states."""
    
    def __init__(self, snapshot_dir: str = ".snapshots"):
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(exist_ok=True)
    
    def save_snapshot(self, name: str, data: Any):
        """Save snapshot to file."""
        filepath = self.snapshot_dir / f"{name}.json"
        
        # Convert data to JSON-serializable format.
        if hasattr(data, 'tolist'):  # NumPy array.
            serializable = data.tolist()
        elif isinstance(data, complex):
            serializable = {'real': data.real, 'imag': data.imag}
        else:
            serializable = data
        
        with open(filepath, 'w') as f:
            json.dump({'data': serializable, 'timestamp': time.time()}, f)
    
    def load_snapshot(self, name: str) -> Any:
        """Load snapshot from file."""
        filepath = self.snapshot_dir / f"{name}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r') as f:
            content = json.load(f)
        
        return content['data']
    
    def assert_match(self, name: str, current: Any) -> bool:
        """
        Assert current state matches snapshot.
        
        Returns:
            True if match, False otherwise.
        """
        saved = self.load_snapshot(name)
        
        if saved is None:
            # No snapshot exists, save current.
            self.save_snapshot(name, current)
            return True
        
        # Compare.
        import numpy as np
        if isinstance(saved, list) and hasattr(current, '__iter__'):
            return np.allclose(np.array(saved), current, atol=1e-6)
        else:
            return saved == current


class TestDashboard:
    """Test result dashboard with trend analysis."""
    
    def __init__(self):
        self.history: List[Dict] = []
    
    def add_run(self, results: List[RegressionResult], 
                metadata: Optional[Dict] = None):
        """Add a test run to history."""
        summary = {
            'timestamp': time.time(),
            'total': len(results),
            'passed': sum(1 for r in results if r.status == TestStatus.PASSED),
            'failed': sum(1 for r in results if r.status == TestStatus.FAILED),
            'errors': sum(1 for r in results if r.status == TestStatus.ERROR),
            'avg_runtime': sum(r.runtime for r in results) / len(results) if results else 0
        }
        
        if metadata:
            summary['metadata'] = metadata
        
        self.history.append(summary)
    
    def get_trend(self, metric: str = 'pass_rate') -> List[float]:
        """Get trend data for a metric."""
        if metric == 'pass_rate':
            return [r['passed'] / r['total'] for r in self.history if r['total'] > 0]
        elif metric == 'avg_runtime':
            return [r['avg_runtime'] for r in self.history]
        else:
            return []
    
    def export_html(self, filepath: str):
        """Export dashboard as HTML."""
        html = self._generate_html()
        with open(filepath, 'w') as f:
            f.write(html)
    
    def _generate_html(self) -> str:
        """Generate HTML dashboard."""
        lines = []
        lines.append("<html><head><title>Test Dashboard</title></head>")
        lines.append("<body>")
        lines.append("<h1>Quantum Test Dashboard</h1>")
        lines.append(f"<p>Total runs: {len(self.history)}</p>")
        
        if self.history:
            latest = self.history[-1]
            lines.append("<h2>Latest Run</h2>")
            lines.append(f"<p>Passed: {latest['passed']}/{latest['total']}</p>")
            lines.append(f"<p>Average runtime: {latest['avg_runtime']:.2f}s</p>")
        
        lines.append("</body></html>")
        return "\n".join(lines)


class AutoTestGenerator:
    """Automatic test generation from circuit specifications."""
    
    def __init__(self):
        self.generation_rules: List[callable] = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default test generation rules."""
        self.generation_rules.append(self._rule_unitarity)
        self.generation_rules.append(self._rule_normalization)
        self.generation_rules.append(self._rule_hermitian)
    
    def generate_tests(self, circuit_spec: Dict) -> List[Dict]:
        """
        Generate tests from circuit specification.
        
        Args:
            circuit_spec: Circuit specification dictionary.
            
        Returns:
            List of test dictionaries.
        """
        tests = []
        
        for rule in self.generation_rules:
            test = rule(circuit_spec)
            if test:
                tests.append(test)
        
        return tests
    
    def _rule_unitarity(self, spec: Dict) -> Optional[Dict]:
        """Generate test: circuit should be unitary."""
        if 'unitary' in spec or spec.get('type') == 'unitary':
            return {
                'name': f"test_unitarity_{spec.get('name', 'unknown')}",
                'type': 'unitarity',
                'check': lambda U: np.allclose(U @ U.conj().T, np.eye(len(U)))
            }
        return None
    
    def _rule_normalization(self, spec: Dict) -> Optional[Dict]:
        """Generate test: output state should be normalized."""
        return {
            'name': 'test_normalization',
            'type': 'normalization',
            'check': lambda state: np.isclose(np.linalg.norm(state), 1.0, atol=1e-6)
        }
    
    def _rule_hermitian(self, spec: Dict) -> Optional[Dict]:
        """Generate test: operator should be Hermitian."""
        if spec.get('type') == 'observable':
            return {
                'name': f"test_hermitian_{spec.get('name', 'unknown')}",
                'type': 'hermitian',
                'check': lambda O: np.allclose(O, O.conj().T)
            }
        return None
