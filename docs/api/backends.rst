Backends API
============

AbirQu supports 12 hardware backends with a unified interface.

Base Backend
------------

.. automodule:: abirqu.backend
   :members:
   :undoc-members:
   :show-inheritance:

Hardware Backends
-----------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Backend
     - Module
   * - IBM Quantum
     - ``abirqu.backends.ibm``
   * - D-Wave
     - ``abirqu.backends.dwave``
   * - Amazon Braket
     - ``abirqu.backends.aws``
   * - Azure Quantum
     - ``abirqu.backends.azure``
   * - Google Cirq
     - ``abirqu.backends.google``
   * - IonQ
     - ``abirqu.backends.ionq``
   * - Rigetti
     - ``abirqu.backends.rigetti``
   * - Quantinuum
     - ``abirqu.backends.quantinuum``
   * - Pasqal
     - ``abirqu.backends.pasqal``
   * - OQC
     - ``abirqu.backends.oqc``
   * - QuEra
     - ``abirqu.backends.quera``
   * - SpinQ
     - ``abirqu.backends.spinq``

Simulators
----------

.. automodule:: abirqu.simulation
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: abirqu.numpy_sim
   :members:
   :undoc-members:
   :show-inheritance:
