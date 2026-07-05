Getting Started
===============

Installation
------------

Install from PyPI:

.. code-block:: bash

   pip install abirqu

Or install from source:

.. code-block:: bash

   git clone https://github.com/Abiress/abirqu.git
   cd abirqu
   pip install -e .

Optional extras:

.. code-block:: bash

   pip install abirqu[ibm]       # IBM Quantum backend
   pip install abirqu[dwave]     # D-Wave annealing
   pip install abirqu[gpu]       # GPU acceleration (CuPy)
   pip install abirqu[visualization]  # Matplotlib plots
   pip install abirqu[all-hardware]   # All verified backends

Requirements
------------

- Python >= 3.9
- NumPy >= 1.21
- SciPy >= 1.7
- NetworkX >= 2.6

Your first circuit
------------------

.. code-block:: python

   from abirqu import Circuit, H, CNOT, QuantumRun

   # Build a Bell state
   qc = Circuit(2)
   qc.h(0)
   qc.cx(0, 1)
   qc.measure_all()

   # Run on the local NumPy simulator
   result = QuantumRun(qc, shots=1024).run()
   print(result.counts)
   # {'00': ~512, '11': ~512}

Running on real hardware
------------------------

AbirQu supports 12 hardware providers. For IBM Quantum:

.. code-block:: python

   from abirqu import Circuit, H, CNOT, IBMQuantumBackend

   qc = Circuit(2)
   qc.h(0)
   qc.cx(0, 1)
   qc.measure_all()

   backend = IBMQuantumBackend(
       token="your_ibm_token",
       backend_name="ibm_brisbane",
   )
   result = backend.run(qc, shots=1024)
   print(result.counts)

See the :doc:`tutorials/index` for step-by-step guides.

Next steps
----------

- :doc:`tutorials/quickstart` — Walk through your first algorithm
- :doc:`api/index` — Full API reference
- :doc:`benchmarks` — Performance benchmarks
- `GitHub <https://github.com/Abiress/abirqu>`_ — Source code
