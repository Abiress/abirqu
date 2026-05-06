"""
Task 20.3 — Load Testing Framework.

Simulate multiple concurrent users running quantum circuits.
Measure system behavior under load.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics


class LoadTestType(Enum):
    """Types of load tests."""
    CONCURRENT_USERS = "concurrent_users"
    RAMP_UP = "ramp_up"
    Spike = "spike"
    ENDURANCE = "endurance"
    STRESS = "stress"


class LoadTestStatus(Enum):
    """Status of a load test."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class LoadTestConfig:
    """Configuration for a load test."""
    name: str
    type: LoadTestType
    num_users: int = 10
    duration_sec: int = 60
    ramp_up_sec: int = 10
    requests_per_user: int = 100
    think_time_ms: int = 100  # Time between requests.
    circuit_type: str = "random"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type.value,
            'num_users': self.num_users,
            'duration_sec': self.duration_sec,
            'ramp_up_sec': self.ramp_up_sec,
            'requests_per_user': self.requests_per_user,
            'think_time_ms': self.think_time_ms
        }


@dataclass
class UserResult:
    """Results for a single virtual user."""
    user_id: str
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'total_requests': self.total_requests,
            'successful': self.successful,
            'failed': self.failed,
            'success_rate': self.successful / max(self.total_requests, 1),
            'avg_response_time': self.total_time / max(self.total_requests, 1),
            'min_time': self.min_time if self.min_time != float('inf') else 0,
            'max_time': self.max_time,
            'errors': self.errors
        }


