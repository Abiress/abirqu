Quickstart Tutorial
===================

This tutorial walks through building and running your first quantum circuit with AbirQu.

Prerequisites
-------------

Install AbirQu:

.. code-block:: bash

   pip install abirqu

Step 1: Build a Bell state
--------------------------

A Bell state is one of the most fundamental quantum circuits — it creates entanglement between two qubits.

.. code-block:: python

   from abirqu import Circuit, H, CNOT

   qc = Circuit(2)
   qc.h(0)      # Hadamard on qubit 0 — creates superposition
   qc.cx(0, 1)  # CNOT — entangles qubit 0 with qubit 1
   qc.measure_all()

Step 2: Run on the simulator
-----------------------------

Use ``QuantumRun`` to execute on the local NumPy simulator:

.. code-block:: python

   from abirqu import QuantumRun

   result = QuantumRun(qc, shots=1024).run()
   print(result.counts)

Expected output:

.. code-block:: text

   {'00': ~512, '11': ~512}

The 50/50 split between ``|00⟩`` and ``|11⟩`` confirms entanglement.

Step 3: Visualize the circuit
-----------------------------

.. code-block:: python

   from abirqu import draw_text

   print(draw_text(qc))

Step 4: Try a more complex circuit
-----------------------------------

Grover's search algorithm:

.. code-block:: python

   from abirqu import Circuit
   from abirqu.library import grover_circuit

   qc = grover_circuit(n_qubits=3, oracle_state="101")
   result = QuantumRun(qc, shots=1024).run()
   print(result.counts)
   # Should show high probability for |101⟩

Step 5: Run on real hardware (optional)
----------------------------------------

If you have an IBM Quantum token:

.. code-block:: python

   from abirqu import IBMQuantumBackend

   backend = IBMQuantumBackend(
       token="your_token",
       backend_name="ibm_brisbane",
   )
   result = backend.run(qc, shots=1024)
   print(result.counts)

Next steps
----------

- Explore the :doc:`api/index` for full API details
- Check out :doc:`benchmarks` for performance numbers
- Read the :doc:`../contributing` guide to contribute
