"""
AbirQu Bloch Sphere Widget
Copyright 2026 Abir Maheshwari

3D Bloch sphere visualization for single-qubit states.
"""
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


@dataclass
class BlochState:
    """Bloch sphere representation of a qubit state."""
    theta: float = 0.0  # polar angle (0 = |0⟩, π = |1⟩)
    phi: float = 0.0    # azimuthal angle

    @property
    def x(self) -> float:
        return math.sin(self.theta) * math.cos(self.phi)

    @property
    def y(self) -> float:
        return math.sin(self.theta) * math.sin(self.phi)

    @property
    def z(self) -> float:
        return math.cos(self.theta)

    @property
    def alpha(self) -> complex:
        return math.cos(self.theta / 2)

    @property
    def beta(self) -> complex:
        import cmath
        return cmath.exp(1j * self.phi) * math.sin(self.theta / 2)

    @classmethod
    def from_statevector(cls, alpha: complex, beta: complex) -> 'BlochState':
        theta = 2 * math.acos(min(1.0, abs(alpha)))
        phi = 0.0
        if abs(beta) > 1e-10 and abs(math.sin(theta/2)) > 1e-10:
            phi = math.atan2(beta.imag, beta.real)
        return cls(theta=theta, phi=phi)

    @classmethod
    def from_dict(cls, counts: Dict[str, int], num_qubits: int = 1,
                  qubit: int = 0) -> 'BlochState':
        if not counts:
            return cls(0, 0)

        p0, p1 = 0.0, 0.0
        for bitstring, count in counts.items():
            if qubit < len(bitstring):
                bit = int(bitstring[qubit])
                if bit == 0:
                    p0 += count
                else:
                    p1 += count

        total = p0 + p1
        if total == 0:
            return cls(0, 0)

        p0 /= total
        p1 /= total
        theta = 2 * math.acos(min(1.0, math.sqrt(p0)))
        return cls(theta=theta, phi=0.0)

    def __repr__(self):
        return f"BlochState(θ={self.theta:.3f}, φ={self.phi:.3f}, x={self.x:.3f}, y={self.y:.3f}, z={self.z:.3f})"


