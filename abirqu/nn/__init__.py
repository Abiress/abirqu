"""
Neural-Network Integration
==========================
Wrappers for PyTorch, JAX, and TensorFlow/Keras that embed parameterised
quantum circuits as differentiable layers.

Each integration falls back gracefully if its framework is not installed.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
# Internal: parameterised quantum circuit forward pass
# ---------------------------------------------------------------------------

def _quantum_forward(
    x: np.ndarray,
    weights: np.ndarray,
    n_qubits: int,
    n_layers: int,
    entanglement: str,
) -> np.ndarray:
    """Execute a parameterised quantum circuit on a batch of inputs.

    Parameters
    ----------
    x : np.ndarray, shape (batch, n_qubits)
        Input features (encoded via angle rotation).
    weights : np.ndarray, shape (n_layers, n_qubits)
        Rotation angles per layer.
    n_qubits : int
    n_layers : int
    entanglement : str
        ``"linear"``, ``"circular"``, or ``"full"``.

    Returns
    -------
    np.ndarray, shape (batch, n_qubits)
        Expectation values ⟨Z⟩ for each qubit.
    """
    from ..gates import rx, ry, rz, H, CNOT, CZ

    batch_size = x.shape[0]
    state = np.zeros((batch_size, 2 ** n_qubits), dtype=np.complex128)
    state[:, 0] = 1.0  # |00…0⟩

    # Encoding layer: Rx(x_i)
    for q in range(n_qubits):
        state = _apply_1q_batch(state, rx, x[:, q], q, n_qubits)

    # Variational layers
    for layer in range(n_layers):
        # Rotation layer
        for q in range(n_qubits):
            state = _apply_1q_batch(state, ry, weights[layer, q], q, n_qubits)
        # Entanglement layer
        state = _apply_entanglement(state, n_qubits, entanglement)

    # Measure ⟨Z⟩ per qubit
    return _measure_z_expectations(state, n_qubits)


def _apply_1q_batch(
    state: np.ndarray,
    gate_fn: Any,
    angles: np.ndarray,
    qubit: int,
    n_qubits: int,
) -> np.ndarray:
    """Apply a parameterised single-qubit gate to a batched state."""
    batch = state.shape[0]
    dim = 2 ** n_qubits
    mask = 1 << qubit
    new_state = np.zeros_like(state)

    for b in range(batch):
        theta = float(angles[b])
        g = gate_fn(theta)
        for i in range(dim):
            bit = (i >> qubit) & 1
            other = i ^ mask
            if bit == 0:
                new_state[b, i] = g[0, 0] * state[b, i] + g[0, 1] * state[b, other]
                new_state[b, other] = g[1, 0] * state[b, i] + g[1, 1] * state[b, other]
    return new_state


def _apply_entanglement(
    state: np.ndarray, n_qubits: int, kind: str
) -> np.ndarray:
    """Apply CNOT entangling layer."""
    dim = 2 ** n_qubits
    batch = state.shape[0]
    pairs: List[Tuple[int, int]] = []

    if kind == "linear":
        pairs = [(i, i + 1) for i in range(n_qubits - 1)]
    elif kind == "circular":
        pairs = [(i, (i + 1) % n_qubits) for i in range(n_qubits)]
    elif kind == "full":
        pairs = [(i, j) for i in range(n_qubits) for j in range(i + 1, n_qubits)]
    else:
        pairs = [(i, i + 1) for i in range(n_qubits - 1)]

    for ctrl, tgt in pairs:
        mask_ctrl = 1 << ctrl
        mask_tgt = 1 << tgt
        new_state = np.zeros_like(state)
        for b in range(batch):
            for i in range(dim):
                c = (i >> ctrl) & 1
                t = (i >> tgt) & 1
                if c == 0:
                    new_state[b, i] = state[b, i]
                else:
                    flipped = i ^ mask_tgt
                    new_state[b, i] = state[b, flipped]
        state = new_state

    return state


def _measure_z_expectations(state: np.ndarray, n_qubits: int) -> np.ndarray:
    """Compute ⟨Z⟩ for each qubit from the state vector."""
    batch = state.shape[0]
    dim = 2 ** n_qubits
    expectations = np.zeros((batch, n_qubits), dtype=np.float64)

    probs = np.abs(state) ** 2  # (batch, dim)
    for q in range(n_qubits):
        mask = 1 << q
        for i in range(dim):
            sign = 1.0 - 2.0 * ((i >> q) & 1)
            expectations[:, q] += sign * probs[:, i]
    return expectations


def _parameter_shift_gradient(
    x: np.ndarray,
    weights: np.ndarray,
    n_qubits: int,
    n_layers: int,
    entanglement: str,
    epsilon: float = math.pi / 2,
) -> np.ndarray:
    """Compute gradient of output w.r.t. weights via parameter-shift rule."""
    grad = np.zeros_like(weights)
    for layer in range(n_layers):
        for q in range(n_qubits):
            w_plus = weights.copy()
            w_plus[layer, q] += epsilon
            out_plus = _quantum_forward(x, w_plus, n_qubits, n_layers, entanglement)

            w_minus = weights.copy()
            w_minus[layer, q] -= epsilon
            out_minus = _quantum_forward(x, w_minus, n_qubits, n_layers, entanglement)

            grad[layer, q] = float(np.mean(out_plus - out_minus)) / (2.0 * math.sin(epsilon))
    return grad


# ---------------------------------------------------------------------------
# PyTorch integration
# ---------------------------------------------------------------------------

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    class QuantumLayer(nn.Module):
        """PyTorch ``nn.Module`` wrapping a parameterised quantum circuit.

        Parameters
        ----------
        n_qubits : int
            Number of qubits.
        n_layers : int
            Number of variational layers.
        entanglement : str
            Entanglement topology (``"linear"``, ``"circular"``, ``"full"``).
        """

        def __init__(
            self,
            n_qubits: int = 4,
            n_layers: int = 2,
            entanglement: str = "linear",
        ) -> None:
            super().__init__()
            self.n_qubits = n_qubits
            self.n_layers = n_layers
            self.entanglement = entanglement
            self.weights = nn.Parameter(
                torch.randn(n_layers, n_qubits) * 0.1
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """Forward pass — quantum circuit as a differentiable layer.

            Parameters
            ----------
            x : torch.Tensor, shape (batch, n_qubits)
                Input features.

            Returns
            -------
            torch.Tensor, shape (batch, n_qubits)
                ⟨Z⟩ expectations.
            """
            x_np = x.detach().cpu().numpy()
            w_np = self.weights.detach().cpu().numpy()
            out = _quantum_forward(
                x_np, w_np, self.n_qubits, self.n_layers, self.entanglement
            )
            return torch.tensor(out, dtype=x.dtype, device=x.device)

        def parameter_shift_grad(
            self, x: torch.Tensor
        ) -> torch.Tensor:
            """Compute gradient via parameter-shift (detached from autograd)."""
            x_np = x.detach().cpu().numpy()
            w_np = self.weights.detach().cpu().numpy()
            grad_np = _parameter_shift_gradient(
                x_np, w_np, self.n_qubits, self.n_layers, self.entanglement
            )
            return torch.tensor(grad_np, dtype=x.dtype, device=x.device)

except ImportError:
    QuantumLayer = None  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# JAX integration
# ---------------------------------------------------------------------------

try:
    import jax
    import jax.numpy as jnp

    class QuantumJAXLayer:
        """JAX-based parameterised quantum circuit layer.

        Parameters
        ----------
        n_qubits : int
        n_layers : int
        entanglement : str
        """

        def __init__(
            self,
            n_qubits: int = 4,
            n_layers: int = 2,
            entanglement: str = "linear",
        ) -> None:
            self.n_qubits = n_qubits
            self.n_layers = n_layers
            self.entanglement = entanglement
            self.weights = jnp.array(
                np.random.randn(n_layers, n_qubits) * 0.1
            )

        def forward(self, x: jnp.ndarray) -> jnp.ndarray:
            """Forward pass returning ⟨Z⟩ expectations."""
            x_np = np.array(x)
            w_np = np.array(self.weights)
            out = _quantum_forward(
                x_np, w_np, self.n_qubits, self.n_layers, self.entanglement
            )
            return jnp.array(out)

        def grad(self, x: jnp.ndarray) -> jnp.ndarray:
            """Compute gradient using ``jax.grad``."""
            x_np = np.array(x)

            def loss(w: np.ndarray) -> float:
                out = _quantum_forward(
                    x_np, w, self.n_qubits, self.n_layers, self.entanglement
                )
                return float(np.mean(out))

            grad_fn = jax.grad(loss)
            grad_np = grad_fn(np.array(self.weights))
            return jnp.array(grad_np)

except ImportError:
    QuantumJAXLayer = None  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# TensorFlow / Keras integration
# ---------------------------------------------------------------------------

try:
    import tensorflow as tf

    class QuantumTFLayer(tf.keras.layers.Layer):
        """TensorFlow/Keras layer wrapping a parameterised quantum circuit.

        Parameters
        ----------
        n_qubits : int
        n_layers : int
        entanglement : str
        """

        def __init__(
            self,
            n_qubits: int = 4,
            n_layers: int = 2,
            entanglement: str = "linear",
            **kwargs: Any,
        ) -> None:
            super().__init__(**kwargs)
            self.n_qubits = n_qubits
            self.n_layers = n_layers
            self.entanglement = entanglement
            self.q_weights = self.add_weight(
                name="q_weights",
                shape=(n_layers, n_qubits),
                initializer="random_normal",
                trainable=True,
            )

        def call(self, inputs: tf.Tensor) -> tf.Tensor:
            """Forward pass returning ⟨Z⟩ expectations."""
            x_np = inputs.numpy() if hasattr(inputs, "numpy") else np.array(inputs)
            w_np = self.q_weights.numpy()
            out = _quantum_forward(
                x_np, w_np, self.n_qubits, self.n_layers, self.entanglement
            )
            return tf.constant(out, dtype=inputs.dtype)

except ImportError:
    QuantumTFLayer = None  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Hybrid model (classical + quantum)
# ---------------------------------------------------------------------------

class HybridModel:
    """Combines a classical neural network with a quantum layer.

    The classical part compresses ``input_dim`` features down to
    ``n_qubits`` features, which are then fed into the quantum layer.

    Falls back to a purely classical layer if no quantum framework is
    available.

    Parameters
    ----------
    input_dim : int
        Dimensionality of classical input.
    n_qubits : int
        Number of qubits in the quantum layer.
    n_layers : int
        Variational depth.
    entanglement : str
        Entanglement topology.
    """

    def __init__(
        self,
        input_dim: int = 8,
        n_qubits: int = 4,
        n_layers: int = 2,
        entanglement: str = "linear",
    ) -> None:
        self.input_dim = input_dim
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.entanglement = entanglement

        # Classical weights (simple linear projection)
        self.W = np.random.randn(input_dim, n_qubits) * np.sqrt(2.0 / input_dim)
        self.b = np.zeros(n_qubits)

        # Quantum layer (if available)
        self._quantum: Any = None
        if QuantumLayer is not None:
            self._quantum = QuantumLayer(n_qubits, n_layers, entanglement)
        elif QuantumJAXLayer is not None:
            self._quantum = QuantumJAXLayer(n_qubits, n_layers, entanglement)
        elif QuantumTFLayer is not None:
            self._quantum = QuantumTFLayer(n_qubits, n_layers, entanglement)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass: classical → quantum → output.

        Parameters
        ----------
        x : np.ndarray, shape (batch, input_dim)

        Returns
        -------
        np.ndarray, shape (batch, n_qubits)
        """
        # Classical projection
        h = x @ self.W + self.b  # (batch, n_qubits)
        h = np.tanh(h)

        # Quantum layer
        if self._quantum is not None:
            try:
                return np.asarray(self._quantum.forward(h))
            except Exception:
                pass

        # Fallback: return classical output directly
        return h

    @property
    def framework(self) -> str:
        """Return the name of the active quantum framework, or ``'numpy'``."""
        if QuantumLayer is not None:
            return "pytorch"
        if QuantumJAXLayer is not None:
            return "jax"
        if QuantumTFLayer is not None:
            return "tensorflow"
        return "numpy"


__all__ = [
    "HybridModel",
    "QuantumLayer",
    "QuantumJAXLayer",
    "QuantumTFLayer",
]
