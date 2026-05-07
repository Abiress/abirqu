import numpy as np
from abirqu.circuit import Circuit
from abirqu.noise import NoiseModel

class DensityMatrixSimulator:
    """
    Kraus-operator density matrix simulator for exact noise modeling.
    Supports single-qubit gates, CNOT, and various noise channels.
    """

    def __init__(self, num_qubits):
        self.n = num_qubits
        self.dim = 1 << num_qubits
        self.rho = np.zeros((self.dim, self.dim), dtype=complex)
        self.rho[0, 0] = 1.0  # |0...0><0...0|

    def apply_gate(self, qubit, matrix_2x2):
        """Apply single-qubit gate via U ρ U†."""
        U = self._full_unitary(qubit, matrix_2x2)
        self.rho = U @ self.rho @ U.conj().T

    def apply_cnot(self, control, target):
        """Apply CNOT gate."""
        U = np.eye(self.dim, dtype=complex)
        cb, tb = 1 << control, 1 << target
        for i in range(self.dim):
            if (i & cb) != 0:
                j = i ^ tb
                U[i, i] = 0; U[j, j] = 0
                U[i, j] = 1; U[j, i] = 1
        self.rho = U @ self.rho @ U.conj().T

    def apply_depolarizing(self, qubit, p):
        """Apply depolarizing channel: ρ → (1-p)ρ + p/2*I (standard convention)."""
        if p <= 0:
            return
        X = np.array([[0,1],[1,0]], dtype=complex)
        Y = np.array([[0,-1j],[1j,0]], dtype=complex)
        Z = np.array([[1,0],[0,-1]], dtype=complex)

        # ρ → (1-p)ρ + p/2*I is equivalent to
        # ρ → (1 - 3p/4)ρ + p/4(XρX + YρY + ZρZ)
        rho_new = (1 - 0.75 * p) * self.rho
        for pauli in [X, Y, Z]:
            K = self._full_unitary(qubit, pauli)
            rho_new += (p / 4.0) * K @ self.rho @ K.conj().T
        self.rho = rho_new

    def apply_amplitude_damping(self, qubit, gamma):
        """Apply amplitude damping: K0 = [[1,0],[0,√(1-γ)]], K1 = [[0,√γ],[0,0]]."""
        K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
        K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
        K0_full = self._full_unitary(qubit, K0)
        K1_full = self._full_unitary(qubit, K1)
        self.rho = K0_full @ self.rho @ K0_full.conj().T + K1_full @ self.rho @ K1_full.conj().T

    def get_probabilities(self):
        """Return measurement probabilities from diagonal."""
        return np.real(np.diag(self.rho))

    def get_purity(self):
        """Tr(ρ²) — 1 for pure states, <1 for mixed states."""
        return np.real(np.trace(self.rho @ self.rho))

    def _full_unitary(self, qubit, matrix_2x2):
        """Build full 2^n × 2^n unitary from single-qubit 2×2 matrix."""
        ops = [np.eye(2, dtype=complex)] * self.n
        ops[self.n - 1 - qubit] = np.array(matrix_2x2, dtype=complex)
        result = ops[0]
        for op in ops[1:]:
            result = np.kron(result, op)
        return result

    def run_circuit(self, circuit, noise_model=None):
        """Run a circuit with optional per-gate noise."""
        H = np.array([[1,1],[1,-1]], dtype=complex) / np.sqrt(2)
        X = np.array([[0,1],[1,0]], dtype=complex)
        gates_map = {'H': H, 'X': X}

        for gate in getattr(circuit, 'gates', []):
            name = gate.name.upper()
            if name in gates_map:
                self.apply_gate(gate.qubits[0], gates_map[name])
            elif name in ('CNOT', 'CX'):
                self.apply_cnot(gate.qubits[0], gate.qubits[1])
            elif name == 'RZ':
                theta = gate.params[0]
                mat = np.array([[np.exp(-1j*theta/2), 0],
                                [0, np.exp(1j*theta/2)]], dtype=complex)
                self.apply_gate(gate.qubits[0], mat)
            elif name == 'RY':
                theta = gate.params[0]
                c, s = np.cos(theta/2), np.sin(theta/2)
                mat = np.array([[c, -s], [s, c]], dtype=complex)
                self.apply_gate(gate.qubits[0], mat)

            # Apply noise after each gate
            if noise_model:
                for q in gate.qubits:
                    for err in noise_model.get_qubit_errors(q):
                        if err['type'].value == 'depolarizing':
                            self.apply_depolarizing(q, err['probability'])
                        elif err['type'].value == 'amplitude_damping':
                            self.apply_amplitude_damping(q, err['gamma'])