class BlochSphereWidget:
    """Bloch sphere renderer — generates 3D sphere data for visualization."""

    def __init__(self, resolution: int = 30):
        self.resolution = resolution
        self.state = BlochState()
        self._sphere_mesh = self._generate_sphere_mesh()
        self._axis_data = self._generate_axes()

    def set_state(self, state: BlochState):
        self.state = state

    def set_from_statevector(self, alpha: complex, beta: complex):
        self.state = BlochState.from_statevector(alpha, beta)

    def set_from_counts(self, counts: Dict[str, int], num_qubits: int = 1,
                        qubit: int = 0):
        self.state = BlochState.from_dict(counts, num_qubits, qubit)

    def _generate_sphere_mesh(self) -> Dict:
        res = self.resolution
        vertices = []
        indices = []
        normals = []

        for i in range(res + 1):
            theta = math.pi * i / res
            for j in range(res + 1):
                phi = 2 * math.pi * j / res
                x = math.sin(theta) * math.cos(phi)
                y = math.sin(theta) * math.sin(phi)
                z = math.cos(theta)
                vertices.append((x, y, z))
                normals.append((x, y, z))

        for i in range(res):
            for j in range(res):
                v0 = i * (res + 1) + j
                v1 = v0 + 1
                v2 = v0 + (res + 1)
                v3 = v2 + 1
                indices.extend([v0, v2, v1, v1, v2, v3])

        return {'vertices': vertices, 'indices': indices, 'normals': normals}

    def _generate_axes(self) -> Dict:
        return {
            'lines': [
                {'start': (-1.3, 0, 0), 'end': (1.3, 0, 0), 'color': '#f85149', 'label': 'X'},
                {'start': (0, -1.3, 0), 'end': (0, 1.3, 0), 'color': '#3fb950', 'label': 'Y'},
                {'start': (0, 0, -1.3), 'end': (0, 0, 1.3), 'color': '#58a6ff', 'label': 'Z'},
            ],
            'labels': {
                'top': {'pos': (0, 0, 1.4), 'text': '|0⟩', 'color': '#58a6ff'},
                'bottom': {'pos': (0, 0, -1.4), 'text': '|1⟩', 'color': '#f85149'},
                'right': {'pos': (1.4, 0, 0), 'text': '|+⟩', 'color': '#3fb950'},
                'left': {'pos': (-1.4, 0, 0), 'text': '|−⟩', 'color': '#3fb950'},
                'front': {'pos': (0, 1.4, 0), 'text': '|+i⟩', 'color': '#a855f7'},
                'back': {'pos': (0, -1.4, 0), 'text': '|−i⟩', 'color': '#a855f7'},
            },
        }

    def get_state_vector(self) -> Dict:
        """Get the state vector point on the Bloch sphere."""
        return {
            'x': self.state.x,
            'y': self.state.y,
            'z': self.state.z,
            'theta': self.state.theta,
            'phi': self.state.phi,
        }

    def get_arrow_data(self) -> Dict:
        """Get arrow from origin to state vector."""
        return {
            'origin': (0, 0, 0),
            'tip': (self.state.x, self.state.y, self.state.z),
            'color': '#7c3aed',
        }

    def get_render_data(self) -> Dict:
        """Get complete render data for the Bloch sphere."""
        return {
            'sphere': self._sphere_mesh,
            'axes': self._axis_data,
            'state_vector': self.get_state_vector(),
            'arrow': self.get_arrow_data(),
            'state_info': {
                'alpha': complex(self.state.alpha),
                'beta': complex(self.state.beta),
                'bloch_x': self.state.x,
                'bloch_y': self.state.y,
                'bloch_z': self.state.z,
            },
        }

    def project_2d(self, rotation_x: float = -0.5,
                   rotation_y: float = 0.7) -> Dict:
        """Project 3D sphere to 2D for flat rendering."""
        cx, cy = 200, 200
        scale = 150

        def rotate_point(x, y, z, rx, ry):
            cos_x, sin_x = math.cos(rx), math.sin(rx)
            y, z = y * cos_x - z * sin_x, y * sin_x + z * cos_x
            cos_y, sin_y = math.cos(ry), math.sin(ry)
            x, z = x * cos_y - z * sin_y, x * sin_y + z * cos_y
            return x, y, z

        def project(x, y, z):
            rx, ry = rotation_x, rotation_y
            x, y, z = rotate_point(x, y, z, rx, ry)
            px = cx + x * scale
            py = cy - z * scale
            depth = y
            return {'x': px, 'y': py, 'depth': depth}

        sx, sy, sz = self.state.x, self.state.y, self.state.z
        sx, sy, sz = rotate_point(sx, sy, sz, rotation_x, rotation_y)

        great_circles = []
        for plane in ['xy', 'xz', 'yz']:
            points = []
            for i in range(65):
                t = 2 * math.pi * i / 64
                if plane == 'xy':
                    x, y, z = math.cos(t), math.sin(t), 0
                elif plane == 'xz':
                    x, y, z = math.cos(t), 0, math.sin(t)
                else:
                    x, y, z = 0, math.cos(t), math.sin(t)
                p = rotate_point(x, y, z, rotation_x, rotation_y)
                points.append({'x': cx + p[0] * scale, 'y': cy - p[2] * scale, 'depth': p[1]})
            great_circles.append({'points': points, 'plane': plane})

        return {
            'center': {'x': cx, 'y': cy},
            'radius': scale,
            'state_point': {'x': cx + sx * scale, 'y': cy - sz * scale, 'depth': sy},
            'arrow': {
                'origin': {'x': cx, 'y': cy},
                'tip': {'x': cx + sx * scale, 'y': cy - sz * scale},
            },
            'great_circles': great_circles,
            'labels': {
                '|0⟩': project(0, 0, 1.2),
                '|1⟩': project(0, 0, -1.2),
                '|+⟩': project(1.2, 0, 0),
                '|−⟩': project(-1.2, 0, 0),
                '|+i⟩': project(0, 1.2, 0),
                '|−i⟩': project(0, -1.2, 0),
            },
        }
