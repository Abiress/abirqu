# Contributing to AbirQu

## Priority Areas (where help is needed)

1. **Rayon parallelization** — Close the 20q+ gap with Cirq
2. **Phase polynomial optimizer** — Implement real parity-matrix optimization
3. **GPU kernels** — CUDA/Metal native simulation
4. **Hardware backend testing** — Connect to real IBM/Google hardware
5. **Documentation** — API docs, tutorials, examples

## Development Setup

```bash
git clone https://github.com/abirqu/abirqu.git
cd abirqu
python -m venv venv
source venv/bin/activate
pip install maturin
maturin develop --release
pip install -e .
```

## Testing

Run `python test_features.py` before submitting any PR.
All benchmarks must pass with TVD < 0.01 against reference implementations.