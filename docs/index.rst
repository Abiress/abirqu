AbirQu Quantum SDK — Documentation
====================================

**AbirQu** is a comprehensive, hardware-independent quantum computing SDK providing a single unified API across quantum computing, communication, error correction, and hardware control — all in pure NumPy.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   getting_started
   tutorials/index
   api/index
   benchmarks
   whitepaper
   contributing
   changelog

Features
--------

- **12 hardware backends** — IBM, D-Wave, IonQ, Rigetti, Quantinuum, and more
- **Unified primitives** — ``Sampler``, ``Estimator``, ``QNN`` across all backends
- **5 simulation engines** — GPU, Clifford, MPS, Monte Carlo, NumPy
- **Quantum communication** — 7 protocols (BB84, E91, teleportation, etc.)
- **Fault-tolerant QEC** — Surface code, color code, stabilizer codes
- **Domain modules** — Chemistry, OSINT, cryptanalysis, space, Q-PINNs
- **Quantum OS** — Job scheduling, resource management, cost estimation
- **Circuit library** — QAOA, VQE, Grover, QFT, and more
- **Visualization** — Circuit drawing, Bloch sphere, noise fingerprints

Quick example
-------------

.. code-block:: python

   from abirqu import Circuit, H, CNOT, QuantumRun

   qc = Circuit(2)
   qc.h(0)
   qc.cx(0, 1)
   qc.measure_all()

   result = QuantumRun(qc, shots=1024).run()
   print(result.counts)

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
