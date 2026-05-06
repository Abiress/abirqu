"""
Phase 16: Quantum Sensing & Metrology Module.

Task 16.1 — Quantum Sensor Simulator
Task 16.2 — Quantum-Enhanced Measurement Protocols
Task 16.3 — Quantum Clock & Timing
Task 16.4 — Quantum Imaging Module
Task 16.5 — Sensing Algorithm Library
"""

from .sensor_simulator import (
    QuantumSensorSimulator, Magnetometer, Gravimeter, AtomicClock, Interferometer,
    SensorReading, SensorType,
    SensorNoiseModel, SensitivityEstimator, CramérRaoBound, QuantumFisherInformation,
    SensorNetwork
)
from .measurement_protocols import (
    SqueezedStateGenerator, NOONStateProtocol, EntanglementEnhancedSensing,
    AdaptiveMeasurement, QuantumEnhancedProtocols,
    MeasurementResult, StateType
)
from .clock_timing import (
    AtomicClockSimulation, TimingSynchronization, QuantumEnhancedGPS,
    PrecisionEstimation,
    ClockReading
)
from .imaging import (
    QuantumImagingSimulator, ResolutionEnhancer,
    QuantumIllumination, ImageReconstructor,
    ImageResult, ImagingType
)
from .algorithm_library import (
    SensingTemplateLibrary, ParameterEstimation, MultiParameterEstimation,
    SensitivityOptimizer, SensingIntegratedCircuit,
    SensingResult, SensingTask
)

__all__ = [
    # Task 16.1
    'QuantumSensorSimulator', 'Magnetometer', 'Gravimeter', 'AtomicClock', 'Interferometer',
    'SensorReading', 'SensorType',
    'SensorNoiseModel', 'SensitivityEstimator', 'CramérRaoBound', 'QuantumFisherInformation',
    'SensorNetwork',
    # Task 16.2
    'SqueezedStateGenerator', 'NOONStateProtocol', 'EntanglementEnhancedSensing',
    'AdaptiveMeasurement', 'QuantumEnhancedProtocols',
    'MeasurementResult', 'StateType',
    # Task 16.3
    'AtomicClockSimulation', 'TimingSynchronization', 'QuantumEnhancedGPS',
    'PrecisionEstimation',
    'ClockReading',
    # Task 16.4
    'QuantumImagingSimulator', 'ResolutionEnhancer',
    'QuantumIllumination', 'ImageReconstructor',
    'ImageResult', 'ImagingType',
    # Task 16.5
    'SensingTemplateLibrary', 'ParameterEstimation', 'MultiParameterEstimation',
    'SensitivityOptimizer', 'SensingIntegratedCircuit',
    'SensingResult', 'SensingTask',
]
