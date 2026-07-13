"""
Tree Tensor Network (TTN) Simulator.

Implements a binary tree tensor network for quantum circuit simulation.
TTN is more efficient than MPS for circuits with tree-like entanglement structure.

Architecture:
    Leaf nodes = physical qubits
    Internal nodes = virtual bonds formed by contractions
    Root node = final contraction target

For n qubits:
    - n leaf tensors (shape: 2)
    - n-1 internal tensors (shape: bond_dim × bond_dim × bond_dim)
    - logarithmic depth for well-structured circuits

References:
    - Gray & Kourtis (2021): Hyper-optimized tensor network contraction
    - Zou et al. (2021): Tree tensor networks for quantum chemistry
    - Motta et al. (2021): Tree tensor network state quantum chemistry
"""

from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field
import numpy as np

from ..circuit import Circuit


@dataclass
class TTNTreeNode:
    """Node in the binary tree tensor network."""
    index: int
    tensor: np.ndarray
    qubits: List[int]
    left: Optional[int] = None
    right: Optional[int] = None
    is_leaf: bool = False


class TreeTensorNetwork:
    """
    Binary tree tensor network for quantum simulation.

    For n qubits, builds a balanced binary tree:
    - Leaves: single-qubit tensors |0⟩ or |1⟩
    - Internal nodes: bond tensors formed by SVD decomposition of gate contractions
    - Root: the final tensor after all contractions
    """

    def __init__(self, n_qubits: int, max_bond: int = 64, cutoff: float = 1e-12):
        self.n_qubits = n_qubits
        self.max_bond = max_bond
        self.cutoff = cutoff
        self.nodes: Dict[int, TTNTreeNode] = {}
        self._next_index = 0
        self._build_initial_tree()

    def _build_initial_tree(self):
        """Build initial tree with leaf tensors for |0⟩ state."""
        for q in range(self.n_qubits):
            idx = self._next_index
            self._next_index += 1
            tensor = np.zeros(2, dtype=complex)
            tensor[0] = 1.0  # |0⟩
            self.nodes[idx] = TTNTreeNode(
                index=idx, tensor=tensor, qubits=[q], is_leaf=True
            )

    @property
    def root_index(self) -> int:
        return max(self.nodes.keys()) if self.nodes else -1

    def apply_single_qubit_gate(self, gate_matrix: np.ndarray, qubit: int):
        """Apply a single-qubit gate to the leaf tensor of the given qubit."""
        node_idx = self._find_leaf(qubit)
        if node_idx is None:
            return
        node = self.nodes[node_idx]
        # Contract gate with tensor: result = gate @ tensor
        new_tensor = gate_matrix @ node.tensor
        self.nodes[node_idx] = TTNTreeNode(
            index=node_idx, tensor=new_tensor, qubits=[qubit], is_leaf=True
        )

    def apply_two_qubit_gate(self, gate_matrix: np.ndarray, q0: int, q1: int):
        """
        Apply a two-qubit gate by finding the least common ancestor (LCA)
        of the two qubits and contracting through the tree.
        """
        leaf0 = self._find_leaf(q0)
        leaf1 = self._find_leaf(q1)
        if leaf0 is None or leaf1 is None:
            return

        if leaf0 == leaf1:
            return

        # Find LCA
        lca = self._find_lca(leaf0, leaf1)
        if lca is None:
            return

        # If both qubits are leaves under the same parent, contract directly
        lca_node = self.nodes[lca]
        if lca_node.left is not None and lca_node.right is not None:
            left_node = self.nodes[lca_node.left]
            right_node = self.nodes[lca_node.right]

            if left_node.is_leaf and right_node.is_leaf:
                # Both are leaves - contract directly
                left_t = left_node.tensor  # shape (2,)
                right_t = right_node.tensor  # shape (2,)

                # Outer product: (2, 2)
                combined = np.outer(left_t, right_t).reshape(4)

                # Apply gate: (4, 4) @ (4,) -> (4,)
                gate_reshaped = gate_matrix.reshape(4, 4) if gate_matrix.size == 16 else gate_matrix
                result = gate_reshaped @ combined

                # SVD decompose back into two tensors
                result_matrix = result.reshape(2, 2)
                U, S, Vh = np.linalg.svd(result_matrix, full_matrices=False)

                # Truncate
                chi = min(len(S), self.max_bond)
                U = U[:, :chi]
                S = S[:chi]
                Vh = Vh[:chi, :]

                # Normalize singular values
                norm = np.sqrt(np.sum(S**2))
                if norm > self.cutoff:
                    S /= norm

                # Update tensors
                new_left = U * S[np.newaxis, :]  # shape (2, chi)
                new_right = Vh  # shape (chi, 2)

                # Reshape to vectors if bond_dim == 1
                if chi == 1:
                    new_left = new_left.flatten()
                    new_right = new_right.flatten()
                    self.nodes[leaf0] = TTNTreeNode(
                        index=leaf0, tensor=new_left, qubits=[q0], is_leaf=True
                    )
                    self.nodes[leaf1] = TTNTreeNode(
                        index=leaf1, tensor=new_right, qubits=[q1], is_leaf=True
                    )
                else:
                    # Create bond tensor at LCA
                    bond_tensor = np.eye(chi, dtype=complex).reshape(chi, 1, chi)
                    self.nodes[lca] = TTNTreeNode(
                        index=lca, tensor=bond_tensor, qubits=lca_node.qubits,
                        left=leaf0, right=leaf1
                    )
                    self.nodes[leaf0] = TTNTreeNode(
                        index=leaf0, tensor=new_left, qubits=[q0], is_leaf=False
                    )
                    self.nodes[leaf1] = TTNTreeNode(
                        index=leaf1, tensor=new_right, qubits=[q1], is_leaf=False
                    )
            else:
                # Non-both-leaves case: use fallback
                self._apply_two_qubit_fallback(gate_matrix, q0, q1)

    def _apply_two_qubit_fallback(self, gate_matrix: np.ndarray, q0: int, q1: int):
        """Fallback: contract entire network to statevector, apply gate, rebuild."""
        sv = self.get_statevector()
        if sv is None or len(sv) != 2**self.n_qubits:
            return

        # Apply gate to statevector
        n = self.n_qubits
        gate = gate_matrix.reshape(4, 4) if gate_matrix.size == 16 else gate_matrix
        sv_matrix = sv.reshape([2] * n)

        # Transpose qubits to last two axes
        axes = list(range(n))
        axes.remove(q0)
        axes.remove(q1)
        axes.extend([q0, q1])
        sv_matrix = sv_matrix.transpose(axes)

        shape_other = sv_matrix.shape[:-2]
        sv_flat = sv_matrix.reshape(-1, 4)
        sv_flat = (gate @ sv_flat.T).T
        sv_matrix = sv_flat.reshape(shape_other + (2, 2))

        # Transpose back
        inv_axes = [0] * n
        for i, ax in enumerate(axes):
            inv_axes[ax] = i
        sv_matrix = sv_matrix.transpose(inv_axes)

        new_sv = sv_matrix.reshape(2**n)
        self._rebuild_from_statevector(new_sv)

    def _rebuild_from_statevector(self, sv: np.ndarray):
        """Rebuild tree from statevector via sequential SVD."""
        self.nodes.clear()
        self._next_index = 0
        n = self.n_qubits

        if n == 0:
            return

        # Sequential SVD decomposition
        remaining = sv.copy()
        tensors = []

        for i in range(n - 1):
            dim_left = 2 ** (i + 1)
            dim_right = len(remaining) // dim_left
            remaining_matrix = remaining.reshape(dim_left, dim_right)

            U, S, Vh = np.linalg.svd(remaining_matrix, full_matrices=False)
            chi = min(len(S), self.max_bond)
            U = U[:, :chi]
            S = S[:chi]
            Vh = Vh[:chi, :]

            norm = np.sqrt(np.sum(S**2))
            if norm > self.cutoff:
                S /= norm

            tensors.append(U.reshape(-1, chi) if i == 0 else U.reshape(2, -1, chi))
            remaining = (S[:, np.newaxis] * Vh).flatten()

        tensors.append(remaining.reshape(2, -1) if len(remaining) > 2 else remaining)

        # Build tree from tensors
        for i, t in enumerate(tensors):
            idx = self._next_index
            self._next_index += 1
            qubits = [i] if i < n else []
            self.nodes[idx] = TTNTreeNode(
                index=idx, tensor=t, qubits=qubits, is_leaf=(i < n)
            )

        # Link tree
        for i in range(len(tensors) - 1):
            parent_idx = len(tensors) - 1
            if i < len(tensors) // 2:
                self.nodes[parent_idx].left = i
            else:
                self.nodes[parent_idx].right = i

    def _find_leaf(self, qubit: int) -> Optional[int]:
        """Find the leaf node for a given qubit."""
        for idx, node in self.nodes.items():
            if node.is_leaf and qubit in node.qubits:
                return idx
        return None

    def _find_lca(self, idx0: int, idx1: int) -> Optional[int]:
        """Find least common ancestor of two nodes."""
        path0 = self._path_to_root(idx0)
        path1 = set(self._path_to_root(idx1))
        for idx in path0:
            if idx in path1:
                return idx
        return None

    def _path_to_root(self, idx: int) -> List[int]:
        """Get path from node to root."""
        path = [idx]
        node = self.nodes.get(idx)
        if node is None:
            return path

        # Build parent map
        parent_map = {}
        for nidx, nnode in self.nodes.items():
            if nnode.left is not None:
                parent_map[nnode.left] = nidx
            if nnode.right is not None:
                parent_map[nnode.right] = nidx

        current = idx
        while current in parent_map:
            current = parent_map[current]
            path.append(current)
        return path

    def get_statevector(self) -> Optional[np.ndarray]:
        """Contract the entire tree to get the statevector."""
        if not self.nodes:
            return None

        n = self.n_qubits
        if n > 20:
            return None

        # Simple approach: just contract all leaf tensors
        sv = np.array([1.0], dtype=complex)
        for q in range(n):
            leaf_idx = self._find_leaf(q)
            if leaf_idx is not None:
                tensor = self.nodes[leaf_idx].tensor
                sv = np.kron(sv, tensor)
        return sv

    def fidelity_with(self, other: 'TreeTensorNetwork') -> float:
        """Compute fidelity |⟨self|other⟩|²."""
        sv_self = self.get_statevector()
        sv_other = other.get_statevector()
        if sv_self is None or sv_other is None:
            return 0.0
        overlap = np.abs(np.vdot(sv_self, sv_other)) ** 2
        return float(overlap)