@dataclass
class LoadTestResult:
    """Result of a load test."""
    config: LoadTestConfig
    status: LoadTestStatus
    start_time: float
    end_time: Optional[float] = None
    user_results: List[UserResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'config': self.config.to_dict(),
            'status': self.status.value,
            'duration': (self.end_time or time.time()) - self.start_time,
            'user_results': [r.to_dict() for r in self.user_results],
            'statistics': self._calculate_statistics()
        }
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate aggregate statistics."""
        if not self.user_results:
            return {}
        
        all_times = []
        total_requests = 0
        total_success = 0
        total_failed = 0
        
        for ur in self.user_results:
            total_requests += ur.total_requests
            total_success += ur.successful
            total_failed += ur.failed
        
        return {
            'total_requests': total_requests,
            'total_successful': total_success,
            'total_failed': total_failed,
            'overall_success_rate': total_success / max(total_requests, 1),
            'requests_per_second': total_requests / max(self.to_dict()['duration'], 1)
        }


class VirtualUser:
    """Simulates a single virtual user."""
    
    def __init__(self, user_id: str, config: LoadTestConfig):
        self.user_id = user_id
        self.config = config
        self.result = UserResult(user_id=user_id)
        self.stop_flag = threading.Event()
        self.executor_fn: Optional[Callable] = None
    
    def set_executor(self, fn: Callable):
        """Set the function to execute for each request."""
        self.executor_fn = fn
    
    def run(self):
        """Run the user simulation."""
        start_time = time.time()
        
        for _ in range(self.config.requests_per_user):
            if self.stop_flag.is_set():
                break
            
            if time.time() - start_time > self.config.duration_sec:
                break
            
            # Execute request.
            if self.executor_fn:
                try:
                    req_start = time.perf_counter()
                    self.executor_fn()
                    req_time = time.perf_counter() - req_start
                    
                    self.result.total_time += req_time
                    self.result.min_time = min(self.result.min_time, req_time)
                    self.result.max_time = max(self.result.max_time, req_time)
                    self.result.successful += 1
                except Exception as e:
                    self.result.failed += 1
                    self.result.errors.append(str(e))
            
            self.result.total_requests += 1
            
            # Think time.
            if self.config.think_time_ms > 0:
                time.sleep(self.config.think_time_ms / 1000.0)
        
        return self.result
    
    def stop(self):
        """Stop the user."""
        self.stop_flag.set()


class CircuitLoadGenerator:
    """Generate load test circuits."""
    
    def __init__(self):
        self.circuit_templates = {
            'simple': [('h', 0), ('measure', 0)],
            'bell': [('h', 0), ('cnot', 0, 1), ('measure', 0), ('measure', 1)],
            'random': None  # Generated dynamically.
        }
    
    def generate(self, type: str, num_qubits: int = 5, depth: int = 10) -> List[Tuple]:
        """Generate a circuit for load testing."""
        if type == 'simple':
            return self.circuit_templates['simple'].copy()
        elif type == 'bell':
            return self.circuit_templates['bell'].copy()
        elif type == 'random':
            import random
            gates = ['h', 't', 's', 'cnot', 'rx', 'ry']
            circuit = []
            for _ in range(depth):
                gate = random.choice(gates)
                if gate == 'cnot' and num_qubits >= 2:
                    q1 = random.randint(0, num_qubits - 1)
                    q2 = random.randint(0, num_qubits - 1)
                    if q1 != q2:
                        circuit.append(('cnot', q1, q2))
                else:
                    q = random.randint(0, num_qubits - 1)
                    circuit.append((gate, q))
            return circuit
        return []
    
    def get_executor(self, type: str):
        """Get an executor function for the circuit type."""
        circuit = self.generate(type)
        
        def execute():
            # Simulate circuit execution.
            time.sleep(0.001)  # Simulate 1ms execution.
            return {'result': 'simulated', 'circuit': circuit}
        
        return execute


class LoadTester:
    """Main load testing framework."""
    
    def __init__(self):
        self.tests: Dict[str, LoadTestResult] = {}
        self.users: List[VirtualUser] = []
        self.generator = CircuitLoadGenerator()
        self.test_counter = 0
        self.active_test: Optional[str] = None
    
    def create_test(self, config: LoadTestConfig) -> str:
        """Create a new load test."""
        self.test_counter += 1
        test_id = f"loadtest_{self.test_counter}"
        
        result = LoadTestResult(
            config=config,
            status=LoadTestStatus.PENDING,
            start_time=time.time()
        )
        
        self.tests[test_id] = result
        return test_id
    
    def run_test(self, test_id: str) -> LoadTestResult:
        """Run a load test."""
        if test_id not in self.tests:
            raise ValueError(f"Test {test_id} not found")
        
        result = self.tests[test_id]
        result.status = LoadTestStatus.RUNNING
        self.active_test = test_id
        
        config = result.config
        
        # Get executor function.
        executor = self.generator.get_executor(config.circuit_type)
        
        # Create virtual users.
        users = []
        for i in range(config.num_users):
            user = VirtualUser(
                user_id=f"user_{i}",
                config=config
            )
            user.set_executor(executor)
            users.append(user)
        
        # Run users (with ramp-up if specified).
        self.users = users
        results = []
        
        with ThreadPoolExecutor(max_workers=config.num_users) as executor_pool:
            futures = []
            
            for i, user in enumerate(users):
                # Ramp-up delay.
                if config.ramp_up_sec > 0 and config.type == LoadTestType.RAMP_UP:
                    delay = (config.ramp_up_sec / config.num_users) * i
                    time.sleep(delay)
                
                future = executor_pool.submit(user.run)
                futures.append(future)
            
            # Collect results.
            for future in as_completed(futures):
                try:
                    user_result = future.result()
                    results.append(user_result)
                except Exception as e:
                    # Create error result.
                    error_result = UserResult(user_id="unknown")
                    error_result.failed += 1
                    error_result.errors.append(str(e))
                    results.append(error_result)
        
        result.user_results = results
        result.status = LoadTestStatus.COMPLETED
        result.end_time = time.time()
        self.active_test = None
        
        return result
    
    def cancel_test(self, test_id: str) -> bool:
        """Cancel a running test."""
        if test_id not in self.tests:
            return False
        
        # Stop all users.
        for user in self.users:
            user.stop()
        
        result = self.tests[test_id]
        result.status = LoadTestStatus.CANCELLED
        result.end_time = time.time()
        
        return True
    
    def get_test(self, test_id: str) -> Optional[LoadTestResult]:
        """Get a test result."""
        return self.tests.get(test_id)
    
    def list_tests(self) -> List[Dict[str, Any]]:
        """List all load tests."""
        return [
            {
                'test_id': tid,
                'name': r.config.name,
                'type': r.config.type.value,
                'status': r.status.value,
                'num_users': r.config.num_users,
                'duration': (r.end_time or time.time()) - r.start_time
            }
            for tid, r in self.tests.items()
        ]
    
    def compare_tests(self, test_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple load test results."""
        comparison = {}
        
        for tid in test_ids:
            result = self.tests.get(tid)
            if result:
                stats = result._calculate_statistics()
                comparison[tid] = {
                    'name': result.config.name,
                    'total_requests': stats.get('total_requests', 0),
                    'success_rate': stats.get('overall_success_rate', 0),
                    'requests_per_second': stats.get('requests_per_second', 0)
                }
        
        return comparison
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load tester statistics."""
        total_tests = len(self.tests)
        completed = sum(1 for r in self.tests.values() if r.status == LoadTestStatus.COMPLETED)
        
        return {
            'total_tests': total_tests,
            'completed': completed,
            'running': sum(1 for r in self.tests.values() if r.status == LoadTestStatus.RUNNING),
            'total_users_simulated': sum(
                r.config.num_users for r in self.tests.values()
            )
        }
