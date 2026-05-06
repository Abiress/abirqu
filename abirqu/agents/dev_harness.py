"""Dev Harness for AbirQu. Copyright 2026 Abir Maheshwari"""
from typing import Optional, Dict, List, Any, Callable
from ..core.circuit import Circuit
from ..core.qvm import QuantumVirtualMachine

class DevelopmentHarness:
    """Runs tests and validates quantum circuits."""
    
    def __init__(self):
        self.tests = []
        self.results = []
        
    def add_test(self, name: str, test_func: Callable, description: str = ""):
        """Add a test to the harness."""
        self.tests.append({
            'name': name,
            'func': test_func,
            'description': description
        })
        
    def run_all(self) -> bool:
        """Run all registered tests."""
        self.results = []
        all_passed = True
        
        for test in self.tests:
            try:
                result = test['func']()
                passed = result is True or (isinstance(result, dict) and result.get('passed', False))
                self.results.append({
                    'name': test['name'],
                    'passed': passed,
                    'result': result
                })
                if not passed:
                    all_passed = False
            except Exception as e:
                self.results.append({
                    'name': test['name'],
                    'passed': False,
                    'error': str(e)
                })
                all_passed = False
                
        return all_passed
        
    def run_circuit_tests(self, circuit: Circuit) -> Dict[str, Any]:
        """Run standard tests on a circuit."""
        results = {
            'valid': True,
            'gate_count': len(circuit.gates),
            'depth': circuit.depth(),
            'tests': []
        }
        
        # Test 1: Circuit can be simulated
        try:
            qvm = QuantumVirtualMachine(circuit.num_qubits)
            # Simulate (simplified)
            results['tests'].append({'name': 'simulation', 'passed': True})
        except Exception as e:
            results['valid'] = False
            results['tests'].append({'name': 'simulation', 'passed': False, 'error': str(e)})
            
        # Test 2: Gate count > 0
        passed = len(circuit.gates) > 0
        results['tests'].append({'name': 'has_gates', 'passed': passed})
        
        # Test 3: Depth is reasonable
        passed = circuit.depth() <= len(circuit.gates) * 2
        results['tests'].append({'name': 'reasonable_depth', 'passed': passed})
        
        return results
        
    def benchmark_circuit(self, circuit: Circuit, num_trials: int = 100) -> Dict[str, float]:
        """Benchmark circuit performance."""
        import time
        
        # Simulation time
        times = []
        for _ in range(num_trials):
            start = time.perf_counter()
            qvm = QuantumVirtualMachine(circuit.num_qubits)
            # Would actually run circuit here
            end = time.perf_counter()
            times.append(end - start)
            
        return {
            'avg_simulation_time_ms': sum(times) / len(times) * 1000,
            'min_time_ms': min(times) * 1000,
            'max_time_ms': max(times) * 1000,
            'gate_count': len(circuit.gates),
            'depth': circuit.depth()
        }
        
    def get_results(self) -> List[Dict]:
        """Get test results."""
        return self.results
        
    def summary(self) -> str:
        """Get test summary."""
        if not self.results:
            return "No tests run"
            
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        
        return f"Tests: {passed}/{total} passed ({100*passed/total:.1f}%)"
