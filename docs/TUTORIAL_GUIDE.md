# AbirQu Tutorial Guide

Target version: AbirQu v0.1.0 Alpha

This guide is designed as a practical learning path, similar in spirit to hands-on flows used in major quantum SDK ecosystems.

## Learning Path

1. Build your first circuit
2. Run local simulation
3. Analyze measurement output
4. Use interchange formats
5. Use SDK compatibility and backend routing
6. Apply optimization and mitigation flows

## Tutorial 1: Your First Circuit

```python
from abirqu.circuit import Circuit
from abirqu.simulator import SimulatorBackend

qc = Circuit(2)
qc.h(0)
qc.cnot(0, 1)
qc.measure_all()

result = SimulatorBackend().run(qc, shots=1024)
print(result["counts"])
```

Expected behavior:
- Most counts in `00` and `11`
- Near-balanced Bell distribution

## Tutorial 2: Parameterized Circuits

```python
from abirqu.circuit import Circuit
from abirqu.simulator import SimulatorBackend

qc = Circuit(1)
qc.ry(0, 1.2)
qc.measure_all()

print(SimulatorBackend().run(qc, shots=512)["counts"])
```

## Tutorial 3: Algorithm Templates

```python
from abirqu.algorithms import grover_search

qc = grover_search(target_state=1, num_qubits=3)
print(qc.run(shots=512)["counts"])
```

## Tutorial 4: Transpilation and Routing

```python
from abirqu.circuit import Circuit
from abirqu.optimize.transpiler import HardwareAwareTranspiler

qc = Circuit(3)
qc.h(0)
qc.cnot(0, 2)

tr = HardwareAwareTranspiler("IBM")
tr.set_coupling_map([(0, 1), (1, 2)])
out = tr.transpile(qc)
print(out.stats)
```

## Tutorial 5: Interchange Conversion

```python
from abirqu import AbirQuSDK

sdk = AbirQuSDK()
qasm = """OPENQASM 2.0;
qreg q[2];
h q[0];
cx q[0], q[1];
"""

quil = sdk.convert_interchange("openqasm2", "quil", qasm)
print(quil)
```

## Tutorial 6: Compatibility Report

```python
from abirqu import AbirQuSDK

sdk = AbirQuSDK()
report = sdk.compatibility_report()
print(report["summary"])
```

## Tutorial 7: Backend Routing Dry-Run

```python
from abirqu import AbirQuSDK
from abirqu.circuit import Circuit

sdk = AbirQuSDK()
qc = Circuit(2).h(0).cnot(0, 1)

print(sdk.run_on_backend(qc, provider="local", shots=128))
print(sdk.run_on_backend(qc, provider="rigetti", shots=128, dry_run=True))
```

## Tutorial 8: Notebook and Colab Workflow

Notebook cell plan:
- Cell 1: install and imports
- Cell 2: build circuit
- Cell 3: run simulator and inspect counts
- Cell 4: run compatibility report
- Cell 5: try format conversion

Colab quick start:

```python
!pip install abirqu
```

## Tutorial 9: Testing Your Changes

```bash
source .venv/bin/activate
PYTHONPATH=. pytest -q tests/test_phase1_8_smoke.py tests/test_sdk_compatibility.py tests/test_sdk_full_wiring.py
```

## Tutorial 10: Contributing a New Phase Feature

Suggested process:
1. Implement code in the relevant `abirqu/phases/phaseXX.py`
2. Add tests under `tests/`
3. Add or update `templates/phases/phaseXX_template.md`
4. Update README and this guide with only verified claims

## Common Pitfalls

- Missing optional provider dependencies for cloud adapters
- Running without proper credentials for provider APIs
- Assuming dry-run equals live hardware execution
- Assuming PyPI availability before release is published

## What to Read Next

- `README.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `THREAT_MODEL.md`
