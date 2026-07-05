Benchmarks
==========

Real, reproducible benchmarks measured on local NumPy simulator (Intel, 64 threads).

Circuit Performance
-------------------

.. list-table::
   :header-rows: 1
   :widths: 25 15 15 15 15

   * - Circuit
     - Qubits
     - Gates
     - Depth
     - Time
   * - QFT
     - 8
     - 96
     - 42
     - 43 ms
   * - QFT
     - 12
     - 216
     - 66
     - 1.4 s
   * - Random
     - 10q × 20d
     - 300
     - —
     - 775 ms
   * - VQE
     - 8q × 3 reps
     - 69
     - —
     - 50 ms
   * - GHZ
     - 10
     - 9
     - 10
     - 10 ms
   * - Full pipeline
     - 10
     - 29
     - —
     - 86 ms

Running benchmarks yourself
---------------------------

.. code-block:: bash

   python benchmarks/run_benchmarks.py

The benchmark suite tests:

- Circuit construction time
- Gate decomposition
- Simulation (NumPy, GPU if available)
- End-to-end execution with measurement
- Noise model overhead

Comparison with other SDKs
--------------------------

AbirQu focuses on **breadth** (12 backends, 7 communication protocols, 6 domain modules) rather than raw simulation speed. For production-grade hardware execution, consider Qiskit (IBM), Cirq (Google), or Braket (Amazon).
