"""
AbirQu Quantum Communication Module
Copyright 2026 Abir Maheshwari

Quantum Key Distribution (QKD) protocols and quantum networking
for India's 1,000-km and 2,000-km QKD networks.

Protocols:
- BB84: First QKD protocol (prepare-and-measure)
- E91: Entanglement-based QKD
- CV-QKD: Continuous-variable QKD
- DI-QKD: Device-independent QKD
- Satellite QKD: Long-distance via satellite
- Quantum Repeaters: Extending range
- Quantum Network: Multi-node simulation

References:
- Bennett & Brassard (1984): BB84 protocol
- Ekert (1991): E91 protocol
- Grosshans & Grangier (2002): CV-QKD
- India's National Quantum Mission: 1,000-km/2,000-km QKD network
"""

from .bb84 import BB84Protocol, BB84Simulator
from .e91 import E91Protocol, E91Simulator
from .cv_qkd import CVQKDProtocol, GaussianModulation
from .di_qkd import DIQKDProtocol, BellTest
from .satellite import SatelliteQKD, SatelliteLink
from .repeaters import QuantumRepeater, RepeaterChain
from .network import QuantumNetwork, QuantumNode, QuantumChannel

__all__ = [
    'BB84Protocol', 'BB84Simulator',
    'E91Protocol', 'E91Simulator',
    'CVQKDProtocol', 'GaussianModulation',
    'DIQKDProtocol', 'BellTest',
    'SatelliteQKD', 'SatelliteLink',
    'QuantumRepeater', 'RepeaterChain',
    'QuantumNetwork', 'QuantumNode', 'QuantumChannel',
]
