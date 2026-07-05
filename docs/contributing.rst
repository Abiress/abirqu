Contributing
============

We welcome contributions to AbirQu! This page summarizes the contributing workflow.

.. include:: ../CONTRIBUTING.md
   :parser: myst_parser.sphinx_

For the full guide, see `CONTRIBUTING.md <https://github.com/Abiress/abirqu/blob/main/CONTRIBUTING.md>`_ in the repository.

Quick start
-----------

1. Fork the repository
2. Create a feature branch: ``git checkout -b feature/my-feature``
3. Make your changes
4. Run tests: ``pytest tests/``
5. Submit a pull request

Development setup
-----------------

.. code-block:: bash

   git clone https://github.com/Abiress/abirqu.git
   cd abirqu
   pip install -e ".[dev]"
   pytest tests/

Code standards
--------------

- Follow PEP 8 (enforced by ``ruff``)
- Line length: 100 characters
- All public APIs must have docstrings
- All changes must include tests
- Run ``ruff check .`` before committing

Project structure
-----------------

.. code-block:: text

   abirqu/
   ├── circuit.py        # Circuit, Gate, Measurement
   ├── gates.py          # Quantum gates (X, Y, Z, H, CNOT, ...)
   ├── backend.py        # Backend interface
   ├── backends/         # Hardware provider implementations
   ├── transpiler/       # Circuit transpilation
   ├── primitives/       # Sampler, Estimator, QNN
   ├── library/          # Circuit library (QAOA, VQE, Grover, ...)
   ├── visualization/    # Drawing, Bloch sphere, histograms
   ├── chemistry/        # Quantum chemistry module
   ├── osint/            # Graph intelligence module
   ├── crypto/           # Cryptanalysis module
   ├── space/            # HHL solver, Q-PINNs
   ├── qec/              # Quantum error correction
   └── tests/            # Test suite