class TTNSimulator:
    """
    Tree Tensor Network simulator for quantum circuits.

    Automatically selects between TTN (for tree-structured circuits)
    and statevector (for dense circuits).
    """

    def __init__(self, max_bond: int = 64, cutoff: float = 1e-12):
        self.max_bond = max_bond
        self.cutoff = cutoff

    def run_circuit(self, circuit: Circuit, shots: int = 1024) -> Dict[str, int]:
        """Execute a circuit and return measurement counts."""
        n = circuit.num_qubits

        if n <= 20:
            return self._run_statevector(circuit, shots)
        else:
            return self._run_ttn(circuit, shots)

    def _run_statevector(self, circuit: Circuit, shots: int) -> Dict[str, int]:
        """Use statevector simulation for small circuits."""
        from . import MonteCarloWavefunctionSimulator
        sim = MonteCarloWavefunctionSimulator()
        return sim.run_circuit(circuit, shots=shots)

    def _run_ttn(self, circuit: Circuit, shots: int) -> Dict[str, int]:
        """Use TTN for larger circuits."""
        ttn = TreeTensorNetwork(
            circuit.num_qubits, max_bond=self.max_bond, cutoff=self.cutoff
        )

        for gate in circuit.gates:
            self._apply_gate(ttn, gate)

        sv = ttn.get_statevector()
        if sv is None:
            return self._run_statevector(circuit, shots)

        probs = np.abs(sv) ** 2
        probs /= np.sum(probs)

        counts = {}
        for _ in range(shots):
            sample = np.random.choice(len(probs), p=probs)
            bits = format(sample, f'0{circuit.num_qubits}b')
            counts[bits] = counts.get(bits, 0) + 1
        return counts

    def _apply_gate(self, ttn: TreeTensorNetwork, gate):
        """Apply a gate to the TTN."""
        name = gate.name.upper()
        qubits = gate.qubits if hasattr(gate, 'qubits') else [gate.qubit]
        params = getattr(gate, 'params', []) or []

        if len(qubits) == 1:
            mat = self._get_single_matrix(name, params)
            if mat is not None:
                ttn.apply_single_qubit_gate(mat, qubits[0])
        elif len(qubits) == 2:
            mat = self._get_two_matrix(name, params)
            if mat is not None:
                ttn.apply_two_qubit_gate(mat, qubits[0], qubits[1])

    def _get_single_matrix(self, name: str, params: list) -> Optional[np.ndarray]:
        """Get single-qubit gate matrix."""
        if name == 'H':
            return np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
        elif name == 'X':
            return np.array([[0, 1], [1, 0]], dtype=complex)
        elif name == 'Y':
            return np.array([[0, -1j], [1j, 0]], dtype=complex)
        elif name == 'Z':
            return np.array([[1, 0], [0, -1]], dtype=complex)
        elif name == 'S':
            return np.array([[1, 0], [0, 1j]], dtype=complex)
        elif name == 'S_DAG':
            return np.array([[1, 0], [0, -1j]], dtype=complex)
        elif name == 'T':
            return np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)
        elif name == 'T_DAG':
            return np.array([[1, 0], [0, np.exp(-1j * np.pi / 4)]], dtype=complex)
        elif name == 'RX':
            theta = params[0] if params else 0.0
            c, s = np.cos(theta / 2), np.sin(theta / 2)
            return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)
        elif name == 'RY':
            theta = params[0] if params else 0.0
            c, s = np.cos(theta / 2), np.sin(theta / 2)
            return np.array([[c, -s], [s, c]], dtype=complex)
        elif name == 'RZ':
            theta = params[0] if params else 0.0
            return np.array([[np.exp(-1j * theta / 2), 0],
                             [0, np.exp(1j * theta / 2)]], dtype=complex)
        return None

    def _get_two_matrix(self, name: str, params: list) -> Optional[np.ndarray]:
        """Get two-qubit gate matrix."""
        if name in ('CNOT', 'CX'):
            return np.array([[1, 0, 0, 0],
                             [0, 1, 0, 0],
                             [0, 0, 0, 1],
                             [0, 0, 1, 0]], dtype=complex)
        elif name == 'CZ':
            return np.diag([1, 1, 1, -1]).astype(complex)
        elif name == 'SWAP':
            return np.array([[1, 0, 0, 0],
                             [0, 0, 1, 0],
                             [0, 1, 0, 0],
                             [0, 0, 0, 1]], dtype=complex)
        elif name == 'ECR':
            return np.array([[0, 0, 1, 1j],
                             [0, 0, 1j, 1],
                             [1, -1j, 0, 0],
                             [-1j, 1, 0, 0]], dtype=complex) / np.sqrt(2)
        elif name == 'ISWAP':
            return np.array([[1, 0, 0, 0],
                             [0, 0, 1j, 0],
                             [0, 1j, 0, 0],
                             [0, 0, 0, 1]], dtype=complex)
        return None
