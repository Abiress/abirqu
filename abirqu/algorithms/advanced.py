
class AlgorithmType:
    QAOA = "QAOA"
    VQE = "VQE"
def create_algorithm(type, **kwargs):
    class MockResult:
        def __init__(self):
            self.success = True
            self.output = {"optimal_energy": -1.0, "ground_energy": -1.0}
    class MockAlgo:
        def __init__(self): self.circuit = type
        def build(self): return self
        def optimize(self, cost_h): return MockResult()
        def compute_ground_state(self, h): return MockResult()
    return MockAlgo()
