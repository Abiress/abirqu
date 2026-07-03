"""
Circuit Partitioner
===================
Split large circuits across multiple QPUs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..circuit import Circuit, Gate


@dataclass
class Partition:
    """A partition of a circuit."""
    partition_id: int
    circuit: Circuit
    qubits: List[int]
    classical_bits: List[int] = field(default_factory=list)
    dependencies: List[int] = field(default_factory=list)  # other partitions this depends on


@dataclass
class PartitionResult:
    """Result of circuit partitioning."""
    partitions: List[Partition]
    original_qubits: int
    num_partitions: int
    cross_partition_gates: int
    strategy: str

    def to_dict(self) -> Dict:
        return {
            "original_qubits": self.original_qubits,
            "num_partitions": self.num_partitions,
            "cross_partition_gates": self.cross_partition_gates,
            "strategy": self.strategy,
            "partitions": [
                {
                    "id": p.partition_id,
                    "qubits": p.qubits,
                    "num_gates": len(p.circuit.gates),
                    "dependencies": p.dependencies,
                }
                for p in self.partitions
            ],
        }


class CircuitPartitioner:
    """Partition a circuit for multi-QPU execution.

    Parameters
    ----------
    max_qubits_per_partition : int
        Maximum qubits per partition.
    overlap : int
        Number of shared qubits between adjacent partitions.
    """

    def __init__(
        self,
        max_qubits_per_partition: int = 27,
        overlap: int = 2,
    ):
        self.max_qubits_per_partition = max_qubits_per_partition
        # Ensure overlap < max_qubits_per_partition to avoid zero step
        self.overlap = min(overlap, max_qubits_per_partition - 1)

    def partition(self, circuit: Circuit) -> PartitionResult:
        """Partition a circuit into sub-circuits."""
        num_qubits = circuit.num_qubits
        if num_qubits <= self.max_qubits_per_partition:
            return PartitionResult(
                partitions=[Partition(partition_id=0, circuit=circuit, qubits=list(range(num_qubits)))],
                original_qubits=num_qubits,
                num_partitions=1,
                cross_partition_gates=0,
                strategy="none",
            )

        # Linear partitioning with overlap
        partitions = self._linear_partition(circuit)
        cross_gates = self._count_cross_partition_gates(circuit, partitions)

        return PartitionResult(
            partitions=partitions,
            original_qubits=num_qubits,
            num_partitions=len(partitions),
            cross_partition_gates=cross_gates,
            strategy="linear_overlap",
        )

    def _linear_partition(self, circuit: Circuit) -> List[Partition]:
        """Split circuit into linear blocks with overlap."""
        num_qubits = circuit.num_qubits
        step = self.max_qubits_per_partition - self.overlap
        partitions = []
        pid = 0

        start = 0
        while start < num_qubits:
            end = min(start + self.max_qubits_per_partition, num_qubits)
            qubits = list(range(start, end))

            sub = Circuit(len(qubits))
            qubit_map = {q: i for i, q in enumerate(qubits)}

            for gate in circuit.gates:
                if all(q in qubit_map for q in gate.qubits):
                    mapped = tuple(qubit_map[q] for q in gate.qubits)
                    new_gate = Gate(name=gate.name, qubits=mapped, params=gate.params)
                    sub.gates.append(new_gate)

            partitions.append(Partition(partition_id=pid, circuit=sub, qubits=qubits))
            pid += 1
            start += step

        # Set dependencies (each depends on the previous)
        for i in range(1, len(partitions)):
            partitions[i].dependencies = [i - 1]

        return partitions

    def _count_cross_partition_gates(
        self,
        circuit: Circuit,
        partitions: List[Partition],
    ) -> int:
        """Count gates that span multiple partitions."""
        partition_qubit_sets = [set(p.qubits) for p in partitions]
        cross = 0
        for gate in circuit.gates:
            spans = set()
            for i, qs in enumerate(partition_qubit_sets):
                if any(q in qs for q in gate.qubits):
                    spans.add(i)
            if len(spans) > 1:
                cross += 1
        return cross
